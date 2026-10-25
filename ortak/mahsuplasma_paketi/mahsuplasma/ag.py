"""Borç ağı: kim kime ne kadar TL borçlu.

Düğümler üç katmandan birindedir:
    "holding"  -> zincirin tepesi, vadeyi uzatan taraf
    "araci"    -> KOBİ / tedarikçi, konkordato zincirinin kırılgan halkası
    "hane"     -> ücretliler (ücret alacağı olan taraf)

Kenarlar (borclu -> alacakli, tutar, vade) biçimindedir. Vade, ödemenin
hangi turda istendiğini gösterir; sıralama senaryoları bunun üzerinden kurulur.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import copy

KATMANLAR = ("holding", "araci", "hane")


@dataclass
class Firma:
    ad: str
    katman: str
    nakit: float = 0.0          # dışsal likidite (e_i)
    doviz_borcu: float = 0.0    # mevcut döviz borcu (TL karşılığı)
    ithal_girdi_ihtiyaci: float = 0.0  # mahsuplaşmayla azalmayan döviz ihtiyacı
    calisan: int = 0

    def __post_init__(self):
        if self.katman not in KATMANLAR:
            raise ValueError(f"Bilinmeyen katman: {self.katman}")


@dataclass
class Borc:
    borclu: str
    alacakli: str
    tutar: float
    vade: int = 1
    ucret: bool = False  # ücret borcu mu (firma -> hane)


@dataclass
class BorcAgi:
    firmalar: dict[str, Firma] = field(default_factory=dict)
    borclar: list[Borc] = field(default_factory=list)

    # ---- kurulum ----
    def firma_ekle(self, firma: Firma) -> None:
        self.firmalar[firma.ad] = firma

    def borc_ekle(self, borclu: str, alacakli: str, tutar: float,
                  vade: int = 1, ucret: bool = False) -> None:
        if borclu == alacakli or tutar <= 0:
            return
        for ad in (borclu, alacakli):
            if ad not in self.firmalar:
                raise KeyError(f"Ağda olmayan düğüm: {ad}")
        self.borclar.append(Borc(borclu, alacakli, float(tutar), vade, ucret))

    def kopya(self) -> "BorcAgi":
        return copy.deepcopy(self)

    # ---- özet büyüklükler ----
    def matris(self) -> dict[tuple[str, str], float]:
        """Aynı yöndeki borçları toplar: (i, j) -> L_ij."""
        m: dict[tuple[str, str], float] = {}
        for b in self.borclar:
            m[(b.borclu, b.alacakli)] = m.get((b.borclu, b.alacakli), 0.0) + b.tutar
        return m

    def brut_borc(self) -> float:
        return sum(b.tutar for b in self.borclar)

    def toplam_yukumluluk(self) -> dict[str, float]:
        out = {ad: 0.0 for ad in self.firmalar}
        for b in self.borclar:
            out[b.borclu] += b.tutar
        return out

    def toplam_alacak(self) -> dict[str, float]:
        out = {ad: 0.0 for ad in self.firmalar}
        for b in self.borclar:
            out[b.alacakli] += b.tutar
        return out

    def net_pozisyon(self) -> dict[str, float]:
        """Alacak - borç. Mahsuplaşma bunu DEĞİŞTİREMEZ (temel kısıt)."""
        y, a = self.toplam_yukumluluk(), self.toplam_alacak()
        return {ad: a[ad] - y[ad] for ad in self.firmalar}

    def katmana_gore(self, katman: str) -> list[str]:
        return [ad for ad, f in self.firmalar.items() if f.katman == katman]
