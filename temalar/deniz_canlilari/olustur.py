# -*- coding: utf-8 -*-
"""
İki katmanlı "Deniz Canlıları" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Bu tema, parça çizimlerini `varlik/<canli>.png` referans görsellerinden türetir:
her görselin siluetinden lazer için TEK, tıknaz kapalı kontur çıkarılır (ince
uzantılar morfolojik kapama ile ahşap dayanımına uygun hale getirilir) ve aynı
görsel renk kümeleme ile VEKTÖRE çevrilip (color-trace) bu kontura hizalı
biçimde baskıya çizilir. Böylece baskı ile kesim asla ayrışmaz — kontur hem SVG
kırpma maskesini hem DXF polikline'ını besler; baskı ise saf vektördür (raster yok).

Çıktılar (cikti/):
  1. deniz_canlilari_uv_kalip.pdf   – UV hizalama kalıbı (yalnız dış çerçeve, 1:1)
  2. deniz_canlilari_uv_baski.pdf   – ÜST katman baskısı, 2 mm taşmalı (324x184)
  3. deniz_canlilari_alt_golge.pdf  – ALT katman gölge baskısı (324x184)
  4. deniz_canlilari_lazer_kesim.dxf – Lazer: ÜST (cepli) + ALT (düz) panolar

Çalıştırma:  python3 olustur.py
Bağımlılıklar: ezdxf cairosvg shapely pillow numpy scikit-image scipy
"""
import base64
import math
import os
import random
import struct

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage import measure

from shapely.affinity import scale as s_olcek, translate as s_tasi
from shapely.geometry import Point, Polygon, box as s_kutu
from shapely.ops import nearest_points, unary_union

# ---------------------------------------------------------------- temel ölçüler
W, H = 320.0, 180.0
BLEED = 2.0
CORNER_R = 8.0
MIN_GAP = 7.5
MIN_EDGE = 6.0

KLASOR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KLASOR, "cikti")
VARLIK = os.path.join(KLASOR, "varlik")
LOGO_PNG = os.path.join(VARLIK, "zoziva_logo.png")
TEMA = "deniz_canlilari"

# ---------------------------------------------------------------- geometri araçları
def daire(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=24)


def yol_svg(poly):
    pts = list(poly.exterior.coords)[:-1]
    d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f} " + " ".join(
        f"L {x:.2f} {y:.2f}" for x, y in pts[1:])
    return d + " Z"


def cerceve_poly():
    return s_kutu(CORNER_R, CORNER_R, W - CORNER_R, H - CORNER_R).buffer(CORNER_R, quad_segs=16)

# ---------------------------------------------------------------- görselden vektör
K_RENK = 20            # renk kümeleme paleti (color-trace)
IZ_GEN = 640          # izleme çözünürlüğü (px genişlik)


def _arka_plan(rgb):
    """Kenardan bağlı beyaz bölge = arka plan (iç beyazları korur)."""
    beyaz = (rgb[:, :, 0] > 238) & (rgb[:, :, 1] > 238) & (rgb[:, :, 2] > 238)
    lab, _ = ndimage.label(beyaz)
    kenar = set(lab[0, :]) | set(lab[-1, :]) | set(lab[:, 0]) | set(lab[:, -1])
    kenar.discard(0)
    return np.isin(lab, list(kenar))


def _yumusat_yol(contour, sv, ox, oy):
    """px kontur -> yumuşatılmış -> mm SVG 'd' dizesi."""
    c = measure.approximate_polygon(np.asarray(contour), tolerance=0.9)
    if len(c) < 4:
        c = np.asarray(contour)
    pts = [(col * sv + ox, row * sv + oy) for row, col in c]
    return (f"M {pts[0][0]:.2f} {pts[0][1]:.2f} "
            + " ".join(f"L {x:.2f} {y:.2f}" for x, y in pts[1:]) + " Z")


