# -*- coding: utf-8 -*-
"""
İki katmanlı "Araçlar" puzzle üretim dosyalarını oluşturur (320 x 180 mm).

Çıktılar (cikti/ klasörüne):
  1. araclar_uv_kalip.pdf        – UV baskı hizalama kalıbı (320x180, kesim konturları)
  2. araclar_uv_baski.pdf        – UV baskı dosyası, her kenardan 2 mm taşmalı (324x184)
  3. araclar_lazer_kesim.dxf     – Lazer kesim: ÜST katman (cepli) + ALT katman (düz)
  4. araclar_onizleme.png        – Ekranda bakmak için önizleme

Çalıştırma:  python3 olustur.py
"""
import math
import os

# ---------------------------------------------------------------- temel ölçüler
W, H = 320.0, 180.0          # bitmiş puzzle (mm)
BLEED = 2.0                  # baskı taşması (mm)
CORNER_R = 8.0               # dış köşe yuvarlatma (çocuk güvenliği)
MIN_GAP = 7.5                # iki parça arası en az duvar (mm)
MIN_EDGE = 6.0               # parça ile dış kenar arası en az duvar (mm)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cikti")

# renk paleti
C = dict(
    gok="#B9E7F8", gunes="#FFD23F", bulut="#FFFFFF",
    cim="#7ECB5A", cim_koyu="#5FB344", govde_agac="#8B5E3C", yaprak="#3E9B4F",
    yol="#9A9AA2", yol_cizgi="#FFFFFF", kaldirim="#C8C8CF",
    deniz="#3FA9E0", dalga="#9BD9F4",
    dis_cizgi="#2B2B33",
    ucak="#F2F5F7", ucak_aksan="#E04747", cam="#CDEBF7",
    balon1="#E04747", balon2="#FFD23F", balon3="#3D7DE0", sepet="#8B5E3C",
    heli="#F2762E", heli_koyu="#D95F1E",
    traktor="#4CAF50", traktor_koyu="#3B8F3F", teker="#3A3A42", jant="#C9C9CE",
    itfaiye="#E02D2D", itfaiye_koyu="#B82323", merdiven="#F5F5F5",
    araba="#3D7DE0", araba_koyu="#2F63B4",
    otobus="#F5B301", otobus_koyu="#D99C00",
    yelken="#FFFFFF", tekne="#E04747", direk="#6B4A2F",
    feribot="#F2F5F7", feribot_alt="#2F63B4", baca="#FFD23F",
)

# ---------------------------------------------------------------- yol (path) aracı
class Yol:
    """SVG path + örneklenmiş poligon üreten basit çizim yolu (mm, y aşağı)."""

    def __init__(self):
        self.d = []
        self.pts = []
        self.start = None

    def M(self, x, y):
        self.d.append(f"M {x:.3f} {y:.3f}")
        self.pts.append((x, y))
        self.start = (x, y)
        return self

    def L(self, x, y):
        self.d.append(f"L {x:.3f} {y:.3f}")
        self.pts.append((x, y))
        return self

    def C(self, x1, y1, x2, y2, x, y, n=16):
        x0, y0 = self.pts[-1]
        self.d.append(f"C {x1:.3f} {y1:.3f} {x2:.3f} {y2:.3f} {x:.3f} {y:.3f}")
        for i in range(1, n + 1):
            t = i / n
            mt = 1 - t
            px = mt**3 * x0 + 3 * mt**2 * t * x1 + 3 * mt * t**2 * x2 + t**3 * x
            py = mt**3 * y0 + 3 * mt**2 * t * y1 + 3 * mt * t**2 * y2 + t**3 * y
            self.pts.append((px, py))
        return self

    def arc(self, cx, cy, r, a0, a1):
        """a0 -> a1 (derece) çember yayı; artan açı ekranda saat yönü (y aşağı).
        Mevcut noktadan yay başlangıcına çizgi çekilmiş olmalı ya da eşleşmeli."""
        a0r, a1r = math.radians(a0), math.radians(a1)
        sx, sy = cx + r * math.cos(a0r), cy + r * math.sin(a0r)
        if not self.pts:
            self.M(sx, sy)
        elif abs(self.pts[-1][0] - sx) > 1e-6 or abs(self.pts[-1][1] - sy) > 1e-6:
            self.L(sx, sy)
        n = max(1, int(math.ceil(abs(a1r - a0r) / (math.pi / 2) - 1e-9)))
        for i in range(n):
            b0 = a0r + (a1r - a0r) * i / n
            b1 = a0r + (a1r - a0r) * (i + 1) / n
            k = 4.0 / 3.0 * math.tan((b1 - b0) / 4.0)
            p0 = (cx + r * math.cos(b0), cy + r * math.sin(b0))
            p3 = (cx + r * math.cos(b1), cy + r * math.sin(b1))
            c1 = (p0[0] - k * r * math.sin(b0), p0[1] + k * r * math.cos(b0))
            c2 = (p3[0] + k * r * math.sin(b1), p3[1] - k * r * math.cos(b1))
            self.C(c1[0], c1[1], c2[0], c2[1], p3[0], p3[1], n=12)
        return self

    def Z(self):
        self.d.append("Z")
        if self.start and self.pts[-1] != self.start:
            self.pts.append(self.start)
        return self

    def svg(self):
        return " ".join(self.d)

    def bbox(self):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        return min(xs), min(ys), max(xs), max(ys)


