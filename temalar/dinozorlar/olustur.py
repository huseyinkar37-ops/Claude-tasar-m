# -*- coding: utf-8 -*-
"""
İki katmanlı "Dinozorlar" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Çıktılar (cikti/):
  1. dinozorlar_uv_kalip.pdf    – UV hizalama kalıbı (yalnız dış çerçeve, 1:1)
  2. dinozorlar_uv_baski.pdf    – ÜST katman baskısı, 2 mm taşmalı (324x184)
  3. dinozorlar_alt_golge.pdf   – ALT katman gölge baskısı (324x184)
  4. dinozorlar_lazer_kesim.dxf – Lazer: ÜST (cepli) + ALT (düz) panolar

Çalıştırma:  python3 olustur.py
"""
import base64
import math
import os
import random
import struct

from shapely.affinity import rotate as s_dondur, scale as s_olcek, \
    translate as s_tasi
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
TEMA = "dinozorlar"

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

# ---------------------------------------------------------------- dinozor konturları
def kontur_pteranodon():
    """Uçan sürüngen: iki yana açılmış kanatlar, sivri gaga (ibik baskıda)."""
    return birlesim([
        kapsul(58, 33, 78, 32, 7.5),                                # gövde
        cokgen((62, 30), (44, 14), (28, 15), (33, 25), (54, 40)),   # sol kanat
        kapsul(28, 15, 44, 14, 3.6),                                # sol kanat ön kenarı
        cokgen((76, 29), (92, 13), (105, 16), (99, 27), (84, 36)),  # sağ kanat
        kapsul(92, 13, 105, 16, 3.6),                               # sağ kanat ön kenarı
        elips(83, 36, 8.5, 6.5, -14),                               # baş
        cokgen((86, 33.5), (101, 40), (97, 44.5), (84, 41)),        # sivri gaga
    ], kapa=1.9)


def kontur_brakiyozor():
    """Uzun boyunlu dev otçul: küçük baş, fıçı gövde, sütun bacaklar."""
    return birlesim([
        elips(223, 41, 19, 11),                                     # gövde
        kapsul(234, 40, 245, 15, 4.6),                              # dik uzun boyun
        elips(249, 12, 6.0, 4.8, -26),                              # baş
        kapsul(205, 39, 193, 43, 4.2),                              # kuyruk
        kapsul(195, 43, 181, 46, 2.8),                              # kuyruk ucu
        kapsul(231, 47, 232, 53, 4.4),                              # ön bacak
        kapsul(222, 48, 221, 53, 3.8),                              # ön bacak (uzak)
        kapsul(211, 46, 210, 53, 4.6),                              # arka bacak
        kapsul(217, 48, 216, 53, 3.6),                              # arka bacak (uzak)
    ], kapa=1.5)


def kontur_trex():
    """Tyrannosaurus rex: iri kafa, açık ağız, ayrı duran güçlü bacaklar."""
    return birlesim([
        elips(52, 90, 19, 13.5, -14),                               # gövde
        kapsul(62, 84, 70, 79, 6.5),                                # boyun
        elips(76, 74, 12, 8.8, -12),                                # baş
        cokgen((64, 78), (88, 73.5), (90, 82), (66, 86)),           # çene
        kapsul(36, 94, 22, 103, 5.4),                               # kuyruk
        kapsul(24, 103, 14, 108, 3.3),                              # kuyruk ucu
        elips(51, 100, 10, 9),                                      # uyluk
        kapsul(53, 105, 51, 113, 4.2),                              # baldır
        kapsul(46, 115.5, 57, 115.5, 3.0),                          # ayak
        kapsul(70, 101, 70, 112, 3.6),                              # arka bacak
        kapsul(68, 114, 78, 114, 2.8),                              # arka ayak
    ], kapa=1.6)


def kontur_triceratops():
    """Üç boynuzlu otçul: kalkan biçimli yaka, gaga ağız, tıknaz gövde."""
    return birlesim([
        elips(163, 97, 25, 15),                                     # gövde
        elips(136, 95, 11.5, 14.5, -12),                            # yaka kalkanı
        daire(131, 82.5, 3.2), daire(141, 84.5, 3.2),               # yaka fistoları
        daire(146, 92, 3.0), daire(144, 104, 3.0),
        elips(124, 100, 10.5, 8.5),                                 # baş
        cokgen((115, 96), (106, 92), (117, 89)),                    # burun boynuzu
        cokgen((122, 90), (112, 78), (121, 86)),                    # sol kaş boynuzu
        cokgen((131, 88), (125, 76), (134, 85)),                    # sağ kaş boynuzu
        kapsul(184, 94, 197, 89, 4.6),                              # kuyruk
        kapsul(147, 108, 146, 115, 4.8),                            # ön bacak
        kapsul(156, 109, 156, 115, 3.8),                            # ön bacak (uzak)
        kapsul(177, 108, 178, 115, 4.8),                            # arka bacak
        kapsul(168, 109, 168, 115, 3.8),                            # arka bacak (uzak)
    ], kapa=1.6)


def kontur_stegosaurus():
    """Sırtı plakalı otçul: küçük baş, kemerli sırt, dikenli kuyruk."""
    return birlesim([
        elips(262, 92, 26, 14),                                     # gövde
        kapsul(242, 91, 232, 96, 5.4),                              # ince boyun
        elips(224, 98, 8.6, 6.2, -14),                              # baş
        kapsul(286, 90, 299, 86, 5.0),                              # kuyruk
        cokgen((297, 82), (307, 77), (301, 88)),                    # kuyruk dikeni 1
        cokgen((298, 89), (308, 91), (299, 95)),                    # kuyruk dikeni 2
        cokgen((244, 82), (247, 70), (253, 81)),                    # sırt plakası 1
        cokgen((254, 80), (259, 68), (265, 79)),                    # sırt plakası 2
        cokgen((266, 79), (271, 69), (277, 81)),                    # sırt plakası 3
        cokgen((278, 82), (282, 74), (286, 85)),                    # sırt plakası 4
        kapsul(249, 104, 248, 110, 4.6),                            # ön bacak
        kapsul(258, 105, 258, 110, 3.6),                            # ön bacak (uzak)
        kapsul(275, 104, 276, 110, 4.6),                            # arka bacak
        kapsul(266, 105, 266, 110, 3.6),                            # arka bacak (uzak)
    ], kapa=1.5)


def kontur_spinosaurus():
    """Sırt yelkenli etçil: timsah çenesi, yüksek yelken, güçlü kuyruk."""
    return birlesim([
        elips(66, 148, 29, 12),                                     # gövde
        elips(64, 139, 26, 12),                                     # yelken tabanı
        cokgen((42, 146), (52, 132), (78, 130), (90, 144)),         # yelken
        elips(98, 148, 11, 8, -8),                                  # baş
        kapsul(104, 150, 119, 153, 4.6),                            # uzun çene
        kapsul(40, 152, 27, 157, 5.0),                              # kuyruk
        kapsul(29, 157, 17, 161, 3.3),                              # kuyruk ucu
        elips(72, 156, 9.5, 9),                                     # uyluk
        kapsul(74, 158, 72, 162, 3.8),                              # baldır
        kapsul(68, 163.5, 79, 163.5, 3.0),                          # ayak
        kapsul(52, 157, 52, 161, 3.2),                              # arka bacak
        kapsul(47, 164, 57, 164, 2.6),                              # arka ayak
    ], kapa=1.6)


