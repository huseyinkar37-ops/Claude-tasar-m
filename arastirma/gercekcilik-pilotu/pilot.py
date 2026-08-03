# -*- coding: utf-8 -*-
"""
Gerçekçilik pilotu v2 — anatomi düzeltmeleri.

v1'de malzeme sistemi (kabartma, AO, ıslaklık, temas gölgesi) tuttu ama
siluetler yanlıştı. v2 formu düzeltiyor:
  - yunus: kısa gaga + belirgin melon, falkat sırt yüzgeci, geniş kuyruk
  - kaplumbağa: parametrik kabuk + gerçek plaka dizilimi (5 orta, 4 yan çift,
    kenar halkası), uzun kürek biçimli ön yüzgeçler
  - balık: fusiform gövde, çatal kuyruk, ışınlı yüzgeçler
"""
import math
import os

import resvg_py
from shapely.geometry import Polygon

KLASOR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ eğri araçları
def _kr(pts, g=1.0):
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1 = pts[(i - 1) % n], pts[i]
        p2, p3 = pts[(i + 1) % n], pts[(i + 2) % n]
        out.append((p1,
                    (p1[0] + (p2[0] - p0[0]) / 6.0 * g,
                     p1[1] + (p2[1] - p0[1]) / 6.0 * g),
                    (p2[0] - (p3[0] - p1[0]) / 6.0 * g,
                     p2[1] - (p3[1] - p1[1]) / 6.0 * g),
                    p2))
    return out


def egri_yol(pts, g=1.0):
    seg = _kr(pts, g)
    d = [f"M {seg[0][0][0]:.3f} {seg[0][0][1]:.3f}"]
    for _, c1, c2, p2 in seg:
        d.append(f"C {c1[0]:.3f} {c1[1]:.3f} {c2[0]:.3f} {c2[1]:.3f} "
                 f"{p2[0]:.3f} {p2[1]:.3f}")
    return " ".join(d) + " Z"


def egri_poly(pts, g=1.0, adim=18):
    o = []
    for p1, c1, c2, p2 in _kr(pts, g):
        for k in range(adim):
            t = k / adim
            u = 1 - t
            o.append((u**3 * p1[0] + 3*u*u*t * c1[0] + 3*u*t*t * c2[0] + t**3 * p2[0],
                      u**3 * p1[1] + 3*u*u*t * c1[1] + 3*u*t*t * c2[1] + t**3 * p2[1]))
    return Polygon(o).buffer(0)


def poly_yol(pts):
    return ("M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts)) + " Z"


# ------------------------------------------------------------------ SVG
def el(ad, **a):
    ic = a.pop("icerik", None)
    s = "<" + ad + "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"'
                           for k, v in a.items())
    return s + (f">{ic}</{ad}>" if ic is not None else "/>")


def lin(i, x1, y1, x2, y2, dur):
    s = [f'<linearGradient id="{i}" gradientUnits="userSpaceOnUse" x1="{x1}" '
         f'y1="{y1}" x2="{x2}" y2="{y2}">']
    for o, c, *op in dur:
        s.append(f'<stop offset="{o}" stop-color="{c}"'
                 + (f' stop-opacity="{op[0]}"' if op else "") + "/>")
    return "".join(s) + "</linearGradient>"


def rad(i, cx, cy, r, dur):
    s = [f'<radialGradient id="{i}" gradientUnits="userSpaceOnUse" cx="{cx}" '
         f'cy="{cy}" r="{r}">']
    for o, c, *op in dur:
        s.append(f'<stop offset="{o}" stop-color="{c}"'
                 + (f' stop-opacity="{op[0]}"' if op else "") + "/>")
    return "".join(s) + "</radialGradient>"


def f_bulanik(i, s, pay=60):
    return (f'<filter id="{i}" x="-{pay}%" y="-{pay}%" width="{100+2*pay}%" '
            f'height="{100+2*pay}%"><feGaussianBlur stdDeviation="{s}"/></filter>')


def f_deri(i, frek, okt=4, kab=1.6, toh=5, az=228, elv=56):
    return (f'<filter id="{i}" x="-15%" y="-15%" width="130%" height="130%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{frek}" '
            f'numOctaves="{okt}" seed="{toh}" result="n"/>'
            f'<feDiffuseLighting in="n" surfaceScale="{kab}" diffuseConstant="1" '
            f'lighting-color="#ffffff" result="d">'
            f'<feDistantLight azimuth="{az}" elevation="{elv}"/></feDiffuseLighting>'
            f'<feComposite in="d" in2="SourceGraphic" operator="arithmetic" '
            f'k1="1" k2="0" k3="0" k4="0" result="c"/>'
            f'<feComposite in="c" in2="SourceGraphic" operator="in"/></filter>')


