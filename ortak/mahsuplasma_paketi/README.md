# Çoklu Mahsuplaşma Modeli

Firmalar arası TL borç zincirlerini **çok taraflı mahsuplaşma** ile çözen,
kalan borcu **yukarıdan aşağıya nakit akışıyla** ödeten ve sonunda
**kimin kilitli, kimin gerçekten batık olduğunu** ayıran bir mekanizma modeli.

> Bu bir öngörü modeli değil, bir **mekanizma laboratuvarıdır**. Sentetik
> veriyle çalışır. Asıl çıktısı rakamlar değil, zincirin hangi halkasının
> hangi koşulda koptuğudur.

## Fikir, tek paragrafta

A, B'ye 100 borçlu; B, C'ye 100; C de A'ya 100. Kimse aslında net borçlu
değil, ama herkes "önce alacağımı tahsil edeyim" diye beklediği için üçü de
nakit sıkışıklığına düşer ve krediye koşar. Mahsuplaşma bu döngüyü kâğıt
üzerinde kapatır. Geriye kalan borç **gürültüden arınmış** borçtur: onu
ödeyemeyen firma kilitli değil, gerçekten batıktır. Model bu ayrımı yapar.

## Zincir (modelin aşamaları)

| # | Aşama | Ne yapıyor | Kod |
|---|-------|-----------|-----|
| 1 | Brüt durum | Mahsup yok, herkes vadesi gelince elindeki nakitle öder | `sirali_odeme` |
| 2 | Mahsup | Döngüler silinir, **net pozisyonlar korunur** | `optimal_mahsup`, `dongu_iptali` |
| 3 | Akışla ödeme | Kalan borç tur tur, yukarıdan aşağı ödenir (tasfiye değil) | `sirali_odeme` |
| 4 | Şart kaldıracı | Holdingin ödemesi vergi yapılandırma/teşvik/ihale şartına bağlanır | `holding_odeme_orani → 1` |
| 5 | Teşhis | kilitli / batık / sağlam; gerçek zarar | `eisenberg_noe`, `teshis` |
| 6 | Ücret kanalı | Serbest kalan likiditenin ücrete geçişi (β) + asgari ücret | `Parametreler` |
| 7 | Döviz kanalı | TL açığından doğan döviz talebi düşer, ithal girdi talebi **düşmez** | `_doviz_talebi` |

### Teknik çekirdek

- **Optimal mahsup:** Fleischman, Dini & Littera (2020) yaklaşımı. Var olan
  ticari kenarlar üzerinde, her firmanın net pozisyonu sabit tutularak toplam
  brüt borcu en aza indiren **minimum maliyetli akış** problemi.
- **Ödeme kapasitesi:** Eisenberg & Noe (2001) takas vektörü. Tam
  koordinasyonla eşzamanlı ödemede bile ödenemeyen kısım = **gerçek zarar**.
- **Kilitli firma** = sıralı ödemede temerrüde düşen ama Eisenberg-Noe'da
  ödeme gücü yeten firma. Sorunu ödeme gücü değil, sıra ve koordinasyon.

## Tek sistemle bağlantı

Bu klasör RAPOR.md'deki beş adımın ilk üçünü modeller:

| Rapordaki adım | Modeldeki karşılığı |
|---|---|
| 1. E-fatura eşleşmesi, kapalı döngü kapanır | `optimal_mahsup` (aşama 2) |
| 2. Kalan net borç üstten alta akışla ödenir | `sirali_odeme` + şart kaldıracı (aşama 3-4) |
| 3. Akış banka kredisiyle çevrilmez | Model kredi kullanmaz; "kredi ihtiyacı" sütunu, kredi olmadan açıkta kalan tutarı gösterir |
| 4. Hedef primli endeksli senet | Modellenmedi |
| 5. Konut / kira kolu | Modellenmedi |

## Kurulum ve çalıştırma

```bash
cd mahsup
pip install networkx pytest
python ornekler/calistir.py
python -m pytest -q
```

```python
from mahsuplasma import calistir, Parametreler, rapor_yaz
from mahsuplasma.senaryo import turkiye_tipi

s = calistir(turkiye_tipi(), Parametreler(asgari_ucret_artisi=0.25))
print(rapor_yaz(s))
```

## Örnek çıktı (sentetik ağ, 3 holding + 40 aracı, tohum=42)

| Aşama | Temerrüt | Ücretini ödeyemeyen | Kredisiz açık |
|---|---|---|---|
| Brüt (mahsupsuz) | 39 | 15 | 1.740 |
| Mahsup + akış | 9 | 9 | 241 |
| + Şart kaldıracı | 9 | 7 | 218 |

Brüt borcun %46'sı silindi. 40 aracıdan 32'si **kilitli**, 7'si **batık**.
Mekanizma sonunda ücretini ödeyemeyen firma sayısı batık firma sayısına
iniyor: yani mekanizma gürültüyü temizliyor, gerçek zararı bırakıyor.

**Sıralama testi (%25 asgari ücret artışı):** artış tahsilattan *sonra*
gelirse 7 aracı ücretini ödeyemiyor; *önce* gelirse 24. Aynı politika,
farklı sıra, üç kat fark.

## Modelin söylemediği şeyler (bilinçli sınırlar)

1. **Net borçluyu silmez.** Mahsup döngüleri kapatır; holdingin net borcu
   yerinde kalır. Onu ödeten şey mahsup değil, şart kaldıracıdır (4. aşama).
2. **Enflasyon aracı değildir.** Model para yaratmaz, var olanı yeniden
   dağıtır. Kredi talebini azaltır; bunun enflasyona dolaylı etkisi ayrıca
   ve ampirik olarak test edilmelidir.
3. **Ücret aktarımı varsayımdır.** β < 1 varsayılır; serbest kalan
   likiditenin ücrete geçmesi mekanizmanın değil, pazarlık gücünün ve idari
   asgari ücretin sonucudur. Savunması en kolay iddia "istihdamın ve ödeme
   zincirinin korunması"dır.
4. **İthal girdi kaynaklı döviz ihtiyacına dokunmaz.**
5. **Sentetik veri.** Gerçek uygulamada ağ GİB e-fatura verisinden kurulmalı.
6. **Tek dönem ve tek seferlik.** Tekrarlanan mahsupta ahlaki tehlike
   (Rusya 1992: "nasılsa silinir" gecikmesi) modellenmemiştir.

## Kaynaklar

- Fleischman, T., Dini, P., Littera, G. (2020). *Liquidity-Saving through
  Obligation-Clearing and Mutual Credit.* Journal of Risk and Financial Management.
- Eisenberg, L., Noe, T. H. (2001). *Systemic Risk in Financial Systems.* Management Science.
- Ickes, B. W., Ryterman, R. (1992). *The Interenterprise Arrears Crisis in Russia.* Post-Soviet Affairs.
- Stodder, J. (2009). *Complementary Credit Networks and Macroeconomic Stability: Switzerland's Wirtschaftsring.*
