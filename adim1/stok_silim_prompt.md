# PROMPT — Stok silimi

Rol: Titiz veri araştırmacısı. Kuramı doğrulama. Ölç. Yalnız kamuya açık kayıt. Alıntı 15 kelimeyi geçmesin. Uydurma kenar yazma. Bulamadığını "bulunamadı, X sorgu denendi" diye yaz. Birincil: TCMB Finansal Hesaplar Raporu 2026-I, kimden-kime tabloları. Haber ikincil.

Ön kayıt: `cursor/odeme-zinciri-kalicilik-f01a`. Akış mahsubu ayrı durur. 2026-Q1 brüt servis 3,09 trilyon TL/ay, mahsup sonrası 1,77, silinen yüzde 42,1. Birim trilyon TL/ay. O yüzde stoka taşınmaz. Stok birimi milyar TL, dönem sonu.

## Ne ölçülür

Stok silimi, aynı çiftin karşılıklı bakiyesinin alt bacağını düşürmektir. Net pozisyon sabit kalır. Gözlenen tahsilat değildir. Sürtünmesiz üst sınırdır.

İki sütun. Birleştirilmez.

1. Araç ayrı. Kredi yalnız krediyle, mevduat yalnız mevduatla, borçlanma senedi yalnız senetle mahsup edilir. Farklı araç aynı çiftte silinmez.
2. Araç birleşik. Aynı çiftte kredi, mevduat ve senet tek havuzda mahsup edilir. Bu model tercihidir, muhasebe işlemi değildir. "Firma mevduatını krediye saydı" diye yazılmaz.

## Girdi

TCMB Finansal Hesaplar Raporu 2026-I, kimden-kime.

- Kredi: https://www.tcmb.gov.tr/wps/wcm/connect/26eee1f5-1c00-435e-8309-4b60702f4ee6/Finansal+Hesaplar+Raporu_2026Q1.pdf
- Ayrı bölüm: https://www.tcmb.gov.tr/wps/wcm/connect/bf500c17-e3d5-40bd-8475-370caca9c6fd/VII.+Kimden-Kime+Tablolar%C4%B1.pdf

Yazılacak çiftler, raporda sayı varsa: finansal olmayan kuruluş ↔ parasal ve finansal kuruluş, hane ↔ parasal ve finansal kuruluş, parasal ve finansal kuruluş kendi içi, genel yönetim, dünyanın geri kalanı.

Karşı taraf yazılmayan kalem stoka girmez. Hisse ve özkaynak girmez. Diğer borç ve diğer alacak girmez. "Karşı taraf yok" diye ayrı satır.

Finansal kuruluş, repo B haznesi değildir. B, TCMB ayrılmış bankadır. Raporda banka alt kırılımı yoksa "banka ayrılmadı" yaz. B hazne silme oranını bu tabloya yapıştırma.

## Kod

Çıktı `stok_silim.csv`. Sütun: arac, alacakli, borclu, stok, karsi_bacak, silinen, net_kalan, yontem (arac_ayri / arac_birlesik), kaynak_url, alinti.

Silinen = min(bacak, karşı bacak). Karşı bacak yoksa silinen boş. Sıfır yazma.

Kendi içi mevduat (10.258 milyar TL) karşı bacak raporda yoksa aday satırdır. Silinen boş kalır. Sıfırlamak uydurmadır.

Akış sonucu bu dosyaya sütun olarak girmez. Yüzde 42,1 burada yok.

## Yanlışlayıcı

H-S Stok, akışın aynı işi değildir.
- Araç ayrı silinen / ilgili stok, akıştaki yüzde 42,1'nin 15 puan yakınındaysa `hipotez_duser`. İki ölçüm karışmış olabilir.
- Araç ayrı silinen belirgin düşükse `stok_ayri`. Stok silimi akış siliminden küçük kalır.
- Karşı tarafı olmayan hisse ve diğer borç, firma yükümlülüğünün yarısından fazlaysa `stok_dar`. Silinen, firma borcunun gövdesine değmez.
- Kendi içi mevduatta karşı bacak yoksa o satır skora girmez.

## Çıktı

1. Araç ayrı ve araç birleşik, yan yana. Hangisi muhasebe, hangisi tercih, yaz.
2. `stok_silim.csv`.
3. H-S: `test_edilemez` / `stok_ayri` / `hipotez_duser` / `stok_dar`.
4. Girmeyen kalemler: hisse, diğer borç, diğer alacak. Payları.
5. Arama günlüğü: açılan pdf, okunan tablo, boş kalan çift.

Yorumu ölçümden ayır. "Borç kapandı" deme. "Karşılıklı bacak düştü, net durdu" de. Akış yüzdesini stoka uydurma.
