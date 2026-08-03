# -*- coding: utf-8 -*-
"""
İki katmanlı "Deniz Canlıları" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Görseller elle çizilmiyor; varlik/kaynak/ altındaki kaynak çizimlerden
siluet.py ile silueti, kesim.py ile üretime uygun kesim konturu çıkarılıyor.
Baskı, her parçanın kesim konturuna kırpılmış çizimi + dışında beyaz sticker
payı olarak kuruluyor.

Çıktılar (cikti/):
  1. deniz_canlilari_uv_kalip.pdf    – UV hizalama kalıbı (yalnız dış çerçeve, 1:1)
  2. deniz_canlilari_uv_baski.pdf    – ÜST katman baskısı, 2 mm taşmalı (324x184)
  3. deniz_canlilari_alt_golge.pdf   – ALT katman gölge baskısı (324x184)
  4. deniz_canlilari_lazer_kesim.dxf – Lazer: ÜST (cepli) + ALT (düz) panolar
  5. deniz_canlilari_onizleme.png    – kontrol önizlemesi (yuvalar görünür)

Çalıştırma:  python3 olustur.py
"""
import base64
import io
import os

import cairosvg
import ezdxf
import numpy as np
from PIL import Image
from shapely.affinity import translate as s_tasi
from shapely.geometry import Point, Polygon, box as s_kutu
from shapely.ops import nearest_points

import kesim
import siluet

# ---------------------------------------------------------------- temel ölçüler
W, H = 320.0, 180.0
BLEED = 2.0
CORNER_R = 8.0
MIN_GAP = 7.5
MIN_EDGE = 6.0
YUVA_R = 5.5
GOLGE_ICE = 0.4              # alt katman gölgesinin içe kaçıklığı

KLASOR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KLASOR, "cikti")
LOGO_PNG = os.path.join(KLASOR, "varlik", "zoziva_logo.png")
TEMA = "deniz_canlilari"
FONT = "DejaVu Sans"

# ---------------------------------------------------------------- yerleşim
# Parça merkezleri (mm). 4 sütun x 2 satır; etiketler parçanın altına gelir.
YERLESIM = {
    "yunus":        (48.0, 44.0),
    "denizanasi":   (124.0, 44.0),
    "kaplumbaga":   (204.0, 44.0),
    "balik":        (278.0, 44.0),
    "denizati":     (40.0, 128.0),
    "yengec":       (124.0, 128.0),
    "ahtapot":      (206.0, 128.0),
    "denizyildizi": (278.0, 128.0),
}

ETIKETLER = {
    "yunus":        ("Yunus", "Dolphin"),
    "denizanasi":   ("Denizanası", "Jellyfish"),
    "denizati":     ("Denizatı", "Seahorse"),
    "kaplumbaga":   ("Kaplumbağa", "Sea Turtle"),
    "balik":        ("Balık", "Fish"),
    "ahtapot":      ("Ahtapot", "Octopus"),
    "yengec":       ("Yengeç", "Crab"),
    "denizyildizi": ("Denizyıldızı", "Starfish"),
}

# Parmak yuvasının hangi yönde açılacağı (parça merkezine göre birim yön)
YUVA_YON = {
    "yunus":        (-1.0, 0.35),
    "denizanasi":   (-1.0, -0.25),
    "kaplumbaga":   (0.15, -1.0),
    "balik":        (0.2, -1.0),
    "denizati":     (-1.0, 0.0),
    "yengec":       (-1.0, -0.3),
    "ahtapot":      (-1.0, -0.35),
    "denizyildizi": (1.0, 0.15),
}


# ---------------------------------------------------------------- parça hazırlığı
def parca_yukle(ad):
    """Kesim konturunu ve baskıya girecek RGBA görseli panoya yerleştirir."""
    r = kesim.isle(ad)
    mm_px = r["mm_px"]
    kes_m, ciz_m, rgb = r["kesim"], r["maske"], r["rgb"]

    # baskı yüzü: çizim varsa çizim rengi, kesim payı kaldıysa beyaz sticker
    h, w = kes_m.shape
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., :3] = 255
    ciz = ciz_m & kes_m
    rgba[..., :3][ciz] = rgb[ciz]
    rgba[..., 3] = np.where(kes_m, 255, 0)

    kontur = r["kesim_kontur"]
    x0, y0, x1, y1 = kontur.bounds
    cx, cy = YERLESIM[ad]
    dx, dy = cx - (x0 + x1) / 2.0, cy - (y0 + y1) / 2.0
    return {
        "ad": ad,
        "kontur": s_tasi(kontur, dx, dy),
        "rgba": Image.fromarray(rgba),
        "gorsel_kutu": (dx, dy, w * mm_px, h * mm_px),
        "budanan_pay": r["budanan_pay"],
        "dpi": r["dpi"],
    }


