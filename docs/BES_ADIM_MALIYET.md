# Beş adımın maliyeti ve yürütme maliyeti, adım adım

Çalıştır: `python3 bes_adim_maliyet.py`. Çıktı: `bes_adim_maliyet.csv`. Maliyet satırları adım 4 ve 5'in kendi koşularındaki bantlardan; yürütme satırları `yurutme_maliyet.py` modelinden. Tüm sayılar varsayım bandı; ölçüm değil.

Yürütme maliyeti = tespit + tahsil + idari maliyet. Model (`yurutme_maliyet.py`): yürütme = program akışı × ρ. Program akışı: adım 1'de ortak stok, adım 2'de mahsupla silinen, adım 3'te yıllık duran faiz, adım 4'te prim toplamı, adım 5'te Ho→Ha transferi; adım 1 (ortak stok) ve 2 (mahsupla silinen) için stok, yalnız alt ρ ile üst sınır; adım 3 (duran faiz) için yıllık akış. ρ bandı varsayım: %0,4 / %9 / %25 (pilot payı) / %29; alt, orta ve üst uçlar Grosh'a atfedilen hedefleme idaresi aralığı (ikincil kaynak, doğrulanmadı), %25 `hekis_model` pilot payı (karar). Bileşenlere (tespit/tahsil/idari) ayrılmadı: yalnız toplam.

## Maliyet nereden geliyor (sırayla)

**Genel kural.** Yürütme maliyeti = program akışı × ρ. Akış her adımın kendi koşusundan okunur; ρ (tespit + tahsil + idari payı) dışarıdan gelen bir orandır ve hiçbir adımın ölçümü değildir. ρ'nun dört değeri: %0,4 / %9 / %29, Grosh'a atfedilen hedefleme idaresi aralığının alt ucu, bildirilen ortalaması ve üst ucu (ikincil kaynak, doğrulanmadı); %25 `hekis_model` pilotundaki pay (bedel/sübvansiyon ≥ 1,25; karar).

**Adım 1.** Akış, `adim1_stok.csv` TOPLAM satırındaki ortak stoktur: 20.363,4 milyar TL. Altı sektör çiftinin her birinde iki yön bacağı metinden alınır; ters yön metinde yoksa EVDS konsolide olmayan aynı-araç üst sınırı konur, çift düzeyinde ortak = min. Silinen tutarı veren kimden-kime tablosu depoda yok, bu yüzden stok silinebilecek en çok tutardır. Bu stoğa yalnız ρ'nun alt ucu (%0,4) uygulanır, sonuç 81,5 milyar TL tek seferlik üst sınırdır; %9 ve üstü gerçekçi olmayan tutar verdiği için kullanılmaz.

**Adım 2.** Akış, mahsupla silinen 14.602,3 milyar TL'dir (`adim2_nace_ag.csv`, silinen oranı %88,5). Ağ 17 NACE kısmı (Sektör Bilançoları 2024), 17 hane düğümü ve bir dış düğümden oluşur, 322 kenar vardır. Düğümler ölçümdür, kenar dağılımı çekim/RAS varsayımıdır ve tam grafta silinen oran üst sınırdır. Aynı nedenle yalnız %0,4 uygulanır: 58,4 milyar TL, tek seferlik üst sınır.

**Adım 3.** Akış, duran faizdir (`adim3_faiz_durma.csv`): D = κ·u₂·S₀, I = ψ·(r/4)·D. S₀, EVDS'te firmaların kredi yükümlülüğüdür (F.4, 2026-Q1): 25.339,8 milyar TL, ölçüm. r, ticari kredi faizidir (TP.KTF17), son gözlem 2026-09'da %53,19 ve sonrası sabit tutulur (varsayım). ψ = 3.143,4 / (0,6038 × 14.527,5) = 0,3584, Sektör Bilançoları kapsamı ile EVDS arasındaki oran. κ (0,25; 0,5; 1,0) varsayımdır. 2029'da yıllık duran faiz 1.207,6 / 2.415,6 / 4.830,8 milyar TL olur ve yürütme maliyeti bunun ρ katıdır (ρ %9'da 108,7 / 217,4 / 434,8 milyar TL/yıl).

**Adım 4.** İhraç, θ · 19.361,9 · Δu₃'tür; 19.361,9, üç ölçülmüş adres stokunun toplamıdır (hane vadeli mevduat 8.322,4 + firma vadeli mevduat 4.400,1 + gerçek kişi YP mevduat 6.639,4; 2026-Q1). θ ∈ {0,1; 0,25; 0,5}, yenileme χ ∈ {0; 0,5}, prim π ∈ {%2; %5} varsayımdır; ihraççı K′ de varsayımdır. 12 senaryoda 2029–2031 toplam prim 77,5 ile 1.058,9 milyar TL arasında, bankaların mevduat kaybından doğan yıllık kredi daralması (× 0,08) 154,9 ile 774,5 milyar TL arasındadır. Yürütme maliyeti prim toplamının ρ katıdır; ρ'nun bu adımdaki dayanağı en zayıftır, çünkü hedeflenmiş transfer idaresi için bildirilen aralık mevduat senedine taşınmıştır. Senedin endeks bacağı hesaplanmadığı için prim alt sınır olabilir.

