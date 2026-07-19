# -*- coding: utf-8 -*-
"""
İki katmanlı "Araçlar" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Çıktılar (cikti/ klasörüne):
  1. araclar_uv_kalip.pdf        – UV baskı hizalama kalıbı (320x180, kesim konturları)
  2. araclar_uv_baski.pdf        – UV baskı dosyası, her kenardan 2 mm taşmalı (324x184)
  3. araclar_lazer_kesim.dxf     – Lazer kesim: ÜST katman (cepli) + ALT katman (düz)
  4. araclar_onizleme.png        – Ekranda bakmak için önizleme

Geometri: her parça basit şekillerin (kutu/elips/kapsül/çokgen) birleşiminden
oluşur; morfolojik kapama/açma köşeleri yumuşatır ve TEK kapalı dış kontur
üretir. Aynı kontur hem baskıya hem DXF'e gider — ikisi asla ayrışamaz.

Çalıştırma:  python3 olustur.py
"""
import math
import os
import random

from shapely.affinity import rotate as s_dondur, scale as s_olcek
from shapely.geometry import LineString, Point, Polygon, box as s_kutu
from shapely.ops import unary_union

# ---------------------------------------------------------------- temel ölçüler
W, H = 320.0, 180.0          # bitmiş puzzle (mm)
BLEED = 2.0                  # baskı taşması (mm)
CORNER_R = 8.0               # dış köşe yuvarlatma (çocuk güvenliği)
MIN_GAP = 7.5                # iki parça arası en az duvar (mm)
MIN_EDGE = 6.0               # parça ile dış kenar arası en az duvar (mm)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cikti")

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
    """Parçaları birleştirir, köşeleri yumuşatır, TEK dış kontur döndürür.
    kapa: içbükey köşe yumuşatma + küçük boşluk köprüleme (mm)
    ac  : dışbükey köşe yumuşatma + ~2*ac'den ince çıkıntı temizliği (mm)"""
    u = unary_union(parcalar)
    u = u.buffer(kapa, quad_segs=10).buffer(-kapa - ac, quad_segs=10).buffer(ac, quad_segs=10)
    if u.geom_type == "MultiPolygon":
        u = max(u.geoms, key=lambda g: g.area)
    u = Polygon(u.exterior).simplify(0.05, preserve_topology=True)
    return u


def yol_svg(poly):
    pts = list(poly.exterior.coords)[:-1]
    d = f"M {pts[0][0]:.2f} {pts[0][1]:.2f} " + " ".join(
        f"L {x:.2f} {y:.2f}" for x, y in pts[1:])
    return d + " Z"


def cerceve_poly():
    return s_kutu(CORNER_R, CORNER_R, W - CORNER_R, H - CORNER_R).buffer(CORNER_R, quad_segs=16)

# ---------------------------------------------------------------- araç konturları
# Her araç: basit parçaların birleşimi -> tek kapalı kesim konturu.

def kontur_balon():
    return birlesim([
        daire(42, 24, 17.5),                                   # kubbe
        cokgen((30, 32), (54, 32), (47.5, 44.5), (36.5, 44.5)),  # etek
        kutu(35.5, 44, 13, 6, 1.2),                            # sepet
    ], kapa=2.0)


def kontur_ucak():
    return birlesim([
        kapsul(106, 31.5, 169, 31.5, 5.3),                     # gövde
        cokgen((97, 15.5), (104.5, 15.5), (116, 29), (97, 29)),  # dikey kuyruk
        cokgen((97, 29.5), (89.5, 35), (89.5, 37.5), (102, 33)),  # yatay kuyruk
        cokgen((131, 34), (153, 34), (128, 50.5), (119, 50.5)),  # kanat
        kapsul(143, 42, 154, 42, 4.2),                         # motor
    ])


def kontur_helikopter():
    return birlesim([
        elips(250, 33.5, 20, 11),                              # kabin
        elips(261, 37, 12, 8.5),                               # burun
        kutu(243, 21.5, 19, 8, 2.5),                           # motor kaportası
        kapsul(266, 30.5, 292, 28.8, 2.6),                     # incelen kuyruk bomu
        cokgen((287.5, 35.5), (290.5, 19.5), (295, 19.5), (297, 35.5)),  # kuyruk dikmesi
        kutu(277.5, 26.2, 7.5, 2.4, 1.1),                      # yatay stabilizatör
        kapsul(227, 13.2, 283, 13.2, 2.6),                     # ana pervane
        kutu(249.5, 14.5, 6, 9),                               # pervane mili
        kapsul(235, 50.2, 271, 50.2, 2.0),                     # kızak
        kutu(242, 43.5, 4.2, 7.5), kutu(260.5, 43.5, 4.2, 7.5),  # kızak ayakları
    ])


def kontur_traktor():
    return birlesim([
        cokgen((16, 100.5), (43, 99), (46, 103.5), (46, 112), (16, 112)),  # kaput
        kutu(44, 86, 28, 20, 3),                               # kabin
        kutu(19.5, 87.5, 5, 14, 1),                            # egzoz borusu
        kutu(18.2, 86.2, 7.6, 3.6, 1.6),                       # egzoz şapkası
        kutu(13.5, 103, 4.5, 9, 1),                            # ön ağırlık
        daire(58, 110.5, 17.5),                                # arka teker
        daire(27.5, 118, 10),                                  # ön teker
    ])


def kontur_itfaiye():
    return birlesim([
        kutu(92, 94.5, 47, 27.5, 1.5),                         # ekipman kasası
        cokgen((139, 98.5), (152.5, 98.5), (159.5, 105.5),
               (160.5, 111), (160.5, 121.5), (139, 121.5)),    # kabin
        kutu(159.8, 113, 4.0, 8.5, 1.2),                       # ön tampon
        daire(104.5, 121.5, 6.5),                              # arka teker
        daire(147.5, 121.5, 6.5),                              # ön teker
    ])


def kontur_araba():
    return birlesim([
        kutu(176.5, 110.5, 51, 12.5, 3.5),                     # alt gövde
        cokgen((185.5, 111.5), (190.5, 101), (212.5, 101), (219.5, 111.5)),  # tavan
        daire(190, 121.5, 6),                                  # ön teker
        daire(214, 121.5, 6),                                  # arka teker
    ], kapa=1.8)


def kontur_otobus():
    return birlesim([
        kutu(240, 94, 73.5, 28.5, 5),                          # gövde
        elips(307.5, 108, 6, 13.5),                            # yuvarlak ön
        daire(256, 121.5, 6.5),                                # arka teker
        daire(297, 121.5, 6.5),                                # ön teker
    ])


def kontur_yelkenli():
    return birlesim([
        cokgen((45, 157), (101, 157), (92, 169.5), (56, 169.5)),  # gövde
        kutu(71, 136, 4, 22),                                  # direk
        cokgen((70, 138), (70, 156.5), (49, 156.5)),           # ana yelken
        cokgen((77, 141), (77, 156.5), (96, 156.5)),           # flok yelken
        kutu(53, 153.5, 18, 3),                                # bumba
    ])


def kontur_feribot():
    return birlesim([
        cokgen((190, 156.5), (292, 156.5), (282.5, 170), (199.5, 170)),  # tekne
        kutu(201, 148.5, 78, 9, 1),                            # ana güverte
        kutu(211, 141.5, 42, 8.5, 1.5),                        # köprü üstü
        cokgen((259, 140.5), (267.5, 140.5), (269, 149.5), (257.5, 149.5)),  # baca
    ])


PARCALAR = [(ad, f(), sinif) for ad, f, sinif in [
    ("balon",      kontur_balon,      "hava"),
    ("ucak",       kontur_ucak,       "hava"),
    ("helikopter", kontur_helikopter, "hava"),
    ("traktor",    kontur_traktor,    "kara"),
    ("itfaiye",    kontur_itfaiye,    "kara"),
    ("araba",      kontur_araba,      "kara"),
    ("otobus",     kontur_otobus,     "kara"),
    ("yelkenli",   kontur_yelkenli,   "deniz"),
    ("feribot",    kontur_feribot,    "deniz"),
]]

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
    g = []
    # ortam
    g.append(_lin("gok", 0, -6, 0, 72, [(0, "#3E92CC"), (0.5, "#7FC2E8"),
                                        (0.85, "#C6E7F5"), (1, "#EAF3E2")]))
    g.append(_rad("gunes", 77, 11, 18, [(0, "#FFFDF0"), (0.35, "#FFF2BC", 0.95),
                                        (0.7, "#FFE99A", 0.4), (1, "#FFE99A", 0)]))
    g.append(_lin("cim", 0, 58, 0, 92, [(0, "#94C96A"), (0.5, "#79B551"), (1, "#5E9C41")]))
    g.append(_lin("sis", 0, 55, 0, 67, [(0, "#FFFFFF", 0.0), (0.55, "#F2FAFE", 0.55),
                                        (1, "#F2FAFE", 0.0)]))
    g.append(_lin("yol", 0, 92, 0, 136, [(0, "#7C7C84"), (0.5, "#6E6E76"), (1, "#5C5C64")]))
    g.append(_lin("su", 0, 136, 0, 186, [(0, "#72C0E6"), (0.3, "#48A3D6"),
                                         (0.7, "#2E84BC"), (1, "#1E6497")]))
    # cam: iç mekân üzerine gök yansıması
    g.append('<linearGradient id="cam" x1="0" y1="0" x2="0.6" y2="1">'
             '<stop offset="0" stop-color="#F0FAFF" stop-opacity="0.95"/>'
             '<stop offset="0.4" stop-color="#AFD6EC" stop-opacity="0.85"/>'
             '<stop offset="1" stop-color="#557E9C" stop-opacity="0.8"/></linearGradient>')
    # gövdeler (4 duraklı, metalik)
    g.append(_lin("kirmizi", 0, 94, 0, 128, [(0, "#FF8A7A"), (0.35, "#E8453A"),
                                             (0.75, "#BE2F26"), (1, "#8F211B")]))
    g.append(_lin("mavi", 0, 100, 0, 128, [(0, "#8CB8F4"), (0.35, "#4A7FDB"),
                                           (0.75, "#2F58AC"), (1, "#20407D")]))
    g.append(_lin("sari", 0, 93, 0, 128, [(0, "#FFDf78"), (0.35, "#F7B32B"),
                                          (0.75, "#DB930F"), (1, "#A96F06")]))
    g.append(_lin("yesil", 0, 84, 0, 128, [(0, "#84CC70"), (0.35, "#46983F"),
                                           (0.75, "#2E7A33"), (1, "#1E5A24")]))
    g.append(_lin("turuncu", 0, 12, 0, 53, [(0, "#FFB273"), (0.35, "#F07E2E"),
                                            (0.75, "#D2601C"), (1, "#9E4512")]))
    g.append(_lin("beyazmetal", 0, 15, 0, 52, [(0, "#FFFFFF"), (0.45, "#EFF3F6"),
                                               (0.8, "#CBD5DC"), (1, "#9FACB6")]))
    g.append(_lin("beyazmetal2", 0, 138, 0, 172, [(0, "#FFFFFF"), (0.5, "#ECF0F3"),
                                                  (1, "#B4C0C9")]))
    g.append(_lin("balonzar", 24, 6, 56, 48, [(0, "#FFE08A"), (0.45, "#EF7F2E"),
                                              (1, "#C23A28")]))
    g.append(_lin("yelkeng", 0, 134, 0, 158, [(0, "#FFFFFF"), (1, "#D4DCE3")]))
    g.append(_lin("ahsap", 0, 0, 1, 0, [(0, "#B08A5A"), (0.5, "#8A6238"), (1, "#6E4C2A")]))
    # tekerlek birim-uzay gradyanları (translate+scale ile kullanılır)
    g.append(_rad("lastik", 0, 0, 1, [(0.5, "#43434B"), (0.8, "#2A2A31"), (1, "#17171C")]))
    g.append(_rad("jant", 0, 0, 1, [(0, "#FAFBFC"), (0.5, "#DFE4E9"),
                                    (0.78, "#B7C0C8"), (1, "#79838D")]))
    g.append(_lin("krom", 0, 0, 0, 1, [(0, "#F4F7F9"), (0.45, "#C9D2D9"),
                                       (0.55, "#96A2AB"), (1, "#DFE6EB")]))
    return "<defs>" + "".join(g) + "</defs>"