def yuvarlak_dikdortgen(x, y, w, h, r):
    p = Yol()
    p.M(x + r, y)
    p.L(x + w - r, y).arc(x + w - r, y + r, r, -90, 0)
    p.L(x + w, y + h - r).arc(x + w - r, y + h - r, r, 0, 90)
    p.L(x + r, y + h).arc(x + r, y + h - r, r, 90, 180)
    p.L(x, y + r).arc(x + r, y + r, r, 180, 270)
    p.Z()
    return p

# ---------------------------------------------------------------- araç konturları
# Her araç TEK kapalı kontur (lazer dış çizgiden keser). Detaylar baskıda.

def kontur_balon():
    p = Yol()
    p.M(24, 26)                                      # sol orta
    p.C(24, 12, 32, 8, 43, 8)                        # sol üst
    p.C(54, 8, 62, 12, 62, 26)                       # sağ üst
    p.C(62, 34, 55, 39, 50, 43)                      # sağa incelme
    p.L(50, 48).L(36, 48).L(36, 43)                  # sepet
    p.C(31, 39, 24, 34, 24, 26)                      # sola incelme
    p.Z()
    return p


def kontur_ucak():
    p = Yol()
    p.M(94, 18).L(106, 18)                           # kuyruk üstü
    p.C(112, 18, 115, 23, 119, 26.5)                 # kuyruktan gövdeye
    p.L(154, 26.5)
    p.C(168, 26.5, 176, 29, 178, 33.5)               # burun üst
    p.C(176, 38, 168, 40, 154, 40)                   # burun alt
    p.L(148, 40)
    p.L(136, 50).L(112, 50).L(121, 40)               # kanat
    p.L(107, 40)
    p.C(100, 40, 96, 38, 94, 34)                     # kuyruk altı
    p.Z()
    return p


def kontur_helikopter():
    p = Yol()
    p.M(225, 14).L(279, 14)
    p.arc(279, 17, 3, -90, 90)                       # pervane sağ ucu
    p.L(255, 20).L(255, 26)                          # mil sağ
    p.C(266, 26.5, 272, 31, 273, 36)                 # burun üst
    p.C(272, 43, 265, 48, 256, 48)                   # burun alt
    p.L(240, 48)
    p.C(233, 48, 228, 44, 228, 42)                   # karın
    p.L(228, 38).L(214, 38).L(208, 38)               # kuyruk altı
    p.L(208, 22).L(214, 24).L(214, 30)               # kuyruk dikey kanat
    p.L(228, 30).L(228, 26).L(247, 26)               # kuyruk üstü -> gövde
    p.L(247, 20).L(225, 20)                          # mil sol
    p.arc(225, 17, 3, 90, 270)                       # pervane sol ucu
    p.Z()
    return p


