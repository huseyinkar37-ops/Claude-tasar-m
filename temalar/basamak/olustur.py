# -*- coding: utf-8 -*-
"""
Çocuklar için "El Yıkama Basamağı" üretim dosyalarını oluşturur.

Ürün: 15 mm huş kontrplaktan, VİDASIZ geçmeli (kertme-dil / mortise-tenon)
iki basamaklı tabure. Alt basamak (150 mm) tırmanmak, üst platform (300 mm)
lavaboya erişip el yıkamak içindir. Bütün parçalar tek levhadan kesilir ve
tutkalla birbirine geçer.

Çıktılar (cikti/ klasörüne):
  1. basamak_lazer_kesim.dxf   – CNC / lazer kesim (tüm parçalar levhaya dizili)
  2. basamak_teknik.png        – Teknik çizim: yan + ön görünüş, ölçüler
  3. basamak_montaj.png        – Monte edilmiş 3B (kabinet projeksiyon) görünüm
  4. basamak_kesim_yerlesim.png – Levha üstü parça dizilimi (DXF'in birebir önizlemesi)
  5. README.md güncel değilse elle yazılır (malzeme + montaj)

Geometri: tüm kertikler (mortise) ve diller (tenon) TEK sayısal kaynaktan
türetilir; böylece parça üstündeki dil ile yan panelindeki kertik asla
birbirinden ayrışamaz — tıpkı puzzle temalarındaki baskı/kesim eşleşmesi gibi.

Çalıştırma:  python3 olustur.py
"""
import math
import os

from shapely.affinity import translate as s_tasi
from shapely.geometry import Point, Polygon, box as s_kutu
from shapely.ops import unary_union

# ------------------------------------------------------------------ ölçüler (mm)
KALINLIK   = 15.0     # huş kontrplak kalınlığı
GENISLIK   = 380.0    # taburenin toplam eni (dil uçları dış yüzeye taşarak geçer)
DERINLIK   = 360.0    # ön-arka taban ayak izi (devrilmezlik için yükseklikten büyük)
H1         = 150.0    # alt basamak üst yüzey yüksekliği
H2         = 300.0    # üst platform üst yüzey yüksekliği
ALT_DERIN  = 150.0    # alt basamağın ön-arka derinliği (x: 0..150)
UST_DERIN  = DERINLIK - ALT_DERIN   # üst platform derinliği (x: 150..360 = 210)
KUSAK_H    = 60.0     # ön kuşak (parmak/toe-kick) yüksekliği

KOSE_R     = 12.0     # açıkta kalan dış köşe yumuşatma (çocuk güvenliği)
GOVDE_R    = 6.0      # yatay/dikey parça gövde köşe yumuşatma
DUVAR_MIN  = 8.0      # kertik ile kertik / kenar arası en az ahşap duvarı
DIL_MIN    = 40.0     # bir dilin en az uzunluğu (bağlantı sağlamlığı)

# Kertik = dil ile birebir; lazer/CNC kerf'i (~0.15 mm) sıkı-tutkallı geçme verir.
KLASOR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(KLASOR, "cikti")

# ------------------------------------------------------------ tek kaynak: geçmeler
# Her yatay/dikey parça yan panele şu "diller" (tab) ile geçer. Aynı sayılar hem
# parçanın dilini hem yan panelin kertiğini üretir.
#
# yon='y'  -> yatay parça (basamak): yan panelde kertik y-aralığı = SLOT (kalınlık),
#            diller x (derinlik) boyunca => TABS = [(x0,x1), ...]
# yon='x'  -> dikey parça (riser/arka/kuşak): kertik x-aralığı = SLOT, diller y boyunca.
# acik=True  -> basamak, yan panelin üst kenarına açık çentik olarak oturur
#              (üst yüzey flush; kertik üstten açıktır) — kenara değmesi normaldir.
GECME = {
    "alt_basamak": dict(yon="y", slot=(H1 - KALINLIK, H1),
                        tabs=[(20, 68), (82, 130)],
                        derinlik=ALT_DERIN, g0=0.0, acik=True),   # global x = g0 + yerel v
    "ust_platform": dict(yon="y", slot=(H2 - KALINLIK, H2),
                        tabs=[(180, 236), (266, 322)],
                        derinlik=UST_DERIN, g0=ALT_DERIN, acik=True),
    "riser": dict(yon="x", slot=(ALT_DERIN + 10, ALT_DERIN + 10 + KALINLIK),
                        tabs=[(170, 213), (235, 278)],
                        derinlik=H2 - H1 - KALINLIK, g0=H1, acik=False),  # global y = g0 + yerel v
    "arka": dict(yon="x", slot=(DERINLIK - 30, DERINLIK - 30 + KALINLIK),
                        tabs=[(28, 80), (124, 176), (220, 278)],
                        derinlik=H2, g0=0.0, acik=False),
    "on_kusak": dict(yon="x", slot=(12, 12 + KALINLIK),
                        tabs=[(15, 55)],
                        derinlik=KUSAK_H, g0=0.0, acik=False),
}