def goruntu_cikar(ad, cx, cy, hedef_boy, kapa, ac):
    """Referans görselden lazer konturu + renkli vektör çizimi türetir.

    Döner: (poly_mm, vektor)
      poly_mm : lazer/gölge/yuva için tek tıknaz kapalı kontur
      vektor  : dict(dolgu=[(renk,d),...], kontur=[d,...])  mm uzayında
    """
    im0 = Image.open(os.path.join(VARLIK, ad + ".png")).convert("RGB")

    # --- 1) siluet -> lazer konturu (tam çözünürlük)
    rgb0 = np.asarray(im0)
    nesne = ~_arka_plan(rgb0)
    dolu = ndimage.binary_fill_holes(nesne)
    polis = []
    for c in measure.find_contours(dolu.astype(float), 0.5):
        if len(c) < 20:
            continue
        p = Polygon([(x, y) for y, x in c])
        if p.is_valid and p.area > 200:
            polis.append(p)
    if not polis:
        raise RuntimeError("kontur bulunamadı: " + ad)
    birim = unary_union(polis)
    ys, _ = np.where(dolu)
    s = hedef_boy / (ys.max() - ys.min())                       # tam-px -> mm
    birim_s = s_olcek(birim, s, s, origin=(0, 0))
    bx0, by0, bx1, by1 = birim_s.bounds
    tx, ty = cx - (bx0 + bx1) / 2, cy - (by0 + by1) / 2         # görsel kökeni -> mm ofseti
    kap = birim_s.buffer(kapa, quad_segs=12).buffer(-kapa - ac, quad_segs=12).buffer(ac, quad_segs=12)
    if kap.geom_type == "MultiPolygon":
        kap = max(kap.geoms, key=lambda g: g.area)
    poly = s_tasi(Polygon(kap.exterior).simplify(0.15, preserve_topology=True), tx, ty)

    # --- 2) color-trace -> renkli vektör (aynı çerçeveye hizalı)
    k = IZ_GEN / im0.width
    im = im0.resize((round(im0.width * k), round(im0.height * k)), Image.LANCZOS)
    arr = ndimage.median_filter(np.asarray(im), size=(3, 3, 1))  # benek temizliği
    im = Image.fromarray(arr)
    obj = ndimage.binary_fill_holes(~_arka_plan(arr))
    sv = s / k                                                  # iz-px -> mm

    pim = im.quantize(colors=K_RENK, method=Image.MAXCOVERAGE, dither=Image.NONE)
    labels = np.asarray(pim)
    pal = np.asarray(pim.getpalette()[:K_RENK * 3]).reshape(-1, 3)
    kontur_renk = int(np.argmin(pal @ [0.299, 0.587, 0.114]))   # en koyu palet = dış çizgi

    dolgu, kontur_yol = [], []
    for idx in range(K_RENK):
        m = (labels == idx) & obj
        if m.sum() < 25:
            continue
        if idx == kontur_renk:                                  # dış çizgi: delikli, en üstte
            mm = ndimage.binary_closing(m, iterations=1)
            for c in measure.find_contours(mm.astype(float), 0.5):
                if len(c) >= 12:
                    kontur_yol.append(_yumusat_yol(c, sv, tx, ty))
            continue
        renk = "#{:02X}{:02X}{:02X}".format(*pal[idx])          # renk bölgesi
        etq, n = ndimage.label(ndimage.binary_fill_holes(m))
        for li in range(1, n + 1):
            comp = etq == li
            if comp.sum() < 40:
                continue
            cs = measure.find_contours(ndimage.binary_fill_holes(comp).astype(float), 0.5)
            if cs:
                c = max(cs, key=len)
                if len(c) >= 12:
                    dolgu.append((comp.sum(), renk, _yumusat_yol(c, sv, tx, ty)))
    dolgu.sort(key=lambda t: -t[0])                             # büyük alan altta
    vektor = {"dolgu": [(r, d) for _, r, d in dolgu], "kontur": kontur_yol}
    return poly, vektor


# (ad, cx, cy, hedef_boy_mm, kapa, ac, sınıf) — kapa: kapama yarıçapı (tıknazlaştırma)
YERLESIM = [
    ("yunus",        56, 31, 34, 1.8, 0.8, "yuzey"),
    ("denizanasi",  152, 31, 38, 2.4, 0.9, "yuzey"),
    ("balik",       250, 33, 32, 1.8, 0.8, "yuzey"),
    ("denizati",     29, 95, 48, 2.6, 0.9, "orta"),
    ("kaplumbaga",  142, 90, 41, 1.8, 0.8, "orta"),
    ("ahtapot",     256, 96, 42, 2.8, 0.9, "orta"),
    ("yengec",       72, 147, 36, 2.6, 0.9, "taban"),
    ("denizyildizi", 166, 147, 36, 3.0, 0.9, "taban"),
]

_cikti = {ad: goruntu_cikar(ad, cx, cy, boy, kapa, ac)
          for ad, cx, cy, boy, kapa, ac, _ in YERLESIM}
PARCALAR = [(ad, _cikti[ad][0], sinif) for ad, *_, sinif in YERLESIM]
VEKTOR = {ad: _cikti[ad][1] for ad in _cikti}