def f_islak(i, frek, kab=2.2, us=26, lx=90, ly=10, lz=70, toh=2):
    return (f'<filter id="{i}" x="-20%" y="-20%" width="140%" height="140%">'
            f'<feTurbulence type="fractalNoise" baseFrequency="{frek}" '
            f'numOctaves="3" seed="{toh}" result="n"/>'
            f'<feSpecularLighting in="n" surfaceScale="{kab}" specularConstant="1" '
            f'specularExponent="{us}" lighting-color="#ffffff" result="s">'
            f'<fePointLight x="{lx}" y="{ly}" z="{lz}"/></feSpecularLighting>'
            f'<feComposite in="s" in2="SourceGraphic" operator="in"/></filter>')


def klip(e, i, d):
    e.append(f'<clipPath id="{i}"><path d="{d}"/></clipPath>')
    return i


def ic_golge(e, k, d, renk="#06202F", kal=3.2, op=0.52):
    e.append(el("path", d=d, fill="none", stroke=renk, stroke_width=kal,
                opacity=op, filter="url(#fb_ao)", clip_path=f"url(#{k})"))


def kenar_isigi(e, k, d, renk="#FFFFFF", kal=1.5, dx=-0.4, dy=-0.8, op=0.45):
    e.append(el("path", d=d, fill="none", stroke=renk, stroke_width=kal,
                opacity=op, filter="url(#fb_rim)", clip_path=f"url(#{k})",
                transform=f"translate({dx},{dy})"))


def temas(e, cx, cy, rx, ry, op=0.26):
    e.append(el("ellipse", cx=cx, cy=cy, rx=rx, ry=ry, fill="#04121C",
                opacity=op, filter="url(#fb_zemin)"))


# ================================================================== YUNUS
# Şişe burunlu yunus yan profili: gaga kısa, melon belirgin, sırt yüzgeci falkat.
YUNUS = [
    (100.0, 33.0), (95.5, 30.6),                     # gaga ucu + üstü
    (90.5, 28.6), (86.0, 23.6), (79.5, 20.4),        # melon çıkıntısı (dik alın)
    (70.5, 18.4), (62.0, 17.4),                      # sırt
    (57.0, 17.2), (49.5, 7.8), (44.5, 18.6),         # falkat sırt yüzgeci
    (36.0, 20.6), (26.5, 23.2),                      # kuyruk sapı üstü
    (19.0, 20.0), (11.0, 15.4),                      # üst lob
    (16.5, 25.0), (20.0, 29.6), (16.5, 34.2),        # fisto
    (11.0, 43.6), (19.5, 38.0),                      # alt lob
    (27.0, 34.2), (38.0, 39.6), (50.0, 42.2),
    (57.0, 42.6), (49.5, 52.2), (63.0, 43.2),        # göğüs yüzgeci
    (72.0, 41.2), (82.0, 38.6), (90.5, 35.6), (97.0, 34.3),
]


