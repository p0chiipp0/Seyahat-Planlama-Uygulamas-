
from pathlib import Path
from gercek_veri import RealWorldDataManager

def main():
    base = Path(__file__).parent / "gercek_harita_verileri"
    dm = RealWorldDataManager(base)

    print("1/3 Ülke sınırları indiriliyor / yükleniyor...")
    countries = dm.load_countries(download_if_missing=True)
    print(f"Ülke sayısı: {len(countries.get('features', []))}")

    print("2/3 GeoNames şehir verisi indiriliyor / indexleniyor...")
    dm.build_city_index()
    print("Şehir index hazır.")

    print("3/3 ADM1 sınırları ülke bazlı indiriliyor...")
    print("Bu işlem uzun sürebilir. İstersen kapatıp uygulamada ülkeye tıkladıkça otomatik indirebilirsin.")
    answer = input("Tüm ülkelerin ADM1 verisini şimdi indirmek istiyor musun? (e/h): ").strip().lower()
    if answer == "e":
        ok, fail = dm.download_all_adm1(countries, progress=print)
        print(f"Tamamlandı. Başarılı: {ok}, Hatalı: {len(fail)}")
        if fail:
            print("Hatalılar:")
            for iso, err in fail:
                print(iso, err)
    else:
        print("ADM1 toplu indirme atlandı. Uygulamada ülkeye tıklayınca o ülke otomatik indirilecek.")

if __name__ == "__main__":
    main()