def kontur_traktor():
    p = Yol()
    p.M(18, 104).L(40, 104)                          # kaput üstü
    p.L(46, 92)                                      # ön cam eğimi
    p.C(47, 88.5, 49, 88, 52, 88)                    # kabin ön köşe
    p.L(66, 88)
    p.C(70, 88, 72, 89.5, 72, 93)                    # kabin arka köşe
    p.L(72, 100)
    p.L(74.5, 106)                                   # arka tekere iniş
    p.arc(60, 113, 15, -25, 205)                     # BÜYÜK arka teker
    p.L(38.6, 112.4)
    p.arc(30, 119, 9, -47, 215)                      # küçük ön teker
    p.L(18, 112)
    p.Z()
    return p


def kontur_itfaiye():
    p = Yol()
    p.M(94, 96).L(134, 96)                           # kasa üstü
    p.L(134, 101).L(140, 101)                        # kasa-kabin basamağı
    p.L(151, 101)
    p.L(158, 109)                                    # ön cam eğimi
    p.C(159.5, 110.5, 160, 112, 160, 114)
    p.L(160, 122).L(152.5, 122)
    p.arc(146.5, 122, 6, 0, 180)                     # ön teker
    p.L(112.5, 122)
    p.arc(106.5, 122, 6, 0, 180)                     # arka teker
    p.L(94, 122)
    p.Z()
    return p


def kontur_araba():
    p = Yol()
    p.M(184, 112).L(188, 111)
    p.C(190, 104.5, 193, 103, 197, 103)              # tavan ön
    p.L(209, 103)
    p.C(213, 103, 216, 104.5, 218, 111)              # tavan arka
    p.L(222, 112)
    p.C(225, 113, 226, 115, 226, 117)
    p.L(226, 122).L(220.5, 122)
    p.arc(215, 122, 5.5, 0, 180)                     # arka teker
    p.L(196.5, 122)
    p.arc(191, 122, 5.5, 0, 180)                     # ön teker
    p.L(178, 122).L(178, 117)
    p.C(178, 114.5, 180, 113, 184, 112)
    p.Z()
    return p


def kontur_otobus():
    p = Yol()
    p.M(245, 96).L(305, 96)
    p.arc(305, 101, 5, -90, 0)                       # sağ üst köşe
    p.L(310, 118)
    p.arc(306, 118, 4, 0, 90)                        # sağ alt köşe
    p.L(300.5, 122)
    p.arc(294.5, 122, 6, 0, 180)                     # ön teker
    p.L(262.5, 122)
    p.arc(256.5, 122, 6, 0, 180)                     # arka teker
    p.L(244, 122)
    p.arc(244, 118, 4, 90, 180)                      # sol alt köşe
    p.L(240, 101)
    p.arc(245, 101, 5, 180, 270)                     # sol üst köşe
    p.Z()
    return p


def kontur_yelkenli():
    p = Yol()
    p.M(46, 158).L(52, 158)
    p.C(56, 151, 61, 143, 66, 138)                   # ana yelken yatay kenarı
    p.L(66, 158)                                     # ana yelken arka (direk) kenarı
    p.L(71, 158).L(71, 144)                          # flok yelken ön kenarı
    p.C(78, 147, 87, 153, 93, 158)                   # flok eğimi
    p.L(100, 158)
    p.L(92, 170).L(54, 170)                          # gövde altı
    p.Z()
    return p


def kontur_feribot():
    p = Yol()
    p.M(192, 158).L(208, 158).L(208, 150)
    p.L(232, 150).L(232, 142).L(244, 142).L(244, 150)  # baca
    p.L(268, 150).L(268, 158)
    p.L(290, 158)
    p.L(280, 170).L(202, 170)
    p.Z()
    return p


