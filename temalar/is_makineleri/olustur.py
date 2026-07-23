# -*- coding: utf-8 -*-
"""
İki katmanlı "İş Makineleri" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Parçalar elle vektör çizilir (araclar temasıyla aynı yaklaşım): her makine basit
şekillerin (kutu/elips/kapsül/çokgen) BİRLEŞİMİdir; `birlesim()` köşeleri
yumuşatıp lazer için TEK kapalı dış kontur üretir. Aynı kontur hem SVG çizimini
hem DXF polyline'ını besler; baskı ile kesim asla ayrışmaz.

Çıktılar (cikti/):
  1. is_makineleri_uv_kalip.pdf    – UV hizalama kalıbı (yalnız dış çerçeve, 1:1)
  2. is_makineleri_uv_baski.pdf    – ÜST katman baskısı, 2 mm taşmalı (324x184)
  3. is_makineleri_alt_golge.pdf   – ALT katman gölge baskısı (324x184)
  4. is_makineleri_lazer_kesim.dxf – Lazer: ÜST (cepli) + ALT (düz) panolar

Çalıştırma:  python3 olustur.py
Bağımlılıklar: ezdxf cairosvg shapely
"""
import base64
import math
import os
import random
import struct

from shapely.affinity import rotate as s_dondur, scale as s_olcek, translate as s_tasi
from shapely.geometry import LineString, Point, Polygon, box as s_kutu
from shapely.ops import nearest_points, unary_union

# ---------------------------------------------------------------- temel ölçüler
W, H = 320.0, 180.0
BLEED = 2.0
CORNER_R = 8.0
MIN_GAP = 7.5
MIN_EDGE = 6.0

KLASOR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KLASOR, "cikti")
LOGO_PNG = os.path.join(KLASOR, "varlik", "zoziva_logo.png")
TEMA = "is_makineleri"

# ---------------------------------------------------------------- geometri araçları
def elips(cx, cy, rx, ry, aci=0.0):
    e = s_olcek(Point(cx, cy).buffer(1.0, quad_segs=24), rx, ry, origin=(cx, cy))
    return s_dondur(e, aci, origin=(cx, cy)) if aci else e


def daire(cx, cy, r):
    return Point(cx, cy).buffer(r, quad_segs=24)


def kapsul(x1, y1, x2, y2, r):
    return LineString([(x1, y1), (x2, y2)]).buffer(r, quad_segs=12)


def kutu(x, y, w, h, r=0.0):
    if r <= 0:
        return s_kutu(x, y, x + w, y + h)
    return s_kutu(x + r, y + r, x + w - r, y + h - r).buffer(r, quad_segs=10)


def cokgen(*pts):
    return Polygon(pts)


def birlesim(parcalar, kapa=1.3, ac=0.7):
    u = unary_union(parcalar)
    u = u.buffer(kapa, quad_segs=10).buffer(-kapa - ac, quad_segs=10).buffer(ac, quad_segs=10)
    if u.geom_type == "MultiPolygon":
        u = max(u.geoms, key=lambda g: g.area)
    return Polygon(u.exterior).simplify(0.05, preserve_topology=True)


def yol_svg(poly):
    pts = list(poly.exterior.coords)[:-1]
    d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f} " + " ".join(
        f"L {x:.2f} {y:.2f}" for x, y in pts[1:])
    return d + " Z"


def cerceve_poly():
    return s_kutu(CORNER_R, CORNER_R, W - CORNER_R, H - CORNER_R).buffer(CORNER_R, quad_segs=16)

# ---------------------------------------------------------------- makine konturları
# Her makine kendi (cx,cy) merkezine göre çizilir; parçalar birleşip tek kontur olur.

def kontur_ekskavator(cx, cy):
    return birlesim([
        kutu(cx - 26, cy + 8, 44, 12, 5),                       # palet (track)
        kutu(cx - 18, cy - 10, 30, 20, 3),                      # üst gövde / kabin
        kapsul(cx + 8, cy - 2, cx + 25, cy - 15, 4.6),          # bom
        kapsul(cx + 24, cy - 14, cx + 31, cy + 4, 4.2),         # kol
        cokgen((cx + 27, cy + 3), (cx + 37, cy + 2), (cx + 36, cy + 12),
               (cx + 28, cy + 13)),                             # kepçe
    ], kapa=1.8)