**Adım 4.5.** Tanım repodadır (`ADIM45_BIRIM.md`): mevcut TL'den yeni fiat TL'ye geçiş, λ = 1 parite (varsayım), yeni lira altın ya da döviz üzerinde alacak değil, kur çapası 49,1274 TL/USD (`bes_yil_senaryo.csv` taban, tüm yıllarda sabit), pencere 2030-Q1..Q4. TL para stoku 16.472,8 milyar TL (2026-Q1). Plasebo kontrolü (`ADIM45_MALIYET.md`): TL bileşen payları λ'dan bağımsız aynı kalır; bu aritmetik gereğidir, para yanılsaması ve yuvarlama enflasyonu modelde yok. Fayda sıfır; tek gerçek terim yürütme maliyeti: A (banknot basımı ≈ 10 milyon $ × 49,1274 + kurum başı yazılım 20–100 bin $ × 100–1.000 kurum, varsayım) 0,59 – 5,40 milyar TL; B (tam yeni birim, GSYH 2025'in %0,3–1,0'ı, ikincil kaynak) 189,7 – 632,4 milyar TL üst referans.

**Adım 5.** Akış, ev sahibinden (Ho) kiracıya (Ha) giden transferdir (`adim5_kira_aralik.csv`). Birim kira 275,37 TL/m²/ay, EVDS serisi TP.BK.TR, 2026-Q3 (değerlemesi yapılan konutlar (kredili alım ağırlıklı); tüm kiralık stok değil), tek ölçüm. Konut alanı 90–110 m², kiracı hane oranı %25–30 varsayım; toplam hane 26.977.795 elle girilmiş dış kaynaktır. Piyasa kirası 24.783 – 30.291 TL/ay, HEKİS havuz kirası 20.000 TL/ay (model varsayımı) olduğundan fark 4.783 – 10.291 TL/ay'dır. Transfer = fark × kiracı hane × kapsama payı × 12: kapsama %20'de 77,4 – 199,9, %50'de 193,6 – 499,7, %100'de 387,1 – 999,4 milyar TL/yıl. Yürütme maliyeti transferin ρ katıdır; hane içi bir aktarım olduğu için H toplamında net maliyet değil dağılımdır.

## Adım 1: stok

- **maliyet**: `yok`. Adım 1 stok; maliyet satırı yok.
- **yürütme ρ=0.4% (üst sınır): ortak stok 20,363.4 × ρ**: 81.5 – 81.5 milyar TL (tek sefer) (`modellendi_ust_sinir`). Silinen tutar boş: ortak stok silinebilecek en çok. ρ ≥ %9 uygulanmaz: 1,833-5,905 milyar TL gerçekçi değil.

## Adım 2: temerrüt ve ücret

- **maliyet**: `yok`. Temerrüt 0, parametre; maliyet satırı yok.
- **yürütme ρ=0.4% (üst sınır): silinen 14,602.3 × ρ**: 58.4 – 58.4 milyar TL (tek sefer) (`modellendi_ust_sinir`). Mahsupla silinen (Faz 2 düğümlü ağ; kenarlar varsayım, üst sınır). ρ ≥ %9 uygulanmaz: 1,314-4,235 milyar TL gerçekçi değil.

## Adım 3: faiz durma

- **maliyet**: `yok`. Kredi ihtiyacı 0; faizin durması modellenmedi.
- **yürütme ρ=0.4% (alt), κ=0.25: duran faiz 1,207.6 × ρ**: 4.8 – 4.8 milyar TL/yıl (2029) (`modellendi_band`). κ varsayım; r_t ileri sabit (Faz 3).
- **yürütme ρ=9% (orta), κ=0.25: duran faiz 1,207.6 × ρ**: 108.7 – 108.7 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=25% (pilot payı), κ=0.25: duran faiz 1,207.6 × ρ**: 301.9 – 301.9 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=29% (üst), κ=0.25: duran faiz 1,207.6 × ρ**: 350.2 – 350.2 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=0.4% (alt), κ=0.5: duran faiz 2,415.6 × ρ**: 9.7 – 9.7 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=9% (orta), κ=0.5: duran faiz 2,415.6 × ρ**: 217.4 – 217.4 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=25% (pilot payı), κ=0.5: duran faiz 2,415.6 × ρ**: 603.9 – 603.9 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=29% (üst), κ=0.5: duran faiz 2,415.6 × ρ**: 700.5 – 700.5 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=0.4% (alt), κ=1.0: duran faiz 4,830.8 × ρ**: 19.3 – 19.3 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=9% (orta), κ=1.0: duran faiz 4,830.8 × ρ**: 434.8 – 434.8 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=25% (pilot payı), κ=1.0: duran faiz 4,830.8 × ρ**: 1207.7 – 1207.7 milyar TL/yıl (2029) (`modellendi_band`).
- **yürütme ρ=29% (üst), κ=1.0: duran faiz 4,830.8 × ρ**: 1400.9 – 1400.9 milyar TL/yıl (2029) (`modellendi_band`).

