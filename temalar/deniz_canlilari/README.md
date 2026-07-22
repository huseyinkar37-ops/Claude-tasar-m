# Deniz Canlıları Puzzle – Tema 02

İki katmanlı eğitici çocuk puzzle'ı. Bitmiş ölçü **320 × 180 mm**, dış köşeler 8 mm yuvarlatılmış. 8 canlı parçası, üç derinlik kuşağına yerleştirilmiştir — çocuk hem canlıları hem nerede yaşadıklarını öğrenir:

| Kuşak | Parçalar |
|---|---|
| Yüzeye yakın | yunus, denizanası |
| Orta su | denizatı, kaplumbağa, balık (palyaço) |
| Deniz tabanı | ahtapot, yengeç, denizyıldızı |

## Üretim dosyaları (`cikti/`)

| Dosya | Amaç | Ölçü |
|---|---|---|
| `deniz_canlilari_uv_kalip.pdf` | UV hizalama kalıbı — **yalnız dış çerçeve konturu** (1:1) | 320 × 180 mm |
| `deniz_canlilari_uv_baski.pdf` | ÜST katman baskısı — her kenardan 2 mm taşmalı | 324 × 184 mm |
| `deniz_canlilari_alt_golge.pdf` | ALT katman gölge baskısı — cep tabanlarında siluetler | 324 × 184 mm |
| `deniz_canlilari_lazer_kesim.dxf` | Lazer kesim (mm, R2010) | iki pano yan yana |
| `deniz_canlilari_onizleme.png` | Ekran önizlemesi (yuvalar görünür) | ~170 dpi |

Beyaz mürekkep dosyası kullanılmıyor. Gölge siluetleri 0,4 mm içeri alınmıştır.

### DXF katmanları

- `UST_KATMAN_KESIM` (kırmızı): dış çerçeve + 8 canlı konturu + **8 parmak yuvası hilali** (R 5,5 mm, her cebin açık tarafında).
- `ALT_KATMAN_KESIM` (mavi): düz taban panosu.
- `YAZI` (gri): etiketler — kesilmez, lazer yazılımında kapatın.

### Baskı içeriği

- Canlı çizimleri **referans görsellerden** üretilir: her canlının resmi `varlik/<canli>.png` altında durur (masal kitabı stili — kalın koyu kontur, iri parlak göz, gülen yüz, doygun renk). Stili beğenmezseniz bu PNG'yi değiştirip betiği yeniden çalıştırmanız yeter.
- `olustur.py` her görselin **siluetini** çıkarır (beyaz zemini kenardan temizler, iç beyazları korur), lazer için TEK tıknaz kapalı kontur türetir (ince uzantıları ahşap dayanımına göre morfolojik kapama ile şişirir) ve aynı görseli bu kontura kırpılı biçimde baskıya gömer. Böylece **baskı ile kesim asla ayrışmaz** — tek kontur hem SVG kırpma maskesini hem DXF polyline'ını besler.
- Her parçanın yanında **Türkçe / İngilizce** ad plakası (İngilizce mavi renkte): Yunus / Dolphin, Denizanası / Jellyfish, Denizatı / Seahorse, Kaplumbağa / Sea Turtle, Balık / Fish, Ahtapot / Octopus, Yengeç / Crab, Denizyıldızı / Starfish. Konumlar parmak yuvalarıyla çakışmaz.
- Sağ üst köşede **zoziva** logosu (`varlik/zoziva_logo.png`).
- Dekor: su yüzeyi, ışık hüzmeleri, çerçeveli kabarcıklar, kumlu taban, renkli mercanlar (mor/pembe dallı), sarı tüp süngerler, yosunlar, kayalar, tarak/salyangoz kabukları, mini denizyıldızı.

### Görselleri değiştirme / yerleşim

- Bir canlıyı değiştirmek: `varlik/<canli>.png` dosyasını yeni bir resimle (tercihen düz beyaz zeminli, tek nesne) değiştirin, `python3 olustur.py` çalıştırın. Kontur, gölge ve kesim otomatik yeniden türetilir.
- Konum, boyut ve kontur tıknazlığı `olustur.py` içindeki `YERLESIM` tablosundan ayarlanır: `(ad, merkez_x, merkez_y, hedef_boy_mm, kapa, ac, sınıf)`. `kapa` büyüdükçe ince uzantılar daha çok şişer/birleşir.

## Üretim notları

- İş sırası ve toleranslar `temalar/araclar/README.md` ile aynıdır (kerf telafisi yok, parçalar arası ≥ 7,5 mm, kenara ≥ 6 mm; kod doğrular).
- İnce uzantılı canlılarda (denizanası tentakülleri, ahtapot kolları) kesim şekli morfolojik kapama ile tıknazlaştırılır; yine de çok ince yerler için `YERLESIM`'deki `kapa` değerini artırabilirsiniz.

## Yeniden üretme

```bash
pip install ezdxf cairosvg shapely pillow numpy scikit-image scipy
python3 olustur.py
```

> Not: `araclar` teması saf vektör çizimken bu tema görsel-siluet tabanlıdır; bu yüzden ek olarak `pillow`, `numpy`, `scikit-image`, `scipy` gerekir.
