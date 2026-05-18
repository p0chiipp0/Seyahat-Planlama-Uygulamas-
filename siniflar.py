
from dataclasses import dataclass, field
from typing import List


@dataclass
class Gezgin:
    gezgin_id: str
    ad: str
    email: str
    telefon: str = ""

    def bilgi(self):
        return f"{self.ad} ({self.email})"


@dataclass
class Seyahat:
    seyahat_id: str
    baslik: str
    baslangic: str
    bitis: str
    tarih: str
    butce: float
    tip: str = "Kültür"
    durum: str = "Planlanıyor"
    duraklar: List[dict] = field(default_factory=list)

    def durak_ekle(self, durak: dict):
        self.duraklar.append(durak)

    def rota_olustur(self):
        durak_adlari = [d.get("sehir", "") for d in self.duraklar]
        return " → ".join([self.baslangic] + durak_adlari + [self.bitis])

    def butce_hesapla(self):
        return self.butce + sum(float(d.get("harcama", 0) or 0) for d in self.duraklar)


@dataclass
class Durak:
    sehir: str
    gun: int
    gezilecek_yerler: str
    harcama: float
    not_metni: str = ""

    def ozet(self):
        return f"{self.sehir} - {self.gun} gün"


@dataclass
class Konaklama:
    otel_adi: str
    sehir: str
    fiyat: float
    giris_tarihi: str
    cikis_tarihi: str

    def bilgi(self):
        return f"{self.otel_adi} / {self.sehir} / {self.fiyat} TL"


@dataclass
class Plan:
    plan_id: str
    gun: str
    saat: str
    aktivite: str
    not_metni: str

    def plan_ozeti(self):
        return f"{self.gun} {self.saat}: {self.aktivite}"


@dataclass
class Rezervasyon:
    rezervasyon_id: str
    tur: str
    ad: str
    tarih: str
    durum: str = "Beklemede"

    def rezervasyon_onayla(self):
        self.durum = "Onaylandı"

    def iptal_et(self):
        self.durum = "İptal Edildi"


@dataclass
class ButceKalemi:
    kategori: str
    tutar: float
    not_metni: str = ""

    def bilgi(self):
        return f"{self.kategori}: {self.tutar} TL"


@dataclass
class GunlukPaylasimi:
    baslik: str
    konum: str
    metin: str
    duygu: str = ""
    puan: int = 5
    foto: str = ""
    tavsiye: str = ""

    def gunluk_ekle(self):
        return {"baslik": self.baslik, "konum": self.konum, "metin": self.metin}


@dataclass
class ValizEsya:
    ad: str
    kategori: str
    durum: str = "Hazırlanmadı"

    def esya_isaretle(self):
        self.durum = "Hazır"


@dataclass
class Belge:
    ad: str
    tur: str
    link: str

    def belge_ekle(self):
        return {"ad": self.ad, "tur": self.tur, "link": self.link}


@dataclass
class AcilDurumBilgisi:
    baslik: str
    bilgi: str
    not_metni: str = ""


@dataclass
class SeyahatArkadasi:
    ad: str
    telefon: str
    rol: str
    gorev: str
