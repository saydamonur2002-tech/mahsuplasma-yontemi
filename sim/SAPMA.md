# SAPMA (ON_KAYIT 2026-10-25 16:17 +03'e göre)
- EVDS ilk çekimde haftalık geldi; `frequency=5&aggregationTypes=avg` ile aylığa çevrildi (ham önbellek silinip yeniden çekildi).
- Faiz hedefi tutmadı (53,19 vs 51,51). Model, repo sabiti yerine EVDS son değerini (51,51) kullanıyor.
- G1 kanalı: ON_KAYIT'ta çıktıydı. Eğim ters işaretli çıktı; kanal kapatıldı ve `G1_degisim_pp` boş bırakıldı. MC çıktısından da çıkarıldı.
- λ* toleransı 0,022 sapmayla aşıldı; parametre değiştirilmedi, raporlandı.
- θ kalibrasyonu 2024'te 12 ay yerine 7 aya dayanıyor (veri 2024-06'da başlıyor).
- Test "k=1 Adım1 = 738,2 ±0,5" olarak kaydedilmişti. Dinamik 2. yıl rampa nedeniyle 737,0 çıkıyor. Test, tam yıllık mekanizmayı (738,2 ±0,5) ve 2. yılı (±%1) ayrı ayrı denetleyecek şekilde değişti.
- ON_KAYIT'ta olmayan ek çıktılar: kaçınılan köprü faizi, ücret kanalı (β=0,0439 × serbest likidite 208,4).
- TÜFE satırı GSYH 2026 için repodaki varsayım yolunu kullanıyor.
- Ödemeyen payı, repodaki `odemeyen_payi_aylik.csv` yerine EVDS'ten (`TP.HPBITABLO6.19`, `.55`, aynı tanım) indiriliyor; böylece betik tek başına çalışıyor. 2026-09'a kadar eski dosyayla birebir aynı. Yeni 2026-10 ayı eklendi: kredi talebi satırları 0,3–0,7 pp, G1 eğimi −0,039'dan −0,043'e değişti.