def kontur_damperli(cx, cy):
    return birlesim([
        kutu(cx - 28, cy + 7, 58, 5, 1),                        # şasi
        kutu(cx - 28, cy - 9, 18, 18, 3),                       # kabin
        cokgen((cx - 8, cy - 13), (cx + 29, cy - 15), (cx + 29, cy + 9),
               (cx - 8, cy + 9)),                               # damper kasası
        daire(cx - 16, cy + 13, 8),                             # ön teker
        daire(cx + 13, cy + 13, 8.5),                           # arka teker 1
        daire(cx + 24, cy + 13, 8.5),                           # arka teker 2
    ], kapa=1.7)


def kontur_vinc(cx, cy):
    return birlesim([
        kutu(cx - 30, cy + 3, 60, 12, 3),                       # şasi
        kutu(cx - 30, cy - 8, 16, 12, 2),                       # kabin
        kutu(cx - 12, cy - 6, 12, 12, 2),                       # döner platform
        kapsul(cx - 4, cy - 2, cx + 33, cy - 19, 4.3),          # bom (kol)
        daire(cx - 18, cy + 17, 7),                             # tekerler
        daire(cx + 2, cy + 17, 7),
        daire(cx + 16, cy + 17, 7),
    ], kapa=1.7)


def kontur_buldozer(cx, cy):
    return birlesim([
        kutu(cx - 24, cy + 7, 46, 13, 5),                       # palet
        kutu(cx - 10, cy - 12, 28, 22, 3),                      # gövde + kabin
        kutu(cx - 6, cy - 18, 4, 8, 1.2),                       # egzoz
        cokgen((cx - 31, cy - 1), (cx - 22, cy + 1), (cx - 22, cy + 18),
               (cx - 32, cy + 20)),                             # bıçak (blade)
        kapsul(cx - 24, cy + 8, cx - 10, cy + 9, 2.6),          # bıçak kolu
    ], kapa=1.8)


def kontur_mikser(cx, cy):
    return birlesim([
        kutu(cx - 30, cy + 7, 62, 5, 1),                        # şasi
        kutu(cx - 30, cy - 9, 18, 18, 3),                       # kabin
        elips(cx + 8, cy - 3, 22, 14, -12),                     # tambur (drum)
        cokgen((cx + 26, cy + 2), (cx + 33, cy + 5), (cx + 30, cy + 11),
               (cx + 24, cy + 9)),                              # huni
        daire(cx - 18, cy + 13, 7.5),                           # tekerler
        daire(cx + 12, cy + 13, 8),
        daire(cx + 22, cy + 13, 8),
    ], kapa=1.7)


def kontur_forklift(cx, cy):
    return birlesim([
        kutu(cx - 4, cy - 3, 24, 18, 2),                        # gövde
        kutu(cx - 4, cy - 21, 22, 4, 1.4),                      # tavan koruma kafesi
        kapsul(cx + 1, cy - 19, cx + 1, cy - 3, 1.8),           # arka direk
        kapsul(cx + 15, cy - 19, cx + 15, cy - 3, 1.8),         # ön direk
        kutu(cx - 11, cy - 20, 4.5, 32, 1.4),                   # kaldırma direği
        kapsul(cx - 26, cy + 12, cx - 9, cy + 12, 2.4),         # çatal
        daire(cx - 2, cy + 13, 6.5),                            # ön teker
        daire(cx + 16, cy + 13, 5.8),                           # arka teker
    ], kapa=2.0)


def kontur_silindir(cx, cy):
    return birlesim([
        kutu(cx - 27, cy + 1, 20, 21, 9.5),                     # ön silindir (drum)
        kutu(cx - 9, cy - 11, 30, 23, 3),                       # gövde + kabin
        kapsul(cx - 16, cy + 10, cx - 8, cy + 10, 3),           # silindir çatalı
        daire(cx + 17, cy + 12, 10),                            # arka teker
    ], kapa=1.8)


def kontur_yukleyici(cx, cy):
    return birlesim([
        kutu(cx + 1, cy - 13, 31, 25, 3),                       # arka gövde + kabin
        kapsul(cx + 4, cy + 2, cx - 15, cy + 6, 4.2),           # kol
        cokgen((cx - 31, cy - 2), (cx - 14, cy + 2), (cx - 14, cy + 15),
               (cx - 33, cy + 17)),                             # kepçe
        daire(cx - 10, cy + 16, 10),                            # ön teker
        daire(cx + 20, cy + 16, 10),                            # arka teker
    ], kapa=1.8)


