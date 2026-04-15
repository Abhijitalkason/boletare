# Discussion Summary — 2026-03-22

## Session Overview

This session focused on troubleshooting an Azure VM resize issue via Crossplane, where `spec.forProvider.size` (desired: `Standard_B2s`) did not match `status.atProvider.size` (actual: `Standard_B1s`). We verified the behavior against official Crossplane documentation.

---

## 1. The Problem: Spec vs Status Mismatch

```
spec.forProvider.size   = Standard_B2s   (desired — what we requested)
status.atProvider.size  = Standard_B1s   (actual — what's running in Azure)
```

The VM resize from B1s → B2s was requested but not applied by Azure.

---

## 2. How Crossplane Handles VM Resize (Verified from Docs)

### Reconciliation Loop

Crossplane follows a continuous reconciliation loop:

1. **Observe** — Provider calls Azure API to read current VM state → populates `status.atProvider`
2. **Compare** — Compares `spec.forProvider` (desired) vs observed state
3. **Update** — If drift detected, issues an Update call to Azure API
4. **Enforce** — `spec.forProvider` is the **source of truth**. Any external changes (e.g., portal resize) get reverted by Crossplane

### Key Fact: Crossplane Does NOT Auto-Deallocate

Crossplane/Upjet does **NOT** automatically stop or deallocate the VM before resizing. The chain is:

1. Crossplane detects `spec.forProvider.size` differs from observed state
2. Upjet (Terraform wrapper) calls Azure Compute API `VirtualMachines.CreateOrUpdate` with new size
3. **Azure decides** what happens next:
   - If new size is available on current hardware cluster → Azure **restarts** the VM in-place (VM will reboot)
   - If new size is NOT available on current cluster → Azure API **returns an error** → Crossplane reports `ReconcileError`

### The `size` Field is an In-Place Update

- The `size` field is **NOT** a ForceNew field in Terraform
- Changing it does **not** destroy and recreate the VM
- It triggers an in-place update via the Azure API

**Sources:**
- [Crossplane Managed Resources](https://docs.crossplane.io/latest/managed-resources/managed-resources/)
- [LinuxVirtualMachine - Upbound Marketplace](https://marketplace.upbound.io/providers/upbound/provider-azure-compute/v0.41.0/resources/compute.azure.upbound.io/LinuxVirtualMachine/v1beta1)
- [Azure VM Resize - Microsoft Learn](https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/resize-vm)
- [Terraform azurerm_linux_virtual_machine](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_virtual_machine)

---

## 3. Common Resize Failure Reasons

| Error | Cause | Resolution |
|-------|-------|------------|
| `OperationNotAllowed: VM size not available in current hardware cluster` | New SKU not available on current host | **Deallocate the VM first**, then retry |
| `AllocationFailed` | Azure cannot allocate the size in region/zone | Try different size or region |
| `OperationNotAllowed: VM is not in a state to be resized` | VM is in failed/transitioning state | Fix VM state in Azure first |
| `refuse to update...requires replacing it` | Upjet safety mechanism for ForceNew fields | Delete and recreate (does NOT apply to `size`) |
| Quota exceeded | Subscription vCPU quota limit reached | Request quota increase in Azure portal |

### Circuit Breaker

If reconciliation fails repeatedly, Crossplane activates a circuit breaker:
- `Responsive` condition becomes `False`
- Reason: `WatchCircuitOpen`
- Reconciliation pauses to avoid thrashing

---

## 4. Troubleshooting Commands

### Check Resource Conditions (Most Important)
```powershell
# Describe the resource — shows conditions, events, errors
kubectl describe linuxvirtualmachine vm-ops-test
```

Look for these conditions in the output:
```
Status:
  Conditions:
    Type:    Ready
    Status:  True/False
    Reason:  Available / Creating / Deleting / Unavailable

    Type:    Synced
    Status:  True/False
    Reason:  ReconcileSuccess / ReconcileError / ReconcilePaused
    Message: <detailed error message here>

    Type:    Responsive        (circuit breaker)
    Status:  True/False
    Reason:  WatchCircuitOpen
```

### Check Events
```powershell
kubectl get events --field-selector involvedObject.name=vm-ops-test
```

### Check Provider Logs
```powershell
kubectl -n crossplane-system logs -l pkg.crossplane.io/revision --tail=100
```

### Force Re-Reconciliation (If Stuck)
```powershell
kubectl annotate linuxvirtualmachine vm-ops-test force-reconcile=$(date +%s)
```

---

## 5. What We Should Do for Our vm-ops-test

### Step 1: Diagnose
```powershell
kubectl describe linuxvirtualmachine vm-ops-test
```
Check if `Synced` condition is `False` with a `ReconcileError` message.

### Step 2: Most Likely Fix — Deallocate First

If the error says "size not available in current hardware cluster":

```powershell
# Option A: Deallocate via Azure CLI
az vm deallocate --resource-group <rg-name> --name vm-ops-test

# Option B: If using Crossplane power state management
# Set the VM to stopped/deallocated state, wait, then set desired size
```

After deallocation, Crossplane will retry the resize on next reconciliation tick and Azure will allocate on a compatible host.

### Step 3: Verify
```powershell
# Confirm both spec and status match after resize
kubectl get linuxvirtualmachine vm-ops-test -o jsonpath='{.spec.forProvider.size}'
kubectl get linuxvirtualmachine vm-ops-test -o jsonpath='{.status.atProvider.size}'
```

Both should now show `Standard_B2s`.

---

## 6. Key Learnings

### Crossplane is a Terraform Wrapper (via Upjet)
- The Azure provider (`provider-upjet-azure`) wraps Terraform's `azurerm` provider
- Any Terraform behavior for `azurerm_linux_virtual_machine` applies to Crossplane
- The original `crossplane-contrib/provider-azure` is **archived** — use the Upjet-based provider

### spec.forProvider vs status.atProvider
- `spec.forProvider` = **desired state** (what you want)
- `status.atProvider` = **observed state** (what Azure actually has)
- When they differ, Crossplane tries to reconcile — but may fail if Azure rejects the change

### Crossplane Does NOT Handle VM Power State for Resize
- No built-in mechanism to pre-emptively deallocate before resize
- If deallocation is required, handle it externally (Azure CLI, custom controller, or Composition)
- This is a gap in the Crossplane Azure provider workflow

### The `Synced` Condition is Your Best Friend
- `Synced=True, Reason=ReconcileSuccess` → all good
- `Synced=False, Reason=ReconcileError` → check the `Message` field for the exact Azure error
- Always check this first when spec and status don't match