# ---------------------------------------------------------------- parmak yuvaları
YUVA_R = 5.5
YUVA_KONUM = {                    # hedef nokta; kontura otomatik oturtulur
    "yunus":        (56, 52),     # karın altı
    "denizanasi":   (152, 54),    # tentakül altı
    "balik":        (250, 15),    # üst
    "denizati":     (46, 95),     # sağ
    "kaplumbaga":   (142, 115),   # alt
    "ahtapot":      (283, 96),    # sağ
    "yengec":       (72, 127),    # üst
    "denizyildizi": (166, 170),   # alt
}


def _yuva_hesapla():
    yuvalar = {}
    for ad, poly, _ in PARCALAR:
        hx, hy = YUVA_KONUM[ad]
        merkez = nearest_points(poly.exterior, Point(hx, hy))[0]
        hilal = daire(merkez.x, merkez.y, YUVA_R).difference(poly)
        if hilal.geom_type == "MultiPolygon":
            hilal = max(hilal.geoms, key=lambda g: g.area)
        yuvalar[ad] = Polygon(hilal.exterior).simplify(0.05, preserve_topology=True)
    return yuvalar


YUVALAR = _yuva_hesapla()

ETIKETLER = {                     # (TR, EN, x, y, boyut, dikey pay)
    "yunus":        ("Yunus", "Dolphin", 56, 61, 3.6, 2.3),
    "denizanasi":   ("Denizanası", "Jellyfish", 152, 62, 3.6, 2.3),
    "balik":        ("Balık", "Fish", 250, 61, 3.6, 2.3),
    "denizati":     ("Denizatı", "Seahorse", 30, 127, 3.2, 2.0),
    "kaplumbaga":   ("Kaplumbağa", "Sea Turtle", 108, 121, 3.4, 2.2),
    "ahtapot":      ("Ahtapot", "Octopus", 256, 125, 3.4, 2.2),
    "yengec":       ("Yengeç", "Crab", 72, 174, 3.4, 2.2),
    "denizyildizi": ("Denizyıldızı", "Starfish", 200, 174, 3.4, 2.2),
}

# ---------------------------------------------------------------- doğrulama
def dogrula():
    hatalar = []
    kenar = cerceve_poly().exterior
    for ad, poly, _ in PARCALAR:
        d = poly.distance(kenar)
        if d < MIN_EDGE:
            hatalar.append(f"{ad}: dış kenara {d:.1f} mm (en az {MIN_EDGE} mm)")
    for i in range(len(PARCALAR)):
        for j in range(i + 1, len(PARCALAR)):
            a, b = PARCALAR[i], PARCALAR[j]
            d = a[1].distance(b[1])
            if d <= 0:
                hatalar.append(f"{a[0]} ile {b[0]} ÇAKIŞIYOR")
            elif d < MIN_GAP:
                hatalar.append(f"{a[0]}–{b[0]} arası {d:.1f} mm (en az {MIN_GAP} mm)")
    for ad, hilal in YUVALAR.items():
        sahip = next(p for n, p, _ in PARCALAR if n == ad)
        if hilal.is_empty or hilal.area < 8:
            hatalar.append(f"{ad} yuvası çok küçük (alan {hilal.area:.1f} mm²)")
        if sahip.distance(hilal) > 0.15:
            hatalar.append(f"{ad} yuvası kontura bitişik değil")
        if hilal.distance(kenar) < 4.0:
            hatalar.append(f"{ad} yuvası dış kenara {hilal.distance(kenar):.1f} mm")
        for n, p, _ in PARCALAR:
            if n != ad and hilal.distance(p) < 4.0:
                hatalar.append(f"{ad} yuvası {n} parçasına {hilal.distance(p):.1f} mm")
    return hatalar

# ---------------------------------------------------------------- SVG yardımcıları
def _el(ad, **attr):
    icerik = attr.pop("icerik", None)
    s = "<" + ad + "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attr.items())
    return s + (f">{icerik}</{ad}>" if icerik is not None else "/>")