# (ad, cx, cy, sınıf, kontur_fn) — üç kuşak: kazı / taşıma / yol
YERLESIM = [
    ("ekskavator", 62, 37, "kazi",   kontur_ekskavator),
    ("damperli",  166, 37, "tasima", kontur_damperli),
    ("vinc",      256, 35, "tasima", kontur_vinc),
    ("buldozer",   64, 92, "kazi",   kontur_buldozer),
    ("mikser",    168, 92, "tasima", kontur_mikser),
    ("forklift",  264, 93, "tasima", kontur_forklift),
    ("silindir",   97, 147, "yol",   kontur_silindir),
    ("yukleyici", 214, 147, "kazi",  kontur_yukleyici),
]

MERKEZ = {ad: (cx, cy) for ad, cx, cy, _, _ in YERLESIM}
PARCALAR = [(ad, fn(cx, cy), sinif) for ad, cx, cy, sinif, fn in YERLESIM]

# ---------------------------------------------------------------- parmak yuvaları
YUVA_R = 5.5
YUVA_KONUM = {                    # hedef nokta; kontura otomatik oturtulur
    "ekskavator": (55, 60),       # palet altı
    "damperli":   (166, 58),      # alt
    "vinc":       (256, 57),      # alt
    "buldozer":   (66, 116),      # alt
    "mikser":     (168, 114),     # alt
    "forklift":   (264, 113),     # alt
    "silindir":   (97, 170),      # alt
    "yukleyici":  (214, 170),     # alt
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
    "ekskavator": ("Ekskavatör", "Excavator", 62, 68, 3.2, 2.0),
    "damperli":   ("Damperli Kamyon", "Dump Truck", 166, 66, 3.2, 2.0),
    "vinc":       ("Vinç", "Crane", 256, 66, 3.2, 2.0),
    "buldozer":   ("Buldozer", "Bulldozer", 64, 122, 3.2, 2.0),
    "mikser":     ("Beton Mikseri", "Mixer", 168, 122, 3.2, 2.0),
    "forklift":   ("Forklift", "Forklift", 264, 121, 3.2, 2.0),
    "silindir":   ("Yol Silindiri", "Road Roller", 97, 176, 3.2, 2.0),
    "yukleyici":  ("Kepçe", "Wheel Loader", 214, 176, 3.2, 2.0),
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
        _lin("gok", 0, -6, 0, 120, [(0, "#4FA6DE"), (0.5, "#8FCBEC"), (1, "#D6EEF7")]),
        _rad("gunes", 300, 12, 26, [(0, "#FFFDF0"), (0.4, "#FFF0B0", 0.9),
                                    (1, "#FFF0B0", 0)]),
        _lin("toprak", 0, 120, 0, 186, [(0, "#D9A85E"), (0.5, "#C6924A"), (1, "#A9762F")]),
        _lin("sari", 0, -20, 0, 30, [(0, "#FFDF6E"), (0.4, "#FBC02D"),
                                     (0.8, "#E39A10"), (1, "#B87608")]),
        _lin("turuncu", 0, -20, 0, 30, [(0, "#FFB25A"), (0.4, "#F5842A"),
                                        (0.8, "#DB6415"), (1, "#A9480C")]),
        _lin("kirmizi", 0, -20, 0, 30, [(0, "#FF8A78"), (0.4, "#E84A3C"),
                                        (0.8, "#C22D22"), (1, "#8F1F18")]),
        _lin("yesil", 0, -20, 0, 30, [(0, "#8FD07A"), (0.4, "#4E9E42"),
                                      (0.8, "#357C2F"), (1, "#245C22")]),
        _lin("metal", 0, -20, 0, 30, [(0, "#FFFFFF"), (0.45, "#E6EBEF"),
                                      (0.8, "#C0CAD2"), (1, "#94A0AA")]),
        _lin("koyu", 0, -20, 0, 30, [(0, "#5A636D"), (0.5, "#3D4650"), (1, "#262D35")]),
        _rad("lastik", 0, 0, 1, [(0.5, "#43434B"), (0.8, "#2A2A31"), (1, "#17171C")]),
        _rad("jant", 0, 0, 1, [(0, "#FAFBFC"), (0.5, "#DFE4E9"),
                               (0.78, "#B7C0C8"), (1, "#79838D")]),
        '<linearGradient id="cam" x1="0" y1="0" x2="0.6" y2="1">'
        '<stop offset="0" stop-color="#EAF7FF" stop-opacity="0.95"/>'
        '<stop offset="0.5" stop-color="#A9D2EA" stop-opacity="0.85"/>'
        '<stop offset="1" stop-color="#5C86A2" stop-opacity="0.8"/></linearGradient>',
    ]
    return "<defs>" + "".join(g) + "</defs>"


def _klip(e, ad, poly):
    e.append(f'<clipPath id="{ad}"><path d="{yol_svg(poly)}"/></clipPath>')
    return f"url(#{ad})"

