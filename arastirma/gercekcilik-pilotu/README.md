# Gerçekçilik pilotu — bulgular

Amaç: "kod ile üretilen vektör görsel ne kadar gerçekçi olabilir?" sorusunu
ölçmek. Üretim dosyalarına dokunulmadı; bu klasör bir deney kaydıdır.

## Kritik teknik bulgu: cairosvg SVG filtrelerini yok sayıyor

`cairosvg` `feGaussianBlur`, `feTurbulence`, `feDiffuseLighting` ve
`feSpecularLighting` dahil tüm filtre zincirini sessizce atlıyor — bulanıklık
uygulanmıyor, gürültü düz siyah dolgu olarak çıkıyor. Mevcut temaların düz
görünmesinin başlıca teknik sebeplerinden biri budur: yumuşak gölge, kabartma
ve parlaklık üretmek fiilen mümkün değildi.

`resvg` (pip: `resvg-py`) aynı filtreleri doğru render ediyor. Bu pilot resvg
kullanır.

## Uygulanan teknikler

| Teknik | Ne kazandırıyor |
|---|---|
| Catmull-Rom → kübik Bézier siluet | İlkel şekil birleşimi yerine serbest organik form |
| Çok duraklı gövde gradyanı | Düz dolgu yerine hacim |
| `feTurbulence` + `feDiffuseLighting` | Gerçek deri/kabuk kabartması |
| `feSpecularLighting` | Islak yüzey vurgusu |
| `feGaussianBlur` ile iç gölge (AO) | Kontur boyunca hacim; siyah dış çizgiye gerek kalmıyor |
| Bulanık kenar ışığı | Işık yönünden ince parlama |
| Bulanık temas gölgesi | Zeminden ayrışma |
| Yumuşak geçişli karşı-gölgeleme | Keskin karın çizgisi yerine doğal geçiş |

## Üretilebilirlik

Bézier siluetler zaten imalata uygun çıktı — `buffer(+1.4).buffer(-1.4)`
kapaması alanı %0.0–0.1 değiştiriyor. Yani ilkel şekil birleşimindeki
"sosisleşme" sorunu ortadan kalkıyor; kesim konturu çizimin kendisi olabiliyor.

## Sonuç

Ulaşılan nokta: **üst düzey gerçekçi vektör illüstrasyon**. Ulaşılamayan
nokta: **fotoğrafik gerçekçilik**. Kalan fark gölgelendirme değil, mikro
detay (pul varyansı, deri altı saçılım, asimetri, yıpranma) — el ile yazılan
vektörle kapanmıyor.

Ayrıca her canlı, kontrol noktalarını körlemesine yerleştirip render'a bakarak
düzeltmeyi gerektiriyor: 3 canlı için 3 tur sürdü.

Fotoğrafik hedef için raster yol (gerçek görsel kaynağı + arka plan temizleme
+ kontura maskeleme) gerekiyor. O yolda kesim konturu görselin alfa
siluetinden türetileceği için anatomi sorunu da kendiliğinden çözülür.

## Çalıştırma

```bash
pip install resvg-py shapely
python3 pilot.py
```