def ciz_yunus(e):
    d = egri_yol(YUNUS, 0.90)
    k = klip(e, "k_yunus", d)
    temas(e, 56, 58.5, 34, 3.4)
    e.append(el("path", d=d, fill="url(#g_yunus)"))
    # karşı-gölgeleme: koyu sırt / açık karın, yumuşak geçişli
    e.append(el("path", d="M 6 34.5 C 34 47.5 74 44.0 104 33.0 L 104 58 L 6 58 Z",
                fill="url(#g_yunus_karin)", clip_path=f"url(#{k})",
                filter="url(#fb_karin)"))
    # yüzgeç form gölgeleri
    for pts in ([(57.0, 17.4), (49.5, 8.0), (44.7, 18.6), (52.0, 19.4)],
                [(57.0, 42.6), (49.5, 52.2), (63.0, 43.2), (58.5, 41.8)]):
        e.append(el("path", d=egri_yol(pts, 0.9), fill="#33485B", opacity=0.42,
                    clip_path=f"url(#{k})", filter="url(#fb_form)"))
    e.append(el("path", d=d, fill="#8FA3B4", opacity=0.28,
                filter="url(#f_deri_yunus)"))
    e.append(el("path", d=d, fill="#FFFFFF", opacity=0.30,
                filter="url(#f_islak_yunus)"))
    e.append(el("ellipse", cx=64, cy=23.5, rx=26, ry=5.0, fill="#EAF3F9",
                opacity=0.28, transform="rotate(-6 64 23.5)",
                clip_path=f"url(#{k})", filter="url(#fb_parla)"))
    ic_golge(e, k, d, "#0B2334", 3.0, 0.48)
    kenar_isigi(e, k, d, "#DCEEF8", 1.4, -0.4, -0.8, 0.42)
    # melon/gaga ayrım kırışığı — yunusu köpekbalığından ayıran detay
    e.append(el("path", d="M 90.8 28.2 C 89.6 31.0 89.8 33.4 90.6 35.4",
                fill="none", stroke="#4A6072", stroke_width=0.55, opacity=0.55,
                stroke_linecap="round"))
    # ağız yarığı (hafif, karikatür gülüş değil)
    e.append(el("path", d="M 99.0 34.0 C 93.0 36.4 87.0 36.6 82.4 35.2",
                fill="none", stroke="#31465A", stroke_width=0.7, opacity=0.7,
                stroke_linecap="round"))
    e.append(el("ellipse", cx=80.8, cy=29.8, rx=1.45, ry=1.2, fill="#101C24"))
    e.append(el("ellipse", cx=80.4, cy=29.4, rx=0.48, ry=0.38, fill="#FFFFFF",
                opacity=0.85))
    e.append(el("ellipse", cx=74.0, cy=19.0, rx=1.1, ry=0.5, fill="#243645",
                opacity=0.75))


# ================================================================== KAPLUMBAĞA
# Kabuk parametrik: s = boy ekseni (0..1), t = en ekseni (-1..1).
KB_MX, KB_Y0, KB_BOY, KB_RX = 172.0, 56.0, 62.0, 25.5


def kb_w(s):
    """Kabuk yarı-genişliği: önde geniş, arkaya doğru daralan yumurta oval."""
    return KB_RX * (max(1e-6, 1 - (2 * s - 1) ** 2)) ** 0.40 * (1 - 0.26 * s)


def kb_p(s, t):
    return (KB_MX + t * kb_w(s), KB_Y0 + s * KB_BOY)


def kb_kontur(n=64):
    sag = [kb_p(i / n, 1.0) for i in range(n + 1)]
    sol = [kb_p(1 - i / n, -1.0) for i in range(n + 1)]
    return sag + sol


