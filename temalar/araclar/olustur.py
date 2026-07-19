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
        elips(248, 36, 24, 13),                                # gövde
        elips(260, 39, 13, 10),                                # burun kabini
        kapsul(270, 31.5, 288, 31.5, 3.2),                     # kuyruk bomu
        cokgen((283.5, 33.5), (287, 21.5), (293.5, 21.5), (295.5, 33.5)),  # kuyruk dikmesi
        kapsul(224, 15, 282, 15, 2.7),                         # ana pervane
        kutu(249, 16, 7, 10),                                  # pervane mili
        kapsul(233, 50.3, 271, 50.3, 2.0),                     # kızak
        kutu(240, 44, 4.5, 7), kutu(259.5, 44, 4.5, 7),        # kızak ayakları
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
    g.append(_lin("gok", 0, -6, 0, 70, [(0, "#5FB7E8"), (0.7, "#A7DCF5"), (1, "#D7F0FB")]))
    g.append(_lin("cim", 0, 58, 0, 92, [(0, "#93D468"), (1, "#6CB84A")]))
    g.append(_lin("yol", 0, 92, 0, 136, [(0, "#9B9BA3"), (1, "#7E7E88")]))
    g.append(_lin("su", 0, 136, 0, 186, [(0, "#5BB9E9"), (0.5, "#3D9FD8"), (1, "#2E7FBC")]))
    g.append(_rad("gunes", 77, 11, 17, [(0, "#FFF3B0"), (0.45, "#FFE06A", 0.9), (1, "#FFE06A", 0)]))
    g.append('<linearGradient id="cam" x1="0" y1="0" x2="0.7" y2="1">'
             '<stop offset="0" stop-color="#EAF7FF"/>'
             '<stop offset="1" stop-color="#8FC3E4"/></linearGradient>')
    g.append(_lin("kirmizi", 0, 94, 0, 128, [(0, "#F4655A"), (0.45, "#DE3B31"), (1, "#B02A24")]))
    g.append(_lin("mavi", 0, 100, 0, 128, [(0, "#6FA7EE"), (0.45, "#3D74D3"), (1, "#2B54A4")]))
    g.append(_lin("sari", 0, 94, 0, 128, [(0, "#FFD34E"), (0.5, "#F5AE0A"), (1, "#D28E00")]))
    g.append(_lin("yesil", 0, 84, 0, 128, [(0, "#66BE58"), (0.5, "#3F9143"), (1, "#2F7335")]))
    g.append(_lin("turuncu", 0, 12, 0, 53, [(0, "#FF9B57"), (0.5, "#F0742B"), (1, "#CE5A1A")]))
    g.append(_lin("beyazmetal", 0, 15, 0, 52, [(0, "#FFFFFF"), (0.6, "#E9EEF2"), (1, "#C3CCD4")]))
    g.append(_lin("beyazmetal2", 0, 138, 0, 172, [(0, "#FFFFFF"), (0.6, "#E9EEF2"), (1, "#BFC9D1")]))
    g.append(_lin("balonzar", 24, 8, 60, 46, [(0, "#FFDD55"), (0.5, "#F2762E"), (1, "#D8342A")]))
    g.append(_lin("yelkeng", 0, 134, 0, 158, [(0, "#FFFFFF"), (1, "#D9E2EA")]))
    g.append(_rad("jant", 0, 0, 1, [(0, "#F2F5F7"), (0.65, "#C3CAD3"), (1, "#8C959F")]))
    return "<defs>" + "".join(g) + "</defs>"

# ---------------------------------------------------------------- ortak çizim parçaları
def teker(e, cx, cy, r, jant_oran=0.62):
    """Gerçekçi tekerlek: lastik + sırt izleri + jant + bijonlar."""
    e.append(_el("circle", cx=cx, cy=cy, r=r, fill="#26262B"))
    e.append(_el("circle", cx=cx, cy=cy, r=r * 0.985, fill="none",
                 stroke="#3A3A41", stroke_width=r * 0.16,
                 stroke_dasharray=f"{r*0.22} {r*0.26}"))
    rj = r * jant_oran
    e.append(f'<g transform="translate({cx},{cy}) scale({rj:.3f})">'
             f'<circle cx="0" cy="0" r="1" fill="url(#jant)"/></g>')
    e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.32, fill="#9AA2AC"))
    e.append(_el("circle", cx=cx, cy=cy, r=rj * 0.14, fill="#5E656D"))
    for i in range(5):
        a = math.radians(i * 72 - 90)
        e.append(_el("circle", cx=cx + rj * 0.62 * math.cos(a),
                     cy=cy + rj * 0.62 * math.sin(a), r=rj * 0.1, fill="#6E7680"))


def hacim(e, klip, poly, guc=0.20):
    """Parçaya genel ışık/gölge hacmi: üstten aydınlık, alttan koyu."""
    x0, y0, x1, y1 = poly.bounds
    w, h = x1 - x0, y1 - y0
    e.append(_el("ellipse", cx=x0 + w * 0.42, cy=y0 + h * 0.2, rx=w * 0.62, ry=h * 0.34,
                 fill="#FFFFFF", opacity=f"{guc}", clip_path=f"url(#{klip})"))
    e.append(_el("ellipse", cx=x0 + w * 0.55, cy=y1 + h * 0.05, rx=w * 0.75, ry=h * 0.3,
                 fill="#1B2733", opacity=f"{guc * 0.75}", clip_path=f"url(#{klip})"))


