# -*- coding: utf-8 -*-
"""
Katmanlı puzzle üretim motoru — tüm temalar için ortak.

Girdi
-----
  varlik/sahne.png            : parçasız arka plan sahnesi (yazısız)
  varlik/parca_<anahtar>.png  : her parça, düz magenta (#FF00FF) zeminde (yazısız)

Çıktı (cikti/)
--------------
  <tema>_uv_baski.pdf     ÜST katman baskısı, her kenardan 2 mm taşmalı
  <tema>_uv_kalip.pdf     UV hizalama kalıbı (yalnız dış çerçeve, 1:1)
  <tema>_lazer_kesim.dxf  ÜST (cep + yarım ay) ve ALT (düz + gravür) panolar
  <tema>_onizleme.png     kesim çizgileri ve yarım aylar görünür kontrol baskısı

Tasarım kuralları (bkz. README)
-------------------------------
  * Parçalar yerindeyken sahne eksiksiz bir bütündür.
  * ALT katman düz; parça yerlerine kontur GRAVÜR olarak, ``GRAVUR_ICERI`` kadar
    küçültülmüş çizilir (hem ipucu hem boşken görsel değer).
  * ÜST katmanda cepler kesilir. DXF'te parça başına TEK kapalı kontur vardır;
    0,3 mm oturma payı lazer kerfiyle sağlanır -> operatöre "kerf 0,3 mm,
    çizgi üzerinde kes" talimatı verilir.
  * Her cebin açık kenarında Ø12 mm yarım ay; ad plakasına asla değmez.
  * 4 mm altı ayrıntı kesilmez (ahşap dayanımı), parçalar arası >= 7,5 mm duvar,
    dış kenara >= 6 mm.
"""
from __future__ import annotations

import base64
import io
import math
import os
from dataclasses import dataclass, field

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
from skimage import measure

from shapely.affinity import translate as s_tasi
from shapely.geometry import Point, Polygon, box as s_kutu
from shapely.ops import unary_union

# ---------------------------------------------------------------- sabitler
BLEED = 2.0                 # her kenardan taşma payı (mm)
CORNER_R = 8.0              # dış köşe yuvarlatma (mm)
MIN_GAP = 7.5               # parçalar arası en az duvar (mm)
MIN_EDGE = 6.0              # parça -> dış kenar (mm)
MIN_DETAY = 4.0             # en ince kesilebilir ayrıntı (mm)
YUVA_CAP = 12.0             # parmak yuvası (yarım ay) çapı (mm)
YUVA_ACIKLIK = 4.0          # yuva -> diğer parça / dış kenar (mm)
GRAVUR_ICERI = 0.5          # alt katman gravür konturunun içeri payı (mm)
KERF = 0.3                  # operatöre bildirilecek oturma payı (mm)
BASKI_DPI = 300             # kompozit baskı çözünürlüğü

CIZGI = "#20262B"


# ---------------------------------------------------------------- veri modeli
@dataclass
class Parca:
    """Tek puzzle parçası. Konum/boy mm cinsinden, sahne koordinatında."""
    anahtar: str
    ad_tr: str
    ad_en: str
    merkez: tuple                    # (x, y) hedef merkez, mm
    genislik: float                  # hedef genişlik, mm (yükseklik orandan)
    dosya: str = ""                  # boşsa varlik/parca_<anahtar>.png
    etiket_yon: str = "alt"          # alt | ust
    etiket_kaydir: tuple = (0.0, 0.0)
    golge: bool = True               # zemine oturan parçaya yumuşak gölge


@dataclass
class Tema:
    ad: str                          # dosya adı öneki, örn. "dinozorlar"
    baslik: str                      # kalıp PDF'ine yazılan başlık
    parcalar: list
    klasor: str                      # tema klasörünün mutlak yolu
    W: float = 320.0
    H: float = 180.0
    sahne: str = "sahne.png"
    etiket_boyut: float = 4.0

    @property
    def varlik(self):
        return os.path.join(self.klasor, "varlik")

    @property
    def cikti(self):
        return os.path.join(self.klasor, "cikti")


# ---------------------------------------------------------------- yardımcılar
def _disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def _tek(g):
    """Geometriyi tek dış halkalı poligona indirger."""
    if g.is_empty:
        return g
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda x: x.area)
    return Polygon(g.exterior)