def cerceve_poly():
    return s_kutu(CORNER_R, CORNER_R, W - CORNER_R,
                  H - CORNER_R).buffer(CORNER_R, quad_segs=16)


def yuva_hesapla(parcalar):
    """Her parçanın açık tarafına hilal biçimli parmak yuvası oturtur."""
    yuvalar = {}
    for p in parcalar:
        poly = p["kontur"]
        c = poly.centroid
        ux, uy = YUVA_YON[p["ad"]]
        n = (ux ** 2 + uy ** 2) ** 0.5
        hedef = Point(c.x + ux / n * 60, c.y + uy / n * 60)
        merkez = nearest_points(poly.exterior, hedef)[0]
        hilal = siluet.Polygon(Point(merkez.x, merkez.y)
                               .buffer(YUVA_R, quad_segs=24).exterior)
        hilal = hilal.difference(poly)
        if hilal.is_empty:
            continue
        if hilal.geom_type == "MultiPolygon":
            hilal = max(hilal.geoms, key=lambda g: g.area)
        yuvalar[p["ad"]] = Polygon(hilal.exterior).simplify(
            0.05, preserve_topology=True)
    return yuvalar


# ---------------------------------------------------------------- doğrulama
def dogrula(parcalar, yuvalar):
    hatalar = []
    kenar = cerceve_poly().exterior
    for p in parcalar:
        d = p["kontur"].distance(kenar)
        if d < MIN_EDGE:
            hatalar.append(f"{p['ad']}: dış kenara {d:.1f} mm "
                           f"(en az {MIN_EDGE} mm)")
    for i in range(len(parcalar)):
        for j in range(i + 1, len(parcalar)):
            a, b = parcalar[i], parcalar[j]
            d = a["kontur"].distance(b["kontur"])
            if d <= 0:
                hatalar.append(f"{a['ad']} ile {b['ad']} ÇAKIŞIYOR")
            elif d < MIN_GAP:
                hatalar.append(f"{a['ad']}–{b['ad']} arası {d:.1f} mm "
                               f"(en az {MIN_GAP} mm)")
    for ad, hilal in yuvalar.items():
        sahip = next(p["kontur"] for p in parcalar if p["ad"] == ad)
        if hilal.is_empty or hilal.area < 8:
            hatalar.append(f"{ad} yuvası çok küçük ({hilal.area:.1f} mm²)")
        if sahip.distance(hilal) > 0.15:
            hatalar.append(f"{ad} yuvası kontura bitişik değil")
        if hilal.distance(kenar) < 4.0:
            hatalar.append(f"{ad} yuvası dış kenara "
                           f"{hilal.distance(kenar):.1f} mm")
        for p in parcalar:
            if p["ad"] != ad and hilal.distance(p["kontur"]) < 4.0:
                hatalar.append(f"{ad} yuvası {p['ad']} parçasına "
                               f"{hilal.distance(p['kontur']):.1f} mm")
    return hatalar


# ---------------------------------------------------------------- SVG
def yol_svg(poly):
    pts = list(poly.exterior.coords)[:-1]
    d = f"M {pts[0][0]:.3f} {pts[0][1]:.3f} " + " ".join(
        f"L {x:.3f} {y:.3f}" for x, y in pts[1:])
    return d + " Z"