# ---------------------------------------------------------------- ortak çizim parçaları
def zemin_golgesi(e, cx, cy, rx):
    for f_rx, ry, op in [(1.0, 2.4, 0.10), (0.78, 1.8, 0.10), (0.5, 1.2, 0.12)]:
        e.append(_el("ellipse", cx=cx, cy=cy, rx=rx * f_rx, ry=ry,
                     fill="#3A2A12", opacity=f"{op}"))


def hacim(e, klip, poly, guc=0.12):
    x0, y0, x1, y1 = poly.bounds
    w, h = x1 - x0, y1 - y0
    e.append(_el("ellipse", cx=x0 + w * 0.4, cy=y0 + h * 0.16, rx=w * 0.6, ry=h * 0.3,
                 fill="#FFFFFF", opacity=f"{guc}", clip_path=f"url(#{klip})"))
    e.append(_el("ellipse", cx=x0 + w * 0.55, cy=y1 + h * 0.02, rx=w * 0.72, ry=h * 0.26,
                 fill="#1A130A", opacity=f"{guc * 0.8}", clip_path=f"url(#{klip})"))


def teker(e, cx, cy, r):
    """Lastik + diş + jant + bijon."""
    e.append(_el("ellipse", cx=cx, cy=cy + r - 0.2, rx=r * 1.05, ry=1.3,
                 fill="#241A0C", opacity=0.3))
    e.append(f'<g transform="translate({cx},{cy}) scale({r:.3f})">'
             f'<circle cx="0" cy="0" r="1" fill="url(#lastik)"/></g>')
    for i in range(20):
        a = math.radians(i * 18)
        e.append(_el("line", x1=cx + r * 0.93 * math.cos(a), y1=cy + r * 0.93 * math.sin(a),
                     x2=cx + r * 0.995 * math.cos(a), y2=cy + r * 0.995 * math.sin(a),
                     stroke="#0E0E13", stroke_width=r * 0.09, opacity=0.8))
    rj = r * 0.6
    e.append(f'<g transform="translate({cx},{cy}) scale({rj:.3f})">'
             f'<circle cx="0" cy="0" r="1" fill="url(#jant)"/></g>')
    for i in range(5):
        a = math.radians(i * 72 - 90)
        e.append(_el("line", x1=cx, y1=cy, x2=cx + rj * 0.82 * math.cos(a),
                     y2=cy + rj * 0.82 * math.sin(a), stroke="#98A1AB",
                     stroke_width=rj * 0.3, stroke_linecap="round"))
    e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.2, fill="#818B95"))
    e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.2, fill="none", stroke="#525A63",
                 stroke_width=0.35))


def palet(e, x, y, w, h):
    """Paletli taban (track): koyu bant + makaralar + diş."""
    r = h / 2
    e.append(_el("rect", x=x, y=y, width=w, height=h, rx=r, fill="url(#koyu)"))
    e.append(_el("rect", x=x, y=y, width=w, height=h, rx=r, fill="none",
                 stroke="#1B2128", stroke_width=0.6))
    n = max(4, int(w / 7))
    for i in range(n):                                          # diş (tread)
        tx = x + 3 + i * (w - 6) / (n - 1)
        e.append(_el("line", x1=tx, y1=y + 1.2, x2=tx, y2=y + h - 1.2,
                     stroke="#12161B", stroke_width=1.1, opacity=0.7))
    e.append(_el("circle", cx=x + r + 1, cy=y + r, r=r * 0.55, fill="#6A727C"))  # tahrik
    e.append(_el("circle", cx=x + w - r - 1, cy=y + r, r=r * 0.55, fill="#6A727C"))
    for i in range(int((w - 2 * r) / 6)):
        e.append(_el("circle", cx=x + r + 4 + i * 6, cy=y + h - 2, r=1.4, fill="#8A929B"))


def cam(e, x, y, w, h, r=1.2):
    e.append(_el("rect", x=x, y=y, width=w, height=h, rx=r, fill="url(#cam)"))
    e.append(_el("rect", x=x, y=y, width=w, height=h, rx=r, fill="none",
                 stroke="#22303B", stroke_width=0.6))
    e.append(_el("path", d=f"M {x+w*0.15} {y+h*0.85} L {x+w*0.7} {y+h*0.12}",
                 stroke="#FFFFFF", stroke_width=0.9, opacity=0.5))


def uyari(e, x, y, w, h, klip):
    """Sarı-siyah uyarı şeridi."""
    n = max(3, int(w / 3.2))
    for i in range(n):
        if i % 2:
            continue
        e.append(_el("path", d=f"M {x+i*w/n} {y+h} L {x+i*w/n+w/n} {y+h} "
                               f"L {x+i*w/n+w/n+h*0.6} {y} L {x+i*w/n+h*0.6} {y} Z",
                     fill="#1A1A1F", opacity=0.9, clip_path=klip))