# ------------------------------------------------------------------ geometri araç
def yuv_kutu(x0, y0, x1, y1, r=0.0):
    """Köşeleri r ile yuvarlatılmış dikdörtgen (r>0)."""
    if r <= 0:
        return s_kutu(x0, y0, x1, y1)
    return s_kutu(x0 + r, y0 + r, x1 - r, y1 - r).buffer(r, quad_segs=16)


def kose_yumusat(poly, r):
    """Dışbükey köşeleri (açık kenarlar) r ile yuvarlat; kertik/dil dik kalır
    çünkü bu yalnız dış halkaya uygulanır sonra kertikler ayrıca çıkarılır."""
    return poly.buffer(-r, join_style=1).buffer(r, join_style=1)


# ------------------------------------------------------------------ yan panel
def yan_panel():
    """Merdiven profilli yan panel + tüm kertikler (delik olarak)."""
    profil = Polygon([
        (0, 0), (DERINLIK, 0), (DERINLIK, H2),
        (ALT_DERIN, H2), (ALT_DERIN, H1), (0, H1),
    ])
    # köşeleri yumuşat (hem dışbükey basamak burunları hem içbükey iç köşe)
    dis = profil.buffer(KOSE_R, join_style=1).buffer(-2 * KOSE_R, join_style=1) \
                .buffer(KOSE_R, join_style=1)
    dis = Polygon(dis.exterior)
    acik, kapali = [], []
    for ad in GECME:
        (acik if GECME[ad]["acik"] else kapali).extend(yan_kertik(ad))
    if acik:                                  # basamak çentikleri: üst kenardan çıkar
        uzat = [s_kutu(a.bounds[0], a.bounds[1], a.bounds[2], a.bounds[3] + 3.0)
                for a in acik]               # üste 3 mm taşır ki temiz açık çentik olsun
        dis = dis.difference(unary_union(uzat))
        if dis.geom_type == "MultiPolygon":
            dis = max(dis.geoms, key=lambda p: p.area)
    return Polygon(dis.exterior, [list(k.exterior.coords) for k in kapali])


def yan_kertik(ad):
    """ad'lı parçanın yan paneldeki kertik dikdörtgenleri."""
    g = GECME[ad]
    s0, s1 = g["slot"]
    kutular = []
    for a0, a1 in g["tabs"]:
        if g["yon"] == "y":         # yatay parça: kertik x=[a0,a1], y=slot
            kutular.append(s_kutu(a0, s0, a1, s1))
        else:                        # dikey parça: kertik x=slot, y=[a0,a1]
            kutular.append(s_kutu(s0, a0, s1, a1))
    return kutular