def png_uri(im):
    tmp = io.BytesIO()
    im.save(tmp, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(tmp.getvalue()).decode()


def tanimlar():
    return (
        '<defs>'
        '<linearGradient id="su" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="{-BLEED}" x2="0" y2="{H + BLEED}">'
        '<stop offset="0" stop-color="#5CCDF4"/>'
        '<stop offset="0.45" stop-color="#2AA3DC"/>'
        '<stop offset="1" stop-color="#11719F"/></linearGradient>'
        '<linearGradient id="kum" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="{H - 24}" x2="0" y2="{H + BLEED}">'
        '<stop offset="0" stop-color="#F7DC8E"/>'
        '<stop offset="1" stop-color="#DFB055"/></linearGradient>'
        '<radialGradient id="isik" gradientUnits="userSpaceOnUse" '
        f'cx="{W * 0.5}" cy="{-BLEED}" r="{W * 0.55}">'
        '<stop offset="0" stop-color="#EAFBFF" stop-opacity="0.55"/>'
        '<stop offset="1" stop-color="#EAFBFF" stop-opacity="0"/>'
        '</radialGradient>'
        '</defs>')


def zemin(e):
    e.append(f'<rect x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" '
             f'height="{H + 2 * BLEED}" fill="url(#su)"/>')
    e.append(f'<rect x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" '
             f'height="{H + 2 * BLEED}" fill="url(#isik)"/>')
    e.append(f'<path d="M {-BLEED} {H - 12} '
             f'C {W * 0.25} {H - 22} {W * 0.6} {H - 6} {W + BLEED} {H - 16} '
             f'L {W + BLEED} {H + BLEED} L {-BLEED} {H + BLEED} Z" '
             f'fill="url(#kum)"/>')


def _etiket_kutusu(ad, poly):
    tr, en = ETIKETLER[ad]
    x0, y0, x1, y1 = poly.bounds
    cx = (x0 + x1) / 2.0
    y = y1 + 6.4
    gen = len(f"{tr} • {en}") * 1.62 + 6.0
    return s_kutu(cx - gen / 2, y - 3.6, cx + gen / 2, y + 3.0)


def suslemeler(e, parcalar):
    """Dekoratif ögeler — hiçbiri parça ya da etiket alanına girmez."""
    yasak = [p["kontur"].buffer(3.0) for p in parcalar]
    yasak += [_etiket_kutusu(p["ad"], p["kontur"]).buffer(2.0)
              for p in parcalar]

    def guvenli(geom):
        return not any(geom.intersects(k) for k in yasak)

    # yüzeyden inen ışık huzmeleri (sütun aralarında)
    for x, gen, boy, egim in [(80, 12, 100, 5), (150, 14, 110, 6),
                              (238, 11, 95, 4)]:
        huzme = Polygon([(x, -BLEED), (x + gen, -BLEED),
                         (x + gen + egim, boy), (x + egim, boy)])
        if guvenli(huzme):
            e.append(f'<path d="{yol_svg(huzme)}" fill="#EAFBFF" '
                     f'opacity="0.13"/>')

    # uzaktaki balık sürüsü (orta bant)
    for bx, by, s in [(96, 92, 1.0), (108, 84, 0.8), (104, 100, 0.9),
                      (176, 96, 1.0), (188, 88, 0.85), (184, 104, 0.75),
                      (256, 94, 0.95), (268, 86, 0.8), (264, 102, 0.85)]:
        gov = Point(bx, by).buffer(2.4 * s)
        if not guvenli(gov.buffer(2.0)):
            continue
        e.append(f'<path d="M {bx - 3.4 * s:.1f} {by:.1f} '
                 f'q {3.4 * s:.1f} {-2.2 * s:.1f} {6.8 * s:.1f} 0 '
                 f'q {-3.4 * s:.1f} {2.2 * s:.1f} {-6.8 * s:.1f} 0 Z" '
                 f'fill="#0E5F8C" opacity="0.20"/>')
        e.append(f'<path d="M {bx + 3.2 * s:.1f} {by:.1f} '
                 f'l {2.4 * s:.1f} {-1.6 * s:.1f} l 0 {3.2 * s:.1f} Z" '
                 f'fill="#0E5F8C" opacity="0.20"/>')

    # kabarcıklar
    for x, y, r in [(88, 24, 2.2), (92, 17, 1.4), (80, 32, 1.1),
                    (166, 30, 2.0), (172, 22, 1.3), (160, 40, 1.1),
                    (247, 34, 2.4), (252, 26, 1.5), (240, 44, 1.2),
                    (86, 150, 2.0), (90, 142, 1.3), (168, 62, 1.6),
                    (10, 96, 2.0), (312, 96, 2.0), (14, 88, 1.3),
                    (308, 104, 1.4), (150, 118, 1.5), (200, 74, 1.4)]:
        d = Point(x, y).buffer(r)
        if guvenli(d):
            e.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#FFFFFF" '
                     f'opacity="0.30"/>')
            e.append(f'<circle cx="{x - r * 0.3}" cy="{y - r * 0.3}" '
                     f'r="{r * 0.32}" fill="#FFFFFF" opacity="0.55"/>')

    # zemindeki mercan ve yosunlar
    for x, boy, egim, renk in [(14, 24, 5, "#37A45C"), (308, 22, -4, "#37A45C"),
                               (96, 20, 3, "#2E8F51"), (232, 22, -3, "#2E8F51"),
                               (170, 17, 2, "#37A45C")]:
        sap = s_kutu(x - 4, H - 10 - boy, x + 4, H - 8)
        if guvenli(sap):
            e.append(f'<path d="M {x} {H - 8} '
                     f'C {x + egim} {H - 8 - boy * 0.4} '
                     f'{x - egim} {H - 8 - boy * 0.7} '
                     f'{x + egim * 0.5} {H - 8 - boy}" stroke="{renk}" '
                     f'stroke-width="2.6" fill="none" stroke-linecap="round" '
                     f'opacity="0.85"/>')
    # mercan öbekleri — düz gri leke yerine dallı siluet
    for x, s, renk in [(56, 1.0, "#E08A6A"), (206, 0.85, "#D9789E"),
                       (286, 1.1, "#E08A6A"), (128, 0.8, "#D9789E")]:
        obek = s_kutu(x - 6 * s, H - 8 - 12 * s, x + 6 * s, H - 6)
        if not guvenli(obek):
            continue
        for dx, dy, kal in [(0, 12, 2.4), (-4, 8.5, 1.9), (4, 9.5, 1.9),
                            (-6.5, 5.5, 1.5), (6.5, 6, 1.5)]:
            e.append(f'<path d="M {x} {H - 7} '
                     f'Q {x + dx * s * 0.5:.1f} {H - 7 - dy * s * 0.6:.1f} '
                     f'{x + dx * s:.1f} {H - 7 - dy * s:.1f}" '
                     f'stroke="{renk}" stroke-width="{kal * s:.1f}" '
                     f'fill="none" stroke-linecap="round" opacity="0.7"/>')