PARCALAR = [
    ("balon",      kontur_balon(),      "hava"),
    ("ucak",       kontur_ucak(),       "hava"),
    ("helikopter", kontur_helikopter(), "hava"),
    ("traktor",    kontur_traktor(),    "kara"),
    ("itfaiye",    kontur_itfaiye(),    "kara"),
    ("araba",      kontur_araba(),      "kara"),
    ("otobus",     kontur_otobus(),     "kara"),
    ("yelkenli",   kontur_yelkenli(),   "deniz"),
    ("feribot",    kontur_feribot(),    "deniz"),
]

# ---------------------------------------------------------------- doğrulama
def dogrula():
    hatalar = []
    kutular = {}
    for ad, yol, _ in PARCALAR:
        kutular[ad] = yol.bbox()
    for ad, (x0, y0, x1, y1) in kutular.items():
        if x0 < MIN_EDGE or y0 < MIN_EDGE or x1 > W - MIN_EDGE or y1 > H - MIN_EDGE:
            hatalar.append(f"{ad}: dış kenara {MIN_EDGE} mm'den yakın "
                           f"(bbox {x0:.1f},{y0:.1f} – {x1:.1f},{y1:.1f})")
    adlar = list(kutular)
    for i in range(len(adlar)):
        for j in range(i + 1, len(adlar)):
            a, b = kutular[adlar[i]], kutular[adlar[j]]
            dx = max(a[0] - b[2], b[0] - a[2], 0)
            dy = max(a[1] - b[3], b[1] - a[3], 0)
            if dx == 0 and dy == 0:
                hatalar.append(f"{adlar[i]} ile {adlar[j]} ÇAKIŞIYOR")
            elif max(dx, dy) < MIN_GAP:
                hatalar.append(f"{adlar[i]}–{adlar[j]} arası {max(dx, dy):.1f} mm "
                               f"(en az {MIN_GAP} mm olmalı)")
    return hatalar

# ---------------------------------------------------------------- baskı deseni (SVG)
def _el(ad, **attr):
    icerik = attr.pop("icerik", None)
    s = "<" + ad + "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attr.items())
    return s + (f">{icerik}</{ad}>" if icerik is not None else "/>")


def _bulut(x, y, olcek=1.0):
    e = []
    for dx, dy, r in [(0, 0, 5), (5, -2.5, 6), (11, 0, 5), (5.5, 2, 5.5)]:
        e.append(_el("circle", cx=x + dx * olcek, cy=y + dy * olcek,
                     r=r * olcek, fill=C["bulut"], opacity="0.95"))
    return e


def _agac(x, taban, r=6.5):
    return [
        _el("rect", x=x - 1.5, y=taban - 8, width=3, height=8, fill=C["govde_agac"]),
        _el("circle", cx=x, cy=taban - 11, r=r, fill=C["yaprak"]),
    ]