# ---------------------------------------------------------------- ortak çizim parçaları
def _klip(e, ad, poly):
    e.append(f'<clipPath id="{ad}"><path d="{yol_svg(poly)}"/></clipPath>')
    return f"url(#{ad})"


def zemin_golgesi(e, cx, cy, rx):
    """Aracın altına yumuşak temas gölgesi (katmanlı)."""
    for f_rx, ry, op in [(1.0, 2.4, 0.10), (0.78, 1.8, 0.10), (0.5, 1.2, 0.12)]:
        e.append(_el("ellipse", cx=cx, cy=cy, rx=rx * f_rx, ry=ry,
                     fill="#0C1620", opacity=f"{op}"))


def yansima(e, cx, cy, rx):
    """Su üstündeki tekne yansıması."""
    for f_rx, ry, dy, op in [(0.95, 2.6, 1.6, 0.14), (0.7, 1.8, 3.6, 0.10),
                             (0.45, 1.2, 5.4, 0.07)]:
        e.append(_el("ellipse", cx=cx, cy=cy + dy, rx=rx * f_rx, ry=ry,
                     fill="#0A2A45", opacity=f"{op}"))


def teker(e, cx, cy, r, stil="araba"):
    """Gerçekçi tekerlek: lastik + diş + jant + bijon."""
    e.append(_el("ellipse", cx=cx, cy=cy + r - 0.2, rx=r * 1.05, ry=1.3,
                 fill="#0C1620", opacity=0.3))
    e.append(f'<g transform="translate({cx},{cy}) scale({r:.3f})">'
             f'<circle cx="0" cy="0" r="1" fill="url(#lastik)"/></g>')
    if stil == "traktor":
        for i in range(13):
            a = i * 360 / 13
            e.append(f'<g transform="rotate({a:.1f} {cx} {cy})">'
                     f'<rect x="{cx - r*0.09:.2f}" y="{cy - r:.2f}" width="{r*0.18:.2f}" '
                     f'height="{r*0.34:.2f}" rx="{r*0.05:.2f}" fill="#111116" '
                     f'opacity="0.9"/></g>')
        rj = r * 0.56
    else:
        for i in range(20):
            a = math.radians(i * 18)
            e.append(_el("line",
                         x1=cx + r * 0.93 * math.cos(a), y1=cy + r * 0.93 * math.sin(a),
                         x2=cx + r * 0.995 * math.cos(a), y2=cy + r * 0.995 * math.sin(a),
                         stroke="#0E0E13", stroke_width=r * 0.09, opacity=0.8))
        rj = r * (0.58 if stil == "kamyon" else 0.62)
    e.append(f'<g transform="translate({cx},{cy}) scale({rj:.3f})">'
             f'<circle cx="0" cy="0" r="1" fill="url(#jant)"/></g>')
    e.append(_el("circle", cx=cx, cy=cy, r=rj, fill="none", stroke="#FFFFFF",
                 stroke_width=0.35, opacity=0.4))
    if stil == "traktor":
        e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.9, fill="#E8B33B"))
        e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.9, fill="none", stroke="#B4831B",
                     stroke_width=0.5))
        n_b, rb = 6, rj * 0.5
    elif stil == "kamyon":
        e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.55, fill="#C7CED5"))
        n_b, rb = 6, rj * 0.72
    else:
        for i in range(5):
            a = math.radians(i * 72 - 90)
            e.append(_el("line", x1=cx, y1=cy, x2=cx + rj * 0.82 * math.cos(a),
                         y2=cy + rj * 0.82 * math.sin(a), stroke="#98A1AB",
                         stroke_width=rj * 0.3, stroke_linecap="round"))
        n_b, rb = 5, rj * 0.45
    for i in range(n_b):
        a = math.radians(i * 360 / n_b - 90 + (36 if n_b == 5 else 30))
        e.append(_el("circle", cx=cx + rb * math.cos(a), cy=cy + rb * math.sin(a),
                     r=max(0.35, rj * 0.09), fill="#5A626C"))
    e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.18, fill="#818B95"))
    e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.18, fill="none", stroke="#525A63",
                 stroke_width=0.35))
    # jant üst parlaması
    e.append(_el("path", d=f"M {cx - rj*0.7:.2f} {cy - rj*0.7:.2f} "
                           f"A {rj:.2f} {rj:.2f} 0 0 1 {cx + rj*0.5:.2f} {cy - rj*0.86:.2f}",
                 fill="none", stroke="#FFFFFF", stroke_width=0.45, opacity=0.5))


def hacim(e, klip, poly, guc=0.12):
    x0, y0, x1, y1 = poly.bounds
    w, h = x1 - x0, y1 - y0
    e.append(_el("ellipse", cx=x0 + w * 0.4, cy=y0 + h * 0.18, rx=w * 0.6, ry=h * 0.32,
                 fill="#FFFFFF", opacity=f"{guc}", clip_path=f"url(#{klip})"))
    e.append(_el("ellipse", cx=x0 + w * 0.55, cy=y1 + h * 0.02, rx=w * 0.72, ry=h * 0.26,
                 fill="#101E2A", opacity=f"{guc * 0.8}", clip_path=f"url(#{klip})"))

# ---------------------------------------------------------------- dekor
def _agac(e, x, taban, olcek=1.0):
    s = olcek
    e.append(_el("ellipse", cx=x + 1.5 * s, cy=taban + 0.4, rx=6 * s, ry=1.1 * s,
                 fill="#3E7030", opacity=0.35))
    e.append(_el("path", d=f"M {x-1.5*s} {taban} L {x-1.0*s} {taban-8.5*s} "
                           f"L {x+1.0*s} {taban-8.5*s} L {x+1.5*s} {taban} Z",
                 fill="#71512F"))
    e.append(_el("line", x1=x, y1=taban - 7.5 * s, x2=x + 3 * s, y2=taban - 11 * s,
                 stroke="#71512F", stroke_width=1.0 * s))
    for dx, dy, r, renk in [(-3.4, -11.5, 4.6, "#2E7239"), (3.4, -12, 4.8, "#3A8845"),
                            (0, -15.5, 5.2, "#469750"), (-0.2, -12, 4.3, "#55A75F")]:
        e.append(_el("circle", cx=x + dx * s, cy=taban + dy * s, r=r * s, fill=renk))
    e.append(_el("circle", cx=x - 1.8 * s, cy=taban - 14.5 * s, r=2.6 * s, fill="#68B872",
                 opacity=0.8))


def _ahir(e):
    e.append(_el("ellipse", cx=153, cy=90.6, rx=19, ry=1.6, fill="#3E7030", opacity=0.3))
    e.append(_el("path", d="M 136 90 L 136 74 L 152 65 L 168 74 L 168 90 Z", fill="#B8483D"))
    e.append(_el("path", d="M 136 90 L 136 74 L 152 65 L 152 90 Z", fill="#CE5A4C"))
    for yy in (77.5, 81.5, 85.5, 89.2):
        e.append(_el("line", x1=136.4, y1=yy, x2=167.6, y2=yy, stroke="#96382F",
                     stroke_width=0.55, opacity=0.75))
    e.append(_el("path", d="M 132.5 76 L 152 64.5 L 171.5 76 L 168.2 76 L 152 66.8 "
                           "L 135.8 76 Z", fill="#6E2C25"))
    e.append(_el("path", d="M 133.5 75.6 L 152 64.9 L 170.5 75.6", fill="none",
                 stroke="#874138", stroke_width=0.7))
    e.append(_el("rect", x=146.5, y=78.5, width=11, height=11.5, rx=0.7, fill="#5E241D"))
    e.append(_el("rect", x=147.5, y=79.5, width=9, height=10.5, fill="#7C3128"))
    e.append(_el("path", d="M 147.5 79.5 L 156.5 90 M 156.5 79.5 L 147.5 90",
                 stroke="#5E241D", stroke_width=1.0, fill="none"))
    e.append(_el("circle", cx=152, cy=71.2, r=2.4, fill="#F1E9D4"))
    e.append(_el("circle", cx=152, cy=71.2, r=2.4, fill="none", stroke="#6E2C25",
                 stroke_width=0.7))
    e.append(_el("path", d="M 149.6 71.2 L 154.4 71.2 M 152 68.8 L 152 73.6",
                 stroke="#6E2C25", stroke_width=0.5, fill="none"))
    # temel taşları
    e.append(_el("rect", x=136, y=88.6, width=32, height=1.6, fill="#8A8072", opacity=0.9))


def _yeldegirmeni(e):
    e.append(_el("ellipse", cx=268, cy=90.4, rx=8, ry=1.3, fill="#3E7030", opacity=0.3))
    e.append(_el("path", d="M 262.5 90 L 265 70 L 271 70 L 273.5 90 Z", fill="#E7DFC8"))
    e.append(_el("path", d="M 262.5 90 L 265 70 L 268 70 L 268 90 Z", fill="#D2C8AC"))
    e.append(_el("line", x1=263.6, y1=82, x2=272.6, y2=82, stroke="#B5A98C",
                 stroke_width=0.6))
    e.append(_el("rect", x=266.2, y=84.5, width=3.6, height=5.5, rx=1.6, fill="#6E5638"))
    e.append(_el("path", d="M 264.4 70 A 3.6 3.6 0 0 1 271.6 70 Z", fill="#9E4438"))
    for a0 in (35, 125, 215, 305):
        a = math.radians(a0)
        x2, y2 = 268 + 12 * math.cos(a), 68.5 + 12 * math.sin(a)
        e.append(_el("line", x1=268, y1=68.5, x2=x2, y2=y2, stroke="#5E452C",
                     stroke_width=1.2))
        # kafes kanat
        for t in (0.35, 0.55, 0.75, 0.95):
            px, py = 268 + 12 * t * math.cos(a), 68.5 + 12 * t * math.sin(a)
            e.append(_el("line", x1=px, y1=py, x2=px + 3.4 * math.cos(a + 0.55),
                         y2=py + 3.4 * math.sin(a + 0.55), stroke="#5E452C",
                         stroke_width=0.55, opacity=0.9))
        e.append(_el("line", x1=268 + 4 * math.cos(a) + 3.3 * math.cos(a + 0.55),
                     y1=68.5 + 4 * math.sin(a) + 3.3 * math.sin(a + 0.55),
                     x2=268 + 11.6 * math.cos(a) + 3.3 * math.cos(a + 0.55),
                     y2=68.5 + 11.6 * math.sin(a) + 3.3 * math.sin(a + 0.55),
                     stroke="#5E452C", stroke_width=0.5, opacity=0.85))
    e.append(_el("circle", cx=268, cy=68.5, r=1.5, fill="#3E2E1C"))


def _bulut(e, bx, by, s, op):
    blob = [(-8, 1.2, 4.4), (-3, -2.8, 5.8), (3.6, -1.2, 5.2), (9, 1.2, 3.9), (0.6, 1.8, 5)]
    for dx, dy, r in blob:
        e.append(_el("circle", cx=bx + dx * s * 1.6, cy=by + dy * s * 1.6,
                     r=r * s * 1.6, fill="#FDFEFF", opacity=op))
    for dx, dy, r in blob:
        e.append(_el("circle", cx=bx + dx * s * 1.6, cy=by + (dy + 1.6) * s * 1.6,
                     r=r * s * 1.45, fill="#C2D8E6", opacity=op * 0.35))
    e.append(_el("ellipse", cx=bx, cy=by + 4.4 * s, rx=14 * s * 1.4, ry=2.4 * s,
                 fill="#FDFEFF", opacity=op))


def _marti(e, x, y, s=1.0):
    e.append(_el("path", d=f"M {x-3.6*s} {y} Q {x-1.8*s} {y-2.2*s} {x} {y} "
                           f"Q {x+1.8*s} {y-2.2*s} {x+3.6*s} {y}",
                 fill="none", stroke="#4E5B66", stroke_width=0.75 * s,
                 stroke_linecap="round"))