def _lin(idad, x1, y1, x2, y2, duraklar):
    s = [f'<linearGradient id="{idad}" gradientUnits="userSpaceOnUse" '
         f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">']
    for ofs, renk, *op in duraklar:
        o = f' stop-opacity="{op[0]}"' if op else ""
        s.append(f'<stop offset="{ofs}" stop-color="{renk}"{o}/>')
    s.append("</linearGradient>")
    return "".join(s)


def _rad(idad, cx, cy, r, duraklar):
    s = [f'<radialGradient id="{idad}" gradientUnits="userSpaceOnUse" '
         f'cx="{cx}" cy="{cy}" r="{r}">']
    for ofs, renk, *op in duraklar:
        o = f' stop-opacity="{op[0]}"' if op else ""
        s.append(f'<stop offset="{ofs}" stop-color="{renk}"{o}/>')
    s.append("</radialGradient>")
    return "".join(s)


def tanimlar():
    g = [
        _lin("su", 0, -6, 0, 186, [(0, "#4FC8F2"), (0.45, "#219FD8"), (1, "#1173A9")]),
        _lin("kum", 0, 156, 0, 184, [(0, "#F8DA82"), (1, "#E2B455")]),
        _rad("gunes_su", 160, -4, 130, [(0, "#EAFBFF", 0.5), (0.6, "#CFF2FC", 0.15),
                                        (1, "#CFF2FC", 0)]),
    ]
    return "<defs>" + "".join(g) + "</defs>"


def _klip(e, ad, poly):
    e.append(f'<clipPath id="{ad}"><path d="{yol_svg(poly)}"/></clipPath>')
    return f"url(#{ad})"


def zemin_golgesi(e, cx, cy, rx):
    for f_rx, ry, op in [(1.0, 2.2, 0.10), (0.75, 1.6, 0.10), (0.5, 1.1, 0.12)]:
        e.append(_el("ellipse", cx=cx, cy=cy, rx=rx * f_rx, ry=ry,
                     fill="#0A2438", opacity=f"{op}"))


def logo_ciz(e):
    if not os.path.exists(LOGO_PNG):
        print("UYARI: logo bulunamadı, atlandı:", LOGO_PNG)
        return
    veri = open(LOGO_PNG, "rb").read()
    px_w, px_h = struct.unpack(">II", veri[16:24])
    lw = 30.0
    lh = lw * px_h / px_w
    x0, y0 = 312.0 - lw, 7.0
    b64 = base64.b64encode(veri).decode()
    e.append(f'<image x="{x0:.2f}" y="{y0:.2f}" width="{lw:.2f}" '
             f'height="{lh:.2f}" xlink:href="data:image/png;base64,{b64}"/>')


def etiket(e, x, y, tr, en, boyut=3.0, pad_y=2.2):
    on = f"{tr} / "
    kf = 0.62                                   # ortalama karakter genişliği katsayısı
    w_on = len(on) * boyut * kf
    w_en = len(en) * boyut * kf
    w = w_on + w_en + 6.4
    h = boyut + pad_y
    cy = y - 0.3 * boyut
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2 + 0.5, width=w, height=h, rx=1.6,
                 fill="#0A2438", opacity=0.2))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.6,
                 fill="#FFFFFF", opacity=0.97))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.6,
                 fill="none", stroke="#26343F", stroke_width=0.35, opacity=0.5))
    bas = x - (w_on + w_en) / 2
    e.append(_el("text", x=bas, y=y, icerik=on, fill="#1C2733", font_size=boyut,
                 font_family="sans-serif", font_weight="bold", text_anchor="start"))
    e.append(_el("text", x=bas + w_on, y=y, icerik=en, fill="#2563D9",
                 font_size=boyut, font_family="sans-serif", font_weight="bold",
                 text_anchor="start"))

# ---------------------------------------------------------------- dekor
def kabarcik(e, x, y, r):
    e.append(_el("circle", cx=x, cy=y, r=r, fill="#FFFFFF", opacity=0.16))
    e.append(_el("circle", cx=x, cy=y, r=r, fill="none", stroke="#FFFFFF",
                 stroke_width=max(0.35, r * 0.2), opacity=0.85))
    e.append(_el("circle", cx=x - r * 0.32, cy=y - r * 0.36, r=r * 0.26,
                 fill="#FFFFFF", opacity=0.95))


def yosun(e, x, taban, boy, s=1.0, renk="#37A45C", koyu="#268244"):
    for dx, egim, b2 in [(0, 1, 1.0), (3.6 * s, -1, 0.82), (-2.8 * s, -0.6, 0.7)]:
        by = boy * b2
        e.append(_el("path",
                     d=f"M {x+dx} {taban} C {x+dx+5*s*egim} {taban-by*0.3} "
                       f"{x+dx-4*s*egim} {taban-by*0.62} {x+dx+3*s*egim} {taban-by} "
                       f"C {x+dx+5.5*s*egim} {taban-by*0.64} {x+dx-2.5*s*egim} "
                       f"{taban-by*0.32} {x+dx-1.6*s} {taban} Z", fill=renk))
        e.append(_el("path",
                     d=f"M {x+dx+0.6*s} {taban} C {x+dx+3*s*egim} {taban-by*0.35} "
                       f"{x+dx-2*s*egim} {taban-by*0.65} {x+dx+2.2*s*egim} {taban-by*0.94}",
                     fill="none", stroke=koyu, stroke_width=0.8 * s, opacity=0.9))