def _magenta_ayikla(yol):
    """Magenta (#FF00FF) zeminli PNG'yi RGBA + boolean maskeye çevirir.

    Alfa kanalı varsa doğrudan kullanılır; yoksa magenta anahtarlanır.
    """
    im = Image.open(yol)
    if im.mode == "RGBA" and np.asarray(im)[..., 3].min() < 250:
        a = np.asarray(im)
        maske = a[..., 3] > 128
    else:
        im = im.convert("RGB")
        a = np.asarray(im).astype(np.int16)
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        zemin = (r > 170) & (b > 170) & (g < 110)          # magenta
        maske = ~zemin
        # JPEG/yeniden örnekleme saçaklarını temizle
        maske = ndi.binary_opening(maske, structure=_disk(2))
        maske = ndi.binary_closing(maske, structure=_disk(2))
        a = np.dstack([a.astype(np.uint8),
                       np.where(maske, 255, 0).astype(np.uint8)])
        im = Image.fromarray(a, "RGBA")
    if not maske.any():
        raise RuntimeError(f"{yol}: konu bulunamadı (magenta anahtarlama başarısız)")
    etiket, _ = ndi.label(maske)
    en_buyuk = np.argmax(np.bincount(etiket.ravel())[1:]) + 1
    maske = ndi.binary_fill_holes(etiket == en_buyuk)
    return im.convert("RGBA"), maske


def _maske_poligon(maske, pxmm, sadelik=0.15):
    """İkili maskenin dış sınırını mm cinsinden tek kapalı poligona çevirir."""
    pad = np.pad(maske, 1)
    izler = measure.find_contours(pad.astype(float), 0.5)
    if not izler:
        raise RuntimeError("kontur bulunamadı")
    iz = max(izler, key=len)
    p = Polygon([((c - 1) / pxmm, (r - 1) / pxmm) for r, c in iz])
    if not p.is_valid:
        p = _tek(p.buffer(0))
    return Polygon(p.exterior).simplify(sadelik, preserve_topology=True)


def cerceve_poly(T):
    return s_kutu(CORNER_R, CORNER_R, T.W - CORNER_R,
                  T.H - CORNER_R).buffer(CORNER_R, quad_segs=16)


# ---------------------------------------------------------------- 1. parçalar
def parcalari_yukle(T):
    """Her parçanın RGBA görselini, mm poligonunu ve ölçeğini hazırlar."""
    veri = {}
    for p in T.parcalar:
        yol = os.path.join(T.varlik, p.dosya or f"parca_{p.anahtar}.png")
        if not os.path.exists(yol):
            raise FileNotFoundError(yol)
        im, maske = _magenta_ayikla(yol)
        ys, xs = np.nonzero(maske)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        im = im.crop((x0, y0, x1, y1))
        maske = maske[y0:y1, x0:x1]

        pxmm = maske.shape[1] / p.genislik            # kaynak px / mm
        # 4 mm altı çıkıntıları buda, köşeleri yumuşat (ahşap dayanımı)
        r_ac = max(1, int(round(MIN_DETAY * pxmm / 2)))
        r_kapa = max(1, int(round(0.8 * pxmm)))
        temiz = ndi.binary_opening(maske, structure=_disk(r_ac))
        et, n = ndi.label(temiz)
        if n == 0:
            raise RuntimeError(f"{p.anahtar}: {MIN_DETAY} mm budama sonrası boş kaldı")
        temiz = et == (np.argmax(np.bincount(et.ravel())[1:]) + 1)
        temiz = ndi.binary_fill_holes(ndi.binary_closing(temiz, structure=_disk(r_kapa)))

        poly = _maske_poligon(temiz, pxmm)
        cx, cy = poly.centroid.x, poly.centroid.y
        poly = s_tasi(poly, p.merkez[0] - cx, p.merkez[1] - cy)
        veri[p.anahtar] = {
            "parca": p, "gorsel": im, "maske": maske, "pxmm": pxmm,
            "poly": poly, "yerel_merkez": (cx, cy),
        }
    return veri