def kontur_velosiraptor():
    """Çevik etçil: ince boyun, sivri çene, sıçramaya hazır bacaklar."""
    return birlesim([
        elips(246, 150, 14.5, 10, -20),                             # gövde
        kapsul(252, 145, 259, 138, 4.8),                            # ince boyun
        elips(262, 136, 9.0, 7.2, -16),                             # iri baş
        cokgen((263, 130.6), (277, 139.4), (272, 143.2), (258, 141)),  # sivri çene
        kapsul(235, 154, 224, 159, 4.2),                            # kuyruk
        kapsul(226, 159, 216, 161, 2.9),                            # kuyruk ucu
        elips(248, 157, 8.2, 8),                                    # uyluk
        kapsul(250, 161, 248, 164, 3.4),                            # baldır
        kapsul(246, 166.5, 256, 166.5, 2.8),                        # ayak
        kapsul(234, 159, 233, 163, 2.9),                            # arka bacak
        kapsul(228, 165, 237, 165, 2.4),                            # arka ayak
    ], kapa=1.6)


PARCALAR = [(ad, f(), sinif) for ad, f, sinif in [
    ("pteranodon",   kontur_pteranodon,   "ucan"),
    ("brakiyozor",   kontur_brakiyozor,   "otcul"),
    ("trex",         kontur_trex,         "etcil"),
    ("triceratops",  kontur_triceratops,  "otcul"),
    ("stegosaurus",  kontur_stegosaurus,  "otcul"),
    ("spinosaurus",  kontur_spinosaurus,  "etcil"),
    ("velosiraptor", kontur_velosiraptor, "etcil"),
]]

# ---------------------------------------------------------------- parmak yuvaları
YUVA_R = 5.5
YUVA_KONUM = {                     # hedef nokta; kontura otomatik oturtulur
    "pteranodon":   (68, 44),      # gövde altı
    "brakiyozor":   (174, 46),     # kuyruk ucu (sol)
    "trex":         (52, 70),      # sırt üstü
    "triceratops":  (163, 74),     # sırt üstü
    "stegosaurus":  (216, 100),    # baş önü (sol)
    "spinosaurus":  (126, 156),    # çene ucu (sağ)
    "velosiraptor": (211, 162),    # kuyruk ucu (sol)
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

ETIKETLER = {                      # (TR, EN, x, y, boyut, dikey pay)
    "pteranodon":   ("Pteranodon", "Pteranodon", 66, 56.0, 4.0, 2.4),
    "brakiyozor":   ("Brakiyozor", "Brachiosaurus", 218, 64.0, 4.0, 2.4),
    "trex":         ("T-Rex", "T-Rex", 30, 126.0, 4.0, 2.4),
    "triceratops":  ("Triceratops", "Triceratops", 155, 128.0, 4.0, 2.4),
    "stegosaurus":  ("Stegosaurus", "Stegosaurus", 262, 122.0, 3.6, 2.2),
    "spinosaurus":  ("Spinosaurus", "Spinosaurus", 72, 176.0, 3.6, 2.2),
    "velosiraptor": ("Velosiraptor", "Velociraptor", 247, 176.0, 3.6, 2.2),
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
    g = []
    # sahne
    g.append(_lin("gokyuzu", 0, -6, 0, 96, [(0, "#7CC6EE"), (0.55, "#A5DCF4"),
                                            (1, "#CDEEFA")]))
    g.append(_lin("dag", 0, 44, 0, 82, [(0, "#8FA9BE"), (1, "#6E8CA5")]))
    g.append(_lin("orman", 0, 56, 0, 116, [(0, "#2E7A45"), (1, "#1E5C33")]))
    g.append(_lin("cim", 0, 100, 0, 186, [(0, "#8FC94A"), (0.55, "#79B637"),
                                          (1, "#5F9B27")]))
    g.append(_lin("gol", 0, 146, 0, 186, [(0, "#5FC2EC"), (1, "#2C93CC")]))
    g.append(_lin("patika", 0, 148, 0, 186, [(0, "#EBD08A"), (1, "#D6B463")]))
    g.append(_rad("gunes", 300, 4, 90, [(0, "#FFF6D2", 0.55), (0.6, "#FFF6D2", 0.18),
                                        (1, "#FFF6D2", 0)]))
    # dinozor renkleri
    g.append(_lin("pterog", 0, 12, 0, 46, [(0, "#F5A83C"), (0.55, "#E88526"),
                                           (1, "#D06D14")]))
    g.append(_lin("brakig", 0, 8, 0, 56, [(0, "#57B7B0"), (0.5, "#3C9C99"),
                                          (1, "#2C7F80")]))
    g.append(_lin("trexg", 0, 66, 0, 120, [(0, "#8DBE4C"), (0.5, "#6FA234"),
                                           (1, "#568425")]))
    g.append(_lin("tricerag", 0, 76, 0, 122, [(0, "#A8AE5E"), (0.5, "#8B9247"),
                                              (1, "#6F7635")]))
    g.append(_lin("stegog", 0, 66, 0, 116, [(0, "#9CC456"), (0.5, "#7EA83D"),
                                            (1, "#628A2A")]))
    g.append(_lin("spinog", 0, 128, 0, 170, [(0, "#A98BDA"), (0.5, "#8F6DC6"),
                                             (1, "#7454A9")]))
    g.append(_lin("velog", 0, 128, 0, 170, [(0, "#F2AE45"), (0.5, "#E28B26"),
                                            (1, "#C87014")]))
    g.append(_lin("yelkeng", 0, 128, 0, 150, [(0, "#F0705A"), (0.6, "#DB4A38"),
                                              (1, "#BE3324")]))
    g.append(_lin("plakag", 0, 66, 0, 92, [(0, "#F08A4B"), (0.6, "#DE6B2C"),
                                           (1, "#C1521A")]))
    return "<defs>" + "".join(g) + "</defs>"


def _klip(e, ad, poly):
    e.append(f'<clipPath id="{ad}"><path d="{yol_svg(poly)}"/></clipPath>')
    return f"url(#{ad})"


def zemin_golgesi(e, cx, cy, rx):
    for f_rx, ry, op in [(1.0, 2.4, 0.10), (0.75, 1.7, 0.10), (0.5, 1.2, 0.12)]:
        e.append(_el("ellipse", cx=cx, cy=cy, rx=rx * f_rx, ry=ry,
                     fill="#1E4416", opacity=f"{op}"))


def hacim(e, klip, poly, guc=0.12):
    x0, y0, x1, y1 = poly.bounds
    w, h = x1 - x0, y1 - y0
    e.append(_el("ellipse", cx=x0 + w * 0.4, cy=y0 + h * 0.18, rx=w * 0.6, ry=h * 0.32,
                 fill="#FFFFFF", opacity=f"{guc}", clip_path=f"url(#{klip})"))
    e.append(_el("ellipse", cx=x0 + w * 0.55, cy=y1 + h * 0.02, rx=w * 0.72, ry=h * 0.26,
                 fill="#20140A", opacity=f"{guc * 0.8}", clip_path=f"url(#{klip})"))


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
                 fill="#1B3310", opacity=0.2))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.6,
                 fill="#FFFFFF", opacity=0.97))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.6,
                 fill="none", stroke="#2A3A28", stroke_width=0.35, opacity=0.5))
    bas = x - (w_on + w_en) / 2
    e.append(_el("text", x=bas, y=y, icerik=on, fill="#1C2733", font_size=boyut,
                 font_family="sans-serif", font_weight="bold", text_anchor="start"))
    e.append(_el("text", x=bas + w_on, y=y, icerik=en, fill="#2563D9",
                 font_size=boyut, font_family="sans-serif", font_weight="bold",
                 text_anchor="start"))

# ---------------------------------------------------------------- dekor
def bulut(e, x, y, s=1.0):
    for dx, dy, r in [(-5.5, 1.0, 3.4), (0, -1.4, 4.6), (5.2, 0.6, 3.6),
                      (-1.6, 1.8, 3.8), (3.0, 2.0, 3.2)]:
        e.append(_el("circle", cx=x + dx * s, cy=y + dy * s, r=r * s, fill="#FFFFFF",
                     opacity=0.95))
    e.append(_el("ellipse", cx=x, cy=y + 2.6 * s, rx=8.4 * s, ry=2.4 * s,
                 fill="#FFFFFF", opacity=0.95))


