# Mahsuplaşma Yöntemi (Adım 1 ve Adım 2)

Türkiye'de firmalar ve sektörler arası karşılıklı TL borçların **mahsuplaşma** ile ne kadar silinebileceğini ölçen/modelleyen çalışma. Kaynak: [zarar-teorisi](https://github.com/saydamonur2002-tech/zarar-teorisi) projesindeki beş adımlı sistemin ilk iki adımı (dal `adim4-senet-paylasim`, commit `58432a5`, salt okuma ile kopyalandı).

> Bu bir öngörü ya da politika önerisi değil, bir **mekanizma ve üst sınır** çalışmasıdır. **Nedensellik iddiası yoktur.** Sayıların çoğu üst sınırdır; "stok yüzde X silindi" denmez.

## Etiketler
[VERİ] ölçüm · [HESAP] veriden hesap · [VARSAYIM] model varsayımı · [VEKİL] vekil ölçü · [İKİNCİL] ikincil kaynak · [DOĞRULANMADI]

## Adım 1 — Karşılıklı stokların mahsubu (iki taraflı)
Sektör çiftlerinde (hane H, firmalar F, bankalar B′, diğer finansal K′, dış dünya D) iki yönlü borç bacaklarının ortak kısmı (min) silinebilir.
- Hazneler arası: Σortak 20.363,4 / Σbrüt 78.870,4 milyar TL → `yeni_tavan` 0,2582 [HESAP, üst sınır]; eski yöntem 0,0728 (`adim1_stok.csv`, `docs/BES_ADIM.md`).
- F sektörü içi ticari borç (EVDS 2026-Q1, konsolide olmayan − konsolide): 39.928,6 milyar TL [VERİ] (`adim1/ADIM1_NACE.md`).
- NACE 17 kısım (Sektör Bilançoları 2024): brüt 14.335,4, silinen_max 13.100,9 = %91,4 [HESAP, üst sınır].
- Zaman bandı 2009–2024 tam graf oranı [0,665; 0,925]; seyrek ağ (yoğunluk 0,25) alt ucu 0,124 [VARSAYIM] (`adim1/rev_adim1_sonuc.json`).
- Silinen gerçek tutar **boş**: firma düzeyi kimden-kime verisi yok.

## Adım 2 — Çok taraflı mahsup ağı + akışla ödeme
17 NACE kısmı + 17 hane (ücret) düğümü + 1 dış düğüm; optimal mahsup (Fleischman, Dini & Littera 2020), sıralı ödeme, Eisenberg–Noe teşhisi (`ortak/mahsuplasma_paketi`).
- Mahsupla silinen 14.602,3 milyar TL (%88,5) [HESAP; düğümler ölçüm, kenarlar VARSAYIM] (`adim2/ADIM2_NACE_AG.md`).
- Çapa G1 firma takip oranı %2,522 (2026-09) [VERİ]; nakit çarpanı λ* = 0,8931 [VARSAYIM, kalibrasyon].
- Ücret geçiş tavanı β = 0,0439 [HESAP]; sentetik 0,3 tavanın üstünde.
- Brüt aşama kredi ihtiyacı 8.328,6 milyar TL (λ=1) → şart sonrası 0,0 [VARSAYIM, model].

## Finansman gideri etkisi (docs/analiz_adim12)
Adım 1 net faiz düşüşü 738,2 milyar TL/yıl [HESAP] = 2024/2025 firma finansman giderinin %23 / %17'si. Brüt rakamlar ve Adım 2 köprü faizi mevcut gideri aştığı için gerçekçi değil (`docs/analiz_adim12/finansman/RAPOR.md`). ON_KAYIT/SAPMA dosyaları her alt klasörde.

## Klasörler
- `adim1/` kodlar, sonuçlar, raporlar (stok silim, NACE, rev C, sektör mahsup)
- `adim2/` NACE ağı, rev D, ödeme–mahsup
- `ortak/` `mahsuplasma_paketi` (Python paketi + testler), `evds_cek.py`, `rev_veri.py`
- `docs/` BES_ADIM.md, BES_ADIM_MALIYET.md, analiz_adim12 (finansman, hassasiyet, model, oran84, gider payı)
- `tests/` sonuç tutarlılık testleri

## Veri kaynakları
- TCMB EVDS, **resmi uç nokta `https://evds3.tcmb.gov.tr/igmevdsms-dis`** (`ortak/evds_cek.py`). Anahtar gerekirse yalnız ortam değişkeninden (`EVDS_API_KEY`) okunmalıdır; depoda anahtar yoktur.
- TCMB Finansal Hesaplar ve Sektör Bilançoları; TÜİK Yapısal İş İstatistikleri (xls); BDDK/EVDS takip oranları.
- **Ham veri yüklenmedi** (lisans/telif belirsizliği): EVDS ham indirmeleri (`*_ham.csv`, `finansal_hesaplar_uzun.csv`, `odemeyen_payi_aylik.csv`), TÜİK `.xls` dosyaları, TCMB PDF'leri. Bunlar yerelde indirilmelidir.

## Nasıl çalıştırılır
```
pip install numpy pandas scipy networkx pytest matplotlib
pytest -q tests                                   # 3 test
(cd ortak/mahsuplasma_paketi && pytest -q)        # 12 test
(cd docs/analiz_adim12/model && pytest -q)        # 1 test
(cd ortak/mahsuplasma_paketi && python ornekler/calistir.py)
```
`adim1/` ve `adim2/` betikleri kaynak depodaki düz klasör yapısını (`KOK = betik klasörü`, paket `KOK/mahsup`) ve ham veriyi bekler; burada arşiv olarak durur. Yeniden üretmek için zarar-teorisi deposunda ham veriyle çalıştırın.

## Sınırlar
Kenar dağılımı (çekim/RAS) gözlenmedi; tam graf oranları üst sınırdır. Kaynaklar ve dönemler farklı (2024 NACE, 2026-Q1 EVDS). KOBİ/büyük ayrımı vekildir. Nedensellik iddiası yoktur.

## Lisans
MIT (kaynak depo ile aynı).

## Simülasyon (sim/)
`sim/mahsup_sim.py` Adım 1 + Adım 2'yi 24 ay aylık dinamik ve Monte Carlo (N=5000) ile simüle eder; EVDS `TP.KTF17` ve ödemeyen payı verisine kalibre eder. Ayrıntı: `sim/RAPOR.md`, `sim/ON_KAYIT.md`, `sim/SAPMA.md`.
- Adım 1, tam katılım: 2. yıl faiz düşüşü 737,0 milyar TL [HESAP, üst sınır] = 2025 finansman giderinin %17,2'si; MC medyanı 446,7 (P5–P95 236,8–724,2) [VARSAYIM dağılımları].
- Adım 2 kaçınılan köprü kredi faizi (tam katılım, MC medyanı 3.113 milyar TL/yıl) varsayımsaldır, faiz düşüşüne eklenmez.
- TÜFE muhasebe üst sınırı (k=%100, 2. yıl): merkez senaryo 0,262 pp [HESAP]; Monte Carlo medyanı 0,150 pp (P5 0,043 / P95 0,326) [VARSAYIM].
- **Kalibrasyon: 4 hedeften 1'i tuttu** (finansman gideri 2025 geri testi, −%6,6). Faiz hedefi (1,68 pp) ve λ* istikrarı (0,022) tutmadı; G1–faiz ilişkisi ters işaretli çıktığı için kullanılamadı.
- Nedensellik iddiası yoktur. Ham veri (`sim/ham/`) yüklenmez; betik EVDS'ten `EVDS_API_KEY` ortam değişkeniyle indirir.