# ---------------------------------------------------------------- 2. yerleşim
def yerlesimi_duzelt(T, veri, tur_sayisi=400):
    """Parçaları birbirinden ve kenardan iterek paylara uydurur.

    Konumlar yaklaşık verilir; bu gevşetme adımı >= MIN_GAP ve >= MIN_EDGE
    kurallarını garantiye alır. Taşınan miktarı rapor eder.
    """
    ic_alan = cerceve_poly(T).buffer(-MIN_EDGE)
    baslangic = {k: (v["poly"].centroid.x, v["poly"].centroid.y)
                 for k, v in veri.items()}
    anahtarlar = list(veri)

    for _ in range(tur_sayisi):
        itme = {k: np.zeros(2) for k in anahtarlar}
        bozuk = False
        for i, a in enumerate(anahtarlar):
            for b in anahtarlar[i + 1:]:
                pa, pb = veri[a]["poly"], veri[b]["poly"]
                d = pa.distance(pb)
                if d >= MIN_GAP:
                    continue
                bozuk = True
                va = np.array([pa.centroid.x, pa.centroid.y])
                vb = np.array([pb.centroid.x, pb.centroid.y])
                yon = vb - va
                n = np.linalg.norm(yon)
                yon = yon / n if n > 1e-6 else np.array([1.0, 0.0])
                itis = (MIN_GAP - d) * 0.55
                itme[a] -= yon * itis
                itme[b] += yon * itis
        for a in anahtarlar:
            pa = veri[a]["poly"]
            if not ic_alan.contains(pa):
                bozuk = True
                disari = pa.difference(ic_alan)
                if not disari.is_empty:
                    c = np.array([pa.centroid.x, pa.centroid.y])
                    dc = np.array([disari.centroid.x, disari.centroid.y])
                    yon = c - dc
                    n = np.linalg.norm(yon)
                    if n > 1e-6:
                        itme[a] += yon / n * min(2.0, 0.6 + disari.area ** 0.5 * 0.2)
        if not bozuk:
            break
        for a in anahtarlar:
            if np.linalg.norm(itme[a]) > 1e-9:
                veri[a]["poly"] = s_tasi(veri[a]["poly"], *itme[a])

    rapor = []
    for k, v in veri.items():
        yeni = (v["poly"].centroid.x, v["poly"].centroid.y)
        dx, dy = yeni[0] - baslangic[k][0], yeni[1] - baslangic[k][1]
        if math.hypot(dx, dy) > 0.15:
            rapor.append(f"{k}: konum {math.hypot(dx, dy):.1f} mm kaydırıldı "
                         f"(dx={dx:+.1f}, dy={dy:+.1f})")
    return rapor


# ---------------------------------------------------------------- 3. yarım aylar
def yuvalari_yerlestir(T, veri, etiketler):
    """Her cebin en ferah kenarına Ø12 mm yarım ay yerleştirir.

    Ad plakasına ve komşu parçalara YUVA_ACIKLIK payı bırakılır.
    """
    R = YUVA_CAP / 2.0
    kenar = cerceve_poly(T).exterior
    yazi_alani = unary_union([e["kutu"] for e in etiketler.values()])
    sonuc, rapor = {}, []
    for k, v in veri.items():
        poly = v["poly"]
        digerleri = unary_union([w["poly"] for a, w in veri.items() if a != k])
        cevre = poly.exterior
        n = max(160, int(cevre.length / 1.2))
        en_iyi, skor_en = None, -1e9
        for t in range(n):
            c = cevre.interpolate(t / n, normalized=True)
            hilal = _tek(Point(c.x, c.y).buffer(R, quad_segs=24).difference(poly))
            if hilal.is_empty or hilal.area < 14.0:
                continue
            skor = min(hilal.distance(digerleri), hilal.distance(kenar))
            if hilal.intersects(yazi_alani):
                skor -= 1000                       # ad yazısını asla kesme
            if skor > skor_en:
                skor_en, en_iyi = skor, hilal
        if en_iyi is None or skor_en < YUVA_ACIKLIK:
            rapor.append(f"{k}: uygun yarım ay bulunamadı (en iyi açıklık "
                         f"{skor_en:.1f} mm) — konumu/etiketi kaydırın")
        if en_iyi is not None:
            sonuc[k] = en_iyi.simplify(0.05, preserve_topology=True)
    return sonuc, rapor


# ---------------------------------------------------------------- 4. etiketler
def _etiket_olcu(tr, en, boyut):
    kf = 0.62
    on = f"{tr} / "
    w_on, w_en = len(on) * boyut * kf, len(en) * boyut * kf
    return w_on, w_en, w_on + w_en + 6.4, boyut + 2.4


