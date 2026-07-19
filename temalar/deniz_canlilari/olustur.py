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
    "yunus":        ("Yunus", "Dolphin", 61, 57.4, 4.0, 2.4),
    "denizanasi":   ("Denizanası", "Jellyfish", 149, 57.8, 4.0, 2.4),
    "denizati":     ("Denizatı", "Seahorse", 37, 125.6, 3.2, 2.0),
    "kaplumbaga":   ("Kaplumbağa", "Sea Turtle", 137, 117.6, 4.0, 2.4),
    "balik":        ("Balık", "Fish", 251, 111.4, 4.0, 2.4),
    "ahtapot":      ("Ahtapot", "Octopus", 58, 176.0, 3.2, 2.0),
    "yengec":       ("Yengeç", "Crab", 163, 126.6, 3.2, 2.0),
    "denizyildizi": ("Denizyıldızı", "Starfish", 261, 176.0, 3.2, 2.0),
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
    g.append(_lin("su", 0, -6, 0, 186, [(0, "#4FC8F2"), (0.45, "#219FD8"),
                                        (1, "#1173A9")]))
    g.append(_lin("kum", 0, 156, 0, 184, [(0, "#F8DA82"), (1, "#E2B455")]))
    g.append(_rad("gunes_su", 160, -4, 130, [(0, "#EAFBFF", 0.5), (0.6, "#CFF2FC", 0.15),
                                             (1, "#CFF2FC", 0)]))
    g.append(_lin("yunusg", 0, 12, 0, 48, [(0, "#B2BfCB"), (0.55, "#93A3B1"),
                                           (1, "#7E8F9E")]))
    g.append(_rad("anasig", 149, 20, 34, [(0, "#FBD3E8"), (0.6, "#F3A8D0"),
                                          (1, "#DE7EB4")]))
    g.append(_lin("atig", 0, 62, 0, 118, [(0, "#FFC44D"), (0.6, "#F5A11F"),
                                          (1, "#E88A0E")]))
    g.append(_lin("kabukg", 0, 62, 0, 106, [(0, "#BE8129"), (0.6, "#A96D1B"),
                                            (1, "#8F5911")]))
    g.append(_lin("baligg", 0, 66, 0, 106, [(0, "#FFD84A"), (0.55, "#FFC226"),
                                            (1, "#F2A90D")]))
    g.append(_lin("ahtapotg", 0, 120, 0, 174, [(0, "#FF9C3D"), (0.55, "#F57F1B"),
                                               (1, "#E56A0A")]))
    g.append(_lin("yengecg", 0, 126, 0, 172, [(0, "#F6503A"), (0.55, "#E63220"),
                                              (1, "#C81F10")]))
    g.append(_rad("yildizg", 261, 145, 34, [(0, "#FFAF4A"), (0.6, "#F58C22"),
                                            (1, "#E0740F")]))
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
    # ışık hüzmeleri (belirgin, neşeli)
    for x0, tilt, gen in [(46, -8, 7), (98, 4, 10), (152, -3, 8), (208, 7, 11),
                          (262, -5, 7)]:
        e.append(_el("path", d=f"M {x0 - gen} 2 L {x0 + gen} 2 L {x0 + tilt + gen * 2.6} 92 "
                               f"L {x0 + tilt - gen * 2.6} 92 Z", fill="#EAFBFF",
                     opacity=0.10))
    # kabarcık kolonları
    for bx, by, br in [(76, 40, 1.5), (80, 32, 1.1), (74, 25, 0.8),
                       (108, 22, 1.7), (113, 13, 1.2), (105, 7, 0.8),
                       (186, 56, 1.5), (191, 47, 1.0),
                       (222, 68, 1.3), (218, 60, 0.9),
                       (300, 92, 1.8), (305, 82, 1.3), (298, 73, 0.9),
                       (12, 126, 1.5), (17, 117, 1.0), (206, 116, 1.3),
                       (211, 108, 0.9), (95, 129, 1.1), (152, 30, 1.0),
                       (156, 22, 0.7)]:
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
    dalli_mercan(e, 12, 177, 16)
    tup_sunger(e, 15, 177.5, 0.9)
    kaya(e, 6, 178, 10, 5)
    kaya(e, 101, 175.5, 12, 6.5)
    kaya(e, 110, 177, 9, 4.6, "#6B7C8A")
    tarak_kabugu(e, 119, 175.5, 1.1)
    yosun(e, 124, 173, 25, 0.9)
    yosun(e, 205, 172, 33, 1.05)
    yosun(e, 213, 174, 24, 0.85, "#2FAF6E", "#1F8A50")
    spiral_kabuk(e, 225, 176.5, 1.0)
    mini_yildiz(e, 221, 166.5, 4.2)
    dalli_mercan(e, 303, 176, 14, "#F06CA8", "#C74E86")
    kaya(e, 313, 177.5, 10, 5.2)
    yosun(e, 295, 174, 21, 0.8)
    tarak_kabugu(e, 288, 177, 0.9, "#B48CD8", "#8A62B0")
    # --- taban canlıları zemin gölgeleri
    zemin_golgesi(e, 58, 171, 28)
    zemin_golgesi(e, 163, 170.5, 26)
    zemin_golgesi(e, 261, 172.5, 17)
    # --- canlılar
    e += canli_detaylari()
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

