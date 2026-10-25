# Mahsuplaşma — sektörel etki (EVDS)

## Tekrar

```bash
python3 mahsup_sektor_evds.py
```

Girdi yalnızca EVDS (`evds_cek.fetch_group`). Çıktılar: `mahsup_evds_ham.csv`, `mahsup_sektor_donem.csv`, `mahsup_sektor_ozet.json`.

## Tanım

- **Sektör:** TCMB finansal hesaplar hazneleri H, F, B, K, D (NACE değil).
- **Kenar:** Aylık kredi + diğer hesap servisi × enstrüman bazlı L^m paylaşımı (trilyon TL/ay). Bilateral fatura yok; `kalibre_matris` varsayımı.
- **Mahsup:** `optimal_mahsup` — net pozisyon sektör bazında korunur; brüt çıkış düşer.

## Son koşu (EVDS çekim tarihi: depo)

| Dönem | Brüt (TL/ay) | Mahsup sonrası | Silinen |
| --- | ---: | ---: | ---: |
| 2025-Q4 | 2,90 | 1,68 | %42,1 |
| 2026-Q1 | 3,09 | 1,77 | %42,1 |

**2026-Q2:** EVDS finansal hesaplarda henüz yok (son gözlem 2026-Q1).

### 2026-Q1 — sektör brüt **çıkış** silinmesi (TL/ay)

| Hazne | Silinen | Oran (kendi brüt çıkışına) |
| --- | ---: | ---: |
| B (bankalar) | 0,425 | %95,5 |
| F (firmalar) | 0,302 | %18,1 |
| D | 0,256 | %100* |
| K | 0,245 | %100* |
| H | 0,090 | %19,1 |

\*K ve D’de mahsup sonrası brüt çıkış sıfıra iner; net alacaklı pozisyon korunur.

## Sınır

- Ödeme/temerrüt simülasyonu yok; yalnızca brüt yükümlülük mahsupu.
- 150 firma / KAP / e-fatura ağı değil; makro hazne ağı.