def etiket(e, ad, poly):
    tr, en = ETIKETLER[ad]
    x0, y0, x1, y1 = poly.bounds
    cx = (x0 + x1) / 2.0
    y = y1 + 6.4
    metin = f"{tr} • {en}"
    gen = len(metin) * 1.62 + 6.0
    e.append(f'<rect x="{cx - gen / 2:.2f}" y="{y - 3.6:.2f}" width="{gen:.2f}" '
             f'height="6.6" rx="3.3" fill="#FFFFFF" opacity="0.92"/>')
    e.append(f'<text x="{cx:.2f}" y="{y + 1.15:.2f}" font-family="{FONT}" '
             f'font-size="3.5" font-weight="bold" fill="#14496B" '
             f'text-anchor="middle">{metin}</text>')


def logo_ciz(e):
    if not os.path.exists(LOGO_PNG):
        return
    im = Image.open(LOGO_PNG).convert("RGBA")
    gen = 30.0
    boy = gen * im.size[1] / im.size[0]
    e.append(f'<image x="{W - gen - 8:.2f}" y="6" width="{gen:.2f}" '
             f'height="{boy:.2f}" href="{png_uri(im)}" opacity="0.95"/>')


def parcalari_ciz(e, parcalar):
    for p in parcalar:
        dx, dy, gw, gh = p["gorsel_kutu"]
        e.append(f'<image x="{dx:.3f}" y="{dy:.3f}" width="{gw:.3f}" '
                 f'height="{gh:.3f}" href="{png_uri(p["rgba"])}"/>')


def sahne_svg(parcalar, yuvalar, yuva_goster=False):
    e = [tanimlar()]
    zemin(e)
    suslemeler(e, parcalar)
    parcalari_ciz(e, parcalar)
    for p in parcalar:
        etiket(e, p["ad"], p["kontur"])
    logo_ciz(e)
    if yuva_goster:
        for hilal in yuvalar.values():
            e.append(f'<path d="{yol_svg(hilal)}" fill="#0A2438" '
                     f'opacity="0.30"/>')
    return "".join(e)


def svg_belge(icerik, tasmali=True):
    if tasmali:
        w, h, ox = W + 2 * BLEED, H + 2 * BLEED, BLEED
    else:
        w, h, ox = W, H, 0.0
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            f'<g transform="translate({ox},{ox})">{icerik}</g></svg>')