def etiketleri_hesapla(T, veri):
    """Her parçanın altına/üstüne ad plakası yerleştirir ve kutusunu döndürür."""
    ci = {}
    for k, v in veri.items():
        p = v["parca"]
        x0, y0, x1, y1 = v["poly"].bounds
        w_on, w_en, w, h = _etiket_olcu(p.ad_tr, p.ad_en, T.etiket_boyut)
        cx = (x0 + x1) / 2 + p.etiket_kaydir[0]
        cy = (y1 + 3.2 + h / 2 if p.etiket_yon == "alt"
              else y0 - 3.2 - h / 2) + p.etiket_kaydir[1]
        cx = min(max(cx, w / 2 + 3.0), T.W - w / 2 - 3.0)
        cy = min(max(cy, h / 2 + 3.0), T.H - h / 2 - 3.0)
        ci[k] = {"cx": cx, "cy": cy, "w": w, "h": h, "w_on": w_on, "w_en": w_en,
                 "tr": p.ad_tr, "en": p.ad_en,
                 "kutu": s_kutu(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)}
    return ci


# ---------------------------------------------------------------- 5. doğrulama
def dogrula(T, veri, yuvalar, etiketler):
    h = []
    kenar = cerceve_poly(T).exterior
    ad = list(veri)
    for k in ad:
        d = veri[k]["poly"].distance(kenar)
        if d < MIN_EDGE - 0.05:
            h.append(f"{k}: dış kenara {d:.2f} mm (en az {MIN_EDGE})")
    for i, a in enumerate(ad):
        for b in ad[i + 1:]:
            d = veri[a]["poly"].distance(veri[b]["poly"])
            if d <= 0:
                h.append(f"{a} ile {b} ÇAKIŞIYOR")
            elif d < MIN_GAP - 0.05:
                h.append(f"{a}–{b} arası {d:.2f} mm (en az {MIN_GAP})")
    for k in ad:
        if k not in yuvalar:
            h.append(f"{k}: yarım ay yerleştirilemedi")
            continue
        hilal = yuvalar[k]
        if veri[k]["poly"].distance(hilal) > 0.2:
            h.append(f"{k} yarım ayı kontura bitişik değil")
        if hilal.distance(kenar) < YUVA_ACIKLIK - 0.05:
            h.append(f"{k} yarım ayı dış kenara {hilal.distance(kenar):.2f} mm")
        for b in ad:
            if b != k and hilal.distance(veri[b]["poly"]) < YUVA_ACIKLIK - 0.05:
                h.append(f"{k} yarım ayı {b} parçasına "
                         f"{hilal.distance(veri[b]['poly']):.2f} mm")
        for b, e in etiketler.items():
            if hilal.intersects(e["kutu"]):
                h.append(f"{k} yarım ayı '{e['tr']}' ad plakasını kesiyor")
    for i, a in enumerate(ad):
        for b in ad[i + 1:]:
            if etiketler[a]["kutu"].intersects(etiketler[b]["kutu"]):
                h.append(f"'{etiketler[a]['tr']}' ve '{etiketler[b]['tr']}' "
                         f"ad plakaları çakışıyor")
    for k in ad:
        for b in ad:
            if etiketler[k]["kutu"].intersects(veri[b]["poly"]):
                h.append(f"'{etiketler[k]['tr']}' ad plakası {b} parçasını örtüyor")
    return h