## Adım 4: adres yönlendirme (senet)

- **maliyet: prim toplamı 2029-2031**: 77.5 – 1058.9 milyar TL (`band_varsayim`). 12 senaryo; orta (θ 0,25 χ 0,5 π 0,05) 529.4. Endeks bacağı hesaplanmadı: alt sınır olabilir.
- **maliyet: kredi daralması (tepe, yıllık)**: 154.9 – 774.5 milyar TL/yıl (`band_varsayim`). Orta 387.2. Banka mevduat kaybı × 0,08.
- **yürütme ρ=0.4% (alt)**: 0.3 – 4.2 milyar TL (2029-31) (`modellendi_band`). Prim toplamı × ρ. ρ dayanağı zayıf: hedeflenmiş transfer idaresi aralığı senet ihracına taşındı.
- **yürütme ρ=9% (orta)**: 7.0 – 95.3 milyar TL (2029-31) (`modellendi_band`). Orta senaryo prim 529.4 × ρ = 47.6.
- **yürütme ρ=25% (pilot payı)**: 19.4 – 264.7 milyar TL (2029-31) (`modellendi_band`). hekis_model pilot SAFETY=1,25 (karar).
- **yürütme ρ=29% (üst)**: 22.5 – 307.1 milyar TL (2029-31) (`modellendi_band`).

## Adım 4.5: yeni para birimi (plasebo)

- **fayda**: 0 – 0 milyar TL (`plasebo`). TL bileşen payları λ'dan bağımsız (aritmetik gereği); repo tanımı: ADIM45_BIRIM.md, λ=1 parite.
- **yürütme A: basım + yazılım**: 0.59 – 5.40 milyar TL (tek sefer, 2030 penceresi) (`modellendi_band`). Basım ≈ 10 milyon $ × 49,1274 (sabit çapa) + kurum başı yazılım 20-100 bin $ × N (100-1.000, varsayım).
- **yürütme B: tam yeni birim (GSYH %0,3-1,0), üst referans**: 189.7 – 632.4 milyar TL (tek sefer) (`modellendi_band`). GSYH 2025 63,240.5 milyar TL (tavan_akis.csv); aralık ikincil kaynak.

## Adım 5: kira

- **maliyet: Ho→Ha transferi, kapsama %20**: 77.4 – 199.9 milyar TL/yıl (`band_varsayim`). H içi aktarım; H toplam NL 0.
- **maliyet: Ho→Ha transferi, kapsama %50**: 193.6 – 499.7 milyar TL/yıl (`band_varsayim`).
- **maliyet: Ho→Ha transferi, kapsama %100**: 387.1 – 999.4 milyar TL/yıl (`band_varsayim`).
- **yürütme ρ=0.4% (alt), kapsama %20**: 0.3 – 0.8 milyar TL/yıl (`modellendi_band`). Transfer × ρ.
- **yürütme ρ=9% (orta), kapsama %20**: 7.0 – 18.0 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=25% (pilot payı), kapsama %20**: 19.4 – 50.0 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=29% (üst), kapsama %20**: 22.4 – 58.0 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=0.4% (alt), kapsama %50**: 0.8 – 2.0 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=9% (orta), kapsama %50**: 17.4 – 45.0 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=25% (pilot payı), kapsama %50**: 48.4 – 124.9 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=29% (üst), kapsama %50**: 56.1 – 144.9 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=0.4% (alt), kapsama %100**: 1.5 – 4.0 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=9% (orta), kapsama %100**: 34.8 – 89.9 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=25% (pilot payı), kapsama %100**: 96.8 – 249.8 milyar TL/yıl (`modellendi_band`).
- **yürütme ρ=29% (üst), kapsama %100**: 112.3 – 289.8 milyar TL/yıl (`modellendi_band`).

## Ne denmez

- 'Yürütme maliyeti ölçüldü' denmez; ρ bandı varsayım, program akışı bant. Adım 1 ve 2 stok mahsubu: yalnız alt ρ, üst sınır; bu oran stok temizliği için bile iyimser olabilir.
- ρ'nun dayanağı ikincil kaynak (Grosh'a atfedilen %0,4-29); adım 4'te (mevduat senedi) daha da zayıf.
- Adım 4 ve 5 maliyetleri toplanmaz: biri prim ve kredi daralması, öteki hane içi aktarım.
- Bantlar güven aralığı değil; varsayım aralığının uçları.
