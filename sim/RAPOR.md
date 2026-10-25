# Mahsuplaşma simülasyonu (Adım 1 + Adım 2): sonuç ve kalibrasyon

Çalıştır: `python3 mahsup_sim.py` (EVDS `https://evds3.tcmb.gov.tr/igmevdsms-dis`, anahtar `EVDS_API_KEY` ortam değişkeninden) · Test: `pytest -q test_sim.py` (4/4) · Ön kayıt: `ON_KAYIT.md` (2026-10-25 16:17 +03).

## Önce sonuç
- **Adım 1 tek başına** tam katılımda yılda en fazla **737–738 milyar TL** faiz düşüşü verir [HESAP, üst sınır]. Bu, 2025 firma finansman giderinin **%17,2**'si. Monte Carlo medyanı 446,7 (P5–P95: 236,8–724,2) [VARSAYIM dağılımları].
- **Adım 2** ek olarak kaçınılan köprü kredi faizi üretir (tam katılım MC medyanı 3.113 milyar TL/yıl). Ancak bu tutar **bugün ödenen bir gider değil**, varsayımsal köprü ihtiyacının faizidir. Faiz düşüşüne eklenmez.
- TÜFE'ye muhasebe üst sınırı küçük: tam katılımda **0,15 pp** (P95 0,33) [VARSAYIM: geçiş payı ve GSYH yolu]. Nedensellik iddiası değil.
- **Kalibrasyonda 4 hedeften 1'i tuttu, 2'si tutmadı, 1'i kullanılamadı.** Ayrıntı aşağıda.

## Senaryo tablosu (2. yıl, merkez: mahsup gerçekleşme 1, spread 9,89 pp, silme 0,885; milyar TL)
| Adım | Katılım | Silinen A1 | Silinen A2 | Faiz düşüşü 1. yıl | 2. yıl | % fin. gideri 2025 | Kaçınılan köprü faizi | Kaçınılan likidite | Kredi talebi | Ücret kanalı | TÜFE üst sınır pp |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | %25 | 1.865,9 | – | 99,7 | 184,2 | 4,3 | – | – | – | – | 0,065 |
| 1 | %50 | 3.731,8 | – | 199,4 | 368,5 | 8,6 | – | – | – | – | 0,131 |
| 1 | %100 | 7.463,7 | – | 398,7 | 737,0 | 17,2 | – | – | – | – | 0,262 |
| 1+2 | %25 | 1.865,9 | 3.650,6 | 99,7 | 184,2 | 4,3 | 1.070,8 | 2.082,1 | −%10,3 | 2,3 | 0,065 |
| 1+2 | %50 | 3.731,8 | 7.301,1 | 199,4 | 368,5 | 8,6 | 2.141,6 | 4.164,3 | −%20,6 | 4,6 | 0,131 |
| 1+2 | %100 | 7.463,7 | 14.602,2 | 398,7 | 737,0 | 17,2 | 4.283,2 | 8.328,5 | −%41,2 | 9,1 | 0,262 |

Tüm satırlar [HESAP] (mekanizma) ve [VARSAYIM] (katılım, rampa). Merkez değerler mahsup gerçekleşmesini 1 aldığı için üst uçtadır. Kredi talebi = −kaçınılan köprü / ticari kredi stoku (20.232,2, 2026-10) [VARSAYIM: köprünün bankadan alınacağı]. Bu stok ölçekli bir üst sınırdır, gerçek bir kredi daralması tahmini değildir.

## Monte Carlo (N=5000; P5 / P50 / P95; 2. yıl)
| Senaryo | Faiz düşüşü | Kaçınılan köprü faizi | Kredi talebi % | TÜFE pp |
|---|---|---|---|---|
| 1, %25 | 59,2 / 111,7 / 181,0 | – | – | 0,011 / 0,038 / 0,081 |
| 1, %50 | 118,4 / 223,4 / 362,1 | – | – | 0,022 / 0,075 / 0,163 |
| 1, %100 | 236,8 / 446,7 / 724,2 | – | – | 0,043 / 0,150 / 0,326 |
| 1+2, %25 | 59,2 / 111,7 / 181,0 | 578,0 / 778,4 / 976,8 | −9,5 / −7,6 / −5,7 | 0,011 / 0,038 / 0,081 |
| 1+2, %50 | 118,4 / 223,4 / 362,1 | 1.156,1 / 1.556,8 / 1.953,6 | −19,1 / −15,2 / −11,3 | 0,022 / 0,075 / 0,163 |
| 1+2, %100 | 236,8 / 446,7 / 724,2 | 2.312,1 / 3.113,5 / 3.907,3 | −37,6 / −29,9 / −22,2 | 0,043 / 0,150 / 0,326 |

Dağılımlar [VARSAYIM]: mahsup gerçekleşme üçgen(0,25; 0,6; 1), spread üçgen(5; 9,89; 15), silme üçgen(0,40; 0,65; 0,885), geçiş payı üçgen(0; 0,3; 0,6).

## Kalibrasyon ve geri test
| Hedef | Kaynak / seri | Model | Gerçek | Tolerans | Sonuç |
|---|---|---|---|---|---|
| Ticari kredi faizi | EVDS `TP.KTF17`, aylık ort., 2026-10 [VERİ] | 53,19 (repo) | 51,51 | ±1 pp | **Tutmadı** (fark 1,68 pp). Simülasyon 51,51'i kullanır. |
| Firma finansman gideri 2025 | TCMB Sektör Bilançoları 3.177,7 (2024) / 4.280,3 (2025) [VERİ]; ticari kredi stoku EVDS `TP.HPBITABLO6.19` (BDDK tablo 6; betik indirir) | θ=0,5039, 2024'e kalibre [HESAP]; 2025 tahmini 3.998,7 | 4.280,3 | ±%15 | **Tuttu** (−%6,6, örneklem dışı) |
| λ* zaman istikrarı | `rev_adim2_sonuc.json`, 5 çapa (2024-06…2026-09) | 0,8931 | 0,8931–0,9151 | ±0,02 | **Tutmadı** (en büyük sapma 0,022) |
| Ödemeyen payı (G1) ~ faiz(t−6) | `TP.HPBITABLO6.19/.55` + `TP.KTF17`, n=29 | eğim −0,043, R² 0,32 [TAHMİN] | – | işaret > 0 | **Kullanılamadı.** İşaret beklenenin tersi: dönemde faiz düşerken G1 yükseldi. Temerrüt kanalı simüle edilmedi. |

θ, 2024'te yalnız 7 aya dayanır (seri 2024-06'da başlıyor).

## Sınırlar
- Adım 2 kenarları gözlenmedi (çekim/RAS); silinen oranlar üst sınır. Firma düzeyinde kimden kime verisi yok.
- Katılım rampası (yarı süre 6 ay) ve tüm MC dağılımları varsayım. Spread [İKİNCİL] kaynaktan.
- TÜFE satırı bir muhasebe üst sınırı (faiz düşüşü × geçiş / GSYH 2026 = 84.425 [VARSAYIM yolu, repo]); fiyat davranışı modellenmedi.
- Temerrüt/G1 etkisi ölçülemedi (yukarıda). Nedensellik iddiası yok; haberler kullanılmadı.