def dalli_mercan(e, x, taban, boy, renk="#A45DD8", koyu="#7E3FB0"):
    dallar = [(0, 0, -0.1), (-0.55, 0.34, -0.5), (0.55, 0.3, 0.42),
              (-0.3, 0.58, -0.9), (0.34, 0.62, 0.95)]
    for ox, oy, tilt in dallar:
        x1, y1 = x + ox * boy * 0.5, taban - oy * boy
        x2 = x1 + tilt * boy * 0.32
        y2 = y1 - boy * (0.42 if oy else 0.62)
        e.append(_el("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=renk,
                     stroke_width=3.0, stroke_linecap="round"))
        e.append(_el("circle", cx=x2, cy=y2, r=1.7, fill=renk))
        e.append(_el("circle", cx=x2 - 0.4, cy=y2 - 0.4, r=0.6, fill="#C88FE8",
                     opacity=0.9))
    e.append(_el("line", x1=x, y1=taban, x2=x, y2=taban - boy * 0.62, stroke=koyu,
                 stroke_width=3.4, stroke_linecap="round"))


def tup_sunger(e, x, taban, s=1.0):
    for dx, h, w in [(-3.5 * s, 9 * s, 4.2 * s), (1.5 * s, 13 * s, 4.6 * s),
                     (6 * s, 7.5 * s, 3.8 * s)]:
        e.append(_el("rect", x=x + dx - w / 2, y=taban - h, width=w, height=h,
                     rx=w * 0.42, fill="#F2C230"))
        e.append(_el("rect", x=x + dx - w / 2 + w * 0.16, y=taban - h + 0.6,
                     width=w * 0.3, height=h - 1.6, rx=w * 0.15, fill="#FFDD6E",
                     opacity=0.9))
        e.append(_el("ellipse", cx=x + dx, cy=taban - h + 0.8, rx=w * 0.32,
                     ry=w * 0.2, fill="#B3830A"))


def kaya(e, x, taban, w, h, renk="#7C8D9B"):
    e.append(_el("path", d=f"M {x-w/2} {taban} Q {x-w/2-1} {taban-h} {x-w*0.1} {taban-h} "
                           f"Q {x+w/2+1} {taban-h*0.9} {x+w/2} {taban} Z", fill=renk))
    e.append(_el("path", d=f"M {x-w*0.32} {taban-h*0.86} Q {x} {taban-h*1.04} "
                           f"{x+w*0.3} {taban-h*0.8}", fill="none", stroke="#A9B7C2",
                 stroke_width=1.0, opacity=0.9))


def tarak_kabugu(e, x, y, s=1.0, renk="#F5A8C8", koyu="#D9709E"):
    e.append(_el("path", d=f"M {x-3.4*s} {y} A {3.4*s} {3.4*s} 0 0 1 {x+3.4*s} {y} Z",
                 fill=renk))
    for aa in (-58, -28, 0, 28, 58):
        ar = math.radians(aa - 90)
        e.append(_el("line", x1=x, y1=y, x2=x + 3.1 * s * math.cos(ar),
                     y2=y + 3.1 * s * math.sin(ar), stroke=koyu,
                     stroke_width=0.5 * s))
    e.append(_el("path", d=f"M {x-1.1*s} {y} L {x-1.8*s} {y+1.4*s} L {x+1.8*s} {y+1.4*s} "
                           f"L {x+1.1*s} {y} Z", fill=renk))


def spiral_kabuk(e, x, y, s=1.0):
    e.append(_el("circle", cx=x, cy=y, r=2.6 * s, fill="#EAC48E"))
    e.append(_el("path", d=f"M {x+2.6*s} {y} A 2.6 2.6 0 1 1 {x} {y-2.6*s} "
                           f"A 1.7 1.7 0 1 0 {x} {y+1.7*s} A 0.9 0.9 0 1 1 {x} {y-0.9*s}",
                 fill="none", stroke="#B3854A", stroke_width=0.6 * s))
    e.append(_el("path", d=f"M {x+2.4*s} {y+1} L {x+4.4*s} {y+1.6*s} L {x+3*s} {y+2.4*s} Z",
                 fill="#EAC48E"))