def yanardag(e, x, taban, boy, gen):
    """Duman tüten volkan konisi."""
    yarim = gen / 2
    e.append(_el("path", d=f"M {x-yarim} {taban} L {x-6} {taban-boy} L {x+6} {taban-boy} "
                           f"L {x+yarim} {taban} Z", fill="#8B93A0"))
    e.append(_el("path", d=f"M {x-yarim} {taban} L {x-6} {taban-boy} L {x-1} {taban-boy} "
                           f"L {x-yarim*0.42} {taban} Z", fill="#9BA4B0", opacity=0.85))
    # kar/kül tepesi
    e.append(_el("path", d=f"M {x-6} {taban-boy} L {x+6} {taban-boy} "
                           f"L {x+4.4} {taban-boy+4.4} L {x+1.4} {taban-boy+2.2} "
                           f"L {x-1.8} {taban-boy+4.6} L {x-4.6} {taban-boy+2.4} Z",
                 fill="#E2E7EC", opacity=0.92))
    # krater ağzı
    e.append(_el("ellipse", cx=x, cy=taban - boy, rx=6, ry=1.6, fill="#5F4038"))
    e.append(_el("ellipse", cx=x, cy=taban - boy + 0.2, rx=4.2, ry=1.0, fill="#E2622A"))
    # yamaç çizgileri
    for dx in (-3.4, 1.2, 4.0):
        e.append(_el("path", d=f"M {x+dx*1.4} {taban-boy+3} L {x+dx*3.4} {taban-2}",
                     stroke="#727C89", stroke_width=0.7, fill="none", opacity=0.8))
    # duman
    for dy, r, op in [(5, 3.0, 0.75), (11, 4.0, 0.6), (18, 5.0, 0.45),
                      (25.5, 5.8, 0.3)]:
        e.append(_el("circle", cx=x + (dy * 0.24), cy=taban - boy - dy, r=r,
                     fill="#D9DEE4", opacity=f"{op}"))
        e.append(_el("circle", cx=x + (dy * 0.24) - r * 0.5, cy=taban - boy - dy + r * 0.2,
                     r=r * 0.68, fill="#E8ECF0", opacity=f"{op * 0.8}"))


def palmiye(e, x, taban, boy, s=1.0, egim=0.0):
    """Gövdesi hafif kavisli palmiye ağacı."""
    tepe_x = x + egim
    tepe_y = taban - boy
    e.append(_el("path", d=f"M {x-2.2*s} {taban} Q {x-1.2*s+egim*0.4} {taban-boy*0.55} "
                           f"{tepe_x-1.5*s} {tepe_y} L {tepe_x+1.5*s} {tepe_y} "
                           f"Q {x+1.2*s+egim*0.4} {taban-boy*0.55} {x+2.2*s} {taban} Z",
                 fill="#8B5E33"))
    for i in range(5):
        yy = tepe_y + 3 + i * (boy - 6) / 5
        xx = x + egim * (1 - (yy - tepe_y) / max(boy, 1)) * 0.9
        e.append(_el("path", d=f"M {xx-2.0*s} {yy} Q {xx} {yy+1.4*s} {xx+2.0*s} {yy}",
                     stroke="#6E4826", stroke_width=0.6 * s, fill="none", opacity=0.9))
    # yapraklar (geniş yelpaze)
    for aci, uz in [(-176, 1.0), (-146, 1.05), (-114, 0.95), (-66, 0.95), (-34, 1.05),
                    (-4, 1.0), (-160, 0.8), (-20, 0.8), (-90, 0.85)]:
        ar = math.radians(aci)
        ux, uy = math.cos(ar), math.sin(ar)
        L = 23.0 * s * uz
        ex_, ey_ = tepe_x + ux * L, tepe_y + uy * L + L * 0.40
        cx_, cy_ = tepe_x + ux * L * 0.52, tepe_y + uy * L * 0.98
        koyu = "#1F7A3C" if uz > 0.95 else "#2C8F49"
        e.append(_el("path", d=f"M {tepe_x} {tepe_y} Q {cx_} {cy_} {ex_} {ey_} "
                               f"Q {cx_+ux*2.0} {cy_+5.4*s} {tepe_x} {tepe_y+2.6*s} Z",
                     fill=koyu))
        e.append(_el("path", d=f"M {tepe_x} {tepe_y} Q {cx_} {cy_} {ex_} {ey_}",
                     stroke="#125C2A", stroke_width=0.6 * s, fill="none",
                     opacity=0.85))
        # yaprak dişleri
        for t in (0.45, 0.68, 0.88):
            lx = tepe_x + ux * L * t * 0.9
            ly = tepe_y + uy * L * t + L * 0.4 * t * t
            e.append(_el("line", x1=lx, y1=ly, x2=lx - ux * 1.2 * s, y2=ly + 3.2 * s,
                         stroke="#155F2C", stroke_width=0.5 * s, opacity=0.7))
    e.append(_el("circle", cx=tepe_x, cy=tepe_y + 0.6 * s, r=2.4 * s, fill="#155F2C"))
    for dx, dy in [(-2.8, 3.0), (2.8, 3.0), (0, 4.2)]:
        e.append(_el("circle", cx=tepe_x + dx * s, cy=tepe_y + dy * s, r=1.4 * s,
                     fill="#C97A2B"))


def egrelti(e, x, taban, boy, s=1.0, renk="#2F9B4E", koyu="#1E7739"):
    """Yelpaze biçimli eğrelti otu."""
    for aci in (-140, -118, -90, -62, -40):
        ar = math.radians(aci)
        ux, uy = math.cos(ar), math.sin(ar)
        ex_, ey_ = x + ux * boy * 0.72, taban + uy * boy
        e.append(_el("path", d=f"M {x} {taban} Q {x+ux*boy*0.3} {taban+uy*boy*0.72} "
                               f"{ex_} {ey_}", stroke=renk, stroke_width=1.9 * s,
                     fill="none", stroke_linecap="round"))
        for t in (0.35, 0.55, 0.75, 0.92):
            px = x + ux * boy * 0.72 * t
            py = taban + uy * boy * t
            e.append(_el("line", x1=px, y1=py, x2=px - uy * 2.6 * s, y2=py + ux * 2.6 * s,
                         stroke=koyu, stroke_width=0.75 * s, stroke_linecap="round"))
            e.append(_el("line", x1=px, y1=py, x2=px + uy * 2.6 * s, y2=py - ux * 2.6 * s,
                         stroke=koyu, stroke_width=0.75 * s, stroke_linecap="round"))


def cali(e, x, taban, w, h, renk="#3FA85A", koyu="#2A8443"):
    """Yuvarlak çalı öbeği."""
    for dx, dy, r in [(-w * 0.32, -h * 0.12, h * 0.52), (0, -h * 0.34, h * 0.62),
                      (w * 0.32, -h * 0.1, h * 0.5)]:
        e.append(_el("circle", cx=x + dx, cy=taban + dy, r=r, fill=renk))
    for dx, dy, r in [(-w * 0.3, -h * 0.3, h * 0.26), (w * 0.12, -h * 0.55, h * 0.28)]:
        e.append(_el("circle", cx=x + dx, cy=taban + dy, r=r, fill=koyu, opacity=0.55))


def kaya(e, x, taban, w, h, renk="#8892A0"):
    e.append(_el("path", d=f"M {x-w/2} {taban} Q {x-w/2-1} {taban-h} {x-w*0.1} {taban-h} "
                           f"Q {x+w/2+1} {taban-h*0.9} {x+w/2} {taban} Z", fill=renk))
    e.append(_el("path", d=f"M {x-w*0.32} {taban-h*0.86} Q {x} {taban-h*1.04} "
                           f"{x+w*0.3} {taban-h*0.8}", fill="none", stroke="#B2BCC7",
                 stroke_width=1.0, opacity=0.9))
    e.append(_el("path", d=f"M {x-w/2} {taban} Q {x-w*0.1} {taban-h*0.18} {x+w/2} {taban}",
                 fill="#5F6B78", opacity=0.25))


