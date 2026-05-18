# Riftify Seyahat Planlama Uygulaması — Kod Açıklaması

## Genel Bakış

**Riftify**, Python ve Tkinter kullanılarak geliştirilmiş kapsamlı bir seyahat planlama uygulamasıdır. Uygulama; kullanıcı hesabı, dünya haritası, ülke ve il/bölge seçimi, turistik yer keşfi, rota oluşturma, otel/ulaşım seçimi, bütçe kontrolü, yorum sistemi ve TXT rapor alma özelliklerini tek arayüzde toplar.

Bu dosya, projenin kod yapısını, sınıflarını, metodlarını, veri akışını ve önemli özelliklerinin nasıl çalıştığını açıklamak için hazırlanmıştır.

---

## Dosya Yapısı

| Dosya / Klasör | Sorumluluk |
|---|---|
| `main.py` | Uygulamanın ana arayüzü, sayfalar, harita, rota, popüler yerler ve hesap sistemi |
| `veritabani.py` | JSON veri okuma/yazma, rota ve bütçe kayıtları |
| `siniflar.py` | Seyahat, konaklama ve plan gibi OOP veri sınıfları |
| `yerlesik_bolgeler.py` | Ülke/il/bölge listeleri ve yerleşik bölge verileri |
| `gercek_veri.py` | Harita veya gerçek veri destek fonksiyonları |
| `platform_verisi.json` | Demo hesabın örnek verileri |
| `kullanici_hesaplari.json` | Kullanıcı hesap bilgileri |
| `kullanici_verileri/` | Yeni kullanıcıların ayrı veri dosyaları |
| `harita_verileri/` | Dünya haritası ve idari bölge dosyaları |
| `popular_images/` | Popüler turistik yer fotoğrafları |
| `riftify_logo.png` | Uygulama logosu |
| `README_KULLANIM_KILAVUZU.txt` | Hocaya yönelik kullanım açıklaması |

---

## 1. `main.py` — Ana Uygulama Dosyası

`main.py`, Riftify uygulamasının en önemli dosyasıdır. Arayüz sayfaları, kullanıcı giriş sistemi, harita, rota oluşturma, popüler yerler, bütçe ve rapor ekranları burada yönetilir.

### Genel Sorumluluklar

| Bölüm | Açıklama |
|---|---|
| `App` | Ana pencereyi ve oturum yönetimini kontrol eder |
| `LoginPage` | Giriş ve yeni hesap oluşturma ekranı |
| `Shell` | Sol menü, üst hesap menüsü ve sayfa geçişleri |
| `HomePage` | Ana menü ve özet ekran |
| `WorldMapPage` | İnteraktif dünya haritası |
| `RouteCreatePage` | Rota oluşturma ekranı |
| `PopularPlacesPage` | Popüler turistik yerler ekranı |
| `RoutesPage` | Kaydedilen rotalar ve TXT rapor |
| `BudgetPage` | Bütçe belirleme ve bütçe aşımı kontrolü |
| `ToolsHubPage` | Yardımcı araçlar ekranı |

---

## 1.1 `App` Sınıfı

`App`, ana Tkinter penceresini temsil eder.

### Görevleri

- Uygulama penceresini oluşturur.
- Uygulama adını ve logosunu ayarlar.
- Giriş ekranını açar.
- Giriş başarılı olunca kullanıcıya özel veri dosyasını yükler.
- Çıkış yapıldığında tekrar giriş ekranına döner.
- Şifre değiştirme penceresini açar.

### Önemli Metodlar

| Metod | Açıklama |
|---|---|
| `show_login()` | Giriş ekranını gösterir |
| `show_main(email)` | Giriş yapan kullanıcıya ait ana ekranı açar |
| `logout()` | Oturumu kapatır |
| `change_password_window()` | Şifre değiştirme ekranını açar |

### Kullanıcıya Özel Veri Mantığı

Demo hesap:

```text
hira@gmail.com / 123
```

Demo hesap `platform_verisi.json` içindeki hazır örnek verilerle açılır.

Yeni açılan hesaplar ise boş veriyle başlar ve kendi dosyasında saklanır. Böylece kullanıcıların rotaları, bütçeleri ve yorumları birbirine karışmaz.

---

## 1.2 `LoginPage` Sınıfı

Kullanıcı giriş ve hesap oluşturma ekranıdır.

### Özellikler

- E-posta ve şifre ile giriş
- Yeni hesap açma
- Aynı e-posta ile tekrar hesap açmayı engelleme
- Aynı isim-soyisimle tekrar hesap açmayı engelleme
- Şifreyi gizleme/gösterme
- Şifre değiştirme sistemine uygun hesap kaydı

### Hesap Kayıt Mantığı

Yeni hesap açılırken şu kontroller yapılır:

- İsim boş olamaz.
- Soy isim boş olamaz.
- E-posta `@gmail.com` ile bitmelidir.
- Aynı e-posta ile ikinci hesap açılamaz.
- Aynı isim ve soy isimle ikinci hesap açılamaz.
- Şifre çok kısa olamaz.

### Veri Saklama

Hesaplar `kullanici_hesaplari.json` dosyasında tutulur. Şifreler düz metin olarak değil, hash mantığıyla saklanır.

---

## 1.3 `Shell` Sınıfı

`Shell`, girişten sonra açılan ana iskelet yapıdır.

### Görevleri

- Sol menüyü oluşturur.
- Sayfa geçişlerini yönetir.
- Sağ üst hesap menüsünü gösterir.
- Şifre değiştir ve çıkış yap işlemlerini bağlar.

### Sol Menüdeki Sayfalar

| Sayfa | Açıklama |
|---|---|
| Ana Menü | Genel özet ekranı |
| Harita | Dünya haritası ve bölge seçimi |
| Rota Oluştur | Yeni seyahat planı oluşturma |
| Popüler | Popüler turistik yerler |
| Rotalar | Kaydedilen rotalar |
| Plan | Günlük plan ekranı |
| Araçlar | Bütçe, rezervasyon, belge, valiz gibi yardımcı araçlar |

### Sayfa Geçiş Mantığı

Her menü butonu `show(key)` metodunu çağırır. Bu metod açık sayfayı temizler ve istenen sayfayı yeniden oluşturur.

---

## 2. Harita Sistemi

## 2.1 `WorldMapPage` Sınıfı

`WorldMapPage`, uygulamadaki interaktif dünya haritasını yönetir.

### Görevleri

- Dünya haritasını çizer.
- Ülke sınırlarını gösterir.
- Ülke seçimini algılar.
- Seçilen ülkeye odaklanır.
- Ülkenin il/eyalet/bölge sınırlarını gösterir.
- Bölge seçilince bilgi kartı açar.
- Seçilen bölge için turistik yerler ekranını açar.

### Harita Mantığı

Harita, koordinat/polygon mantığıyla çalışır. Ülkelerin sınırları koordinat listelerinden oluşur. Program bu koordinatları ekrandaki canvas üzerine çizer.

```text
GeoJSON / koordinat verisi
        ↓
Polygon çizimi
        ↓
Canvas üzerinde ülke şekli
        ↓
Tıklanan ülke tespit edilir
        ↓
Ülkeye odaklanılır
```

### Ülke Tıklama Mantığı

Her ülke çizilirken canvas üzerinde bir tag/id alır. Kullanıcı tıkladığında hangi tag’e basıldığı bulunur ve ilgili ülke seçilir.

### Önemli Metodlar

