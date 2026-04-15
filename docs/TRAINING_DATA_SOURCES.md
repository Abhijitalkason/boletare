# Training Data Sources — Archive.org OCR Files

All sources verified on 2026-04-08 via the `internetarchive` Python package. Each item has a `_djvu.txt` OCR text file suitable for the existing parsing pipeline.

**Last update:** 2026-04-10 — 11 active sources (5 sources removed: 3 unavailable due to DRM/language, 2 dropped after format analysis showed zero biographical event content).

## Download URL Pattern

```
https://archive.org/download/{IDENTIFIER}/{OCR_FILENAME}
```

## Bulk Download

Use the bulk download script which handles all 13 sources, validation, retries, and idempotency:

```bash
python scripts/training/01b_download_all_ocr.py
```

Source list lives in [scripts/training/ocr_sources.py](../scripts/training/ocr_sources.py).

---

## Books (5 items)

### 1. Notable Horoscopes — B.V. Raman
- **Identifier:** `NotableHoroscopesBVR`
- **OCR File:** `Notable Horoscopes_djvu.txt`
- **Local Path:** `data/training/raw/notable_horoscopes_ocr.txt`
- **URL:** https://archive.org/download/NotableHoroscopesBVR/Notable%20Horoscopes_djvu.txt
- **Status:** Downloaded (715 KB) — In use, 108 samples extracted

### 2. How to Judge a Horoscope — R. Santhanam (translation)
- **Identifier:** `how-to-judge-a-horoscope-r.-santhanam`
- **OCR File:** `How to Judge a Horoscope - R. Santhanam_djvu.txt`
- **Local Path:** `data/training/raw/judge_horoscope_santhanam_ocr.txt`
- **URL:** https://archive.org/download/how-to-judge-a-horoscope-r.-santhanam/How%20to%20Judge%20a%20Horoscope%20-%20R.%20Santhanam_djvu.txt
- **Status:** Downloaded (1024 KB)

### 3. How to Judge a Horoscope Vol 1 — B.V. Raman
- **Identifier:** `raman-how-to-judge-horoscope-2`
- **OCR File:** `raman-how-to-judge-horoscope-1_djvu.txt`
- **Local Path:** `data/training/raw/judge_horoscope_v1_raman_ocr.txt`
- **URL:** https://archive.org/download/raman-how-to-judge-horoscope-2/raman-how-to-judge-horoscope-1_djvu.txt
- **Status:** Downloaded (456 KB)

### 4. How to Judge a Horoscope Vol 2 — B.V. Raman
- **Identifier:** `raman-how-to-judge-horoscope-2`
- **OCR File:** `raman-how-to-judge-horoscope-2_djvu.txt`
- **Local Path:** `data/training/raw/judge_horoscope_v2_raman_ocr.txt`
- **URL:** https://archive.org/download/raman-how-to-judge-horoscope-2/raman-how-to-judge-horoscope-2_djvu.txt
- **Status:** Downloaded (652 KB)

### 5. Hindu Predictive Astrology — B.V. Raman
- **Identifier:** `hindupredictiveastrologyofbvraman`
- **OCR File:** `Hindu Predictive Astrology of B V Raman_djvu.txt`
- **Local Path:** `data/training/raw/hindu_predictive_astrology_ocr.txt`
- **URL:** https://archive.org/download/hindupredictiveastrologyofbvraman/Hindu%20Predictive%20Astrology%20of%20B%20V%20Raman_djvu.txt
- **Status:** Downloaded (477 KB)

---

## The Astrological Magazine — B.V. Raman (6 volumes)

### 6. Volume 75 (1986)
- **Identifier:** `rojr_the-astrological-magazine-volume-75-monthly-journal-edited-by-b-v-raman-ast`
- **OCR File:** `The Astrological Magazine Volume 75 Monthly Journal Edited by B V Raman Astrology Bangalore 1986 - Raman Publications_djvu.txt`
- **Local Path:** `data/training/raw/astro_magazine_v75_1986_ocr.txt`
- **Status:** Downloaded (1696 KB)

### 7. Volume 76 (1987)
- **Identifier:** `gnrz_the-astrological-magazine-edited-by-b-v-raman-astrology-magazine-volume-76-`
- **OCR File:** `The Astrological Magazine Edited by B V Raman Astrology Magazine Volume 76 Monthly Bangalore 1987 - Raman Publications_djvu.txt`
- **Local Path:** `data/training/raw/astro_magazine_v76_1987_ocr.txt`
- **Status:** Downloaded (2046 KB)

### 8. Volume 77 (1988)
- **Identifier:** `mjii_the-astrological-magazine-volume-77-monthly-magazine-edited-by-bangalore-ve`
- **OCR File:** `The Astrological Magazine Volume 77 Monthly Magazine Edited By Bangalore Venkata Raman Astrology Bangalore 1988 - Raman Publications_djvu.txt`
- **Local Path:** `data/training/raw/astro_magazine_v77_1988_ocr.txt`
- **Status:** Downloaded (3199 KB)