def nilufer(e, x, y, r, cicek=False):
    e.append(_el("path", d=f"M {x+r} {y} A {r} {r*0.86} 0 1 0 {x+r*0.28} {y-r*0.86} "
                           f"L {x} {y} Z", fill="#3E9E4E"))
    e.append(_el("path", d=f"M {x+r} {y} A {r} {r*0.86} 0 1 0 {x+r*0.28} {y-r*0.86}",
                 fill="none", stroke="#2E7F3C", stroke_width=0.4))
    if cicek:
        for i in range(6):
            ar = math.radians(i * 60)
            e.append(_el("ellipse", cx=x - r * 0.1 + math.cos(ar) * r * 0.34,
                         cy=y - r * 0.34 + math.sin(ar) * r * 0.3, rx=r * 0.3,
                         ry=r * 0.18, fill="#F6A8C8",
                         transform=f"rotate({i*60} {x-r*0.1+math.cos(ar)*r*0.34:.2f} "
                                   f"{y-r*0.34+math.sin(ar)*r*0.3:.2f})"))
        e.append(_el("circle", cx=x - r * 0.1, cy=y - r * 0.34, r=r * 0.16,
                     fill="#F7D64A"))


def ayak_izi(e, x, y, s=1.0, aci=0.0):
    """Kuma basılmış üç parmaklı dinozor ayak izi."""
    g = [f'<g transform="rotate({aci} {x} {y})" opacity="0.28">']
    g.append(_el("ellipse", cx=x, cy=y, rx=2.6 * s, ry=3.2 * s, fill="#A8823C"))
    for dx, dy in [(-2.4, -3.0), (0, -4.0), (2.4, -3.0)]:
        g.append(_el("ellipse", cx=x + dx * s, cy=y + dy * s, rx=1.15 * s, ry=1.7 * s,
                     fill="#A8823C"))
    g.append("</g>")
    e.append("".join(g))

# ---------------------------------------------------------------- sahne
def sahne_svg(yuva_goster=False):
    rnd = random.Random(71)
    e = [tanimlar()]

    # --- gökyüzü + güneş ışığı
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=112, fill="url(#gokyuzu)"))
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=100, fill="url(#gunes)"))

    # --- bulutlar (boş bölgelerde)
    bulut(e, 12, 15, 0.8)
    bulut(e, 146, 11, 0.95)
    bulut(e, 170, 32, 0.7)
    bulut(e, 101, 8, 0.6)
    bulut(e, 116, 30, 0.65)

    # --- uzak dağ silsilesi (arka plan bandı)
    e.append(_el("path", d="M -6 78 L 24 54 L 44 66 L 70 46 L 96 68 L 122 50 L 150 70 "
                           "L 178 48 L 206 68 L 236 52 L 262 70 L 292 50 L 326 74 "
                           "L 326 96 L -6 96 Z", fill="url(#dag)", opacity=0.92))
    for px, py in [(70, 46), (178, 48), (292, 50)]:
        e.append(_el("path", d=f"M {px-7} {py+8} L {px} {py} L {px+7} {py+8} "
                              f"L {px+3.4} {py+6.4} L {px} {py+8.4} L {px-3.6} {py+6.6} Z",
                     fill="#DDE6EE", opacity=0.8))

    # --- yanardağ (ormanın ardında, üst-orta boşlukta)
    yanardag(e, 142, 86, 48, 60)

    # --- orman bandı (yuvarlak tropik kanopi, arka plan)
    e.append(_el("path", d="M -6 74 Q 40 66 84 72 Q 130 78 176 70 Q 224 62 268 72 "
                           "Q 300 79 326 71 L 326 118 L -6 118 Z", fill="#2A7040",
                 opacity=0.55))
    for i in range(40):
        cx_ = -10 + i * 8.6
        cy_ = 80 - (4 + ((i * 7) % 5) * 3.2)
        r_ = 7.5 + ((i * 5) % 4) * 1.7
        e.append(_el("circle", cx=f"{cx_:.1f}", cy=f"{cy_:.1f}", r=f"{r_:.1f}",
                     fill="url(#orman)"))
    e.append(_el("rect", x=-6, y=79, width=W + 12, height=39, fill="url(#orman)"))
    for i in range(30):
        cx_ = -8 + i * 11.4
        cy_ = 79 - (2 + ((i * 11) % 4) * 2.6)
        r_ = 5.4 + ((i * 3) % 3) * 1.2
        e.append(_el("circle", cx=f"{cx_:.1f}", cy=f"{cy_:.1f}", r=f"{r_:.1f}",
                     fill="#3B8C50", opacity=0.7))

    # --- çimen zemin
    e.append(_el("path", d="M -6 104 Q 60 96 120 103 Q 190 111 250 101 Q 292 95 326 104 "
                           "L 326 186 L -6 186 Z", fill="url(#cim)"))
    for _ in range(150):
        px, py = rnd.uniform(-4, 322), rnd.uniform(106, 182)
        hh = rnd.uniform(1.4, 3.4)
        e.append(_el("path", d=f"M {px:.1f} {py:.1f} q {hh*0.4:.1f} {-hh*0.6:.1f} "
                              f"{hh*0.15:.1f} {-hh:.1f}", stroke="#57931F",
                     stroke_width=0.45, fill="none",
                     opacity=f"{rnd.uniform(0.3, 0.65):.2f}"))

    # --- sol alt gölet (spinosaurus burada yürüyor)
    e.append(_el("path", d="M -6 148 Q 30 141 68 146 Q 112 152 138 165 Q 150 172 146 186 "
                           "L -6 186 Z", fill="url(#gol)"))
    e.append(_el("path", d="M -6 148 Q 30 141 68 146 Q 112 152 138 165 Q 150 172 146 186",
                 fill="none", stroke="#1F7FB4", stroke_width=1.0, opacity=0.6))
    for wy, wx0, wx1, op in [(156, -4, 40, 0.5), (166, 6, 52, 0.4), (176, -2, 44, 0.45),
                             (161, 96, 130, 0.4), (172, 88, 126, 0.35)]:
        dd = f"M {wx0} {wy} "
        n = max(2, int((wx1 - wx0) / 9))
        for i in range(n):
            dd += f"q 4.5 {-1.5 if i % 2 == 0 else 1.5} 9 0 "
        e.append(_el("path", d=dd, fill="none", stroke="#FFFFFF", stroke_width=0.9,
                     opacity=f"{op}"))
    nilufer(e, 6, 172, 5.0, cicek=True)
    nilufer(e, -2, 160, 4.2)
    nilufer(e, 132, 178, 4.6, cicek=True)

    # --- sağ alt kum patikası
    e.append(_el("path", d="M 326 128 Q 292 134 268 148 Q 246 161 240 186 L 326 186 Z",
                 fill="url(#patika)"))
    e.append(_el("path", d="M 326 128 Q 292 134 268 148 Q 246 161 240 186", fill="none",
                 stroke="#C9A34F", stroke_width=0.9, opacity=0.7))
    for _ in range(45):
        px, py = rnd.uniform(250, 322), rnd.uniform(140, 182)
        e.append(_el("circle", cx=f"{px:.1f}", cy=f"{py:.1f}",
                     r=f"{rnd.uniform(0.2, 0.55):.2f}", fill="#B98F3E",
                     opacity=f"{rnd.uniform(0.3, 0.6):.2f}"))
    ayak_izi(e, 296, 168, 1.0, 12)
    ayak_izi(e, 288, 158, 1.0, 6)
    ayak_izi(e, 305, 152, 1.0, 18)

    # --- palmiyeler (parça kutularının dışında)
    palmiye(e, 10, 64, 42, 0.82, egim=-2.5)
    palmiye(e, 274, 64, 38, 0.78, egim=3.0)
    palmiye(e, 178, 178, 32, 0.66, egim=-2.0)

    # --- alt orta ve kenar bitki/kaya öbekleri
    kaya(e, 138, 178, 18, 9)
    kaya(e, 152, 174, 11, 5.6, "#78838F")
    egrelti(e, 168, 176, 15, 0.95)
    cali(e, 186, 176, 16, 11)
    egrelti(e, 200, 174, 12, 0.8, "#3BAE5C", "#268A45")
    ayak_izi(e, 160, 152, 0.9, -8)

    kaya(e, 300, 128, 16, 8)
    egrelti(e, 314, 140, 13, 0.85)
    cali(e, 291, 172, 15, 10, "#38A055", "#26783E")
    kaya(e, 6, 130, 13, 6.5, "#7D8894")
    egrelti(e, 5, 124, 12, 0.8)
    cali(e, 213, 138, 13, 9, "#43AE60", "#2C8546")

    # --- yere basan dinozorların zemin gölgeleri
    zemin_golgesi(e, 56, 118, 24)
    zemin_golgesi(e, 161, 116, 30)
    zemin_golgesi(e, 261, 111, 26)
    zemin_golgesi(e, 246, 168, 18)

    # --- dinozorlar
    e += dino_detaylari()

    # --- parça dış çizgileri (kalın, masal kitabı konturu)
    for _, poly, _ in PARCALAR:
        e.append(_el("path", d=yol_svg(poly), fill="none", stroke="#20262B",
                     stroke_width=1.5, stroke_linejoin="round"))

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

