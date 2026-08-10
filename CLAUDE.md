# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **toy design studio** repository ("tasarım" = design). It produces manufacturing-ready files for two-layer educational children's puzzles: a top layer with vehicle/figure-shaped pockets cut out, glued onto a flat bottom layer. Each theme ships four production files: a UV-print alignment template (1:1 PDF, outer frame contour only), a top-layer UV artwork PDF with 2 mm bleed on every edge, a bottom-layer shadow-print PDF (piece silhouettes inset 0.4 mm, same bleed) so children can match pieces to pockets, and a laser-cutting DXF containing both layers. No white-ink underbase file is used.

Known facts:

- **Remote**: https://github.com/huseyinkar37-ops/Claude-tasar-m (public)
- **Default branch**: `main`

## Communication

- Communicate with the user in Turkish (Türkçe): all conversation, explanations, and summaries should be written in Turkish. This is the repository owner's explicit preference.
- File names, code identifiers, and comments are also in Turkish (e.g. `olustur.py`, `kontur_balon`, `cikti/`). Follow that convention for new themes.

## Commands

```bash
pip install ezdxf cairosvg shapely  # dependencies (Python 3.11+)
pip install numpy scipy scikit-image pillow  # additionally for image-derived themes
cd temalar/<tema> && python3 olustur.py   # regenerate all production files into cikti/
```

There is no test framework; each generator script self-validates its layout on run (piece-to-piece and piece-to-edge clearances) and prints warnings on violations. Treat those warnings as failures.

## Architecture

- `temalar/<tema>/olustur.py` — one self-contained generator per puzzle theme. Everything is defined in millimeters in SVG-style y-down coordinates and emitted as: print PDF (with bleed offset), template PDF, preview PNGs (via cairosvg), and DXF (via ezdxf, y-axis flipped to y-up).
- The core abstraction is shapely-based composition: each piece is built as a **union of primitives** (`kutu`/`elips`/`kapsul`/`cokgen`/`daire`), then `birlesim()` applies morphological closing+opening (fillets concave/convex corners, bridges sub-2.6 mm gaps, prunes sub-1.4 mm slivers) and returns ONE exterior ring. That same polygon feeds both the SVG artwork and the DXF polylines, so print and cut can never drift apart.
- Each puzzle piece is a `kontur_*()` function returning **one closed contour** (lasers cut the outer outline only — no holes). Printed details (windows, stripes, text, gradients, `hacim()` light/shade overlays, `teker()` wheels) are drawn separately in `arac_detaylari()`, clipped to the contour. Decorative background elements must stay outside all piece bounding boxes.
- Two kinds of theme exist. **Drawn themes** (`araclar`, `deniz_canlilari`) compose the scene
  from primitives as described above. **Image-derived themes** (`dinozorlar`) take a fixed
  illustration as the print and *extract* the piece contours from it by segmentation
  (plaque masking → dark-outline flood fill → morphological opening → nearest-marker
  watershed → marching squares → mm polygons). For those, the board takes the artwork's
  aspect ratio rather than 320×180, the source composition rarely satisfies the clearance
  rules, so contours get trimmed equally on both sides of each too-close pair, and print
  resolution must be checked (source px ÷ board mm × 25.4 ≥ 150 dpi).
- Layout constants that matter: 320×180 mm finished size, 2 mm bleed, 8 mm rounded corners, ≥7.5 mm wall between pieces, ≥6 mm to outer edges, no cut feature narrower than ~4 mm (wood strength). `dogrula()` enforces the clearances with real polygon distances (not bounding boxes).
- DXF layers: `UST_KATMAN_KESIM` (top layer: frame + piece contours), `ALT_KATMAN_KESIM` (flat bottom frame), `YAZI` (non-cut labels). Both boards are laid out side by side in one file.

## Conventions for New Themes

- Copy `temalar/araclar/` as the starting point; keep the four-output contract and file-naming pattern (`<tema>_uv_kalip.pdf`, `<tema>_uv_baski.pdf`, `<tema>_alt_golge.pdf`, `<tema>_lazer_kesim.dxf`).
- Pieces must stay chunky for small hands: roughly 25–40 mm tall, no thin necks. Kerf compensation is deliberately NOT applied (the ~0.2 mm kerf gives the loose pocket fit desired for children).
- Every pocket gets a half-moon finger notch (`YUVA_R` = 5.5 mm crescent, cut as a separate closed shape in the top-layer DXF) placed on the piece's open side; `dogrula()` checks notches keep ≥4 mm to other pieces and the frame. Turkish • English name labels are printed near each piece and must never overlap a notch. Notches appear in the preview PNG only — never in the print PDFs.
- Always eyeball the generated `*_onizleme.png` after changes — the layout validator catches spacing, not aesthetics.