# ------------------------------------------------- yatay/dikey (dilli) parçalar
def dilli_parca(ad):
    """Genişlik boyunca uzanan, iki ucunda geçme dili olan düz parça."""
    g = GECME[ad]
    derin = g["derinlik"]
    govde = yuv_kutu(KALINLIK, 0, GENISLIK - KALINLIK, derin, r=GOVDE_R)
    diller = []
    for a0, a1 in g["tabs"]:
        v0, v1 = a0 - g["g0"], a1 - g["g0"]   # global konumu yerel v'ye taşı
        diller.append(s_kutu(0, v0, KALINLIK, v1))
        diller.append(s_kutu(GENISLIK - KALINLIK, v0, GENISLIK, v1))
    poly = unary_union([govde] + diller)
    if poly.geom_type == "MultiPolygon":
        poly = max(poly.geoms, key=lambda p: p.area)
    delikler = []
    if ad == "arka":     # taşıma için el deliği (üst orta)
        from shapely.affinity import scale as s_olcek
        cx, cy = GENISLIK / 2, derin - 55
        el = s_olcek(Point(cx, cy).buffer(1.0, quad_segs=24), 48, 18, origin=(cx, cy))
        delikler = [list(el.exterior.coords)]
    return Polygon(poly.exterior, delikler)


# ------------------------------------------------------------ parça kataloğu
def parcalar():
    """(ad, poly, adet, etiket) listesi — kesilecek tüm benzersiz parçalar."""
    return [
        ("yan",          yan_panel(),            2, "YAN PANEL (x2)"),
        ("ust_platform", dilli_parca("ust_platform"), 1, "UST PLATFORM (x1)"),
        ("arka",         dilli_parca("arka"),        1, "ARKA PANEL (x1)"),
        ("alt_basamak",  dilli_parca("alt_basamak"), 1, "ALT BASAMAK (x1)"),
        ("riser",        dilli_parca("riser"),       1, "DIKEY RISER (x1)"),
        ("on_kusak",     dilli_parca("on_kusak"),    1, "ON KUSAK (x1)"),
    ]


# ------------------------------------------------------------------ doğrulama
def dogrula():
    hatalar = []
    # 1) devrilme payı: taban derinliği yükseklikten büyük olmalı
    if DERINLIK <= H2:
        hatalar.append(f"Devrilme riski: derinlik {DERINLIK} <= yukseklik {H2}")
    # 2) dil uzunlukları
    for ad, g in GECME.items():
        for a0, a1 in g["tabs"]:
            if a1 - a0 < DIL_MIN:
                hatalar.append(f"{ad}: dil {a1-a0:.0f} mm < {DIL_MIN:.0f} mm")
    # 3) yan paneldeki tüm geçmeler arası ahşap duvarı (açık çentikler dahil)
    rects = []
    for ad in GECME:
        for r in yan_kertik(ad):
            rects.append((ad, r))
    for i, (ad_i, ki) in enumerate(rects):
        for j in range(i + 1, len(rects)):
            ad_j, kj = rects[j]
            d = ki.distance(kj)
            if d < DUVAR_MIN - 0.01:
                hatalar.append(f"gecme {ad_i}-{ad_j} arasi {d:.1f} mm (<{DUVAR_MIN})")
    # kapalı kertiklerin dış kenara mesafesi
    dis_ring = Polygon(yan_panel().exterior).exterior
    for ad in GECME:
        if GECME[ad]["acik"]:
            continue
        for k in yan_kertik(ad):
            d = k.distance(dis_ring)
            if d < DUVAR_MIN - 0.01:
                hatalar.append(f"kertik {ad} dis kenara {d:.1f} mm (<{DUVAR_MIN})")
    # 4) parça sığması: hiçbir dil parça derinliğini aşmasın
    for ad, g in GECME.items():
        for a0, a1 in g["tabs"]:
            v0, v1 = a0 - g["g0"], a1 - g["g0"]
            if v0 < -0.01 or v1 > g["derinlik"] + 0.01:
                hatalar.append(f"{ad}: dil ({v0:.0f},{v1:.0f}) derinlik {g['derinlik']:.0f} disinda")
    return hatalar


# ------------------------------------------------------------------ levha dizimi
SAC_MARJ = 20.0
SAC_ARA = 15.0
SAC_EN = 1220.0     # standart huş kontrplak eni