# ---------------------------------------------------------------- dinozor detayları
def goz(e, x, y, r, bakis=(0.25, 0.1)):
    """Masal kitabı gözü: beyaz + iri siyah bebek + parlak nokta."""
    e.append(_el("circle", cx=x, cy=y, r=r, fill="#FFFFFF"))
    e.append(_el("circle", cx=x, cy=y, r=r, fill="none", stroke="#20262B",
                 stroke_width=r * 0.16))
    e.append(_el("circle", cx=x + r * bakis[0], cy=y + r * bakis[1], r=r * 0.58,
                 fill="#20262B"))
    e.append(_el("circle", cx=x + r * (bakis[0] + 0.16), cy=y + r * (bakis[1] - 0.28),
                 r=r * 0.2, fill="#FFFFFF"))


def gulus(e, x, y, w, kal=1.1):
    e.append(_el("path", d=f"M {x - w / 2} {y} Q {x} {y + w * 0.55} {x + w / 2} {y}",
                 fill="none", stroke="#20262B", stroke_width=kal,
                 stroke_linecap="round"))


def disler(e, noktalar, boy=1.8, asagi=True, klip=None):
    """Ağız hattı boyunca sivri beyaz dişler."""
    ek = {"clip_path": klip} if klip else {}
    for (x, y) in noktalar:
        yy = y + boy if asagi else y - boy
        e.append(_el("path", d=f"M {x-0.9} {y} L {x+0.9} {y} L {x} {yy} Z",
                     fill="#FFFFFF", stroke="#C8CDD2", stroke_width=0.2, **ek))


def benekler(e, noktalar, renk, klip=None, op=0.9):
    ek = {"clip_path": klip} if klip else {}
    for (x, y, r) in noktalar:
        e.append(_el("circle", cx=x, cy=y, r=r, fill=renk, opacity=f"{op}", **ek))