# ---------------------------------------------------------------- sahne
def sahne_svg():
    rnd = random.Random(37)
    e = [tanimlar()]
    # --- gökyüzü + sirus bulutları + güneş
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=76, fill="url(#gok)"))
    for sx, sy, sw in [(120, 9, 60), (215, 17, 48), (25, 22, 40)]:
        e.append(_el("path", d=f"M {sx} {sy} q {sw*0.5} {-2.2} {sw} 0",
                     fill="none", stroke="#FFFFFF", stroke_width=1.6, opacity=0.16,
                     stroke_linecap="round"))
    e.append(_el("circle", cx=77, cy=11, r=18, fill="url(#gunes)"))
    e.append(_el("circle", cx=77, cy=11, r=6.2, fill="#FFF6D8"))
    e.append(_el("circle", cx=77, cy=11, r=6.2, fill="none", stroke="#FFE9A0",
                 stroke_width=1.4, opacity=0.7))
    _bulut(e, 148, 12, 1.0, 0.95)
    _bulut(e, 192, 27, 0.65, 0.9)
    _bulut(e, 26, 39, 0.55, 0.85)
    _bulut(e, 301, 56, 0.5, 0.8)
    _marti(e, 66, 31, 1.0)
    _marti(e, 184, 21, 0.75)
    # --- uzak tepeler: iki yumuşak silsile + ağaç sırası + ufuk pusu
    e.append(_el("path", d="M -6 63 Q 30 54.5 78 59.5 Q 130 64.5 190 60 Q 240 56 326 62 "
                           "L 326 74 L -6 74 Z", fill="#C8E1B2", opacity=0.95))
    for hx, hy in [(12, 60), (28, 57.8), (46, 57.2), (66, 58.8), (112, 61.5),
                   (154, 62.8), (178, 62), (200, 60.2), (222, 58.4), (246, 56.9),
                   (282, 58), (300, 58.8), (314, 60)]:
        e.append(_el("circle", cx=hx, cy=hy, r=1.9, fill="#8FBE74", opacity=0.6))
        e.append(_el("circle", cx=hx + 2.4, cy=hy + 0.7, r=1.4, fill="#7FB264",
                     opacity=0.5))
    e.append(_el("path", d="M -6 66.5 Q 60 60.5 130 64.5 Q 200 69 258 64.5 "
                           "Q 292 62 326 65 L 326 76 L -6 76 Z", fill="#ABD28E"))
    e.append(_el("rect", x=-6, y=55, width=W + 12, height=12, fill="url(#sis)"))
    # --- çimen
    e.append(_el("rect", x=-6, y=64, width=W + 12, height=28.5, fill="url(#cim)"))
    for fx, fy, renk in [(100, 88, "#F2D64B"), (128, 85.5, "#E8734D"), (198, 87, "#F2D64B"),
                         (222, 84.5, "#E8734D"), (244, 88, "#F5F0E6"), (290, 86, "#E8734D"),
                         (108, 84, "#F5F0E6")]:
        e.append(_el("line", x1=fx, y1=fy + 2.6, x2=fx, y2=fy, stroke="#42802F",
                     stroke_width=0.6))
        e.append(_el("circle", cx=fx, cy=fy, r=0.95, fill=renk))
        e.append(_el("circle", cx=fx, cy=fy, r=0.35, fill="#7C5E18"))
    for _ in range(70):                                # çim öbekleri
        tx = rnd.uniform(84, 318)
        ty = rnd.uniform(66, 90.5)
        e.append(_el("path", d=f"M {tx:.1f} {ty:.1f} q 0.9 -2.2 1.8 0",
                     fill="none", stroke="#528F3C", stroke_width=0.5, opacity=0.55))
    _agac(e, 98, 91, 1.0)
    _agac(e, 121, 89.5, 0.78)
    _ahir(e)
    _agac(e, 185, 90.5, 1.0)
    _yeldegirmeni(e)
    _agac(e, 303, 90, 0.72)
    # ahırdan yola inen toprak patika (çit kapısına)
    e.append(_el("path", d="M 146 90 L 158 90 L 166 92 L 138 92 Z", fill="#D9C49A",
                 opacity=0.9))
    e.append(_el("path", d="M 148 90 L 156 90 L 161 91.6 L 143 91.6 Z", fill="#C9B183",
                 opacity=0.7))
    for pdx, pdy in [(147, 91.1), (152.5, 90.6), (158, 91.3), (149.5, 91.7)]:
        e.append(_el("circle", cx=pdx, cy=pdy, r=0.28, fill="#A8916A"))
    # ahşap çiftlik çiti (patika hizasında kapı boşluğu; traktörün sağından başlar)
    citler = [(-6.0, 7.2), (84.0, 139.0), (165.0, 316.0)]
    for cx1, cx2 in citler:
        for ry in (88.3, 90.3):
            e.append(_el("rect", x=cx1, y=ry, width=cx2 - cx1, height=0.85, rx=0.4,
                         fill="#A5825A"))
            e.append(_el("rect", x=cx1, y=ry + 0.62, width=cx2 - cx1, height=0.23,
                         fill="#7C5E3C", opacity=0.8))
    direkler = [-2.0, 4.0] + [float(px) for px in range(86, 139, 11)] + \
               [float(px) for px in range(167, 316, 11)]
    for px in direkler:
        e.append(_el("rect", x=px - 0.8, y=87.4, width=1.6, height=4.6, rx=0.35,
                     fill="#8A6A42"))
        e.append(_el("rect", x=px - 0.8, y=87.4, width=0.55, height=4.6, fill="#A5825A",
                     opacity=0.8))
    for px in (139.0, 165.0):   # kapı direkleri biraz yüksek
        e.append(_el("rect", x=px - 0.95, y=86.8, width=1.9, height=5.2, rx=0.4,
                     fill="#7C5E3C"))
    # --- yol (asfalt dokusu + şerit çizgileri + rögar)
    e.append(_el("rect", x=-6, y=92, width=W + 12, height=44, fill="url(#yol)"))
    e.append(_el("rect", x=-6, y=92, width=W + 12, height=2, fill="#B9B9BF"))
    e.append(_el("rect", x=-6, y=94, width=W + 12, height=0.8, fill="#4A4A52", opacity=0.7))
    # taş rıhtım duvarı (yol ile deniz arasında)
    e.append(_el("rect", x=-6, y=132.4, width=W + 12, height=0.8, fill="#4A4A52",
                 opacity=0.7))
    e.append(_el("rect", x=-6, y=133.2, width=W + 12, height=2.8, fill="#9C9CA4"))
    e.append(_el("rect", x=-6, y=133.2, width=W + 12, height=0.6, fill="#C9C9CF"))
    e.append(_el("line", x1=-6, y1=134.8, x2=W + 6, y2=134.8, stroke="#7E7E86",
                 stroke_width=0.3, opacity=0.7))
    for i, jx in enumerate(range(-6, 326, 8)):
        e.append(_el("line", x1=jx + (4 if i % 2 else 0), y1=133.9,
                     x2=jx + (4 if i % 2 else 0), y2=134.8, stroke="#7E7E86",
                     stroke_width=0.35, opacity=0.8))
        e.append(_el("line", x1=jx, y1=134.8, x2=jx, y2=136, stroke="#7E7E86",
                     stroke_width=0.35, opacity=0.8))
    for _ in range(300):                               # asfalt benekleri
        px, py = rnd.uniform(-4, 322), rnd.uniform(95.5, 131.5)
        koyu = rnd.random() < 0.55
        e.append(_el("circle", cx=f"{px:.1f}", cy=f"{py:.1f}",
                     r=f"{rnd.uniform(0.1, 0.32):.2f}",
                     fill="#26262C" if koyu else "#B9B9BF",
                     opacity="0.35" if koyu else "0.22"))
    for ty in (103.5, 117.5):                          # lastik aşınma izleri
        e.append(_el("rect", x=-6, y=ty, width=W + 12, height=4.6, fill="#3A3A40",
                     opacity=0.10))
    e.append(_el("rect", x=-6, y=95.4, width=W + 12, height=1.1, fill="#E9E9E4",
                 opacity=0.85))
    e.append(_el("rect", x=-6, y=130.6, width=W + 12, height=1.1, fill="#E9E9E4",
                 opacity=0.85))
    x = -4
    while x < W + 6:                                   # orta şerit
        e.append(_el("rect", x=x, y=112.9, width=11, height=2.4, rx=0.5,
                     fill="#E9E9E4", opacity=0.9))
        x += 27
    e.append(f'<g transform="translate(170,99.2)">'
             f'<circle cx="0" cy="0" r="2.3" fill="#4A4A52"/>'
             f'<circle cx="0" cy="0" r="2.3" fill="none" stroke="#2E2E34" stroke-width="0.5"/>'
             f'<path d="M -1.4 -0.8 L 1.4 -0.8 M -1.7 0 L 1.7 0 M -1.4 0.8 L 1.4 0.8" '
             f'stroke="#2E2E34" stroke-width="0.4"/></g>')
    # rıhtım babaları
    for bx in (22, 84, 170, 233, 305):
        e.append(_el("path", d=f"M {bx-1.3} 136 L {bx-1.1} 133.6 A 1.35 1.1 0 0 1 "
                               f"{bx+1.1} 133.6 L {bx+1.3} 136 Z", fill="#2E343B"))
        e.append(_el("ellipse", cx=bx, cy=133.5, rx=1.35, ry=0.75, fill="#4A525B"))
    # --- deniz
    e.append(_el("rect", x=-6, y=136, width=W + 12, height=50, fill="url(#su)"))
    e.append(_el("rect", x=-6, y=136, width=W + 12, height=1.2, fill="#CBE9F6",
                 opacity=0.85))
    for wy, op in [(139.5, 0.10), (145.5, 0.09), (152.5, 0.08), (161, 0.07), (172, 0.06)]:
        e.append(_el("rect", x=-6, y=wy, width=W + 12, height=1.15, fill="#E8F6FD",
                     opacity=f"{op + 0.04}"))
        e.append(_el("rect", x=-6, y=wy + 1.15, width=W + 12, height=0.7, fill="#0E3A5E",
                     opacity=f"{op * 0.6}"))
    for _ in range(60):                                # güneş parıltısı
        px, py = rnd.uniform(30, 150), rnd.uniform(137.5, 152)
        e.append(_el("circle", cx=f"{px:.1f}", cy=f"{py:.1f}",
                     r=f"{rnd.uniform(0.15, 0.4):.2f}", fill="#FFFFFF",
                     opacity=f"{rnd.uniform(0.15, 0.4):.2f}"))
    for wx, wy, s in [(24, 147, 1), (118, 143.5, 0.8), (152, 159, 1.05), (28, 167, 0.9),
                      (124, 174, 1.0), (176, 168.5, 0.8), (301, 147, 0.85), (305, 169, 0.8)]:
        e.append(_el("path", d=f"M {wx} {wy} q {5*s} {-2.6} {10*s} 0 q {5*s} {2.6} {10*s} 0",
                     fill="none", stroke="#D6EFFA", stroke_width=1.3 * s,
                     stroke_linecap="round", opacity=0.75))
    # şamandıra
    e.append(_el("ellipse", cx=169.7, cy=167, rx=3.6, ry=1.0, fill="#0A2A45", opacity=0.25))
    e.append(_el("path", d="M 168 166 L 171.4 166 L 170.9 159.8 L 168.5 159.8 Z",
                 fill="#D6473B"))
    e.append(_el("path", d="M 168.15 165.2 L 171.25 165.2 L 171.1 163.4 L 168.3 163.4 Z",
                 fill="#F1E9D4"))
    e.append(_el("circle", cx=169.7, cy=158.9, r=0.9, fill="#FFD23F"))
    e.append(_el("circle", cx=169.7, cy=158.9, r=0.9, fill="none", stroke="#8F7B22",
                 stroke_width=0.3))
    # --- zemin gölgeleri + su yansımaları, sonra araçlar
    e += zemin_katmani()
    e += arac_detaylari()
    # --- parça dış çizgileri (ince — kesim payını gizler)
    for _, poly, _ in PARCALAR:
        e.append(_el("path", d=yol_svg(poly), fill="none", stroke="#1C2833",
                     stroke_width=0.7, stroke_linejoin="round", opacity=0.8))
    return e

