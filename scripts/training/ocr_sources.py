"""
OCR source configuration for all Archive.org training data sources.

Each entry maps an Archive.org item to a standardized local filename.
Used by 01b_download_all_ocr.py for bulk downloads.
"""

from __future__ import annotations

SOURCES = [
    # --- Books ---
    {
        "id": "NotableHoroscopesBVR",
        "ocr_file": "Notable Horoscopes_djvu.txt",
        "output_name": "notable_horoscopes_ocr.txt",
        "title": "Notable Horoscopes — B.V. Raman",
        "category": "book",
    },
    {
        "id": "how-to-judge-a-horoscope-r.-santhanam",
        "ocr_file": "How to Judge a Horoscope - R. Santhanam_djvu.txt",
        "output_name": "judge_horoscope_santhanam_ocr.txt",
        "title": "How to Judge a Horoscope — R. Santhanam",
        "category": "book",
    },
    {
        "id": "raman-how-to-judge-horoscope-2",
        "ocr_file": "raman-how-to-judge-horoscope-1_djvu.txt",
        "output_name": "judge_horoscope_v1_raman_ocr.txt",
        "title": "How to Judge a Horoscope Vol 1 — B.V. Raman",
        "category": "book",
    },
    {
        "id": "raman-how-to-judge-horoscope-2",
        "ocr_file": "raman-how-to-judge-horoscope-2_djvu.txt",
        "output_name": "judge_horoscope_v2_raman_ocr.txt",
        "title": "How to Judge a Horoscope Vol 2 — B.V. Raman",
        "category": "book",
    },
    # NOTE: "Three Hundred Important Combinations" (both editions) DROPPED — it is a
    # yoga catalog with zero biographical event data (married=0, died=7 stray words).
    # The book illustrates astrological combinations, not life outcomes. Useless for
    # event-prediction training.
    {
        "id": "hindupredictiveastrologyofbvraman",
        "ocr_file": "Hindu Predictive Astrology of B V Raman_djvu.txt",
        "output_name": "hindu_predictive_astrology_ocr.txt",
        "title": "Hindu Predictive Astrology — B.V. Raman",
        "category": "book",
    },
    # NOTE: Removed sources unavailable due to Archive.org DRM or non-English OCR:
    #   - hindupredictivea00bvra (1938 original) — access-restricted (Controlled Digital Lending)
    #   - vTBL_hindu-predictive-astrology... — Devanagari/Sanskrit OCR, not English
    #   - lightonlifeintro00defo (Light on Life) — access-restricted, no public alternative
    # --- Astrological Magazine volumes ---
    {
        "id": "rojr_the-astrological-magazine-volume-75-monthly-journal-edited-by-b-v-raman-ast",
        "ocr_file": "The Astrological Magazine Volume 75 Monthly Journal Edited by B V Raman Astrology Bangalore 1986 - Raman Publications_djvu.txt",
        "output_name": "astro_magazine_v75_1986_ocr.txt",
        "title": "The Astrological Magazine Vol 75 (1986)",
        "category": "magazine",
    },
    {
        "id": "gnrz_the-astrological-magazine-edited-by-b-v-raman-astrology-magazine-volume-76-",
        "ocr_file": "The Astrological Magazine Edited by B V Raman Astrology Magazine Volume 76 Monthly Bangalore 1987 - Raman Publications_djvu.txt",
        "output_name": "astro_magazine_v76_1987_ocr.txt",
        "title": "The Astrological Magazine Vol 76 (1987)",
        "category": "magazine",
    },
    {
        "id": "mjii_the-astrological-magazine-volume-77-monthly-magazine-edited-by-bangalore-ve",
        "ocr_file": "The Astrological Magazine Volume 77 Monthly Magazine Edited By Bangalore Venkata Raman Astrology Bangalore 1988 - Raman Publications_djvu.txt",
        "output_name": "astro_magazine_v77_1988_ocr.txt",
        "title": "The Astrological Magazine Vol 77 (1988)",
        "category": "magazine",
    },
    {
        "id": "axus_the-astrological-magazine-volume-78-issue-1-january-monthly-magazine-1989-e",
        "ocr_file": "The Astrological Magazine Volume 78 Issue 1 January Monthly Magazine 1989 Edited by Bangalore Venkata Raman English Sanskrit Astrology Bangalore - Raman Publications_djvu.txt",
        "output_name": "astro_magazine_v78_1989_ocr.txt",
        "title": "The Astrological Magazine Vol 78 Issue 1 (Jan 1989)",
        "category": "magazine",
    },
    {
        "id": "njqv_the-astrological-magazine-editor-bangalore-venkata-raman-astrology-magazine",
        "ocr_file": "The Astrological Magazine Editor Bangalore Venkata Raman Astrology Magazine Volume 79 Issue 1 January Monthly 1990 Bangalore - The Astrological Magazine_djvu.txt",
        "output_name": "astro_magazine_v79_1990_ocr.txt",
        "title": "The Astrological Magazine Vol 79 Issue 1 (Jan 1990)",
        "category": "magazine",
    },
    {
        "id": "lpyj_the-astrological-magazine-world-trends-and-tensions-in-1991-92-b-v-raman-vo",
        "ocr_file": "The Astrological Magazine World Trends And Tensions In 1991-92 B V Raman Volume 80 Issue 1 Monthly Magazine 1991 Bangalore - Raman Publications_djvu.txt",
        "output_name": "astro_magazine_v80_1991_ocr.txt",
        "title": "The Astrological Magazine Vol 80 Issue 1 (1991)",
        "category": "magazine",
    },
]
