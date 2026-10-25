# Faz 2 — Adım 2: ölçülmüş düğümlü ağ (sentetik 150 firma yerine)

Çalıştır: `python3 adim2_nace_ag.py`. Çıktı: `adim2_nace_ag.csv`, `adim2_nace_dugum.csv`, `adim2_nace_ag_sonuc.json`.

`adim2.csv` yazılmaz; sentetik satır (150 firma, temerrüt 0, `modellendi`) ve H-A2 kilidi durur. Aynı mahsup paketi, başka düğümler: 17 NACE kısmı (Sektör Bilançoları 2024), 17 hane düğümü (ücret), bir dış düğüm.

## Ne ölçüm, ne varsayım

- Ölçüm: düğüm nakdi (hazır değerler), ticari borç/alacak toplamları, ücret (personel maliyeti/12), çalışan sayısı; çapa G1 firma takip oranı 2.522% (2026-09).
- Varsayım: kenar dağılımı (çekim/RAS, Faz 1); dış düğüm brüt borcu (EVDS payı 0.108 → 1,501.4 milyar); vade hepsi 1 tur; ücret aylık dilim; λ* kalibrasyonu.
- Eksik: A (tarım) YSHİ kapsamı dışı → ücret ve çalışan 0; o kısımda ücret temerrüdü ölçülemez.
- λ*: brüt aşamada firma ödenmemiş/brüt payını G1'e oturtan nakit çarpanı: **0.8931** (`kalibrasyon_varsayim`). λ=1 ölçülen nakitle koşu ayrı satır.
- β tavanı: Σücret_aylık / (Σticari borç + Σücret_aylık) = **0.0439**; sentetik 0,3 bunun ÜSTÜNDE. Orantılı dağılım varsayımı: serbest kalan likidite vadesi gelen yükümlülüklere payıyla gider; ücret payı bu kadar. Kısım bazında `adim2_nace_dugum.csv`. Üst sınır, ölçüm değil.
- Brüt aşama kredi ihtiyacı (8,328.6 milyar, λ=1) stok ölçekli köprü ihtiyacıdır; tüm ticari borç tek turda istenirse. F F.4 stoku ile karşılaştırılır, eşitlenmez.

## Senaryo satırları (milyar TL; adet)

| λ | etiket | holding | β | temerrüt brüt→mahsup→şart | ücret temerrüt brüt→şart | kredi ihtiyacı brüt→şart | istihdam korunan brüt→şart | silinen (oran) | serbest likidite | ücret piyasa kanalı | kilitli | batık |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1.0 | olcum | 0.5 | 0.3 | 15→0→0 | 14→0 | 8,328.6→0.0 | 651,881→19,789,007 | 14,602.3 (88.5%) | 208.4 | 62.5 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R+S | — |
| 1.0 | olcum | 0.5 | 0.0439 | 15→0→0 | 14→0 | 8,328.6→0.0 | 651,881→19,789,007 | 14,602.3 (88.5%) | 208.4 | 9.1 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R+S | — |
| 1.0 | olcum | 1.0 | 0.3 | 15→0→0 | 14→0 | 8,328.6→0.0 | 651,881→19,789,007 | 14,602.3 (88.5%) | 4.0 | 1.2 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R+S | — |
| 1.0 | olcum | 1.0 | 0.0439 | 15→0→0 | 14→0 | 8,328.6→0.0 | 651,881→19,789,007 | 14,602.3 (88.5%) | 4.0 | 0.2 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R+S | — |
| 0.8931 | kalibrasyon_varsayim | 0.5 | 0.3 | 15→1→1 | 14→1 | 9,022.9→0.1 | 651,881→19,455,240 | 14,602.3 (88.5%) | 278.8 | 83.7 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R | S |
| 0.8931 | kalibrasyon_varsayim | 0.5 | 0.0439 | 15→1→1 | 14→1 | 9,022.9→0.1 | 651,881→19,455,240 | 14,602.3 (88.5%) | 278.8 | 12.2 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R | S |
| 0.8931 | kalibrasyon_varsayim | 1.0 | 0.3 | 15→1→1 | 14→1 | 9,022.9→0.1 | 651,881→19,455,240 | 14,602.3 (88.5%) | 57.4 | 17.2 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R | S |
| 0.8931 | kalibrasyon_varsayim | 1.0 | 0.0439 | 15→1→1 | 14→1 | 9,022.9→0.1 | 651,881→19,455,240 | 14,602.3 (88.5%) | 57.4 | 2.5 | A+B+C+D+E+F+G+H+I+J+M+N+Q+R | S |

## Sentetik ile fark

- Sentetik: 150 aracı, şart sonrası temerrüt 0. Burada düğüm 17 kısım; temerrüt sayısı düğüm sayısına bağlıdır, firma sayısına çevrilmez. Temerrüt eden kısım = o kısmın toplulaştırılmış nakdi borcunu karşılamıyor; kısım içi dağılım görünmez.
- Silinen oranı tam grafta tabana iner (Faz 1 (b)); gerçek seyrek ağda daha düşük. Üst sınır.

## Ne denmez

- 'Adım 2 ölçüldü' denmez; düğümler ölçüm, kenarlar varsayım: `modellendi_olculmus_dugum`.
- Bu satırlar `adim2.csv`'ye ve `uc_kural_senaryo.csv`'ye taşınmaz.