| Metod | Açıklama |
|---|---|
| `draw()` | Haritayı çizer |
| `select_country(idx)` | Seçilen ülkeye odaklanır |
| `reset_world()` | Dünya haritasına geri döner |
| `draw_admin1_for_selected()` | Seçilen ülkenin il/eyalet/bölge sınırlarını çizer |
| `update_region_panel()` | Sağ panelde il/bölge listesini günceller |
| `show_region_info_card()` | Seçili bölge için bilgi kartı açar |
| `open_region_tourism_places()` | Seçilen bölgenin turistik yerlerini açar |

---

## 2.2 İl / Bölge Bilgi Kartı

Haritada bir il/bölge seçildiğinde bilgi kartı açılır.

### Gösterilen Bilgiler

- Nüfus
- Mahalleler / bölgeler
- Posta kodu
- İl / bölge adı
- Ülke
- Alan kodu
- En alçak nokta
- İGE

Bilgi kartının içinde **Turistik Yerler** butonu bulunur. Bu buton seçilen bölgeye ait turistik yerleri listeler.

---

## 2.3 Turistik Yerler

Seçilen il/bölge için 10 turistik mekan listelenir.

### Her Turistik Yerde

- Mekan adı
- Kategori
- Puan
- Açıklama
- Detay butonu
- Rota Ekle butonu

### Detay Ekranı

Detay ekranında kısa tarihçe gösterilir. Kullanıcı isterse buradan doğrudan rota oluşturma sayfasına geçebilir.

---

## 3. Rota Oluşturma Sistemi

## 3.1 `RouteCreatePage` Sınıfı

`RouteCreatePage`, kullanıcının yeni seyahat rotası oluşturduğu sayfadır.

### Kullanıcıdan Alınan Bilgiler

| Alan | Açıklama |
|---|---|
| Çıkış ülkesi | Rotanın başladığı ülke |
| Çıkış ili/bölgesi | Rotanın başladığı şehir/bölge |
| Varış ülkesi | Gidilecek ülke |
| Varış ili/bölgesi | Gidilecek şehir/bölge |
| Gidiş tarihi | Seyahatin başlangıç tarihi |
| Dönüş tarihi | Seyahatin bitiş tarihi |
| Ulaşım tipi | Araba, otobüs veya uçak |
| Otel | Seçilen otel |
| Not | Kullanıcının plan notu |

### Önemli Metodlar

| Metod | Açıklama |
|---|---|
| `country_selector()` | Ülke arama/seçme kutusu oluşturur |
| `depart_region_selector()` | Çıkış ili/bölgesi seçtirir |
| `region_selector()` | Varış ili/bölgesi seçtirir |
| `distance_km()` | Çıkış ve varış bölgeleri arası mesafeyi hesaplar |
| `overseas()` | Deniz aşırı/farklı kıta kontrolü yapar |
| `refresh_hotels()` | Seçilen bölge için otel listesini günceller |
| `refresh_transport()` | Ulaşım seçenekleri ve maliyetleri günceller |
| `refresh_summary()` | Sağ taraftaki özet ve toplam masrafı günceller |
| `validate()` | Eksik/hatalı alan kontrolü yapar |
| `save_route()` | Rotayı JSON verisine kaydeder |

---

## 3.2 Mesafe Hesaplama

Mesafe, çıkış ili/bölgesi ve varış ili/bölgesine göre hesaplanır. Türkiye illeri için yaklaşık gerçek koordinatlar eklenmiştir.

### Mantık

```text
Çıkış ili koordinatı
        ↓
Varış ili koordinatı
        ↓
İki nokta arası mesafe
        ↓
Ulaşım maliyeti
```

Bu sayede örneğin Türkiye / İstanbul → Türkiye / Malatya rotası ülke merkezinden değil şehirler arası hesaplanır.

---

## 3.3 Deniz Aşırı Kontrolü

`overseas()` metodu, araba ve otobüs seçiminin mantıklı olup olmadığını kontrol eder.

### Kontrol Edilen Durumlar

- Farklı kıta seçimi
- Ada ülkeleri
- Deniz aşırı ülkeler
- Çok uzun ve pratikte uçuş gerektiren rotalar