def dino_detaylari():
    e = []
    P = {ad: poly for ad, poly, _ in PARCALAR}
    CIZGI = "#20262B"

    # ---------- PTERANODON (turuncu, süzülen)
    p = P["pteranodon"]
    kp = _klip(e, "kptero", p)
    e.append(_el("path", d=yol_svg(p), fill="url(#pterog)"))
    # kanat zarları (açık ton)
    e.append(_el("path", d="M 62 30 L 44 15 L 30 16 L 34 25 L 54 39 Z", fill="#F7C079",
                 opacity=0.95, clip_path=kp))
    e.append(_el("path", d="M 76 29 L 92 14 L 104 17 L 98 27 L 84 35 Z", fill="#F7C079",
                 opacity=0.95, clip_path=kp))
    # kanat parmak çizgileri
    for x1, y1, x2, y2 in [(63, 31, 39, 20), (63, 33, 45, 27), (64, 35, 51, 33),
                           (76, 30, 96, 19), (76, 32, 95, 25), (77, 34, 90, 31)]:
        e.append(_el("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke="#C97C21",
                     stroke_width=0.75, opacity=0.85, clip_path=kp))
    # kanat ön kenarı koyu bant
    e.append(_el("path", d="M 30 16 Q 46 12.5 63 29", fill="none", stroke="#D06D14",
                 stroke_width=2.0, opacity=0.9, clip_path=kp))
    e.append(_el("path", d="M 104 17 Q 90 12 76 29", fill="none", stroke="#D06D14",
                 stroke_width=2.0, opacity=0.9, clip_path=kp))
    # gövde tüy dokusu
    for gx, gy in [(63, 31), (68, 32), (73, 31.5), (66, 35), (71, 35.5)]:
        e.append(_el("path", d=f"M {gx-1.6} {gy} q 1.6 1.4 3.2 0", stroke="#C97C21",
                     stroke_width=0.55, fill="none", opacity=0.75, clip_path=kp))
    # ibik (yalnız baskıda – silüette yok)
    e.append(_el("path", d="M 82 33 L 64 22.5 L 68 20 L 85 29.5 Z", fill="#F7C079",
                 stroke=CIZGI, stroke_width=1.0, stroke_linejoin="round",
                 clip_path=kp))
    e.append(_el("path", d="M 80 30.6 L 69.5 24.4", stroke="#C97C21", stroke_width=0.7,
                 fill="none", opacity=0.9, clip_path=kp))
    # gaga ayrım hattı
    e.append(_el("path", d="M 86 37.4 Q 93 39.2 99.5 42.2", fill="none", stroke=CIZGI,
                 stroke_width=1.0, stroke_linecap="round"))
    goz(e, 83.5, 34.8, 2.9, (0.3, 0.08))
    e.append(_el("ellipse", cx=90.5, cy=38.8, rx=0.8, ry=0.5, fill=CIZGI, opacity=0.8))
    hacim(e, "kptero", p, 0.10)

    # ---------- BRAKİYOZOR (turkuaz, uzun boyunlu)
    b = P["brakiyozor"]
    kb = _klip(e, "kbraki", b)
    e.append(_el("path", d=yol_svg(b), fill="url(#brakig)"))
    # açık krem karın + boyun ön hattı
    e.append(_el("path", d="M 203 45 Q 223 57 243 45 L 246 60 L 201 60 Z", fill="#F2E3BE",
                 opacity=0.95, clip_path=kb))
    e.append(_el("path", d="M 235.4 40.6 L 246.4 15.6 L 249.4 17.0 L 238.4 42.0 Z",
                 fill="#F2E3BE", opacity=0.9, clip_path=kb))
    e.append(_el("path", d="M 203 45 Q 223 57 243 45", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.8, clip_path=kb))
    # sırt benekleri
    benekler(e, [(211, 34, 2.0), (219, 32, 2.3), (228, 33.5, 2.0), (234, 37, 1.7),
                 (205, 38, 1.7), (223, 39, 1.9), (214, 41, 1.6), (238, 29, 1.5),
                 (241, 23, 1.4), (243.5, 17, 1.2)], "#2C7F80", kb, 0.55)
    # bacak ayrım çizgileri (kaynaşan bacakları baskıda ayır)
    for dd in ("M 226.5 46 Q 226.5 51 226.5 58", "M 214 45.5 Q 214 51 214 58"):
        e.append(_el("path", d=dd, fill="none", stroke="#1E6466", stroke_width=2.2,
                     opacity=0.9, clip_path=kb))
        e.append(_el("path", d=dd, fill="none", stroke=CIZGI, stroke_width=0.9,
                     opacity=0.65, clip_path=kb))
    # kuyruk çizgisi
    e.append(_el("path", d="M 204 41 Q 193 44.5 182 46.5", fill="none", stroke="#2C7F80",
                 stroke_width=0.9, opacity=0.8, clip_path=kb))
    # boyun boğumları
    for i in range(6):
        t = 0.1 + i * 0.17
        nx, ny = 234 + 11 * t, 40 - 25 * t
        e.append(_el("line", x1=nx - 3.4, y1=ny - 1.5, x2=nx + 3.4, y2=ny + 1.5,
                     stroke="#2C7F80", stroke_width=0.7, opacity=0.5, clip_path=kb))
    # baş
    e.append(_el("path", d="M 243.5 12.6 Q 248 10.8 253 13.2", fill="none",
                 stroke=CIZGI, stroke_width=0.9, opacity=0.85))
    gulus(e, 250.0, 14.4, 3.6, 0.9)
    goz(e, 248.4, 10.4, 2.1, (0.26, 0.06))
    # burun deliği
    e.append(_el("ellipse", cx=253.0, cy=11.4, rx=0.7, ry=0.45, fill=CIZGI,
                 opacity=0.8))
    hacim(e, "kbraki", b, 0.09)

    # ---------- T-REX (yeşil, sarı karınlı)
    t = P["trex"]
    kt = _klip(e, "ktrex", t)
    e.append(_el("path", d=yol_svg(t), fill="url(#trexg)"))
    # sarı karın
    e.append(_el("path", d="M 34 92 Q 52 104 70 91 L 72 122 L 32 122 Z", fill="#F0D452",
                 opacity=0.95, clip_path=kt))
    e.append(_el("path", d="M 34 92 Q 52 104 70 91", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.75, clip_path=kt))
    e.append(_el("path", d="M 64 80 Q 70 86 68 94 L 76 94 L 76 76 Z", fill="#F0D452",
                 opacity=0.9, clip_path=kt))
    # sırt benekleri
    benekler(e, [(44, 80, 2.2), (52, 78, 2.4), (60, 80, 2.0), (38, 86, 1.8),
                 (48, 85, 1.9), (56, 86, 1.7), (32, 92, 1.6), (28, 98, 1.5),
                 (72, 68, 1.7), (80, 67, 1.5), (66, 71, 1.4)], "#4C7B1F", kt, 0.55)
    # kuyruk çizgisi
    e.append(_el("path", d="M 38 96 Q 26 102 15 107", fill="none", stroke="#4C7B1F",
                 stroke_width=1.0, opacity=0.8, clip_path=kt))
    # bacak ayrımı (kaynaşan bacakları baskıda ayır)
    e.append(_el("path", d="M 62 99 Q 66 106 65.5 118", fill="none", stroke="#3F6B18",
                 stroke_width=2.6, opacity=0.9, clip_path=kt))
    e.append(_el("path", d="M 62 99 Q 66 106 65.5 118", fill="none", stroke=CIZGI,
                 stroke_width=1.0, opacity=0.7, clip_path=kt))
    e.append(_el("path", d="M 44 104 Q 52 101 58 104", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.6, clip_path=kt))
    e.append(_el("path", d="M 68 106 Q 71 110 71 114", fill="none", stroke=CIZGI,
                 stroke_width=0.85, opacity=0.6, clip_path=kt))
    # pençeler
    for fx in (47.5, 51.5, 55.5):
        e.append(_el("path", d=f"M {fx} 117.4 L {fx+1.6} 118.6 L {fx-0.4} 118.6 Z",
                     fill="#F2EEDC", clip_path=kt))
    for fx in (70.5, 74.0, 77.0):
        e.append(_el("path", d=f"M {fx} 116 L {fx+1.4} 117 L {fx-0.4} 117 Z",
                     fill="#F2EEDC", clip_path=kt))
    # minik kol + pençe (baskıda)
    e.append(_el("path", d="M 63.5 87 Q 68.5 89.5 71.5 93.5", fill="none",
                 stroke="#4C7B1F", stroke_width=3.4, stroke_linecap="round",
                 clip_path=kt))
    e.append(_el("path", d="M 63.5 87 Q 68.5 89.5 71.5 93.5", fill="none", stroke=CIZGI,
                 stroke_width=1.0, stroke_linecap="round", clip_path=kt))
    for cx_, cy_ in [(73.4, 94.4), (72.2, 96.0)]:
        e.append(_el("path", d=f"M {cx_-1.2} {cy_-1.2} L {cx_+0.8} {cy_+0.6} "
                              f"L {cx_-1.6} {cy_+0.4} Z", fill="#F2EEDC",
                     clip_path=kt))
    # ağız + dişler
    e.append(_el("path", d="M 66 81.6 Q 78 84.4 89.6 79.2", fill="none", stroke=CIZGI,
                 stroke_width=1.2, stroke_linecap="round"))
    disler(e, [(70, 81.0), (74, 81.9), (78, 82.2), (82, 81.8), (86, 80.6)], 1.9,
           True, kt)
    disler(e, [(72, 79.6), (76.5, 80.1), (81, 79.9), (85, 79.2)], 1.7, False, kt)
    e.append(_el("path", d="M 88.5 76 Q 90.6 77.6 90 80", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.85))
    # kaş + göz + burun
    e.append(_el("path", d="M 73 67.6 Q 78 66 82.5 68", fill="none", stroke="#4C7B1F",
                 stroke_width=1.6, opacity=0.9, stroke_linecap="round"))
    goz(e, 78, 71, 3.3, (0.24, 0.06))
    e.append(_el("ellipse", cx=87.6, cy=75.2, rx=0.9, ry=0.6, fill=CIZGI, opacity=0.8))
    hacim(e, "ktrex", t, 0.10)

    # ---------- TRICERATOPS (haki yeşil, üç boynuzlu)
    c = P["triceratops"]
    kc = _klip(e, "ktricera", c)
    e.append(_el("path", d=yol_svg(c), fill="url(#tricerag)"))
    # açık karın
    e.append(_el("path", d="M 142 100 Q 163 112 186 99 L 188 122 L 140 122 Z",
                 fill="#E4DFA8", opacity=0.9, clip_path=kc))
    e.append(_el("path", d="M 142 100 Q 163 112 186 99", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.7, clip_path=kc))
    # yaka kalkanı
    e.append(f'<g clip-path="{kc}">')
    e.append(_el("ellipse", cx=136, cy=95, rx=11.5, ry=14.5, fill="#C6B96A",
                 transform="rotate(-12 136 95)"))
    e.append(_el("ellipse", cx=136, cy=95, rx=11.5, ry=14.5, fill="none", stroke=CIZGI,
                 stroke_width=1.3, transform="rotate(-12 136 95)"))
    for aa in (-118, -78, -38, 2, 42):
        ar = math.radians(aa)
        e.append(_el("circle", cx=136 + 10.6 * math.cos(ar), cy=95 + 13.2 * math.sin(ar),
                     r=1.6, fill="#A89B4E"))
    for aa in (-100, -60, -20, 20):
        ar = math.radians(aa)
        e.append(_el("line", x1=136 + 3.4 * math.cos(ar), y1=95 + 4.2 * math.sin(ar),
                     x2=136 + 9.6 * math.cos(ar), y2=95 + 12 * math.sin(ar),
                     stroke="#A89B4E", stroke_width=0.85, opacity=0.9))
    e.append("</g>")
    # boynuzlar (krem)
    e.append(_el("path", d="M 122.5 90.5 L 113 78.5 L 120.5 86.5 Z", fill="#F3EBCD",
                 stroke=CIZGI, stroke_width=0.8, stroke_linejoin="round",
                 clip_path=kc))
    e.append(_el("path", d="M 131.5 88.5 L 126 76.5 L 133.5 85.5 Z", fill="#F3EBCD",
                 stroke=CIZGI, stroke_width=0.8, stroke_linejoin="round",
                 clip_path=kc))
    e.append(_el("path", d="M 115.5 95.5 L 107 92 L 116.5 89.6 Z", fill="#F3EBCD",
                 stroke=CIZGI, stroke_width=0.8, stroke_linejoin="round",
                 clip_path=kc))
    # gaga ağız
    e.append(_el("path", d="M 114.5 101.5 Q 119 103.6 124 102.6", fill="none",
                 stroke=CIZGI, stroke_width=1.1, stroke_linecap="round"))
    goz(e, 122, 96.5, 2.7, (-0.3, 0.05))
    e.append(_el("ellipse", cx=115.5, cy=98.4, rx=0.8, ry=0.55, fill=CIZGI,
                 opacity=0.8))
    # sırt benekleri
    benekler(e, [(155, 86, 2.2), (164, 84.5, 2.4), (173, 86.5, 2.0), (180, 90, 1.7),
                 (150, 91, 1.8), (160, 92, 1.7), (170, 92.5, 1.6), (186, 92, 1.4)],
             "#6F7635", kc, 0.55)
    # bacak ayrımları (kaynaşan bacakları baskıda ayır)
    for dd in ("M 152 105 Q 156 110 156 119", "M 172.5 105 Q 168 110 168 119"):
        e.append(_el("path", d=dd, fill="none", stroke="#5D6329", stroke_width=2.4,
                     opacity=0.9, clip_path=kc))
        e.append(_el("path", d=dd, fill="none", stroke=CIZGI, stroke_width=0.95,
                     opacity=0.7, clip_path=kc))
    # tırnaklar
    for fx in (144.5, 153.5, 175.5, 165.5):
        e.append(_el("path", d=f"M {fx} 118 L {fx+3.4} 118 L {fx+1.7} 119.8 Z",
                     fill="#F3EBCD", clip_path=kc))
    hacim(e, "ktricera", c, 0.09)

    # ---------- STEGOSAURUS (yeşil gövde, turuncu plakalar)
    s = P["stegosaurus"]
    ks = _klip(e, "kstego", s)
    e.append(_el("path", d=yol_svg(s), fill="url(#stegog)"))
    # açık karın
    e.append(_el("path", d="M 240 96 Q 262 108 285 95 L 287 118 L 238 118 Z",
                 fill="#E6E0A4", opacity=0.9, clip_path=ks))
    e.append(_el("path", d="M 240 96 Q 262 108 285 95", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.7, clip_path=ks))
    # sırt plakaları
    for pts in ["243.5,83 247,69.5 253.5,82",
                "253.5,81 259,67.5 265.5,80",
                "265.5,80 271,68.5 277.5,82",
                "277.5,83 282,73.5 286.5,86"]:
        d = "M " + " L ".join(pts.split()) + " Z"
        e.append(_el("path", d=d, fill="url(#plakag)", clip_path=ks))
        e.append(_el("path", d=d, fill="none", stroke=CIZGI, stroke_width=1.1,
                     clip_path=ks))
    for cx_, cy_, rx_, ry_ in [(247.5, 77, 1.6, 3.2), (259.5, 75, 1.8, 3.6),
                               (271.5, 76, 1.7, 3.4), (282, 80, 1.3, 2.6)]:
        e.append(_el("ellipse", cx=cx_, cy=cy_, rx=rx_, ry=ry_, fill="#F7B382",
                     opacity=0.75, clip_path=ks))
    # kuyruk dikenleri (krem)
    for d in ["M 297 82.5 L 307.5 77.5 L 301 88 Z", "M 298 89 L 308.5 91.5 L 299 95 Z"]:
        e.append(_el("path", d=d, fill="#F3EBCD", stroke=CIZGI, stroke_width=0.8,
                     clip_path=ks))
    # gövde benekleri
    benekler(e, [(252, 90, 2.0), (261, 88.5, 2.2), (270, 90, 1.9), (278, 93, 1.6),
                 (247, 95, 1.7), (258, 96, 1.6), (268, 96.5, 1.5), (236, 92, 1.5)],
             "#5C8226", ks, 0.55)
    # bacak ayrımları (kaynaşan bacakları baskıda ayır) + tırnaklar
    for dd in ("M 254 102 Q 258 106 258 114", "M 271 102 Q 266 106 266 114"):
        e.append(_el("path", d=dd, fill="none", stroke="#54781F", stroke_width=2.4,
                     opacity=0.9, clip_path=ks))
        e.append(_el("path", d=dd, fill="none", stroke=CIZGI, stroke_width=0.95,
                     opacity=0.7, clip_path=ks))
    for fx in (246.5, 256, 273.5, 264):
        e.append(_el("path", d=f"M {fx} 113 L {fx+3.4} 113 L {fx+1.7} 114.8 Z",
                     fill="#F3EBCD", clip_path=ks))
    # baş
    e.append(_el("path", d="M 216.5 100.6 Q 221 102.6 226 101.4", fill="none",
                 stroke=CIZGI, stroke_width=1.0, stroke_linecap="round"))
    goz(e, 223, 96.4, 2.4, (-0.3, 0.05))
    e.append(_el("ellipse", cx=216.6, cy=97.6, rx=0.75, ry=0.5, fill=CIZGI,
                 opacity=0.8))
    hacim(e, "kstego", s, 0.09)

    # ---------- SPINOSAURUS (mor gövde, kırmızı yelken)
    sp = P["spinosaurus"]
    ksp = _klip(e, "kspino", sp)
    e.append(_el("path", d=yol_svg(sp), fill="url(#spinog)"))
    # yelken
    e.append(_el("path", d="M 41.5 145 Q 50 131 66 129 Q 82 130 90.5 143.5 "
                           "Q 66 138 41.5 145 Z", fill="url(#yelkeng)", clip_path=ksp))
    e.append(_el("path", d="M 41.5 145 Q 50 131 66 129 Q 82 130 90.5 143.5", fill="none",
                 stroke=CIZGI, stroke_width=1.2, clip_path=ksp))
    for tx, ty in [(48, 136), (55, 131.5), (62, 129.8), (70, 129.8), (78, 131.5),
                   (85, 136)]:
        e.append(_el("line", x1=tx, y1=ty, x2=tx + (66 - tx) * 0.13, y2=143,
                     stroke="#9E2A1C", stroke_width=0.85, opacity=0.85,
                     clip_path=ksp))
    # krem karın
    e.append(_el("path", d="M 42 151 Q 66 162 94 150 L 96 172 L 40 172 Z",
                 fill="#F0E2C4", opacity=0.92, clip_path=ksp))
    e.append(_el("path", d="M 42 151 Q 66 162 94 150", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.7, clip_path=ksp))
    # gövde benekleri
    benekler(e, [(50, 148, 2.0), (58, 147, 2.2), (74, 147.5, 2.0), (84, 148, 1.7),
                 (46, 153, 1.7), (66, 152, 1.6), (78, 152.5, 1.5), (34, 153, 1.5),
                 (26, 157, 1.3)], "#6B4CA0", ksp, 0.5)
    # kuyruk çizgisi
    e.append(_el("path", d="M 40 154 Q 28 158 18 161", fill="none", stroke="#6B4CA0",
                 stroke_width=1.0, opacity=0.8, clip_path=ksp))
    # bacak ayrımı (kaynaşan bacakları baskıda ayır) + pençeler
    e.append(_el("path", d="M 64 155 Q 60 160 60 168", fill="none", stroke="#6B4CA0",
                 stroke_width=2.6, opacity=0.95, clip_path=ksp))
    e.append(_el("path", d="M 64 155 Q 60 160 60 168", fill="none", stroke=CIZGI,
                 stroke_width=1.0, opacity=0.7, clip_path=ksp))
    e.append(_el("path", d="M 51 158 Q 52 161 52 166", fill="none", stroke=CIZGI,
                 stroke_width=0.85, opacity=0.6, clip_path=ksp))
    for fx in (69, 73.5, 78):
        e.append(_el("path", d=f"M {fx} 165.8 L {fx+1.6} 167.0 L {fx-0.4} 167.0 Z",
                     fill="#F2EEDC", clip_path=ksp))
    for fx in (48.5, 52, 55.5):
        e.append(_el("path", d=f"M {fx} 166.4 L {fx+1.4} 167.4 L {fx-0.4} 167.4 Z",
                     fill="#F2EEDC", clip_path=ksp))
    # kol (baskıda)
    e.append(_el("path", d="M 84.5 147.5 Q 89 150 92 153", fill="none",
                 stroke="#6B4CA0", stroke_width=3.2, stroke_linecap="round",
                 clip_path=ksp))
    e.append(_el("path", d="M 84.5 147.5 Q 89 150 92 153", fill="none",
                 stroke=CIZGI, stroke_width=1.0, stroke_linecap="round",
                 clip_path=ksp))
    for cx_, cy_ in [(93.6, 154.0), (92.4, 155.6)]:
        e.append(_el("path", d=f"M {cx_-1.2} {cy_-1.2} L {cx_+0.8} {cy_+0.6} "
                              f"L {cx_-1.6} {cy_+0.4} Z", fill="#F2EEDC",
                     clip_path=ksp))
    # timsah çenesi + dişler
    e.append(_el("path", d="M 92 151.4 Q 106 154.6 119.6 154.4", fill="none",
                 stroke=CIZGI, stroke_width=1.15, stroke_linecap="round"))
    disler(e, [(97, 152.4), (101.5, 153.4), (106, 154.0), (110.5, 154.4),
               (115, 154.5)], 1.6, True, ksp)
    disler(e, [(99, 151.4), (103.5, 152.4), (108, 153.0), (112.5, 153.4)], 1.4,
           False, ksp)
    e.append(_el("path", d="M 104 147 Q 112 147.6 118.6 150.6", fill="none",
                 stroke="#6B4CA0", stroke_width=0.8, opacity=0.85, clip_path=ksp))
    goz(e, 98, 145.4, 2.9, (0.26, 0.06))
    e.append(_el("ellipse", cx=117.4, cy=150.6, rx=0.8, ry=0.55, fill=CIZGI,
                 opacity=0.8))
    hacim(e, "kspino", sp, 0.10)

    # ---------- VELOSİRAPTOR (turuncu, çizgili)
    v = P["velosiraptor"]
    kv = _klip(e, "kvelo", v)
    e.append(_el("path", d=yol_svg(v), fill="url(#velog)"))
    # krem karın
    e.append(_el("path", d="M 234 153 Q 248 161 262 151 L 264 174 L 232 174 Z",
                 fill="#F5E3C0", opacity=0.9, clip_path=kv))
    e.append(_el("path", d="M 234 153 Q 248 161 262 151", fill="none", stroke=CIZGI,
                 stroke_width=0.85, opacity=0.7, clip_path=kv))
    # sırt çizgileri (kaplan deseni)
    for x0, y0 in [(238, 148), (243, 145), (248, 144), (253, 145), (257, 143),
                   (232, 152), (228, 156)]:
        e.append(_el("path", d=f"M {x0} {y0} q 1.6 3.0 0.4 5.6", stroke="#B85F0E",
                     stroke_width=1.5, fill="none", opacity=0.65,
                     stroke_linecap="round", clip_path=kv))
    # kuyruk çizgisi
    e.append(_el("path", d="M 236 154 Q 226 159 217 161", fill="none", stroke="#B85F0E",
                 stroke_width=0.9, opacity=0.8, clip_path=kv))
    # bacak ayrımı (kaynaşan bacakları baskıda ayır) + orak pençe
    e.append(_el("path", d="M 241 155 Q 238 160 238 168", fill="none", stroke="#B85F0E",
                 stroke_width=2.4, opacity=0.95, clip_path=kv))
    e.append(_el("path", d="M 241 155 Q 238 160 238 168", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.7, clip_path=kv))
    for fx in (247, 251, 255):
        e.append(_el("path", d=f"M {fx} 168.6 L {fx+1.5} 169.7 L {fx-0.4} 169.7 Z",
                     fill="#F2EEDC", clip_path=kv))
    for fx in (230.5, 234, 237):
        e.append(_el("path", d=f"M {fx} 167.2 L {fx+1.3} 168.2 L {fx-0.4} 168.2 Z",
                     fill="#F2EEDC", clip_path=kv))
    e.append(_el("path", d="M 245 161.5 Q 242.6 163.6 243.6 165.8", fill="none",
                 stroke="#F2EEDC", stroke_width=1.4, stroke_linecap="round",
                 clip_path=kv))
    # kol (baskıda)
    e.append(_el("path", d="M 253 148.5 Q 257 151 260 154.5", fill="none",
                 stroke="#C87014", stroke_width=3.0, stroke_linecap="round",
                 clip_path=kv))
    e.append(_el("path", d="M 253 148.5 Q 257 151 260 154.5", fill="none",
                 stroke=CIZGI, stroke_width=0.95, stroke_linecap="round",
                 clip_path=kv))
    for cx_, cy_ in [(261.4, 155.6), (260.2, 157.2)]:
        e.append(_el("path", d=f"M {cx_-1.1} {cy_-1.1} L {cx_+0.7} {cy_+0.6} "
                              f"L {cx_-1.5} {cy_+0.4} Z", fill="#F2EEDC",
                     clip_path=kv))
    # çene ayrım hattı + dişler
    e.append(_el("path", d="M 258.5 139.2 Q 266.5 140.8 275 141.6", fill="none",
                 stroke=CIZGI, stroke_width=1.05, stroke_linecap="round",
                 clip_path=kv))
    disler(e, [(262, 140.0), (265.8, 140.8), (269.4, 141.3), (273, 141.6)], 1.4,
           True, kv)
    e.append(_el("path", d="M 261.5 133.4 Q 269 135.4 276.5 139.2", fill="none",
                 stroke="#B85F0E", stroke_width=0.8, opacity=0.85, clip_path=kv))
    goz(e, 262, 133.4, 2.7, (0.3, 0.06))
    e.append(_el("ellipse", cx=274.4, cy=139.0, rx=0.7, ry=0.5, fill=CIZGI,
                 opacity=0.8))
    hacim(e, "kvelo", v, 0.10)

    return e

