# -*- coding: utf-8 -*-
"""
İki katmanlı "Deniz Canlıları" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Çıktılar (cikti/):
  1. deniz_canlilari_uv_kalip.pdf   – UV hizalama kalıbı (yalnız dış çerçeve, 1:1)
  2. deniz_canlilari_uv_baski.pdf   – ÜST katman baskısı, 2 mm taşmalı (324x184)
  3. deniz_canlilari_alt_golge.pdf  – ALT katman gölge baskısı (324x184)
  4. deniz_canlilari_lazer_kesim.dxf – Lazer: ÜST (cepli) + ALT (düz) panolar

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
TEMA = "deniz_canlilari"

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

# ---------------------------------------------------------------- canlı konturları
def kontur_yunus():
    return birlesim([
        elips(58, 29, 30, 12),                                  # gövde
        elips(78, 28, 13, 10),                                  # baş/melon
        kapsul(89, 31, 95.5, 32.2, 3.0),                        # burun
        kapsul(33, 29, 25, 28, 4.2),                            # kuyruk sapı
        cokgen((26, 26), (13.5, 16), (17.5, 29)),               # kuyruk üst lobu
        cokgen((26, 30), (13.5, 40), (17.5, 27.5)),             # kuyruk alt lobu
        cokgen((54, 12.5), (64, 15), (57, 21.5), (50, 19)),     # sırt yüzgeci
        elips(62, 41.5, 8, 4.5, 35),                            # göğüs yüzgeci
    ], kapa=1.8)


def kontur_denizanasi():
    parca = [elips(149, 25, 20.5, 16.5), kutu(130, 25, 38, 9.5, 3)]
    for i in range(5):
        parca.append(daire(133.5 + i * 7.8, 35.5, 4.4))         # etek fistoları
    parca += [
        kapsul(137.5, 38, 132.5, 46.5, 2.7),                    # sol tentakül
        kapsul(148.5, 39, 148.5, 48.5, 2.7),                    # orta tentakül
        kapsul(159.5, 38, 164.5, 46.5, 2.7),                    # sağ tentakül
    ]
    return birlesim(parca, kapa=1.6)


def kontur_denizati():
    return s_tasi(birlesim([
        kapsul(23, 74.5, 31, 75.5, 3.2),                        # burun
        elips(36, 79, 8.5, 7.5),                                # baş
        cokgen((33, 68), (38, 64), (41, 69), (36, 72)),         # taç
        elips(41, 93, 10.5, 14.5, 8),                           # gövde
        cokgen((49, 82), (56, 88), (52, 99), (46, 93)),         # sırt yüzgeci
        kapsul(43, 104, 39, 111, 4.6),                          # kuyruk üst
        kapsul(39, 111, 45, 115.5, 4.0),                        # kuyruk kıvrım
        daire(47.5, 112.5, 5.2),                                # kuyruk lülesi
    ], kapa=1.6), 0, -2.5)


def kontur_kaplumbaga():
    return birlesim([
        elips(140, 84, 33, 21.5),                               # kabuk
        elips(102, 79, 10, 8),                                  # baş
        kapsul(109, 81, 117, 83, 6),                            # boyun
        elips(125, 105, 14, 6.5, 32),                           # ön yüzgeç (alt)
        elips(123, 65.5, 11, 5, -25),                           # ön yüzgeç (üst)
        elips(169, 100.5, 10, 5.5, 24),                         # arka yüzgeç
    ], kapa=1.8)


def kontur_balik():
    return birlesim([
        elips(249, 86, 25, 15.5),                               # gövde
        cokgen((270, 86), (284, 71), (284, 101)),               # kuyruk
        cokgen((237, 69.5), (256, 68), (251, 77), (239, 77)),   # sırt yüzgeci
        elips(244, 99.5, 7, 4, 18),                             # karın yüzgeci
        elips(259, 97.5, 6, 3.6, -12),                          # anal yüzgeç
        daire(225.5, 86, 3.4),                                  # dudaklar
    ], kapa=1.6)


def kontur_ahtapot():
    return s_tasi(birlesim([
        elips(58, 141, 21.5, 17.5),                             # kafa
        elips(58, 152, 24, 10),                                 # gövde eteği
        kapsul(38, 152, 29, 161.5, 4.4), daire(27.5, 163, 4.6),  # kol 1
        kapsul(49, 157, 45.5, 165.5, 4.2), daire(45, 166, 4.6),  # kol 2
        kapsul(67, 157, 70.5, 165.5, 4.2), daire(71, 166, 4.6),  # kol 3
        kapsul(78, 152, 87, 161.5, 4.4), daire(88.5, 163, 4.6),  # kol 4
    ], kapa=1.8), 0, 1.5)


def kontur_yengec():
    return birlesim([
        elips(163, 150, 23.5, 14.5),                            # kabuk
        daire(137, 138.5, 6.8),                                 # sol kıskaç
        kapsul(143, 143, 150, 146.5, 4.8),                      # sol kol
        cokgen((133, 131.5), (140, 134), (136, 140)),           # sol kıskaç ağzı
        daire(189, 138.5, 6.8),                                 # sağ kıskaç
        kapsul(183, 143, 176, 146.5, 4.8),                      # sağ kol
        cokgen((193, 131.5), (186, 134), (190, 140)),           # sağ kıskaç ağzı
        kutu(155.6, 131, 4.2, 9, 2), daire(157.7, 130.5, 3.1),  # sol göz sapı
        kutu(166.2, 131, 4.2, 9, 2), daire(168.3, 130.5, 3.1),  # sağ göz sapı
        kapsul(146, 161, 139.5, 167.5, 2.6),                    # bacaklar
        kapsul(155, 163.5, 151, 168.5, 2.5),
        kapsul(171, 163.5, 175, 168.5, 2.5),
        kapsul(180, 161, 186.5, 167.5, 2.6),
    ], kapa=1.6)


def kontur_denizyildizi():
    kollar = []
    for i in range(5):
        a = math.radians(-90 + i * 72)
        ux, uy = math.cos(a), math.sin(a)
        kollar.append(kapsul(261, 149, 261 + 19 * ux, 149 + 19 * uy, 7.2))
    return birlesim(kollar, kapa=2.6)


PARCALAR = [(ad, f(), sinif) for ad, f, sinif in [
    ("yunus",        kontur_yunus,        "yuzey"),
    ("denizanasi",   kontur_denizanasi,   "yuzey"),
    ("denizati",     kontur_denizati,     "orta"),
    ("kaplumbaga",   kontur_kaplumbaga,   "orta"),
    ("balik",        kontur_balik,        "orta"),
    ("ahtapot",      kontur_ahtapot,      "taban"),
    ("yengec",       kontur_yengec,       "taban"),
    ("denizyildizi", kontur_denizyildizi, "taban"),
]]

# ---------------------------------------------------------------- parmak yuvaları
YUVA_R = 5.5
YUVA_KONUM = {                    # hedef nokta; kontura otomatik oturtulur
    "yunus":        (44, 44),     # karın sol-altı
    "denizanasi":   (174, 24),    # sağ
    "denizati":     (14, 88),     # sol
    "kaplumbaga":   (104, 60),    # üst-sol
    "balik":        (250, 62),    # üst
    "ahtapot":      (18, 146),    # sol
    "yengec":       (163, 174),   # alt
    "denizyildizi": (294, 144),   # sağ
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
    "yunus":        ("YUNUS", "DOLPHIN", 61, 57.4, 4.0, 2.4),
    "denizanasi":   ("DENİZANASI", "JELLYFISH", 149, 57.8, 4.0, 2.4),
    "denizati":     ("DENİZATI", "SEAHORSE", 37, 125.6, 3.2, 2.0),
    "kaplumbaga":   ("KAPLUMBAĞA", "SEA TURTLE", 137, 117.6, 4.0, 2.4),
    "balik":        ("BALIK", "FISH", 251, 111.4, 4.0, 2.4),
    "ahtapot":      ("AHTAPOT", "OCTOPUS", 58, 176.0, 3.2, 2.0),
    "yengec":       ("YENGEÇ", "CRAB", 163, 126.6, 3.2, 2.0),
    "denizyildizi": ("DENİZYILDIZI", "STARFISH", 261, 176.0, 3.2, 2.0),
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
    g.append(_lin("su", 0, -6, 0, 186, [(0, "#8FDCEC"), (0.3, "#57B6DA"),
                                        (0.65, "#2F88BE"), (1, "#1B5E94")]))
    g.append(_lin("kum", 0, 156, 0, 184, [(0, "#EFDFAF"), (0.5, "#E3CD94"),
                                          (1, "#D2B577")]))
    g.append(_rad("gunes_su", 30, 0, 55, [(0, "#FFFBE0", 0.75), (0.5, "#F2F7D8", 0.3),
                                          (1, "#F2F7D8", 0)]))
    g.append(_lin("yunusg", 0, 9, 0, 50, [(0, "#8FB2C9"), (0.45, "#5F8AA8"),
                                          (1, "#3E637F")]))
    g.append(_rad("anasig", 149, 22, 32, [(0, "#F7CBDF"), (0.55, "#E39FC6"),
                                          (1, "#BC74A4")]))
    g.append(_lin("atig", 0, 62, 0, 118, [(0, "#FFCB72"), (0.5, "#F29A3E"),
                                          (1, "#D3752B")]))
    g.append(_lin("kabukg", 0, 60, 0, 108, [(0, "#93B765"), (0.5, "#64934B"),
                                            (1, "#426F36")]))
    g.append(_lin("baligg", 0, 66, 0, 106, [(0, "#FFA352"), (0.5, "#F2712E"),
                                            (1, "#D6521E")]))
    g.append(_lin("ahtapotg", 0, 120, 0, 172, [(0, "#BE87D8"), (0.5, "#9B5FB9"),
                                               (1, "#744093")]))
    g.append(_lin("yengecg", 0, 126, 0, 172, [(0, "#FF8663"), (0.5, "#E94E33"),
                                              (1, "#B83423")]))
    g.append(_rad("yildizg", 261, 144, 32, [(0, "#FFCB72"), (0.55, "#F29A3E"),
                                            (1, "#D9752B")]))
    return "<defs>" + "".join(g) + "</defs>"


def _klip(e, ad, poly):
    e.append(f'<clipPath id="{ad}"><path d="{yol_svg(poly)}"/></clipPath>')
    return f"url(#{ad})"


def zemin_golgesi(e, cx, cy, rx):
    for f_rx, ry, op in [(1.0, 2.2, 0.10), (0.75, 1.6, 0.10), (0.5, 1.1, 0.12)]:
        e.append(_el("ellipse", cx=cx, cy=cy, rx=rx * f_rx, ry=ry,
                     fill="#0A2438", opacity=f"{op}"))


def hacim(e, klip, poly, guc=0.12):
    x0, y0, x1, y1 = poly.bounds
    w, h = x1 - x0, y1 - y0
    e.append(_el("ellipse", cx=x0 + w * 0.4, cy=y0 + h * 0.18, rx=w * 0.6, ry=h * 0.32,
                 fill="#FFFFFF", opacity=f"{guc}", clip_path=f"url(#{klip})"))
    e.append(_el("ellipse", cx=x0 + w * 0.55, cy=y1 + h * 0.02, rx=w * 0.72, ry=h * 0.26,
                 fill="#0A1E30", opacity=f"{guc * 0.8}", clip_path=f"url(#{klip})"))


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
                 fill="#0A2438", opacity=0.2))
    e.append(_el("rect", x=x0, y=y0, width=pw, height=ph, rx=1.6,
                 fill="#FCF9F1", opacity=0.96))
    e.append(_el("rect", x=x0, y=y0, width=pw, height=ph, rx=1.6, fill="none",
                 stroke="#26343F", stroke_width=0.3, opacity=0.55))
    b64 = base64.b64encode(veri).decode()
    e.append(f'<image x="{x0 + 2.5:.2f}" y="{y0 + 1.6:.2f}" width="{lw:.2f}" '
             f'height="{lh:.2f}" xlink:href="data:image/png;base64,{b64}"/>')


def etiket(e, x, y, tr, en, boyut=3.0, pad_y=2.2):
    metin = f"{tr} • {en}"
    w = len(metin) * boyut * 0.70 + (len(metin) - 1) * 0.35 + 6.0
    h = boyut + pad_y
    cy = y - 0.28 * boyut
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2 + 0.5, width=w, height=h, rx=1.4,
                 fill="#0A2438", opacity=0.2))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.4,
                 fill="#FCF9F1", opacity=0.96))
    e.append(_el("rect", x=x - w / 2, y=cy - h / 2, width=w, height=h, rx=1.4,
                 fill="none", stroke="#26343F", stroke_width=0.3, opacity=0.55))
    e.append(_el("text", x=x, y=y, icerik=metin, fill="#22303B", font_size=boyut,
                 font_family="sans-serif", font_weight="bold", text_anchor="middle",
                 letter_spacing="0.35"))

# ---------------------------------------------------------------- dekor
def kabarcik(e, x, y, r, op=0.8):
    e.append(_el("circle", cx=x, cy=y, r=r, fill="#FFFFFF", opacity=0.10 * op))
    e.append(_el("circle", cx=x, cy=y, r=r, fill="none", stroke="#E8F8FE",
                 stroke_width=r * 0.18, opacity=0.55 * op))
    e.append(_el("circle", cx=x - r * 0.35, cy=y - r * 0.4, r=r * 0.24, fill="#FFFFFF",
                 opacity=0.7 * op))


def minik_balik(e, x, y, s=1.0, yon=1):
    e.append(_el("ellipse", cx=x, cy=y, rx=3.4 * s, ry=1.7 * s, fill="#1E4E74",
                 opacity=0.55))
    e.append(_el("path", d=f"M {x + 3.0*s*yon} {y} L {x + 5.2*s*yon} {y - 1.6*s} "
                           f"L {x + 5.2*s*yon} {y + 1.6*s} Z", fill="#1E4E74",
                 opacity=0.55))
    e.append(_el("circle", cx=x - 1.6 * s * yon, cy=y - 0.3 * s, r=0.3 * s,
                 fill="#DFF2FB", opacity=0.8))


def yosun(e, x, taban, boy, s=1.0, renk="#3E8F5A"):
    for dx, egim in [(0, 1), (3.5 * s, -1)]:
        e.append(_el("path",
                     d=f"M {x+dx} {taban} C {x+dx+4*s*egim} {taban-boy*0.3} "
                       f"{x+dx-3*s*egim} {taban-boy*0.62} {x+dx+2.5*s*egim} {taban-boy} "
                       f"C {x+dx+4.5*s*egim} {taban-boy*0.66} {x+dx-2*s*egim} "
                       f"{taban-boy*0.34} {x+dx-1.2*s} {taban}",
                     fill=renk, opacity=0.9))
    e.append(_el("path", d=f"M {x+1.2*s} {taban} C {x+3*s} {taban-boy*0.4} "
                           f"{x-1*s} {taban-boy*0.7} {x+1.5*s} {taban-boy*0.92}",
                 fill="none", stroke="#2E6E44", stroke_width=0.7 * s, opacity=0.8))


def mercan(e, x, taban, s=1.0):
    for dx, dy, r in [(0, -3, 3.2), (-3.4, -6.5, 2.7), (3.2, -7, 2.9), (-0.4, -9.5, 2.5),
                      (5.8, -3.5, 2.3), (-5.6, -3, 2.2)]:
        e.append(_el("circle", cx=x + dx * s, cy=taban + dy * s, r=r * s, fill="#E8798A"))
        e.append(_el("circle", cx=x + dx * s - r * s * 0.25, cy=taban + dy * s - r * s * 0.3,
                     r=r * s * 0.35, fill="#F2A3B0", opacity=0.9))
    e.append(_el("ellipse", cx=x, cy=taban + 0.4, rx=7.5 * s, ry=1.2 * s, fill="#B98E52",
                 opacity=0.4))


def kaya(e, x, taban, w, h, renk="#5E7A88"):
    e.append(_el("path", d=f"M {x-w/2} {taban} Q {x-w/2} {taban-h} {x-w*0.12} {taban-h} "
                           f"Q {x+w/2} {taban-h*0.96} {x+w/2} {taban} Z", fill=renk))
    e.append(_el("path", d=f"M {x-w*0.34} {taban-h*0.88} Q {x-w*0.05} {taban-h*1.02} "
                           f"{x+w*0.3} {taban-h*0.82}", fill="none", stroke="#7E98A6",
                 stroke_width=0.8, opacity=0.7))


def deniz_kabugu(e, x, y, s=1.0):
    e.append(_el("path", d=f"M {x-3.2*s} {y} A 3.2 3.2 0 0 1 {x+3.2*s} {y} Z",
                 fill="#F2E3C2", transform=f"rotate(180 {x} {y})"))
    e.append(_el("path", d=f"M {x-3.2*s} {y} A 3.2 3.2 0 0 1 {x+3.2*s} {y} Z",
                 fill="#F2E3C2"))
    for a in (-55, -20, 20, 55):
        ar = math.radians(a - 90)
        e.append(_el("line", x1=x, y1=y, x2=x + 3.0 * s * math.cos(ar),
                     y2=y + 3.0 * s * math.sin(ar), stroke="#D8BE92",
                     stroke_width=0.5 * s))

# ---------------------------------------------------------------- sahne
def sahne_svg(yuva_goster=False):
    rnd = random.Random(53)
    e = [tanimlar()]
    # su kütlesi + yüzey + güneş ışıması
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=H + 12, fill="url(#su)"))
    e.append(_el("circle", cx=30, cy=0, r=55, fill="url(#gunes_su)"))
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=9.5, fill="#C9F0F8",
                 opacity=0.55))
    for wx in range(-6, 326, 22):
        e.append(_el("path", d=f"M {wx} 3.6 q 5.5 -2.4 11 0 q 5.5 2.4 11 0",
                     fill="none", stroke="#E8FAFE", stroke_width=1.3, opacity=0.7))
    # ışık hüzmeleri (tanrı ışınları)
    for x0, x1t, geno, genb in [(36, 66, 9, 26), (96, 150, 12, 34), (208, 190, 10, 30)]:
        e.append(_el("path", d=f"M {x0-geno} 4 L {x0+geno} 4 L {x1t+genb} 96 "
                               f"L {x1t-genb} 96 Z", fill="#EAF9E8", opacity=0.05))
    # arka plan küçük balık sürüleri + kabarcıklar
    for fx, fy, s, yon in [(272, 28, 1.0, -1), (282, 35, 0.85, -1), (271, 41, 0.8, -1),
                           (290, 30, 0.7, -1), (72, 92, 0.9, 1), (82, 98, 0.75, 1),
                           (70, 103, 0.7, 1), (204, 34, 0.8, 1), (213, 40, 0.65, 1)]:
        minik_balik(e, fx, fy, s, yon)
    for bx, by, br in [(108, 20, 1.6), (112, 12, 1.1), (104, 8, 0.8), (186, 56, 1.4),
                       (190, 48, 1.0), (300, 96, 1.7), (305, 87, 1.2), (298, 78, 0.9),
                       (12, 128, 1.4), (17, 119, 1.0), (206, 120, 1.3), (210, 112, 0.9),
                       (95, 130, 1.1), (222, 68, 1.0)]:
        kabarcik(e, bx, by, br)
    # --- deniz tabanı: kum + dokular
    e.append(_el("path", d=f"M -6 166 Q 40 158 90 163 Q 150 168 210 162 Q 265 157 326 164 "
                           f"L 326 186 L -6 186 Z", fill="url(#kum)"))
    for rx_, ry_ in [(60, 171), (140, 174), (250, 172), (300, 176), (20, 176)]:
        e.append(_el("path", d=f"M {rx_-7} {ry_} q 7 -2.2 14 0", fill="none",
                     stroke="#C9AC6E", stroke_width=0.8, opacity=0.7))
    for _ in range(46):
        px, py = rnd.uniform(-4, 322), rnd.uniform(163, 179)
        e.append(_el("circle", cx=f"{px:.1f}", cy=f"{py:.1f}",
                     r=f"{rnd.uniform(0.15, 0.4):.2f}", fill="#B7975C",
                     opacity=f"{rnd.uniform(0.25, 0.5):.2f}"))
    # taban dekoru (parça alanlarının dışında)
    kaya(e, 116, 168, 13, 7)
    kaya(e, 124, 169.5, 9, 4.8, "#54707E")
    yosun(e, 8, 176, 26, 1.0)
    yosun(e, 214, 172, 34, 1.1)
    yosun(e, 222, 174, 24, 0.85, "#4AA968")
    mercan(e, 203, 176, 0.95)
    deniz_kabugu(e, 104, 175.5, 1.0)
    deniz_kabugu(e, 298, 173, 0.85)
    kaya(e, 306, 174, 11, 5.5)
    # --- canlı zemin gölgeleri (taban canlıları)
    zemin_golgesi(e, 58, 171, 28)
    zemin_golgesi(e, 163, 170.5, 26)
    zemin_golgesi(e, 261, 172.5, 17)
    # --- canlılar
    e += canli_detaylari()
    # --- parça dış çizgileri
    for _, poly, _ in PARCALAR:
        e.append(_el("path", d=yol_svg(poly), fill="none", stroke="#173042",
                     stroke_width=0.7, stroke_linejoin="round", opacity=0.8))
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
    e = []
    P = {ad: poly for ad, poly, _ in PARCALAR}

    # ---------- YUNUS
    y = P["yunus"]
    ky = _klip(e, "kyunus", y)
    e.append(_el("path", d=yol_svg(y), fill="url(#yunusg)"))
    # açık karın (gövde kavisini izler)
    e.append(_el("path", d="M 24 31.5 Q 58 45 93 32.5 L 93 50 L 24 50 Z",
                 fill="#DCE9F2", clip_path=ky))
    e.append(_el("path", d="M 24 31.5 Q 58 45 93 32.5", fill="none", stroke="#4A7089",
                 stroke_width=0.5, opacity=0.6, clip_path=ky))
    # yan süpürme (açık gri şerit)
    e.append(_el("path", d="M 30 27 Q 58 36 88 29.5 Q 58 40 30 31 Z", fill="#9FBDD1",
                 opacity=0.5, clip_path=ky))
    # yüzgeç gölgeleri
    e.append(_el("path", d="M 54 12.5 L 64 15 L 57 21.5 L 50 19 Z", fill="#3E637F",
                 clip_path=ky, opacity=0.85))
    e.append(_el("ellipse", cx=62, cy=41.5, rx=8, ry=4.5, fill="#33566E", opacity=0.8,
                 transform="rotate(35 62 41.5)", clip_path=ky))
    e.append(_el("path", d="M 26 26 L 15 17 M 26 30 L 15 39", stroke="#33566E",
                 stroke_width=1.6, opacity=0.5, fill="none", clip_path=ky))
    # sırt parlaması + hava deliği
    e.append(_el("path", d="M 34 22 C 52 15.5 74 16 88 24", fill="none",
                 stroke="#C9DEEB", stroke_width=1.6, opacity=0.55, clip_path=ky))
    e.append(_el("ellipse", cx=71, cy=18.4, rx=1.2, ry=0.55, fill="#2E4A5E",
                 opacity=0.9))
    # göz + gülümseyen ağız
    e.append(_el("circle", cx=80, cy=29.5, r=2.0, fill="#12242F"))
    e.append(_el("circle", cx=80.6, cy=28.9, r=0.65, fill="#FFFFFF", opacity=0.9))
    e.append(_el("path", d="M 84.5 33.6 Q 89.5 36.2 94.5 34.2", fill="none",
                 stroke="#12242F", stroke_width=0.85, opacity=0.85))
    hacim(e, "kyunus", y, 0.11)

    # ---------- DENİZANASI
    a = P["denizanasi"]
    ka = _klip(e, "kanasi", a)
    e.append(_el("path", d=yol_svg(a), fill="url(#anasig)"))
    # iç ışıma + kubbe çizgileri
    e.append(_el("ellipse", cx=147, cy=20, rx=13, ry=8.5, fill="#FBE3EE", opacity=0.75,
                 clip_path=ka))
    for dx in (-12, -4, 4, 12):
        e.append(_el("path", d=f"M {149+dx} 11 C {149+dx*1.25} 18 {149+dx*1.25} 26 "
                               f"{149+dx*1.05} 32", fill="none", stroke="#C481AC",
                     stroke_width=0.6, opacity=0.7, clip_path=ka))
    # etek fisto çizgisi
    e.append(_el("path", d="M 130 33.5 Q 133.5 38.5 137.5 34.5 Q 141 39.5 145.2 34.8 "
                           "Q 149 39.8 153 34.8 Q 156.8 39.5 160.5 34.5 Q 164.5 38.5 168 33.5",
                 fill="none", stroke="#A85E90", stroke_width=0.8, opacity=0.85,
                 clip_path=ka))
    # tentakül şeritleri + benekler
    for tx1, ty1, tx2, ty2 in [(137.5, 38, 132.5, 49), (148.5, 39, 148.5, 51),
                               (159.5, 38, 164.5, 49)]:
        e.append(_el("line", x1=tx1, y1=ty1, x2=tx2, y2=ty2, stroke="#A85E90",
                     stroke_width=1.1, opacity=0.8, clip_path=ka))
    for sx, sy in [(139, 22), (150, 17), (158, 24), (144, 28), (154, 29)]:
        e.append(_el("circle", cx=sx, cy=sy, r=1.0, fill="#FFFFFF", opacity=0.55))
    hacim(e, "kanasi", a, 0.10)

    # ---------- DENİZATI (detaylar yerel koordinatta, grupla taşınır)
    d = s_tasi(P["denizati"], 0, 2.5)
    e.append('<g transform="translate(0,-2.5)">')
    kd = _klip(e, "kati", d)
    e.append(_el("path", d=yol_svg(d), fill="url(#atig)"))
    # karın boğumları
    for i in range(6):
        yy = 84 + i * 5.2
        e.append(_el("path", d=f"M 32 {yy} Q 41 {yy+2.8} 50.5 {yy}", fill="none",
                     stroke="#C2681F", stroke_width=0.8, opacity=0.75, clip_path=kd))
    # sırt yüzgeci ışınları
    e.append(_el("path", d="M 47.5 84 Q 55 88 52.5 97.5 Q 47.5 94 46 90 Z",
                 fill="#FFDFA0", clip_path=kd, opacity=0.95))
    e.append(_el("path", d="M 49.5 86 L 52.5 88.5 M 49 89.5 L 52 92 M 48.8 93 L 51.5 95",
                 stroke="#E0912E", stroke_width=0.7, opacity=0.9, fill="none",
                 clip_path=kd))
    # taç + göz + burun
    e.append(_el("path", d="M 33.5 68.5 L 37.5 65.5 L 40 69 L 36.5 71.5 Z",
                 fill="#FFDFA0", clip_path=kd, opacity=0.95))
    e.append(_el("circle", cx=36.5, cy=78, r=2.0, fill="#12242F"))
    e.append(_el("circle", cx=37.1, cy=77.4, r=0.65, fill="#FFFFFF", opacity=0.9))
    e.append(_el("path", d="M 24 73.8 L 31 74.6", stroke="#C2681F", stroke_width=0.8,
                 fill="none", opacity=0.8))
    # kuyruk kıvrım çizgisi
    e.append(_el("path", d="M 42.5 103 C 39.5 108 40 112 45 114.5 C 49.5 116 51.5 113 "
                           "50 110.5", fill="none", stroke="#C2681F", stroke_width=0.9,
                 opacity=0.8, clip_path=kd))
    hacim(e, "kati", d, 0.12)
    e.append("</g>")

    # ---------- KAPLUMBAĞA
    k = P["kaplumbaga"]
    kk = _klip(e, "kkaplumbaga", k)
    e.append(_el("path", d=yol_svg(k), fill="#A8C87A"))
    # kabuk
    e.append(_el("ellipse", cx=140, cy=84, rx=33, ry=21.5, fill="url(#kabukg)"))
    e.append(_el("ellipse", cx=140, cy=84, rx=33, ry=21.5, fill="none", stroke="#2F5228",
                 stroke_width=1.0, opacity=0.8))
    # kabuk plakaları (altıgen deseni)
    e.append(_el("path", d="M 128 68 L 143 66.5 L 152 74 L 149 84 L 134 85.5 L 125 78 Z",
                 fill="none", stroke="#2F5228", stroke_width=0.9, opacity=0.85,
                 clip_path=kk))
    e.append(_el("path", d="M 152 74 L 163 73 L 169 80 L 166 89 L 149 84 M 149 84 "
                           "L 146 95 L 131 96 L 134 85.5 M 125 78 L 114 80 L 111 88 "
                           "L 117 94 L 131 96 M 143 66.5 L 145 63 M 163 73 L 167 70",
                 fill="none", stroke="#2F5228", stroke_width=0.8, opacity=0.75,
                 clip_path=kk))
    # kabuk kenar bordürü
    e.append(_el("path", d="M 108 88 A 33 21.5 0 0 0 172 88 L 172 92 A 33 21.5 0 0 1 "
                           "108 92 Z", fill="#E8D8A0", clip_path=kk, opacity=0.9))
    # baş + benekler + göz + ağız
    for sx, sy, sr in [(99, 75, 1.0), (104, 73.5, 0.8), (101, 80, 0.8), (106, 78, 0.7),
                       (120, 62, 0.8), (126, 64.5, 0.7), (124, 107, 0.8), (130, 109, 0.7),
                       (168, 99, 0.8), (172, 102, 0.65)]:
        e.append(_el("circle", cx=sx, cy=sy, r=sr, fill="#5E8A3C", opacity=0.85))
    e.append(_el("circle", cx=97.5, cy=76.5, r=1.9, fill="#12242F"))
    e.append(_el("circle", cx=98.1, cy=75.9, r=0.6, fill="#FFFFFF", opacity=0.9))
    e.append(_el("path", d="M 93.5 80.5 Q 96.5 82.5 100 81.5", fill="none",
                 stroke="#12242F", stroke_width=0.7, opacity=0.8))
    hacim(e, "kkaplumbaga", k, 0.11)

    # ---------- BALIK (palyaço)
    b = P["balik"]
    kb = _klip(e, "kbalik", b)
    e.append(_el("path", d=yol_svg(b), fill="url(#baligg)"))
    # beyaz bantlar (siyah kenarlı)
    for bx, gen in [(237, 7.5), (255, 8.5)]:
        e.append(_el("path", d=f"M {bx-gen/2} 66 C {bx-gen/2-1.5} 80 {bx-gen/2-1.5} 92 "
                               f"{bx-gen/2} 104 L {bx+gen/2} 104 C {bx+gen/2+1.5} 92 "
                               f"{bx+gen/2+1.5} 80 {bx+gen/2} 66 Z", fill="#F7F3EA",
                     clip_path=kb))
        for kx in (bx - gen / 2, bx + gen / 2):
            e.append(_el("path", d=f"M {kx} 66 C {kx-1.5} 80 {kx-1.5} 92 {kx} 104",
                         fill="none", stroke="#1E2A33", stroke_width=0.8, opacity=0.85,
                         clip_path=kb))
    # kuyruk/yüzgeç kenarları
    e.append(_el("path", d="M 270 86 L 284 71 L 284 101 Z", fill="none",
                 stroke="#1E2A33", stroke_width=1.2, opacity=0.75, clip_path=kb))
    e.append(_el("path", d="M 276 78 L 276 94", fill="none", stroke="#C2531E",
                 stroke_width=0.8, opacity=0.7, clip_path=kb))
    e.append(_el("path", d="M 237 69.5 L 256 68 L 251 77 L 239 77 Z", fill="none",
                 stroke="#1E2A33", stroke_width=1.0, opacity=0.7, clip_path=kb))
    # göz + dudak + parlama
    e.append(_el("circle", cx=232, cy=81, r=2.6, fill="#F7F3EA"))
    e.append(_el("circle", cx=232.4, cy=81.3, r=1.7, fill="#12242F"))
    e.append(_el("circle", cx=233, cy=80.6, r=0.55, fill="#FFFFFF", opacity=0.9))
    e.append(_el("path", d="M 223.5 84.5 Q 225.5 86.5 228 85.8", fill="none",
                 stroke="#8C3A16", stroke_width=0.7, opacity=0.8))
    e.append(_el("path", d="M 234 72 C 244 69.5 256 70 264 74", fill="none",
                 stroke="#FFD9A8", stroke_width=1.4, opacity=0.6, clip_path=kb))
    hacim(e, "kbalik", b, 0.12)

    # ---------- AHTAPOT (detaylar yerel koordinatta, grupla taşınır)
    o = s_tasi(P["ahtapot"], 0, -1.5)
    e.append('<g transform="translate(0,1.5)">')
    ko = _klip(e, "kahtapot", o)
    e.append(_el("path", d=yol_svg(o), fill="url(#ahtapotg)"))
    # kol vantuzları
    for vx, vy in [(31, 158), (28, 162.5), (45.5, 161), (45, 165.5), (70.5, 161),
                   (71, 165.5), (85, 158), (88, 162.5), (37, 153.5), (79, 153.5)]:
        e.append(_el("circle", cx=vx, cy=vy, r=1.15, fill="#E3C2EE", opacity=0.9))
        e.append(_el("circle", cx=vx, cy=vy, r=0.5, fill="#B98CD1", opacity=0.9))
    # kafa benekleri
    for sx, sy, sr in [(48, 130, 1.2), (56, 126.5, 1.0), (66, 129, 1.2), (61, 134, 0.8),
                       (51, 137, 0.8)]:
        e.append(_el("circle", cx=sx, cy=sy, r=sr, fill="#D8A8E8", opacity=0.8))
    # gözler + gülümseme + yanaklar
    for gx in (49.5, 66.5):
        e.append(_el("circle", cx=gx, cy=143.5, r=3.6, fill="#F7F3EA"))
        e.append(_el("circle", cx=gx + 0.5, cy=144, r=2.2, fill="#12242F"))
        e.append(_el("circle", cx=gx + 1.2, cy=143.2, r=0.7, fill="#FFFFFF",
                     opacity=0.9))
    e.append(_el("path", d="M 54 150.5 Q 58 153.5 62 150.5", fill="none",
                 stroke="#4E2668", stroke_width=1.0, opacity=0.9))
    e.append(_el("ellipse", cx=43.5, cy=148, rx=2.2, ry=1.3, fill="#E88BB0",
                 opacity=0.55))
    e.append(_el("ellipse", cx=72.5, cy=148, rx=2.2, ry=1.3, fill="#E88BB0",
                 opacity=0.55))
    hacim(e, "kahtapot", o, 0.11)
    e.append("</g>")

    # ---------- YENGEÇ
    yc = P["yengec"]
    kyc = _klip(e, "kyengec", yc)
    e.append(_el("path", d=yol_svg(yc), fill="url(#yengecg)"))
    # kabuk benekleri + alt kenar
    for sx, sy in [(152, 146), (162, 143), (172, 146.5), (157, 151), (168, 151.5)]:
        e.append(_el("circle", cx=sx, cy=sy, r=0.9, fill="#FFB59C", opacity=0.8))
    e.append(_el("path", d="M 141 156 Q 163 163 185 156", fill="none", stroke="#8C2416",
                 stroke_width=0.9, opacity=0.7, clip_path=kyc))
    # kıskaç eklem çizgileri
    e.append(_el("path", d="M 143.5 141.5 L 149.5 145.5 M 182.5 141.5 L 176.5 145.5",
                 stroke="#8C2416", stroke_width=0.8, fill="none", opacity=0.8,
                 clip_path=kyc))
    e.append(_el("path", d="M 133.5 134 L 138 139.5 M 192.5 134 L 188 139.5",
                 stroke="#8C2416", stroke_width=0.7, fill="none", opacity=0.7,
                 clip_path=kyc))
    # gözler
    for gx in (157.7, 168.3):
        e.append(_el("circle", cx=gx, cy=130.5, r=2.2, fill="#F7F3EA"))
        e.append(_el("circle", cx=gx + 0.3, cy=130.8, r=1.3, fill="#12242F"))
        e.append(_el("circle", cx=gx + 0.8, cy=130.2, r=0.45, fill="#FFFFFF",
                     opacity=0.9))
    # ağız
    e.append(_el("path", d="M 159.5 138 Q 163 140.5 166.5 138", fill="none",
                 stroke="#5E170D", stroke_width=0.9, opacity=0.85))
    # bacak eklemleri
    e.append(_el("path", d="M 143 164 L 145.5 162.5 M 153 166 L 154.5 164.5 "
                           "M 173 166 L 171.5 164.5 M 183 164 L 180.5 162.5",
                 stroke="#8C2416", stroke_width=0.7, fill="none", opacity=0.75,
                 clip_path=kyc))
    hacim(e, "kyengec", yc, 0.12)

    # ---------- DENİZYILDIZI
    z = P["denizyildizi"]
    kz = _klip(e, "kyildiz", z)
    e.append(_el("path", d=yol_svg(z), fill="url(#yildizg)"))
    # merkez + kollara akan çizgiler
    e.append(_el("circle", cx=261, cy=148, r=6, fill="#FFDFA0", opacity=0.75))
    for i in range(5):
        aa = math.radians(-90 + i * 72)
        ux, uy = math.cos(aa), math.sin(aa)
        e.append(_el("line", x1=261 + 4 * ux, y1=149 + 4 * uy, x2=261 + 21 * ux,
                     y2=149 + 21 * uy, stroke="#C2681F", stroke_width=0.8,
                     opacity=0.65, clip_path=kz))
        for t in (9, 14, 19):
            px_, py_ = 261 + t * ux, 149 + t * uy
            nx, nyy = -uy, ux
            for tarafi in (-1, 1):
                e.append(_el("circle", cx=px_ + nx * 3.2 * tarafi,
                             cy=py_ + nyy * 3.2 * tarafi, r=0.62, fill="#B85F1E",
                             opacity=0.75))
    # göz + gülümseme (sevimli)
    e.append(_el("circle", cx=257.5, cy=146.5, r=1.5, fill="#12242F"))
    e.append(_el("circle", cx=264.5, cy=146.5, r=1.5, fill="#12242F"))
    e.append(_el("circle", cx=258, cy=146, r=0.5, fill="#FFFFFF", opacity=0.9))
    e.append(_el("circle", cx=265, cy=146, r=0.5, fill="#FFFFFF", opacity=0.9))
    e.append(_el("path", d="M 258 151 Q 261 153.5 264 151", fill="none",
                 stroke="#12242F", stroke_width=0.9, opacity=0.9))
    hacim(e, "kyildiz", z, 0.12)

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
