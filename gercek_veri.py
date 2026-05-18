
from pathlib import Path
import json
import urllib.request
import urllib.parse
import zipfile
import io
import csv
import unicodedata


class RealWorldDataManager:
    """Gerçek dünya harita verilerini güvenli cache sistemiyle yöneten katman.

    - Ülkeler: Natural Earth 10m Admin-0 GeoJSON
    - İl/eyalet/bölge: geoBoundaries ADM1, ülke seçilince ülke bazlı indirilir
    - Şehir koordinatları: GeoNames cities5000, isteğe bağlı indirilir

    Bu sınıf mevcut uygulama özelliklerini bozmaz; sadece harita/veri katmanını gerçek
    kaynaklardan besler. İnternet yoksa mevcut cache/veriyle çalışmayı dener.
    """

    COUNTRIES_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson"
    GEOBOUNDARIES_API = "https://www.geoboundaries.org/api/current/gbOpen/{iso3}/ADM1/"
    GEONAMES_CITIES5000_URL = "https://download.geonames.org/export/dump/cities5000.zip"

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.countries_file = self.base_dir / "countries_ne_10m.geojson"
        self.adm1_dir = self.base_dir / "adm1"
        self.adm1_dir.mkdir(exist_ok=True)
        self.cities_file = self.base_dir / "cities5000.txt"
        self.city_index_file = self.base_dir / "cities_index.json"
        self._city_index = None

    def _urlretrieve(self, url, dest):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url, timeout=60) as resp:
            data = resp.read()
        dest.write_bytes(data)
        return dest

    def _read_json(self, path):
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def load_countries(self, download_if_missing=True):
        """Natural Earth 10m ülke sınırlarını yükler."""
        if not self.countries_file.exists() and download_if_missing:
            self._urlretrieve(self.COUNTRIES_URL, self.countries_file)
        if self.countries_file.exists():
            return self._read_json(self.countries_file)
        return None

    def country_iso3(self, feature):
        props = feature.get("properties", {}) if feature else {}
        for k in ["ISO_A3", "iso_a3", "ADM0_A3", "adm0_a3", "SOV_A3", "sov_a3", "GU_A3", "gu_a3", "BRK_A3", "brk_a3"]:
            v = props.get(k)
            if v and str(v).strip() and str(v).strip() != "-99":
                return str(v).strip().upper()
        return ""

    def adm1_file_for(self, iso3):
        return self.adm1_dir / f"{str(iso3).upper()}_ADM1.geojson"

    def load_adm1(self, iso3, download_if_missing=True):
        """Seçilen ülkenin gerçek ADM1 sınırlarını geoBoundaries üzerinden yükler.
        Performans için önce simplifiedGeometryGeoJSON kullanılır.
        """
        iso3 = str(iso3 or "").upper().strip()
        if not iso3:
            return None

        out = self.adm1_file_for(iso3)
        if not out.exists() and download_if_missing:
            api_url = self.GEOBOUNDARIES_API.format(iso3=urllib.parse.quote(iso3))
            req = urllib.request.Request(api_url, headers={"User-Agent": "Routify-Travel-Planner/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                meta = json.loads(resp.read().decode("utf-8"))

            urls = []
            for key in ["simplifiedGeometryGeoJSON", "gjDownloadURL"]:
                u = meta.get(key)
                if u and u not in urls:
                    urls.append(u)

            last_error = None
            for gj_url in urls:
                try:
                    self._urlretrieve(gj_url, out)
                    data = self._read_json(out)
                    if data and data.get("features"):
                        return data
                    try:
                        out.unlink()
                    except Exception:
                        pass
                except Exception as e:
                    last_error = e
                    try:
                        if out.exists():
                            out.unlink()
                    except Exception:
                        pass

            if last_error:
                raise RuntimeError(f"{iso3} ADM1 indirilemedi: {last_error}")
            raise RuntimeError(f"{iso3} için geoBoundaries ADM1 GeoJSON bağlantısı bulunamadı.")

        if out.exists():
            data = self._read_json(out)
            if data and data.get("features"):
                return data
        return None


    def download_all_adm1(self, countries_geojson=None, progress=None):
        """İstersen tüm ülkelerin ADM1 dosyalarını toplu indirir.
        Uygulama içinde otomatik çağrılmaz; büyük veri olduğu için bilinçli çalıştırılır.
        """
        if countries_geojson is None:
            countries_geojson = self.load_countries(download_if_missing=True)
        ok, fail = 0, []
        for f in countries_geojson.get("features", []):
            iso3 = self.country_iso3(f)
            if not iso3:
                continue
            try:
                self.load_adm1(iso3, download_if_missing=True)
                ok += 1
                if progress:
                    progress(f"{iso3} indirildi")
            except Exception as e:
                fail.append((iso3, str(e)))
                if progress:
                    progress(f"{iso3} hata: {e}")
        return ok, fail

    def normalize(self, text):
        if text is None:
            return ""
        text = str(text).strip().lower()
        text = text.translate(str.maketrans("çğıöşüâîû", "cgiosuaiu"))
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        keep = []
        for ch in text:
            keep.append(ch if ch.isalnum() else " ")
        return " ".join("".join(keep).split())

    def ensure_cities5000(self):
        """GeoNames şehir verisini indirir ve txt olarak cache'ler."""
        if self.cities_file.exists():
            return True
        with urllib.request.urlopen(self.GEONAMES_CITIES5000_URL, timeout=90) as resp:
            data = resp.read()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            name = "cities5000.txt"
            if name not in z.namelist():
                name = z.namelist()[0]
            self.cities_file.write_bytes(z.read(name))
        return True

    def build_city_index(self, max_rows=None):
        """cities5000.txt dosyasından hızlı şehir koordinat index'i oluşturur."""
        if self.city_index_file.exists():
            try:
                self._city_index = json.loads(self.city_index_file.read_text(encoding="utf-8"))
                return self._city_index
            except Exception:
                pass

        self.ensure_cities5000()
        idx = {}
        with self.cities_file.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.reader(f, delimiter="\t")
            for i, row in enumerate(reader):
                if max_rows and i >= max_rows:
                    break
                if len(row) < 19:
                    continue
                name = row[1]
                asciiname = row[2]
                alternates = row[3]
                lat = row[4]
                lon = row[5]
                country = row[8]
                population = row[14] if len(row) > 14 else "0"
                try:
                    rec = {
                        "name": name,
                        "ascii": asciiname,
                        "lat": float(lat),
                        "lon": float(lon),
                        "country": country,
                        "population": int(population or 0),
                    }
                except Exception:
                    continue

                keys = {self.normalize(name), self.normalize(asciiname)}
                for alt in (alternates or "").split(",")[:40]:
                    if alt:
                        keys.add(self.normalize(alt))
                for k in keys:
                    if not k:
                        continue
                    old = idx.get(k)
                    if old is None or rec["population"] > old.get("population", 0):
                        idx[k] = rec

        self.city_index_file.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
        self._city_index = idx
        return idx

    def find_city(self, name):
        """Şehir adı için gerçek koordinat arar. Cache yoksa indirmeyi dener."""
        q = self.normalize(name)
        if not q:
            return None
        try:
            idx = self._city_index or self.build_city_index()
            if q in idx:
                return idx[q]
            # Çok kontrollü başlangıç araması
            candidates = []
            for k, rec in idx.items():
                if k.startswith(q) or q.startswith(k):
                    candidates.append(rec)
                    if len(candidates) >= 40:
                        break
            if candidates:
                candidates.sort(key=lambda r: r.get("population", 0), reverse=True)
                return candidates[0]
        except Exception:
            return None
        return None