def plaka_hex(s0, s1, t_dar, t_genis, n=3):
    """Altıgen plaka: dikişlerde dar, ortada geniş — gerçek vertebral biçim."""
    sm = (s0 + s1) / 2
    kose = [(s0, -t_dar), (sm, -t_genis), (s1, -t_dar),
            (s1, t_dar), (sm, t_genis), (s0, t_dar)]
    p = []
    for i in range(len(kose)):
        a, b = kose[i], kose[(i + 1) % len(kose)]
        for j in range(n):
            u = j / n
            p.append(kb_p(a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return p


def plaka(s0, s1, t0, t1, n=4):
    p = [kb_p(s0 + (s1 - s0) * i / n, t0) for i in range(n + 1)]
    p += [kb_p(s1, t0 + (t1 - t0) * i / n) for i in range(1, n + 1)]
    p += [kb_p(s1 - (s1 - s0) * i / n, t1) for i in range(1, n + 1)]
    p += [kb_p(s0, t1 - (t1 - t0) * i / n) for i in range(1, n)]
    return p


KAPLUM = [                                        # gövde: baş + 4 yüzgeç
    (172.0, 47.5), (179.5, 50.5), (181.0, 57.0),                     # baş sağ
    (191.0, 60.0), (196.5, 66.0),                                    # omuz sağ
    (214.0, 71.0), (231.0, 86.0), (226.0, 94.5), (206.0, 84.0),      # ön yüzgeç sağ
    (198.0, 90.0), (194.0, 104.0),
    (206.0, 114.0), (200.0, 121.5), (187.0, 114.5),                  # arka yüzgeç sağ
    (177.0, 115.0), (172.0, 121.0), (167.0, 115.0), (157.0, 114.5),  # kuyruk
    (144.0, 114.5), (138.0, 121.5), (132.0, 114.0),                  # arka yüzgeç sol
    (150.0, 104.0), (146.0, 90.0), (138.0, 84.0),
    (118.0, 94.5), (113.0, 86.0), (130.0, 71.0),                     # ön yüzgeç sol
    (147.5, 66.0), (153.0, 60.0),
    (163.0, 57.0), (164.5, 50.5),
]


def ciz_kaplumbaga(e):
    d_g = egri_yol(KAPLUM, 0.72)
    d_k = poly_yol(kb_kontur())
    kg = klip(e, "k_kaplum", d_g)
    kk = klip(e, "k_kabuk", d_k)
    temas(e, 172, 122, 42, 4.0)

    e.append(el("path", d=d_g, fill="url(#g_deri)"))
    e.append(el("path", d=d_g, fill="#5E7A46", opacity=0.32,
                filter="url(#f_deri_kaplum)"))
    ic_golge(e, kg, d_g, "#16260F", 2.8, 0.5)
    kenar_isigi(e, kg, d_g, "#DCF0C4", 1.3, -0.4, -0.7, 0.38)

    e.append(el("path", d=d_k, fill="url(#g_kabuk)"))
    # 5 orta (vertebral) plaka — altıgen
    kesit = [0.05, 0.23, 0.41, 0.59, 0.77, 0.94]
    for i in range(5):
        e.append(el("path", d=poly_yol(plaka_hex(kesit[i], kesit[i + 1],
                                                 0.20, 0.32)),
                    fill="url(#g_plaka)", stroke="#4A2E10", stroke_width=0.5,
                    opacity=0.92, clip_path=f"url(#{kk})"))
    # 4 çift yan (kostal) plaka — dikişleri vertebrallerle şaşırtmalı
    yan = [0.02, 0.24, 0.46, 0.68, 0.94]
    for yon in (1, -1):
        for i in range(4):
            e.append(el("path",
                        d=poly_yol(plaka(yan[i], yan[i + 1],
                                         yon * 0.26, yon * 0.80)),
                        fill="url(#g_plaka)", stroke="#4A2E10",
                        stroke_width=0.45, opacity=0.86,
                        clip_path=f"url(#{kk})"))
    # kenar (marjinal) plaka halkası
    for i in range(11):
        s0, s1 = 0.02 + i * 0.089, 0.02 + (i + 1) * 0.089
        for yon in (1, -1):
            e.append(el("path", d=poly_yol(plaka(s0, s1, yon * 0.78, yon * 1.0)),
                        fill="#8A5A22", stroke="#4A2E10", stroke_width=0.4,
                        opacity=0.5, clip_path=f"url(#{kk})"))

    e.append(el("path", d=d_k, fill="#7A4E1B", opacity=0.36,
                filter="url(#f_deri_kabuk)"))
    ic_golge(e, kk, d_k, "#2A1806", 3.4, 0.58)
    kenar_isigi(e, kk, d_k, "#F3D9A6", 1.4, -0.5, -0.9, 0.42)
    e.append(el("ellipse", cx=161, cy=72, rx=14, ry=10, fill="#FFF0CE",
                opacity=0.22, transform="rotate(-24 161 72)",
                clip_path=f"url(#{kk})", filter="url(#fb_parla)"))

    # baş: gerçek oranlı, gülümsemesiz
    e.append(el("ellipse", cx=172, cy=52.5, rx=7.8, ry=6.4, fill="url(#g_bas)",
                clip_path=f"url(#{kg})"))
    for px, py, rx_, ry_ in [(166.5, 56.5, 1.9, 1.5), (177.5, 56.5, 1.9, 1.5),
                             (168.5, 51.0, 1.5, 1.2), (175.5, 51.0, 1.5, 1.2),
                             (172.0, 47.8, 1.3, 1.0)]:
        e.append(el("ellipse", cx=px, cy=py, rx=rx_, ry=ry_, fill="#C2D68F",
                    opacity=0.40, stroke="#5B7534", stroke_width=0.3,
                    clip_path=f"url(#{kg})"))
    for dx in (-4.2, 4.2):
        e.append(el("ellipse", cx=172 + dx, cy=51.2, rx=1.2, ry=1.0,
                    fill="#14200C"))
        e.append(el("ellipse", cx=172 + dx - 0.3, cy=50.8, rx=0.38, ry=0.3,
                    fill="#FFFFFF", opacity=0.8))
    # gaga hattı
    e.append(el("path", d="M 168.6 47.8 C 170.4 46.6 173.6 46.6 175.4 47.8",
                fill="none", stroke="#3F5423", stroke_width=0.55, opacity=0.65,
                stroke_linecap="round"))
    # ön yüzgeç kas/pul çizgileri
    for x0, y0, x1, y1 in [(202, 71, 221, 82), (201, 76, 217, 87),
                           (142, 71, 123, 82), (143, 76, 127, 87)]:
        e.append(el("path", d=f"M {x0} {y0} Q {(x0+x1)/2} {(y0+y1)/2 - 3} {x1} {y1}",
                    fill="none", stroke="#415B26", stroke_width=0.5, opacity=0.5,
                    clip_path=f"url(#{kg})"))


# ================================================================== BALIK
BALIK = [
    (226.0, 88.0), (231.0, 79.5), (239.0, 72.5), (249.0, 68.0),      # baş + sırt
    (256.0, 61.5), (266.0, 63.5), (272.5, 71.0),                     # sırt yüzgeci
    (281.0, 80.0), (285.5, 84.5),                                    # kuyruk sapı
    (301.0, 69.5), (295.0, 88.0), (301.0, 106.5),                    # çatal kuyruk
    (285.5, 91.5), (277.0, 96.5),
    (268.0, 103.5), (259.0, 101.0),                                  # anal yüzgeç
    (249.0, 102.5), (241.0, 97.0), (232.5, 93.0),                    # karın yüzgeci
]


def ciz_balik(e):
    d = egri_yol(BALIK, 0.82)
    k = klip(e, "k_balik", d)
    temas(e, 264, 116, 30, 3.4)
    e.append(el("path", d=d, fill="url(#g_balik)"))
    e.append(el("path", d="M 222 94 C 244 105 272 102 306 92 L 306 120 L 222 120 Z",
                fill="url(#g_balik_karin)", clip_path=f"url(#{k})",
                filter="url(#fb_karin)"))
    # pullar: gövde eğrisini takip eden sıralar
    pul = []
    for sira in range(10):
        yy = 70.0 + sira * 3.5
        kay = 1.8 if sira % 2 else 0.0
        for sut in range(18):
            px = 232.0 + sut * 3.4 + kay
            pul.append(el("path", d=f"M {px:.1f} {yy:.1f} a 2.3 2.7 0 0 1 4.2 0",
                          fill="none", stroke="#9A6408", stroke_width=0.34,
                          opacity=0.40, clip_path=f"url(#{k})"))
    e.append("".join(pul))
    # yüzgeç ışınları
    ray = []
    for i in range(6):
        t = i / 5
        ray.append(el("line", x1=257 + t * 14, y1=63 + t * 7.5, x2=259 + t * 12,
                      y2=73 + t * 6, stroke="#B87A0C", stroke_width=0.45,
                      opacity=0.6, clip_path=f"url(#{k})"))
        ray.append(el("line", x1=252 + t * 15, y1=102 + t * 1.5, x2=254 + t * 13,
                      y2=95 + t * 3, stroke="#B87A0C", stroke_width=0.42,
                      opacity=0.55, clip_path=f"url(#{k})"))
    for i in range(9):
        t = i / 8
        ray.append(el("line", x1=287, y1=86 + (t - 0.5) * 4, x2=299,
                      y2=71 + t * 34, stroke="#B87A0C", stroke_width=0.42,
                      opacity=0.5, clip_path=f"url(#{k})"))
    e.append("".join(ray))
    # solungaç kapağı + göğüs yüzgeci
    e.append(el("path", d="M 243 72.5 C 238.5 80 239 92 244.5 99.5", fill="none",
                stroke="#8F5C06", stroke_width=0.75, opacity=0.55))
    e.append(el("path", d=egri_yol([(247, 86), (256, 90), (252, 97), (246, 92)], 0.9),
                fill="#E8A81C", opacity=0.55, stroke="#9A6408",
                stroke_width=0.4, clip_path=f"url(#{k})"))
    e.append(el("path", d=d, fill="#E8A81C", opacity=0.24,
                filter="url(#f_deri_balik)"))
    e.append(el("path", d=d, fill="#FFFFFF", opacity=0.36,
                filter="url(#f_islak_balik)"))
    ic_golge(e, k, d, "#5B3402", 2.6, 0.48)
    kenar_isigi(e, k, d, "#FFF3C8", 1.3, -0.4, -0.8, 0.46)
    e.append(el("circle", cx=237.5, cy=81.0, r=3.0, fill="url(#g_goz)"))
    e.append(el("circle", cx=237.5, cy=81.0, r=1.5, fill="#0B0D10"))
    e.append(el("circle", cx=236.7, cy=80.1, r=0.6, fill="#FFFFFF", opacity=0.9))
    e.append(el("circle", cx=237.5, cy=81.0, r=3.0, fill="none", stroke="#8A5A08",
                stroke_width=0.45, opacity=0.65))


# ================================================================== belge
def tanimlar():
    g = ["<defs>"]
    g += [f_bulanik("fb_ao", 1.1), f_bulanik("fb_rim", 0.7),
          f_bulanik("fb_zemin", 2.6), f_bulanik("fb_karin", 2.4),
          f_bulanik("fb_form", 1.1), f_bulanik("fb_parla", 3.2)]
    g += [f_deri("f_deri_yunus", 0.55, 4, 0.85, 5),
          f_islak("f_islak_yunus", 0.11, 1.8, 30, 70, 6, 55, 2),
          f_deri("f_deri_kaplum", 0.85, 4, 1.0, 9),
          f_deri("f_deri_kabuk", 0.40, 5, 1.4, 3),
          f_deri("f_deri_balik", 0.70, 4, 0.75, 11),
          f_islak("f_islak_balik", 0.14, 1.6, 34, 250, 60, 45, 4)]
    g += [
        lin("g_yunus", 0, 8, 0, 52, [(0, "#465C6E"), (0.30, "#688093"),
                                     (0.62, "#8CA3B5"), (1, "#ADC1CE")]),
        lin("g_yunus_karin", 0, 32, 0, 50, [(0, "#DDE9F0", 0.0),
                                            (0.40, "#E6EFF5", 0.85),
                                            (1, "#F2F8FB", 0.95)]),
        lin("g_deri", 0, 51, 0, 120, [(0, "#9CBB6A"), (0.45, "#7CA04C"),
                                      (1, "#5B7A34")]),
        lin("g_bas", 0, 50, 0, 64, [(0, "#A8C776"), (1, "#6F9440")]),
        # kabuk düz bir kubbe; küre etkisi vermemesi için geçişler yumuşak
        lin("g_kabuk", 150, 60, 196, 116, [(0, "#B98130"), (0.40, "#A56A22"),
                                           (0.75, "#8C5518"), (1, "#77450F")]),
        rad("g_plaka", 162, 70, 44, [(0, "#CE9A4E"), (0.55, "#B0742A"),
                                     (1, "#8F5817")]),
        lin("g_balik", 0, 61, 0, 108, [(0, "#C97F04"), (0.30, "#EDAC12"),
                                       (0.66, "#F9C93E"), (1, "#FBDD76")]),
        lin("g_balik_karin", 0, 92, 0, 108, [(0, "#FBE49C", 0.0),
                                             (0.5, "#FCEEC0", 0.55),
                                             (1, "#FEF7E0", 0.75)]),
        rad("g_goz", 236.5, 80, 3.3, [(0, "#E8B93C"), (0.6, "#B87C10"),
                                      (1, "#7A4E06")]),
    ]
    return "".join(g) + "</defs>"


def sahne():
    e = []
    ciz_yunus(e)
    ciz_kaplumbaga(e)
    e.append('<g transform="translate(18,6)">')
    ciz_balik(e)
    e.append("</g>")
    return "".join(e)


def _yaz(dosya, svg, px):
    yol = os.path.join(KLASOR, dosya)
    open(yol, "wb").write(bytes(resvg_py.svg_to_bytes(svg_string=svg, width=px)))
    return yol


def uret(dosya, px=2400):
    w, h = 320.0, 132.0
    return _yaz(dosya, f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                       f'height="{h}" viewBox="0 0 {w} {h}">{tanimlar()}'
                       f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>'
                       f'{sahne()}</svg>', px)


def yakin(dosya, kutu, px=1500):
    x, y, w, h = kutu
    return _yaz(dosya, f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" '
                       f'height="{h}" viewBox="{x} {y} {w} {h}">{tanimlar()}'
                       f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                       f'fill="#FFFFFF"/>{sahne()}</svg>', px)


if __name__ == "__main__":
    print(uret("v3_sayfa.png"))
    print(yakin("v3_yunus.png", (6, 4, 100, 56)))
    print(yakin("v3_kaplum.png", (106, 42, 132, 88)))
    print(yakin("v3_balik.png", (220, 56, 90, 66)))
    for ad, pts, g in [("yunus", YUNUS, 0.90), ("kaplumbaga", KAPLUM, 0.72),
                       ("balik", BALIK, 0.82)]:
        p = egri_poly(pts, g)
        kes = p.buffer(1.4).buffer(-1.4)
        print(f"{ad}: {p.area:.0f} mm² -> kapama {kes.area:.0f} mm² "
              f"(%{100 * (kes.area / p.area - 1):.1f})")