# ---------------------------------------------------------------- canlı detayları
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


def canli_detaylari():
    e = []
    P = {ad: poly for ad, poly, _ in PARCALAR}
    CIZGI = "#20262B"

    # ---------- YUNUS
    y = P["yunus"]
    ky = _klip(e, "kyunus", y)
    e.append(_el("path", d=yol_svg(y), fill="url(#yunusg)"))
    # açık karın
    e.append(_el("path", d="M 20 31 Q 58 43.5 96 31.5 L 96 50 L 20 50 Z",
                 fill="#DDE6EC", clip_path=ky))
    e.append(_el("path", d="M 20 31 Q 58 43.5 96 31.5", fill="none", stroke=CIZGI,
                 stroke_width=0.9, opacity=0.85, clip_path=ky))
    # yüzgeç ayrım çizgileri + koyu dolgular
    e.append(_el("path", d="M 54 12.5 L 64 15 L 57 21.5 L 50 19 Z", fill="#7E8F9E",
                 clip_path=ky))
    e.append(_el("path", d="M 50.5 19.5 Q 57 16.5 63 15.5", fill="none", stroke=CIZGI,
                 stroke_width=1.0, clip_path=ky))
    e.append(_el("ellipse", cx=62, cy=41.5, rx=8, ry=4.5, fill="#8DA0AF", opacity=0.95,
                 transform="rotate(35 62 41.5)", clip_path=ky))
    e.append(_el("path", d="M 55.5 38.5 Q 62 38 68 42", fill="none", stroke=CIZGI,
                 stroke_width=1.0, clip_path=ky))
    e.append(_el("path", d="M 26 25.5 Q 24 28 25.5 31.5", fill="none", stroke=CIZGI,
                 stroke_width=1.0, opacity=0.9, clip_path=ky))
    # burun çizgisi + neşeli ağız
    e.append(_el("path", d="M 95.5 32.6 Q 87 36.2 80.5 34.0", fill="none",
                 stroke=CIZGI, stroke_width=1.1, stroke_linecap="round"))
    goz(e, 79.5, 28.6, 3.0)
    # hava deliği
    e.append(_el("ellipse", cx=70.5, cy=18.3, rx=1.2, ry=0.55, fill=CIZGI,
                 opacity=0.85))
    hacim(e, "kyunus", y, 0.09)

    # ---------- DENİZANASI
    a = P["denizanasi"]
    ka = _klip(e, "kanasi", a)
    e.append(_el("path", d=yol_svg(a), fill="url(#anasig)"))
    # iç kubbe ışıltısı
    e.append(_el("ellipse", cx=146, cy=18.5, rx=12, ry=7, fill="#FBD9EB", opacity=0.9,
                 clip_path=ka))
    e.append(_el("ellipse", cx=142.5, cy=15.5, rx=5.5, ry=3, fill="#FFFFFF",
                 opacity=0.75, transform="rotate(-16 142.5 15.5)"))
    # kubbe çizgileri
    for dx in (-11, -4, 4, 11):
        e.append(_el("path", d=f"M {149 + dx * 0.3} 10 C {149 + dx} 17 {149 + dx * 1.15} "
                               f"24 {149 + dx} 31.5", fill="none", stroke="#C2699E",
                     stroke_width=0.7, opacity=0.8, clip_path=ka))
    # etek fisto çizgisi (kalın, sevimli)
    e.append(_el("path", d="M 130 33.5 Q 133.5 38.5 137.5 34.5 Q 141 39.5 145.2 34.8 "
                           "Q 149 39.8 153 34.8 Q 156.8 39.5 160.5 34.5 Q 164.5 38.5 168 33.5",
                 fill="none", stroke="#C2699E", stroke_width=1.1, opacity=0.95,
                 clip_path=ka))
    # tentakül orta çizgileri
    for tx1, ty1, tx2, ty2 in [(137.5, 39, 133.5, 46), (148.5, 40, 148.5, 47.5),
                               (159.5, 39, 163.5, 46)]:
        e.append(_el("line", x1=tx1, y1=ty1, x2=tx2, y2=ty2, stroke="#C2699E",
                     stroke_width=1.1, opacity=0.85, clip_path=ka))
    goz(e, 144, 25.5, 2.5)
    goz(e, 154, 25.5, 2.5)
    gulus(e, 149, 30.2, 5.5, 1.1)
    # yanaklar
    e.append(_el("ellipse", cx=139.5, cy=28.8, rx=1.9, ry=1.1, fill="#F2789E",
                 opacity=0.55))
    e.append(_el("ellipse", cx=158.5, cy=28.8, rx=1.9, ry=1.1, fill="#F2789E",
                 opacity=0.55))
    hacim(e, "kanasi", a, 0.07)

    # ---------- DENİZATI
    d = s_tasi(P["denizati"], 0, 2.5)
    e.append('<g transform="translate(0,-2.5)">')
    kd = _klip(e, "kati", d)
    e.append(_el("path", d=yol_svg(d), fill="url(#atig)"))
    # karın plakası
    e.append(_el("path", d="M 33 82 Q 30.5 95 34 106 Q 38 111 42.5 106 Q 39.5 94 41 82 "
                           "Q 37 79.5 33 82 Z", fill="#FFD98A", clip_path=kd,
                 opacity=0.95))
    # karın boğum çizgileri (kalın)
    for i in range(6):
        yy = 84.5 + i * 4.4
        e.append(_el("path", d=f"M 32 {yy} Q 38.5 {yy + 2.4} 44 {yy + 0.6}", fill="none",
                     stroke="#C97F12", stroke_width=0.95, opacity=0.9, clip_path=kd))
    # sırt tarağı (fırfır kenar)
    e.append(_el("path", d="M 44.5 80 Q 47 82.5 45.5 85.5 Q 48.5 87 47.5 90.5 "
                           "Q 50.5 92 49 95.5", fill="none", stroke="#C97F12",
                 stroke_width=1.0, opacity=0.9, clip_path=kd))
    # yüzgeç
    e.append(_el("path", d="M 47.5 84 Q 55 88 52.5 97.5 Q 47.5 94 46 90 Z",
                 fill="#FFDD9E", clip_path=kd))
    e.append(_el("path", d="M 49.3 85.8 L 52.6 88.4 M 48.8 89 L 52.2 91.9 M 48.5 92.4 "
                           "L 51.6 95", stroke="#E09022", stroke_width=0.7,
                 opacity=0.95, fill="none", clip_path=kd))
    # taç + burun
    e.append(_el("path", d="M 33.5 68.5 L 37.5 65.5 L 40 69 L 36.5 71.5 Z",
                 fill="#FFDD9E", clip_path=kd))
    e.append(_el("path", d="M 34.2 69.3 L 38 66.6", stroke="#C97F12", stroke_width=0.7,
                 fill="none", opacity=0.9))
    e.append(_el("path", d="M 23.5 73.4 L 30.5 74.4 M 23.7 76 L 30 76.3",
                 stroke="#C97F12", stroke_width=0.8, fill="none", opacity=0.9))
    gulus(e, 25.5, 77.6, 3.4, 0.8)
    goz(e, 36.5, 77.5, 2.6, (0.28, 0.05))
    # kuyruk kıvrım çizgisi
    e.append(_el("path", d="M 42.5 103 C 39.5 108 40 112.5 45.5 114.5 C 50 115.8 51.5 112 "
                           "49 110 C 47 108.6 45 110 45.8 112", fill="none",
                 stroke="#C97F12", stroke_width=1.0, opacity=0.95, clip_path=kd))
    hacim(e, "kati", d, 0.10)
    e.append("</g>")

    # ---------- KAPLUMBAĞA (kahverengi kabuk, yeşil deri)
    k = P["kaplumbaga"]
    kk = _klip(e, "kkaplumbaga", k)
    e.append(_el("path", d=yol_svg(k), fill="#A9C86B"))
    # deri benekleri
    for sx, sy, sr in [(98, 73.5, 1.1), (103.5, 72, 0.9), (106.5, 76, 1.0),
                       (99.5, 79.5, 0.9), (104.5, 80.5, 0.8), (119, 61.5, 1.0),
                       (125, 63.5, 0.9), (130, 66, 0.8), (121, 107.5, 1.0),
                       (127, 109.5, 0.9), (133, 110.5, 0.8), (167, 99.5, 0.9),
                       (172, 102.5, 0.8)]:
        e.append(_el("circle", cx=sx, cy=sy, r=sr, fill="#7FA344", opacity=0.9))
    # yüzgeç ayrım çizgileri
    e.append(_el("path", d="M 111 96 Q 122 100 133 99 M 113 68.5 Q 122 66 130 67",
                 fill="none", stroke=CIZGI, stroke_width=1.0, opacity=0.85,
                 clip_path=kk))
    # kabuk (kahverengi) + kenar bandı
    e.append(_el("ellipse", cx=140, cy=84, rx=33, ry=21.5, fill="url(#kabukg)"))
    e.append(_el("ellipse", cx=140, cy=84, rx=33, ry=21.5, fill="none", stroke=CIZGI,
                 stroke_width=1.4))
    e.append(_el("path", d="M 108.5 89 A 33 21.5 0 0 0 171.5 89 L 171 93.5 A 33 21.5 0 "
                           "0 1 109 93.5 Z", fill="#E3B85C", clip_path=kk))
    for aa in range(-155, 181, 28):
        ar = math.radians(aa)
        e.append(_el("line", x1=140 + 30 * math.cos(ar), y1=84 + 19.4 * math.sin(ar),
                     x2=140 + 33 * math.cos(ar), y2=84 + 21.5 * math.sin(ar),
                     stroke="#8F5911", stroke_width=0.8, opacity=0.9))
    # plakalar (kalın çizgili)
    kabuk_elips = elips(140, 84, 32.2, 20.8)
    for pts, ton in [("128,68 143,66.5 152,74 149,84 134,85.5 125,78", "#C08A2E"),
                     ("152,74 163,73 169,80 166,89 149,84", "#B37E24"),
                     ("149,84 146,95 131,96 134,85.5", "#AA761E"),
                     ("125,78 114,80 111,88 117,94 131,96 134,85.5", "#B37E24"),
                     ("143,66.5 145,63.5 158,63.5 163,73 152,74", "#AA761E")]:
        plaka = Polygon([tuple(map(float, p.split(","))) for p in pts.split()])
        kesit = plaka.intersection(kabuk_elips)
        if kesit.is_empty:
            continue
        for gg in (kesit.geoms if kesit.geom_type == "MultiPolygon" else [kesit]):
            e.append(_el("path", d=yol_svg(gg), fill=ton, opacity=0.95))
            e.append(_el("path", d=yol_svg(gg), fill="none", stroke="#6E4310",
                         stroke_width=1.2))
    goz(e, 98, 75.8, 2.6, (0.2, 0.05))
    gulus(e, 96.5, 81.2, 5.4, 1.0)
    e.append(_el("circle", cx=93.2, cy=77.2, r=0.4, fill=CIZGI, opacity=0.8))
    hacim(e, "kkaplumbaga", k, 0.09)

    # ---------- BALIK (sarı-mavi tropikal)
    b = P["balik"]
    kb = _klip(e, "kbalik", b)
    e.append(_el("path", d=yol_svg(b), fill="url(#baligg)"))
    # mavi bantlar
    for dpath in ("M 234.5 69.5 C 232.8 76 232.6 88 234.3 100 L 240.6 99 "
                  "C 239 88 239.2 76 240.8 68.5 Z",
                  "M 247.5 66.8 C 245 74 244.2 82 244.4 88 C 244.6 94 246 100 248.4 104 "
                  "L 255.5 103 C 253.6 96 253.2 74 255 66.5 Z",
                  "M 262 69 C 260.8 76 260.8 92 262 99.5 L 266.8 96.5 "
                  "C 265.9 90 265.9 80 266.8 73.5 Z"):
        e.append(_el("path", d=dpath, fill="#2B57C4", clip_path=kb))
    # kuyruk + yüzgeçler turuncu
    e.append(_el("path", d="M 271 79.5 L 284 71 L 284 101 L 271 92.5 Z", fill="#F5A623",
                 clip_path=kb))
    e.append(_el("path", d="M 272 80.5 L 272 91.5", fill="none", stroke=CIZGI,
                 stroke_width=1.0, clip_path=kb))
    e.append(_el("path", d="M 275.5 78 L 275.5 94 M 279.5 75.5 L 279.5 96.5",
                 fill="none", stroke="#D9820F", stroke_width=0.8, opacity=0.9,
                 clip_path=kb))
    e.append(_el("path", d="M 237 69.5 L 256 68 L 251 77 L 239 77 Z", fill="#F5A623",
                 clip_path=kb))
    e.append(_el("path", d="M 239.5 76.2 Q 247 74.5 254.5 68.8", fill="none",
                 stroke=CIZGI, stroke_width=1.0, opacity=0.9, clip_path=kb))
    e.append(_el("path", d="M 242 75.7 L 243 70 M 246.5 75 L 247.5 69.3 M 251 74.2 "
                           "L 252 68.6", stroke="#D9820F", stroke_width=0.7,
                 opacity=0.9, fill="none", clip_path=kb))
    e.append(_el("path", d="M 240 100.8 Q 245 103.4 250 101.2 M 255.5 100 Q 259.5 101.6 "
                           "263 98.8", fill="none", stroke=CIZGI, stroke_width=0.9,
                 opacity=0.85, clip_path=kb))
    # göğüs yüzgeci
    e.append(f'<g transform="rotate(-20 243 90.5)">'
             f'<ellipse cx="243" cy="90.5" rx="5.8" ry="3.3" fill="#F5A623"/>'
             f'<ellipse cx="243" cy="90.5" rx="5.8" ry="3.3" fill="none" '
             f'stroke="#20262B" stroke-width="0.9"/></g>')
    e.append(_el("path", d="M 239 91.4 L 247.6 89.4 M 239.6 93 L 247.6 91.2",
                 stroke="#D9820F", stroke_width=0.55, opacity=0.9, fill="none"))
    # dudak + gülümseme + göz
    e.append(_el("path", d="M 223.4 84.2 Q 226 83 228.4 84", fill="none", stroke=CIZGI,
                 stroke_width=0.9, stroke_linecap="round"))
    gulus(e, 226, 87.6, 4.6, 1.0)
    goz(e, 232.5, 79.5, 3.1, (0.22, 0.06))
    hacim(e, "kbalik", b, 0.10)

    # ---------- AHTAPOT (neşeli turuncu)
    o = s_tasi(P["ahtapot"], 0, -1.5)
    e.append('<g transform="translate(0,1.5)">')
    ko = _klip(e, "kahtapot", o)
    e.append(_el("path", d=yol_svg(o), fill="url(#ahtapotg)"))
    # kafa ışıltısı
    e.append(_el("ellipse", cx=48, cy=128, rx=10, ry=6.5, fill="#FFC08A", opacity=0.5,
                 transform="rotate(-18 48 128)"))
    # vantuzlar
    for vx, vy, vr in [(35.2, 155, 1.25), (32.2, 158.2, 1.1), (29.4, 161.2, 1.0),
                       (27.3, 163.8, 0.9), (47.8, 159.5, 1.1), (46.6, 162.6, 1.0),
                       (45.6, 165.4, 0.9), (68.2, 159.5, 1.1), (69.4, 162.6, 1.0),
                       (70.4, 165.4, 0.9), (80.8, 155, 1.25), (83.8, 158.2, 1.1),
                       (86.6, 161.2, 1.0), (88.7, 163.8, 0.9)]:
        e.append(_el("circle", cx=vx, cy=vy, r=vr, fill="#FFC08A"))
        e.append(_el("circle", cx=vx, cy=vy, r=vr, fill="none", stroke="#D9660E",
                     stroke_width=0.4))
    # benekler
    for sx, sy in [(44, 124), (58, 121.5), (70, 125), (50, 131), (66, 131.5)]:
        e.append(_el("circle", cx=sx, cy=sy, r=1.15, fill="#FFC08A", opacity=0.95))
    goz(e, 49.5, 142.5, 3.7, (0.22, 0.08))
    goz(e, 66.5, 142.5, 3.7, (0.22, 0.08))
    gulus(e, 58, 149.8, 8.5, 1.25)
    e.append(_el("ellipse", cx=42.5, cy=147.5, rx=2.3, ry=1.35, fill="#F2789E",
                 opacity=0.5))
    e.append(_el("ellipse", cx=73.5, cy=147.5, rx=2.3, ry=1.35, fill="#F2789E",
                 opacity=0.5))
    hacim(e, "kahtapot", o, 0.09)
    e.append("</g>")

    # ---------- YENGEÇ (parlak kırmızı)
    yc = P["yengec"]
    kyc = _klip(e, "kyengec", yc)
    e.append(_el("path", d=yol_svg(yc), fill="url(#yengecg)"))
    # kabuk ışıltısı + alt kenar
    e.append(_el("ellipse", cx=155, cy=144.5, rx=10, ry=5, fill="#FF8A70", opacity=0.6,
                 transform="rotate(-12 155 144.5)", clip_path=kyc))
    e.append(_el("path", d="M 142.5 156.5 Q 163 163.5 183.5 156.5", fill="none",
                 stroke="#A81C0E", stroke_width=1.1, opacity=0.85, clip_path=kyc))
    # kıskaç ayrımları
    e.append(_el("path", d="M 134.5 133 L 139.8 139.8 M 191.5 133 L 186.2 139.8",
                 stroke=CIZGI, stroke_width=1.1, fill="none", clip_path=kyc))
    e.append(_el("path", d="M 143.5 141.5 Q 146.5 145 150.5 146.2 M 182.5 141.5 "
                           "Q 179.5 145 175.5 146.2", stroke=CIZGI, stroke_width=1.0,
                 fill="none", opacity=0.9, clip_path=kyc))
    # bacak eklem çizgileri
    e.append(_el("path", d="M 143 163.5 L 146.2 162 M 152.4 165.6 L 154.8 164 "
                           "M 173.6 165.6 L 171.2 164 M 183 163.5 L 179.8 162",
                 stroke="#A81C0E", stroke_width=0.9, fill="none", opacity=0.9,
                 clip_path=kyc))
    # göz sapları üstünde iri gözler
    goz(e, 157.9, 130.6, 2.8, (0.1, 0.15))
    goz(e, 168.1, 130.6, 2.8, (-0.1, 0.15))
    gulus(e, 163, 143.6, 7.5, 1.25)
    e.append(_el("ellipse", cx=150.5, cy=147.5, rx=2.1, ry=1.2, fill="#FF9E86",
                 opacity=0.65))
    e.append(_el("ellipse", cx=175.5, cy=147.5, rx=2.1, ry=1.2, fill="#FF9E86",
                 opacity=0.65))
    hacim(e, "kyengec", yc, 0.10)

    # ---------- DENİZYILDIZI (noktalı, gülen)
    z = P["denizyildizi"]
    kz = _klip(e, "kyildiz", z)
    e.append(_el("path", d=yol_svg(z), fill="url(#yildizg)"))
    for i in range(5):
        aa = math.radians(-90 + i * 72)
        ux, uy = math.cos(aa), math.sin(aa)
        nx, nyy = -uy, ux
        for t in (8.5, 13, 17.5):
            e.append(_el("circle", cx=261 + t * ux, cy=149 + t * uy, r=0.8,
                         fill="#C4610A", opacity=0.9))
        for t in (10.5, 15.5):
            for taraf in (-1, 1):
                e.append(_el("circle", cx=261 + t * ux + nx * 2.6 * taraf,
                             cy=149 + t * uy + nyy * 2.6 * taraf, r=0.55,
                             fill="#C4610A", opacity=0.8))
    goz(e, 257.3, 145.8, 2.2, (0.2, 0.1))
    goz(e, 264.7, 145.8, 2.2, (0.2, 0.1))
    gulus(e, 261, 150.6, 5.2, 1.1)
    e.append(_el("ellipse", cx=253.8, cy=149.4, rx=1.7, ry=1.0, fill="#FFB27A",
                 opacity=0.7))
    e.append(_el("ellipse", cx=268.2, cy=149.4, rx=1.7, ry=1.0, fill="#FFB27A",
                 opacity=0.7))
    hacim(e, "kyildiz", z, 0.10)

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