def mini_yildiz(e, x, y, r, renk="#F58220"):
    d = "M "
    for i in range(10):
        rr = r if i % 2 == 0 else r * 0.45
        aa = math.radians(-90 + i * 36)
        d += f"{x + rr * math.cos(aa):.1f} {y + rr * math.sin(aa):.1f} L "
    e.append(_el("path", d=d[:-2] + "Z", fill=renk))
    e.append(_el("path", d=d[:-2] + "Z", fill="none", stroke="#C4610A",
                 stroke_width=0.5))

# ---------------------------------------------------------------- sahne
def sahne_svg(yuva_goster=False):
    rnd = random.Random(53)
    e = [tanimlar()]
    # su + yüzey ışığı
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=H + 12, fill="url(#su)"))
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=60, fill="url(#gunes_su)"))
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=8.5, fill="#CFF2FC",
                 opacity=0.6))
    for dy, op in [(3.4, 0.9), (6.2, 0.5)]:
        d = f"M -6 {dy} "
        for i in range(16):
            d += (f"q 5.2 {-2.2 if i % 2 else 2.2} 10.5 0 "
                  f"q 5.2 {2.2 if i % 2 else -2.2} 10.5 0 ")
        e.append(_el("path", d=d, fill="none", stroke="#FFFFFF", stroke_width=1.1,
                     opacity=f"{op}"))
    # ışık hüzmeleri
    for x0, tilt, gen in [(46, -8, 7), (98, 4, 10), (152, -3, 8), (208, 7, 11),
                          (262, -5, 7)]:
        e.append(_el("path", d=f"M {x0 - gen} 2 L {x0 + gen} 2 L {x0 + tilt + gen * 2.6} 92 "
                               f"L {x0 + tilt - gen * 2.6} 92 Z", fill="#EAFBFF",
                     opacity=0.10))
    # kabarcık kolonları
    for bx, by, br in [(88, 54, 1.5), (92, 45, 1.1), (86, 38, 0.8),
                       (120, 20, 1.7), (125, 11, 1.2), (117, 5, 0.8),
                       (190, 60, 1.5), (195, 51, 1.0),
                       (222, 64, 1.3), (218, 56, 0.9),
                       (300, 60, 1.8), (305, 50, 1.3), (298, 41, 0.9),
                       (12, 60, 1.5), (17, 51, 1.0), (110, 150, 1.3),
                       (115, 142, 0.9), (285, 150, 1.1), (215, 22, 1.0),
                       (219, 14, 0.7)]:
        kabarcik(e, bx, by, br)
    # --- kumlu taban
    e.append(_el("path", d=f"M -6 166 Q 40 158 90 163 Q 150 168 210 162 Q 265 157 326 164 "
                           f"L 326 186 L -6 186 Z", fill="url(#kum)"))
    for _ in range(60):
        px, py = rnd.uniform(-4, 322), rnd.uniform(163.5, 179)
        e.append(_el("circle", cx=f"{px:.1f}", cy=f"{py:.1f}",
                     r=f"{rnd.uniform(0.2, 0.55):.2f}", fill="#D9A94E",
                     opacity=f"{rnd.uniform(0.35, 0.7):.2f}"))
    # --- renkli resif dekoru (parça alanlarının dışında)
    dalli_mercan(e, 12, 177, 15)
    tup_sunger(e, 16, 177.5, 0.85)
    kaya(e, 6, 178, 10, 5)
    kaya(e, 118, 176, 12, 6.5)
    kaya(e, 128, 177.5, 9, 4.6, "#6B7C8A")
    tarak_kabugu(e, 137, 176, 1.1)
    spiral_kabuk(e, 108, 177, 1.0)
    yosun(e, 240, 173, 27, 0.95)
    yosun(e, 248, 175, 20, 0.8, "#2FAF6E", "#1F8A50")
    mini_yildiz(e, 235, 167, 4.0)
    dalli_mercan(e, 300, 177, 14, "#F06CA8", "#C74E86")
    kaya(e, 311, 178, 10, 5.2)
    tarak_kabugu(e, 289, 177.5, 0.9, "#B48CD8", "#8A62B0")
    # --- taban canlıları zemin gölgeleri
    zemin_golgesi(e, 72, 167, 24)
    zemin_golgesi(e, 166, 168, 20)
    # --- canlılar (referans görseller, kontura kırpılı)
    e += canli_detaylari()
    # --- parça dış çizgileri (kesim hattı üzerinde ince çerçeve)
    for _, poly, _ in PARCALAR:
        e.append(_el("path", d=yol_svg(poly), fill="none", stroke="#1C2A33",
                     stroke_width=0.6, stroke_linejoin="round", opacity=0.55))
    # --- parmak yuvaları (yalnız önizleme)
    if yuva_goster:
        for hilal in YUVALAR.values():
            e.append(_el("path", d=yol_svg(hilal), fill="#DCC9A5", opacity=0.97))
            e.append(_el("path", d=yol_svg(hilal), fill="none", stroke="#8A7350",
                         stroke_width=0.35))
    # --- etiketler + logo
    for tr, en, ex, ey, boy, pay in ETIKETLER.values():
        etiket(e, ex, ey, tr, en, boy, pay)
    logo_ciz(e)
    return e