def logo_ciz(e):
    if not os.path.exists(LOGO_PNG):
        print("UYARI: logo bulunamadı, atlandı:", LOGO_PNG)
        return
    veri = open(LOGO_PNG, "rb").read()
    px_w, px_h = struct.unpack(">II", veri[16:24])
    lw = 28.0
    lh = lw * px_h / px_w
    pw, ph = lw + 5.0, lh + 3.2
    x0, y0 = 313.0 - pw, 5.8
    e.append(_el("rect", x=x0, y=y0 + 0.5, width=pw, height=ph, rx=1.6,
                 fill="#14212C", opacity=0.16))
    e.append(_el("rect", x=x0, y=y0, width=pw, height=ph, rx=1.6,
                 fill="#FCF9F1", opacity=0.96))
    e.append(_el("rect", x=x0, y=y0, width=pw, height=ph, rx=1.6, fill="none",
                 stroke="#26343F", stroke_width=0.3, opacity=0.55))
    b64 = base64.b64encode(veri).decode()
    e.append(f'<image x="{x0 + 2.5:.2f}" y="{y0 + 1.6:.2f}" width="{lw:.2f}" '
             f'height="{lh:.2f}" xlink:href="data:image/png;base64,{b64}"/>')


def etiket(e, x, y, tr, en, boyut=3.0, pad_y=2.2):
    metin = f"{tr} • {en}"
    w = len(metin) * boyut * 0.62 + 6.0
    h = boyut + pad_y
    cy = y - 0.28 * boyut
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2 + 0.5, width=w, height=h, rx=1.4,
                 fill="#14212C", opacity=0.16))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.4,
                 fill="#FCF9F1", opacity=0.96))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.4,
                 fill="none", stroke="#26343F", stroke_width=0.3, opacity=0.55))
    e.append(_el("text", x=x, y=y, icerik=metin, fill="#22303B", font_size=boyut,
                 font_family="sans-serif", font_weight="bold", text_anchor="middle"))

# ---------------------------------------------------------------- dekor
def bulut(e, x, y, s, op=0.9):
    for dx, dy, r in [(-6, 1.5, 4.5), (0, 0, 6), (6.5, 1.2, 4.8), (1, 3, 5)]:
        e.append(_el("ellipse", cx=x + dx * s, cy=y + dy * s, rx=r * s, ry=r * s * 0.72,
                     fill="#FFFFFF", opacity=op))


def koni(e, x, taban, s=1.0):
    """Trafik konisi (turuncu)."""
    e.append(_el("ellipse", cx=x, cy=taban + 0.4, rx=3.4 * s, ry=1.0 * s,
                 fill="#2A1C0A", opacity=0.25))
    e.append(_el("path", d=f"M {x-3.2*s} {taban} L {x-1.2*s} {taban-8*s} "
                           f"L {x+1.2*s} {taban-8*s} L {x+3.2*s} {taban} Z",
                 fill="#F5842A"))
    e.append(_el("rect", x=x - 1.9 * s, y=taban - 5.4 * s, width=3.8 * s, height=1.6 * s,
                 fill="#FFFFFF"))
    e.append(_el("rect", x=x - 3.6 * s, y=taban - 0.6 * s, width=7.2 * s, height=1.5 * s,
                 rx=0.4, fill="#D2601C"))


def bariyer(e, x, taban, s=1.0):
    """Sarı-siyah şantiye bariyeri."""
    e.append(_el("rect", x=x, y=taban - 6 * s, width=20 * s, height=3.2 * s, rx=0.5,
                 fill="#FBC02D"))
    for i in range(4):
        e.append(_el("path", d=f"M {x+i*5*s} {taban-3*s} l {2.4*s} 0 l {-2.4*s} {3*s} "
                               f"l {-2.4*s} 0 Z", fill="#1A1A1F", opacity=0.85))
    e.append(_el("rect", x=x + 2 * s, y=taban - 6 * s, width=1.6 * s, height=6 * s,
                 fill="#8A929B"))
    e.append(_el("rect", x=x + 16 * s, y=taban - 6 * s, width=1.6 * s, height=6 * s,
                 fill="#8A929B"))


