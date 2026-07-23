# El Yıkama Basamağı — 15 mm Huş Kontrplak

Çocukların lavaboya erişip **kendi başına el yıkayabilmesi** için tasarlanmış,
iki basamaklı, **vidasız geçmeli** (kertme-dil / mortise-tenon) tabure.
Tüm parçalar tek 15 mm huş kontrplak levhadan kesilir ve ahşap tutkalıyla
birbirine geçer.

## Ölçüler

| Ölçü | Değer |
|------|-------|
| Toplam en | 380 mm |
| Toplam derinlik (ayak izi) | 360 mm |
| Alt basamak yüksekliği | 150 mm |
| Üst platform yüksekliği | 300 mm |
| Malzeme | 15 mm huş kontrplak (birch plywood) |
| Levha kullanımı | 1220 × 640 mm (~0,78 m²) — yarım levhadan az |

Derinlik (360 mm) yükseklikten (300 mm) büyük tutuldu; bu, çocuk üst platformun
ön kenarına bassa bile taburenin öne devrilmemesi için gereken denge payıdır.
En iyi güvenlik için tabureyi lavabo dolabına **dayalı** kullanın.

## Parça Listesi (tek levhadan)

| Parça | Adet | Yaklaşık ölçü | Görev |
|-------|------|----------------|-------|
| Yan panel (merdiven profilli) | 2 | 360 × 300 mm | Taşıyıcı yanlar, tüm kertikler burada |
| Üst platform | 1 | 380 × 210 mm | Üstte durulan, el yıkanan yüzey |
| Alt basamak | 1 | 380 × 150 mm | Tırmanma basamağı |
| Dikey rıht (riser) | 1 | 380 × 135 mm | İki basamak arası, platform ön kenarını destekler |
| Arka panel | 1 | 380 × 300 mm | Sağlamlık + taşıma için el deliği |
| Ön kuşak (toe-kick) | 1 | 380 × 60 mm | Ön alt gergi, açılmayı önler |

Basamaklar ve gergiler, yan panellere **iki uçtan geçen dillerle** (through-tenon)
bağlanır; diller yan panelin dış yüzeyine tam gelir. Basamaklar üst kenardan
**açık çentiğe** oturur (üst yüzey pürüzsüz), rıht/arka/kuşak ise **kapalı
kertiğe** girer.

## Üretim Dosyaları (`cikti/`)

| Dosya | Açıklama |
|-------|----------|
| `basamak_lazer_kesim.dxf` | CNC/lazer kesim. `KESIM` katmanı = kesilecek tüm konturlar (parça dış hatları + kertikler + el deliği). `SAC` katmanı = kesilmeyen levha sınırı referansı. `YAZI` = parça etiketleri. Birim: mm. |
| `basamak_teknik.png` | Yan + ön görünüş, ana ölçüler |
| `basamak_montaj.png` | Monte edilmiş 3B görünüm |
| `basamak_kesim_yerlesim.png` | Levha üstü parça dizilimi (DXF önizlemesi) |

## Kesim Notları

- **Kerf telafisi uygulanmadı.** Lazer/CNC kerf'i (~0,15–0,2 mm) tutkallı geçme
  için sıkı-uygun kalır. Freze/router ile kesiyorsanız 3 mm veya daha ince uç
  kullanın; kertikler dar (15 mm).
- Tüm kertik/dil kalınlığı **15 mm** — kullandığınız kontrplağın gerçek
  kalınlığını ölçün. Levha 14,5 mm ise kertikleri o değere göre daraltın
  (`KALINLIK` sabitini `olustur.py` içinde değiştirip yeniden üretin).
- Açıkta kalan tüm köşeler `olustur.py` içinde 12 mm yarıçapla yumuşatıldı.
  Kesimden sonra tüm **kenarları 3–4 mm freze/zımpara ile yuvarlayın** (çocuk
  güvenliği; kıymık önleme).

## Montaj

1. İki yan paneli karşılıklı, kertikleri içe bakacak şekilde yerleştirin.
2. **Arka paneli** her iki yanın arka kertiklerine geçirin — çerçeveyi kareye alır.
3. **Alt basamağı** üstten açık çentiklere oturtun; üst yüzeyi yan panel üst
   kenarıyla aynı hizaya gelir.
4. **Dikey rıhtı** iki basamak arasındaki kertiklere geçirin.
5. **Üst platformu** üst çentiklere oturtun; ön kenarı rıhtın üstüne yaslanır.
6. **Ön kuşağı** en öndeki alt kertiklere geçirin.
7. Bütün geçme yüzeylerine **D3 su bazlı ahşap tutkalı** sürüp birleştirin,
   gönyeye alın, kuruyana kadar işkence/kayış ile sıkın (≈ 1 saat).
8. İsteğe bağlı: her geçmeyi içeriden 4 × 30 mm ahşap dübel veya gizli vida ile
   pekiştirin.

## Bitirme (Öneri)

- 180–220 kum zımpara → toz alma.
- Çocuk güvenli, **su bazlı** mat vernik veya doğal ahşap yağı (2 kat).
  Lavabo yanında kullanılacağı için su itici bitiş önemli.
- Basamak yüzeylerine kaymaz şerit/nokta ekleyin.
- Taban kenarlarına keçe/silikon ayak: zemini çizmez, kaymayı azaltır.

## Yeniden Üretim

```bash
pip install ezdxf cairosvg shapely
cd temalar/basamak && python3 olustur.py
```

Betik çalışırken geçmeleri, dil boylarını ve ahşap duvar mesafelerini kendisi
doğrular; ihlal olursa uyarı basar (uyarıları hata sayın). Ölçüleri değiştirmek
için dosyanın başındaki sabitleri (`KALINLIK`, `GENISLIK`, `DERINLIK`, `H1`,
`H2`, …) düzenleyin.

## Güvenlik

Bu bir **basamak/tabure**dir, korkuluklu "öğrenme kulesi" (learning tower)
değildir. 2 yaş altı veya dengesi zayıf çocuklarda yetişkin gözetimi şarttır ve
tabureyi tezgâha dayalı kullanın. Daha küçük çocuklar için yanlara tutunma
korkuluğu eklenmesi önerilir.