# ---------------------------------------------------------------- canlı detayları
def canli_detaylari():
    """Her canlıyı referansından türetilen renkli VEKTÖR olarak, konturuna kırpılı çizer."""
    e = []
    for ad, poly, _ in PARCALAR:
        v = VEKTOR[ad]
        klip = _klip(e, "k_" + ad, poly)
        e.append(f'<g clip-path="{klip}">')
        for renk, d in v["dolgu"]:                              # renk bölgeleri (altta)
            e.append(f'<path d="{d}" fill="{renk}"/>')
        if v["kontur"]:                                         # dış çizgiler (üstte, delikli)
            e.append(f'<path d="{" ".join(v["kontur"])}" fill="#1A1E22" '
                     f'fill-rule="evenodd"/>')
        e.append("</g>")
    return e

# ---------------------------------------------------------------- SVG belgeleri
def svg_belge(w_mm, h_mm, icerik):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w_mm}mm" height="{h_mm}mm" '
            f'viewBox="0 0 {w_mm} {h_mm}">' + "\n".join(icerik) + "</svg>")


def hiza_isaretleri(renk="#1A1A1A"):
    """Dört köşe register (hiza) haçı — yuvarlatılmış çerçevenin DIŞINDA, köşe
    fire alanında (kesimde atılır, oyuncakta görünmez). Baskı, kalıp ve DXF'te
    AYNI koordinatta bulunur; operatör baskılı tahtayı kesime bu dört noktadan
    çakıştırınca konum + açı + ölçek tam sabitlenir (baskı–kesim kayması biter)."""
    m = []
    for mx, my in [(5, 5), (W - 5, 5), (5, H - 5), (W - 5, H - 5)]:
        m.append(_el("line", x1=mx - 3.2, y1=my, x2=mx + 3.2, y2=my, stroke=renk,
                     stroke_width=0.3))
        m.append(_el("line", x1=mx, y1=my - 3.2, x2=mx, y2=my + 3.2, stroke=renk,
                     stroke_width=0.3))
        m.append(_el("circle", cx=mx, cy=my, r=2.0, fill="none", stroke=renk,
                     stroke_width=0.3))
    return m


def uret_baski_svg(yuva_goster=False):
    icerik = ([f'<g transform="translate({BLEED},{BLEED})">']
              + sahne_svg(yuva_goster) + hiza_isaretleri() + ["</g>"])
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, icerik)


def uret_kalip_svg():
    """UV hizalama kalıbı: 320x180 (ürün yerleştirme jigi) — dış çerçeve + 4 köşe
    hiza haçı. Kalıp boyu SABİT 320x180. Baskı (324x184) bu kalıbın MERKEZİNE
    hizalanır; tasarım her kenardan 2 mm taşar (bleed)."""
    icerik = [_el("path", d=yol_svg(cerceve_poly()), fill="none", stroke="#FF0000",
                  stroke_width=0.25)]
    icerik += hiza_isaretleri("#FF0000")
    icerik.append(_el("text", x=6, y=177.2,
                      icerik="DENİZ CANLILARI PUZZLE 320x180 – UV KALIP (1:1)",
                      fill="#888888", font_size="3", font_family="sans-serif"))
    return svg_belge(W, H, icerik)