# ---------------------------------------------------------------- 6. kompozit
def kompozit_uret(T, veri):
    """Sahne + parçaları BASKI_DPI çözünürlükte tek rastere birleştirir.

    Tuval taşma kutusudur; sahne taşmayı dolduracak şekilde ölçeklenir.
    """
    olcek = BASKI_DPI / 25.4                       # px/mm
    tw = int(round((T.W + 2 * BLEED) * olcek))
    th = int(round((T.H + 2 * BLEED) * olcek))
    yol = os.path.join(T.varlik, T.sahne)
    if not os.path.exists(yol):
        raise FileNotFoundError(yol)
    tuval = Image.open(yol).convert("RGB").resize((tw, th), Image.LANCZOS)

    def mm2px(x, y):
        return int(round((x + BLEED) * olcek)), int(round((y + BLEED) * olcek))

    for k, v in veri.items():
        p, im = v["parca"], v["gorsel"]
        hedef_w = int(round(p.genislik * olcek))
        hedef_h = int(round(im.height * hedef_w / im.width))
        im = im.resize((hedef_w, hedef_h), Image.LANCZOS)
        cx, cy = v["poly"].centroid.x, v["poly"].centroid.y
        # yerel_merkez zaten mm: görselin sol-üstü, konturun centroid'ine göre
        lx, ly = v["yerel_merkez"]
        sol, ust = mm2px(cx - lx, cy - ly)
        if p.golge:
            g = Image.new("L", (hedef_w, max(4, hedef_h // 6)), 0)
            from PIL import ImageDraw
            ImageDraw.Draw(g).ellipse([hedef_w * 0.08, 0, hedef_w * 0.92,
                                       g.height], fill=90)
            g = g.filter(ImageFilter.GaussianBlur(max(2, hedef_w // 40)))
            golge = Image.new("RGB", g.size, (25, 35, 20))
            tuval.paste(golge, (sol, ust + hedef_h - g.height // 2), g)
        tuval.paste(im, (sol, ust), im)
    return tuval


# ---------------------------------------------------------------- 7. SVG / PDF
def _yol_svg(poly):
    pts = list(poly.exterior.coords)[:-1]
    return (f"M {pts[0][0]:.3f} {pts[0][1]:.3f} "
            + " ".join(f"L {x:.3f} {y:.3f}" for x, y in pts[1:]) + " Z")


def _png_b64(im):
    tampon = io.BytesIO()
    im.save(tampon, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(tampon.getvalue()).decode()


def _svg(w, h, ic):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">'
            + "\n".join(ic) + "</svg>")


def _etiket_svg(e, boyut):
    bas = e["cx"] - (e["w_on"] + e["w_en"]) / 2
    y = e["cy"] + boyut * 0.35
    x, yy, w, h = e["cx"] - e["w"] / 2, e["cy"] - e["h"] / 2, e["w"], e["h"]
    return [
        f'<rect x="{x:.2f}" y="{yy + 0.5:.2f}" width="{w:.2f}" height="{h:.2f}" '
        f'rx="1.6" fill="#12200C" fill-opacity="0.20"/>',
        f'<rect x="{x:.2f}" y="{yy:.2f}" width="{w:.2f}" height="{h:.2f}" rx="1.6" '
        f'fill="#FFFFFF" fill-opacity="0.97"/>',
        f'<rect x="{x:.2f}" y="{yy:.2f}" width="{w:.2f}" height="{h:.2f}" rx="1.6" '
        f'fill="none" stroke="#2A3A28" stroke-width="0.35" stroke-opacity="0.5"/>',
        f'<text x="{bas:.2f}" y="{y:.2f}" fill="#1C2733" font-size="{boyut}" '
        f'font-family="sans-serif" font-weight="bold">{e["tr"]} / </text>',
        f'<text x="{bas + e["w_on"]:.2f}" y="{y:.2f}" fill="#2563D9" '
        f'font-size="{boyut}" font-family="sans-serif" '
        f'font-weight="bold">{e["en"]}</text>',
    ]


def baski_svg(T, kompozit, etiketler, veri=None, yuvalar=None):
    tw, th = T.W + 2 * BLEED, T.H + 2 * BLEED
    ic = [f'<image x="0" y="0" width="{tw}" height="{th}" '
          f'preserveAspectRatio="none" xlink:href="{_png_b64(kompozit)}"/>',
          f'<g transform="translate({BLEED},{BLEED})">']
    for e in etiketler.values():
        ic += _etiket_svg(e, T.etiket_boyut)
    if veri:                                        # önizleme katmanı
        for v in veri.values():
            ic.append(f'<path d="{_yol_svg(v["poly"])}" fill="none" '
                      f'stroke="#FF1744" stroke-width="0.6"/>')
        for hilal in (yuvalar or {}).values():
            ic.append(f'<path d="{_yol_svg(hilal)}" fill="#FFFFFF" '
                      f'fill-opacity="0.75" stroke="#FF1744" stroke-width="0.4"/>')
        ic.append(f'<path d="{_yol_svg(cerceve_poly(T))}" fill="none" '
                  f'stroke="#2979FF" stroke-width="0.6"/>')
    ic.append("</g>")
    return _svg(tw, th, ic)


def kalip_svg(T):
    return _svg(T.W, T.H, [
        f'<path d="{_yol_svg(cerceve_poly(T))}" fill="none" stroke="#FF0000" '
        f'stroke-width="0.25"/>',
        f'<text x="6" y="{T.H - 4:.1f}" fill="#888888" font-size="3" '
        f'font-family="sans-serif">{T.baslik} {T.W:.0f}x{T.H:.0f} '
        f'- UV KALIP (1:1)</text>'])


# ---------------------------------------------------------------- 8. DXF
def dxf_uret(T, dosya, veri, yuvalar):
    import ezdxf

    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    doc.layers.add("UST_KATMAN_KESIM", color=1)     # kırmızı
    doc.layers.add("ALT_KATMAN_KESIM", color=5)     # mavi
    doc.layers.add("ALT_KATMAN_GRAVUR", color=3)    # yeşil (kesme, çiz)
    doc.layers.add("YAZI", color=8)

    def poli(poly, dx, katman):
        pts, son = [], None
        for (x, y) in list(poly.exterior.coords)[:-1]:
            q = (round(x + dx, 3), round(T.H - y, 3))
            if q != son:
                pts.append(q)
                son = q
        if len(pts) > 1 and pts[0] == pts[-1]:
            pts.pop()
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": katman})

    poli(cerceve_poly(T), 0, "UST_KATMAN_KESIM")
    for v in veri.values():
        poli(v["poly"], 0, "UST_KATMAN_KESIM")
    for hilal in yuvalar.values():
        poli(hilal, 0, "UST_KATMAN_KESIM")

    dx = T.W + 15
    poli(cerceve_poly(T), dx, "ALT_KATMAN_KESIM")
    for v in veri.values():
        g = v["poly"].buffer(-GRAVUR_ICERI, quad_segs=8)
        if g.is_empty:
            continue
        for gg in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            poli(Polygon(gg.exterior), dx, "ALT_KATMAN_GRAVUR")

    msp.add_text(f"UST KATMAN - cepler + yarim aylar ({T.W:.0f}x{T.H:.0f}) "
                 f"- KERF {KERF} mm, cizgi uzerinde kes",
                 dxfattribs={"layer": "YAZI", "height": 6}).set_placement((0, T.H + 6))
    msp.add_text(f"ALT KATMAN - duz taban + gravur konturlar "
                 f"(ic pay {GRAVUR_ICERI} mm)",
                 dxfattribs={"layer": "YAZI", "height": 6}).set_placement((dx, T.H + 6))
    doc.saveas(dosya)


# ---------------------------------------------------------------- ana akış
def uret(T):
    print(f"Tema: {T.baslik}  pano {T.W:.0f}x{T.H:.0f} mm, "
          f"{len(T.parcalar)} parça")
    veri = parcalari_yukle(T)

    for satir in yerlesimi_duzelt(T, veri) or ["  (yerleşim düzeltmesi gerekmedi)"]:
        print("  •", satir)

    etiketler = etiketleri_hesapla(T, veri)
    yuvalar, y_rapor = yuvalari_yerlestir(T, veri, etiketler)
    for satir in y_rapor:
        print("  !", satir)

    hatalar = dogrula(T, veri, yuvalar, etiketler)
    print()
    if hatalar:
        print("UYARI – yerleşim sorunları:")
        for h in hatalar:
            print("  •", h)
    else:
        print("Yerleşim doğrulandı: paylar, yarım aylar ve ad plakaları kurallara uygun.")

    # baskı çözünürlüğü denetimi
    for k, v in veri.items():
        dpi = v["pxmm"] * 25.4
        if dpi < 150:
            print(f"  ! {k}: parça çözünürlüğü {dpi:.0f} dpi (<150) — "
                  f"kaynak görseli büyüt")

    os.makedirs(T.cikti, exist_ok=True)
    import cairosvg

    kompozit = kompozit_uret(T, veri)
    cairosvg.svg2pdf(bytestring=baski_svg(T, kompozit, etiketler).encode(),
                     write_to=f"{T.cikti}/{T.ad}_uv_baski.pdf")
    cairosvg.svg2pdf(bytestring=kalip_svg(T).encode(),
                     write_to=f"{T.cikti}/{T.ad}_uv_kalip.pdf")
    cairosvg.svg2png(
        bytestring=baski_svg(T, kompozit, etiketler, veri, yuvalar).encode(),
        write_to=f"{T.cikti}/{T.ad}_onizleme.png", output_width=2200)
    dxf_uret(T, f"{T.cikti}/{T.ad}_lazer_kesim.dxf", veri, yuvalar)

    print("\nparçalar:")
    for k, v in veri.items():
        x0, y0, x1, y1 = v["poly"].bounds
        p = v["parca"]
        print(f"  {p.ad_tr:<14} ({p.ad_en:<15}) {x1-x0:6.1f} x {y1-y0:6.1f} mm  "
              f"{v['pxmm']*25.4:4.0f} dpi")
    print("Tamamlandı ->", T.cikti)
    return veri, yuvalar, etiketler