def yerlesim():
    """Basit raf-paketleme: (ad, poly_yerlestirilmis, etiket, adet) döndürür.
    Her adet ayrı yerleştirilir."""
    ogeler = []
    for ad, poly, adet, etiket in parcalar():
        for k in range(adet):
            ogeler.append([ad, poly, f"{etiket}", k])
    # yüksekliğe göre azalan sırala (raf verimi)
    ogeler.sort(key=lambda o: -(o[1].bounds[3] - o[1].bounds[1]))
    yerlesmis = []
    x = SAC_MARJ
    y = SAC_MARJ
    raf_h = 0.0
    for ad, poly, etiket, k in ogeler:
        x0, y0, x1, y1 = poly.bounds
        w, h = x1 - x0, y1 - y0
        if x + w > SAC_EN - SAC_MARJ:      # yeni rafa geç
            x = SAC_MARJ
            y += raf_h + SAC_ARA
            raf_h = 0.0
        p = s_tasi(poly, x - x0, y - y0)
        yerlesmis.append((ad, p, etiket))
        x += w + SAC_ARA
        raf_h = max(raf_h, h)
    sac_boy = y + raf_h + SAC_MARJ
    return yerlesmis, sac_boy


# ------------------------------------------------------------------ DXF çıktı
def uret_dxf(dosya):
    import ezdxf
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4        # milimetre
    msp = doc.modelspace()
    doc.layers.add("KESIM", color=1)    # tüm kesim konturları (dış + kertik/delik)
    doc.layers.add("SAC", color=8)      # levha sınırı (kesilmez, referans)
    doc.layers.add("YAZI", color=5)

    yerlesmis, sac_boy = yerlesim()

    def poli(ring, layer):
        pts = [(round(x, 3), round(y, 3)) for x, y in list(ring.coords)[:-1]]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    # levha sınırı (referans)
    msp.add_lwpolyline([(0, 0), (SAC_EN, 0), (SAC_EN, sac_boy), (0, sac_boy)],
                       close=True, dxfattribs={"layer": "SAC"})

    for ad, poly, etiket in yerlesmis:
        poli(poly.exterior, "KESIM")
        for ic in poly.interiors:            # kertikler + el deliği
            poli(ic, "KESIM")
        x0, y0, x1, y1 = poly.bounds
        msp.add_text(etiket, dxfattribs={"layer": "YAZI", "height": 8}) \
           .set_placement((x0, y1 + 4))

    msp.add_text("15 mm hus kontrplak - EL YIKAMA BASAMAGI",
                 dxfattribs={"layer": "YAZI", "height": 12}).set_placement((0, sac_boy + 6))
    doc.saveas(dosya)
    return sac_boy


# ------------------------------------------------------------------ SVG yardımcı
def svg_belge(w, h, ic, arka="#ffffff"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.1f}mm" '
            f'height="{h:.1f}mm" viewBox="0 0 {w:.1f} {h:.1f}">'
            f'<rect width="{w:.1f}" height="{h:.1f}" fill="{arka}"/>'
            + "".join(ic) + "</svg>")


def yol(poly, dolgu, cizgi="#8a6a2f", kalin=0.6):
    def ring(coords):
        p = list(coords)
        d = f"M {p[0][0]:.2f} {p[0][1]:.2f} " + " ".join(
            f"L {x:.2f} {y:.2f}" for x, y in p[1:]) + " Z"
        return d
    d = ring(poly.exterior.coords)
    for i in poly.interiors:
        d += " " + ring(i.coords)
    return (f'<path d="{d}" fill="{dolgu}" fill-rule="evenodd" '
            f'stroke="{cizgi}" stroke-width="{kalin}"/>')


HUS = "#e9d4a6"
HUS_KOYU = "#d8bd85"
CIZGI = "#9c7b3f"