def _klip(e, ad, poly):
    e.append(f'<clipPath id="{ad}"><path d="{yol_svg(poly)}"/></clipPath>')
    return f"url(#{ad})"

# ---------------------------------------------------------------- sahne
def _agac(e, x, taban, olcek=1.0):
    s = olcek
    e.append(_el("path", d=f"M {x-1.6*s} {taban} L {x-1.1*s} {taban-9*s} "
                           f"L {x+1.1*s} {taban-9*s} L {x+1.6*s} {taban} Z",
                 fill="#7A5233"))
    e.append(_el("line", x1=x, y1=taban - 8 * s, x2=x + 3.2 * s, y2=taban - 11.5 * s,
                 stroke="#7A5233", stroke_width=1.1 * s))
    for dx, dy, r, renk in [(-3.2, -12, 4.6, "#2F7D3C"), (3.4, -12.5, 4.9, "#3C9149"),
                            (0, -16, 5.4, "#49A455"), (0, -12.5, 4.4, "#57B463")]:
        e.append(_el("circle", cx=x + dx * s, cy=taban + dy * s, r=r * s, fill=renk))


def _ahir(e):
    # gövde + çatı + kapı — çiftlik ambarı
    e.append(_el("path", d="M 136 90 L 136 74 L 152 65 L 168 74 L 168 90 Z", fill="#C24C41"))
    e.append(_el("path", d="M 136 90 L 136 74 L 152 65 L 152 90 Z", fill="#D95F53"))
    e.append(_el("path", d="M 132.5 76 L 152 64.5 L 171.5 76 L 168 76 L 152 67 L 136 76 Z",
                 fill="#8C3A31"))
    for yy in (78, 82, 86):
        e.append(_el("line", x1=137, y1=yy, x2=167, y2=yy, stroke="#A8443A",
                     stroke_width=0.7, opacity=0.8))
    e.append(_el("rect", x=147, y=79, width=10, height=11, rx=0.8, fill="#7C3128"))
    e.append(_el("path", d="M 147 79 L 157 90 M 157 79 L 147 90", stroke="#5E241D",
                 stroke_width=1.1, fill="none"))
    e.append(_el("circle", cx=152, cy=71.5, r=2.6, fill="#F5EFE0"))
    e.append(_el("circle", cx=152, cy=71.5, r=2.6, fill="none", stroke="#8C3A31",
                 stroke_width=0.8))


def _yeldegirmeni(e):
    e.append(_el("path", d="M 262.5 90 L 265 70 L 271 70 L 273.5 90 Z", fill="#EDE6D6"))
    e.append(_el("path", d="M 262.5 90 L 265 70 L 268 70 L 268 90 Z", fill="#D9D0BC"))
    e.append(_el("path", d="M 264.4 70 A 3.6 3.6 0 0 1 271.6 70 Z", fill="#B0483C"))
    for a0 in (35, 125, 215, 305):
        a = math.radians(a0)
        x2, y2 = 268 + 12 * math.cos(a), 68.5 + 12 * math.sin(a)
        e.append(_el("line", x1=268, y1=68.5, x2=x2, y2=y2, stroke="#6E4A2E",
                     stroke_width=1.5))
        px, py = 268 + 7.5 * math.cos(a), 68.5 + 7.5 * math.sin(a)
        e.append(_el("line", x1=px, y1=py, x2=px + 4 * math.cos(a + 0.5),
                     y2=py + 4 * math.sin(a + 0.5), stroke="#6E4A2E", stroke_width=3.0,
                     stroke_linecap="round", opacity=0.9))
    e.append(_el("circle", cx=268, cy=68.5, r=1.7, fill="#4E3520"))


def _marti(e, x, y, s=1.0):
    e.append(_el("path", d=f"M {x-4*s} {y} Q {x-2*s} {y-2.6*s} {x} {y} "
                           f"Q {x+2*s} {y-2.6*s} {x+4*s} {y}",
                 fill="none", stroke="#5D6B77", stroke_width=0.9 * s,
                 stroke_linecap="round"))


