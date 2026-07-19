# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **toy design studio** repository ("tasarım" = design). It produces manufacturing-ready files for two-layer educational children's puzzles: a top layer with vehicle/figure-shaped pockets cut out, glued onto a flat bottom layer. Each theme ships three production files: a UV-print alignment template (1:1 PDF), a UV-print artwork PDF with 2 mm bleed on every edge, and a laser-cutting DXF containing both layers.

Known facts:

- **Remote**: https://github.com/huseyinkar37-ops/Claude-tasar-m (public)
- **Default branch**: `main`

## Communication

- Communicate with the user in Turkish (Türkçe): all conversation, explanations, and summaries should be written in Turkish. This is the repository owner's explicit preference.
- File names, code identifiers, and comments are also in Turkish (e.g. `olustur.py`, `kontur_balon`, `cikti/`). Follow that convention for new themes.

## Commands

```bash
pip install ezdxf cairosvg          # dependencies (Python 3.11+)
cd temalar/<tema> && python3 olustur.py   # regenerate all production files into cikti/
```

There is no test framework; each generator script self-validates its layout on run (piece-to-piece and piece-to-edge clearances) and prints warnings on violations. Treat those warnings as failures.

## Architecture

- `temalar/<tema>/olustur.py` — one self-contained generator per puzzle theme. Everything is defined in millimeters in SVG-style y-down coordinates and emitted as: print PDF (with bleed offset), template PDF, preview PNGs (via cairosvg), and DXF (via ezdxf, y-axis flipped to y-up).
- The core abstraction is the `Yol` path builder (move/line/cubic/arc). It records both an SVG path string **and** a sampled polyline from the same geometry, so the printed artwork and the DXF cut contours can never drift apart.
- Each puzzle piece is a `kontur_*()` function returning **one closed contour** (lasers cut the outer outline only). Printed details (windows, stripes, text) are drawn separately in `arac_detaylari()`, clipped to the contour. Decorative background elements must stay outside all piece bounding boxes.
- Layout constants that matter: 320×180 mm finished size, 2 mm bleed, 8 mm rounded corners, ≥7.5 mm wall between pieces, ≥6 mm to outer edges, no cut feature narrower than ~4 mm (wood strength). `dogrula()` enforces the clearances.
- DXF layers: `UST_KATMAN_KESIM` (top layer: frame + piece contours), `ALT_KATMAN_KESIM` (flat bottom frame), `YAZI` (non-cut labels). Both boards are laid out side by side in one file.

## Conventions for New Themes

- Copy `temalar/araclar/` as the starting point; keep the three-output contract and file-naming pattern (`<tema>_uv_kalip.pdf`, `<tema>_uv_baski.pdf`, `<tema>_lazer_kesim.dxf`).
- Pieces must stay chunky for small hands: roughly 25–40 mm tall, no thin necks. Kerf compensation is deliberately NOT applied (the ~0.2 mm kerf gives the loose pocket fit desired for children).
- Always eyeball the generated `*_onizleme.png` after changes — the layout validator catches spacing, not aesthetics.