# ------------------------------------------------------- kesim yerleşim önizleme
def uret_kesim_svg():
    yerlesmis, sac_boy = yerlesim()
    ic = [f'<rect x="0" y="0" width="{SAC_EN}" height="{sac_boy}" '
          f'fill="#faf6ec" stroke="#c9c1ad" stroke-width="2"/>']
    for ad, poly, etiket in yerlesmis:
        ic.append(yol(poly, HUS, CIZGI, 0.8))
        x0, y0, x1, y1 = poly.bounds
        ic.append(f'<text x="{(x0+x1)/2:.1f}" y="{(y0+y1)/2:.1f}" '
                  f'font-size="11" fill="#6b5424" text-anchor="middle" '
                  f'font-family="sans-serif">{etiket}</text>')
    ic.append(f'<text x="{SAC_EN/2:.1f}" y="{sac_boy-8:.1f}" font-size="16" '
              f'fill="#6b5424" text-anchor="middle" font-family="sans-serif">'
              f'15 mm hus kontrplak - kesim yerlesimi ({SAC_EN:.0f} x {sac_boy:.0f} mm)</text>')
    return svg_belge(SAC_EN, sac_boy, ic, "#ffffff")


# --------------------------------------------------------------- teknik çizim
def uret_teknik_svg():
    M = 55.0                       # görünüşler arası boşluk
    ust = 45.0
    # yan görünüş profili
    profil = [(0, 0), (DERINLIK, 0), (DERINLIK, H2),
              (ALT_DERIN, H2), (ALT_DERIN, H1), (0, H1)]
    LP = 100.0                     # sol boşluk (ölçü yazıları için)
    W = LP + DERINLIK + M + GENISLIK + 40
    Ht = H2 + ust + 90

    def flip(pts, ox):    # y-yukarı -> ekran y-aşağı
        return [(ox + x, ust + (H2 - y)) for x, y in pts]

    ic = []
    # ---- yan görünüş
    ox = LP
    p = flip(profil, ox)
    d = f'M {p[0][0]:.1f} {p[0][1]:.1f} ' + " ".join(f'L {x:.1f} {y:.1f}' for x, y in p[1:]) + " Z"
    ic.append(f'<path d="{d}" fill="{HUS}" stroke="{CIZGI}" stroke-width="1.4"/>')
    # basamak yüzeyleri vurgusu
    for (xa, xb, yy) in [(0, ALT_DERIN, H1), (ALT_DERIN, DERINLIK, H2)]:
        (x1, y1) = (ox + xa, ust + (H2 - yy))
        (x2, y2) = (ox + xb, ust + (H2 - yy))
        ic.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                  f'stroke="#7a5c22" stroke-width="2.5"/>')

    def olcu_dik(x, ya, yb, yaz, ox_):   # dikey ölçü çizgisi (yükseklik)
        xa = ox_ + x
        y1 = ust + (H2 - ya)
        y2 = ust + (H2 - yb)
        ic.append(f'<line x1="{xa:.1f}" y1="{y1:.1f}" x2="{xa:.1f}" y2="{y2:.1f}" '
                  f'stroke="#444" stroke-width="0.6"/>')
        ic.append(f'<text x="{xa-4:.1f}" y="{(y1+y2)/2:.1f}" font-size="11" fill="#333" '
                  f'text-anchor="end" font-family="sans-serif">{yaz}</text>')

    olcu_dik(-16, 0, H1, "150", ox)
    olcu_dik(-42, 0, H2, "300 mm", ox)

    def olcu_yatay(y, xa, xb, yaz, ox_):
        yy = ust + (H2 - 0) + 16 + y
        x1 = ox_ + xa
        x2 = ox_ + xb
        ic.append(f'<line x1="{x1:.1f}" y1="{yy:.1f}" x2="{x2:.1f}" y2="{yy:.1f}" '
                  f'stroke="#444" stroke-width="0.6"/>')
        ic.append(f'<text x="{(x1+x2)/2:.1f}" y="{yy+13:.1f}" font-size="11" fill="#333" '
                  f'text-anchor="middle" font-family="sans-serif">{yaz}</text>')

    olcu_yatay(0, 0, ALT_DERIN, "150", ox)
    olcu_yatay(20, 0, DERINLIK, "360 mm (derinlik)", ox)
    ic.append(f'<text x="{ox+DERINLIK/2:.1f}" y="{ust-14:.1f}" font-size="13" '
              f'fill="#6b5424" text-anchor="middle" font-family="sans-serif" '
              f'font-weight="bold">YAN GORUNUS</text>')

    # ---- ön görünüş
    ox2 = LP + DERINLIK + M
    front = [(0, 0), (GENISLIK, 0), (GENISLIK, H2), (0, H2)]
    fp = [(ox2 + x, ust + (H2 - y)) for x, y in front]
    d2 = f'M {fp[0][0]:.1f} {fp[0][1]:.1f} ' + " ".join(f'L {x:.1f} {y:.1f}' for x, y in fp[1:]) + " Z"
    ic.append(f'<path d="{d2}" fill="{HUS}" stroke="{CIZGI}" stroke-width="1.4"/>')
    # yan panel kalınlıkları (iki kenarda 15 mm)
    for xx in [0, GENISLIK - KALINLIK]:
        ic.append(f'<rect x="{ox2+xx:.1f}" y="{ust:.1f}" width="{KALINLIK:.1f}" '
                  f'height="{H2:.1f}" fill="{HUS_KOYU}" stroke="{CIZGI}" stroke-width="1"/>')
    # basamak çizgileri
    for yy in [H1, H2]:
        y = ust + (H2 - yy)
        ic.append(f'<line x1="{ox2:.1f}" y1="{y:.1f}" x2="{ox2+GENISLIK:.1f}" y2="{y:.1f}" '
                  f'stroke="#7a5c22" stroke-width="2"/>')
    ic.append(f'<text x="{ox2+GENISLIK/2:.1f}" y="{ust-14:.1f}" font-size="13" '
              f'fill="#6b5424" text-anchor="middle" font-family="sans-serif" '
              f'font-weight="bold">ON GORUNUS</text>')
    # en ölçüsü
    yb = ust + H2 + 16
    ic.append(f'<line x1="{ox2:.1f}" y1="{yb:.1f}" x2="{ox2+GENISLIK:.1f}" y2="{yb:.1f}" '
              f'stroke="#444" stroke-width="0.6"/>')
    ic.append(f'<text x="{ox2+GENISLIK/2:.1f}" y="{yb+13:.1f}" font-size="11" fill="#333" '
              f'text-anchor="middle" font-family="sans-serif">380 mm (en)</text>')

    ic.append(f'<text x="{W/2:.1f}" y="{Ht-14:.1f}" font-size="14" fill="#6b5424" '
              f'text-anchor="middle" font-family="sans-serif" font-weight="bold">'
              f'EL YIKAMA BASAMAGI - 15 mm hus kontrplak</text>')
    return svg_belge(W, Ht, ic, "#ffffff")