### Sonuç

Eğer rota deniz aşırıysa:

- Araba seçilemez.
- Otobüs seçilemez.
- Uçak seçilmesi istenir.

Kullanıcıya uyarı gösterilir.

---

## 3.4 Otel Sistemi

Seçilen varış bölgesine göre 10 otel önerisi oluşturulur.

### Otel Bilgileri

- Otel adı
- Gecelik fiyat
- Sıralama
- Toplam konaklama maliyeti

Toplam konaklama maliyeti:

```text
gecelik fiyat × gece sayısı
```

---

## 3.5 Ulaşım Sistemi

Ulaşım türleri:

- Araba
- Otobüs
- Uçak

### Araba Seçilirse

- Mesafe
- Tahmini süre
- Benzin maliyeti
- Gişe maliyeti
- Toplam yol masrafı

hesaplanır.

### Otobüs Seçilirse

- Otobüs firmaları listelenir.
- Fiyat ve süre gösterilir.
- Deniz aşırı rotalarda engellenir.

### Uçak Seçilirse

- Uçak firmaları listelenir.
- Fiyat ve süre gösterilir.
- Deniz aşırı rotalarda önerilen seçenektir.

---

## 4. Popüler Yerler Sistemi

## 4.1 `PopularPlacesPage` Sınıfı

Popüler turistik yerlerin listelendiği sayfadır.

### İçerik

- Fotoğraf
- Yer adı
- Ülke
- Puan
- Kategori
- Kısa açıklama
- Detay butonu
- Rotaya Ekle butonu

### Popüler Yer Detayı

Detay ekranında:

- Büyük fotoğraf
- Kısa tarihçe
- Bugünün hava durumu
- En iyi oteller
- Ortalama bütçe
- Ziyaretçi yorumları
- Rota Ekle butonu

bulunur.

---

## 4.2 Popüler Yerden Rota Ekleme

Kullanıcı popüler yerde **Rotaya Ekle** dediğinde mesaj göstermek yerine direkt `RouteCreatePage` sayfasına yönlendirilir.

Otomatik dolan bilgiler:

- Varış ülkesi
- Varış bölgesi
- Gezilecek yer

Bu sayede kullanıcı aynı bilgileri tekrar yazmak zorunda kalmaz.

---

## 4.3 Yorum Sistemi

Popüler yerlerde örnek yorumlar bulunur. Bazı yorumlar olumlu, bazıları olumsuzdur.

### Yorum Yazma Kuralı

Kullanıcı bir popüler yere yorum yazmak için önce o yeri içeren rotayı tamamlamalıdır.

### Akış

```text
Popüler yerden rota oluştur
        ↓
Rotalar sayfasında rotayı Tamamla
        ↓
Popüler yer için yorum yazma ekranı açılır
        ↓
Yorum kullanıcı verisine kaydedilir
```

---

## 5. Rotalar Sistemi

## 5.1 `RoutesPage` Sınıfı

Kaydedilen rotaların listelendiği sayfadır.

### Yapılabilen İşlemler

- Rota detayını açma
- Otomatik özet gösterme
- TXT rapor oluşturma
- Rotayı tamamlandı olarak işaretleme
- Popüler yer rotası tamamlandıysa yorum yazma

### Rota Kaydı Alanları

| Alan | Açıklama |
|---|---|
| `seyahat_id` | Benzersiz rota kimliği |
| `baslik` | Rota başlığı |
| `baslangic` | Çıkış ülke/il |
| `bitis` | Varış ülke/il |
| `tarih` | Gidiş tarihi |
| `donus_tarihi` | Dönüş tarihi |
| `otel` | Seçilen otel |
| `ulasim` | Ulaşım tipi |
| `toplam_masraf` | Tahmini toplam maliyet |
| `durum` | Planlanıyor / Tamamlandı |

---

## 5.2 TXT Rapor