def toprak_yigin(e, x, taban, w, h):
    e.append(_el("path", d=f"M {x-w/2} {taban} Q {x-w*0.25} {taban-h} {x} {taban-h*0.9} "
                           f"Q {x+w*0.28} {taban-h*1.05} {x+w/2} {taban} Z",
                 fill="#B98A45"))
    e.append(_el("path", d=f"M {x-w*0.3} {taban-h*0.7} Q {x} {taban-h*0.95} {x+w*0.28} {taban-h*0.72}",
                 fill="none", stroke="#8F6A33", stroke_width=1.0, opacity=0.8))

# ---------------------------------------------------------------- sahne
def sahne_svg(yuva_goster=False):
    rnd = random.Random(71)
    e = [tanimlar()]
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=126, fill="url(#gok)"))
    e.append(_el("circle", cx=300, cy=12, r=26, fill="url(#gunes)"))
    bulut(e, 60, 24, 1.1)
    bulut(e, 150, 16, 0.9)
    bulut(e, 232, 30, 1.0)
    # zemin (şantiye toprağı)
    e.append(_el("path", d="M -6 118 Q 80 110 160 116 Q 240 122 326 114 L 326 186 L -6 186 Z",
                 fill="url(#toprak)"))
    e.append(_el("path", d="M -6 118 Q 80 110 160 116 Q 240 122 326 114",
                 fill="none", stroke="#8F6A33", stroke_width=1.0, opacity=0.6))
    for _ in range(70):                                         # çakıl
        px, py = rnd.uniform(-4, 322), rnd.uniform(120, 178)
        e.append(_el("circle", cx=f"{px:.1f}", cy=f"{py:.1f}",
                     r=f"{rnd.uniform(0.3, 0.8):.2f}", fill="#8F6A33",
                     opacity=f"{rnd.uniform(0.3, 0.6):.2f}"))
    # dekor (parça alanları dışında)
    toprak_yigin(e, 20, 124, 30, 12)
    koni(e, 40, 126, 1.0)
    bariyer(e, 128, 128, 1.0)
    koni(e, 158, 127, 0.9)
    toprak_yigin(e, 250, 122, 34, 13)
    koni(e, 300, 126, 1.0)
    bariyer(e, 40, 172, 1.1)
    koni(e, 150, 165, 1.0)
    # zemin temas gölgeleri
    for ad, poly, _ in PARCALAR:
        x0, y0, x1, y1 = poly.bounds
        zemin_golgesi(e, (x0 + x1) / 2, y1 - 1.0, (x1 - x0) * 0.42)
    # makineler
    e += is_detaylari()
    # parça dış çizgileri
    for _, poly, _ in PARCALAR:
        e.append(_el("path", d=yol_svg(poly), fill="none", stroke="#1C2A33",
                     stroke_width=1.2, stroke_linejoin="round"))
    # parmak yuvaları (yalnız önizleme)
    if yuva_goster:
        for hilal in YUVALAR.values():
            e.append(_el("path", d=yol_svg(hilal), fill="#E4D2A8", opacity=0.97))
            e.append(_el("path", d=yol_svg(hilal), fill="none", stroke="#8A7350",
                         stroke_width=0.35))
    # etiketler + logo
    for tr, en, ex, ey, boy, pay in ETIKETLER.values():
        etiket(e, ex, ey, tr, en, boy, pay)
    logo_ciz(e)
    return e

# ---------------------------------------------------------------- makine detayları
GRAD = {"ekskavator": "sari", "damperli": "turuncu", "vinc": "sari",
        "buldozer": "sari", "mikser": "yesil", "forklift": "kirmizi",
        "silindir": "sari", "yukleyici": "sari"}