### 9. Volume 78 Issue 1 (January 1989) ⭐ best magazine
- **Identifier:** `axus_the-astrological-magazine-volume-78-issue-1-january-monthly-magazine-1989-e`
- **OCR File:** `The Astrological Magazine Volume 78 Issue 1 January Monthly Magazine 1989 Edited by Bangalore Venkata Raman English Sanskrit Astrology Bangalore - Raman Publications_djvu.txt`
- **Local Path:** `data/training/raw/astro_magazine_v78_1989_ocr.txt`
- **Status:** Downloaded (3641 KB)

### 10. Volume 79 Issue 1 (January 1990)
- **Identifier:** `njqv_the-astrological-magazine-editor-bangalore-venkata-raman-astrology-magazine`
- **OCR File:** `The Astrological Magazine Editor Bangalore Venkata Raman Astrology Magazine Volume 79 Issue 1 January Monthly 1990 Bangalore - The Astrological Magazine_djvu.txt`
- **Local Path:** `data/training/raw/astro_magazine_v79_1990_ocr.txt`
- **Status:** Downloaded (3589 KB)

### 11. Volume 80 Issue 1 — World Trends 1991-92
- **Identifier:** `lpyj_the-astrological-magazine-world-trends-and-tensions-in-1991-92-b-v-raman-vo`
- **OCR File:** `The Astrological Magazine World Trends And Tensions In 1991-92 B V Raman Volume 80 Issue 1 Monthly Magazine 1991 Bangalore - Raman Publications_djvu.txt`
- **Local Path:** `data/training/raw/astro_magazine_v80_1991_ocr.txt`
- **Status:** Downloaded (3653 KB)

---

## Removed Sources

The following sources were originally identified but **removed** from `ocr_sources.py`:

### Unavailable (DRM / wrong language)

| Title | Reason |
|---|---|
| Hindu Predictive Astrology (1938 original) — `hindupredictivea00bvra` | DRM-locked (Controlled Digital Lending). Returns HTTP 401. Replaced with `hindupredictiveastrologyofbvraman` (item #5 above) |
| Hindu Predictive Astrology (Raman Pub reprint) — `vTBL_hindu-predictive-astrology...` | OCR is in Devanagari/Sanskrit script, not English. Useless for the English parser |
| Light on Life — `lightonlifeintro00defo` | DRM-locked (Controlled Digital Lending). Returns HTTP 401. No public English alternative found |

### Dropped after format analysis

| Title | Reason |
|---|---|
| Three Hundred Important Combinations (1947 ed.) — `314068300ThreeHundredImportantCombinationsOfBVRaman1947Ed` | **Zero biographical event content** (`married`=0, `died`=7 stray words). Book is a yoga catalog teaching pattern recognition; example charts have no documented life outcomes. Useless for event-prediction training |
| Three Hundred Important Combinations (Vedic Astrology ed.) — `ThreeHundredImportantCombinationsInVedicAstrology` | Same as above — different edition of the same book, identical zero-event problem |

---

## Summary

| Category | Count | Total Size | Est. Samples | Parser Effort |
|----------|-------|-----------|-------------|---------------|
| Books (Raman + Santhanam) | 5 | ~3.3 MB | 220-340 | Low–Medium |
| Astrological Magazine | 6 | ~17.8 MB | 150-300 | High (LLM-assisted) |
| **Total active** | **11** | **~21.1 MB** | **~370-640** | |

## Format Clusters (for parser planning)

Each book falls into one of three parser-effort clusters based on its OCR structure:

| Cluster | Books | Format | Parser Strategy |
|---------|-------|--------|-----------------|
| **A. Biographical narrative** | #1 Notable Horoscopes | `No. X.— NAME` blocks with structured `Birth Details` + life-event paragraphs | ✅ Existing parser |
| **B. Technique illustration** | #2 Santhanam, #3 Raman v1, #4 Raman v2 | `Chart No. X.—Born on DD-MM-YYYY` inline within technique prose | New parser variant — Cluster B |
| **C. Numbered case sketches** | #5 Hindu Predictive Astrology | `N. Birth Data:—Male, Born on...` + `General Remarks:—events` | Minor parser tweak (Cluster A delimiter swap) |
| **D. Magazine articles** | #6–11 Astro Magazine | Charts scattered in articles, no consistent structure | LLM-assisted extraction |

## Parser Implementation Order (effort × yield)

1. **#5 Hindu Predictive Astrology** — Cluster C, quick win, ~30-50 samples (1-2 days)
2. **#2 Santhanam** — Cluster B, highest single-book yield, ~60-100 samples (3-5 days)
3. **#3 + #4 Raman v1/v2** — reuse Cluster B parser, ~30-60 combined (1-2 days)
4. **#9 Magazine v78 (best)** — LLM probe, ~40-80 samples (1 week)
5. **#6, #7, #8, #10, #11 — remaining magazines** — only if v78 probe succeeds

**Realistic 4-week target:** ~280-490 new samples → dataset grows from 108 to ~390-600.

## Notes

- Items #3 and #4 are both hosted under the same Archive.org identifier (Vol 1 and Vol 2 as separate files).
- K.N. Rao books are NOT on Archive.org (still in copyright, published by Vani Publications). Would require purchase + custom OCR.
- Magazine volumes are single issues, not complete annual compilations. Expect 20-50 case studies per volume.
- All `*_ocr.txt` files in `data/training/raw/` are gitignored due to size; track via DVC if reproducibility is required.