def uret_golge_svg():
    ic = [f'<g transform="translate({BLEED},{BLEED})">']
    ic.append(_el("rect", x=-6, y=-6, width=W + 12, height=H + 12, fill="#DCEEF8"))
    ic.append(_el("path", d="M -6 166 Q 40 158 90 163 Q 150 168 210 162 Q 265 157 "
                            "326 164 L 326 186 L -6 186 Z", fill="#EFE6C8"))
    for ad, poly, _ in PARCALAR:
        for iceri, op in ((-0.15, 0.4), (-0.55, 1.0)):
            g = poly.buffer(iceri, quad_segs=8)
            if g.is_empty:
                continue
            geoms = g.geoms if g.geom_type == "MultiPolygon" else [g]
            for gg in geoms:
                ic.append(_el("path", d=yol_svg(gg), fill="#54677A", opacity=f"{op}"))
    ic += hiza_isaretleri()
    ic.append("</g>")
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, ic)

# ---------------------------------------------------------------- DXF
def uret_dxf(dosya):
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    doc.layers.add("UST_KATMAN_KESIM", color=1)
    doc.layers.add("ALT_KATMAN_KESIM", color=5)
    doc.layers.add("YAZI", color=8)
    doc.layers.add("HIZA", color=2)          # kesilmez: baskı-kesim hiza haçları

    def poli(poly, dx, katman):
        pts, son = [], None
        for (x, yy) in list(poly.exterior.coords)[:-1]:
            q = (round(x + dx, 3), round(H - yy, 3))
            if q != son:
                pts.append(q)
                son = q
        if pts[0] == pts[-1]:
            pts.pop()
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": katman})

    poli(cerceve_poly(), 0, "UST_KATMAN_KESIM")
    for _, poly, _ in PARCALAR:
        poli(poly, 0, "UST_KATMAN_KESIM")
    for hilal in YUVALAR.values():
        poli(hilal, 0, "UST_KATMAN_KESIM")
    dx_alt = W + 15
    poli(cerceve_poly(), dx_alt, "ALT_KATMAN_KESIM")

    # baskı ile kesimi çakıştırmak için 4 köşe hiza haçı — iki panoda da (baskı/kalıp/gölge ile aynı yer)
    for dx in (0, dx_alt):
        for mx, my in [(5, 5), (W - 5, 5), (5, H - 5), (W - 5, H - 5)]:
            x, yy = mx + dx, H - my
            msp.add_line((x - 3.2, yy), (x + 3.2, yy), dxfattribs={"layer": "HIZA"})
            msp.add_line((x, yy - 3.2), (x, yy + 3.2), dxfattribs={"layer": "HIZA"})
            msp.add_circle((x, yy), 2.0, dxfattribs={"layer": "HIZA"})

    msp.add_text("UST KATMAN - deniz canlilari + cepler (320x180)",
                 dxfattribs={"layer": "YAZI", "height": 6}).set_placement((0, H + 6))
    msp.add_text("ALT KATMAN - duz taban (320x180)",
                 dxfattribs={"layer": "YAZI", "height": 6}).set_placement((dx_alt, H + 6))
    doc.saveas(dosya)

# ---------------------------------------------------------------- ana akış
def main():
    hatalar = dogrula()
    if hatalar:
        print("UYARI – yerleşim sorunları:")
        for hh in hatalar:
            print("  •", hh)
    else:
        print("Yerleşim doğrulandı: tüm parçalar aralık kurallarına uygun.")

    os.makedirs(OUT, exist_ok=True)
    import cairosvg

    baski = uret_baski_svg(yuva_goster=False)
    onizleme = uret_baski_svg(yuva_goster=True)
    kalip = uret_kalip_svg()
    golge = uret_golge_svg()

    cairosvg.svg2pdf(bytestring=baski.encode(), write_to=f"{OUT}/{TEMA}_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=kalip.encode(), write_to=f"{OUT}/{TEMA}_uv_kalip.pdf")
    cairosvg.svg2pdf(bytestring=golge.encode(), write_to=f"{OUT}/{TEMA}_alt_golge.pdf")
    cairosvg.svg2png(bytestring=onizleme.encode(),
                     write_to=f"{OUT}/{TEMA}_onizleme.png", output_width=2200)
    cairosvg.svg2png(bytestring=golge.encode(),
                     write_to=f"{OUT}/{TEMA}_alt_golge_onizleme.png", output_width=1920)
    uret_dxf(f"{OUT}/{TEMA}_lazer_kesim.dxf")

    for ad, poly, sinif in PARCALAR:
        x0, y0, x1, y1 = poly.bounds
        print(f"  parça {ad:<13} ({sinif:<5}) {x1-x0:5.1f} x {y1-y0:5.1f} mm")
    print("Tamamlandı ->", OUT)


if __name__ == "__main__":
    main()