def is_detaylari():
    e = []
    P = {ad: poly for ad, poly, _ in PARCALAR}
    CIZGI = "#1C2A33"

    def govde(ad):
        poly = P[ad]
        klip = _klip(e, "k_" + ad, poly)
        e.append(_el("path", d=yol_svg(poly), fill=f"url(#{GRAD[ad]})"))
        return klip

    # ---------- EKSKAVATÖR
    cx, cy = MERKEZ["ekskavator"]
    k = govde("ekskavator")
    palet(e, cx - 26, cy + 8, 44, 12)
    cam(e, cx - 14, cy - 7, 15, 11)
    e.append(_el("path", d=f"M {cx+8} {cy-2} L {cx+25} {cy-15} M {cx+24} {cy-14} "
                           f"L {cx+31} {cy+4}", stroke="#C98A10", stroke_width=1.4,
                 fill="none", opacity=0.8, clip_path=k))
    uyari(e, cx - 18, cy + 4, 30, 3.5, k)
    hacim(e, "k_ekskavator", P["ekskavator"], 0.10)

    # ---------- DAMPERLİ KAMYON
    cx, cy = MERKEZ["damperli"]
    k = govde("damperli")
    cam(e, cx - 26, cy - 7, 14, 10)
    e.append(_el("path", d=f"M {cx-8} {cy-13} L {cx+29} {cy-15} L {cx+29} {cy+9} "
                           f"L {cx-8} {cy+9} Z", fill="none", stroke="#A9480C",
                 stroke_width=1.2, opacity=0.7, clip_path=k))
    uyari(e, cx - 8, cy + 5, 37, 4, k)
    teker(e, cx - 16, cy + 13, 8)
    teker(e, cx + 13, cy + 13, 8.5)
    teker(e, cx + 24, cy + 13, 8.5)
    hacim(e, "k_damperli", P["damperli"], 0.10)

    # ---------- VİNÇ
    cx, cy = MERKEZ["vinc"]
    k = govde("vinc")
    cam(e, cx - 28, cy - 6, 12, 10)
    e.append(_el("path", d=f"M {cx-4} {cy-2} L {cx+33} {cy-19}", stroke="#1C2A33",
                 stroke_width=1.2, fill="none", opacity=0.6, clip_path=k))
    for t in range(1, 6):                                       # bom kafes çizgileri
        px = cx - 4 + t * 6.2
        py = cy - 2 - t * 2.85
        e.append(_el("line", x1=px, y1=py + 2, x2=px, y2=py - 2, stroke="#C98A10",
                     stroke_width=0.8, opacity=0.7, clip_path=k))
    e.append(_el("circle", cx=cx + 33, cy=cy - 19, r=1.4, fill="#3D4650"))  # makara
    e.append(_el("line", x1=cx + 33, y1=cy - 18, x2=cx + 33, y2=cy - 8, stroke="#3D4650",
                 stroke_width=0.6))
    teker(e, cx - 18, cy + 17, 7)
    teker(e, cx + 2, cy + 17, 7)
    teker(e, cx + 16, cy + 17, 7)
    hacim(e, "k_vinc", P["vinc"], 0.10)

    # ---------- BULDOZER
    cx, cy = MERKEZ["buldozer"]
    k = govde("buldozer")
    palet(e, cx - 24, cy + 7, 46, 13)
    cam(e, cx - 6, cy - 9, 14, 11)
    e.append(_el("path", d=f"M {cx-31} {cy-1} L {cx-22} {cy+1} L {cx-22} {cy+18} "
                           f"L {cx-32} {cy+20} Z", fill="url(#metal)", opacity=0.9,
                 clip_path=k))
    e.append(_el("path", d=f"M {cx-31} {cy-1} L {cx-22} {cy+1} L {cx-22} {cy+18} "
                           f"L {cx-32} {cy+20} Z", fill="none", stroke=CIZGI,
                 stroke_width=1.0, clip_path=k))
    uyari(e, cx - 10, cy + 5, 26, 3.5, k)
    hacim(e, "k_buldozer", P["buldozer"], 0.10)

    # ---------- BETON MİKSERİ
    cx, cy = MERKEZ["mikser"]
    k = govde("mikser")
    cam(e, cx - 28, cy - 7, 14, 10)
    e.append(_el("ellipse", cx=cx + 8, cy=cy - 3, rx=22, ry=14,
                 transform=f"rotate(-12 {cx+8} {cy-3})", fill="url(#metal)",
                 clip_path=k))
    e.append(_el("ellipse", cx=cx + 8, cy=cy - 3, rx=22, ry=14,
                 transform=f"rotate(-12 {cx+8} {cy-3})", fill="none", stroke=CIZGI,
                 stroke_width=1.0, clip_path=k))
    for t in (-14, -4, 6, 16):                                  # tambur sarmal bantları
        e.append(_el("line", x1=cx + t, y1=cy - 16, x2=cx + t + 6, y2=cy + 10,
                     stroke="#9AA6AF", stroke_width=1.4, opacity=0.8, clip_path=k))
    teker(e, cx - 18, cy + 13, 7.5)
    teker(e, cx + 12, cy + 13, 8)
    teker(e, cx + 22, cy + 13, 8)
    hacim(e, "k_mikser", P["mikser"], 0.10)

    # ---------- FORKLİFT
    cx, cy = MERKEZ["forklift"]
    k = govde("forklift")
    cam(e, cx - 1, cy - 2, 15, 12)
    e.append(_el("rect", x=cx - 11, y=cy - 20, width=4.5, height=32, rx=1.4,
                 fill="url(#koyu)", clip_path=k))                # kaldırma direği
    e.append(_el("path", d=f"M {cx-26} {cy+12} L {cx-9} {cy+12}", stroke="#3D4650",
                 stroke_width=2.2, clip_path=k))                 # çatal
    e.append(_el("path", d=f"M {cx-4} {cy-21} L {cx+18} {cy-21}", stroke="#1A1A1F",
                 stroke_width=1.4, clip_path=k))
    teker(e, cx - 2, cy + 13, 6.5)
    teker(e, cx + 16, cy + 13, 5.8)
    hacim(e, "k_forklift", P["forklift"], 0.10)

    # ---------- YOL SİLİNDİRİ
    cx, cy = MERKEZ["silindir"]
    k = govde("silindir")
    e.append(_el("rect", x=cx - 27, y=cy + 1, width=20, height=21, rx=9.5,
                 fill="url(#metal)", clip_path=k))               # ön silindir
    e.append(_el("rect", x=cx - 27, y=cy + 1, width=20, height=21, rx=9.5,
                 fill="none", stroke=CIZGI, stroke_width=1.0, clip_path=k))
    e.append(_el("line", x1=cx - 17, y1=cy + 2, x2=cx - 17, y2=cy + 21, stroke="#9AA6AF",
                 stroke_width=0.8, opacity=0.8, clip_path=k))
    cam(e, cx - 6, cy - 9, 15, 11)
    uyari(e, cx - 8, cy + 6, 28, 3.5, k)
    teker(e, cx + 17, cy + 12, 10)
    hacim(e, "k_silindir", P["silindir"], 0.10)

    # ---------- KEPÇE / YÜKLEYİCİ
    cx, cy = MERKEZ["yukleyici"]
    k = govde("yukleyici")
    cam(e, cx + 6, cy - 10, 15, 12)
    e.append(_el("path", d=f"M {cx-31} {cy-2} L {cx-14} {cy+2} L {cx-14} {cy+15} "
                           f"L {cx-33} {cy+17} Z", fill="url(#metal)", opacity=0.92,
                 clip_path=k))
    e.append(_el("path", d=f"M {cx-31} {cy-2} L {cx-14} {cy+2} L {cx-14} {cy+15} "
                           f"L {cx-33} {cy+17} Z", fill="none", stroke=CIZGI,
                 stroke_width=1.0, clip_path=k))
    e.append(_el("path", d=f"M {cx+4} {cy+2} L {cx-15} {cy+6}", stroke="#C98A10",
                 stroke_width=1.6, opacity=0.8, clip_path=k))
    uyari(e, cx + 2, cy + 6, 28, 3.5, k)
    teker(e, cx - 10, cy + 16, 10)
    teker(e, cx + 20, cy + 16, 10)
    hacim(e, "k_yukleyici", P["yukleyici"], 0.10)

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
    """Dış çerçeve + 4 köşe hiza haçı; baskıyla birebir çakışsın diye baskıyla
    aynı sayfa (324x184) ve 2 mm bleed ofseti kullanır."""
    icerik = [f'<g transform="translate({BLEED},{BLEED})">',
              _el("path", d=yol_svg(cerceve_poly()), fill="none", stroke="#FF0000",
                  stroke_width=0.25)]
    icerik += hiza_isaretleri("#FF0000")
    icerik.append(_el("text", x=6, y=177.2,
                      icerik="IS MAKINELERI PUZZLE 320x180 – UV KALIP (1:1)",
                      fill="#888888", font_size="3", font_family="sans-serif"))
    icerik.append("</g>")
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, icerik)


def uret_golge_svg():
    ic = [f'<g transform="translate({BLEED},{BLEED})">']
    ic.append(_el("rect", x=-6, y=-6, width=W + 12, height=H + 12, fill="#E7EFF4"))
    ic.append(_el("path", d="M -6 118 Q 80 110 160 116 Q 240 122 326 114 L 326 186 "
                            "L -6 186 Z", fill="#EDE0C4"))
    for ad, poly, _ in PARCALAR:
        for iceri, op in ((-0.15, 0.4), (-0.55, 1.0)):
            g = poly.buffer(iceri, quad_segs=8)
            if g.is_empty:
                continue
            geoms = g.geoms if g.geom_type == "MultiPolygon" else [g]
            for gg in geoms:
                ic.append(_el("path", d=yol_svg(gg), fill="#5A6470", opacity=f"{op}"))
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

    msp.add_text("UST KATMAN - is makineleri + cepler (320x180)",
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
        print(f"  parça {ad:<11} ({sinif:<6}) {x1-x0:5.1f} x {y1-y0:5.1f} mm")
    print("Tamamlandı ->", OUT)


if __name__ == "__main__":
    main()