# --------------------------------------------------------------- 3B montaj görünüm
def _golge(hexcol, f):
    r = int(hexcol[1:3], 16); g = int(hexcol[3:5], 16); b = int(hexcol[5:7], 16)
    r, g, b = (min(255, int(c * f)) for c in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def uret_montaj_svg():
    """Parçaları basit kutulara ayır, izometrik projeksiyonla painter's-algorithm
    (arkadan öne) çiz. Ön (Y=0) izleyiciye yakın; basamaklar ve rıht görünür."""
    D = DERINLIK
    W_ = GENISLIK

    def proj(X, Y, Z):                  # 30° izometrik; ön (Y=0) yakın olsun (Yw=D-Y)
        Yw = D - Y
        return (0.866 * (X - Yw), 0.5 * (X + Yw) - Z)

    # (ad, x0,x1, y0,y1, z0,z1, taban renk)
    kutular = [
        ("sol_alt",  0, KALINLIK,          0, D,              0, H1,   HUS),
        ("sol_ust",  0, KALINLIK,          H1, D,             H1, H2,  HUS),
        ("sag_alt",  W_ - KALINLIK, W_,    0, D,              0, H1,   HUS),
        ("sag_ust",  W_ - KALINLIK, W_,    H1, D,             H1, H2,  HUS),
        ("kusak",    KALINLIK, W_ - KALINLIK, 12, 27,          0, KUSAK_H, HUS_KOYU),
        ("alt_tread", KALINLIK, W_ - KALINLIK, 0, ALT_DERIN,   H1 - KALINLIK, H1, "#f2e2b8"),
        ("riser",    KALINLIK, W_ - KALINLIK, 160, 175,        H1, H2 - KALINLIK, HUS_KOYU),
        ("ust_tread", KALINLIK, W_ - KALINLIK, H1, D,          H2 - KALINLIK, H2, "#f2e2b8"),
        ("arka",     KALINLIK, W_ - KALINLIK, 330, 345,        0, H2,   HUS_KOYU),
    ]

    def yuzler(b):
        _, x0, x1, y0, y1, z0, z1, col = b
        # dünya y -> Yw = D-y ; yakın yüz = küçük y (ön). Görünür: üst(z1), ön(y0), sağ(x1)
        ust = [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        on = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)]
        sag = [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)]
        return [(ust, _golge(col, 1.0)), (sag, _golge(col, 0.74)), (on, _golge(col, 0.88))]

    # painter: kutuları merkez derinliğine göre sırala (arkadan öne)
    def anahtar(b):
        _, x0, x1, y0, y1, z0, z1, col = b
        cx, cy, cz = (x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2
        return (cx + (D - cy) + cz)     # büyük = yakın -> sonra çiz
    kutular.sort(key=anahtar)

    ic = []
    for b in kutular:
        for pts3, col in yuzler(b):
            p = [proj(*q) for q in pts3]
            d = f'M {p[0][0]:.2f} {p[0][1]:.2f} ' + " ".join(f'L {x:.2f} {y:.2f}' for x, y in p[1:]) + " Z"
            ic.append(f'<path d="{d}" fill="{col}" stroke="{CIZGI}" stroke-width="0.8" '
                      f'stroke-linejoin="round"/>')

    # ölçek + çerçeve
    allp = [proj(*q) for b in kutular for pts3, _ in yuzler(b) for q in pts3]
    xs = [p[0] for p in allp]; ys = [p[1] for p in allp]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    pad = 45
    w = (maxx - minx) + 2 * pad
    h = (maxy - miny) + 2 * pad + 34
    dx, dy = pad - minx, pad - miny
    grup = f'<g transform="translate({dx:.2f},{dy:.2f})">' + "".join(ic) + "</g>"
    baslik = (f'<text x="{w/2:.1f}" y="{h-14:.1f}" font-size="16" fill="#6b5424" '
              f'text-anchor="middle" font-family="sans-serif" font-weight="bold">'
              f'Monte edilmis gorunum - iki basamakli el yikama taburesi</text>')
    return svg_belge(w, h, [grup, baslik], "#ffffff")


# ------------------------------------------------------------------ ana akış
def main():
    print("=== El Yikama Basamagi uretici ===")
    hatalar = dogrula()
    if hatalar:
        print("UYARI - tasarim sorunlari:")
        for h in hatalar:
            print("  •", h)
    else:
        print("Dogrulandi: gecmeler, dil boylari ve duvar mesafeleri kurallara uygun.")

    os.makedirs(OUT, exist_ok=True)
    import cairosvg

    sac_boy = uret_dxf(f"{OUT}/basamak_lazer_kesim.dxf")
    cairosvg.svg2png(bytestring=uret_kesim_svg().encode(),
                     write_to=f"{OUT}/basamak_kesim_yerlesim.png", output_width=2000)
    cairosvg.svg2png(bytestring=uret_teknik_svg().encode(),
                     write_to=f"{OUT}/basamak_teknik.png", output_width=2000)
    cairosvg.svg2png(bytestring=uret_montaj_svg().encode(),
                     write_to=f"{OUT}/basamak_montaj.png", output_width=1800)

    print(f"Levha: {SAC_EN:.0f} x {sac_boy:.0f} mm  ({SAC_EN*sac_boy/1e6:.2f} m^2)")
    for ad, poly, adet, etiket in parcalar():
        x0, y0, x1, y1 = poly.bounds
        print(f"  {etiket:<22} {x1-x0:6.1f} x {y1-y0:6.1f} mm  (kertik/delik: {len(poly.interiors)})")
    print("Tamamlandi ->", OUT)


if __name__ == "__main__":
    main()