# ---------------------------------------------------------------- SVG belgeleri
def svg_belge(w_mm, h_mm, icerik):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w_mm}mm" height="{h_mm}mm" '
            f'viewBox="0 0 {w_mm} {h_mm}">' + "\n".join(icerik) + "</svg>")


def uret_baski_svg(yuva_goster=False):
    icerik = ([f'<g transform="translate({BLEED},{BLEED})">']
              + sahne_svg(yuva_goster) + ["</g>"])
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, icerik)


def uret_kalip_svg():
    icerik = [_el("path", d=yol_svg(cerceve_poly()), fill="none", stroke="#FF0000",
                  stroke_width=0.25)]
    icerik.append(_el("text", x=6, y=177.2,
                      icerik="DİNOZORLAR PUZZLE 320x180 – UV KALIP (1:1)",
                      fill="#888888", font_size="3", font_family="sans-serif"))
    return svg_belge(W, H, icerik)


def uret_golge_svg():
    ic = [f'<g transform="translate({BLEED},{BLEED})">']
    ic.append(_el("rect", x=-6, y=-6, width=W + 12, height=H + 12, fill="#DCEEF8"))
    ic.append(_el("path", d="M -6 104 Q 60 96 120 103 Q 190 111 250 101 Q 292 95 326 104 "
                            "L 326 186 L -6 186 Z", fill="#E4EFCF"))
    for ad, poly, _ in PARCALAR:
        for iceri, op in ((-0.15, 0.4), (-0.55, 1.0)):
            g = poly.buffer(iceri, quad_segs=8)
            if g.is_empty:
                continue
            geoms = g.geoms if g.geom_type == "MultiPolygon" else [g]
            for gg in geoms:
                ic.append(_el("path", d=yol_svg(gg), fill="#54677A", opacity=f"{op}"))
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

    msp.add_text("UST KATMAN - dinozorlar + cepler (320x180)",
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