Rota için dışarı aktarılabilir TXT rapor oluşturulur.

### Raporda Bulunanlar

- Rota başlığı
- Çıkış ve varış bilgileri
- Tarihler
- Otel
- Ulaşım
- Toplam masraf
- Notlar

Bu özellik, kullanıcının seyahat planını dosya olarak almasını sağlar.

---

## 6. Bütçe Sistemi

## 6.1 `BudgetPage` Sınıfı

Kullanıcı toplam seyahat bütçesini belirler.

### Yapılabilenler

- Toplam bütçe girme
- Bütçeyi kaydetme
- Planlanan harcamayı görme
- Kalan bütçeyi görme

### Rota Oluştururken Bütçe Kontrolü

Rota oluşturma sırasında toplam masraf hesaplanır. Eğer bu masraf kullanıcının bütçesini aşarsa uyarı gösterilir:

```text
Bütçenizi artırın veya daha ekonomik seçim yapın.
```

Bu kontrol, kullanıcı daha rota kaydetmeden maliyet farkındalığı sağlar.

---

## 7. Kullanıcı ve Veri Sistemi

## 7.1 Hesap Dosyası

Kullanıcı hesapları `kullanici_hesaplari.json` dosyasında tutulur.

### Hesap Alanları

- ad
- soyad
- email
- password_hash

Şifreler düz metin değil, hash olarak tutulur.

---

## 7.2 Kullanıcıya Özel Veri

Demo hesap hazır verilerle gelir.

Yeni kullanıcılar:

- Boş rota listesiyle başlar.
- Boş bütçe ile başlar.
- Kendi yorumlarını ve rotalarını ayrı dosyada saklar.

Bu veriler `kullanici_verileri/` klasöründe tutulur.

---

## 8. `veritabani.py` — Veri Katmanı

`veritabani.py`, JSON veri dosyalarının okunması ve yazılması için kullanılır.

### Görevleri

- Varsayılan veri oluşturma
- Kullanıcıya özel veri dosyası açma
- Seyahatleri kaydetme
- Bütçe kayıtlarını saklama
- Rota ve rezervasyon verilerini tutma
- Program kapanıp açılsa bile verilerin korunmasını sağlama

### Örnek Veri Akışı

```text
Kullanıcı rota kaydeder
        ↓
RouteCreatePage.save_route()
        ↓
db.veri güncellenir
        ↓
db.kaydet()
        ↓
JSON dosyasına yazılır
```

---

## 9. `siniflar.py` — OOP Sınıfları

Bu dosya, hocanın istediği nesne tabanlı yapıyı destekleyen sınıfları içerir.

### Ana Sınıflar

| Sınıf | Görev |
|---|---|
| `Seyahat` | Seyahat/rota bilgisini temsil eder |
| `Konaklama` | Otel ve fiyat bilgisini temsil eder |
| `Plan` | Rota ve aktiviteleri temsil eder |

---

## 9.1 `Seyahat` Sınıfı

Bir seyahat kaydını temsil eder.

### Özellikler

- `seyahat_id`
- `gidis_yeri`
- `varis_yeri`
- `tarih`
- `donus_tarihi`
- `ulasim`
- `toplam_masraf`

### Metodlar

| Metod | Açıklama |
|---|---|
| `ozet()` | Seyahat bilgilerini özetler |
| `rapor_olustur()` | Seyahat bilgisini rapor formatına getirir |

---

## 9.2 `Konaklama` Sınıfı

Otel ve konaklama bilgisini temsil eder.

### Özellikler

- `otel_adi`
- `fiyat`
- `gece_sayisi`

### Metodlar

| Metod | Açıklama |
|---|---|
| `toplam_fiyat()` | Gecelik fiyat × gece sayısı hesaplar |

---

## 9.3 `Plan` Sınıfı

Seyahat planını temsil eder.

### Özellikler

