# Faz 1 — Adım 1: silinen miktarın hesaplanabilir sınırı (F sektörü içi)

Çalıştır: `python3 adim1_nace.py`. Çıktı: `adim1_nace.csv`, `adim1_nace_kenar.csv`, `adim1_yuzde20.csv`, `adim1_nace_sonuc.json`.

`adim1_stok.csv` hazneler arası (H, F, B′, K′, D) üst sınırdır; `silinen` sütunu boş kalır ve bu dosya onu doldurmaz. Burada başka bir nesne ölçülür: firma sektörü içindeki karşılıklı ticari borç. İki sayı toplanmaz.

## (a) Ölçüm: F konsolide olmayan − konsolide, EVDS 2026-Q1 (milyar TL)

| kod | kalem | konsolide olmayan | konsolide | sektör içi | etiket |
| --- | --- | --- | --- | --- | --- |
| ZP22 | VF.8 diğer alacaklar (ticari kredi vekili) | 44,743.7 | 4,815.1 | 39,928.6 | olcum |
| ZP44 | F.8 diğer borçlar (ticari kredi vekili) | 46,340.8 | 6,412.2 | 39,928.6 | olcum |
| ZP45 | F.0 toplam yükümlülük | 141,473.5 | 50,776.6 | 90,697.0 | olcum |

Sektör içi fark, firmaların birbirine olan alacak/borcudur; ZP22 ile ZP44 farkının eşit çıkması tutarlılık kontrolüdür. Bu sayı brüt stoktur; kaçının netleşebileceğini söylemez. Sektör Bilançoları Σ ticari alacak (13,953.2, 2024) bu stokun altındadır: kapsam (bilanço veren firmalar) ve kalem (VF.8 ticari krediden geniştir) farklı; dönem farklı. İkisi eşitlenmez.

## (b) Üst sınır: NACE 17 kısım + dış düğüm, çok taraflı netleştirme tabanı (Sektör Bilançoları 2024)

- Brüt (Σ ticari borç) 14,335.4 milyar; taban Σmax(net,0) 1,234.5; silinen_max 13,100.9 = **91.4%** (`ust_sinir_nace`).
- Kısım içi (aynı NACE) borç düğümde görünmez; dış düğüm artığı taşır. Üst sınır, ölçüm değil.
- Dış düğüm net 382.2: firmaların ticari alacağı ile borcu arasındaki fark (hane, kamu, yurt dışı, kapsam dışı).

| NACE | ticari alacak | ticari borç | net | hazır değerler | banka kredisi KV | finansman gideri | personel |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 81.1 | 105.9 | -24.7 | 35.9 | 47.1 | 20.5 |  |
| B | 142.3 | 121.0 | 21.3 | 103.4 | 55.6 | 38.9 | 91.4 |
| C | 4,434.9 | 3,869.2 | 565.8 | 2,206.4 | 1,961.5 | 1,134.0 | 2,647.1 |
| D | 534.2 | 703.3 | -169.1 | 249.5 | 104.1 | 235.6 | 112.8 |
| E | 45.1 | 50.1 | -5.0 | 10.4 | 9.8 | 7.5 | 49.9 |
| F | 1,381.2 | 1,502.1 | -120.9 | 461.3 | 237.5 | 193.3 | 616.7 |
| G | 4,909.4 | 5,720.5 | -811.2 | 1,858.3 | 1,189.0 | 730.2 | 1,465.7 |
| H | 797.4 | 745.4 | 52.1 | 580.0 | 161.0 | 231.6 | 594.9 |
| I | 224.5 | 271.8 | -47.3 | 209.0 | 90.6 | 78.6 | 457.1 |
| J | 338.4 | 277.2 | 61.2 | 256.6 | 43.4 | 75.9 | 323.3 |
| L | 136.3 | 120.3 | 16.0 | 209.6 | 27.7 | 71.6 | 58.9 |
| M | 368.1 | 416.1 | -48.0 | 308.8 | 172.3 | 234.3 | 321.2 |
| N | 410.2 | 296.1 | 114.1 | 140.5 | 75.5 | 60.3 | 712.7 |
| P | 33.9 | 29.5 | 4.4 | 68.3 | 7.6 | 4.8 | 182.0 |
| Q | 89.3 | 71.8 | 17.5 | 49.9 | 27.1 | 21.0 | 174.3 |
| R | 15.3 | 20.8 | -5.5 | 18.0 | 3.2 | 4.0 | 44.2 |
| S | 11.5 | 14.3 | -2.8 | 6.9 | 2.2 | 1.5 | 42.2 |
| DIS |  |  | 382.2 |  |  |  |  |
| TOPLAM | 13,953.2 | 14,335.4 | -382.2 | 6,772.6 | 4,215.2 | 3,143.4 | 7,894.3 |

## (c) Varsayım: çekim dağılımı + optimal mahsup

- kenar_ij ∝ TB_i · TA_j; 289 kenar; brüt 14,335.4; silinen 12,973.6 (90.5%); teorik taban 1,234.5; kalan kenar 63.
- Çekim dağılımı ölçüm değil. Tam grafta optimal mahsup (b) tabanına iner; gerçek (seyrek) ağda silinen daha az. Kenar matrisi Faz 2'ye `varsayim_dagitim` etiketiyle girdi olur.

## (d) Varsayım: oranı EVDS stokuna taşıma

- 39,928.6 × 0.9139 = **36,490.7 milyar** üst sınır (`varsayim_oran_tasima`). 2024 NACE oranı 2026-Q1 EVDS stokuna taşındı; iki kaynak, iki dönem. Varsayım.

## (e) Ölçülen bant (rev C; eski 'yüzde 20' koşusu kaldırıldı)

- Tam graf oranı 2009–2024: [0.665, 0.925], 2024: 0.914 (`ust_sinir_nace`).
- Seyrek ağ 2024 (çekim+RAS, rastgele kenar alt kümesi, LP en iyi mahsup; `varsayim_yogunluk`):
  - yoğunluk 0.25: min 0.124 / medyan 0.265 / max 0.843
  - yoğunluk 0.5: min 0.274 / medyan 0.563 / max 0.908
  - yoğunluk 0.75: min 0.492 / medyan 0.896 / max 0.907
  - yoğunluk 1.0: min 0.905 / medyan 0.905 / max 0.905
- 2026Ç1 taşıma (`varsayim_oran_tasima`): tam graf 26,556.5–36,945.9 milyar; seyrek alt uç 4,939.2 milyar.

## Ne denmez

- 'Stok yüzde X silindi' denmez; (b) ve (c) üst sınır, (d) varsayım, (e) bant (yoğunluk varsayımlı). Gerçek silinen için firma düzeyi kimden-kime gerekir (depoda yok).
- Hazneler arası `yeni_tavan` 0,2582 ile bu oran toplanmaz; biri hazneler arası, biri F içi.
