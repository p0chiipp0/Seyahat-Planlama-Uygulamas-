
import json
from pathlib import Path


class VeriTabani:
    def __init__(self, path=None, empty=False):
        self.path = Path(path) if path else Path(__file__).with_name("platform_verisi.json")
        self.empty = bool(empty)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            initial = self.bos_veri() if self.empty else self.varsayilan_veri()
            self.path.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8")
        self.veri = self.yukle()

    def yukle(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return self.ensure_schema(data)
        except Exception:
            pass
        return self.bos_veri() if self.empty else self.varsayilan_veri()

    def kaydet(self):
        self.path.write_text(json.dumps(self.veri, ensure_ascii=False, indent=2), encoding="utf-8")

    def bos_veri(self):
        return {
            "seyahatler": [],
            "planlar": [],
            "butce": [],
            "rezervasyonlar": [],
            "gunlukler": [],
            "valiz": [],
            "belgeler": [],
            "acil": [],
            "arkadaslar": [],
            "checklist": [],
            "hatirlaticilar": [],
            "ayarlar": {"butce_limiti": 0},
            "populer_yorumlar": {}
        }

    def ensure_schema(self, data):
        base = self.bos_veri()
        for key, value in base.items():
            data.setdefault(key, value)
        return data

    def varsayilan_veri(self):
        return {
            "seyahatler": [
                {"seyahat_id": "S001", "baslik": "Roma - Paris Avrupa Rotası", "baslangic": "Roma", "bitis": "Paris", "tarih": "2026-06-15", "butce": 35000, "tip": "Kültür", "durum": "Yaklaşıyor", "duraklar": [
                    {"sehir": "Floransa", "gun": "1", "yerler": "Duomo, Uffizi", "harcama": "4500", "not": "Müze bileti önceden alınacak"},
                    {"sehir": "Milano", "gun": "2", "yerler": "Duomo, Navigli", "harcama": "5200", "not": "Tren saatleri kontrol edilecek"},
                    {"sehir": "Lyon", "gun": "1", "yerler": "Eski şehir, nehir kıyısı", "harcama": "3000", "not": "Kısa mola şehri"}
                ]},
                {"seyahat_id": "S002", "baslik": "Kapadokya Balon Turu", "baslangic": "İstanbul", "bitis": "Kapadokya", "tarih": "2026-07-02", "butce": 12000, "tip": "Doğa", "durum": "Planlanıyor", "duraklar": [
                    {"sehir": "Ankara", "gun": "1", "yerler": "Anıtkabir", "harcama": "1500", "not": "Kısa mola"},
                    {"sehir": "Nevşehir", "gun": "3", "yerler": "Göreme, Uçhisar, Balon turu", "harcama": "7000", "not": "Balon turu sabah erken"}
                ]},
                {"seyahat_id": "S003", "baslik": "Ege Kıyıları Yaz Planı", "baslangic": "İzmir", "bitis": "Bodrum", "tarih": "2026-08-10", "butce": 18000, "tip": "Deniz", "durum": "Planlanıyor", "duraklar": [
                    {"sehir": "Çeşme", "gun": "2", "yerler": "Alaçatı, Ilıca", "harcama": "5000", "not": "Plaj çantası hazırlanacak"},
                    {"sehir": "Kuşadası", "gun": "1", "yerler": "Efes, sahil", "harcama": "3500", "not": "Müze kart kontrol"},
                    {"sehir": "Marmaris", "gun": "2", "yerler": "Tekne turu", "harcama": "6000", "not": "Rezervasyon gerekli"}
                ]}
            ],
            "planlar": [
                {"plan_id": "P001", "gun": "1. Gün", "saat": "09:30", "aktivite": "Kolezyum Gezisi", "not": "Biletleri önceden kontrol et."},
                {"plan_id": "P002", "gun": "1. Gün", "saat": "14:00", "aktivite": "Roma Sokak Turu", "not": "Fotoğraf noktalarını işaretle."},
                {"plan_id": "P003", "gun": "2. Gün", "saat": "11:00", "aktivite": "Trenle Milano'ya geçiş", "not": "Bilet QR kodunu hazır tut."},
                {"plan_id": "P004", "gun": "3. Gün", "saat": "10:00", "aktivite": "Louvre çevresi keşfi", "not": "Müze giriş saatini kontrol et."}
            ],
            "butce": [
                {"kategori": "Konaklama", "tutar": 9000, "not": "3 gecelik otel rezervasyonu"},
                {"kategori": "Ulaşım", "tutar": 6500, "not": "Uçak ve tren biletleri"},
                {"kategori": "Yemek", "tutar": 4200, "not": "Günlük restoran bütçesi"},
                {"kategori": "Müze", "tutar": 2600, "not": "Müze ve etkinlik biletleri"},
                {"kategori": "Alışveriş", "tutar": 3000, "not": "Hediyelik ve kişisel harcama"}
            ],
            "rezervasyonlar": [
                {"rezervasyon_id": "R001", "tur": "Otel", "ad": "Roma Merkez Otel", "tarih": "2026-06-15", "durum": "Onaylandı"},
                {"rezervasyon_id": "R002", "tur": "Uçak", "ad": "İstanbul - Roma", "tarih": "2026-06-15", "durum": "Onaylandı"},
                {"rezervasyon_id": "R003", "tur": "Restoran", "ad": "Trastevere Akşam Yemeği", "tarih": "2026-06-16", "durum": "Beklemede"},
                {"rezervasyon_id": "R004", "tur": "Müze", "ad": "Louvre Giriş Bileti", "tarih": "2026-06-19", "durum": "Ödeme Gerekli"}
            ],
            "gunlukler": [
                {"baslik": "Roma'da İlk Gün", "konum": "Roma", "duygu": "Heyecanlı", "puan": "5", "foto": "Kolezyum önünde fotoğraf", "metin": "Kolezyum çevresinde yürüyüş yaptım. Tarihi sokaklar ve meydanlar gezi planına çok güzel bir başlangıç oldu.", "tavsiye": "Biletleri önceden almak zaman kazandırıyor."},
                {"baslik": "Milano Kahve Molası", "konum": "Milano", "duygu": "Keyifli", "puan": "4", "foto": "Duomo meydanı", "metin": "Duomo çevresinde kısa bir mola verdim. Kafeler ve meydan atmosferi yolculuk günlüğüne eklendi.", "tavsiye": "Navigli akşam saatlerinde daha güzel."},
                {"baslik": "Paris Akşam Işıkları", "konum": "Paris", "duygu": "Mutlu", "puan": "5", "foto": "Seine nehri", "metin": "Seine nehri çevresinde akşam yürüyüşü yaptım. Rota planının en keyifli bölümlerinden biri oldu.", "tavsiye": "Akşam yürüyüşü için rahat ayakkabı şart."}
            ],
            "valiz": [
                {"ad": "Pasaport", "kategori": "Belge", "durum": "Hazır"},
                {"ad": "Şarj aleti", "kategori": "Elektronik", "durum": "Hazır"},
                {"ad": "Diş fırçası", "kategori": "Kişisel", "durum": "Hazırlanacak"},
                {"ad": "Yağmurluk", "kategori": "Kıyafet", "durum": "Hazırlanacak"}
            ],
            "belgeler": [
                {"ad": "Uçak Bileti", "tur": "Bilet", "link": "https://www.turkishairlines.com"},
                {"ad": "Otel Rezervasyonu", "tur": "Konaklama", "link": "https://www.booking.com"},
                {"ad": "Seyahat Sigortası", "tur": "Sigorta", "link": "https://www.sigortam.net"}
            ],
            "acil": [
                {"baslik": "Acil Kişi", "bilgi": "+90 555 000 00 00", "not": "Aile iletişim numarası"},
                {"baslik": "Otel Adresi", "bilgi": "Roma Merkez Otel", "not": "Check-in 14:00"},
                {"baslik": "Konsolosluk", "bilgi": "+39 06 0000 0000", "not": "Yurt dışı acil durum"}
            ],
            "arkadaslar": [
                {"ad": "Hira Yağmur", "telefon": "+90 555 111 22 33", "rol": "Planlayıcı", "gorev": "Rota ve günlük plan"},
                {"ad": "Taha Karaman", "telefon": "+90 555 444 55 66", "rol": "Gezgin", "gorev": "Bütçe ve rezervasyon"},
                {"ad": "Eren Öztürk", "telefon": "+90 555 777 88 99", "rol": "Fotoğrafçı", "gorev": "Günlük ve fotoğraf notları"}
            ],
            "checklist": [
                {"madde": "Pasaport kontrol edildi", "durum": "Tamamlandı"},
                {"madde": "Otel rezervasyonu yapıldı", "durum": "Tamamlandı"},
                {"madde": "Döviz alındı", "durum": "Bekliyor"},
                {"madde": "Bavul hazırlandı", "durum": "Bekliyor"}
            ],
            "hatirlaticilar": [
                {"baslik": "Uçuş", "tarih": "2026-06-15", "not": "Havalimanına 3 saat erken git."},
                {"baslik": "Otel giriş", "tarih": "2026-06-15", "not": "Check-in 14:00"},
                {"baslik": "Louvre bileti", "tarih": "2026-06-19", "not": "QR bileti hazır tut."}
            ]
        }

    def get_route(self, sid):
        for r in self.veri["seyahatler"]:
            if r["seyahat_id"] == sid:
                return r
        return None

    def seyahat_ekle(self, data):
        data["seyahat_id"] = f"S{len(self.veri['seyahatler'])+1:03d}"
        data["butce"] = float(data.get("butce") or 0)
        data["duraklar"] = []
        self.veri["seyahatler"].append(data)
        self.kaydet()

    def durak_ekle(self, sid, data):
        r = self.get_route(sid)
        if not r:
            return
        r.setdefault("duraklar", []).append(data)
        self.kaydet()

    def plan_ekle(self, data):
        data["plan_id"] = f"P{len(self.veri['planlar'])+1:03d}"
        self.veri["planlar"].append(data)
        self.kaydet()

    def butce_ekle(self, data):
        data["tutar"] = float(data.get("tutar") or 0)
        self.veri["butce"].append(data)
        self.kaydet()

    def rezervasyon_ekle(self, data):
        data["rezervasyon_id"] = f"R{len(self.veri['rezervasyonlar'])+1:03d}"
        self.veri["rezervasyonlar"].append(data)
        self.kaydet()

    def gunluk_ekle(self, data):
        self.veri["gunlukler"].insert(0, data)
        self.kaydet()

    def liste_ekle(self, key, data):
        self.veri.setdefault(key, []).append(data)
        self.kaydet()
