# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **toy design studio** repository ("tasarım" = design). It produces manufacturing-ready files for two-layer educational children's puzzles: a top layer with figure-shaped pockets cut out, glued onto a flat bottom layer. Each theme ships four production files: a UV-print alignment template (1:1 PDF, outer frame contour only), a top-layer UV artwork PDF with 2 mm bleed on every edge, a bottom-layer shadow-print PDF (piece silhouettes inset 0.4 mm, same bleed) so children can match pieces to pockets, and a laser-cutting DXF containing both layers. No white-ink underbase file is used.

Each theme is a self-contained generator; themes do not import from one another. Copy an existing theme to start a new one.

Known facts:

- **Remote**: https://github.com/huseyinkar37-ops/Claude-tasar-m (public)
- **Default branch**: `main`

## Repository Layout

```
temalar/
  araclar/            # Tema 01 — vehicles (8 pieces across sky / land / sea bands)
  deniz_canlilari/    # Tema 02 — sea creatures (8 pieces across depth bands)
  is_makineleri/      # Tema 03 — construction machines (8 pieces across dig / haul / road bands)
    olustur.py        # self-contained generator for the theme
    README.md         # Turkish production notes for the theme
    varlik/           # brand assets (zoziva_logo.png, transparent PNG)
    cikti/            # generated output — PDFs, DXF, preview PNGs (committed)
```

All themes share the same script skeleton (see Architecture); they differ in how piece contours are produced, the theme-specific detail/decor helpers, and drawing style. `araclar` is the original template. `deniz_canlilari` and `is_makineleri` use a `TEMA = "..."` constant so output filenames derive from one place — prefer that pattern for new themes over the hardcoded filenames still in `araclar`.

Two ways a theme can define its pieces:
- **Vector-drawn** (`araclar`, `is_makineleri`): each `kontur_*()` composes shapely primitives; printed detail is hand-drawn vector art. Deps: `ezdxf cairosvg shapely`. `is_makineleri` uses a `YERLESIM` table `(name, cx, cy, class, kontur_fn)` and draws each machine relative to its own `(cx, cy)` center, so pieces move by editing the table.
- **Image-silhouette + vector trace** (`deniz_canlilari`): each piece comes from a reference PNG in `varlik/<piece>.png`. `goruntu_cikar()` keys out the border-connected white background (interior whites preserved), traces the silhouette to ONE chunky closed contour (morphological close thickens thin protrusions for wood strength), then **color-traces the image to vector** (`K_RENK`-color quantize → per-color region paths, darkest palette entry drawn last as the outline) placed in the same frame and clipped to that contour — so the print is pure vector and still derives from the one cut polygon. Placement/size/thickening live in a `YERLESIM` table `(name, cx, cy, height_mm, kapa, ac, class)`. Extra deps: `pillow numpy scikit-image scipy`. To restyle a creature, swap its PNG and rerun.

## Communication

- Communicate with the user in Turkish (Türkçe): all conversation, explanations, and summaries should be written in Turkish. This is the repository owner's explicit preference.
- File names, code identifiers, comments, and each theme's `README.md` are also in Turkish (e.g. `olustur.py`, `kontur_balon`, `cikti/`). This `CLAUDE.md` is the exception — keep it in English. Follow the Turkish convention for new themes.

## Commands

```bash
pip install ezdxf cairosvg shapely            # base deps (Python 3.11+)
pip install pillow numpy scikit-image scipy   # extra deps for image-silhouette themes (deniz_canlilari)
cd temalar/<tema> && python3 olustur.py        # regenerate all production files into cikti/
```

There is no test framework; each generator's `dogrula()` self-validates the layout on every run (piece-to-piece, piece-to-edge, and notch clearances) and prints warnings on violations. Treat those warnings as failures. `main()` prints "Yerleşim doğrulandı" when the layout is clean, then lists each piece's bounding-box size.

## Architecture

Each `temalar/<tema>/olustur.py` follows the same top-to-bottom structure:

1. **Base measures** — `W, H = 320, 180`, `BLEED = 2`, `CORNER_R = 8`, `MIN_GAP = 7.5`, `MIN_EDGE = 6` (identical across themes); output paths and `LOGO_PNG`.
2. **Geometry primitives** — `elips` / `daire` / `kapsul` / `kutu` / `cokgen` build shapely shapes; `birlesim(parcalar, kapa, ac)` unions a list and applies morphological closing+opening (fillets concave/convex corners, bridges small gaps, prunes slivers), returning ONE exterior ring. That same polygon feeds both the SVG artwork and the DXF polylines, so print and cut can never drift apart. `cerceve_poly()` is the rounded outer frame.
3. **Piece contours** — one `kontur_*()` per piece, each returning a single closed contour (lasers cut the outer outline only — no holes). Results are collected into a module-level `PARCALAR` registry of `(name, polygon, class)` tuples that the validator, SVG, and DXF all iterate.
4. **Finger notches** — `_yuva_hesapla()` places a half-moon crescent (`YUVA_R` ≈ 5.5 mm) on each pocket's open side.
5. **`dogrula()`** — enforces the clearances using real polygon distances (not bounding boxes) and returns a list of violation strings.
6. **SVG helpers + `tanimlar()`** — gradient/def builders and `_klip()` clipping.
7. **Scene + details** — `sahne_svg()` composes background, decor, and pieces; a per-theme `*_detaylari()` draws printed details (windows, faces, stripes, gradients) clipped to each contour. Decorative background elements must stay outside all piece bounding boxes.
8. **Document builders** — `uret_baski_svg()`, `uret_kalip_svg()`, `uret_golge_svg()`, `uret_dxf()`.
9. **`main()`** — runs `dogrula()`, then renders PDFs/PNGs via cairosvg and the DXF via ezdxf (y-axis flipped to y-up).

Everything is defined in millimeters in SVG-style y-down coordinates. The print/preview path uses y-down; only the DXF output flips to y-up.

Theme-specific helpers live under the shared skeleton, e.g.:
- `araclar`: `teker()` wheels, `hacim()` light/shade volume overlay, `yansima()` reflections, and farm/sky decor (`_agac`, `_ahir`, `_yeldegirmeni`, `_bulut`, `_marti`).
- `deniz_canlilari`: `goz()` / `gulus()` for storybook faces, `hacim()`, and underwater decor (`kabarcik`, `yosun`, `dalli_mercan`, `tup_sunger`, `kaya`, `tarak_kabugu`, `spiral_kabuk`, `mini_yildiz`). Drawing style is storybook (thick dark contours, big glossy eyes, smiling faces, saturated color).

DXF layers (both boards laid out side by side in one file):
- `UST_KATMAN_KESIM` — top layer: outer frame + piece contours + the finger-notch crescents (each cut as a separate closed shape).
- `ALT_KATMAN_KESIM` — flat bottom frame only.
- `YAZI` — non-cut labels (turn this layer off in the laser software).

Print/cut registration: the template (kalıp) PDF is a fixed **320×180** — it is the physical placement jig for the product, so its size must not change. The print PDF is **324×184** with the design centered (design center = page center = 162×92), so printing at 100% scale and centering the print on the 320×180 template overhangs an equal 2 mm bleed on every edge and coincides with the cut. There are deliberately **no** registration marks on the print or template — alignment is purely by centering (marks would otherwise print onto the corner of the board). The geometry already resolves to one 320×180 center, so residual print-shifted-relative-to-cut drift is a production-side scaling/positioning error (print scaled-to-fit instead of 100%, or not centered), not a file error.

Preview PNGs render the notches; the print PDFs never do. Note the exact preview set varies by theme (`araclar` also emits `*_kalip_onizleme.png`); the four core production files are always the same.

## Conventions for New Themes

- Copy an existing `temalar/<tema>/` (start from `araclar`, or `deniz_canlilari` if you want the `TEMA`-constant filename pattern). Keep the four-output contract and file-naming pattern (`<tema>_uv_kalip.pdf`, `<tema>_uv_baski.pdf`, `<tema>_alt_golge.pdf`, `<tema>_lazer_kesim.dxf`).
- Pieces must stay chunky for small hands: roughly 25–40 mm tall, no thin necks. Kerf compensation is deliberately NOT applied (the ~0.2 mm kerf gives the loose pocket fit desired for children).
- Every pocket gets a half-moon finger notch placed on the piece's open side; `dogrula()` checks notches keep ≥4 mm to other pieces and the frame. Turkish • English name labels are printed near each piece and must never overlap a notch. Notches appear in the preview PNG only — never in the print PDFs.
- The `varlik/zoziva_logo.png` brand logo (transparent, brand color `#573720`) is auto-embedded top-right; the script warns and proceeds logo-less if the file is missing.
- Generated `cikti/` output is committed to the repo (the `.gitignore` only excludes `__pycache__/` and `*.pyc`). Regenerate and commit the outputs when geometry changes.
- Always eyeball the generated `*_onizleme.png` after changes — the layout validator catches spacing, not aesthetics.