def sahne_svg():
    e = [tanimlar()]
    # --- gökyüzü
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=76, fill="url(#gok)"))
    e.append(_el("circle", cx=77, cy=11, r=16.5, fill="url(#gunes)"))
    e.append(_el("circle", cx=77, cy=11, r=7, fill="#FFD94E"))
    e.append(_el("circle", cx=77, cy=11, r=7, fill="none", stroke="#F7C52F",
                 stroke_width=1.2, opacity=0.8))
    # bulutlar (katmanlı, yumuşak)
    for bx, by, s, op in [(148, 12, 1.0, 0.95), (192, 26, 0.72, 0.9), (26, 38, 0.6, 0.85),
                          (300, 55, 0.55, 0.8)]:
        for dx, dy, r in [(-7, 1, 4.6), (-2, -2.6, 6), (4.4, -0.6, 5), (9.5, 1.6, 3.8),
                          (1, 2, 5.2)]:
            e.append(_el("circle", cx=bx + dx * s * 1.6, cy=by + dy * s * 1.6,
                         r=r * s * 1.6, fill="#FFFFFF", opacity=op))
        e.append(_el("ellipse", cx=bx, cy=by + 4.6 * s, rx=13 * s * 1.4, ry=2.6 * s,
                     fill="#B9D9EC", opacity=0.35 * op))
    _marti(e, 66, 31, 1.0)
    _marti(e, 186, 20, 0.8)
    # --- uzak tepeler + çimen
    e.append(_el("ellipse", cx=58, cy=76, rx=95, ry=15, fill="#A9DA8B", opacity=0.9))
    e.append(_el("ellipse", cx=252, cy=78, rx=115, ry=17, fill="#9AD37B", opacity=0.9))
    e.append(_el("rect", x=-6, y=64, width=W + 12, height=28.5, fill="url(#cim)"))
    # çim dokusu + çiçekler (dekor bölgesi: x>=84, traktörden uzak)
    for fx, fy, renk in [(100, 88, "#F2D64B"), (128, 85.5, "#E8734D"), (198, 87, "#F2D64B"),
                         (222, 84.5, "#E8734D"), (244, 88, "#FFFFFF"), (290, 86, "#E8734D")]:
        e.append(_el("line", x1=fx, y1=fy + 3, x2=fx, y2=fy, stroke="#4E9440",
                     stroke_width=0.7))
        e.append(_el("circle", cx=fx, cy=fy, r=1.1, fill=renk))
        e.append(_el("circle", cx=fx, cy=fy, r=0.4, fill="#8A6A1F"))
    for tx in range(88, 314, 9):
        e.append(_el("path", d=f"M {tx} 91 q 1 -2.6 2 0", fill="none",
                     stroke="#5CA94B", stroke_width=0.6, opacity=0.7))
    _agac(e, 98, 91, 1.0)
    _agac(e, 121, 89.5, 0.8)
    _ahir(e)
    _agac(e, 185, 90.5, 1.05)
    _yeldegirmeni(e)
    _agac(e, 302, 90, 0.75)
    # --- yol
    e.append(_el("rect", x=-6, y=92, width=W + 12, height=44, fill="url(#yol)"))
    e.append(_el("rect", x=-6, y=92, width=W + 12, height=2.2, fill="#C9C9CF"))
    e.append(_el("rect", x=-6, y=94.2, width=W + 12, height=1, fill="#6E6E77", opacity=0.6))
    e.append(_el("rect", x=-6, y=133, width=W + 12, height=3, fill="#C9C9CF"))
    e.append(_el("rect", x=-6, y=132.2, width=W + 12, height=0.9, fill="#6E6E77", opacity=0.6))
    # asfalt lekeleri
    for px, py, rx in [(30, 100, 14), (150, 127, 18), (262, 99, 15), (208, 126, 12)]:
        e.append(_el("ellipse", cx=px, cy=py, rx=rx, ry=2.6, fill="#75757E", opacity=0.45))
    # orta şerit çizgisi
    x = -4
    while x < W + 6:
        e.append(_el("rect", x=x, y=112.8, width=12, height=2.6, rx=1.1,
                     fill="#F5F5F0", opacity=0.92))
        x += 27
    # --- deniz
    e.append(_el("rect", x=-6, y=136, width=W + 12, height=50, fill="url(#su)"))
    e.append(_el("rect", x=-6, y=136, width=W + 12, height=1.4, fill="#BFE6F4", opacity=0.8))
    for wx, wy, s in [(24, 146, 1), (116, 143, 0.8), (150, 158, 1.1), (26, 166, 0.9),
                      (122, 173, 1.0), (176, 168, 0.8), (300, 146, 0.9), (306, 168, 0.8),
                      (162, 141, 0.7)]:
        e.append(_el("path", d=f"M {wx} {wy} q {5*s} {-3*s} {10*s} 0 q {5*s} {3*s} {10*s} 0",
                     fill="none", stroke="#CFEEFA", stroke_width=1.5 * s,
                     stroke_linecap="round", opacity=0.85))
        e.append(_el("ellipse", cx=wx + 10 * s, cy=wy + 2.5 * s, rx=9 * s, ry=1.2 * s,
                     fill="#FFFFFF", opacity=0.12))
    # şamandıra (tekne parçalarının uzağında)
    e.append(_el("path", d="M 168 166 L 171.4 166 L 170.7 159.5 L 168.7 159.5 Z",
                 fill="#E0483C"))
    e.append(_el("rect", x=168.3, y=161.6, width=2.8, height=1.6, fill="#F5F0E6"))
    e.append(_el("circle", cx=169.7, cy=158.6, r=1.0, fill="#FFD23F"))
    e.append(_el("ellipse", cx=169.7, cy=166.8, rx=3.4, ry=0.9, fill="#1B3C57", opacity=0.3))
    # --- araçlar
    e += arac_detaylari()
    # --- parça dış çizgileri (ince, koyu — kesim payını gizler)
    for _, poly, _ in PARCALAR:
        e.append(_el("path", d=yol_svg(poly), fill="none", stroke="#22303B",
                     stroke_width=1.1, stroke_linejoin="round", opacity=0.9))
    return e