# ---------------------------------------------------------------- çıktılar
def uret_baski(parcalar, yuvalar):
    svg = svg_belge(sahne_svg(parcalar, yuvalar))
    yol = os.path.join(OUT, f"{TEMA}_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=svg.encode(), write_to=yol)
    return yol


def uret_onizleme(parcalar, yuvalar, px=2400):
    svg = svg_belge(sahne_svg(parcalar, yuvalar, yuva_goster=True))
    yol = os.path.join(OUT, f"{TEMA}_onizleme.png")
    cairosvg.svg2png(bytestring=svg.encode(), write_to=yol, output_width=px)
    return yol


def uret_kalip(parcalar):
    e = [f'<path d="{yol_svg(cerceve_poly())}" fill="none" stroke="#000000" '
         f'stroke-width="0.25"/>',
         f'<text x="{W / 2}" y="{H / 2}" font-family="{FONT}" font-size="5" '
         f'fill="#000000" text-anchor="middle">{TEMA} — UV hizalama kalıbı '
         f'{W:.0f}x{H:.0f} mm</text>']
    yol = os.path.join(OUT, f"{TEMA}_uv_kalip.pdf")
    cairosvg.svg2pdf(bytestring=svg_belge("".join(e), tasmali=False).encode(),
                     write_to=yol)
    return yol


def uret_golge(parcalar):
    e = [f'<rect x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" '
         f'height="{H + 2 * BLEED}" fill="#FFFFFF"/>']
    for p in parcalar:
        g = p["kontur"].buffer(-GOLGE_ICE, quad_segs=12)
        if g.is_empty:
            continue
        if g.geom_type == "MultiPolygon":
            g = max(g.geoms, key=lambda x: x.area)
        e.append(f'<path d="{yol_svg(Polygon(g.exterior))}" fill="#1D5C86" '
                 f'opacity="0.32"/>')
    yol = os.path.join(OUT, f"{TEMA}_alt_golge.pdf")
    cairosvg.svg2pdf(bytestring=svg_belge("".join(e)).encode(), write_to=yol)
    return yol


def uret_dxf(parcalar, yuvalar):
    doc = ezdxf.new("R2010", setup=True)
    msp = doc.modelspace()
    for ad, renk in [("UST_KATMAN_KESIM", 1), ("ALT_KATMAN_KESIM", 5),
                     ("YAZI", 3)]:
        doc.layers.add(ad, color=renk)

    ayir = W + 20.0                       # iki pano yan yana

    def poli(poly, dx, katman):
        pts = [(x + dx, H - y) for x, y in poly.exterior.coords]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": katman})

    poli(cerceve_poly(), 0.0, "UST_KATMAN_KESIM")
    for p in parcalar:
        poli(p["kontur"], 0.0, "UST_KATMAN_KESIM")
    for hilal in yuvalar.values():
        poli(hilal, 0.0, "UST_KATMAN_KESIM")
    poli(cerceve_poly(), ayir, "ALT_KATMAN_KESIM")

    for p in parcalar:
        x0, y0, x1, y1 = p["kontur"].bounds
        msp.add_text(ETIKETLER[p["ad"]][0],
                     dxfattribs={"layer": "YAZI", "height": 3.0}
                     ).set_placement(((x0 + x1) / 2, H - y1 - 4))
    msp.add_text("UST KATMAN (cepli)", dxfattribs={"layer": "YAZI",
                                                   "height": 5.0}
                 ).set_placement((6, H + 6))
    msp.add_text("ALT KATMAN (duz)", dxfattribs={"layer": "YAZI",
                                                 "height": 5.0}
                 ).set_placement((ayir + 6, H + 6))
    yol = os.path.join(OUT, f"{TEMA}_lazer_kesim.dxf")
    doc.saveas(yol)
    return yol


# ---------------------------------------------------------------- ana akış
def main():
    os.makedirs(OUT, exist_ok=True)
    parcalar = [parca_yukle(ad) for ad in YERLESIM]
    yuvalar = yuva_hesapla(parcalar)

    hatalar = dogrula(parcalar, yuvalar)
    if hatalar:
        print("UYARI — yerleşim doğrulaması:")
        for h in hatalar:
            print("  •", h)
    else:
        print("Yerleşim doğrulaması temiz "
              f"(parça arası ≥{MIN_GAP} mm, kenara ≥{MIN_EDGE} mm).")

    print(f"\n{'canlı':14}{'en×boy mm':>14}{'dpi':>7}{'budanan':>9}")
    for p in parcalar:
        x0, y0, x1, y1 = p["kontur"].bounds
        print(f"{p['ad']:14}{x1 - x0:7.1f}×{y1 - y0:5.1f}{p['dpi']:7.0f}"
              f"{100 * p['budanan_pay']:8.1f}%")

    print()
    for f in (uret_kalip(parcalar), uret_baski(parcalar, yuvalar),
              uret_golge(parcalar), uret_dxf(parcalar, yuvalar),
              uret_onizleme(parcalar, yuvalar)):
        print("yazıldı:", os.path.relpath(f, KLASOR),
              f"({os.path.getsize(f) / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