- `rota`
- `aktiviteler`
- `notlar`

### Metodlar

| Metod | Açıklama |
|---|---|
| `aktivite_ekle()` | Plana aktivite ekler |
| `rota_ozeti()` | Planın kısa özetini döndürür |

---

## 10. Harita Veri Dosyaları

`harita_verileri/` klasörü, dünya haritası ve idari bölge verileri için kullanılır.

### İçerik

| Dosya | Açıklama |
|---|---|
| `ulkeler_sinirlari.geojson` | Ülke sınırları |
| `idari_bolgeler_liste.json` | Ülke/il/bölge listeleri |
| `adm1_cache/` | Açılan ülkelerin bölge sınırı cache verileri |

### Harita Performansı

İndirilen veya kullanılan ülke bölge verileri cache mantığıyla saklanır. Böylece aynı ülke tekrar açıldığında veri yeniden yüklenmek zorunda kalmaz.

---

## 11. Logo ve Görsel Sistem

Uygulama logosu `riftify_logo.png` dosyasıdır.

### Kullanıldığı Yerler

- Giriş ekranı
- Sol menü
- Pencere ikonu

Popüler yer fotoğrafları `popular_images/` klasöründe tutulur.

### Görsel Mantığı

Her popüler yer kartında kendi görseli gösterilir. Görseller uygulama dosyaları içinde bulunduğu için internet bağlantısı gerekmeden açılır.

---

## 12. Veri Akışı

```text
Kullanıcı işlem yapar
        ↓
main.py içindeki ilgili sayfa/metod çalışır
        ↓
db.veri güncellenir
        ↓
veritabani.py kaydetme işlemi yapar
        ↓
JSON dosyası güncellenir
        ↓
Arayüz yenilenir
```

Örnek: Popüler yerden rota oluşturma

```text
Popüler yer kartı
        ↓
Rotaya Ekle butonu
        ↓
Shell.show("route_create")
        ↓
RouteCreatePage otomatik dolar
        ↓
Kullanıcı tarih, otel, ulaşım seçer
        ↓
save_route()
        ↓
JSON verisine rota kaydedilir
```

---

## 13. Hata Kontrolleri

Projede birçok hata kontrolü vardır.

| Kontrol | Açıklama |
|---|---|
| Boş giriş alanı | Kullanıcı uyarılır |
| Aynı e-posta | İkinci hesap açılması engellenir |
| Geçmiş tarih | Rota oluşturulamaz |
| Dönüş tarihi önceyse | Hata verilir |
| Çıkış ili seçilmediyse | Rota kaydedilmez |
| Otel seçilmediyse | Rota kaydedilmez |
| Deniz aşırı araba/otobüs | Engellenir |
| Bütçe aşımı | Kullanıcı uyarılır |

---

## 14. Hocaya Teknik Açıklama İçin Kısa Özet

Bu proje; Python, Tkinter ve JSON kullanılarak geliştirilmiş kapsamlı bir seyahat planlama uygulamasıdır. Kullanıcı hesap sistemi, harita, ülke/il seçimi, turistik yerler, rota oluşturma, otel/ulaşım seçimi, bütçe kontrolü, yorum sistemi ve TXT rapor özellikleri bulunur.

Kod yapısında `main.py` arayüz ve sayfa yönetimini, `veritabani.py` veri saklama işlemlerini, `siniflar.py` ise hocanın istediği OOP sınıf yapısını temsil eder. Harita sistemi koordinat/polygon mantığıyla çalışır. Rota sistemi ise şehirler arası mesafe, ulaşım türü ve otel maliyetini birleştirerek toplam seyahat masrafı üretir.

Proje, hocanın istediği `Seyahat`, `Konaklama` ve `Plan` sınıf mantığını karşılar. Bunun yanında harita, bütçe, popüler yer, yorum, kullanıcı hesabı ve rapor sistemiyle daha kapsamlı hale getirilmiştir.