def sahne_svg(dis_cizgili=True):
    """Baskı deseninin SVG parça listesi (0,0 – 320,180 uzayında)."""
    e = []
    # --- fon bantları (taşma payı için her yöne 6 mm uzatılır, kırpma dışarıda)
    e.append(_el("rect", x=-6, y=-6, width=W + 12, height=70, fill=C["gok"]))
    e.append(_el("rect", x=-6, y=64, width=W + 12, height=28, fill=C["cim"]))
    e.append(_el("rect", x=-6, y=92, width=W + 12, height=44, fill=C["yol"]))
    e.append(_el("rect", x=-6, y=136, width=W + 12, height=50, fill=C["deniz"]))
    # kaldırım şeritleri
    e.append(_el("rect", x=-6, y=92, width=W + 12, height=2.5, fill=C["kaldirim"]))
    e.append(_el("rect", x=-6, y=133.5, width=W + 12, height=2.5, fill=C["kaldirim"]))
    # yol çizgileri
    x = -4
    while x < W + 6:
        e.append(_el("rect", x=x, y=112.6, width=11, height=2.8, rx=1.2,
                     fill=C["yol_cizgi"], opacity="0.9"))
        x += 26
    # güneş
    e.append(_el("circle", cx=303, cy=15, r=8.5, fill=C["gunes"]))
    for i in range(8):
        a = math.radians(i * 45)
        x1, y1 = 303 + 11 * math.cos(a), 15 + 11 * math.sin(a)
        x2, y2 = 303 + 15 * math.cos(a), 15 + 15 * math.sin(a)
        e.append(_el("line", x1=x1, y1=y1, x2=x2, y2=y2, stroke=C["gunes"],
                     stroke_width=2.2, stroke_linecap="round"))
    # bulutlar (parça alanlarının dışında)
    e += _bulut(70, 15)
    e += _bulut(190, 32, 0.8)
    e += _bulut(288, 40, 0.7)
    # çimen dekoru: ağaçlar + ahır + yel değirmeni (parça alanlarının dışında)
    e += _agac(96, 90)
    e += _agac(116, 88, 5.5)
    # ahır
    e.append(_el("path", d="M 136 90 L 136 74 L 152 66 L 168 74 L 168 90 Z",
                 fill="#D9534F"))
    e.append(_el("path", d="M 133 75.5 L 152 66 L 171 75.5 L 168 74 L 152 68 L 136 74 Z",
                 fill="#A63B31"))
    e.append(_el("rect", x=147, y=79, width=10, height=11, fill="#8B3A32"))
    e.append(_el("rect", x=149, y=81, width=6, height=9, fill="#5E2622"))
    e += _agac(186, 89)
    # yel değirmeni
    e.append(_el("path", d="M 262 90 L 264.5 70 L 271.5 70 L 274 90 Z", fill="#F2F5F7"))
    for a0 in (20, 110, 200, 290):
        a = math.radians(a0)
        e.append(_el("line", x1=268, y1=70, x2=268 + 13 * math.cos(a),
                     y2=70 + 13 * math.sin(a), stroke="#8B5E3C",
                     stroke_width=2.4, stroke_linecap="round"))
    e.append(_el("circle", cx=268, cy=70, r=2.2, fill="#8B5E3C"))
    e += _agac(298, 90, 5)
    # dalgalar
    for (wx, wy) in [(30, 148), (120, 145), (160, 162), (30, 168), (250, 178),
                     (110, 176), (300, 150), (210, 139)]:
        e.append(_el("path", d=f"M {wx} {wy} q 5 -3.5 10 0 q 5 3.5 10 0",
                     fill="none", stroke=C["dalga"], stroke_width=1.8,
                     stroke_linecap="round"))
    # --- araç dolguları + detayları
    e += arac_detaylari()
    # --- parça dış çizgileri (kalın, sevimli kontur — kesim payını da gizler)
    if dis_cizgili:
        for _, yol, _ in PARCALAR:
            e.append(_el("path", d=yol.svg(), fill="none", stroke=C["dis_cizgi"],
                         stroke_width=1.6, stroke_linejoin="round"))
    return e