# ---------------------------------------------------------------- araç detayları
def arac_detaylari():
    e = []
    P = {ad: poly for ad, poly, _ in PARCALAR}

    # ---------- BALON
    b = P["balon"]
    kb = _klip(e, "kbalon", b)
    e.append(_el("path", d=yol_svg(b), fill="url(#balonzar)"))
    # dilimler (gore'lar)
    for ofs, renk in [(-14, "#C43A2F"), (-7, "#E8B33B"), (0, "#2F62B0"),
                      (7, "#E8B33B"), (14, "#C43A2F")]:
        e.append(_el("path",
                     d=f"M {42+ofs} 7 C {42+ofs*1.9} 18 {42+ofs*1.9} 32 {42+ofs*0.75} 45 "
                       f"L {42+ofs*0.45} 45 C {42+ofs*1.5} 32 {42+ofs*1.5} 18 {42+ofs*0.6} 7 Z",
                     fill=renk, opacity=0.85, clip_path=kb))
    # yük halkası + halatlar
    e.append(_el("path", d="M 33.5 40.5 L 36.5 44.5 M 50.5 40.5 L 47.5 44.5 M 42 42 L 42 45",
                 stroke="#5E4326", stroke_width=0.9, fill="none"))
    e.append(_el("rect", x=35.5, y=43.6, width=13, height=1.6, rx=0.8, fill="#7A5233",
                 clip_path=kb))
    # sepet örgüsü
    e.append(_el("rect", x=35.8, y=44.6, width=12.4, height=5.2, rx=1, fill="#9A6B3F",
                 clip_path=kb))
    for yy in (46.1, 47.6, 49.1):
        e.append(_el("line", x1=35.8, y1=yy, x2=48.2, y2=yy, stroke="#7A5233",
                     stroke_width=0.55))
    for xx in (38.2, 40.8, 43.4, 46.0):
        e.append(_el("line", x1=xx, y1=44.6, x2=xx, y2=49.8, stroke="#7A5233",
                     stroke_width=0.55, opacity=0.7))
    hacim(e, "kbalon", b, 0.18)

    # ---------- UÇAK
    u = P["ucak"]
    ku = _klip(e, "kucak", u)
    e.append(_el("path", d=yol_svg(u), fill="url(#beyazmetal)"))
    # gövde alt gölgesi + karın çizgisi
    e.append(_el("path", d="M 100 36.4 L 175 36.4 L 175 40 L 100 40 Z", fill="#AEB9C2",
                 opacity=0.75, clip_path=ku))
    # kuyruk: kırmızı süpürme
    e.append(_el("path", d="M 97 15.5 L 104.5 15.5 L 116 29.2 L 108 31.5 L 97 22 Z",
                 fill="#D0382E", clip_path=ku))
    e.append(_el("path", d="M 97 18.5 L 97 29 L 107 31.2 Z", fill="#8C2A23",
                 clip_path=ku, opacity=0.85))
    # yatay kuyruk gölgesi
    e.append(_el("path", d="M 97 29.5 L 89.5 35 L 89.5 37.5 L 102 33 Z", fill="#C3CCD4",
                 clip_path=ku, opacity=0.9))
    # burun + kokpit camı
    e.append(_el("path", d="M 174.5 31.5 C 174.5 29 172 27.3 168.5 26.8 L 168.5 30 Z",
                 fill="#3A4750", opacity=0.35, clip_path=ku))
    e.append(_el("path", d="M 162 27.6 L 168.6 27.6 C 170.8 28.2 172.4 29.2 173.3 30.4 "
                           "L 166 30.4 Z", fill="#274357", clip_path=ku))
    e.append(_el("path", d="M 165.2 27.9 L 168 27.9 L 170.5 30.1 L 167 30.1 Z",
                 fill="#7FB6D9", clip_path=ku))
    # yolcu pencereleri + kapılar
    for wx in range(112, 162, 6):
        e.append(_el("rect", x=wx, y=29.4, width=2.6, height=3.4, rx=1.3, fill="#2E5670"))
        e.append(_el("rect", x=wx + 0.4, y=29.8, width=1.2, height=1.4, rx=0.6,
                     fill="#9CCBE8", opacity=0.9))
    # kanat + motor (hava girişi önde — sağda)
    e.append(_el("path", d="M 131 34 L 153 34 L 128 50.5 L 119 50.5 Z", fill="#D5DDE3",
                 clip_path=ku))
    e.append(_el("path", d="M 131 34 L 153 34 L 147 38 L 128 38 Z", fill="#B9C4CD",
                 clip_path=ku, opacity=0.9))
    e.append(_el("rect", x=139.6, y=38.7, width=15.6, height=7.0, rx=3.0, fill="#8794A0",
                 clip_path=ku))
    e.append(_el("rect", x=139.6, y=38.7, width=15.6, height=2.6, rx=1.3, fill="#A8B4BE",
                 clip_path=ku))
    e.append(_el("ellipse", cx=154.6, cy=42.2, rx=1.9, ry=3.3, fill="#33414C", clip_path=ku))
    e.append(_el("ellipse", cx=154.3, cy=42.2, rx=1.1, ry=2.3, fill="#5E6E7A", clip_path=ku))
    e.append(_el("ellipse", cx=139.9, cy=42.2, rx=1.2, ry=2.2, fill="#6E7680", clip_path=ku))
    hacim(e, "kucak", u, 0.14)

    # ---------- HELİKOPTER
    h = P["helikopter"]
    kh = _klip(e, "kheli", h)
    e.append(_el("path", d=yol_svg(h), fill="url(#turuncu)"))
    # beyaz karın süpürmesi
    e.append(_el("path", d="M 224 41 C 240 36 262 36 274 41 L 274 49 L 224 49 Z",
                 fill="#F7F3EC", opacity=0.95, clip_path=kh))
    e.append(_el("path", d="M 224 40.4 C 240 35.4 262 35.4 274 40.4", fill="none",
                 stroke="#B44E14", stroke_width=0.8, clip_path=kh, opacity=0.7))
    # kuyruk bomu gölge + şerit
    e.append(_el("path", d="M 268 33.4 L 292 33.4 L 292 34.8 L 268 34.8 Z", fill="#B44E14",
                 opacity=0.6, clip_path=kh))
    e.append(_el("path", d="M 283.5 33.5 L 287 21.5 L 293.5 21.5 L 295.5 33.5 Z",
                 fill="#E06420", clip_path=kh))
    # kuyruk rotoru (baskıda: dikme üzerinde disk + pala)
    e.append(_el("line", x1=290.4, y1=21.2, x2=290.4, y2=31.8, stroke="#37424C",
                 stroke_width=1.1, opacity=0.9))
    e.append(_el("circle", cx=290.4, cy=26.5, r=2.6, fill="#37424C"))
    e.append(_el("circle", cx=290.4, cy=26.5, r=0.9, fill="#8C959F"))
    # ana pervane + mil
    e.append(_el("path", d="M 221.5 12.6 L 284.5 12.6 L 284.5 17.4 L 221.5 17.4 Z",
                 fill="#37424C", clip_path=kh))
    e.append(_el("rect", x=250.5, y=17.4, width=4, height=8, fill="#37424C", clip_path=kh))
    e.append(_el("circle", cx=252.5, cy=15, r=2.2, fill="#5E6E7A"))
    # kokpit camı (büyük, çerçeveli)
    e.append(_el("path", d="M 256 27.5 C 265 28 271.5 32.5 272.8 37.5 L 259 37.5 "
                           "C 256.5 37.5 255 35.5 255 33 Z", fill="url(#cam)", clip_path=kh))
    e.append(_el("path", d="M 256 27.5 C 265 28 271.5 32.5 272.8 37.5", fill="none",
                 stroke="#C05515", stroke_width=0.8, clip_path=kh, opacity=0.9))
    e.append(_el("path", d="M 257 29.5 L 263 28.6 L 258.8 34 Z", fill="#FFFFFF",
                 opacity=0.55, clip_path=kh))
    # yan pencere
    e.append(_el("circle", cx=243, cy=33.5, r=4.4, fill="url(#cam)"))
    e.append(_el("circle", cx=243, cy=33.5, r=4.4, fill="none", stroke="#B44E14",
                 stroke_width=0.9))
    e.append(_el("path", d="M 240 31 A 4 4 0 0 1 245 30.4", fill="none", stroke="#FFFFFF",
                 stroke_width=0.9, opacity=0.6))
    # kızaklar
    e.append(_el("path", d="M 231.5 50.3 L 272.5 50.3", stroke="#37424C", stroke_width=3.6,
                 stroke_linecap="round", clip_path=kh))
    e.append(_el("path", d="M 240.5 44 L 240.5 50 M 263.5 44 L 263.5 50", stroke="#37424C",
                 stroke_width=4.2, fill="none", clip_path=kh))
    hacim(e, "kheli", h, 0.15)

    # ---------- TRAKTÖR
    t = P["traktor"]
    kt = _klip(e, "ktraktor", t)
    e.append(_el("path", d=yol_svg(t), fill="url(#yesil)"))
    # kaput yüzeyi + ızgara + far
    e.append(_el("path", d="M 16.8 101 L 42.5 99.6 L 45.4 103.8 L 45.4 111 L 16.8 111 Z",
                 fill="#4FA349", clip_path=kt))
    e.append(_el("path", d="M 16.8 106.5 L 45.4 106.5 L 45.4 111 L 16.8 111 Z",
                 fill="#357B38", clip_path=kt, opacity=0.9))
    for gx in (18.6, 20.4, 22.2):
        e.append(_el("line", x1=gx, y1=107.3, x2=gx, y2=110.4, stroke="#1F4A24",
                     stroke_width=0.8, opacity=0.85))
    e.append(_el("circle", cx=19.8, cy=103.6, r=1.7, fill="#FFE9A8"))
    e.append(_el("circle", cx=19.8, cy=103.6, r=1.7, fill="none", stroke="#8F7B3A",
                 stroke_width=0.5))
    # egzoz + şapka (krom)
    e.append(_el("rect", x=20.4, y=88.4, width=3.2, height=13, rx=1.2, fill="#89939C",
                 clip_path=kt))
    e.append(_el("rect", x=21.0, y=88.4, width=1.0, height=13, fill="#C7CDD3",
                 clip_path=kt, opacity=0.8))
    # kabin: çerçeve + cam + şoför koltuğu + direksiyon
    e.append(_el("rect", x=46.5, y=88.5, width=23, height=15.5, rx=2.2, fill="#2F6B33",
                 clip_path=kt))
    e.append(_el("rect", x=48.3, y=90.2, width=19.4, height=12.2, rx=1.6, fill="url(#cam)"))
    e.append(_el("path", d="M 49 90.5 L 55.5 90.5 L 50.5 102 L 48.3 102 Z", fill="#FFFFFF",
                 opacity=0.5))
    e.append(_el("path", d="M 58 102.4 L 58 94 L 62.5 94 L 62.5 96.5 L 60 96.5 L 60 102.4 Z",
                 fill="#24422A", opacity=0.75))
    e.append(_el("circle", cx=55.2, cy=96.2, r=1.9, fill="none", stroke="#24422A",
                 stroke_width=0.9, opacity=0.8))
    # çamurluklar
    e.append(_el("path", d="M 41.5 96.5 A 18.5 18.5 0 0 1 75.5 104 L 71.5 104.5 "
                           "A 14.6 14.6 0 0 0 45.3 99 Z", fill="#2F6B33", clip_path=kt))
    e.append(_el("path", d="M 17.6 110.5 A 11.8 11.8 0 0 1 37.6 111.5 L 34.4 113 "
                           "A 8.6 8.6 0 0 0 21 112.4 Z", fill="#2F6B33", clip_path=kt,
                 opacity=0.95))
    teker(e, 58, 110.5, 17.5, 0.56)
    teker(e, 27.5, 118, 10, 0.5)
    # traktör jantları sarı olsun (klasik)
    e.append(_el("circle", cx=58, cy=110.5, r=17.5 * 0.56 * 0.92, fill="#E8B33B",
                 opacity=0.9))
    e.append(_el("circle", cx=58, cy=110.5, r=3.4, fill="#8F7B3A"))
    e.append(_el("circle", cx=27.5, cy=118, r=10 * 0.5 * 0.92, fill="#E8B33B", opacity=0.9))
    e.append(_el("circle", cx=27.5, cy=118, r=1.9, fill="#8F7B3A"))
    hacim(e, "ktraktor", t, 0.13)

    # ---------- İTFAİYE
    f = P["itfaiye"]
    kf = _klip(e, "kitfaiye", f)
    e.append(_el("path", d=yol_svg(f), fill="url(#kirmizi)"))
    # kabin camı + çerçevesi
    e.append(_el("path", d="M 141 100 L 151.6 100 L 157.8 106.3 L 157.8 110.5 L 141 110.5 Z",
                 fill="#8C1F1A", clip_path=kf))
    e.append(_el("path", d="M 142.2 101 L 151 101 L 156.6 106.7 L 156.6 109.4 L 142.2 109.4 Z",
                 fill="url(#cam)"))
    e.append(_el("path", d="M 143.5 101.3 L 147 101.3 L 143.8 109.1 L 142.4 109.1 Z",
                 fill="#FFFFFF", opacity=0.55))
    # tepe lambası + siren
    e.append(_el("rect", x=142.5, y=96.6, width=8.5, height=2.2, rx=1.1, fill="#1F3A5C",
                 clip_path=kf))
    e.append(_el("rect", x=143.2, y=96.9, width=3.0, height=1.6, rx=0.8, fill="#3D74D3"))
    e.append(_el("rect", x=147.8, y=96.9, width=3.0, height=1.6, rx=0.8, fill="#E0483C"))
    # kasa: beyaz şerit + İTFAİYE + dolap kapakları
    e.append(_el("rect", x=92.8, y=105.5, width=45.4, height=8.5, fill="#F2EFE9",
                 clip_path=kf))
    e.append(_el("text", x=115.5, y=112.1, icerik="İTFAİYE", fill="#C0271F",
                 font_size="5.6", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle", letter_spacing="0.6"))
    for dx in (94.5, 118.5):
        e.append(_el("rect", x=dx, y=115.5, width=20, height=5.6, rx=0.9, fill="#B02A24",
                     clip_path=kf))
        for lx in range(int(dx) + 2, int(dx) + 19, 3):
            e.append(_el("line", x1=lx, y1=116.1, x2=lx, y2=120.5, stroke="#8C1F1A",
                         stroke_width=0.8, opacity=0.7))
    # çatıdaki merdiven (gümüş, raylı)
    e.append(_el("rect", x=95.5, y=95.8, width=41, height=1.4, rx=0.7, fill="#9AA2AC",
                 clip_path=kf))
    e.append(_el("rect", x=95.5, y=99.6, width=41, height=1.4, rx=0.7, fill="#C3CAD3",
                 clip_path=kf))
    for mx in range(98, 135, 4):
        e.append(_el("line", x1=mx, y1=96.4, x2=mx, y2=100.6, stroke="#8C959F",
                     stroke_width=1.0))
    # far + tampon + basamak
    e.append(_el("circle", cx=158.6, cy=112.6, r=1.6, fill="#FFE9A8"))
    e.append(_el("rect", x=159.8, y=115.8, width=3.6, height=5.4, rx=1.0, fill="#C3CAD3",
                 clip_path=kf))
    e.append(_el("rect", x=139.6, y=113.3, width=18.6, height=1.2, fill="#8C1F1A",
                 clip_path=kf, opacity=0.8))
    teker(e, 104.5, 121.5, 6.5)
    teker(e, 147.5, 121.5, 6.5)
    hacim(e, "kitfaiye", f, 0.13)

    # ---------- ARABA
    a = P["araba"]
    ka = _klip(e, "karaba", a)
    e.append(_el("path", d=yol_svg(a), fill="url(#mavi)"))
    # camlar: ön + yan (B sütunlu)
    e.append(_el("path", d="M 187.6 110.8 L 191.6 102.2 L 201 102.2 L 201 110.8 Z",
                 fill="url(#cam)"))
    e.append(_el("path", d="M 203 110.8 L 203 102.2 L 211.6 102.2 L 217.2 110.8 Z",
                 fill="url(#cam)"))
    e.append(_el("path", d="M 188.6 110.2 L 191.9 103 L 194.6 103 L 191.2 110.2 Z",
                 fill="#FFFFFF", opacity=0.5))
    # kapı çizgisi + kol
    e.append(_el("path", d="M 202 111 L 202 121.5", stroke="#22406E", stroke_width=0.8,
                 fill="none", clip_path=ka))
    e.append(_el("path", d="M 208 121 C 208 117.5 210 115.6 213.4 115.6", fill="none",
                 stroke="#22406E", stroke_width=0.8, opacity=0.7, clip_path=ka))
    e.append(_el("rect", x=204.2, y=113.2, width=3.4, height=1.1, rx=0.55, fill="#22406E"))
    e.append(_el("rect", x=196.4, y=113.2, width=3.4, height=1.1, rx=0.55, fill="#22406E"))
    # gövde süpürme çizgisi + eşik
    e.append(_el("path", d="M 177.5 116.8 L 226.5 116.8 L 226.5 118.6 L 177.5 118.6 Z",
                 fill="#2B54A4", opacity=0.55, clip_path=ka))
    # farlar + stoplar
    e.append(_el("path", d="M 224.9 112.4 L 227.3 112.4 L 227.3 115 L 224.9 114.6 Z",
                 fill="#FFE9A8", clip_path=ka))
    e.append(_el("path", d="M 176.7 112.4 L 179 112.4 L 179 114.9 L 176.7 114.9 Z",
                 fill="#D0382E", clip_path=ka))
    # ayna
    e.append(_el("rect", x=186.2, y=108.4, width=2.4, height=1.8, rx=0.7, fill="#22406E"))
    teker(e, 190, 121.5, 6)
    teker(e, 214, 121.5, 6)
    hacim(e, "karaba", a, 0.16)

    # ---------- OTOBÜS
    o = P["otobus"]
    ko = _klip(e, "kotobus", o)
    e.append(_el("path", d=yol_svg(o), fill="url(#sari)"))
    # pencere bandı (5 cam + çerçeve)
    e.append(_el("rect", x=243, y=98.5, width=59, height=10.4, rx=2.2, fill="#B8860B",
                 opacity=0.5, clip_path=ko))
    for i, wx in enumerate((244.5, 256.5, 268.5, 280.5)):
        e.append(_el("rect", x=wx, y=99.6, width=10, height=8.2, rx=1.4, fill="url(#cam)"))
        e.append(_el("path", d=f"M {wx+1} {99.9} L {wx+4} {99.9} L {wx+1.6} {107.4} "
                               f"L {wx+0.6} {107.4} Z", fill="#FFFFFF", opacity=0.45))
    # ön cam (büyük, eğimli) + kapı
    e.append(_el("path", d="M 300.5 98.8 C 306.5 99.6 310.6 103 311.6 108.2 L 311.6 110.5 "
                           "L 300.5 110.5 Z", fill="url(#cam)", clip_path=ko))
    e.append(_el("path", d="M 301.5 99.2 L 304.5 99.6 L 302.6 110 L 300.9 110 Z",
                 fill="#FFFFFF", opacity=0.5))
    e.append(_el("rect", x=289, y=99.6, width=9.6, height=21.4, rx=1.4, fill="#8C6A08",
                 clip_path=ko, opacity=0.6))
    e.append(_el("rect", x=290, y=100.4, width=3.6, height=19.8, rx=1.0, fill="url(#cam)"))
    e.append(_el("rect", x=294.6, y=100.4, width=3.6, height=19.8, rx=1.0, fill="url(#cam)"))
    # tabela + far + etek şeridi
    e.append(_el("rect", x=302, y=95.6, width=9, height=2.6, rx=0.9, fill="#2B2B33",
                 clip_path=ko))
    e.append(_el("text", x=306.5, y=97.75, icerik="1", fill="#FFD34E", font_size="2.4",
                 font_family="sans-serif", font_weight="bold", text_anchor="middle"))
    e.append(_el("circle", cx=311.2, cy=113.6, r=1.7, fill="#FFE9A8"))
    e.append(_el("rect", x=240.5, y=118.2, width=73, height=2.4, fill="#B8860B",
                 opacity=0.6, clip_path=ko))
    e.append(_el("text", x=265, y=116.4, icerik="OKUL TAŞITI", fill="#3B2F04",
                 font_size="3.4", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle", letter_spacing="0.5"))
    teker(e, 256, 121.5, 6.5)
    teker(e, 297, 121.5, 6.5)
    hacim(e, "kotobus", o, 0.13)

    # ---------- YELKENLİ
    y = P["yelkenli"]
    ky = _klip(e, "kyelkenli", y)
    e.append(_el("path", d=yol_svg(y), fill="url(#yelkeng)"))
    # yelkenler: dikiş çizgileri + gölge
    e.append(_el("path", d="M 70 138.5 L 70 156.5 L 50 156.5 Z", fill="#FFFFFF",
                 clip_path=ky))
    e.append(_el("path", d="M 70 143 L 57.5 156.3 M 70 148.5 L 63 156.3", stroke="#C9D4DC",
                 stroke_width=0.7, fill="none", clip_path=ky))
    e.append(_el("path", d="M 70 138.5 L 70 156.5 L 64 156.5 Z", fill="#E4EAEF",
                 clip_path=ky, opacity=0.8))
    e.append(_el("path", d="M 77 141.5 L 77 156.5 L 95.5 156.5 Z", fill="#F4E9CF",
                 clip_path=ky))
    e.append(_el("path", d="M 77 146.5 L 87.5 156.3 M 77 151.5 L 82 156.3", stroke="#D9C9A3",
                 stroke_width=0.7, fill="none", clip_path=ky))
    # direk + bumba (ahşap)
    e.append(_el("rect", x=71.6, y=136.4, width=2.8, height=21, fill="#8A6238",
                 clip_path=ky))
    e.append(_el("rect", x=72.1, y=136.4, width=0.9, height=21, fill="#B08A5A",
                 clip_path=ky))
    e.append(_el("rect", x=53.5, y=154, width=17.5, height=2.2, rx=1.1, fill="#8A6238",
                 clip_path=ky))
    # gövde: kırmızı + su hattı + güverte
    e.append(_el("path", d="M 45.8 157.3 L 100.2 157.3 L 92 169.3 L 56 169.3 Z",
                 fill="#C0392E", clip_path=ky))
    e.append(_el("path", d="M 45.8 157.3 L 100.2 157.3 L 98.4 160 L 47.6 160 Z",
                 fill="#8A5A3B", clip_path=ky))
    e.append(_el("path", d="M 47 160 L 99 160 L 98 161.6 L 48 161.6 Z", fill="#F2EFE9",
                 clip_path=ky))
    for px in (60, 70, 80, 90):
        e.append(_el("circle", cx=px, cy=164.5, r=1.2, fill="#F2D64B"))
        e.append(_el("circle", cx=px, cy=164.5, r=1.2, fill="none", stroke="#8C6A2F",
                     stroke_width=0.45))
    hacim(e, "kyelkenli", y, 0.12)

    # ---------- FERİBOT
    fb = P["feribot"]
    kfb = _klip(e, "kferibot", fb)
    e.append(_el("path", d=yol_svg(fb), fill="url(#beyazmetal2)"))
    # tekne: lacivert gövde + kırmızı su hattı
    e.append(_el("path", d="M 190.5 157 L 291.5 157 L 282 169.7 L 200 169.7 Z",
                 fill="#1F3A5C", clip_path=kfb))
    e.append(_el("path", d="M 193.5 161.5 L 288.5 161.5 L 282 169.7 L 200 169.7 Z",
                 fill="#16293F", clip_path=kfb))
    e.append(_el("path", d="M 190.5 157 L 291.5 157 L 290.2 158.8 L 191.8 158.8 Z",
                 fill="#C0392E", clip_path=kfb))
    # lombozlar
    for px in range(200, 284, 12):
        e.append(_el("circle", cx=px, cy=164, r=1.5, fill="#7FB6D9"))
        e.append(_el("circle", cx=px, cy=164, r=1.5, fill="none", stroke="#0E1C2B",
                     stroke_width=0.5))
    # ana güverte pencere bandı
    e.append(_el("rect", x=203, y=150.6, width=74, height=5.2, rx=1.2, fill="#33414C",
                 opacity=0.25, clip_path=kfb))
    for px in range(205, 276, 9):
        e.append(_el("rect", x=px, y=151.2, width=5.6, height=4, rx=0.9, fill="url(#cam)"))
    # köprü üstü: camlar + kaptan köşkü
    e.append(_el("rect", x=213, y=143, width=38, height=5.6, rx=1.2, fill="#26343F",
                 clip_path=kfb))
    for px10 in range(2145, 2481, 52):
        e.append(_el("rect", x=px10 / 10, y=143.8, width=3.6, height=4, rx=0.8,
                     fill="#9CCBE8"))
    # baca: sarı + siyah kapak + kırmızı bant
    e.append(_el("path", d="M 259 140.5 L 267.5 140.5 L 269 149.5 L 257.5 149.5 Z",
                 fill="#E8B33B", clip_path=kfb))
    e.append(_el("path", d="M 259 140.5 L 267.5 140.5 L 267.9 143 L 258.6 143 Z",
                 fill="#26262B", clip_path=kfb))
    e.append(_el("path", d="M 258.4 144 L 268.1 144 L 268.4 146 L 258.1 146 Z",
                 fill="#C0392E", clip_path=kfb))
    # can simidi + duman
    e.append(_el("circle", cx=290, cy=152.8, r=2.0, fill="#E0483C", clip_path=kfb))
    e.append(_el("circle", cx=290, cy=152.8, r=0.9, fill="#F2EFE9", clip_path=kfb))
    hacim(e, "kferibot", fb, 0.12)

    return e

# ---------------------------------------------------------------- SVG belgeleri
def svg_belge(w_mm, h_mm, icerik):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{h_mm}mm" '
            f'viewBox="0 0 {w_mm} {h_mm}">' + "\n".join(icerik) + "</svg>")


def uret_baski_svg():
    icerik = [f'<g transform="translate({BLEED},{BLEED})">'] + sahne_svg() + ["</g>"]
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, icerik)


def uret_kalip_svg():
    icerik = [_el("path", d=yol_svg(cerceve_poly()), fill="none", stroke="#FF0000",
                  stroke_width=0.25)]
    for _, poly, _ in PARCALAR:
        icerik.append(_el("path", d=yol_svg(poly), fill="none", stroke="#FF0000",
                          stroke_width=0.25))
    icerik.append(_el("text", x=6, y=177.2,
                      icerik="ARAÇLAR PUZZLE 320x180 – UV KALIP (1:1)",
                      fill="#888888", font_size="3", font_family="sans-serif"))
    return svg_belge(W, H, icerik)

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

    cairosvg.svg2pdf(bytestring=baski.encode(), write_to=f"{OUT}/araclar_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=kalip.encode(), write_to=f"{OUT}/araclar_uv_kalip.pdf")
    cairosvg.svg2png(bytestring=baski.encode(), write_to=f"{OUT}/araclar_onizleme.png",
                     output_width=2200)
    cairosvg.svg2png(bytestring=kalip.encode(), write_to=f"{OUT}/araclar_kalip_onizleme.png",
                     output_width=1920)
    uret_dxf(f"{OUT}/araclar_lazer_kesim.dxf")

    for ad, poly, sinif in PARCALAR:
        x0, y0, x1, y1 = poly.bounds
        print(f"  parça {ad:<11} ({sinif:<5}) {x1-x0:5.1f} x {y1-y0:5.1f} mm")
    print("Tamamlandı ->", OUT)


if __name__ == "__main__":
    main()
