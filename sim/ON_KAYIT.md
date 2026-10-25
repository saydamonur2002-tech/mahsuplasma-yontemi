# ON_KAYIT — mahsup_sim (yazıldı: 2026-10-25 16:17 +03, veri çekilmeden/bakılmadan önce)

## Çıktılar (yıllık, 2026 baz, 24 ay aylık dinamik)
1. Silinen borç stoku (milyar TL)  2. Firma faiz gideri düşüşü (milyar TL/yıl, % finansman gideri)
3. Nakit/likidite ihtiyacı (köprü kredi) 4. Ödemeyen payı (G1 firma takip oranı) değişimi
5. Kredi talebi değişimi (ticari kredi stoku %) 6. TÜFE'ye olası yansıma: yalnız muhasebe üst sınırı = faiz düşüşü × geçiş payı / nominal GSYH [VARSAYIM]; nedensellik değil.

## Senaryolar
Katılım k ∈ {%25, %50, %100} × {Adım1 yalnız, Adım1+2}. 6 senaryo.

## Mekanizma (repodan, değiştirilmez)
Adım1 üst sınır 0,2582; Adım2 ağ silinen %88,5 (14.602,3); λ*=0,8931; β=0,0439; Adım1 net faiz düşüşü 738,2 (k=1).
Aylık yayılım: katılım lojistik rampa (yarı süre ~6 ay, [VARSAYIM]).

## Monte Carlo (N=5000)
mahsup gerçekleşme üçgen(0,25;0,6;1), spread üçgen(5;9,89;15 pp), silme üçgen(0,40;0,65;0,885), geçiş payı üçgen(0;0,3;0,6) [VARSAYIM].

## Kalibrasyon hedefleri ve tolerans
- Ticari kredi faizi TP.KTF17 son değer (EVDS) → model faiz; tolerans ±1 pp
- Firma finansman gideri 2024=3.177,7 / 2025=4.280,3 mlr (Sektör Bilançoları) → baz yıl geri testi: model örtük faiz × borç stoku; tolerans ±%15
- G1 ödemeyen payı (odemeyen_payi_aylik.csv) 2026-09 = λ* çapası; geri test 2024-06…2026-09 çapalarında λ* tekrar üretimi, tolerans ±0,02
- Tutmayan hedef raporlanır, saklanmaz.

## Başarı kriteri
Testler (test_sim.py): k=1 Adım1 merkezde 738,2 ±0,5; MC P5≤merkez≤P95; tüm çıktılar sonlu; geri test tablosu dolu.