def arac_detaylari():
    e = []
    # BALON: şeritler
    b = kontur_balon()
    e.append(_el("path", d=b.svg(), fill=C["balon1"]))
    e.append(f'<clipPath id="klipbalon"><path d="{b.svg()}"/></clipPath>')
    e.append(_el("path", d="M 36 8 C 32 20 32 32 37 44 L 43 46 C 38 32 38 18 43 8 Z",
                 fill=C["balon2"], clip_path="url(#klipbalon)"))
    e.append(_el("path", d="M 50 8 C 54 20 54 32 49 44 L 43 46 C 48 32 48 18 43 8 Z",
                 fill=C["balon3"], clip_path="url(#klipbalon)"))
    e.append(_el("rect", x=36, y=42, width=14, height=6.5, fill=C["sepet"],
                 clip_path="url(#klipbalon)"))
    # UÇAK
    u = kontur_ucak()
    e.append(_el("path", d=u.svg(), fill=C["ucak"]))
    e.append(f'<clipPath id="klipucak"><path d="{u.svg()}"/></clipPath>')
    e.append(_el("path", d="M 94 18 L 106 18 C 112 18 115 23 119 26.5 L 119 34 L 94 34 Z",
                 fill=C["ucak_aksan"], clip_path="url(#klipucak)"))
    e.append(_el("path", d="M 148 40 L 136 50 L 112 50 L 121 40 Z",
                 fill=C["ucak_aksan"], clip_path="url(#klipucak)", opacity="0.92"))
    e.append(_el("path", d="M 154 27 C 166 27 174 29.5 177 33.5 L 160 33.5 L 154 29 Z",
                 fill=C["cam"], clip_path="url(#klipucak)"))
    for wx in (126, 134, 142, 150):
        e.append(_el("circle", cx=wx, cy=31.5, r=1.7, fill=C["cam"]))
    # HELİKOPTER
    h = kontur_helikopter()
    e.append(_el("path", d=h.svg(), fill=C["heli"]))
    e.append(f'<clipPath id="klipheli"><path d="{h.svg()}"/></clipPath>')
    e.append(_el("rect", x=222, y=14, width=60, height=6, fill=C["heli_koyu"],
                 clip_path="url(#klipheli)"))
    e.append(_el("rect", x=208, y=30, width=20, height=8, fill=C["heli_koyu"],
                 clip_path="url(#klipheli)"))
    e.append(_el("path", d="M 256 27 C 265 27.5 271 32 272 36 L 258 36 Z",
                 fill=C["cam"], clip_path="url(#klipheli)"))
    e.append(_el("circle", cx=244, cy=37, r=4.2, fill=C["cam"]))
    # TRAKTÖR
    t = kontur_traktor()
    e.append(_el("path", d=t.svg(), fill=C["traktor"]))
    e.append(f'<clipPath id="kliptraktor"><path d="{t.svg()}"/></clipPath>')
    e.append(_el("rect", x=18, y=100, width=26, height=12, fill=C["traktor_koyu"],
                 clip_path="url(#kliptraktor)"))
    e.append(_el("path", d="M 48 92 L 66 92 L 66 104 L 52 104 Z", fill=C["cam"],
                 clip_path="url(#kliptraktor)"))
    for cx, cy, r in [(60, 113, 15), (30, 119, 9)]:
        e.append(_el("circle", cx=cx, cy=cy, r=r, fill=C["teker"],
                     clip_path="url(#kliptraktor)"))
        e.append(_el("circle", cx=cx, cy=cy, r=r * 0.45, fill=C["jant"]))
    # İTFAİYE
    f = kontur_itfaiye()
    e.append(_el("path", d=f.svg(), fill=C["itfaiye"]))
    e.append(f'<clipPath id="klipitfaiye"><path d="{f.svg()}"/></clipPath>')
    e.append(_el("rect", x=94, y=96, width=40, height=5, fill=C["itfaiye_koyu"],
                 clip_path="url(#klipitfaiye)"))
    e.append(_el("path", d="M 151 101 L 158 109 C 159.5 110.5 160 112 160 114 L 160 116 L 148 116 L 148 101 Z",
                 fill=C["itfaiye_koyu"], clip_path="url(#klipitfaiye)"))
    e.append(_el("path", d="M 150.5 103 L 155.8 109.5 L 150.5 109.5 Z", fill=C["cam"]))
    # merdiven
    e.append(_el("rect", x=98, y=98.2, width=34, height=1.6, fill=C["merdiven"]))
    e.append(_el("rect", x=98, y=102.4, width=34, height=1.6, fill=C["merdiven"]))
    for mx in range(101, 131, 5):
        e.append(_el("rect", x=mx, y=99.5, width=1.4, height=3.2, fill=C["merdiven"]))
    e.append(_el("rect", x=96, y=106, width=42, height=9, rx=1.5, fill="#F2F5F7"))
    e.append(_el("text", x=117, y=112.8, icerik="İTFAİYE", fill=C["itfaiye"],
                 font_size="5.2", font_family="sans-serif", font_weight="bold",
                 text_anchor="middle"))
    for cx in (106.5, 146.5):
        e.append(_el("circle", cx=cx, cy=122, r=6, fill=C["teker"]))
        e.append(_el("circle", cx=cx, cy=122, r=2.6, fill=C["jant"]))
    # ARABA
    a = kontur_araba()
    e.append(_el("path", d=a.svg(), fill=C["araba"]))
    e.append(f'<clipPath id="kliparaba"><path d="{a.svg()}"/></clipPath>')
    e.append(_el("path", d="M 190.5 111 C 192 105.5 194.5 104.5 197.5 104.5 L 202 104.5 L 202 111 Z",
                 fill=C["cam"]))
    e.append(_el("path", d="M 204 104.5 L 208.5 104.5 C 212 104.5 214 105.5 215.5 111 L 204 111 Z",
                 fill=C["cam"]))
    e.append(_el("rect", x=178, y=115, width=48, height=3, fill=C["araba_koyu"],
                 clip_path="url(#kliparaba)"))
    for cx in (191, 215):
        e.append(_el("circle", cx=cx, cy=122, r=5.5, fill=C["teker"]))
        e.append(_el("circle", cx=cx, cy=122, r=2.4, fill=C["jant"]))
    # OTOBÜS
    o = kontur_otobus()
    e.append(_el("path", d=o.svg(), fill=C["otobus"]))
    e.append(f'<clipPath id="klipotobus"><path d="{o.svg()}"/></clipPath>')
    for wx in (246, 261, 276):
        e.append(_el("rect", x=wx, y=101, width=11, height=8, rx=1.5, fill=C["cam"]))
    e.append(_el("path", d="M 300 101 L 306.5 101 C 308.5 103 309.3 106 309.6 109 L 300 109 Z",
                 fill=C["cam"], clip_path="url(#klipotobus)"))
    e.append(_el("rect", x=240, y=113, width=70, height=3, fill=C["otobus_koyu"],
                 clip_path="url(#klipotobus)"))
    for cx in (256.5, 294.5):
        e.append(_el("circle", cx=cx, cy=122, r=6, fill=C["teker"]))
        e.append(_el("circle", cx=cx, cy=122, r=2.6, fill=C["jant"]))
    # YELKENLİ
    y = kontur_yelkenli()
    e.append(_el("path", d=y.svg(), fill=C["yelken"]))
    e.append(f'<clipPath id="klipyelkenli"><path d="{y.svg()}"/></clipPath>')
    e.append(_el("path", d="M 46 158 L 100 158 L 92 170 L 54 170 Z", fill=C["tekne"]))
    e.append(_el("rect", x=66, y=138, width=2.2, height=20, fill=C["direk"]))
    e.append(_el("path", d="M 71 144 C 78 147 87 153 93 158 L 71 158 Z",
                 fill="#FFE9A8", clip_path="url(#klipyelkenli)"))
    # FERİBOT
    fb = kontur_feribot()
    e.append(_el("path", d=fb.svg(), fill=C["feribot"]))
    e.append(f'<clipPath id="klipferibot"><path d="{fb.svg()}"/></clipPath>')
    e.append(_el("path", d="M 192 158 L 290 158 L 284 165.5 L 197 165.5 Z",
                 fill=C["feribot_alt"], clip_path="url(#klipferibot)"))
    e.append(_el("path", d="M 197 165.5 L 284 165.5 L 280 170 L 202 170 Z",
                 fill="#274F8F", clip_path="url(#klipferibot)"))
    e.append(_el("rect", x=232, y=142, width=12, height=8, fill=C["baca"]))
    e.append(_el("rect", x=232, y=142, width=12, height=2.5, fill="#B82323"))
    for wx in (214, 226, 238, 250):
        e.append(_el("circle", cx=wx + 3, cy=154, r=2.2, fill=C["cam"]))
    return e