# ---------------------------------------------------------------- araç detayları
def arac_detaylari():
    e = []
    P = {ad: poly for ad, poly, _ in PARCALAR}

    # ============ BALON ============
    b = P["balon"]
    kb = _klip(e, "kbalon", b)
    e.append(_el("path", d=yol_svg(b), fill="url(#balonzar)"))
    # dilimler: kubbe tepesinden boğaza kavisli gore'lar
    renkler = ["#B92F26", "#E8DCC2", "#31648F", "#E8DCC2", "#B92F26",
               "#E8DCC2", "#31648F"]
    for i, ofs in enumerate((-15, -10, -5, 0, 5, 10, 15)):
        e.append(_el("path",
                     d=f"M {42+ofs*0.12} 6.8 C {42+ofs*1.95} 16 {42+ofs*1.95} 32 "
                       f"{42+ofs*0.5} 44.5 L {42+ofs*0.5-1.6} 44.5 C {42+ofs*1.6} 32 "
                       f"{42+ofs*1.6} 16 {42+ofs*0.12-1.2} 6.8 Z",
                     fill=renkler[i], opacity=0.9, clip_path=kb))
    # yatay yük bantları
    for yy, rx in [(18, 16.2), (28, 17.2)]:
        e.append(_el("path", d=f"M {42-rx} {yy} Q 42 {yy+3} {42+rx} {yy}",
                     fill="none", stroke="#6E2018", stroke_width=0.55, opacity=0.5,
                     clip_path=kb))
    # taç plakası + havalandırma
    e.append(_el("circle", cx=42, cy=8.6, r=2.2, fill="#7C241C", clip_path=kb))
    # brülör alevi + çerçevesi
    e.append(_el("path", d="M 40.6 41 L 43.4 41 L 43 44 L 41 44 Z", fill="#3A4048",
                 clip_path=kb))
    e.append(_el("path", d="M 41.4 40.8 C 40.6 39 41.2 37.6 42 36.6 C 42.8 37.6 43.4 39 "
                           "42.6 40.8 Z", fill="#FFB33B", clip_path=kb))
    e.append(_el("path", d="M 41.8 40.6 C 41.4 39.4 41.8 38.6 42 38.2 C 42.2 38.6 42.6 39.4 "
                           "42.2 40.6 Z", fill="#FFE9A0", clip_path=kb))
    # halatlar
    for x1, x2 in [(33.8, 36.8), (50.2, 47.2), (42, 42)]:
        e.append(_el("line", x1=x1, y1=40.5, x2=x2, y2=44.6, stroke="#4E3826",
                     stroke_width=0.7, opacity=0.9))
    # sepet: hasır örgü + deri bant
    e.append(_el("rect", x=35.8, y=44.2, width=12.4, height=5.6, rx=1.0, fill="#96703F",
                 clip_path=kb))
    for yy in (45.6, 47.0, 48.4):
        e.append(_el("path", d=f"M 35.8 {yy} q 1.55 0.9 3.1 0 q 1.55 -0.9 3.1 0 "
                               f"q 1.55 0.9 3.1 0 q 1.55 -0.9 3.1 0",
                     fill="none", stroke="#6E4C24", stroke_width=0.5, opacity=0.85))
    for xx in (38.3, 40.8, 43.3, 45.8):
        e.append(_el("line", x1=xx, y1=44.2, x2=xx, y2=49.8, stroke="#7C5A2E",
                     stroke_width=0.45, opacity=0.7))
    e.append(_el("rect", x=35.8, y=43.9, width=12.4, height=1.3, rx=0.6, fill="#5E3E1E",
                 clip_path=kb))
    e.append(_el("rect", x=35.8, y=49.1, width=12.4, height=0.9, fill="#5E3E1E",
                 clip_path=kb, opacity=0.9))
    # ışık/gölge
    e.append(_el("ellipse", cx=34, cy=17, rx=9, ry=12, fill="#FFFFFF", opacity=0.30,
                 clip_path=kb))
    e.append(_el("ellipse", cx=53, cy=26, rx=7, ry=13, fill="#5E1408", opacity=0.16,
                 clip_path=kb))

    # ============ UÇAK ============
    u = P["ucak"]
    ku = _klip(e, "kucak", u)
    e.append(_el("path", d=yol_svg(u), fill="url(#beyazmetal)"))
    # gümüş karın + cheatline (pencere hattı şeridi)
    e.append(_el("path", d="M 96 34.6 L 174 34.6 L 174 40 L 96 40 Z", fill="#9AA7B2",
                 opacity=0.8, clip_path=ku))
    e.append(_el("path", d="M 96 33.2 L 172.5 33.2 L 172.5 34.4 L 96 34.4 Z",
                 fill="#C22F27", clip_path=ku))
    e.append(_el("path", d="M 96 34.4 L 172.5 34.4 L 172.5 35.0 L 96 35.0 Z",
                 fill="#1F3A5C", clip_path=ku))
    # gövde panel çizgileri
    for px in (112, 126, 140, 154):
        e.append(_el("line", x1=px, y1=26.6, x2=px, y2=36.6, stroke="#8C99A4",
                     stroke_width=0.3, opacity=0.5))
    # dikey kuyruk: kırmızı + rudder çizgisi + logo
    e.append(_el("path", d="M 97 15.5 L 104.5 15.5 L 116 29.2 L 106.5 31.8 L 97 24 Z",
                 fill="#C22F27", clip_path=ku))
    e.append(_el("path", d="M 100.8 15.5 L 97 15.5 L 97 24 L 103 28.9 Z", fill="#8F1F19",
                 clip_path=ku, opacity=0.9))
    e.append(_el("line", x1=101.5, y1=16.2, x2=98.6, y2=27.4, stroke="#7A1B15",
                 stroke_width=0.4, opacity=0.8))
    e.append(_el("circle", cx=107.5, cy=22.5, r=2.5, fill="#F4F7F9", opacity=0.95))
    e.append(_el("path", d="M 106.2 23.6 Q 107.5 20.4 108.9 21.6 Q 107.9 22 107.5 24.2 Z",
                 fill="#C22F27"))
    # yatay kuyruk
    e.append(_el("path", d="M 97 29.5 L 89.5 35 L 89.5 37.5 L 102 33 Z", fill="#B7C2CB",
                 clip_path=ku))
    e.append(_el("line", x1=91, y1=34.6, x2=99.5, y2=31.6, stroke="#8C99A4",
                 stroke_width=0.35, opacity=0.7))
    # kokpit: iki panel cam
    e.append(_el("path", d="M 165.5 28.0 L 169.6 28.3 C 171.6 28.9 173 29.9 173.8 31.2 "
                           "L 165.2 30.8 Z", fill="#101E28", clip_path=ku))
    e.append(_el("path", d="M 166.2 28.4 L 168.8 28.55 L 168.5 30.5 L 165.9 30.4 Z",
                 fill="#7FB6D9", opacity=0.9))
    e.append(_el("path", d="M 169.8 28.75 L 171.6 29.2 L 172.6 30.7 L 169.5 30.55 Z",
                 fill="#5E96BC", opacity=0.9))
    # burun radom dikişi + pito
    e.append(_el("path", d="M 171.2 28.9 A 6 6 0 0 1 171.2 34.4", fill="none",
                 stroke="#9AA7B2", stroke_width=0.4, opacity=0.8, clip_path=ku))
    # yolcu pencereleri (küçük, sık) + kapılar
    for i in range(11):
        wx = 111 + i * 4.6
        e.append(_el("rect", x=wx, y=30.0, width=1.7, height=2.4, rx=0.85,
                     fill="#15242E"))
        e.append(_el("rect", x=wx + 0.3, y=30.3, width=0.75, height=1.0, rx=0.35,
                     fill="#8FC3E4", opacity=0.9))
    for kx in (108.2, 160.8):
        e.append(_el("rect", x=kx, y=28.8, width=2.1, height=6.2, rx=1.0, fill="none",
                     stroke="#AAB6C0", stroke_width=0.4, opacity=0.9))
    # tescil
    e.append(_el("text", x=104, y=39.2, icerik="TC-EGE", fill="#55606A", font_size="2.1",
                 font_family="sans-serif", font_weight="bold", letter_spacing="0.3"))
    # kanat: üst yüzey + panel + kırmızı uç
    e.append(_el("path", d="M 131 34 L 153 34 L 128 50.5 L 119 50.5 Z", fill="#C7D1D9",
                 clip_path=ku))
    e.append(_el("path", d="M 131 34 L 153 34 L 148.5 37 L 129 37 Z", fill="#A9B6C0",
                 clip_path=ku))
    e.append(_el("path", d="M 128.4 48.3 L 130.7 48.3 L 128 50.5 L 119 50.5 L 121.4 48.3 Z",
                 fill="#C22F27", clip_path=ku, opacity=0.95))
    e.append(_el("line", x1=137, y1=36.4, x2=126, y2=46.6, stroke="#8C99A4",
                 stroke_width=0.35, opacity=0.6))
    e.append(_el("line", x1=145, y1=35.2, x2=133.5, y2=45.8, stroke="#8C99A4",
                 stroke_width=0.3, opacity=0.5))
    # motor: kaporta + giriş dudağı + fan + pilon
    e.append(_el("path", d="M 146 38.9 L 150 36.2 L 152.5 36.2 L 150.5 39.1 Z",
                 fill="#8C99A4", clip_path=ku))
    e.append(_el("rect", x=139.6, y=38.7, width=15.6, height=7.0, rx=3.0, fill="#B7C2CB",
                 clip_path=ku))
    e.append(_el("rect", x=139.6, y=38.7, width=15.6, height=2.4, rx=1.2, fill="#DDE4E9",
                 clip_path=ku, opacity=0.9))
    e.append(_el("rect", x=139.6, y=43.4, width=15.6, height=2.3, rx=1.1, fill="#7C8894",
                 clip_path=ku, opacity=0.8))
    e.append(_el("ellipse", cx=154.6, cy=42.2, rx=1.9, ry=3.3, fill="#1A252E",
                 clip_path=ku))
    e.append(_el("ellipse", cx=154.4, cy=42.2, rx=1.5, ry=2.8, fill="#3C4854",
                 clip_path=ku))
    e.append(_el("path", d="M 154.4 40.2 L 154.4 44.2 M 153.2 42.2 L 155.6 42.2",
                 stroke="#5E6E7A", stroke_width=0.4, clip_path=ku))
    e.append(_el("circle", cx=154.4, cy=42.2, r=0.55, fill="#9AA7B2"))
    e.append(_el("ellipse", cx=140.2, cy=42.3, rx=1.0, ry=1.9, fill="#55606A",
                 clip_path=ku))
    hacim(e, "kucak", u, 0.10)

    # ============ HELİKOPTER (112 hava ambulansı) ============
    h = P["helikopter"]
    kh = _klip(e, "kheli", h)
    e.append(_el("path", d=yol_svg(h), fill="url(#beyazmetal)"))
    # motor kaportası: gri panel + soğutma ızgarası + egzoz
    e.append(_el("rect", x=243.6, y=22.2, width=17.8, height=6.2, rx=2.2, fill="#D5DDE3",
                 clip_path=kh))
    e.append(_el("rect", x=243.6, y=22.2, width=17.8, height=1.6, rx=0.8, fill="#EDF1F4",
                 clip_path=kh, opacity=0.9))
    for gx in (245.8, 247.6, 249.4):
        e.append(_el("line", x1=gx, y1=23.6, x2=gx, y2=26.6, stroke="#9AA7B2",
                     stroke_width=0.5, opacity=0.9))
    e.append(_el("ellipse", cx=259.9, cy=25.0, rx=1.7, ry=1.2, fill="#55606A",
                 clip_path=kh))
    e.append(_el("ellipse", cx=260.4, cy=25.0, rx=1.0, ry=0.8, fill="#1E2830",
                 clip_path=kh))
    # kırmızı gövde kuşağı + bom şeridi (112 hattı)
    e.append(_el("path", d="M 230.5 37.4 C 243 34.2 258 34.4 269 37.0 L 269 41.0 "
                           "C 258 38.4 243 38.2 232.2 41.6 Z", fill="#D8352B",
                 clip_path=kh))
    e.append(_el("path", d="M 230.5 37.4 C 243 34.2 258 34.4 269 37.0 L 269 38.1 "
                           "C 258 35.6 243 35.4 231.0 38.5 Z", fill="#A8241C",
                 clip_path=kh, opacity=0.85))
    e.append(_el("path", d="M 267.5 29.7 L 291.6 27.7 L 291.6 29.9 L 267.5 32.0 Z",
                 fill="#D8352B", clip_path=kh))
    e.append(_el("path", d="M 267.5 31.2 L 291.6 29.2 L 291.6 29.9 L 267.5 32.0 Z",
                 fill="#A8241C", clip_path=kh, opacity=0.8))
    # kuyruk dikmesi: beyaz + kırmızı tepe + iki palalı kuyruk rotoru
    e.append(_el("path", d="M 290.5 19.5 L 295 19.5 L 295.9 26.2 L 289.1 26.2 Z",
                 fill="#D8352B", clip_path=kh))
    e.append(_el("path", d="M 288.3 33.0 L 296.6 33.0 L 297 35.5 L 287.8 35.5 Z",
                 fill="#B7C2CB", clip_path=kh, opacity=0.9))
    e.append(f'<g transform="rotate(24 292.9 27.6)">'
             f'<rect x="292.1" y="22.3" width="1.6" height="10.6" rx="0.8" '
             f'fill="#2A3138"/></g>')
    e.append(_el("circle", cx=292.9, cy=27.6, r=1.1, fill="#7A838C"))
    e.append(_el("circle", cx=292.9, cy=27.6, r=0.45, fill="#3C4854"))
    e.append(_el("text", x=292.6, y=31.6, icerik="TC-HLK", fill="#55606A",
                 font_size="1.45", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle"))
    # yatay stabilizatör
    e.append(_el("rect", x=277.9, y=26.4, width=6.7, height=2.0, rx=0.9, fill="#B7C2CB",
                 clip_path=kh))
    e.append(_el("line", x1=278.2, y1=28.1, x2=284.4, y2=28.1, stroke="#7C8894",
                 stroke_width=0.4, opacity=0.8))
    # ana rotor: koyu palalar + kırmızı uçlar + göbek/mil
    e.append(_el("path", d="M 224.9 11.0 L 285.1 11.0 L 285.1 15.4 L 224.9 15.4 Z",
                 fill="#2A3138", clip_path=kh))
    e.append(_el("rect", x=225.6, y=11.6, width=59, height=1.0, fill="#4A545E",
                 clip_path=kh, opacity=0.8))
    for tx in (225.3, 282.3):
        e.append(_el("rect", x=tx, y=11.1, width=2.4, height=4.2, fill="#D8352B",
                     opacity=0.95, clip_path=kh))
    e.append(_el("rect", x=248.6, y=12.4, width=8.8, height=2.0, rx=0.9, fill="#4A545E"))
    e.append(_el("rect", x=251.1, y=15.4, width=3.4, height=8.4, fill="#3C4854",
                 clip_path=kh))
    e.append(_el("circle", cx=252.8, cy=13.3, r=1.8, fill="#7A838C"))
    e.append(_el("circle", cx=252.8, cy=13.3, r=0.75, fill="#B7C2CB"))
    # kokpit: buruna sarılan cam + iç mekân + silecek
    e.append(_el("path", d="M 252.5 24.6 C 262.5 25.0 270.3 29.3 272.3 34.6 C 273 38.3 "
                           "269.6 41.9 264.1 42.3 L 259.7 42.3 C 256.4 39.4 253.4 32.4 "
                           "252.5 24.6 Z", fill="#14212C", clip_path=kh))
    e.append(_el("path", d="M 253.4 25.4 C 262.4 25.8 269.4 29.8 271.3 34.7 C 271.9 37.9 "
                           "269.1 41.0 264.3 41.4 L 260.3 41.4 C 257.6 38.7 254.3 32.4 "
                           "253.4 25.4 Z", fill="url(#cam)", opacity=0.92))
    e.append(_el("path", d="M 258.7 40.9 C 258.1 38.4 257.4 34.9 257.2 32.4 L 259.3 32.4 "
                           "C 259.8 32.4 260.2 32.8 260.2 33.4 L 260.2 40.9 Z",
                 fill="#101A22", opacity=0.5))
    e.append(_el("circle", cx=258.6, cy=30.9, r=1.3, fill="#101A22", opacity=0.5))
    e.append(_el("path", d="M 253.0 25.3 C 253.9 32.6 256.7 39.2 259.6 41.9", fill="none",
                 stroke="#9AA7B2", stroke_width=0.6, opacity=0.9, clip_path=kh))
    e.append(_el("path", d="M 264.6 25.9 L 266.4 41.7", stroke="#DDE4E9",
                 stroke_width=0.45, fill="none", opacity=0.7))
    e.append(_el("path", d="M 255.2 26.6 L 259.4 26.2 L 257.2 31.6 Z", fill="#FFFFFF",
                 opacity=0.5))
    e.append(_el("path", d="M 267.6 30.4 Q 270.0 32.4 270.8 35.2", fill="none",
                 stroke="#FFFFFF", stroke_width=0.9, opacity=0.45))
    e.append(_el("path", d="M 262.4 40.6 L 265.6 34.8", stroke="#0E1922",
                 stroke_width=0.45, fill="none", opacity=0.8))
    # çene camı
    e.append(_el("ellipse", cx=265.8, cy=43.3, rx=2.0, ry=1.05, fill="#14212C",
                 clip_path=kh))
    e.append(_el("ellipse", cx=265.8, cy=43.1, rx=1.5, ry=0.75, fill="#6FA8CE",
                 clip_path=kh))
    # kayar kapı: dikiş + pencere + kulp
    e.append(_el("rect", x=238.8, y=27.6, width=12.6, height=15.2, rx=2.4, fill="none",
                 stroke="#9AA7B2", stroke_width=0.5, opacity=0.9, clip_path=kh))
    e.append(_el("rect", x=240.8, y=29.3, width=8.4, height=7.0, rx=1.6, fill="#14212C"))
    e.append(_el("rect", x=241.4, y=29.9, width=7.2, height=5.8, rx=1.2, fill="url(#cam)",
                 opacity=0.95))
    e.append(_el("path", d="M 242.0 30.2 L 244.4 30.2 L 242.6 35.4 L 241.7 35.4 Z",
                 fill="#FFFFFF", opacity=0.45))
    e.append(_el("rect", x=246.8, y=36.9, width=2.8, height=0.9, rx=0.45, fill="#55606A"))
    # 112 + görev yazısı (kapının solunda)
    e.append(_el("text", x=235.0, y=33.3, icerik="112", fill="#C42A20", font_size="4.3",
                 font_family="sans-serif", font_weight="bold", text_anchor="middle",
                 letter_spacing="0.4"))
    e.append(_el("text", x=248.5, y=40.1, icerik="ACİL SAĞLIK", fill="#FFFFFF",
                 font_size="1.7", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle", letter_spacing="0.3"))
    # kızaklar: çelik tüp + parlama + ayaklar
    e.append(_el("path", d="M 233.5 50.2 L 272.5 50.2", stroke="#3C4854",
                 stroke_width=3.2, stroke_linecap="round", clip_path=kh))
    e.append(_el("path", d="M 233.8 49.4 L 272.2 49.4", stroke="#9AA7B2",
                 stroke_width=0.9, stroke_linecap="round", clip_path=kh, opacity=0.8))
    for sx in (244.1, 262.6):
        e.append(_el("rect", x=sx - 2.1, y=43.5, width=4.2, height=6.5, fill="#3C4854",
                     clip_path=kh))
        e.append(_el("rect", x=sx - 2.1, y=43.5, width=1.2, height=6.5, fill="#55636F",
                     clip_path=kh))
    hacim(e, "kheli", h, 0.10)

    # ============ TRAKTÖR ============
    t = P["traktor"]
    kt = _klip(e, "ktraktor", t)
    e.append(_el("path", d=yol_svg(t), fill="url(#yesil)"))
    # kaput: yüzey + havalandırma + marka şeridi
    e.append(_el("path", d="M 16.8 101 L 42.5 99.6 L 45.4 103.8 L 45.4 111.2 L 16.8 111.2 Z",
                 fill="#3F8E3D", clip_path=kt))
    e.append(_el("path", d="M 16.8 100.9 L 42.5 99.5 L 42.9 100.2 L 16.8 101.6 Z",
                 fill="#7CC868", clip_path=kt, opacity=0.8))
    e.append(_el("path", d="M 16.8 107 L 45.4 107 L 45.4 111.2 L 16.8 111.2 Z",
                 fill="#26652B", clip_path=kt, opacity=0.95))
    for i, gx in enumerate(range(26, 40, 3)):
        e.append(_el("rect", x=gx, y=102.4, width=1.7, height=3.2, rx=0.5,
                     fill="#1E4A23", opacity=0.85))
    # ön ızgara + far
    e.append(_el("rect", x=16.6, y=104.2, width=3.4, height=6.4, rx=0.6, fill="#1A3A1F",
                 clip_path=kt))
    for yy in (105.4, 106.8, 108.2, 109.6):
        e.append(_el("line", x1=16.9, y1=yy, x2=19.7, y2=yy, stroke="#3C6E40",
                     stroke_width=0.4))
    e.append(_el("rect", x=17.0, y=101.6, width=2.8, height=2.0, rx=0.5, fill="#FFF0BE"))
    e.append(_el("rect", x=17.0, y=101.6, width=2.8, height=2.0, rx=0.5, fill="none",
                 stroke="#8F7B3A", stroke_width=0.35))
    # egzoz: krom boru + kelepçe + yağmur kapağı
    e.append(_el("rect", x=20.4, y=88.6, width=3.2, height=12.6, rx=1.2, fill="url(#krom)",
                 clip_path=kt))
    e.append(_el("rect", x=20.2, y=93.5, width=3.6, height=0.9, fill="#6E7880",
                 clip_path=kt))
    e.append(_el("rect", x=19.4, y=86.9, width=5.2, height=2.2, rx=1.0, fill="#55606A",
                 clip_path=kt))
    # ön ağırlık: dökme demir + çeki kancası
    e.append(_el("rect", x=13.9, y=103.4, width=3.7, height=8.2, rx=0.8, fill="#38403A",
                 clip_path=kt))
    for yy in (105.2, 107.2, 109.2):
        e.append(_el("line", x1=14.2, y1=yy, x2=17.3, y2=yy, stroke="#20261F",
                     stroke_width=0.6))
    # kabin: ROPS çerçevesi + cam + iç mekân
    e.append(_el("rect", x=46.3, y=88.3, width=23.4, height=16.2, rx=2.4, fill="#255C2B",
                 clip_path=kt))
    e.append(_el("rect", x=48.2, y=90.1, width=19.6, height=12.6, rx=1.8, fill="#14212C"))
    e.append(_el("rect", x=48.8, y=90.7, width=18.4, height=11.4, rx=1.4,
                 fill="url(#cam)", opacity=0.92))
    # iç: koltuk + direksiyon
    e.append(_el("path", d="M 58.5 102 L 58.5 95.2 C 58.5 93.8 59.4 93 60.8 93 L 62.4 93 "
                           "C 63.2 93 63.8 93.6 63.8 94.4 L 63.8 96 L 61 96 L 61 102 Z",
                 fill="#1A2830", opacity=0.9))
    e.append(_el("circle", cx=54.6, cy=96.4, r=2.0, fill="none", stroke="#1A2830",
                 stroke_width=0.8, opacity=0.9))
    e.append(_el("line", x1=54.6, y1=96.4, x2=53.2, y2=98.2, stroke="#1A2830",
                 stroke_width=0.7, opacity=0.9))
    # cam parlaması + orta dikme
    e.append(_el("path", d="M 49.4 90.8 L 55.2 90.8 L 50.8 101.6 L 48.9 101.6 Z",
                 fill="#FFFFFF", opacity=0.4))
    e.append(_el("line", x1=57.8, y1=90.1, x2=57.8, y2=102.7, stroke="#255C2B",
                 stroke_width=0.9))
    # çamurluklar + gölgeleri
    e.append(_el("path", d="M 41 96.2 A 18.8 18.8 0 0 1 75.8 104.2 L 71.6 104.8 "
                           "A 14.6 14.6 0 0 0 45 98.8 Z", fill="#255C2B", clip_path=kt))
    e.append(_el("path", d="M 44 98.4 A 15.6 15.6 0 0 1 72.4 104.6 L 71.6 104.8 "
                           "A 14.6 14.6 0 0 0 45 98.8 Z", fill="#183E1D", clip_path=kt,
                 opacity=0.8))
    e.append(_el("path", d="M 17.4 110.6 A 11.9 11.9 0 0 1 37.8 111.4 L 34.6 113 "
                           "A 8.7 8.7 0 0 0 20.9 112.4 Z", fill="#255C2B", clip_path=kt,
                 opacity=0.97))
    teker(e, 58, 110.5, 17.5, "traktor")
    teker(e, 27.5, 118, 10, "traktor")
    hacim(e, "ktraktor", t, 0.10)

    # ============ İTFAİYE ============
    f = P["itfaiye"]
    kf = _klip(e, "kitfaiye", f)
    e.append(_el("path", d=yol_svg(f), fill="url(#kirmizi)"))
    # kabin: cam + iç + silecek + kapı
    e.append(_el("path", d="M 140.3 99.7 L 152 99.7 L 158.4 106.2 L 158.4 111 L 140.3 111 Z",
                 fill="#5E1410", clip_path=kf))
    e.append(_el("path", d="M 141.3 100.6 L 151.5 100.6 L 157.4 106.6 L 157.4 110.1 "
                           "L 141.3 110.1 Z", fill="#14212C"))
    e.append(_el("path", d="M 141.9 101.2 L 151.2 101.2 L 156.8 106.9 L 156.8 109.5 "
                           "L 141.9 109.5 Z", fill="url(#cam)", opacity=0.92))
    e.append(_el("path", d="M 143.2 101.5 L 146.8 101.5 L 143.6 109.2 L 142.1 109.2 Z",
                 fill="#FFFFFF", opacity=0.5))
    e.append(_el("path", d="M 144.5 109.3 L 148 103.6", stroke="#0E1922",
                 stroke_width=0.5, fill="none", opacity=0.85))
    e.append(_el("line", x1=140.9, y1=99.7, x2=140.9, y2=121.5, stroke="#7A1712",
                 stroke_width=0.5, opacity=0.9, clip_path=kf))
    e.append(_el("rect", x=142.2, y=112.6, width=3.2, height=1.0, rx=0.5, fill="#F4C86A"))
    # tepe lambası: taban + mavi/kırmızı lensler + parlama
    e.append(_el("rect", x=141.8, y=96.4, width=9.8, height=2.5, rx=1.2, fill="#1A252E",
                 clip_path=kf))
    e.append(_el("rect", x=142.6, y=96.7, width=3.4, height=1.9, rx=0.9, fill="#2F6FD6"))
    e.append(_el("rect", x=147.4, y=96.7, width=3.4, height=1.9, rx=0.9, fill="#E0312A"))
    e.append(_el("ellipse", cx=144.3, cy=95.9, rx=2.6, ry=1.1, fill="#5E9CFF",
                 opacity=0.25))
    e.append(_el("ellipse", cx=149.1, cy=95.9, rx=2.6, ry=1.1, fill="#FF5E5E",
                 opacity=0.2))
    # kasa: beyaz bant + yazılar
    e.append(_el("rect", x=92.6, y=105.2, width=46.2, height=8.8, fill="#F1EDE4",
                 clip_path=kf))
    e.append(_el("rect", x=92.6, y=105.2, width=46.2, height=1.1, fill="#C9C2B4",
                 clip_path=kf, opacity=0.7))
    e.append(_el("text", x=112, y=112.0, icerik="İTFAİYE", fill="#B02218",
                 font_size="5.4", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle", letter_spacing="0.7"))
    e.append(_el("text", x=132.8, y=109.2, icerik="112", fill="#1F3A5C", font_size="3.2",
                 font_family="sans-serif", font_weight="bold", text_anchor="middle"))
    e.append(_el("text", x=132.8, y=112.2, icerik="ACİL", fill="#1F3A5C", font_size="2.0",
                 font_family="sans-serif", font_weight="bold", text_anchor="middle"))
    # dolaplar: kepenkli + gömme kulplar
    for dx in (94.2, 117.2):
        e.append(_el("rect", x=dx, y=115.0, width=21, height=6.2, rx=0.8, fill="#8F1B15",
                     clip_path=kf))
        e.append(_el("rect", x=dx + 0.7, y=115.6, width=19.6, height=5.0, rx=0.5,
                     fill="#B02218", clip_path=kf))
        for lx in range(int(dx + 1.4), int(dx + 19.4), 2):
            e.append(_el("line", x1=lx, y1=115.8, x2=lx, y2=119.4, stroke="#8F1B15",
                         stroke_width=0.5, opacity=0.8))
        e.append(_el("rect", x=dx + 6.5, y=119.6, width=8, height=0.9, rx=0.45,
                     fill="#C9CFD6"))
    # ikaz şeritleri (kırmızı-beyaz çapraz) — etek
    e.append(_el("rect", x=92.6, y=119.8, width=46.2, height=1.9, fill="#F1EDE4",
                 clip_path=kf))
    for sx in range(90, 140, 5):
        e.append(f'<path d="M {sx} 121.7 L {sx+2.4} 121.7 L {sx+4.3} 119.8 L {sx+1.9} '
                 f'119.8 Z" fill="#D0281E" clip-path="{kf}"/>')
    # çatı: merdiven (raylar + basamaklar) + hortum dolabı
    e.append(_el("rect", x=93.4, y=95.3, width=5.8, height=4.6, rx=0.7, fill="#8F1B15",
                 clip_path=kf))
    e.append(_el("rect", x=94.1, y=96.0, width=4.4, height=3.2, rx=0.5, fill="#A8231B",
                 clip_path=kf))
    e.append(_el("rect", x=101, y=95.6, width=36, height=1.3, rx=0.6, fill="#7C8894",
                 clip_path=kf))
    e.append(_el("rect", x=101, y=99.3, width=36, height=1.3, rx=0.6, fill="#B7C2CB",
                 clip_path=kf))
    for mx in range(103, 136, 3):
        e.append(_el("line", x1=mx, y1=96.2, x2=mx, y2=99.9, stroke="#96A2AB",
                     stroke_width=0.8))
    # ön: far + ızgara + tampon + çamurluk yayı
    e.append(_el("circle", cx=158.7, cy=112.4, r=1.5, fill="#FFF0BE"))
    e.append(_el("circle", cx=158.7, cy=112.4, r=1.5, fill="none", stroke="#8F7B3A",
                 stroke_width=0.4))
    e.append(_el("rect", x=159.9, y=115.6, width=3.6, height=5.6, rx=1.0,
                 fill="url(#krom)", clip_path=kf))
    e.append(_el("circle", cx=161.7, cy=117.2, r=0.7, fill="#FFE9A0", opacity=0.9))
    for cxw in (104.5, 147.5):
        e.append(_el("path", d=f"M {cxw-7.6} 121.5 A 7.6 7.6 0 0 1 {cxw+7.6} 121.5",
                     fill="none", stroke="#12181E", stroke_width=2.2, clip_path=kf,
                     opacity=0.9))
    teker(e, 104.5, 121.5, 6.5, "kamyon")
    teker(e, 147.5, 121.5, 6.5, "kamyon")
    hacim(e, "kitfaiye", f, 0.10)

    # ============ ARABA ============
    a = P["araba"]
    ka = _klip(e, "karaba", a)
    e.append(_el("path", d=yol_svg(a), fill="url(#mavi)"))
    # tavan çizgisi + camlar (iç mekân + koltuk başlıkları)
    e.append(_el("path", d="M 186.9 110.7 L 191.5 102.0 L 212.0 102.0 L 217.9 110.7 Z",
                 fill="#101E28", clip_path=ka))
    e.append(_el("path", d="M 188.1 110.2 L 192.1 102.7 L 199.6 102.7 L 199.6 110.2 Z",
                 fill="url(#cam)", opacity=0.94))
    e.append(_el("path", d="M 201.7 102.7 L 211.4 102.7 L 216.6 110.2 L 201.7 110.2 Z",
                 fill="url(#cam)", opacity=0.94))
    e.append(_el("circle", cx=196.5, cy=107.4, r=1.3, fill="#101A22", opacity=0.8))
    e.append(_el("circle", cx=206.5, cy=107.4, r=1.3, fill="#101A22", opacity=0.8))
    e.append(_el("path", d="M 189 109.8 L 191.9 103.4 L 194.2 103.4 L 191.4 109.8 Z",
                 fill="#FFFFFF", opacity=0.45))
    e.append(_el("path", d="M 203.5 103.2 L 206 103.2 L 210 109.9 L 207.4 109.9 Z",
                 fill="#FFFFFF", opacity=0.3))
    # kapı çizgileri + kulplar + ayna
    e.append(_el("path", d="M 200.7 110.9 C 200.7 114.5 200.7 118 200.5 121.3",
                 fill="none", stroke="#1B355E", stroke_width=0.5, opacity=0.9,
                 clip_path=ka))
    e.append(_el("path", d="M 214.2 110.9 L 214.6 116.8 C 214.7 118.4 214.5 120 214.2 121.3",
                 fill="none", stroke="#1B355E", stroke_width=0.45, opacity=0.75,
                 clip_path=ka))
    for hx in (196.2, 204.4):
        e.append(_el("rect", x=hx, y=112.4, width=3.2, height=1.0, rx=0.5,
                     fill="#C9D2DB"))
        e.append(_el("rect", x=hx, y=113.1, width=3.2, height=0.3, fill="#1B355E",
                     opacity=0.6))
    e.append(_el("path", d="M 187.0 109.0 C 185.8 109.0 185.2 109.6 185.3 110.4 "
                           "L 188.3 110.4 L 188.3 109.0 Z", fill="#2F58AC"))
    # karakter çizgisi + eşik + alt ızgara
    e.append(_el("path", d="M 177.5 113.6 L 226.5 113.6 L 226.5 114.3 L 177.5 114.3 Z",
                 fill="#FFFFFF", opacity=0.22, clip_path=ka))
    e.append(_el("path", d="M 177.5 119.6 L 226.5 119.6 L 226.5 122.4 L 177.5 122.4 Z",
                 fill="#16294F", opacity=0.85, clip_path=ka))
    e.append(_el("path", d="M 221.5 119.0 L 226.8 119.0 L 226.8 121.4 L 221.5 121.4 Z",
                 fill="#0C1620", clip_path=ka, opacity=0.9))
    # farlar: projektör + DRL; stop lambası
    e.append(_el("path", d="M 224.3 111.9 L 227.2 112.7 L 227.2 115.0 L 223.6 114.4 Z",
                 fill="#E8F1F8", clip_path=ka))
    e.append(_el("circle", cx=225.6, cy=113.4, r=0.75, fill="#9CC3E0"))
    e.append(_el("path", d="M 224.3 111.9 L 227.2 112.7 L 227.2 113.2 L 224.2 112.4 Z",
                 fill="#FFFFFF", opacity=0.8))
    e.append(_el("path", d="M 176.8 112.2 L 179.4 111.9 L 179.4 114.8 L 176.8 114.5 Z",
                 fill="#C42A20", clip_path=ka))
    e.append(_el("path", d="M 177.2 112.6 L 178.9 112.4 L 178.9 113.4 L 177.2 113.5 Z",
                 fill="#FF7A70", opacity=0.85))
    # plaka
    e.append(_el("rect", x=177.0, y=116.2, width=5.4, height=2.0, rx=0.3, fill="#F4F7F9"))
    e.append(_el("rect", x=177.0, y=116.2, width=0.8, height=2.0, fill="#2F58AC"))
    e.append(_el("text", x=180.1, y=117.85, icerik="34", fill="#22303B", font_size="1.7",
                 font_family="sans-serif", font_weight="bold", text_anchor="middle"))
    # davlumbazlar
    for cxw in (190, 214):
        e.append(_el("path", d=f"M {cxw-7.2} 121.5 A 7.2 7.2 0 0 1 {cxw+7.2} 121.5",
                     fill="none", stroke="#12181E", stroke_width=2.0, clip_path=ka,
                     opacity=0.9))
    teker(e, 190, 121.5, 6, "araba")
    teker(e, 214, 121.5, 6, "araba")
    hacim(e, "karaba", a, 0.12)

    # ============ OTOBÜS ============
    o = P["otobus"]
    ko = _klip(e, "kotobus", o)
    e.append(_el("path", d=yol_svg(o), fill="url(#sari)"))
    # tavan klima ünitesi + tavan hattı
    e.append(_el("rect", x=246, y=94.4, width=44, height=2.2, rx=1.0, fill="#C98F12",
                 clip_path=ko))
    for vx in range(250, 288, 6):
        e.append(_el("line", x1=vx, y1=94.9, x2=vx + 3, y2=94.9, stroke="#8F6608",
                     stroke_width=0.6, opacity=0.8))
    # flush cam bandı (siyah conta) + camlar + dikmeler
    e.append(_el("rect", x=242.6, y=98.6, width=60.5, height=11.4, rx=2.0, fill="#14181D",
                 clip_path=ko))
    for i in range(4):
        wx = 244.4 + i * 11.6
        e.append(_el("rect", x=wx, y=99.8, width=10.2, height=9.0, rx=1.0,
                     fill="url(#cam)", opacity=0.95))
        e.append(_el("path", d=f"M {wx+0.8} {100.1} L {wx+3.6} {100.1} "
                               f"L {wx+1.6} {108.5} L {wx+0.6} {108.5} Z",
                     fill="#FFFFFF", opacity=0.35))
    # yolcu silüeti (ikinci camda)
    e.append(_el("circle", cx=262.4, cy=104.2, r=1.5, fill="#10141A", opacity=0.75))
    e.append(_el("path", d="M 260.6 108.8 C 260.6 106.6 261.4 105.8 262.4 105.8 "
                           "C 263.4 105.8 264.2 106.6 264.2 108.8 Z", fill="#10141A",
                 opacity=0.75))
    # ön cam + silecekler + tabela
    e.append(_el("path", d="M 300.3 98.9 C 306.6 99.7 310.8 103.2 311.8 108.4 L 311.8 111 "
                           "L 300.3 111 Z", fill="#14181D", clip_path=ko))
    e.append(_el("path", d="M 301.2 99.8 C 306.6 100.5 310.1 103.6 311.0 108.2 L 311.0 "
                           "110.2 L 301.2 110.2 Z", fill="url(#cam)", opacity=0.95))
    e.append(_el("path", d="M 302.1 100.1 L 304.9 100.5 L 303.1 109.8 L 301.4 109.8 Z",
                 fill="#FFFFFF", opacity=0.4))
    e.append(_el("path", d="M 303.4 109.9 L 306.6 103.4 M 307.2 109.9 L 309.4 105.6",
                 stroke="#0E1922", stroke_width=0.5, fill="none", opacity=0.85))
    e.append(_el("rect", x=301.4, y=95.8, width=10.2, height=2.5, rx=0.7, fill="#14181D",
                 clip_path=ko))
    e.append(_el("text", x=306.5, y=97.85, icerik="1 OKUL", fill="#FFB300",
                 font_size="1.9", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle", letter_spacing="0.3"))
    # kapı: çift kanat + camlı + tutamaklar
    e.append(_el("rect", x=289.6, y=99.2, width=9.4, height=21.8, rx=1.2, fill="#B8860B",
                 clip_path=ko, opacity=0.55))
    for dx in (290.4, 295.0):
        e.append(_el("rect", x=dx, y=100.0, width=3.8, height=20.2, rx=0.8,
                     fill="#C99312", clip_path=ko))
        e.append(_el("rect", x=dx + 0.5, y=100.6, width=2.8, height=12.4, rx=0.6,
                     fill="url(#cam)", opacity=0.95))
        e.append(_el("line", x1=dx + 1.9, y1=113.6, x2=dx + 1.9, y2=119.6,
                     stroke="#8F6608", stroke_width=0.5))
    e.append(_el("line", x1=294.7, y1=99.5, x2=294.7, y2=120.6, stroke="#14181D",
                 stroke_width=0.6, opacity=0.85, clip_path=ko))
    # OKUL TAŞITI plakası (sarı zemin, siyah çerçeve — dingiller arasında)
    e.append(_el("rect", x=263.2, y=112.2, width=24.6, height=4.8, rx=0.7, fill="#FFC825"))
    e.append(_el("rect", x=263.2, y=112.2, width=24.6, height=4.8, rx=0.7, fill="none",
                 stroke="#14181D", stroke_width=0.55))
    e.append(_el("text", x=275.5, y=115.75, icerik="OKUL TAŞITI", fill="#14181D",
                 font_size="2.7", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle", letter_spacing="0.3"))
    # etek + davlumbazlar + farlar + plaka
    e.append(_el("rect", x=240.4, y=118.4, width=73, height=2.6, fill="#8F6608",
                 opacity=0.55, clip_path=ko))
    for cxw in (256, 297):
        e.append(_el("path", d=f"M {cxw-7.9} 121.5 A 7.9 7.9 0 0 1 {cxw+7.9} 121.5",
                     fill="none", stroke="#12181E", stroke_width=2.3, clip_path=ko,
                     opacity=0.9))
    e.append(_el("rect", x=310.6, y=113.6, width=2.6, height=2.2, rx=0.5, fill="#FFF0BE",
                 clip_path=ko))
    e.append(_el("rect", x=310.6, y=116.4, width=2.6, height=1.6, rx=0.5, fill="#F5A623",
                 clip_path=ko))
    e.append(_el("rect", x=240.6, y=112.4, width=1.9, height=3.6, rx=0.4, fill="#C42A20",
                 clip_path=ko, opacity=0.9))
    e.append(_el("rect", x=241.6, y=113.2, width=5.8, height=2.1, rx=0.3, fill="#F4F7F9"))
    e.append(_el("rect", x=241.6, y=113.2, width=0.8, height=2.1, fill="#2F58AC"))
    e.append(_el("text", x=245.0, y=114.95, icerik="34", fill="#22303B", font_size="1.7",
                 font_family="sans-serif", font_weight="bold", text_anchor="middle"))
    teker(e, 256, 121.5, 6.5, "kamyon")
    teker(e, 297, 121.5, 6.5, "kamyon")
    hacim(e, "kotobus", o, 0.10)

    # ============ YELKENLİ ============
    y = P["yelkenli"]
    ky = _klip(e, "kyelkenli", y)
    e.append(_el("path", d=yol_svg(y), fill="url(#yelkeng)"))
    # ana yelken: panel dikişleri + leech gölgesi + cunda cepleri
    e.append(_el("path", d="M 70 138.5 L 70 156.5 L 50 156.5 Z", fill="#FBFAF6",
                 clip_path=ky))
    for t, x2 in [(143.5, 57.5), (147.5, 61), (151.5, 64.5)]:
        e.append(_el("path", d=f"M 70 {t} L {x2} 156.4", stroke="#C5CDD4",
                     stroke_width=0.5, fill="none", clip_path=ky))
    e.append(_el("path", d="M 70 138.5 L 70 156.5 L 63.5 156.5 Z", fill="#DDE2E7",
                 clip_path=ky, opacity=0.85))
    for bx, by in [(66.5, 147), (63.5, 151)]:
        e.append(_el("line", x1=bx, y1=by, x2=bx + 2.6, y2=by - 0.4, stroke="#AEB8C0",
                     stroke_width=0.6, opacity=0.9))
    # flok: krem + dikişler + luff kancaları
    e.append(_el("path", d="M 77 141.5 L 77 156.5 L 95.5 156.5 Z", fill="#F2E9D2",
                 clip_path=ky))
    for t, x2 in [(146.5, 86.5), (150.5, 82), (154, 79.5)]:
        e.append(_el("path", d=f"M 77 {t} L {x2} 156.4", stroke="#D8CBA8",
                     stroke_width=0.5, fill="none", clip_path=ky))
    for hy in (143.5, 147, 150.5, 154):
        e.append(_el("circle", cx=77.4, cy=hy, r=0.4, fill="#8A7A52"))
    # arma: ıstralya + patrisa (ince halatlar)
    e.append(_el("line", x1=73.2, y1=136.8, x2=97.8, y2=157.2, stroke="#4A4438",
                 stroke_width=0.4, opacity=0.85, clip_path=ky))
    e.append(_el("line", x1=72.8, y1=136.8, x2=48.4, y2=156.8, stroke="#4A4438",
                 stroke_width=0.4, opacity=0.75, clip_path=ky))
    # direk + bumba: ahşap gradyan + boğum bantları
    e.append(_el("rect", x=71.5, y=136.3, width=3.0, height=21.2, fill="url(#ahsap)",
                 clip_path=ky))
    e.append(_el("rect", x=72.0, y=136.3, width=0.8, height=21.2, fill="#C8A165",
                 clip_path=ky, opacity=0.8))
    for my in (141, 148):
        e.append(_el("rect", x=71.4, y=my, width=3.2, height=0.7, fill="#55402A",
                     clip_path=ky))
    e.append(_el("rect", x=53.4, y=154.0, width=17.8, height=2.3, rx=1.1,
                 fill="url(#ahsap)", clip_path=ky))
    e.append(_el("circle", cx=71.9, cy=155.1, r=0.8, fill="#3E2E1C"))
    # gövde: kırmızı + karina + su hattı + kaplama dikişleri
    e.append(_el("path", d="M 45.8 157.2 L 100.2 157.2 L 92 169.4 L 56 169.4 Z",
                 fill="#C0392E", clip_path=ky))
    e.append(_el("path", d="M 47.9 160.4 L 98.1 160.4 L 92 169.4 L 56 169.4 Z",
                 fill="#8F231A", clip_path=ky))
    e.append(_el("path", d="M 48.6 161.4 L 97.4 161.4 L 96.2 163.2 L 49.8 163.2 Z",
                 fill="#F1EDE4", clip_path=ky))
    e.append(_el("path", d="M 52 165.8 L 94 165.8", stroke="#701812", stroke_width=0.4,
                 opacity=0.6, clip_path=ky))
    # güverte: tik kaplama + kokpit
    e.append(_el("path", d="M 46.5 157.3 L 99.5 157.3 L 98.8 158.9 L 47.5 158.9 Z",
                 fill="#C8A165", clip_path=ky))
    for dxx in range(50, 98, 6):
        e.append(_el("line", x1=dxx, y1=157.4, x2=dxx - 0.3, y2=158.8, stroke="#96703F",
                     stroke_width=0.35, opacity=0.8))
    e.append(_el("rect", x=84, y=157.9, width=7.5, height=1.6, rx=0.7, fill="#6E4C2A",
                 clip_path=ky, opacity=0.85))
    # lombozlar + isim
    for px in (60, 68, 76, 84):
        e.append(_el("circle", cx=px, cy=164.4, r=1.1, fill="#14212C"))
        e.append(_el("circle", cx=px, cy=164.15, r=0.85, fill="#7FB6D9"))
        e.append(_el("circle", cx=px, cy=164.4, r=1.1, fill="none", stroke="#D8D2C4",
                     stroke_width=0.35))
    e.append(_el("text", x=93.2, y=160.1, icerik="RÜZGÂR", fill="#F1EDE4",
                 font_size="1.8", font_family="sans-serif", font_style="italic",
                 text_anchor="end", opacity=0.95))
    hacim(e, "kyelkenli", y, 0.09)

    # ============ FERİBOT ============
    fb = P["feribot"]
    kfb = _klip(e, "kferibot", fb)
    e.append(_el("path", d=yol_svg(fb), fill="url(#beyazmetal2)"))
    # tekne: lacivert + karina + kaplama dikişleri + perçin sıraları
    e.append(_el("path", d="M 190.5 157 L 291.5 157 L 282 169.8 L 200 169.8 Z",
                 fill="#20395A", clip_path=kfb))
    e.append(_el("path", d="M 193.8 161.8 L 288.2 161.8 L 282 169.8 L 200 169.8 Z",
                 fill="#12233A", clip_path=kfb))
    e.append(_el("path", d="M 190.5 157 L 291.5 157 L 290.4 158.6 L 191.7 158.6 Z",
                 fill="#C0392E", clip_path=kfb))
    e.append(_el("path", d="M 195 160.3 L 287.5 160.3", stroke="#2E4A6E",
                 stroke_width=0.4, opacity=0.8, clip_path=kfb))
    for px in range(198, 286, 5):
        e.append(_el("circle", cx=px, cy=159.4, r=0.22, fill="#5E7A9E", opacity=0.8))
    # su kesimi işaretleri (draft marks)
    for i, dy in enumerate((167.6, 165.2, 162.8)):
        e.append(_el("rect", x=284.4 - i * 1.1, y=dy, width=2.2, height=0.55,
                     fill="#E8EDF2", opacity=0.9, clip_path=kfb))
    # lombozlar (çerçeveli)
    for px in range(202, 282, 11):
        e.append(_el("circle", cx=px, cy=164.6, r=1.4, fill="#0C1A2A"))
        e.append(_el("circle", cx=px, cy=164.35, r=1.05, fill="#6FA8CE"))
        e.append(_el("circle", cx=px, cy=164.6, r=1.4, fill="none", stroke="#8CA2BC",
                     stroke_width=0.35))
    # çapa + loça
    e.append(_el("circle", cx=286.8, cy=160.6, r=0.9, fill="#0C1A2A", clip_path=kfb))
    e.append(_el("path", d="M 286.8 160.6 L 286.8 163.6 M 285.6 162.2 L 288 162.2 "
                           "M 285.9 163.9 A 1.6 1.6 0 0 0 287.7 163.9",
                 stroke="#0C1A2A", stroke_width=0.5, fill="none", clip_path=kfb))
    # usturmaça hattı
    e.append(_el("path", d="M 191 157.0 L 291 157.0", stroke="#E8EDF2", stroke_width=0.7,
                 opacity=0.9, clip_path=kfb))
    # ana güverte: cam bandı + vardavela + can filikası
    e.append(_el("rect", x=202.5, y=150.4, width=75.5, height=5.8, rx=1.1, fill="#1C2833",
                 opacity=0.35, clip_path=kfb))
    for px in range(204, 274, 9):
        e.append(_el("rect", x=px, y=151.1, width=6.2, height=4.4, rx=0.8,
                     fill="url(#cam)", opacity=0.95))
        e.append(_el("rect", x=px, y=151.1, width=6.2, height=4.4, rx=0.8, fill="none",
                     stroke="#8CA2BC", stroke_width=0.3))
    e.append(_el("path", d="M 254 149.6 L 278.5 149.6", stroke="#5E6E7E",
                 stroke_width=0.45, clip_path=kfb))
    for px in range(255, 279, 3):
        e.append(_el("line", x1=px, y1=149.6, x2=px, y2=151.0, stroke="#5E6E7E",
                     stroke_width=0.35, opacity=0.9))
    e.append(_el("path", d="M 269.5 151.9 A 3.1 1.5 0 0 1 275.7 151.9 L 275.2 153.4 "
                           "L 270.0 153.4 Z", fill="#E8622E", clip_path=kfb))
    e.append(_el("line", x1=270.4, y1=150.0, x2=270.4, y2=152.2, stroke="#5E6E7E",
                 stroke_width=0.4))
    e.append(_el("line", x1=274.8, y1=150.0, x2=274.8, y2=152.2, stroke="#5E6E7E",
                 stroke_width=0.4))
    # köprü üstü: camlar + kanat + kaptan silueti
    e.append(_el("rect", x=212.6, y=142.8, width=39, height=6.0, rx=1.2, fill="#1C2833",
                 clip_path=kfb))
    for px in range(214, 248, 5):
        e.append(_el("rect", x=px, y=143.6, width=3.6, height=4.4, rx=0.7,
                     fill="url(#cam)", opacity=0.95))
    e.append(_el("circle", cx=220.0, cy=145.9, r=1.1, fill="#10141A", opacity=0.8))
    e.append(_el("path", d="M 212.6 148.2 L 251.6 148.2 L 251.6 149.0 L 212.6 149.0 Z",
                 fill="#8CA2BC", opacity=0.6, clip_path=kfb))
    # baca: İstanbul vapuru stili (sarı + siyah kapak + bantlar) + duman
    e.append(_el("path", d="M 259 140.5 L 267.5 140.5 L 269 149.5 L 257.5 149.5 Z",
                 fill="#E0A92C", clip_path=kfb))
    e.append(_el("path", d="M 259 140.5 L 267.5 140.5 L 267.9 142.8 L 258.62 142.8 Z",
                 fill="#14181D", clip_path=kfb))
    e.append(_el("path", d="M 258.5 143.6 L 268.05 143.6 L 268.3 145.1 L 258.26 145.1 Z",
                 fill="#B02218", clip_path=kfb))
    e.append(_el("path", d="M 260.5 141 L 262 141 L 261.4 149.3 L 259.8 149.3 Z",
                 fill="#FFD466", clip_path=kfb, opacity=0.6))
    for sx, sy, sr, sop in [(263.5, 138.6, 1.5, 0.30), (265.5, 137.0, 1.9, 0.22),
                            (268.0, 135.6, 2.3, 0.15)]:
        e.append(_el("circle", cx=sx, cy=sy, r=sr, fill="#F4F7F9", opacity=f"{sop}"))
    # baş dalgası köpüğü
    e.append(_el("path", d="M 289.5 170.3 q 3.5 0.8 6.5 2.6 q -3.8 0.4 -7.2 -0.6",
                 fill="#EAF6FC", opacity=0.7))
    hacim(e, "kferibot", fb, 0.09)

    return e

# ---------------------------------------------------------------- zemin gölgeleri
def zemin_katmani():
    """Kara araçlarının temas gölgeleri + teknelerin su yansımaları
    (araç çizimlerinden ÖNCE zemine basılır)."""
    e = []
    zemin_golgesi(e, 45, 128.6, 32)     # traktör
    zemin_golgesi(e, 127, 128.4, 37)    # itfaiye
    zemin_golgesi(e, 202, 128.0, 27)    # araba
    zemin_golgesi(e, 276.5, 128.4, 38)  # otobüs
    yansima(e, 73, 170.6, 25)           # yelkenli
    yansima(e, 241, 171.0, 46)          # feribot
    return e

# ---------------------------------------------------------------- SVG belgeleri
def svg_belge(w_mm, h_mm, icerik):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{h_mm}mm" '
            f'viewBox="0 0 {w_mm} {h_mm}">' + "\n".join(icerik) + "</svg>")


def uret_baski_svg():
    icerik = [f'<g transform="translate({BLEED},{BLEED})">'] + sahne_svg() + ["</g>"]
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, icerik)


def uret_kalip_svg():
    """UV hizalama kalıbı: yalnız dış çerçeve konturu (1:1)."""
    icerik = [_el("path", d=yol_svg(cerceve_poly()), fill="none", stroke="#FF0000",
                  stroke_width=0.25)]
    icerik.append(_el("text", x=6, y=177.2,
                      icerik="ARAÇLAR PUZZLE 320x180 – UV KALIP (1:1)",
                      fill="#888888", font_size="3", font_family="sans-serif"))
    return svg_belge(W, H, icerik)


def uret_golge_svg():
    """Alt katman gölge baskısı (324x184, 2 mm taşmalı): cep tabanlarına
    parça gölgeleri basılır — çocuk parçanın yerini gölgeden bulur."""
    ic = [f'<g transform="translate({BLEED},{BLEED})">']
    ic.append(_el("rect", x=-6, y=-6, width=W + 12, height=76, fill="#DDEEF8"))
    ic.append(_el("rect", x=-6, y=64, width=W + 12, height=28.5, fill="#E3F0DA"))
    ic.append(_el("rect", x=-6, y=92, width=W + 12, height=44, fill="#E8E8EC"))
    ic.append(_el("rect", x=-6, y=136, width=W + 12, height=50, fill="#D6EAF7"))
    for yy in (92, 136):
        ic.append(_el("rect", x=-6, y=yy - 0.3, width=W + 12, height=0.6,
                      fill="#C9CDD2", opacity=0.6))
    # parça gölgeleri: hafif içeri alınmış (0.4 mm) — cep duvarından taşmaz
    for _, poly, _ in PARCALAR:
        for iceri, op in ((-0.15, 0.4), (-0.55, 1.0)):
            g = poly.buffer(iceri, quad_segs=8)
            if g.is_empty:
                continue
            geoms = g.geoms if g.geom_type == "MultiPolygon" else [g]
            for gg in geoms:
                ic.append(_el("path", d=yol_svg(gg), fill="#5A6774", opacity=f"{op}"))
    ic.append("</g>")
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, ic)

# ---------------------------------------------------------------- DXF
def uret_dxf(dosya):
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4  # milimetre
    msp = doc.modelspace()
    doc.layers.add("UST_KATMAN_KESIM", color=1)
    doc.layers.add("ALT_KATMAN_KESIM", color=5)
    doc.layers.add("YAZI", color=8)

    def poli(poly, dx, katman):
        pts, son = [], None
        for (x, y) in list(poly.exterior.coords)[:-1]:
            q = (round(x + dx, 3), round(H - y, 3))
            if q != son:
                pts.append(q)
                son = q
        if pts[0] == pts[-1]:
            pts.pop()
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": katman})

    poli(cerceve_poly(), 0, "UST_KATMAN_KESIM")
    for _, poly, _ in PARCALAR:
        poli(poly, 0, "UST_KATMAN_KESIM")
    dx_alt = W + 15
    poli(cerceve_poly(), dx_alt, "ALT_KATMAN_KESIM")

    msp.add_text("UST KATMAN - araclar + cepler (320x180)",
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

    baski = uret_baski_svg()
    kalip = uret_kalip_svg()
    golge = uret_golge_svg()

    cairosvg.svg2pdf(bytestring=baski.encode(), write_to=f"{OUT}/araclar_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=kalip.encode(), write_to=f"{OUT}/araclar_uv_kalip.pdf")
    cairosvg.svg2pdf(bytestring=golge.encode(), write_to=f"{OUT}/araclar_alt_golge.pdf")
    cairosvg.svg2png(bytestring=baski.encode(), write_to=f"{OUT}/araclar_onizleme.png",
                     output_width=2200)
    cairosvg.svg2png(bytestring=kalip.encode(), write_to=f"{OUT}/araclar_kalip_onizleme.png",
                     output_width=1920)
    cairosvg.svg2png(bytestring=golge.encode(),
                     write_to=f"{OUT}/araclar_alt_golge_onizleme.png", output_width=1920)
    uret_dxf(f"{OUT}/araclar_lazer_kesim.dxf")

    for ad, poly, sinif in PARCALAR:
        x0, y0, x1, y1 = poly.bounds
        print(f"  parça {ad:<11} ({sinif:<5}) {x1-x0:5.1f} x {y1-y0:5.1f} mm")
    print("Tamamlandı ->", OUT)


if __name__ == "__main__":
    main()