# ---------------------------------------------------------------- SVG dosyaları
def svg_belge(w_mm, h_mm, icerik, arkaplan=None):
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm}mm" height="{h_mm}mm" '
         f'viewBox="0 0 {w_mm} {h_mm}">']
    if arkaplan:
        s.append(_el("rect", x=0, y=0, width=w_mm, height=h_mm, fill=arkaplan))
    s += icerik
    s.append("</svg>")
    return "\n".join(s)


def uret_baski_svg():
    """UV baskı dosyası: 324x184 (her kenardan 2 mm taşma)."""
    icerik = [f'<g transform="translate({BLEED},{BLEED})">'] + sahne_svg() + ["</g>"]
    return svg_belge(W + 2 * BLEED, H + 2 * BLEED, icerik)


def uret_kalip_svg():
    """UV hizalama kalıbı: 320x180, yalnız kesim konturları (kırmızı ince çizgi)."""
    icerik = []
    cerceve = yuvarlak_dikdortgen(0, 0, W, H, CORNER_R)
    icerik.append(_el("path", d=cerceve.svg(), fill="none", stroke="#FF0000",
                      stroke_width=0.25))
    for _, yol, _ in PARCALAR:
        icerik.append(_el("path", d=yol.svg(), fill="none", stroke="#FF0000",
                          stroke_width=0.25))
    icerik.append(_el("text", x=6, y=177.2, icerik="ARAÇLAR PUZZLE 320x180 – UV KALIP (1:1)",
                      fill="#888888", font_size="3", font_family="sans-serif"))
    return svg_belge(W, H, icerik)

# ---------------------------------------------------------------- DXF
def uret_dxf(dosya):
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4  # milimetre
    msp = doc.modelspace()
    doc.layers.add("UST_KATMAN_KESIM", color=1)   # kırmızı
    doc.layers.add("ALT_KATMAN_KESIM", color=5)   # mavi
    doc.layers.add("YAZI", color=8)               # gri, kesilmez

    def poli(yol, dx, katman):
        # y ekseni: SVG aşağı -> DXF yukarı
        pts, son = [], None
        for (x, y) in yol.pts:
            q = (round(x + dx, 3), round(H - y, 3))
            if q != son:
                pts.append(q)
                son = q
        if pts[0] == pts[-1]:
            pts.pop()
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": katman})

    # ÜST KATMAN (cepli): çerçeve + araç konturları
    poli(yuvarlak_dikdortgen(0, 0, W, H, CORNER_R), 0, "UST_KATMAN_KESIM")
    for _, yol, _ in PARCALAR:
        poli(yol, 0, "UST_KATMAN_KESIM")
    # ALT KATMAN (düz taban)
    dx_alt = W + 15
    poli(yuvarlak_dikdortgen(0, 0, W, H, CORNER_R), dx_alt, "ALT_KATMAN_KESIM")

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
        for h in hatalar:
            print("  •", h)
    else:
        print("Yerleşim doğrulandı: tüm parçalar aralık kurallarına uygun.")

    os.makedirs(OUT, exist_ok=True)
    import cairosvg

    baski = uret_baski_svg()
    kalip = uret_kalip_svg()

    cairosvg.svg2pdf(bytestring=baski.encode(), write_to=f"{OUT}/araclar_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=kalip.encode(), write_to=f"{OUT}/araclar_uv_kalip.pdf")
    cairosvg.svg2png(bytestring=baski.encode(), write_to=f"{OUT}/araclar_onizleme.png",
                     output_width=1944)  # 324 mm -> ~150 dpi
    cairosvg.svg2png(bytestring=kalip.encode(), write_to=f"{OUT}/araclar_kalip_onizleme.png",
                     output_width=1920)
    uret_dxf(f"{OUT}/araclar_lazer_kesim.dxf")

    for ad, yol, sinif in PARCALAR:
        x0, y0, x1, y1 = yol.bbox()
        print(f"  parça {ad:<11} ({sinif:<5}) {x1-x0:5.1f} x {y1-y0:5.1f} mm")
    print("Tamamlandı ->", OUT)


if __name__ == "__main__":
    main()
