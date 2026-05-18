
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import calendar
import math
import webbrowser
import json
import re
import urllib.request
import hashlib
import threading
import time
import unicodedata
from pathlib import Path

from veritabani import VeriTabani
from gercek_veri import RealWorldDataManager
from yerlesik_bolgeler import regions_for


APP_BG = "#0B0F14"      # gece asfaltı
SIDEBAR = "#111820"     # kabin içi koyu ton
PANEL = "#10161D"
CARD = "#151B22"        # metal panel
CARD2 = "#1F2A34"       # ikinci kart tonu
BORDER = "#2D3A45"      # metal çizgi
TEXT = "#F2F4F6"
MUTED = "#9BA8B5"
BLUE = "#2563EB"        # navigasyon mavisi
GREEN = "#22C55E"       # tamamlandı yeşili
YELLOW = "#FACC15"      # far sarısı
RED = "#EF4444"         # fren kırmızısı
ORANGE = "#F59E0B"      # ETS yol ışığı
PURPLE = "#D97706"      # sıcak turuncu vurgu
CYAN = "#38BDF8"


def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def norm_match_text(value):
    return str(value or "").translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower().strip()

def popular_region_from_name(place_name):
    return str(place_name or "").split(" - ", 1)[0].strip()

def match_popular_place_id(place_name):
    target = norm_match_text(place_name)
    if not target:
        return None
    try:
        for p in PopularPlacesPage.PLACES:
            ad = p.get("ad", "")
            if norm_match_text(ad) == target or norm_match_text(ad) in target or target in norm_match_text(ad):
                return p.get("id")
    except Exception:
        return None
    return None

def popular_place_by_id(place_id):
    try:
        for i, p in enumerate(PopularPlacesPage.PLACES):
            if p.get("id") == place_id:
                return i, p
    except Exception:
        pass
    return None, None



def norm_email_global(email):
    return str(email or "").strip().lower()

def norm_name_global(value):
    return str(value or "").strip().casefold()

def password_hash_global(password):
    return hashlib.sha256(str(password or "").encode("utf-8")).hexdigest()

def accounts_file_path():
    return Path(__file__).parent / "kullanici_hesaplari.json"

def load_accounts_global():
    path = accounts_file_path()
    default = [{
        "ad": "Hira",
        "soyad": "Yağmur",
        "email": "hira@gmail.com",
        "password_hash": password_hash_global("123")
    }]
    if not path.exists():
        try:
            path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []
    if not any(norm_email_global(a.get("email")) == "hira@gmail.com" for a in data):
        data.insert(0, default[0])
        try:
            save_accounts_global(data)
        except Exception:
            pass
    return data

def save_accounts_global(accounts):
    accounts_file_path().write_text(json.dumps(accounts, ensure_ascii=False, indent=2), encoding="utf-8")

def get_account_global(email):
    email = norm_email_global(email)
    for acc in load_accounts_global():
        if norm_email_global(acc.get("email")) == email:
            return acc
    return None

def verify_account_global(email, password):
    acc = get_account_global(email)
    return bool(acc and acc.get("password_hash") == password_hash_global(password))

def update_account_password_global(email, new_password):
    email = norm_email_global(email)
    accounts = load_accounts_global()
    for acc in accounts:
        if norm_email_global(acc.get("email")) == email:
            acc["password_hash"] = password_hash_global(new_password)
            save_accounts_global(accounts)
            return True
    return False

def user_data_file_path(email):
    email = norm_email_global(email)
    if email == "hira@gmail.com":
        return Path(__file__).parent / "platform_verisi.json", False
    digest = hashlib.sha256(email.encode("utf-8")).hexdigest()[:16]
    return Path(__file__).parent / "kullanici_verileri" / f"{digest}.json", True




def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except Exception:
        return datetime.now()


def days_left(date_str):
    d = parse_date(date_str)
    return (d.date() - datetime.now().date()).days

def readiness_score(db, route=None):
    """Seyahat hazırlık yüzdesini hesaplar."""
    score = 0
    total = 8

    if route and route.get("duraklar"):
        score += 1
    if db.veri.get("planlar"):
        score += 1
    if db.veri.get("rezervasyonlar"):
        score += 1
    if any(r.get("durum") == "Onaylandı" for r in db.veri.get("rezervasyonlar", [])):
        score += 1
    if db.veri.get("butce"):
        score += 1
    if any(v.get("durum", "").lower() in ["hazır", "tamamlandı"] for v in db.veri.get("valiz", [])):
        score += 1
    if db.veri.get("belgeler"):
        score += 1
    if db.veri.get("acil"):
        score += 1

    return int((score / total) * 100)


def readiness_color(value):
    if value >= 80:
        return GREEN
    if value >= 50:
        return YELLOW
    return RED


def nearest_route(veri):
    routes = []
    today = datetime.now().date()
    for r in veri.get("seyahatler", []):
        d = parse_date(r.get("tarih", "")).date()
        routes.append((abs((d - today).days), (d - today).days, r))
    if not routes:
        return None, 0
    routes.sort(key=lambda x: abs(x[1]))
    return routes[0][2], routes[0][1]


def route_summary(db, route):
    ready = readiness_score(db, route)
    reservation_count = len(db.veri.get("rezervasyonlar", []))
    approved = len([r for r in db.veri.get("rezervasyonlar", []) if r.get("durum") == "Onaylandı"])
    stops = len(route.get("duraklar", []))
    budget = int(float(route.get("butce", 0) or 0))
    return (
        f"{route.get('baslik','Bu seyahat')} için otomatik özet:\\n"
        f"- Başlangıç / Bitiş: {route.get('baslangic','-')} → {route.get('bitis','-')}\\n"
        f"- Tarih: {route.get('tarih','-')}\\n"
        f"- Rota tipi: {route.get('tip','-')}\\n"
        f"- Durum: {route.get('durum','Planlanıyor')}\\n"
        f"- Ara durak sayısı: {stops}\\n"
        f"- Tahmini bütçe: {budget} TL\\n"
        f"- Rezervasyon durumu: {approved}/{reservation_count} onaylandı\\n"
        f"- Hazırlık yüzdesi: %{ready}\\n"
    )


def risk_list(db):
    risks = []
    if not db.veri.get("belgeler"):
        risks.append(("Belge kasasında hiç belge yok.", RED))
    if not db.veri.get("acil"):
        risks.append(("Acil durum bilgileri eksik.", RED))
    pending_res = [r for r in db.veri.get("rezervasyonlar", []) if r.get("durum") != "Onaylandı"]
    if pending_res:
        risks.append((f"{len(pending_res)} rezervasyon hâlâ onay bekliyor.", YELLOW))
    unready = [v for v in db.veri.get("valiz", []) if v.get("durum", "").lower() not in ["hazır", "tamamlandı"]]
    if unready:
        risks.append((f"Valiz listesinde {len(unready)} hazırlanmamış eşya var.", YELLOW))
    total_budget = sum(float(s.get("butce", 0) or 0) for s in db.veri.get("seyahatler", []))
    expense = sum(float(x.get("tutar", 0) or 0) for x in db.veri.get("butce", []))
    if total_budget and expense > total_budget * 0.9:
        risks.append(("Toplam harcama bütçenin %90 seviyesine yaklaştı.", ORANGE))
    near, left = nearest_route(db.veri)
    if near and 0 <= left <= 7:
        risks.append((f"{near.get('baslik')} rotasına {left} gün kaldı.", CYAN))
    if not risks:
        risks.append(("Kritik risk görünmüyor. Seyahat hazırlığı iyi durumda.", GREEN))
    return risks


def achievement_data(db):
    routes = len(db.veri.get("seyahatler", []))
    plans = len(db.veri.get("planlar", []))
    docs = len(db.veri.get("belgeler", []))
    valiz_ready = len([v for v in db.veri.get("valiz", []) if v.get("durum", "").lower() in ["hazır", "tamamlandı"]])
    forum_like = len(db.veri.get("gunlukler", []))
    res_ok = len([r for r in db.veri.get("rezervasyonlar", []) if r.get("durum") == "Onaylandı"])
    expenses = len(db.veri.get("butce", []))
    return [
        ("İlk Rota", routes, 1, "İlk seyahat rotanı oluşturdun."),
        ("Rota Ustası", routes, 5, "5 farklı rota oluştur."),
        ("Planlayıcı", plans, 5, "5 aktivite planla."),
        ("Program Mimarı", plans, 15, "15 aktivite planla."),
        ("Belge Düzeni", docs, 3, "3 seyahat belgesi ekle."),
        ("Belge Uzmanı", docs, 8, "8 belgeyi kasaya ekle."),
        ("Valiz Hazır", valiz_ready, 4, "4 eşyayı hazır işaretle."),
        ("Rezervasyoncu", res_ok, 3, "3 rezervasyonu onaylı tut."),
        ("Bütçe Takipçisi", expenses, 5, "5 harcama kalemi ekle."),
        ("Anı Koleksiyoncusu", forum_like, 3, "3 yolculuk günlüğü yaz."),
    ]


def make_route_report(db, route_id=None):
    route = db.veri.get("seyahatler", [None])[0] if db.veri.get("seyahatler") else None
    if route_id:
        route = next((r for r in db.veri.get("seyahatler", []) if r.get("seyahat_id") == route_id), route)
    if not route:
        return None
    report_dir = Path(__file__).with_name("raporlar")
    report_dir.mkdir(exist_ok=True)
    fname = report_dir / f"seyahat_raporu_{route.get('seyahat_id','rota')}.txt"

    lines = []
    lines.append("ROUTIFY - SEYAHAT RAPORU")
    lines.append("=" * 40)
    lines.append(route_summary(db, route))
    lines.append("\\nDURAKLAR")
    lines.append("-" * 20)
    for d in route.get("duraklar", []):
        lines.append(f"- {d.get('sehir','')} | {d.get('gun','?')} gün | {d.get('yerler','-')} | {d.get('harcama','0')} TL")
    lines.append("\\nGÜNLÜK PLAN")
    lines.append("-" * 20)
    for p in db.veri.get("planlar", []):
        lines.append(f"- {p.get('gun','')} {p.get('saat','')} - {p.get('aktivite','')} | {p.get('not','')}")
    lines.append("\\nREZERVASYONLAR")
    lines.append("-" * 20)
    for r in db.veri.get("rezervasyonlar", []):
        lines.append(f"- {r.get('tur','')} | {r.get('ad','')} | {r.get('tarih','')} | {r.get('durum','')}")
    lines.append("\\nBÜTÇE")
    lines.append("-" * 20)
    for b in db.veri.get("butce", []):
        lines.append(f"- {b.get('kategori','')} | {b.get('tutar','0')} TL | {b.get('not','')}")
    fname.write_text("\\n".join(lines), encoding="utf-8")
    return fname




COUNTRY_TR_OVERRIDES = {
    "Afghanistan": "Afganistan", "Albania": "Arnavutluk", "Algeria": "Cezayir", "Andorra": "Andorra",
    "Angola": "Angola", "Antarctica": "Antarktika", "Argentina": "Arjantin", "Armenia": "Ermenistan",
    "Australia": "Avustralya", "Austria": "Avusturya", "Azerbaijan": "Azerbaycan", "Bahamas": "Bahamalar",
    "Bahrain": "Bahreyn", "Bangladesh": "Bangladeş", "Belarus": "Belarus", "Belgium": "Belçika",
    "Belize": "Belize", "Benin": "Benin", "Bhutan": "Butan", "Bolivia": "Bolivya",
    "Bosnia and Herzegovina": "Bosna-Hersek", "Botswana": "Botsvana", "Brazil": "Brezilya",
    "Brunei": "Brunei", "Bulgaria": "Bulgaristan", "Burkina Faso": "Burkina Faso", "Burundi": "Burundi",
    "Cambodia": "Kamboçya", "Cameroon": "Kamerun", "Canada": "Kanada", "Central African Republic": "Orta Afrika Cumhuriyeti",
    "Chad": "Çad", "Chile": "Şili", "China": "Çin", "Colombia": "Kolombiya",
    "Congo": "Kongo", "Costa Rica": "Kosta Rika", "Croatia": "Hırvatistan", "Cuba": "Küba",
    "Cyprus": "Kıbrıs", "Czechia": "Çekya", "Czech Republic": "Çekya", "Democratic Republic of the Congo": "Kongo Demokratik Cumhuriyeti",
    "Denmark": "Danimarka", "Djibouti": "Cibuti", "Dominican Republic": "Dominik Cumhuriyeti",
    "Ecuador": "Ekvador", "Egypt": "Mısır", "El Salvador": "El Salvador", "Equatorial Guinea": "Ekvator Ginesi",
    "Eritrea": "Eritre", "Estonia": "Estonya", "Ethiopia": "Etiyopya", "Finland": "Finlandiya",
    "France": "Fransa", "Gabon": "Gabon", "Gambia": "Gambiya", "Georgia": "Gürcistan",
    "Germany": "Almanya", "Ghana": "Gana", "Greece": "Yunanistan", "Greenland": "Grönland",
    "Guatemala": "Guatemala", "Guinea": "Gine", "Guinea-Bissau": "Gine-Bissau", "Guyana": "Guyana",
    "Haiti": "Haiti", "Honduras": "Honduras", "Hungary": "Macaristan", "Iceland": "İzlanda",
    "India": "Hindistan", "Indonesia": "Endonezya", "Iran": "İran", "Iraq": "Irak",
    "Ireland": "İrlanda", "Israel": "İsrail", "Italy": "İtalya", "Ivory Coast": "Fildişi Sahili",
    "Japan": "Japonya", "Jordan": "Ürdün", "Kazakhstan": "Kazakistan", "Kenya": "Kenya",
    "Kuwait": "Kuveyt", "Kyrgyzstan": "Kırgızistan", "Laos": "Laos", "Latvia": "Letonya",
    "Lebanon": "Lübnan", "Lesotho": "Lesotho", "Liberia": "Liberya", "Libya": "Libya",
    "Lithuania": "Litvanya", "Luxembourg": "Lüksemburg", "Madagascar": "Madagaskar", "Malawi": "Malavi",
    "Malaysia": "Malezya", "Mali": "Mali", "Mauritania": "Moritanya", "Mexico": "Meksika",
    "Moldova": "Moldova", "Mongolia": "Moğolistan", "Montenegro": "Karadağ", "Morocco": "Fas",
    "Mozambique": "Mozambik", "Myanmar": "Myanmar", "Namibia": "Namibya", "Nepal": "Nepal",
    "Netherlands": "Hollanda", "New Zealand": "Yeni Zelanda", "Nicaragua": "Nikaragua", "Niger": "Nijer",
    "Nigeria": "Nijerya", "North Korea": "Kuzey Kore", "North Macedonia": "Kuzey Makedonya", "Norway": "Norveç",
    "Oman": "Umman", "Pakistan": "Pakistan", "Palestine": "Filistin", "Panama": "Panama",
    "Paraguay": "Paraguay", "Peru": "Peru", "Philippines": "Filipinler", "Poland": "Polonya",
    "Portugal": "Portekiz", "Qatar": "Katar", "Romania": "Romanya", "Russia": "Rusya",
    "Rwanda": "Ruanda", "Saudi Arabia": "Suudi Arabistan", "Senegal": "Senegal", "Serbia": "Sırbistan",
    "Sierra Leone": "Sierra Leone", "Singapore": "Singapur", "Slovakia": "Slovakya", "Slovenia": "Slovenya",
    "Somalia": "Somali", "South Africa": "Güney Afrika", "South Korea": "Güney Kore", "South Sudan": "Güney Sudan",
    "Spain": "İspanya", "Sri Lanka": "Sri Lanka", "Sudan": "Sudan", "Suriname": "Surinam",
    "Sweden": "İsveç", "Switzerland": "İsviçre", "Syria": "Suriye", "Taiwan": "Tayvan",
    "Tajikistan": "Tacikistan", "Tanzania": "Tanzanya", "Thailand": "Tayland", "Togo": "Togo",
    "Tunisia": "Tunus", "Turkey": "Türkiye", "Turkiye": "Türkiye", "Turkmenistan": "Türkmenistan",
    "Uganda": "Uganda", "Ukraine": "Ukrayna", "United Arab Emirates": "Birleşik Arap Emirlikleri",
    "United Kingdom": "Birleşik Krallık", "United States of America": "Amerika Birleşik Devletleri",
    "United States": "Amerika Birleşik Devletleri", "Uruguay": "Uruguay", "Uzbekistan": "Özbekistan",
    "Venezuela": "Venezuela", "Vietnam": "Vietnam", "Western Sahara": "Batı Sahra", "Yemen": "Yemen",
    "Zambia": "Zambiya", "Zimbabwe": "Zimbabve",
}

def country_tr(name):
    return COUNTRY_TR_OVERRIDES.get(str(name), str(name))

def normalize_tr_text(text):
    return str(text or "").translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower().strip()

TR_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan", 5: "Mayıs", 6: "Haziran",
    7: "Temmuz", 8: "Ağustos", 9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}
TR_DAYS = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


class Button(tk.Button):
    def __init__(self, master, text, command=None, bg=BLUE, fg="white", **kwargs):
        self.normal_bg = bg
        self.hover_bg = self.lighten(bg)
        super().__init__(
            master, text=text, command=command, bg=bg, fg=fg,
            activebackground=self.hover_bg, activeforeground=fg,
            bd=0, relief="flat", cursor="hand2",
            font=("Segoe UI", 10, "bold"), padx=12, pady=8, **kwargs
        )
        self.bind("<Enter>", lambda e: self.configure(bg=self.hover_bg))
        self.bind("<Leave>", lambda e: self.configure(bg=self.normal_bg))

    def lighten(self, color):
        c = color.lstrip("#")
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
        return f"#{min(255,r+24):02x}{min(255,g+24):02x}{min(255,b+24):02x}"


class Card(tk.Frame):
    def __init__(self, master, title=None, subtitle=None, bg=CARD, **kwargs):
        super().__init__(master, bg=bg, highlightbackground=BORDER, highlightthickness=1, bd=0, **kwargs)
        self.card_bg = bg
        if title:
            tk.Label(self, text=title, bg=bg, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        if subtitle:
            tk.Label(self, text=subtitle, bg=bg, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(0, 8))


class ScrollFrame(tk.Frame):
    def __init__(self, master, bg=CARD):
        super().__init__(master, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.bar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.win, width=e.width))

        # İmleç bu alanın içindeyken scrollbar üstünde olmasa bile tekerlek çalışır.
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)

    def _bind_mousewheel(self, event=None):
        self.bind_all("<MouseWheel>", self._mw)
        self.bind_all("<Button-4>", self._mw_linux)
        self.bind_all("<Button-5>", self._mw_linux)

    def _unbind_mousewheel(self, event=None):
        self.unbind_all("<MouseWheel>")
        self.unbind_all("<Button-4>")
        self.unbind_all("<Button-5>")

    def _mw_linux(self, event):
        self.canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

    def _mw(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class MapCanvas(tk.Canvas):
    def __init__(self, master, height=210, **kwargs):
        super().__init__(master, bg="#0B2338", height=height, highlightthickness=0, bd=0, **kwargs)
        self.bind("<Configure>", self.draw)

    def draw(self, event=None, pins=None):
        self.delete("all")
        w = self.winfo_width() or 600
        h = self.winfo_height() or 220
        self.create_rectangle(0, 0, w, h, fill="#0B2338", outline="")
        # abstract map background
        self.create_polygon(0, h*.36, w*.18, h*.16, w*.36, h*.28, w*.30, h*.62, w*.10, h*.75, 0, h*.66, fill="#273F35", outline="#4C7A64", smooth=True)
        self.create_polygon(w*.25, h*.08, w*.58, h*.05, w*.78, h*.22, w*.72, h*.54, w*.48, h*.62, w*.35, h*.42, fill="#3A4E39", outline="#6C8C60", smooth=True)
        self.create_polygon(w*.54, h*.56, w*.92, h*.46, w, h*.72, w*.86, h*.94, w*.62, h*.86, fill="#333C2D", outline="#66734F", smooth=True)
        pts = pins or [(w*.08,h*.64), (w*.25,h*.50), (w*.39,h*.55), (w*.54,h*.34), (w*.72,h*.40), (w*.86,h*.24)]
        for i in range(len(pts)-1):
            self.create_line(pts[i], pts[i+1], fill=BLUE, width=4, smooth=True)
        colors = [RED, GREEN, ORANGE, PURPLE, CYAN, YELLOW]
        for i, (x, y) in enumerate(pts):
            self.create_oval(x-10, y-10, x+10, y+10, fill=colors[i % len(colors)], outline="white", width=2)
            self.create_text(x, y-22, text=str(i+1), fill="white", font=("Segoe UI", 8, "bold"))
        # Önizleme yazısı kaldırıldı.


class RouteMapCanvas(tk.Canvas):
    """Rota detaylarında sahte grafik yerine gerçek ülke haritası üzerinde rota gösterir."""
    _countries_cache = None

    CITY_COORDS = {
        "istanbul": (28.9784, 41.0082),
        "kapadokya": (34.8333, 38.6431),
        "nevsehir": (34.7122, 38.6244),
        "ankara": (32.8597, 39.9334),
        "izmir": (27.1428, 38.4237),
        "bodrum": (27.4292, 37.0344),
        "antalya": (30.7133, 36.8969),
        "bursa": (29.0609, 40.1828),
        "konya": (32.4846, 37.8746),
        "trabzon": (39.7168, 41.0027),
        "roma": (12.4964, 41.9028),
        "rome": (12.4964, 41.9028),
        "paris": (2.3522, 48.8566),
        "floransa": (11.2558, 43.7696),
        "florence": (11.2558, 43.7696),
        "milano": (9.1900, 45.4642),
        "milan": (9.1900, 45.4642),
        "venedik": (12.3155, 45.4408),
        "venice": (12.3155, 45.4408),
        "zurih": (8.5417, 47.3769),
        "zurich": (8.5417, 47.3769),
        "berlin": (13.4050, 52.5200),
        "amsterdam": (4.9041, 52.3676),
        "brüksel": (4.3517, 50.8503),
        "brussels": (4.3517, 50.8503),
        "londra": (-0.1276, 51.5072),
        "london": (-0.1276, 51.5072),
        "new york": (-74.0060, 40.7128),
        "minnesota": (-94.6859, 46.7296),
        "minneapolis": (-93.2650, 44.9778),
    }

    def __init__(self, master, route, height=260, **kwargs):
        super().__init__(master, bg="#07111C", height=height, highlightthickness=0, bd=0, **kwargs)
        self.route = route or {}
        # Eski/stabil format: gerçek ADM1 veri indirme ana haritadan çıkarıldı.
        self.bind("<Configure>", self.draw)

    def norm(self, text):
        tr_map = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosuCGIOSUaiu")
        text = str(text or "").strip().lower().translate(tr_map)
        return " ".join(text.replace("-", " ").replace("_", " ").split())

    def load_countries(self):
        if RouteMapCanvas._countries_cache is not None:
            return RouteMapCanvas._countries_cache
        try:
            path = Path(__file__).parent / "harita_verileri" / "ulkeler_sinirlari.geojson"
            RouteMapCanvas._countries_cache = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            RouteMapCanvas._countries_cache = {"features": []}
        return RouteMapCanvas._countries_cache

    def route_city_names(self):
        names = []
        if self.route.get("baslangic"):
            names.append(str(self.route.get("baslangic")))
        for d in self.route.get("duraklar", []) or []:
            s = d.get("sehir") or d.get("ad") or d.get("durak")
            if s:
                names.append(str(s))
        if self.route.get("bitis"):
            names.append(str(self.route.get("bitis")))

        # Hiç durak yoksa başlıkten tahmin etmeye çalışma, mevcut başlangıç/bitiş yeterli.
        clean = []
        for n in names:
            if n and n not in clean:
                clean.append(n)
        return clean

    def coord_for_city(self, name, index=0):
        key = self.norm(name)

        # Önce gerçek GeoNames şehir koordinatı denenir.
        try:
            rec = self.real_data.find_city(name)
            if rec:
                return (float(rec["lon"]), float(rec["lat"]))
        except Exception:
            pass

        # Cache/ internet yoksa bilinen örnek şehir koordinatları fallback.
        if key in self.CITY_COORDS:
            return self.CITY_COORDS[key]

        for k, v in self.CITY_COORDS.items():
            if k in key or key in k:
                return v

        # Son çare: rota bozulmasın diye kararlı fallback koordinatı.
        seed = sum(ord(c) for c in key) + index * 37
        lon = 20 + (seed % 45)
        lat = 34 + ((seed // 7) % 18)
        return (lon, lat)


    def geom_rings(self, geom):
        rings = []
        if not geom:
            return rings
        t = geom.get("type")
        coords = geom.get("coordinates", [])
        if t == "Polygon":
            if coords:
                rings.append(coords[0])
        elif t == "MultiPolygon":
            for poly in coords:
                if poly:
                    rings.append(poly[0])
        return rings

    def bbox_ring(self, ring):
        xs, ys = [], []
        for p in ring:
            try:
                xs.append(float(p[0]))
                ys.append(float(p[1]))
            except Exception:
                pass
        if not xs:
            return None
        return min(xs), min(ys), max(xs), max(ys)

    def intersects(self, a, b):
        return not (a[2] < b[0] or a[0] > b[2] or a[3] < b[1] or a[1] > b[3])

    def make_view(self, points, w, h):
        lons = [p[0] for p in points]
        lats = [p[1] for p in points]
        minlon, maxlon = min(lons), max(lons)
        minlat, maxlat = min(lats), max(lats)
        dx = max(2.0, maxlon - minlon)
        dy = max(2.0, maxlat - minlat)

        # Rota çevresinde ülke/şehirler görünsün.
        padlon = max(2.5, dx * 0.35)
        padlat = max(2.0, dy * 0.45)
        minlon -= padlon
        maxlon += padlon
        minlat -= padlat
        maxlat += padlat

        dx = maxlon - minlon
        dy = maxlat - minlat
        margin = 28
        scale = min((w - margin * 2) / dx, (h - margin * 2) / dy)
        return minlon, minlat, maxlon, maxlat, scale, margin

    def project(self, lon, lat, view, w, h):
        minlon, minlat, maxlon, maxlat, scale, margin = view
        x = margin + (lon - minlon) * scale
        y = margin + (maxlat - lat) * scale
        return x, y

    def draw(self, event=None):
        self.delete("all")
        w = self.winfo_width() or 850
        h = self.winfo_height() or 260
        self.create_rectangle(0, 0, w, h, fill="#07111C", outline="")

        city_names = self.route_city_names()
        coords = [self.coord_for_city(n, i) for i, n in enumerate(city_names)]

        if len(coords) < 2:
            self.create_text(w/2, h/2, text="Rota için başlangıç ve varış bilgisi yok.", fill=TEXT, font=("Segoe UI", 14, "bold"))
            return

        view = self.make_view(coords, w, h)
        bbox = view[:4]

        # Okyanus grid
        for lon in range(-180, 181, 10):
            x1, y1 = self.project(lon, bbox[1], view, w, h)
            x2, y2 = self.project(lon, bbox[3], view, w, h)
            self.create_line(x1, y1, x2, y2, fill="#12324A", width=1)
        for lat in range(-80, 81, 5):
            x1, y1 = self.project(bbox[0], lat, view, w, h)
            x2, y2 = self.project(bbox[2], lat, view, w, h)
            self.create_line(x1, y1, x2, y2, fill="#12324A", width=1)

        # Gerçek ülke sınırları
        data = self.load_countries()
        for f in data.get("features", []):
            for ring in self.geom_rings(f.get("geometry")):
                rb = self.bbox_ring(ring)
                if not rb or not self.intersects(rb, bbox):
                    continue
                pts = []
                step = 1 if len(ring) < 120 else 2
                for p in ring[::step]:
                    try:
                        x, y = self.project(float(p[0]), float(p[1]), view, w, h)
                        pts.extend([x, y])
                    except Exception:
                        pass
                if len(pts) >= 6:
                    self.create_polygon(pts, fill="#273A48", outline="#51606D", width=1)

        # Rota çizgisi
        route_pts = []
        for lon, lat in coords:
            x, y = self.project(lon, lat, view, w, h)
            route_pts.extend([x, y])
        self.create_line(route_pts, fill="#1D4ED8", width=7, smooth=True)
        self.create_line(route_pts, fill=ORANGE, width=3, smooth=True)

        colors = [RED, GREEN, ORANGE, PURPLE, CYAN, YELLOW, BLUE]
        for i, ((lon, lat), name) in enumerate(zip(coords, city_names)):
            x, y = self.project(lon, lat, view, w, h)
            self.create_oval(x-11, y-11, x+11, y+11, fill=colors[i % len(colors)], outline="white", width=2)
            self.create_text(x, y-22, text=str(i+1), fill="white", font=("Segoe UI", 8, "bold"))
            self.create_text(x, y+20, text=name, fill=TEXT, font=("Segoe UI", 8, "bold"))



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Riftify - Seyahat Planlama Uygulaması")
        self.geometry("1320x780")
        self.minsize(1140, 690)
        self.configure(bg=APP_BG)
        try:
            self.app_logo = tk.PhotoImage(file=str(Path(__file__).parent / "riftify_logo.png"))
            self.iconphoto(True, self.app_logo)
        except Exception:
            self.app_logo = None
        self.db = None
        self.current_user_email = None
        self.show_login()

    def clear(self):
        for w in self.winfo_children():
            w.destroy()

    def show_login(self):
        self.current_user_email = None
        self.db = None
        self.clear()
        LoginPage(self, self.show_main).pack(fill="both", expand=True)

    def show_main(self, email=None):
        self.current_user_email = norm_email_global(email or "hira@gmail.com")
        data_path, empty = user_data_file_path(self.current_user_email)
        self.db = VeriTabani(path=data_path, empty=empty)
        self.clear()
        Shell(
            self,
            self.db,
            current_user=self.current_user_email,
            on_logout=self.logout,
            on_change_password=self.change_password_window
        ).pack(fill="both", expand=True)

    def logout(self):
        self.show_login()

    def change_password_window(self):
        email = self.current_user_email
        if not email:
            return

        win = tk.Toplevel(self)
        win.title("Şifre Değiştir")
        win.geometry("460x390")
        win.configure(bg=APP_BG)
        win.transient(self)
        win.grab_set()
        win.lift()
        win.focus_force()

        old_pwd = tk.StringVar()
        new_pwd = tk.StringVar()
        new_pwd2 = tk.StringVar()

        tk.Label(win, text="Şifre Değiştir", bg=APP_BG, fg=TEXT, font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=24, pady=(24, 6))
        tk.Label(win, text=email, bg=APP_BG, fg=MUTED, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=24, pady=(0, 16))

        card = Card(win)
        card.pack(fill="x", padx=24, pady=8)

        def add_entry(label, var):
            tk.Label(card, text=label, bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
            e = tk.Entry(card, textvariable=var, show="•", bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
            e.pack(fill="x", padx=16, ipady=8)
            return e

        add_entry("Mevcut şifre", old_pwd)
        add_entry("Yeni şifre", new_pwd)
        add_entry("Yeni şifre tekrar", new_pwd2)

        def save():
            if not verify_account_global(email, old_pwd.get()):
                messagebox.showerror("Hata", "Mevcut şifre hatalı.", parent=win)
                win.lift()
                return
            if len(new_pwd.get()) < 3:
                messagebox.showerror("Hata", "Yeni şifre çok kısa.", parent=win)
                win.lift()
                return
            if new_pwd.get() != new_pwd2.get():
                messagebox.showerror("Hata", "Yeni şifreler eşleşmiyor.", parent=win)
                win.lift()
                return
            if update_account_password_global(email, new_pwd.get()):
                messagebox.showinfo("Başarılı", "Şifre değiştirildi.", parent=win)
                win.grab_release()
                win.destroy()
            else:
                messagebox.showerror("Hata", "Hesap bulunamadı.", parent=win)
                win.lift()

        Button(card, "Şifreyi Kaydet", command=save, bg=GREEN).pack(fill="x", padx=16, pady=(16, 8))
        Button(card, "Kapat", command=win.destroy, bg="#26384A").pack(fill="x", padx=16, pady=(0, 16))




class LoginPage(tk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, bg=APP_BG)
        self.on_login = on_login
        self.email = tk.StringVar(value="hira@gmail.com")
        self.sifre = tk.StringVar(value="123")
        self.show_password = tk.BooleanVar(value=False)
        self.build()

    def build(self):
        outer = tk.Frame(self, bg=APP_BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = Card(outer)
        card.pack(padx=20, pady=20)
        card.configure(width=560, height=590)
        card.pack_propagate(False)

        head = tk.Frame(card, bg=CARD)
        head.pack(fill="x", padx=30, pady=(20, 4))
        try:
            self.login_logo = tk.PhotoImage(file=str(Path(__file__).parent / "riftify_logo.png"))
            tk.Label(head, image=self.login_logo, bg=CARD).pack(side="left", padx=(0, 12))
        except Exception:
            pass
        text_head = tk.Frame(head, bg=CARD)
        text_head.pack(side="left", fill="x", expand=True)
        tk.Label(text_head, text="Riftify - Seyahat Planlama", bg=CARD, fg=TEXT, font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(text_head, text="Rota, bütçe, rezervasyon ve keşif odaklı modern seyahat paneli", bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        login = tk.Frame(card, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
        login.pack(fill="both", expand=True, padx=34, pady=(0, 20))

        iconrow = tk.Frame(login, bg=CARD2)
        iconrow.pack(pady=(22, 8))
        for emoji, title in [("🧭", "Gezgin"), ("🗺", "Rota")]:
            f = tk.Frame(iconrow, bg=CARD2)
            f.pack(side="left", padx=30)
            c = tk.Canvas(f, width=76, height=76, bg=CARD2, highlightthickness=0)
            c.pack()
            c.create_oval(8, 8, 68, 68, fill="#26384C", outline="#4E7FAB", width=2)
            c.create_text(38, 36, text=emoji, font=("Segoe UI Emoji", 26))
            tk.Label(f, text=title, bg=CARD2, fg=MUTED, font=("Segoe UI", 8)).pack(pady=(2, 0))

        tk.Label(login, text="Gezgin Girişi", bg=CARD2, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(pady=(4, 12))

        frm = tk.Frame(login, bg=CARD2)
        frm.pack(fill="x", padx=28, pady=(0, 12))

        self.entry(frm, "E-posta", self.email).pack(fill="x", pady=6, ipady=9)
        self.password_row(frm, self.sifre).pack(fill="x", pady=6)
        Button(frm, "Oturum Aç", command=self.login, bg="#3E65B8").pack(fill="x", pady=(12, 0))
        Button(frm, "Yeni Hesap Aç", command=self.register_window, bg="#26384A").pack(fill="x", pady=(8, 0))

        tk.Label(outer, text="Yapımcı: E.Hira YAĞMUR", bg=APP_BG, fg="#70849D", font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24, pady=(0, 0))

    def entry(self, master, placeholder, var, show=None):
        e = tk.Entry(master, textvariable=var, show=show, bg="#101826", fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
        e.configure(highlightbackground="#2F425B", highlightthickness=1)
        return e

    def password_row(self, master, var):
        row = tk.Frame(master, bg=CARD2)
        entry = self.entry(row, "Şifre", var, show="•")
        entry.pack(side="left", fill="x", expand=True, ipady=9)
        def toggle():
            self.show_password.set(not self.show_password.get())
            entry.configure(show="" if self.show_password.get() else "•")
            eye.configure(text="🙈" if self.show_password.get() else "👁")
        eye = tk.Button(row, text="👁", command=toggle, bg="#26384A", fg=TEXT, activebackground="#33485F", activeforeground=TEXT, relief="flat", width=4, cursor="hand2")
        eye.pack(side="left", padx=(6, 0), ipady=5)
        return row

    def accounts_path(self):
        return accounts_file_path()

    def norm_email(self, email):
        return norm_email_global(email)

    def norm_name(self, value):
        return norm_name_global(value)

    def password_hash(self, password):
        return password_hash_global(password)

    def load_accounts(self):
        return load_accounts_global()

    def save_accounts(self, accounts):
        save_accounts_global(accounts)

    def verify_account(self, email, password):
        return verify_account_global(email, password)

    def account_duplicate_reason(self, ad, soyad, email):
        email = self.norm_email(email)
        ad_n = self.norm_name(ad)
        soy_n = self.norm_name(soyad)
        for acc in self.load_accounts():
            if self.norm_email(acc.get("email")) == email:
                return "Bu e-posta adresiyle zaten hesap açılmış."
            if self.norm_name(acc.get("ad")) == ad_n and self.norm_name(acc.get("soyad")) == soy_n:
                return "Bu isim ve soy isimle zaten hesap açılmış."
        return None

    def login(self):
        email = self.email.get().strip()
        sifre = self.sifre.get().strip()
        if verify_account_global(email, sifre):
            self.on_login(norm_email_global(email))
        else:
            messagebox.showerror("Giriş Hatası", "E-posta veya şifre hatalı.")



    def password_score(self, pwd):
        score = 0
        if len(pwd) >= 6: score += 1
        if len(pwd) >= 10: score += 1
        if re.search(r"[A-ZÇĞİÖŞÜ]", pwd): score += 1
        if re.search(r"[a-zçğıöşü]", pwd): score += 1
        if re.search(r"\d", pwd): score += 1
        if re.search(r"[^A-Za-z0-9çğıöşüÇĞİÖŞÜ]", pwd): score += 1
        return score

    def register_window(self):
        win = tk.Toplevel(self)
        win.title("Yeni Hesap Aç")
        win.geometry("560x660")
        win.configure(bg=APP_BG)
        win.transient(self.winfo_toplevel())
        win.grab_set()
        win.lift()
        win.focus_force()
        win.protocol("WM_DELETE_WINDOW", win.destroy)

        ad = tk.StringVar()
        soyad = tk.StringVar()
        email = tk.StringVar()
        pwd = tk.StringVar()
        pwd_show = tk.BooleanVar(value=False)

        tk.Label(win, text="Yeni Hesap Aç", bg=APP_BG, fg=TEXT, font=("Segoe UI", 21, "bold")).pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(win, text="Ad, soyad ve @gmail.com ile biten e-posta gerekli.", bg=APP_BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=24, pady=(0, 16))

        form = Card(win)
        form.pack(fill="x", padx=24, pady=8)

        row_name = tk.Frame(form, bg=CARD)
        row_name.pack(fill="x", padx=16, pady=(14, 4))
        left = tk.Frame(row_name, bg=CARD)
        left.pack(side="left", fill="x", expand=True, padx=(0, 6))
        right = tk.Frame(row_name, bg=CARD)
        right.pack(side="left", fill="x", expand=True, padx=(6, 0))

        tk.Label(left, text="İsim", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Entry(left, textvariable=ad, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10)).pack(fill="x", ipady=8, pady=(2, 0))

        tk.Label(right, text="Soy isim", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Entry(right, textvariable=soyad, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10)).pack(fill="x", ipady=8, pady=(2, 0))

        tk.Label(form, text="Gmail adresi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
        e = tk.Entry(form, textvariable=email, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
        e.pack(fill="x", padx=16, ipady=8)

        tk.Label(form, text="Şifre", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
        row = tk.Frame(form, bg=CARD)
        row.pack(fill="x", padx=16)
        pentry = tk.Entry(row, textvariable=pwd, show="•", bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10))
        pentry.pack(side="left", fill="x", expand=True, ipady=8)
        def toggle_pwd():
            pwd_show.set(not pwd_show.get())
            pentry.configure(show="" if pwd_show.get() else "•")
            eye.configure(text="🙈" if pwd_show.get() else "👁")
        eye = tk.Button(row, text="👁", command=toggle_pwd, bg="#26384A", fg=TEXT, relief="flat", width=4, cursor="hand2")
        eye.pack(side="left", padx=(6, 0), ipady=4)

        tk.Label(form, text="Şifre güvenliği", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(14, 2))
        bar = tk.Canvas(form, height=18, bg=CARD2, highlightthickness=0)
        bar.pack(fill="x", padx=16)
        status = tk.Label(form, text="Şifre bekleniyor", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold"))
        status.pack(anchor="w", padx=16, pady=(4, 12))

        def update_strength(*_):
            bar.delete("all")
            w = max(1, bar.winfo_width())
            s = self.password_score(pwd.get())
            if s <= 2:
                color, text, ratio = RED, "Zayıf şifre", 0.33
            elif s <= 4:
                color, text, ratio = ORANGE, "Orta şifre", 0.66
            else:
                color, text, ratio = GREEN, "Güçlü şifre", 1.0
            bar.create_rectangle(0, 0, int(w * ratio), 18, fill=color, outline="")
            status.configure(text=text, fg=color)

        pwd.trace_add("write", update_strength)
        win.after(100, update_strength)

        def save():
            isim = ad.get().strip()
            soy = soyad.get().strip()
            mail = self.norm_email(email.get())
            sifre = pwd.get()

            if not isim or not soy:
                messagebox.showerror("Eksik Bilgi", "İsim ve soy isim boş olamaz.", parent=win)
                win.lift()
                return

            if not re.fullmatch(r"[A-Za-z0-9._%+\-]+@gmail\.com", mail):
                messagebox.showerror("Hatalı Gmail", "Hesap açmak için e-posta mutlaka @gmail.com ile bitmeli.", parent=win)
                win.lift()
                return

            if len(sifre) < 3:
                messagebox.showerror("Şifre", "Şifre çok kısa.", parent=win)
                win.lift()
                return

            duplicate = self.account_duplicate_reason(isim, soy, mail)
            if duplicate:
                messagebox.showerror("Hesap Oluşturulamadı", duplicate, parent=win)
                win.lift()
                return

            accounts = self.load_accounts()
            accounts.append({
                "ad": isim,
                "soyad": soy,
                "email": mail,
                "password_hash": self.password_hash(sifre)
            })
            try:
                self.save_accounts(accounts)
            except Exception as e:
                messagebox.showerror("Kayıt Hatası", f"Hesap kaydedilemedi: {e}", parent=win)
                win.lift()
                return

            messagebox.showinfo("Hesap Açıldı", "Hesap başarıyla oluşturuldu. Şimdi giriş yapabilirsin.", parent=win)
            self.email.set(mail)
            self.sifre.set("")
            win.grab_release()
            win.destroy()


        Button(form, "Hesap Oluştur", command=save, bg=GREEN).pack(fill="x", padx=16, pady=(6, 8))
        Button(form, "Kapat", command=win.destroy, bg="#26384A").pack(fill="x", padx=16, pady=(0, 18))


class Shell(tk.Frame):
    def __init__(self, master, db, current_user=None, on_logout=None, on_change_password=None):
        super().__init__(master, bg=APP_BG)
        self.db = db
        self.current_user = current_user or "hira@gmail.com"
        self.on_logout = on_logout
        self.on_change_password = on_change_password
        self.pages = {
            "home": HomePage,
            "dashboard": DashboardPage,
            "routes": RoutesPage,
            "days": DayPlanPage,
            "budget": BudgetPage,
            "reservations": ReservationPage,
            "journal": JournalPage,
            "packing": PackingPage,
            "documents": DocumentsPage,
            "emergency": EmergencyPage,
            "companions": CompanionsPage,
            "checklist": ChecklistPage,
            "reminders": RemindersPage,
            "smart": SmartTravelPage,
            "compare": ComparePage,
            "search": GlobalSearchPage,
            "worldmap": WorldMapPage,
            "route_create": RouteCreatePage,
            "popular": PopularPlacesPage,
            "tools": ToolsHubPage,
        }
        self.build()

    def build(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=218)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(self, bg=APP_BG)
        self.content.pack(side="left", fill="both", expand=True)

        self.topbar = tk.Frame(self.content, bg=APP_BG, height=42)
        self.topbar.pack(fill="x", side="top")
        self.topbar.pack_propagate(False)

        self.account_btn = tk.Button(
            self.topbar,
            text=f"👤 {self.current_user}",
            command=self.show_account_menu,
            bg="#172335",
            fg=TEXT,
            activebackground="#26384A",
            activeforeground=TEXT,
            bd=0,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6
        )
        self.account_btn.pack(side="right", padx=18, pady=7)

        self.page_area = tk.Frame(self.content, bg=APP_BG)
        self.page_area.pack(side="top", fill="both", expand=True)

        brand = tk.Frame(self.sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=16, pady=(18, 8))
        try:
            self.sidebar_logo = tk.PhotoImage(file=str(Path(__file__).parent / "riftify_logo.png"))
            tk.Label(brand, image=self.sidebar_logo, bg=SIDEBAR).pack(side="left", padx=(0, 8))
        except Exception:
            tk.Label(brand, text="◆", bg=SIDEBAR, fg=ORANGE, font=("Segoe UI", 20, "bold")).pack(side="left", padx=(0, 8))
        brand_text = tk.Frame(brand, bg=SIDEBAR)
        brand_text.pack(side="left", fill="x", expand=True)
        tk.Label(brand_text, text="Riftify", bg=SIDEBAR, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="Riftify Planner", bg=SIDEBAR, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")

        nav = [
            ("home", "⌂", "Ana Menü"),
            ("worldmap", "🌍", "Harita"),
            ("route_create", "➕", "Rota Oluştur"),
            ("popular", "★", "Popüler"),
            ("routes", "🛣", "Rotalar"),
            ("days", "📅", "Plan"),
            ("tools", "🧰", "Araçlar"),
        ]
        tk.Label(self.sidebar, text="Yol Menüsü", bg=SIDEBAR, fg=ORANGE, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(4, 8))
        for key, icon, label in nav:
            b = tk.Button(
                self.sidebar,
                text=f"{icon}  {label}",
                anchor="w",
                bg=SIDEBAR,
                fg=TEXT if key == "home" else MUTED,
                activebackground="#26384A",
                activeforeground=TEXT,
                bd=0,
                relief="flat",
                cursor="hand2",
                font=("Segoe UI", 11, "bold"),
                command=lambda k=key: self.show(k),
            )
            b.pack(fill="x", padx=14, pady=5, ipady=12)

        tk.Label(self.sidebar, text="E.Hira YAĞMUR", bg=SIDEBAR, fg="#70849D", font=("Segoe UI", 8, "bold")).pack(side="bottom", pady=(0, 14))

        self.show("home")

    def show_account_menu(self):
        menu = tk.Menu(self, tearoff=0, bg=CARD, fg=TEXT, activebackground="#26384A", activeforeground=TEXT)
        menu.add_command(label="Şifre Değiştir", command=self.on_change_password)
        menu.add_separator()
        menu.add_command(label="Çıkış Yap", command=self.on_logout)
        try:
            menu.tk_popup(self.account_btn.winfo_rootx(), self.account_btn.winfo_rooty() + self.account_btn.winfo_height())
        finally:
            menu.grab_release()

    def show(self, key, **kwargs):
        for w in self.page_area.winfo_children():
            w.destroy()
        page = self.pages.get(key, DashboardPage)
        page(self.page_area, self.db, self, **kwargs).pack(fill="both", expand=True)



class HomePage(tk.Frame):
    """ETS tarzı sade seyahat kontrol paneli."""
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, bg=APP_BG)
        self.db = db
        self.shell = shell
        self.build()

    def safe_len(self, key):
        try:
            return len(self.db.veri.get(key, []))
        except Exception:
            return 0

    def total_budget_text(self):
        total = 0
        try:
            for item in self.db.veri.get("butce", []):
                total += float(item.get("tutar", 0) or 0)
            for route in self.db.veri.get("seyahatler", []):
                total += float(route.get("butce", 0) or 0)
        except Exception:
            pass
        if total <= 0:
            return "0"
        return f"{int(total):,}".replace(",", ".")

    def last_route_text(self):
        try:
            routes = self.db.veri.get("seyahatler", [])
            if routes:
                r = routes[-1]
                return f"{r.get('baslangic','-')} → {r.get('bitis','-')}"
        except Exception:
            pass
        return "Henüz rota yok"

    def stat_card(self, parent, title, value, subtitle, color=ORANGE):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(card, text=title, bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(card, text=str(value), bg=CARD, fg=color, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=14)
        tk.Label(card, text=subtitle, bg=CARD, fg=TEXT, font=("Segoe UI", 8), wraplength=190, justify="left").pack(anchor="w", padx=14, pady=(0, 12))
        return card

    def quick_card(self, parent, title, desc, button_text, target, accent=ORANGE):
        card = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        top = tk.Frame(card, bg=CARD)
        top.pack(fill="x", padx=16, pady=(16, 6))
        tk.Label(top, text=title, bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(card, text=desc, bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=245, justify="left").pack(anchor="w", padx=16, pady=(0, 14))
        Button(card, button_text, command=lambda: self.shell.show(target), bg=accent).pack(anchor="w", padx=16, pady=(0, 16))
        return card

    def road_canvas(self, parent):
        c = tk.Canvas(parent, height=120, bg=CARD2, highlightthickness=0)
        c.pack(fill="x", padx=18, pady=(8, 16))
        # ETS / navigation road line
        c.create_line(35, 78, 160, 38, 290, 65, 430, 28, 560, 58, 720, 32, fill="#233443", width=18, smooth=True)
        c.create_line(35, 78, 160, 38, 290, 65, 430, 28, 560, 58, 720, 32, fill=ORANGE, width=4, smooth=True)
        for x, y, label in [(35,78,"Başla"), (290,65,"Mola"), (560,58,"Keşif"), (720,32,"Varış")]:
            c.create_oval(x-11, y-11, x+11, y+11, fill="#0B0F14", outline=YELLOW, width=3)
            c.create_text(x, y+26, text=label, fill=TEXT, font=("Segoe UI", 8, "bold"))
        return c

    def build(self):
        wrap = tk.Frame(self, bg=APP_BG)
        wrap.pack(fill="both", expand=True, padx=30, pady=24)

        # Header
        hero = tk.Frame(wrap, bg=APP_BG)
        hero.pack(fill="x")

        left = tk.Frame(hero, bg=APP_BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text="Riftify Riftify Planner", bg=APP_BG, fg=TEXT, font=("Segoe UI", 28, "bold")).pack(anchor="w")
        tk.Label(left, text="Yolunu planla, rotanı yönet, dünyayı keşfet.", bg=APP_BG, fg=MUTED, font=("Segoe UI", 11)).pack(anchor="w", pady=(4, 0))


        # Stats
        stats = tk.Frame(wrap, bg=APP_BG)
        stats.pack(fill="x", pady=(24, 14))
        values = [
            ("Rotalar", self.safe_len("seyahatler"), "Planlanan ve kayıtlı rotalar", ORANGE),
            ("Rezervasyon", self.safe_len("rezervasyonlar"), "Otel, uçuş ve etkinlik kayıtları", BLUE),
            ("Bütçe", self.total_budget_text(), "Toplam tahmini harcama", YELLOW),
            ("Notlar", self.safe_len("gunluk"), "Yolculuk günlüğü ve anılar", GREEN),
        ]
        for i, (title, value, subtitle, color) in enumerate(values):
            stats.columnconfigure(i, weight=1)
            self.stat_card(stats, title, value, subtitle, color).grid(row=0, column=i, sticky="nsew", padx=6)

        # Main content grid
        body = tk.Frame(wrap, bg=APP_BG)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        map_card = tk.Frame(body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        map_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=6)
        tk.Label(map_card, text="Dünya Keşif Haritası", bg=CARD, fg=TEXT, font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=18, pady=(18, 2))
        tk.Label(map_card, text="Ülke seç, il/eyalet sınırlarını incele, bölge bilgilerini ve turistik yerleri aç.", bg=CARD, fg=MUTED, font=("Segoe UI", 10), wraplength=680, justify="left").pack(anchor="w", padx=18)
        self.road_canvas(map_card)

        map_actions = tk.Frame(map_card, bg=CARD)
        map_actions.pack(fill="x", padx=18, pady=(0, 16))
        Button(map_actions, "Haritayı Aç", command=lambda: self.shell.show("worldmap"), bg=ORANGE).pack(side="left", padx=(0, 8))
        Button(map_actions, "Turistik Yer Keşfet", command=lambda: self.shell.show("worldmap"), bg="#26384A").pack(side="left")

        recent = tk.Frame(map_card, bg=CARD2, highlightbackground="#324152", highlightthickness=1)
        recent.pack(fill="x", padx=18, pady=(0, 18))
        tk.Label(recent, text="Son keşif özeti", bg=CARD2, fg=ORANGE, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(recent, text=f"Son rota: {self.last_route_text()}", bg=CARD2, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(0, 3))
        tk.Label(recent, text="Haritadan bir bölge seçerek hava durumu, bölge kartı ve turistik yer ekranına geçebilirsin.", bg=CARD2, fg=MUTED, font=("Segoe UI", 9), wraplength=700, justify="left").pack(anchor="w", padx=14, pady=(0, 12))

        side = tk.Frame(body, bg=APP_BG)
        side.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=6)
        side.columnconfigure(0, weight=1)

        self.quick_card(side, "Rotalarım", "Başlangıç, bitiş, tarih ve duraklarını düzenle.", "Rotalara Git", "routes", BLUE).pack(fill="x", pady=(0, 10))
        self.quick_card(side, "Bütçe & Rezervasyon", "Harcama kalemlerini, otel/uçuş ve etkinlik kayıtlarını takip et.", "Bütçeyi Aç", "budget", ORANGE).pack(fill="x", pady=(0, 10))
        self.quick_card(side, "Günlük Plan", "Saat saat gezi akışı ve günlük program oluştur.", "Planı Aç", "days", GREEN).pack(fill="x", pady=(0, 10))

        bottom = tk.Frame(wrap, bg=APP_BG)
        bottom.pack(fill="x", pady=(14, 0))
        for i, (title, key) in enumerate([("Popüler", "popular"), ("Araçlar", "tools"), ("Rezervasyonlar", "reservations"), ("Günlük", "journal")]):
            bottom.columnconfigure(i, weight=1)
            card = tk.Frame(bottom, bg="#10161D", highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=0, column=i, sticky="nsew", padx=6)
            tk.Label(card, text=title, bg="#10161D", fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
            Button(card, "Aç", command=lambda k=key: self.shell.show(k), bg="#26384A").pack(anchor="w", padx=14, pady=(4, 12))





class BasePage(tk.Frame):
    title = ""
    subtitle = ""
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, bg=APP_BG)
        self.db = db
        self.shell = shell
        self.extra = kwargs
        self.header()

    def header(self):
        h = tk.Frame(self, bg=APP_BG)
        h.pack(fill="x", padx=26, pady=(20, 10))
        left = tk.Frame(h, bg=APP_BG)
        left.pack(side="left")
        tk.Label(left, text=self.title, bg=APP_BG, fg=TEXT, font=("Segoe UI", 23, "bold")).pack(anchor="w")
        tk.Label(left, text=self.subtitle, bg=APP_BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w")




class RouteCreatePage(BasePage):
    title = "Rota Oluştur"
    subtitle = "Çıkış ülkesi, varış ülkesi, il/bölge, tarih, ulaşım, otel ve bütçe planını tek ekranda oluştur."

    AIRLINES = [
        "Turkish Airlines", "Pegasus", "AJet", "Lufthansa", "Qatar Airways",
        "Emirates", "British Airways", "Air France", "KLM", "Singapore Airlines"
    ]
    BUS_COMPANIES = [
        "Metro Turizm", "Kamil Koç", "Pamukkale Turizm", "FlixBus", "Alsa",
        "Eurolines", "National Express", "BlaBlaCar Bus", "RegioJet", "Lux Express"
    ]

    def __init__(self, master, db, shell, **kwargs):
        self.countries = self.load_countries()
        self.depart_query = tk.StringVar()
        self.arrive_query = tk.StringVar()
        self.selected_depart = None
        self.selected_arrive = None
        self.selected_depart_region = tk.StringVar()
        self.depart_region_query = tk.StringVar()
        self.depart_region_values = []
        self.selected_region = tk.StringVar()
        self.region_query = tk.StringVar()
        self.region_values = []
        self.depart_date = tk.StringVar()
        self.return_date = tk.StringVar()
        self.transport = tk.StringVar(value="Uçak")
        self.destination_place = tk.StringVar()
        self.selected_hotel = tk.StringVar()
        self.hotel_prices = {}
        self.selected_transport_option = tk.StringVar()
        self.transport_prices = {}
        self.selected_travel_cost = 0
        self.selected_hotel_price = 0
        self.total_cost = 0
        self.note = None
        self.prefill = kwargs
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def load_countries(self):
        path = Path(__file__).parent / "harita_verileri" / "ulkeler_sinirlari.geojson"
        items = []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for f in data.get("features", []):
                p = f.get("properties", {})
                raw_name = p.get("NAME_TR") or p.get("NAME") or p.get("ADMIN")
                iso = p.get("ISO_A3") or p.get("ADM0_A3") or ""
                cont = p.get("CONTINENT") or "Dünya"
                cx, cy = self.feature_center(f)
                if raw_name:
                    name = country_tr(raw_name)
                    items.append({
                        "name": name,
                        "raw_name": raw_name,
                        "iso": iso,
                        "continent": cont,
                        "lat": cy,
                        "lon": cx
                    })
        except Exception:
            pass
        if not items:
            for raw_name, iso, cont, lat, lon in [
                ("Turkey","TUR","Asia",39,35), ("France","FRA","Europe",46,2), ("Germany","DEU","Europe",51,10),
                ("Italy","ITA","Europe",42,12), ("Japan","JPN","Asia",36,138), ("United States of America","USA","North America",39,-98)
            ]:
                items.append({"name": country_tr(raw_name), "raw_name": raw_name, "iso": iso, "continent": cont, "lat": lat, "lon": lon})
        # Aynı ülke iki kere gelirse tekilleştir.
        unique = {}
        for item in items:
            unique[item["name"]] = item
        return sorted(unique.values(), key=lambda x: x["name"])


    def feature_center(self, f):
        xs, ys = [], []
        def walk(obj):
            if isinstance(obj, (list, tuple)):
                if len(obj) >= 2 and isinstance(obj[0], (int, float)) and isinstance(obj[1], (int, float)):
                    xs.append(float(obj[0])); ys.append(float(obj[1]))
                else:
                    for it in obj:
                        walk(it)
        try:
            walk(f.get("geometry", {}).get("coordinates", []))
        except Exception:
            pass
        if xs and ys:
            return (sum(xs)/len(xs), sum(ys)/len(ys))
        return (0, 0)

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ScrollFrame(body, bg=APP_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = ScrollFrame(body, bg=APP_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        form = Card(left.inner, title="Rota Bilgileri")
        form.pack(fill="x", pady=(0, 10))

        tk.Label(form, text="Çıkış ülkesi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        self.depart_box = self.country_selector(form, self.depart_query, self.on_depart_select)
        self.depart_box.pack(fill="x", padx=16, pady=(0, 10))

        tk.Label(form, text="Çıkış ili / bölgesi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        self.depart_region_box = self.depart_region_selector(form)
        self.depart_region_box.pack(fill="x", padx=16, pady=(0, 10))
        self.selected_depart_region.set("Önce çıkış ülkesi seç")
        self.depart_region_query.set("Önce çıkış ülkesi seç")

        tk.Label(form, text="Varış ülkesi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        self.arrive_box = self.country_selector(form, self.arrive_query, self.on_arrive_select)
        self.arrive_box.pack(fill="x", padx=16, pady=(0, 10))

        tk.Label(form, text="Varış ili / bölgesi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        self.region_box = self.region_selector(form)
        self.region_box.pack(fill="x", padx=16, pady=(0, 10))
        self.selected_region.set("Önce varış ülkesi seç")
        self.region_query.set("Önce varış ülkesi seç")

        tk.Label(form, text="Gezilecek yer", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        tk.Entry(form, textvariable=self.destination_place, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10, "bold")).pack(fill="x", padx=16, ipady=8, pady=(0, 10))

        date_row = tk.Frame(form, bg=CARD)
        date_row.pack(fill="x", padx=16, pady=(8, 10))
        d1 = tk.Frame(date_row, bg=CARD)
        d1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        d2 = tk.Frame(date_row, bg=CARD)
        d2.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(d1, text="Gidiş tarihi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.depart_btn = Button(d1, "Gidiş Tarihi Seç", command=lambda: self.open_calendar(self.depart_date, "gidis"), bg=BLUE)
        self.depart_btn.pack(fill="x", pady=3)
        tk.Label(d2, text="Dönüş tarihi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.return_btn = Button(d2, "Dönüş Tarihi Seç", command=lambda: self.open_calendar(self.return_date, "donus"), bg=BLUE)
        self.return_btn.pack(fill="x", pady=3)

        tk.Label(form, text="Ulaşım tipi", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        trow = tk.Frame(form, bg=CARD)
        trow.pack(fill="x", padx=16, pady=(0, 10))
        for text in ["Araba", "Otobüs", "Uçak"]:
            tk.Radiobutton(trow, text=text, variable=self.transport, value=text, command=self.on_transport_mode_change, bg=CARD, fg=TEXT, selectcolor=CARD2, activebackground=CARD, activeforeground=TEXT).pack(side="left", padx=(0, 14))

        tk.Label(form, text="Not / Oraya gidince yapılacaklar", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        self.note = tk.Text(form, height=5, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", wrap="word")
        self.note.pack(fill="x", padx=16, pady=(0, 12))

        Button(form, "Rotayı Kaydet", command=self.save_route, bg=GREEN).pack(fill="x", padx=16, pady=(4, 16))

        self.hotel_card = Card(right.inner, title="Seçilen İldeki En İyi 10 Otel")
        self.hotel_card.pack(fill="x", pady=(0, 10))
        self.transport_card = Card(right.inner, title="Ulaşım ve Tahmini Maliyet")
        self.transport_card.pack(fill="x", pady=(0, 10))
        self.summary_card = Card(right.inner, title="Özet")
        self.summary_card.pack(fill="x", pady=(0, 10))

        self.update_date_buttons()
        self.apply_prefill()
        self.refresh_hotels()
        self.refresh_transport()
        self.refresh_summary()

    def country_selector(self, master, var, command):
        frame = tk.Frame(master, bg=CARD)

        search = tk.Entry(
            frame,
            textvariable=var,
            bg=CARD2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            highlightbackground="#34485F",
            highlightthickness=1
        )
        search.pack(fill="x", ipady=10)

        lb = tk.Listbox(
            frame,
            height=4,
            bg="#101826",
            fg=TEXT,
            selectbackground=BLUE,
            selectforeground="white",
            relief="flat",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground=BORDER,
            activestyle="none"
        )

        visible = {"value": False}
        exact_selected = {"value": ""}

        def is_exact_country():
            current = var.get().strip()
            return current and any(current == c["name"] for c in self.countries)

        def show_list(event=None, force=False):
            # Ülke seçildikten sonra tekrar tıklayınca dev liste açılmasın.
            # Kullanıcı yazmaya başlarsa liste tekrar açılır.
            if not force and is_exact_country() and event is not None and event.type.name in ("FocusIn", "ButtonPress"):
                hide_list()
                return
            if not visible["value"]:
                lb.pack(fill="x", pady=(4, 0))
                visible["value"] = True
            fill()

        def hide_list(event=None):
            if visible["value"]:
                lb.pack_forget()
                visible["value"] = False

        def fill(*_):
            q = normalize_tr_text(var.get())
            lb.delete(0, "end")
            count = 0
            for c in self.countries:
                name = c["name"]
                raw = c.get("raw_name", "")
                if not q or q in normalize_tr_text(name) or q in normalize_tr_text(raw):
                    lb.insert("end", name)
                    count += 1
                if count >= 30:
                    break

        def select(_=None):
            if not lb.curselection():
                return
            name = lb.get(lb.curselection()[0])
            for c in self.countries:
                if c["name"] == name:
                    exact_selected["value"] = name
                    command(c)
                    hide_list()
                    search.icursor("end")
                    break

        def key_release(event=None):
            show_list(event, force=True)

        search.bind("<FocusIn>", show_list)
        search.bind("<Button-1>", show_list)
        search.bind("<KeyRelease>", key_release)
        search.bind("<Escape>", hide_list)
        lb.bind("<<ListboxSelect>>", select)
        lb.bind("<Return>", select)
        var.trace_add("write", fill)
        fill()
        return frame


    def depart_region_selector(self, master):
        frame = tk.Frame(master, bg=CARD)
        entry = tk.Entry(
            frame,
            textvariable=self.depart_region_query,
            bg=CARD2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            highlightbackground="#34485F",
            highlightthickness=1
        )
        entry.pack(fill="x", ipady=10)

        lb = tk.Listbox(
            frame,
            height=5,
            bg="#101826",
            fg=TEXT,
            selectbackground=BLUE,
            selectforeground="white",
            relief="flat",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground=BORDER,
            activestyle="none"
        )
        visible = {"value": False}

        def hide():
            if visible["value"]:
                lb.pack_forget()
                visible["value"] = False

        def fill(*_):
            q = normalize_tr_text(self.depart_region_query.get())
            lb.delete(0, "end")
            if not self.selected_depart:
                lb.insert("end", "Önce çıkış ülkesi seç")
                return
            count = 0
            for r in self.depart_region_values:
                if not q or q in normalize_tr_text(r):
                    lb.insert("end", r)
                    count += 1
                if count >= 40:
                    break

        def show(event=None, force=False):
            if not self.selected_depart:
                self.depart_region_query.set("Önce çıkış ülkesi seç")
                return
            if not force and self.depart_region_query.get().strip() == self.selected_depart_region.get().strip():
                hide()
                return
            if not visible["value"]:
                lb.pack(fill="x", pady=(4, 0))
                visible["value"] = True
            fill()

        def select(event=None):
            if not lb.curselection():
                return
            value = lb.get(lb.curselection()[0])
            if value == "Önce çıkış ülkesi seç":
                return
            self.selected_depart_region.set(value)
            self.depart_region_query.set(value)
            hide()
            self.on_depart_region_change()

        def key(event=None):
            show(event, force=True)

        entry.bind("<FocusIn>", show)
        entry.bind("<Button-1>", show)
        entry.bind("<KeyRelease>", key)
        entry.bind("<Escape>", lambda e: hide())
        lb.bind("<<ListboxSelect>>", select)
        lb.bind("<Return>", select)
        self.depart_region_query.trace_add("write", fill)
        return frame

    def region_selector(self, master):
        frame = tk.Frame(master, bg=CARD)
        entry = tk.Entry(
            frame,
            textvariable=self.region_query,
            bg=CARD2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            highlightbackground="#34485F",
            highlightthickness=1
        )
        entry.pack(fill="x", ipady=10)

        lb = tk.Listbox(
            frame,
            height=5,
            bg="#101826",
            fg=TEXT,
            selectbackground=BLUE,
            selectforeground="white",
            relief="flat",
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground=BORDER,
            activestyle="none"
        )
        visible = {"value": False}

        def hide():
            if visible["value"]:
                lb.pack_forget()
                visible["value"] = False

        def fill(*_):
            q = normalize_tr_text(self.region_query.get())
            lb.delete(0, "end")
            if not self.selected_arrive:
                lb.insert("end", "Önce varış ülkesi seç")
                return
            count = 0
            for r in self.region_values:
                if not q or q in normalize_tr_text(r):
                    lb.insert("end", r)
                    count += 1
                if count >= 40:
                    break

        def show(event=None, force=False):
            if not self.selected_arrive:
                self.region_query.set("Önce varış ülkesi seç")
                return
            # Seçili bölgeye tekrar tıklayınca kocaman liste açılmasın.
            if not force and self.region_query.get().strip() == self.selected_region.get().strip():
                hide()
                return
            if not visible["value"]:
                lb.pack(fill="x", pady=(4, 0))
                visible["value"] = True
            fill()

        def select(event=None):
            if not lb.curselection():
                return
            value = lb.get(lb.curselection()[0])
            if value == "Önce varış ülkesi seç":
                return
            self.selected_region.set(value)
            self.region_query.set(value)
            hide()
            self.on_region_change()

        def key(event=None):
            show(event, force=True)

        entry.bind("<FocusIn>", show)
        entry.bind("<Button-1>", show)
        entry.bind("<KeyRelease>", key)
        entry.bind("<Escape>", lambda e: hide())
        lb.bind("<<ListboxSelect>>", select)
        lb.bind("<Return>", select)
        self.region_query.trace_add("write", fill)
        return frame

    def on_depart_select(self, country):
        self.selected_depart = country
        self.depart_query.set(country["name"])
        regions = regions_for(country.get("iso", ""), country["name"])
        self.set_depart_region_values(regions)
        self.refresh_transport()
        self.refresh_summary()

    def set_depart_region_values(self, regions, wanted=None):
        self.depart_region_values = list(regions or [])
        if not self.depart_region_values:
            self.selected_depart_region.set("Bölge yok")
            self.depart_region_query.set("Bölge yok")
            return
        if wanted and wanted in self.depart_region_values:
            value = wanted
        else:
            value = self.depart_region_values[0]
        self.selected_depart_region.set(value)
        self.depart_region_query.set(value)

    def on_depart_region_change(self):
        self.selected_transport_option.set("")
        self.selected_travel_cost = 0
        self.refresh_transport()
        self.refresh_summary()


    def set_region_values(self, regions, wanted=None):
        self.region_values = list(regions or [])
        if not self.region_values:
            self.selected_region.set("Bölge yok")
            self.region_query.set("Bölge yok")
            return
        if wanted and wanted in self.region_values:
            value = wanted
        else:
            value = self.region_values[0]
        self.selected_region.set(value)
        self.region_query.set(value)

    def on_arrive_select(self, country):
        self.selected_arrive = country
        self.arrive_query.set(country["name"])
        regions = regions_for(country.get("iso", ""), country["name"])
        wanted = self.prefill.get("arrive_region") if hasattr(self, "prefill") else None
        self.set_region_values(regions, wanted)
        self.refresh_hotels()
        self.refresh_transport()
        self.refresh_summary()

    def on_region_change(self):
        self.selected_transport_option.set("")
        self.selected_travel_cost = 0
        self.refresh_hotels()
        self.refresh_transport()
        self.refresh_summary()

    def normalize_name(self, text):
        return normalize_tr_text(text)

    def find_country_by_name(self, name):
        n = self.normalize_name(name)
        aliases = {
            "turkiye": "turkiye",
            "türkiye": "turkiye",
            "turkey": "turkiye",
            "abd": "amerika birlesik devletleri",
            "amerika": "amerika birlesik devletleri",
            "united states of america": "amerika birlesik devletleri",
            "united states": "amerika birlesik devletleri",
            "ingiltere": "birlesik krallik",
            "united kingdom": "birlesik krallik",
            "almanya": "almanya",
            "germany": "almanya",
            "fransa": "fransa",
            "france": "fransa",
            "italya": "italya",
            "italy": "italya",
            "ispanya": "ispanya",
            "spain": "ispanya",
            "japonya": "japonya",
            "japan": "japonya",
            "misir": "misir",
            "mısır": "misir",
            "egypt": "misir",
            "cekya": "cekya",
            "çekya": "cekya",
            "czechia": "cekya",
            "hollanda": "hollanda",
            "netherlands": "hollanda",
            "avustralya": "avustralya",
            "australia": "avustralya",
            "brezilya": "brezilya",
            "brazil": "brezilya",
            "bae": "birlesik arap emirlikleri",
            "united arab emirates": "birlesik arap emirlikleri",
            "singapore": "singapur",
            "maldives": "maldivler",
        }
        n2 = aliases.get(n, n)
        for c in self.countries:
            cn = self.normalize_name(c["name"])
            raw = self.normalize_name(c.get("raw_name", ""))
            if cn == n or cn == n2 or raw == n or raw == n2 or n in cn or n2 in cn:
                return c
        return None

    def apply_prefill(self):
        if not getattr(self, "prefill", None):
            return
        arrive_country = self.prefill.get("arrive_country")
        arrive_region = self.prefill.get("arrive_region")
        destination_place = self.prefill.get("destination_place")
        if destination_place:
            self.destination_place.set(destination_place)
        if arrive_country:
            country = self.find_country_by_name(arrive_country)
            if country:
                self.selected_arrive = country
                self.arrive_query.set(country["name"])
                regions = regions_for(country.get("iso", ""), country["name"])
                self.set_region_values(regions, arrive_region)
        elif arrive_region:
            self.selected_region.set(arrive_region)
            self.region_query.set(arrive_region)



    def parse_date(self, s):
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None

    def update_date_buttons(self):
        try:
            self.depart_btn.configure(text=self.depart_date.get() or "Gidiş Tarihi Seç")
            self.return_btn.configure(text=self.return_date.get() or "Dönüş Tarihi Seç")
        except Exception:
            pass

    def open_calendar(self, var, kind):
        today = datetime.now().date()
        current = self.parse_date(var.get()) or today
        win = tk.Toplevel(self)
        win.title("Tarih Seç")
        win.geometry("360x340")
        win.configure(bg=APP_BG)
        y = tk.IntVar(value=current.year)
        m = tk.IntVar(value=current.month)

        header = tk.Frame(win, bg=APP_BG)
        header.pack(fill="x", padx=16, pady=12)
        tk.Button(header, text="‹", command=lambda: change_month(-1), bg=CARD2, fg=TEXT, relief="flat").pack(side="left")
        title = tk.Label(header, bg=APP_BG, fg=TEXT, font=("Segoe UI", 13, "bold"))
        title.pack(side="left", expand=True)
        tk.Button(header, text="›", command=lambda: change_month(1), bg=CARD2, fg=TEXT, relief="flat").pack(side="right")
        grid = tk.Frame(win, bg=APP_BG)
        grid.pack(fill="both", expand=True, padx=16, pady=8)

        def change_month(delta):
            mm = m.get() + delta
            yy = y.get()
            if mm < 1:
                mm = 12; yy -= 1
            elif mm > 12:
                mm = 1; yy += 1
            m.set(mm); y.set(yy)
            draw()

        def choose(day):
            d = datetime(y.get(), m.get(), day).date()
            if kind == "gidis" and d < today:
                messagebox.showerror("Tarih Hatası", "Gidiş tarihi bugünden önce olamaz.")
                return
            if kind == "donus":
                gidis = self.parse_date(self.depart_date.get())
                if gidis and d < gidis:
                    messagebox.showerror("Tarih Hatası", "Dönüş tarihi gidiş tarihinden önce olamaz.")
                    return
            var.set(d.strftime("%Y-%m-%d"))
            self.update_date_buttons()
            if kind == "gidis":
                donus = self.parse_date(self.return_date.get())
                if donus and donus < d:
                    self.return_date.set("")
                    self.update_date_buttons()
            self.refresh_summary()
            win.destroy()

        def draw():
            for w in grid.winfo_children():
                w.destroy()
            title.configure(text=f"{TR_MONTHS.get(m.get(), m.get())} {y.get()}")
            for i, dname in enumerate(["Pzt", "Sal", "Çar", "Per", "Cum", "Cmt", "Paz"]):
                tk.Label(grid, text=dname, bg=APP_BG, fg=MUTED, font=("Segoe UI", 8, "bold")).grid(row=0, column=i, sticky="nsew", padx=2, pady=2)
            cal = calendar.Calendar(firstweekday=0)
            for r, week in enumerate(cal.monthdayscalendar(y.get(), m.get()), start=1):
                for c, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid, text="", bg=APP_BG).grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
                    else:
                        d = datetime(y.get(), m.get(), day).date()
                        disabled = (kind == "gidis" and d < today)
                        bg = "#1F2A34" if not disabled else "#111820"
                        fg = TEXT if not disabled else "#53606C"
                        tk.Button(grid, text=str(day), command=(lambda dd=day: choose(dd)) if not disabled else None, bg=bg, fg=fg, relief="flat").grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
            for c in range(7):
                grid.columnconfigure(c, weight=1)
        draw()

    def province_coord_lookup(self, country_name, region_name):
        """Bilinen iller için yaklaşık merkez koordinatları. Özellikle Türkiye içi mesafe daha doğru olsun."""
        if not country_name or not region_name:
            return None
        c = normalize_tr_text(country_name)
        r = normalize_tr_text(region_name)
        turkey = {
            "adana": (37.00, 35.32), "adiyaman": (37.76, 38.28), "afyonkarahisar": (38.76, 30.54),
            "agri": (39.72, 43.05), "ağri": (39.72, 43.05), "amasya": (40.65, 35.83),
            "ankara": (39.93, 32.86), "antalya": (36.89, 30.71), "artvin": (41.18, 41.82),
            "aydin": (37.84, 27.85), "aydın": (37.84, 27.85), "balikesir": (39.65, 27.89),
            "balıkesir": (39.65, 27.89), "bilecik": (40.15, 29.98), "bingol": (38.89, 40.50),
            "bingöl": (38.89, 40.50), "bitlis": (38.40, 42.11), "bolu": (40.73, 31.61),
            "burdur": (37.72, 30.29), "bursa": (40.19, 29.06), "canakkale": (40.15, 26.41),
            "çanakkale": (40.15, 26.41), "cankiri": (40.60, 33.62), "çankırı": (40.60, 33.62),
            "corum": (40.55, 34.95), "çorum": (40.55, 34.95), "denizli": (37.78, 29.09),
            "diyarbakir": (37.91, 40.24), "diyarbakır": (37.91, 40.24), "edirne": (41.68, 26.56),
            "elazig": (38.68, 39.22), "elazığ": (38.68, 39.22), "erzincan": (39.75, 39.49),
            "erzurum": (39.90, 41.27), "eskisehir": (39.77, 30.52), "eskişehir": (39.77, 30.52),
            "gaziantep": (37.07, 37.38), "giresun": (40.91, 38.39), "gumushane": (40.46, 39.48),
            "gümüşhane": (40.46, 39.48), "hakkari": (37.57, 43.74), "hatay": (36.20, 36.16),
            "isparta": (37.76, 30.56), "mersin": (36.80, 34.63), "istanbul": (41.01, 28.97),
            "izmir": (38.42, 27.14), "kars": (40.60, 43.10), "kastamonu": (41.38, 33.78),
            "kayseri": (38.72, 35.49), "kirklareli": (41.74, 27.22), "kırklareli": (41.74, 27.22),
            "kirsehir": (39.15, 34.16), "kırşehir": (39.15, 34.16), "kocaeli": (40.77, 29.94),
            "konya": (37.87, 32.48), "kutahya": (39.42, 29.98), "kütahya": (39.42, 29.98),
            "malatya": (38.35, 38.31), "manisa": (38.61, 27.43), "kahramanmaras": (37.58, 36.94),
            "kahramanmaraş": (37.58, 36.94), "mardin": (37.31, 40.74), "mugla": (37.22, 28.36),
            "muğla": (37.22, 28.36), "mus": (38.74, 41.49), "muş": (38.74, 41.49),
            "nevsehir": (38.62, 34.71), "nevşehir": (38.62, 34.71), "nigde": (37.97, 34.68),
            "niğde": (37.97, 34.68), "ordu": (40.98, 37.88), "rize": (41.02, 40.52),
            "sakarya": (40.78, 30.40), "samsun": (41.29, 36.33), "siirt": (37.93, 41.94),
            "sinop": (42.03, 35.15), "sivas": (39.75, 37.02), "tekirdag": (40.98, 27.51),
            "tekirdağ": (40.98, 27.51), "tokat": (40.32, 36.55), "trabzon": (41.00, 39.72),
            "tunceli": (39.11, 39.55), "sanliurfa": (37.16, 38.80), "şanlıurfa": (37.16, 38.80),
            "usak": (38.68, 29.40), "uşak": (38.68, 29.40), "van": (38.49, 43.38),
            "yozgat": (39.82, 34.81), "zonguldak": (41.45, 31.79), "aksaray": (38.37, 34.03),
            "bayburt": (40.26, 40.22), "karaman": (37.18, 33.22), "kirikkale": (39.84, 33.51),
            "kırıkkale": (39.84, 33.51), "batman": (37.88, 41.13), "sirnak": (37.52, 42.46),
            "şırnak": (37.52, 42.46), "bartin": (41.64, 32.34), "bartın": (41.64, 32.34),
            "ardahan": (41.11, 42.70), "igdir": (39.92, 44.04), "ığdır": (39.92, 44.04),
            "yalova": (40.65, 29.27), "karabuk": (41.20, 32.63), "karabük": (41.20, 32.63),
            "kilis": (36.72, 37.12), "osmaniye": (37.07, 36.25), "duzce": (40.84, 31.16),
            "düzce": (40.84, 31.16)
        }
        if c in ["turkiye", "türkiye", "turkey"] and r in turkey:
            return turkey[r]
        return None

    def synthetic_region_coord(self, country, region_name):
        """Tüm dünya için gerçek veri yoksa, ülke merkezi çevresinde stabil yaklaşık il noktası üretir."""
        if not country:
            return (0.0, 0.0)
        known = self.province_coord_lookup(country.get("name", ""), region_name)
        if known:
            return known

        lat = float(country.get("lat", 0) or 0)
        lon = float(country.get("lon", 0) or 0)
        key = normalize_tr_text(f"{country.get('name','')}-{region_name}")
        h = abs(hash(key))
        # Ülke merkezinden küçük ama stabil kayma; aynı ülke içinde farklı iller farklı km verir.
        lat_offset = ((h % 900) / 900 - 0.5) * 5.0
        lon_offset = (((h // 997) % 900) / 900 - 0.5) * 7.0
        return (lat + lat_offset, lon + lon_offset)

    def route_points(self):
        if not (self.selected_depart and self.selected_arrive):
            return None, None
        dep_region = self.selected_depart_region.get()
        arr_region = self.selected_region.get()
        p1 = self.synthetic_region_coord(self.selected_depart, dep_region)
        p2 = self.synthetic_region_coord(self.selected_arrive, arr_region)
        return p1, p2

    def distance_km(self):
        if not (self.selected_depart and self.selected_arrive):
            return 0
        p1, p2 = self.route_points()
        if not p1 or not p2:
            return 0
        lat1 = math.radians(p1[0]); lon1 = math.radians(p1[1])
        lat2 = math.radians(p2[0]); lon2 = math.radians(p2[1])
        dlat = lat2 - lat1; dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        km = int(6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))
        return max(10, km)



    def overseas(self):
        if not (self.selected_depart and self.selected_arrive):
            return False

        dep_name = normalize_tr_text(self.selected_depart.get("name", ""))
        arr_name = normalize_tr_text(self.selected_arrive.get("name", ""))
        dep_iso = str(self.selected_depart.get("iso", "")).upper()
        arr_iso = str(self.selected_arrive.get("iso", "")).upper()

        if dep_name == arr_name or (dep_iso and dep_iso == arr_iso):
            return False

        # Farklı kıta: kara/otobüs/araba rotası yerine uçak öner.
        if self.selected_depart.get("continent") != self.selected_arrive.get("continent"):
            return True

        # Ada veya deniz aşırı kabul edilen ülkeler. Aynı kıtada olsalar bile araba/otobüs engellenir.
        island_or_oversea = {
            "japonya", "japan", "ingiltere", "birlesik krallik", "united kingdom", "britain", "great britain",
            "irlanda", "ireland", "izlanda", "iceland", "avustralya", "australia", "yeni zelanda", "new zealand",
            "endonezya", "indonesia", "filipinler", "philippines", "singapur", "singapore", "kibris", "cyprus",
            "maldivler", "maldives", "sri lanka", "madagaskar", "madagascar", "gronland", "greenland",
            "tayvan", "taiwan", "kuba", "cuba", "bahamalar", "bahamas"
        }
        if dep_name in island_or_oversea or arr_name in island_or_oversea:
            return True

        # Aynı kıtada ama çok uzun ve pratikte uçuş gerektiren rotalarda da uyarı ver.
        try:
            if self.distance_km() > 3500:
                return True
        except Exception:
            pass

        return False



    def clear_card(self, card, title=None):
        for w in card.winfo_children():
            w.destroy()
        if title:
            tk.Label(card, text=title, bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(14, 6))

    def nights_count(self):
        gidis = self.parse_date(self.depart_date.get())
        donus = self.parse_date(self.return_date.get())
        if gidis and donus and donus >= gidis:
            return max(1, (donus - gidis).days)
        return 1

    def money(self, value):
        try:
            return f"{int(value):,}".replace(",", ".") + " $"
        except Exception:
            return str(value) + " $"

    def choose_hotel(self, hotel, price):
        self.selected_hotel.set(hotel)
        self.selected_hotel_price = int(price)
        self.refresh_summary()

    def choose_transport_option(self, option, price):
        self.selected_transport_option.set(option)
        self.selected_travel_cost = int(price)
        self.refresh_summary()

    def refresh_hotels(self):
        self.clear_card(self.hotel_card, "Seçilen İldeki En İyi 10 Otel")
        self.hotel_prices = {}
        if not (self.selected_arrive and self.selected_region.get() and self.selected_region.get() not in ["Önce varış ülkesi seç", "Bölge yok"]):
            tk.Label(self.hotel_card, text="Önce varış ülkesi ve il/bölge seç.", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=12)
            self.selected_hotel.set("")
            self.selected_hotel_price = 0
            self.refresh_summary()
            return

        base = abs(hash(self.selected_region.get() + self.selected_arrive["name"])) % 120
        names = ["Grand", "Royal", "Central", "City", "Palace", "Park", "Vista", "Blue", "Elite", "Garden"]
        for i in range(10):
            price = 55 + ((base + i * 17) % 220)
            hotel = f"{self.selected_region.get()} {names[i]} Hotel"
            self.hotel_prices[hotel] = price
            if i == 0 and not self.selected_hotel.get():
                self.selected_hotel.set(hotel)
                self.selected_hotel_price = price

            row = tk.Frame(self.hotel_card, bg=CARD)
            row.pack(fill="x", padx=12, pady=2)
            tk.Radiobutton(
                row,
                text=f"{i+1}. {hotel}  •  {price} $ / gece",
                variable=self.selected_hotel,
                value=hotel,
                command=lambda h=hotel, p=price: self.choose_hotel(h, p),
                bg=CARD,
                fg=TEXT,
                selectcolor=CARD2,
                activebackground=CARD,
                activeforeground=TEXT,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
                justify="left"
            ).pack(fill="x", anchor="w")

        # Seçili otel farklı bölgeden kalmışsa ilk oteli seç.
        if self.selected_hotel.get() not in self.hotel_prices:
            first = next(iter(self.hotel_prices))
            self.selected_hotel.set(first)
            self.selected_hotel_price = self.hotel_prices[first]
        else:
            self.selected_hotel_price = self.hotel_prices.get(self.selected_hotel.get(), 0)

        self.refresh_summary()


    def on_transport_mode_change(self):
        self.selected_transport_option.set("")
        self.selected_travel_cost = 0
        self.refresh_transport()

    def refresh_transport(self):
        self.clear_card(self.transport_card, "Ulaşım ve Tahmini Maliyet")
        self.transport_prices = {}
        self.selected_travel_cost = 0

        if not (self.selected_depart and self.selected_arrive):
            tk.Label(self.transport_card, text="Ulaşım hesaplaması için çıkış ve varış ülkesi seç.", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=12)
            self.refresh_summary()
            return
        if self.selected_depart_region.get() in ["", "Önce çıkış ülkesi seç", "Bölge yok"] or self.selected_region.get() in ["", "Önce varış ülkesi seç", "Bölge yok"]:
            tk.Label(self.transport_card, text="Mesafe için çıkış ili/bölgesi ve varış ili/bölgesi seç.", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=12)
            self.refresh_summary()
            return

        mode = self.transport.get()
        km = max(100, self.distance_km())

        if mode in ["Araba", "Otobüs"] and self.overseas():
            tk.Label(self.transport_card, text="Deniz aşırı / farklı kıta rotalarında araba ve otobüs seçilemez. Uçak seçmelisin.", bg=CARD, fg=RED, font=("Segoe UI", 10, "bold"), wraplength=460, justify="left").pack(anchor="w", padx=16, pady=12)
            self.selected_transport_option.set("")
            self.selected_travel_cost = 0
            self.refresh_summary()
            return

        if mode == "Araba":
            hours = km / 85
            fuel = int(km * 0.075 * 1.7)
            toll = int(km * 0.04)
            total = fuel + toll
            self.selected_transport_option.set("Araba")
            self.selected_travel_cost = total
            for txt in [
                f"Tahmini mesafe: {km:,} km".replace(",", "."),
                f"Tahmini süre: {int(hours)} saat {int((hours % 1) * 60)} dakika",
                f"Tahmini benzin: {fuel} $",
                f"Tahmini geçiş/gişe: {toll} $",
                f"Tahmini yol maliyeti: {total} $",
            ]:
                tk.Label(self.transport_card, text=txt, bg=CARD, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=4)

        elif mode == "Otobüs":
            for i, company in enumerate(self.BUS_COMPANIES):
                price = 25 + ((km // 100 + i * 9) % 90)
                hours = max(2, int(km / 70 + i % 3))
                self.transport_prices[company] = price
                if i == 0 and not self.selected_transport_option.get():
                    self.selected_transport_option.set(company)
                    self.selected_travel_cost = price
                tk.Radiobutton(
                    self.transport_card,
                    text=f"{i+1}. {company} • {price} $ • {hours} saat",
                    variable=self.selected_transport_option,
                    value=company,
                    command=lambda c=company, p=price: self.choose_transport_option(c, p),
                    bg=CARD,
                    fg=TEXT,
                    selectcolor=CARD2,
                    activebackground=CARD,
                    activeforeground=TEXT,
                    font=("Segoe UI", 9, "bold"),
                    anchor="w",
                    justify="left"
                ).pack(fill="x", padx=12, pady=2)
            if self.selected_transport_option.get() not in self.transport_prices:
                first = next(iter(self.transport_prices))
                self.selected_transport_option.set(first)
                self.selected_travel_cost = self.transport_prices[first]
            else:
                self.selected_travel_cost = self.transport_prices.get(self.selected_transport_option.get(), 0)

        else:
            for i, company in enumerate(self.AIRLINES):
                price = 80 + ((km // 45 + i * 37) % 620)
                hours = max(1, int(km / 780 + 1 + (i % 2)))
                self.transport_prices[company] = price
                if i == 0 and not self.selected_transport_option.get():
                    self.selected_transport_option.set(company)
                    self.selected_travel_cost = price
                tk.Radiobutton(
                    self.transport_card,
                    text=f"{i+1}. {company} • {price} $ • {hours} saat",
                    variable=self.selected_transport_option,
                    value=company,
                    command=lambda c=company, p=price: self.choose_transport_option(c, p),
                    bg=CARD,
                    fg=TEXT,
                    selectcolor=CARD2,
                    activebackground=CARD,
                    activeforeground=TEXT,
                    font=("Segoe UI", 9, "bold"),
                    anchor="w",
                    justify="left"
                ).pack(fill="x", padx=12, pady=2)
            if self.selected_transport_option.get() not in self.transport_prices:
                first = next(iter(self.transport_prices))
                self.selected_transport_option.set(first)
                self.selected_travel_cost = self.transport_prices[first]
            else:
                self.selected_travel_cost = self.transport_prices.get(self.selected_transport_option.get(), 0)

        self.refresh_summary()


    def budget_limit(self):
        try:
            return float(self.db.veri.get("ayarlar", {}).get("butce_limiti", 0) or 0)
        except Exception:
            return 0

    def spent_before_current_plan(self):
        total = 0
        try:
            for item in self.db.veri.get("butce", []):
                total += float(item.get("tutar", 0) or 0)
        except Exception:
            pass
        return total

    def budget_warning_text(self):
        limit = self.budget_limit()
        if not limit:
            return ""
        used = self.spent_before_current_plan()
        after = used + float(self.total_cost or 0)
        if after > limit:
            return f"Bütçenizi artırın veya daha ekonomik seçim yapın. Bu planla bütçe {int(after - limit)} TL aşılacak."
        return f"Bütçe uygun. Plan sonrası kalan yaklaşık {int(limit - after)} TL."

    def refresh_summary(self):
        self.clear_card(self.summary_card, "Özet ve Toplam Masraf")
        nights = self.nights_count()
        hotel_price = int(self.selected_hotel_price or 0)
        hotel_total = hotel_price * nights if self.selected_hotel.get() else 0
        travel_total = int(self.selected_travel_cost or 0)
        total = hotel_total + travel_total
        self.total_cost = total

        km = self.distance_km() if (self.selected_depart and self.selected_arrive) else 0
        lines = [
            f"Çıkış: {self.selected_depart['name'] if self.selected_depart else '-'}",
            f"Çıkış ili/bölgesi: {self.selected_depart_region.get() or '-'}",
            f"Varış: {self.selected_arrive['name'] if self.selected_arrive else '-'}",
            f"Varış ili/bölgesi: {self.selected_region.get() or '-'}",
            f"Tahmini mesafe: {km} km" if km else "Tahmini mesafe: -",
            f"Gezilecek yer: {self.destination_place.get() or '-'}",
            f"Gidiş: {self.depart_date.get() or '-'}",
            f"Dönüş: {self.return_date.get() or '-'}",
            f"Gece sayısı: {nights}",
            f"Ulaşım: {self.transport.get()} / {self.selected_transport_option.get() or '-'}",
            f"Otel: {self.selected_hotel.get() or '-'}",
            f"Otel masrafı: {hotel_price} $ x {nights} gece = {hotel_total} $",
            f"Ulaşım masrafı: {travel_total} $",
        ]
        for l in lines:
            tk.Label(self.summary_card, text=l, bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold"), wraplength=450, justify="left").pack(anchor="w", padx=16, pady=3)

        tk.Label(
            self.summary_card,
            text=f"Toplam tahmini masraf: {total} $",
            bg=CARD,
            fg=GREEN if total else MUTED,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w", padx=16, pady=(12, 8))

        warning = self.budget_warning_text()
        if warning:
            over = "artırın" in warning
            tk.Label(
                self.summary_card,
                text=warning,
                bg=CARD,
                fg=RED if over else GREEN,
                font=("Segoe UI", 11, "bold"),
                wraplength=440,
                justify="left"
            ).pack(anchor="w", padx=16, pady=(0, 14))


    def validate(self):
        today = datetime.now().date()
        if not self.selected_depart or not self.selected_arrive:
            messagebox.showerror("Eksik", "Çıkış ve varış ülkesi seç.")
            return False
        if not self.selected_depart_region.get() or self.selected_depart_region.get() in ["Önce çıkış ülkesi seç", "Bölge yok"]:
            messagebox.showerror("Eksik", "Çıkış ili/bölgesi seç.")
            return False
        if not self.selected_region.get() or self.selected_region.get() in ["Önce varış ülkesi seç", "Bölge yok"]:
            messagebox.showerror("Eksik", "Varış ili/bölgesi seç.")
            return False
        gidis = self.parse_date(self.depart_date.get())
        donus = self.parse_date(self.return_date.get())
        if not gidis or not donus:
            messagebox.showerror("Eksik", "Gidiş ve dönüş tarihlerini seç.")
            return False
        if gidis < today:
            messagebox.showerror("Tarih Hatası", "Gidiş tarihi bugünden önce olamaz.")
            return False
        if donus < gidis:
            messagebox.showerror("Tarih Hatası", "Dönüş tarihi gidiş tarihinden önce olamaz.")
            return False
        if self.transport.get() in ["Araba", "Otobüs"] and self.overseas():
            messagebox.showerror("Ulaşım Hatası", "Deniz aşırı / farklı kıta rotalarında araba ve otobüs seçilemez. Uçak seçmelisin.")
            return False
        if not self.selected_hotel.get():
            messagebox.showerror("Eksik", "Sağ taraftan bir otel seç.")
            return False
        if self.transport.get() != "Araba" and not self.selected_transport_option.get():
            messagebox.showerror("Eksik", "Sağ taraftan bir ulaşım firması seç.")
            return False
        return True

    def save_route(self):
        if not self.validate():
            return
        self.refresh_summary()
        sid = f"S{len(self.db.veri.get('seyahatler', [])) + 1:03d}"
        not_text = self.note.get("1.0", "end").strip()
        nights = self.nights_count()
        hotel_total = int(self.selected_hotel_price or 0) * nights
        travel_total = int(self.selected_travel_cost or 0)
        total = hotel_total + travel_total
        place = self.destination_place.get().strip() or self.selected_region.get()
        popular_id = match_popular_place_id(place)

        route = {
            "seyahat_id": sid,
            "baslik": f"{self.selected_depart_region.get()} - {self.selected_region.get()} Rota Planı",
            "baslangic": f"{self.selected_depart['name']} / {self.selected_depart_region.get()}",
            "bitis": f"{self.selected_arrive['name']} / {self.selected_region.get()}",
            "tarih": self.depart_date.get(),
            "donus": self.return_date.get(),
            "butce": total,
            "tip": self.transport.get(),
            "durum": "Planlanıyor",
            "not": not_text,
            "otel": self.selected_hotel.get(),
            "ulasim_firmasi": self.selected_transport_option.get(),
            "toplam_masraf": total,
            "populer_yer_id": popular_id,
            "duraklar": [{
                "sehir": self.selected_region.get(),
                "gun": str(nights),
                "yerler": place,
                "harcama": str(total),
                "not": not_text
            }],
        }
        self.db.veri.setdefault("seyahatler", []).append(route)

        # Bütçe ekranında toplam maliyet gider olarak görünsün.
        self.db.veri.setdefault("butce", []).append({
            "kategori": "Konaklama",
            "tutar": hotel_total,
            "not": f"{self.selected_hotel.get()} • {nights} gece • {self.selected_region.get()}",
        })
        self.db.veri.setdefault("butce", []).append({
            "kategori": "Ulaşım",
            "tutar": travel_total,
            "not": f"{self.transport.get()} • {self.selected_transport_option.get() or 'Araba'} • {self.selected_depart['name']} / {self.selected_depart_region.get()} → {self.selected_arrive['name']} / {self.selected_region.get()}",
        })

        self.db.kaydet()
        messagebox.showinfo(
            "Rota Oluşturuldu",
            f"Rota başarıyla kaydedildi.\\nToplam tahmini masraf: {total} $\\nBu tutar bütçe giderlerine eklendi."
        )
        self.shell.show("routes")


class PopularPlacesPage(BasePage):
    title = "Popüler Turistik Yerler"
    subtitle = "Turistler için popüler duraklar, fotoğraflar, tarihçe, bütçe, otel önerileri ve ziyaretçi yorumları."

    PLACES = [
        {
            "id": "paris_eiffel",
            "ad": "Paris - Eyfel Kulesi",
            "ulke": "Fransa",
            "puan": "9.7",
            "etiket": "Romantik şehir",
            "img": "01_paris_eiffel.png",
            "butce": "Günlük ortalama 120 - 220 €",
            "desc": "Müze, kafe, nehir yürüyüşü ve şehir manzarası için en popüler Avrupa duraklarından biri.",
            "tarihce": "Eyfel Kulesi, 1889 Paris Dünya Fuarı için inşa edildi ve kısa sürede Paris'in en güçlü simgesi haline geldi. Başlangıçta geçici bir yapı olarak planlansa da zamanla şehrin kültürel kimliğinin ayrılmaz parçası oldu.",
            "oteller": ["Hôtel La Comtesse", "Pullman Paris Tour Eiffel", "Hôtel Eiffel Blomet", "Le Parisis Paris", "Hôtel Gustave"],
        },
        {
            "id": "istanbul_hagia_sophia",
            "ad": "İstanbul - Ayasofya / Sultanahmet",
            "ulke": "Türkiye",
            "puan": "9.6",
            "etiket": "Tarih + boğaz",
            "img": "02_istanbul_hagia_sophia.png",
            "butce": "Günlük ortalama 2.500 - 6.000 TL",
            "desc": "Ayasofya, Sultanahmet, Kapalıçarşı ve Boğaz hattıyla kültür gezileri için güçlü bir rota.",
            "tarihce": "Ayasofya, Bizans döneminden Osmanlı'ya ve günümüze uzanan çok katmanlı tarihiyle İstanbul'un en önemli yapılarından biridir. Sultanahmet çevresi, Roma, Bizans ve Osmanlı mirasını aynı yürüyüş rotasında birleştirir.",
            "oteller": ["Seven Hills Hotel", "Sura Hagia Sophia Hotel", "White House Hotel Istanbul", "Hotel Amira Istanbul", "Armada Istanbul Old City"],
        },
        {
            "id": "rome_colosseum",
            "ad": "Roma - Kolezyum",
            "ulke": "İtalya",
            "puan": "9.5",
            "etiket": "Antik kent",
            "img": "03_rome_colosseum.png",
            "butce": "Günlük ortalama 100 - 200 €",
            "desc": "Kolezyum, Vatikan, meydanlar ve klasik İtalyan sokaklarıyla tarih odaklı gezi.",
            "tarihce": "Kolezyum, Roma İmparatorluğu'nun en büyük amfitiyatrolarından biri olarak MS 1. yüzyılda inşa edildi. Gladyatör dövüşleri ve büyük halk etkinlikleriyle antik Roma yaşamının merkezlerinden biri oldu.",
            "oteller": ["Hotel Capo d'Africa", "Palazzo Manfredi", "Hotel Duca d'Alba", "Monti Palace Hotel", "FH55 Grand Hotel Palatino"],
        },
        {
            "id": "london_big_ben",
            "ad": "Londra - Big Ben",
            "ulke": "İngiltere",
            "puan": "9.4",
            "etiket": "Klasik şehir",
            "img": "04_london_big_ben.png",
            "butce": "Günlük ortalama 130 - 260 £",
            "desc": "Westminster, Thames kıyısı, müzeler ve klasik Londra rotaları için güçlü bir başlangıç noktası.",
            "tarihce": "Big Ben adı genellikle saat kulesi için kullanılsa da aslında kulenin içindeki büyük çanı ifade eder. Westminster Sarayı ile birlikte Londra'nın siyasi ve tarihi simgelerinden biridir.",
            "oteller": ["Park Plaza Westminster Bridge", "The Westminster London", "St. Ermin's Hotel", "Conrad London St. James", "The Sanctuary House Hotel"],
        },
        {
            "id": "newyork_times_square",
            "ad": "New York - Times Square",
            "ulke": "ABD",
            "puan": "9.2",
            "etiket": "Şehir turu",
            "img": "05_newyork_times_square.png",
            "butce": "Günlük ortalama 180 - 350 $",
            "desc": "Times Square, Central Park, müzeler ve gökdelen manzaralarıyla klasik şehir rotası.",
            "tarihce": "Times Square, 20. yüzyılın başından itibaren tiyatroları, reklam panoları ve yoğun şehir hayatıyla New York'un en bilinen meydanlarından biri haline geldi. Bugün Broadway kültürüyle birlikte anılır.",
            "oteller": ["citizenM New York Times Square", "Moxy NYC Times Square", "Riu Plaza Manhattan", "The Knickerbocker", "Tempo by Hilton Times Square"],
        },
        {
            "id": "dubai_burj_khalifa",
            "ad": "Dubai - Burj Khalifa",
            "ulke": "BAE",
            "puan": "9.0",
            "etiket": "Lüks rota",
            "img": "06_dubai_burj_khalifa.png",
            "butce": "Günlük ortalama 450 - 1.000 AED",
            "desc": "Çöl safari, modern mimari, alışveriş ve marina gezileri için popüler durak.",
            "tarihce": "Burj Khalifa, 2010 yılında açıldı ve modern Dubai'nin küresel mimari vitrini oldu. Gökdelen, şehrin çöl ticaret merkezinden turizm ve finans merkezine dönüşümünü simgeler.",
            "oteller": ["Rove Downtown", "Address Downtown", "Palace Downtown", "Sofitel Dubai Downtown", "Taj Dubai"],
        },
        {
            "id": "tokyo_shibuya",
            "ad": "Tokyo - Shibuya",
            "ulke": "Japonya",
            "puan": "9.3",
            "etiket": "Modern şehir",
            "img": "07_tokyo_shibuya.png",
            "butce": "Günlük ortalama 14.000 - 28.000 ¥",
            "desc": "Teknoloji, alışveriş, neon sokaklar ve Japon kültürünü aynı rotada sunar.",
            "tarihce": "Shibuya, Tokyo'nun gençlik kültürü, moda ve eğlence merkezlerinden biridir. Dünyaca bilinen Shibuya Kavşağı, modern şehir hareketliliğinin sembollerinden biri kabul edilir.",
            "oteller": ["Shibuya Stream Excel Hotel Tokyu", "Cerulean Tower Tokyu Hotel", "JR-East Hotel Mets Shibuya", "sequence Miyashita Park", "Tokyu Stay Shibuya"],
        },
        {
            "id": "bali_ubud",
            "ad": "Bali - Ubud / Sahiller",
            "ulke": "Endonezya",
            "puan": "9.4",
            "etiket": "Doğa ve deniz",
            "img": "08_bali_ubud.png",
            "butce": "Günlük ortalama 700.000 - 1.800.000 IDR",
            "desc": "Pirinç terasları, tapınaklar, plajlar ve tropik tatil planları için popüler.",
            "tarihce": "Ubud, Bali'nin sanat, el işi ve geleneksel yaşam merkezlerinden biri olarak tanınır. Ada, tapınakları, pirinç terasları ve sahilleriyle hem kültür hem dinlenme rotası sunar.",
            "oteller": ["Alaya Resort Ubud", "Ubud Village Hotel", "Bisou Ubud", "Adiwana Resort Jembawan", "Komaneka at Rasa Sayang"],
        },
        {
            "id": "cappadocia_balloons",
            "ad": "Kapadokya - Balon Turu",
            "ulke": "Türkiye",
            "puan": "9.1",
            "etiket": "Doğa harikası",
            "img": "09_cappadocia_balloons.png",
            "butce": "Günlük ortalama 2.000 - 7.000 TL",
            "desc": "Peribacaları, yer altı şehirleri ve sıcak hava balonlarıyla fotoğraf odaklı gezi.",
            "tarihce": "Kapadokya, volkanik tüflerin rüzgâr ve yağmurla şekillenmesi sonucu oluşan peribacalarıyla bilinir. Bölge, erken Hristiyanlık dönemine ait kaya kiliseleri ve yer altı şehirleriyle de önemlidir.",
            "oteller": ["Museum Hotel", "Sultan Cave Suites", "Kelebek Special Cave Hotel", "Argos in Cappadocia", "Mithra Cave Hotel"],
        },
        {
            "id": "barcelona_sagrada",
            "ad": "Barselona - Sagrada Familia",
            "ulke": "İspanya",
            "puan": "9.2",
            "etiket": "Mimari rota",
            "img": "10_barcelona_sagrada_familia.png",
            "butce": "Günlük ortalama 90 - 190 €",
            "desc": "Gaudí mimarisi, sahil, tapas kültürü ve renkli şehir yaşamını aynı geziye ekler.",
            "tarihce": "Sagrada Familia, Antoni Gaudí'nin en ünlü eseridir ve 1882'de başlayan inşasıyla hâlâ Barselona'nın en dikkat çekici yapılarından biridir. Organik formlar ve dini semboller mimarinin merkezindedir.",
            "oteller": ["Sercotel Rosellón", "Hotel Barcelona 1882", "Ayre Hotel Rosellón", "Hotel Europark", "H10 Madison"],
        },
        {
            "id": "rio_christ",
            "ad": "Rio - Kurtarıcı İsa Heykeli",
            "ulke": "Brezilya",
            "puan": "9.0",
            "etiket": "Manzara",
            "img": "11_rio_christ_redeemer.png",
            "butce": "Günlük ortalama 350 - 800 BRL",
            "desc": "Corcovado manzarası, sahiller ve canlı şehir kültürüyle Güney Amerika'nın simgelerinden.",
            "tarihce": "Kurtarıcı İsa Heykeli, 1931'de tamamlandı ve Rio de Janeiro'nun en tanınan simgesi oldu. Corcovado Dağı üzerindeki konumu, şehri ve sahilleri geniş açıyla izleme imkânı verir.",
            "oteller": ["Arena Copacabana Hotel", "Miramar by Windsor", "Windsor California", "Prodigy Santos Dumont", "Hotel Fasano Rio"],
        },
        {
            "id": "cairo_pyramids",
            "ad": "Kahire - Giza Piramitleri",
            "ulke": "Mısır",
            "puan": "9.3",
            "etiket": "Antik dünya",
            "img": "12_cairo_pyramids.png",
            "butce": "Günlük ortalama 1.200 - 3.000 EGP",
            "desc": "Antik Mısır mirası, müzeler ve Nil hattıyla tarih meraklıları için güçlü rota.",
            "tarihce": "Giza Piramitleri, Eski Krallık döneminde firavun mezar kompleksleri olarak inşa edildi. Keops Piramidi, Antik Dünyanın Yedi Harikası arasında günümüze ulaşan tek yapıdır.",
            "oteller": ["Marriott Mena House", "Steigenberger Pyramids Cairo", "Pyramids Valley Boutique Hotel", "Hayat Pyramids View", "Le Méridien Pyramids"],
        },
        {
            "id": "athens_acropolis",
            "ad": "Atina - Akropolis",
            "ulke": "Yunanistan",
            "puan": "9.1",
            "etiket": "Antik kültür",
            "img": "13_athens_acropolis.png",
            "butce": "Günlük ortalama 80 - 170 €",
            "desc": "Antik Yunan mirası, müzeler, meydanlar ve Ege atmosferi için klasik bir rota.",
            "tarihce": "Akropolis, Antik Atina'nın dini ve kültürel merkeziydi. Parthenon tapınağıyla birlikte demokrasi, felsefe ve klasik sanat tarihinin en güçlü sembollerinden biri olarak görülür.",
            "oteller": ["A for Athens", "Electra Metropolis", "Herodion Hotel", "Plaka Hotel", "AthensWas Design Hotel"],
        },
        {
            "id": "venice_canals",
            "ad": "Venedik - Kanallar",
            "ulke": "İtalya",
            "puan": "9.0",
            "etiket": "Kanal şehri",
            "img": "14_venice_canals.png",
            "butce": "Günlük ortalama 110 - 230 €",
            "desc": "Gondol rotaları, tarihi meydanlar ve ada atmosferiyle romantik şehir gezisi.",
            "tarihce": "Venedik, lagün üzerine kurulu yapısıyla Orta Çağ ve Rönesans dönemlerinde güçlü bir deniz ticaret merkeziydi. Kanallar, şehrin ulaşım ve günlük yaşam ağının temel parçasıdır.",
            "oteller": ["Hotel Saturnia & International", "Palazzo Veneziano", "Hotel Antiche Figure", "Carnival Palace", "Splendid Venice"],
        },
        {
            "id": "amsterdam_canals",
            "ad": "Amsterdam - Kanallar",
            "ulke": "Hollanda",
            "puan": "8.9",
            "etiket": "Müze ve kanal",
            "img": "15_amsterdam_canals.png",
            "butce": "Günlük ortalama 100 - 210 €",
            "desc": "Kanal turu, bisiklet yolları, müzeler ve şehir yaşamı için popüler Avrupa durağı.",
            "tarihce": "Amsterdam'ın kanal kuşağı, 17. yüzyılda ticaret ve şehir planlamasının parçası olarak gelişti. Bugün UNESCO mirası olan bu alan, şehrin karakterini belirleyen en önemli unsurlardandır.",
            "oteller": ["The Hoxton Amsterdam", "Hotel Estheréa", "INK Hotel Amsterdam", "Park Plaza Victoria", "Monet Garden Hotel"],
        },
        {
            "id": "sydney_opera",
            "ad": "Sidney - Opera Binası",
            "ulke": "Avustralya",
            "puan": "9.0",
            "etiket": "Liman manzarası",
            "img": "16_sydney_opera_house.png",
            "butce": "Günlük ortalama 170 - 320 AUD",
            "desc": "Liman, sahil yürüyüşleri, modern şehir ve ikonik mimariyle Okyanusya rotası.",
            "tarihce": "Sidney Opera Binası, 1973'te açıldı ve modern mimarinin en bilinen yapılarından biri oldu. Liman kıyısındaki kabuk formu, Avustralya'nın kültürel simgelerinden sayılır.",
            "oteller": ["Rydges Sydney Harbour", "Shangri-La Sydney", "Four Seasons Hotel Sydney", "The Grace Hotel", "Sir Stamford at Circular Quay"],
        },
        {
            "id": "singapore_marina",
            "ad": "Singapur - Marina Bay Sands",
            "ulke": "Singapur",
            "puan": "9.2",
            "etiket": "Modern rota",
            "img": "17_singapore_marina_bay.png",
            "butce": "Günlük ortalama 180 - 360 SGD",
            "desc": "Marina, ışık gösterileri, bahçeler ve şehir manzaralarıyla modern Asya rotası.",
            "tarihce": "Marina Bay, Singapur'un modern şehir planlamasının en görünür alanlarından biridir. Marina Bay Sands ve Gardens by the Bay gibi yapılar, şehrin turizm kimliğini güçlendirmiştir.",
            "oteller": ["Marina Bay Sands", "The Fullerton Hotel", "PARKROYAL COLLECTION Marina Bay", "Pan Pacific Singapore", "Hotel Telegraph"],
        },
        {
            "id": "lasvegas_strip",
            "ad": "Las Vegas - Strip",
            "ulke": "ABD",
            "puan": "8.8",
            "etiket": "Eğlence",
            "img": "18_lasvegas_strip.png",
            "butce": "Günlük ortalama 160 - 330 $",
            "desc": "Işıklar, oteller, gösteriler ve gece hayatıyla eğlence odaklı Amerika rotası.",
            "tarihce": "Las Vegas Strip, 20. yüzyıl ortalarından itibaren büyük otel-kumarhane kompleksleriyle gelişti. Bugün gösteri salonları, temalı oteller ve gece hayatıyla tanınır.",
            "oteller": ["Bellagio", "The Venetian Resort", "Paris Las Vegas", "Caesars Palace", "ARIA Resort & Casino"],
        },
        {
            "id": "maldives_beach",
            "ad": "Maldivler - Plajlar",
            "ulke": "Maldivler",
            "puan": "9.4",
            "etiket": "Deniz tatili",
            "img": "19_maldives_beach.png",
            "butce": "Günlük ortalama 250 - 700 $",
            "desc": "Beyaz kum, turkuaz deniz, su üstü villalar ve dinlenme odaklı balayı rotası.",
            "tarihce": "Maldivler, Hint Okyanusu'ndaki atol adalarıyla tanınır. Mercan resifleri, deniz yaşamı ve ada resort kültürü ülkeyi dünyanın en popüler tropik tatil alanlarından biri yapmıştır.",
            "oteller": ["Meeru Maldives Resort", "Kurumba Maldives", "Sun Siyam Iru Fushi", "Kandima Maldives", "Velassaru Maldives"],
        },
        {
            "id": "prague_oldtown",
            "ad": "Prag - Eski Şehir Meydanı",
            "ulke": "Çekya",
            "puan": "9.1",
            "etiket": "Masalsı şehir",
            "img": "20_prague_old_town.png",
            "butce": "Günlük ortalama 2.000 - 4.500 CZK",
            "desc": "Köprüler, meydanlar, kuleler ve uygun bütçeli Avrupa şehir gezisi için popüler.",
            "tarihce": "Prag Eski Şehir Meydanı, Orta Çağ'dan beri kentin ticari ve sosyal merkezlerinden biridir. Astronomik Saat, Týn Kilisesi ve tarihi sokaklar meydanın en bilinen parçalarıdır.",
            "oteller": ["Hotel Rott", "Grand Hotel Bohemia", "Hotel Leon D'Oro", "Mosaic House Design Hotel", "The Emblem Prague Hotel"],
        },
    ]

    POSITIVE = [
        "Manzara ve atmosfer beklediğimden çok daha güzeldi.",
        "Fotoğraf çekmek için harika, kesinlikle tekrar giderim.",
        "Ulaşım kolaydı ve çevrede gezilecek çok yer vardı.",
        "Tarihi dokusu çok etkileyiciydi, iyi ki gitmişim.",
        "Otel ve restoran seçenekleri gayet iyiydi.",
    ]
    NEGATIVE = [
        "Çok kalabalıktı, sakin gezmek zor oldu.",
        "Fiyatlar beklediğimden yüksekti.",
        "Bazı noktalarda sıra beklemek yorucuydu.",
        "Ulaşım yoğun saatlerde biraz zorladı.",
        "Güzel ama daha iyi planlama yapmak gerekiyor.",
    ]

    def __init__(self, master, db, shell, **kwargs):
        self.photos = []
        self.detail_photos = []
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def users(self):
        users = self.db.veri.get("kullanicilar", [])
        if users:
            return users
        names = [
            ("Elif", "Yılmaz"), ("Mehmet", "Demir"), ("Zeynep", "Kaya"), ("Ahmet", "Şahin"),
            ("Ece", "Çelik"), ("Mert", "Aydın"), ("Derya", "Koç"), ("Berk", "Arslan"),
            ("Selin", "Öztürk"), ("Can", "Yıldız"), ("Nehir", "Polat"), ("Emre", "Kılıç"),
            ("İrem", "Aslan"), ("Kerem", "Doğan"), ("Mina", "Aksoy"), ("Deniz", "Kurt"),
            ("Sude", "Eren"), ("Arda", "Güneş"), ("Yağmur", "Taş"), ("Burak", "Uçar"),
            ("Melis", "Bulut"), ("Ozan", "Kaplan"), ("Ceren", "Avcı"), ("Kaan", "Bozkurt")
        ]
        return [{"ad": a, "soyad": s} for a, s in names]



    def visited_users(self, place_index):
        users = self.users()
        if not users:
            return []
        result = []
        start = (place_index * 9) % len(users)
        for i in range(18):
            result.append(users[(start + i * 5) % len(users)])
        return result

    def comments_for(self, place_index):
        place = self.PLACES[place_index]
        visited = self.visited_users(place_index)
        comments = []
        for i, user in enumerate(visited[:10]):
            rating = ((place_index + i * 2) % 5) + 1
            if i % 4 == 0:
                rating = max(1, min(3, rating))
                text = self.NEGATIVE[(place_index + i) % len(self.NEGATIVE)]
            else:
                rating = max(4, rating)
                text = self.POSITIVE[(place_index + i) % len(self.POSITIVE)]
            comments.append((user, rating, text))

        for item in self.saved_comments_for(place.get("id")):
            user = {"ad": item.get("user", self.current_user_display_name()), "soyad": ""}
            comments.insert(0, (user, int(item.get("rating", 5)), item.get("text", "")))
        return comments



    def load_photo(self, filename):
        path = Path(__file__).parent / "popular_images" / filename
        ph = tk.PhotoImage(file=str(path))
        self.photos.append(ph)
        return ph

    def build(self):
        sf = ScrollFrame(self, bg=APP_BG)
        sf.pack(fill="both", expand=True, padx=26, pady=10)
        for i, p in enumerate(self.PLACES):
            card = tk.Frame(sf.inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=i//2, column=i%2, sticky="nsew", padx=10, pady=10)
            sf.inner.columnconfigure(i%2, weight=1)

            try:
                ph = self.load_photo(p["img"])
                tk.Label(card, image=ph, bg=CARD).pack(fill="x", padx=12, pady=(12, 8))
            except Exception:
                canvas = tk.Canvas(card, width=420, height=235, bg="#1F2A34", highlightthickness=0)
                canvas.pack(fill="x", padx=12, pady=(12, 8))
                canvas.create_text(210, 118, text="Fotoğraf", fill=TEXT, font=("Segoe UI", 18, "bold"))

            tk.Label(card, text=p["ad"], bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=14, pady=(2, 2))
            tk.Label(card, text=f"{p['ulke']} • Puan {p['puan']} • {p['etiket']}", bg=CARD, fg=ORANGE, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=2)
            tk.Label(card, text=p["desc"], bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=420, justify="left").pack(anchor="w", padx=14, pady=(4, 10))

            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", padx=14, pady=(0, 14))
            Button(row, "Detayları Aç", command=lambda idx=i: self.open_detail(idx), bg=BLUE).pack(side="left", padx=(0, 8))
            Button(row, "Rotaya Ekle", command=lambda place=p: self.route_from_popular(place), bg=GREEN).pack(side="left")

    def route_from_popular(self, place):
        region = popular_region_from_name(place.get("ad", ""))
        self.shell.show(
            "route_create",
            arrive_country=place.get("ulke", ""),
            arrive_region=region,
            destination_place=place.get("ad", "")
        )

    def current_user_display_name(self):
        try:
            acc = get_account_global(getattr(self.shell, "current_user", ""))
            if acc:
                return f"{acc.get('ad','')} {acc.get('soyad','')}".strip() or acc.get("email", "Kullanıcı")
        except Exception:
            pass
        return "Kullanıcı"

    def user_completed_place(self, place_id):
        for r in self.db.veri.get("seyahatler", []):
            if r.get("durum") == "Tamamlandı" and (r.get("populer_yer_id") == place_id or match_popular_place_id(self.route_place_text(r)) == place_id):
                return True
        return False

    def route_place_text(self, route):
        try:
            if route.get("duraklar"):
                return route["duraklar"][0].get("yerler", "")
        except Exception:
            pass
        return route.get("baslik", "")

    def saved_comments_for(self, place_id):
        data = self.db.veri.setdefault("populer_yorumlar", {})
        return list(data.get(place_id, [])) if isinstance(data, dict) else []

    def star_text(self, n):
        return "★" * int(n) + "☆" * (5 - int(n))

    def weather_for_place(self, place_index):
        icons = ["☀️", "🌤️", "☁️", "🌧️", "⛅"]
        descs = ["Güneşli", "Parçalı bulutlu", "Bulutlu", "Kısa süreli yağmur", "Ilık"]
        base = 16 + ((place_index * 3) % 12)
        today = datetime.now().date()
        temp = base + (place_index % 6)
        return [(TR_DAYS[today.weekday()], icons[place_index % len(icons)], temp, descs[place_index % len(descs)])]



    def open_detail(self, place_index):
        place = self.PLACES[place_index]
        win = tk.Toplevel(self)
        win.title(place["ad"])
        win.geometry("1120x760")
        win.configure(bg=APP_BG)

        header = tk.Frame(win, bg=APP_BG)
        header.pack(fill="x", padx=22, pady=(18, 8))
        tk.Label(header, text=place["ad"], bg=APP_BG, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(header, text=f"{place['ulke']} • {place['etiket']} • Ortalama bütçe: {place['butce']}", bg=APP_BG, fg=ORANGE, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(2, 0))

        body = tk.Frame(win, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = ScrollFrame(body, bg=APP_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        right = ScrollFrame(body, bg=APP_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        photo_card = Card(left.inner, title="Fotoğraf ve Kısa Tarihçe")
        photo_card.pack(fill="x", pady=(0, 10))
        try:
            ph = tk.PhotoImage(file=str(Path(__file__).parent / "popular_images" / place["img"]))
            self.detail_photos.append(ph)
            tk.Label(photo_card, image=ph, bg=CARD).pack(anchor="w", padx=16, pady=(10, 8))
        except Exception:
            tk.Label(photo_card, text="Fotoğraf yüklenemedi.", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=12)

        tk.Label(photo_card, text=place["tarihce"], bg=CARD, fg=TEXT, font=("Segoe UI", 10), wraplength=480, justify="left").pack(anchor="w", padx=16, pady=(4, 14))

        budget = Card(left.inner, title="Ortalama Bütçe")
        budget.pack(fill="x", pady=10)
        tk.Label(budget, text=place["butce"], bg=CARD, fg=GREEN, font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(8, 12))
        tk.Label(budget, text="Bütçe; konaklama, şehir içi ulaşım, yemek ve temel giriş ücretleri düşünülerek yaklaşık verilmiştir.", bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=480, justify="left").pack(anchor="w", padx=16, pady=(0, 14))

        hotels = Card(right.inner, title="En İyi 5 Otel Önerisi")
        hotels.pack(fill="x", pady=(0, 10))
        for i, h in enumerate(place["oteller"], 1):
            tk.Label(hotels, text=f"{i}. {h}", bg=CARD, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=4)

        weather_card = Card(right.inner, title="Bugünün Hava Durumu")
        weather_card.pack(fill="x", pady=(0, 10))
        for day, icon, temp, desc in self.weather_for_place(place_index):
            row = tk.Frame(weather_card, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=14, pady=4)
            tk.Label(row, text=f"{day}", bg=CARD2, fg=TEXT, font=("Segoe UI", 9, "bold"), width=12, anchor="w").pack(side="left", padx=(10, 4), pady=7)
            tk.Label(row, text=icon, bg=CARD2, fg=TEXT, font=("Segoe UI Emoji", 14)).pack(side="left", padx=4)
            tk.Label(row, text=f"{temp}°  {desc}", bg=CARD2, fg=CYAN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=8)

        comments_card = Card(right.inner, title="Daha Önce Gidenlerin Yorumları")
        comments_card.pack(fill="both", expand=True, pady=10)
        tk.Label(comments_card, text="Bazı ziyaretçiler çok beğenmiş, bazıları ise kalabalık ve fiyatlardan dolayı daha düşük puan vermiştir.", bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=480, justify="left").pack(anchor="w", padx=16, pady=(4, 8))

        for user, rating, text in self.comments_for(place_index):
            row = tk.Frame(comments_card, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            row.pack(fill="x", padx=14, pady=5)
            full_name = f"{user.get('ad','')} {user.get('soyad','')}"
            tk.Label(row, text=f"{full_name}  {self.star_text(rating)}", bg=CARD2, fg=YELLOW if rating >= 4 else RED, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(8, 2))
            tk.Label(row, text=text, bg=CARD2, fg=TEXT, font=("Segoe UI", 9), wraplength=450, justify="left").pack(anchor="w", padx=10, pady=(0, 8))

        if self.user_completed_place(place["id"]):
            Button(comments_card, "Yorum Yaz", command=lambda idx=place_index: self.comment_window(idx), bg=GREEN).pack(anchor="w", padx=16, pady=12)
        else:
            tk.Label(comments_card, text="Yorum yazmak için bu popüler yeri rota olarak tamamlamış olmalısın.", bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=480, justify="left").pack(anchor="w", padx=16, pady=12)

    def comment_window(self, place_index):
        place = self.PLACES[place_index]
        if not self.user_completed_place(place["id"]):
            messagebox.showwarning("Yorum", "Bu yere yorum yazmak için önce bu popüler yeri içeren rotayı tamamlamalısın.")
            return

        win = tk.Toplevel(self)
        win.title("Yorum Yaz")
        win.geometry("480x360")
        win.configure(bg=APP_BG)
        win.transient(self.winfo_toplevel())
        win.lift()
        win.focus_force()

        tk.Label(win, text=place["ad"], bg=APP_BG, fg=TEXT, font=("Segoe UI", 17, "bold")).pack(anchor="w", padx=20, pady=(18, 4))
        tk.Label(win, text="Bu popüler yer tamamlanan rotalarında bulunduğu için yorum yazabilirsin.", bg=APP_BG, fg=MUTED, font=("Segoe UI", 9), wraplength=430, justify="left").pack(anchor="w", padx=20, pady=(0, 14))

        rating_var = tk.StringVar(value="5")
        comment_var = tk.StringVar()

        tk.Label(win, text="Kullanıcı", bg=APP_BG, fg=MUTED).pack(anchor="w", padx=20)
        tk.Label(win, text=self.current_user_display_name(), bg=APP_BG, fg=TEXT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(2, 10))

        tk.Label(win, text="Yıldız", bg=APP_BG, fg=MUTED).pack(anchor="w", padx=20)
        ttk.Combobox(win, textvariable=rating_var, values=["1", "2", "3", "4", "5"], state="readonly").pack(fill="x", padx=20, pady=(2, 10))

        tk.Label(win, text="Yorum", bg=APP_BG, fg=MUTED).pack(anchor="w", padx=20)
        tk.Entry(win, textvariable=comment_var, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=20, ipady=8, pady=(2, 16))

        def save():
            text = comment_var.get().strip()
            if not text:
                messagebox.showwarning("Yorum", "Yorum boş olamaz.", parent=win)
                return
            comments = self.db.veri.setdefault("populer_yorumlar", {})
            comments.setdefault(place["id"], []).append({
                "user": self.current_user_display_name(),
                "rating": int(rating_var.get()),
                "text": text,
                "date": today_str()
            })
            self.db.kaydet()
            messagebox.showinfo("Yorum", "Yorum kaydedildi.", parent=win)
            win.destroy()
            self.open_detail(place_index)

        Button(win, "Kaydet", command=save, bg=GREEN).pack(anchor="w", padx=20)




class DashboardPage(BasePage):
    title = "Riftify Ana Panel"
    subtitle = "Rotalarını, bütçeni, rezervasyonlarını ve seyahat hazırlıklarını tek ekranda takip et."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def build(self):
        stat = tk.Frame(self, bg=APP_BG)
        stat.pack(fill="x", padx=26, pady=8)
        values = [
            ("Toplam Rota", len(self.db.veri["seyahatler"]), BLUE),
            ("Planlanan Aktivite", len(self.db.veri["planlar"]), GREEN),
            ("Rezervasyon", len(self.db.veri["rezervasyonlar"]), YELLOW),
            ("Toplam Harcama", f"{int(sum(float(x['tutar']) for x in self.db.veri['butce']))} TL", PURPLE),
        ]
        for title, val, color in values:
            c = Card(stat)
            c.pack(side="left", fill="x", expand=True, padx=6)
            tk.Label(c, text=title, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(12, 0))
            tk.Label(c, text=str(val), bg=CARD, fg=color, font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=14, pady=(2, 12))

        grid = tk.Frame(self, bg=APP_BG)
        grid.pack(fill="both", expand=True, padx=26, pady=8)
        grid.columnconfigure(0, weight=2)
        grid.columnconfigure(1, weight=1)
        grid.rowconfigure(0, weight=1)

        mapcard = Card(grid, title="Rota Haritası")
        mapcard.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        MapCanvas(mapcard, height=310).pack(fill="x", padx=16, pady=12)
        self.route_chips(mapcard)

        side = tk.Frame(grid, bg=APP_BG)
        side.grid(row=0, column=1, sticky="nsew")
        self.countdown_card(side).pack(fill="x", pady=(0, 10))
        self.today_card(side).pack(fill="x", pady=(0, 10))
        self.upcoming_card(side).pack(fill="x", pady=(0, 10))
        self.warning_card(side).pack(fill="both", expand=True)

    def route_chips(self, master):
        row = tk.Frame(master, bg=CARD)
        row.pack(fill="x", padx=14, pady=(0, 14))
        for s in self.db.veri["seyahatler"][:5]:
            mini = tk.Frame(row, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            mini.pack(side="left", fill="x", expand=True, padx=4)
            tk.Label(mini, text="📍", bg=CARD2, fg=RED, font=("Segoe UI Emoji", 16)).pack(pady=(8, 0))
            tk.Label(mini, text=s["baslik"][:18], bg=CARD2, fg=TEXT, font=("Segoe UI", 8, "bold")).pack(pady=(0, 8))


    def countdown_card(self, master):
        c = Card(master, title="En Yakın Seyahat")
        route, left = nearest_route(self.db.veri)
        if route:
            color = GREEN if left > 7 else YELLOW if left >= 0 else MUTED
            text = f"{route.get('baslik')} rotasına {left} gün kaldı" if left >= 0 else f"{route.get('baslik')} tamamlandı/geçmiş tarih"
            tk.Label(c, text=text, bg=CARD, fg=color, font=("Segoe UI", 11, "bold"), wraplength=290, justify="left").pack(anchor="w", padx=16, pady=(10, 3))
            score = readiness_score(self.db, route)
            self.small_progress(c, score, readiness_color(score))
        else:
            tk.Label(c, text="Henüz rota yok.", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=12)
        return c

    def small_progress(self, master, value, color):
        tk.Label(master, text=f"Hazırlık: %{value}", bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16)
        bar = tk.Canvas(master, height=13, bg=CARD2, highlightthickness=0)
        bar.pack(fill="x", padx=16, pady=(4, 12))
        bar.update_idletasks()
        bar.create_rectangle(0, 0, max(6, int(260 * value / 100)), 13, fill=color, outline="")

    def today_card(self, master):
        c = Card(master, title="Bugün Ne Yapılacak?")
        plans = self.db.veri.get("planlar", [])[:3]
        if not plans:
            tk.Label(c, text="Bugün için plan yok.", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=12)
        for p in plans:
            tk.Label(c, text=f"• {p.get('saat','')} {p.get('aktivite','')}", bg=CARD, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=3)
        return c

    def upcoming_card(self, master):
        c = Card(master, title="Yaklaşan Hatırlatıcılar")
        reminders = sorted(self.db.veri["hatirlaticilar"], key=lambda x: x["tarih"])[:4]
        for r in reminders:
            left = days_left(r["tarih"])
            col = RED if left <= 2 else YELLOW if left <= 7 else GREEN
            tk.Label(c, text=f"• {r['baslik']} - {left} gün kaldı", bg=CARD, fg=col, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=4)
        return c

    def warning_card(self, master):
        c = Card(master, title="Bütçe Durumu")
        total_budget = sum(float(s.get("butce", 0)) for s in self.db.veri["seyahatler"])
        expense = sum(float(x["tutar"]) for x in self.db.veri["butce"])
        diff = total_budget - expense
        tk.Label(c, text=f"Toplam seyahat bütçesi: {int(total_budget)} TL", bg=CARD, fg=TEXT, font=("Segoe UI", 10)).pack(anchor="w", padx=16, pady=(12, 3))
        tk.Label(c, text=f"Harcanan: {int(expense)} TL", bg=CARD, fg=YELLOW, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=3)
        if diff < 0:
            tk.Label(c, text=f"Bütçe aşıldı: {abs(int(diff))} TL", bg=CARD, fg=RED, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=5)
        else:
            tk.Label(c, text=f"Kalan bütçe: {int(diff)} TL", bg=CARD, fg=GREEN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=5)
        return c


class RoutesPage(BasePage):
    title = "Rota Keşif ve Planlama"
    subtitle = "Rota oluştur, durak ekle, rota tipi seç, durum ve gezi detaylarını yönet."

    def __init__(self, master, db, shell, **kwargs):
        self.search = tk.StringVar()
        self.type_filter = tk.StringVar(value="Tümü")
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def build(self):
        top = Card(self)
        top.pack(fill="x", padx=26, pady=(4, 12))
        row = tk.Frame(top, bg=CARD)
        row.pack(fill="x", padx=14, pady=14)
        tk.Entry(row, textvariable=self.search, bg="#101826", fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True, ipady=9, padx=(0, 8))
        ttk.Combobox(row, textvariable=self.type_filter, values=["Tümü", "Kültür", "Deniz", "Doğa", "Kamp", "Yurt dışı", "Ekonomik", "Lüks"], width=14, state="readonly").pack(side="left", padx=4)
        Button(row, "Ara / Filtrele", command=self.refresh, bg=BLUE).pack(side="left", padx=4)

        self.area = ScrollFrame(self, bg=APP_BG)
        self.area.pack(fill="both", expand=True, padx=26, pady=(0, 18))
        self.refresh()

    def filtered_routes(self):
        q = self.search.get().lower().strip()
        f = self.type_filter.get()
        routes = self.db.veri["seyahatler"]
        if q:
            routes = [r for r in routes if q in r["baslik"].lower() or q in r["baslangic"].lower() or q in r["bitis"].lower()]
        if f and f != "Tümü":
            routes = [r for r in routes if r.get("tip") == f]
        return routes

    def refresh(self):
        for w in self.area.inner.winfo_children():
            w.destroy()
        routes = self.filtered_routes()
        for idx, r in enumerate(routes):
            self.route_card(self.area.inner, r).grid(row=idx//2, column=idx%2, sticky="nsew", padx=8, pady=8)
            self.area.inner.columnconfigure(idx%2, weight=1)

    def route_popular_place_id(self, route):
        pid = route.get("populer_yer_id")
        if pid:
            return pid
        try:
            if route.get("duraklar"):
                pid = match_popular_place_id(route["duraklar"][0].get("yerler", ""))
                if pid:
                    return pid
        except Exception:
            pass
        return match_popular_place_id(route.get("baslik", ""))

    def complete_route(self, route):
        route["durum"] = "Tamamlandı"
        self.db.kaydet()
        pid = self.route_popular_place_id(route)
        if pid:
            idx, place = popular_place_by_id(pid)
            if place is not None:
                messagebox.showinfo("Rota Tamamlandı", f"{place['ad']} tamamlandı. Şimdi bu popüler yere yorum yazabilirsin.")
                try:
                    self.shell.show("popular")
                    # Sayfa değiştikten sonra yorum penceresini aç.
                    self.after(120, lambda: self.shell.page_area.winfo_children()[0].comment_window(idx))
                except Exception:
                    pass
                return
        messagebox.showinfo("Rota Tamamlandı", "Rota tamamlandı olarak işaretlendi.")
        self.refresh()

    def open_popular_comment_from_route(self, route):
        pid = self.route_popular_place_id(route)
        idx, place = popular_place_by_id(pid)
        if place is None:
            messagebox.showwarning("Yorum", "Bu rota popüler yerlerle eşleşmedi.")
            return
        self.shell.show("popular")
        try:
            self.after(120, lambda: self.shell.page_area.winfo_children()[0].comment_window(idx))
        except Exception:
            pass

    def route_card(self, master, r):
        c = Card(master)
        tk.Label(c, text=self.route_icon(r), bg=CARD, fg=GREEN, font=("Segoe UI Emoji", 32)).pack(anchor="w", padx=16, pady=(12, 0))
        tk.Label(c, text=r["baslik"], bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(2, 4))
        tk.Label(c, text=r["baslangic"] + " → " + r["bitis"], bg=CARD, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=16)
        durum = r.get("durum", "Planlanıyor")
        tk.Label(c, text=f"{r.get('tip','Kültür')} • {durum} • {r['tarih']}", bg=CARD, fg=YELLOW, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=4)
        tk.Label(
            c,
            text=f"Toplam harcama: {int(float(r.get('butce',0)))} TL • Durak: {len(r.get('duraklar', []))}",
            bg=CARD,
            fg=MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", padx=16, pady=(0, 10))
        row = tk.Frame(c, bg=CARD)
        row.pack(fill="x", padx=16, pady=(0, 14))
        Button(row, "Detay", command=lambda: self.shell.show("routes", detay_id=r["seyahat_id"]), bg=BLUE).pack(side="left")
        Button(row, "Özet", command=lambda: messagebox.showinfo("Otomatik Seyahat Özeti", route_summary(self.db, r)), bg=PURPLE).pack(side="left", padx=6)
        Button(row, "TXT Rapor", command=lambda: self.report_route(r["seyahat_id"]), bg=ORANGE).pack(side="left", padx=6)
        if r.get("durum") != "Tamamlandı":
            Button(row, "Tamamla", command=lambda route=r: self.complete_route(route), bg=GREEN).pack(side="right", padx=6)
        elif self.route_popular_place_id(r):
            Button(row, "Yorum Yaz", command=lambda route=r: self.open_popular_comment_from_route(route), bg=GREEN).pack(side="right", padx=6)
        return c



    def report_route(self, sid):
        path = make_route_report(self.db, sid)
        if path:
            messagebox.showinfo("Rapor Oluşturuldu", f"TXT rapor oluşturuldu:\n{path}")
        else:
            messagebox.showwarning("Rapor", "Rapor oluşturulamadı.")

    def route_icon(self, r):
        t = r.get("tip", "")
        if "Deniz" in t: return "🌊"
        if "Doğa" in t: return "⛰"
        if "Kamp" in t: return "⛺"
        if "Yurt" in t: return "✈"
        if "Lüks" in t: return "💎"
        if "Ekonomik" in t: return "🎒"
        return "🏛"

    def new_route_window(self):
        win = tk.Toplevel(self)
        win.title("Yeni Rota")
        win.geometry("430x560")
        win.configure(bg=APP_BG)
        vars = {k: tk.StringVar() for k in ["baslik","baslangic","bitis","tarih","butce","tip","durum"]}
        vars["tarih"].set((datetime.now()+timedelta(days=30)).strftime("%Y-%m-%d"))
        vars["tip"].set("Kültür")
        vars["durum"].set("Planlanıyor")
        tk.Label(win, text="Yeni Rota Oluştur", bg=APP_BG, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(20, 10))
        for lab, key in [("Rota adı","baslik"),("Başlangıç","baslangic"),("Bitiş","bitis"),("Tarih","tarih"),("Bütçe","butce")]:
            tk.Label(win, text=lab, bg=APP_BG, fg=MUTED).pack(anchor="w", padx=22, pady=(8,2))
            tk.Entry(win, textvariable=vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=22, ipady=8)
        for lab,key,vals in [("Rota tipi","tip",["Kültür","Deniz","Doğa","Kamp","Yurt dışı","Ekonomik","Lüks"]),("Durum","durum",["Planlanıyor","Yaklaşıyor","Devam Ediyor","Tamamlandı","İptal Edildi"])]:
            tk.Label(win, text=lab, bg=APP_BG, fg=MUTED).pack(anchor="w", padx=22, pady=(8,2))
            ttk.Combobox(win, textvariable=vars[key], values=vals, state="readonly").pack(fill="x", padx=22)
        def save():
            data = {k:v.get() for k,v in vars.items()}
            if not data["baslik"] or not data["baslangic"] or not data["bitis"]:
                messagebox.showwarning("Eksik", "Rota adı, başlangıç ve bitiş zorunlu.")
                return
            self.db.seyahat_ekle(data)
            win.destroy()
            self.shell.show("routes")
        Button(win, "Kaydet", command=save, bg=GREEN).pack(fill="x", padx=22, pady=20)

    def stop_window(self, sid):
        win = tk.Toplevel(self)
        win.title("Durak Ekle")
        win.geometry("390x430")
        win.configure(bg=APP_BG)
        vars = {k: tk.StringVar() for k in ["sehir","gun","yerler","harcama","not"]}
        tk.Label(win, text="Durak Ekle", bg=APP_BG, fg=TEXT, font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(20, 10))
        for lab,key in [("Şehir","sehir"),("Kaç gün kalınacak","gun"),("Gezilecek yerler","yerler"),("Tahmini harcama","harcama"),("Not","not")]:
            tk.Label(win, text=lab, bg=APP_BG, fg=MUTED).pack(anchor="w", padx=22, pady=(8,2))
            tk.Entry(win, textvariable=vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=22, ipady=8)
        def save():
            self.db.durak_ekle(sid, {k:v.get() for k,v in vars.items()})
            win.destroy()
            self.shell.show("routes")
        Button(win, "Durak Kaydet", command=save, bg=GREEN).pack(fill="x", padx=22, pady=18)

    def pack(self, *args, **kwargs):
        super().pack(*args, **kwargs)
        # route detail after layout
        sid = self.extra.get("detay_id")
        if sid:
            self.after(80, lambda: self.detail_window(sid))

    def detail_window(self, sid):
        r = self.db.get_route(sid)
        if not r:
            return
        win = tk.Toplevel(self)
        win.title("Rota Detayı")
        win.geometry("900x640")
        win.configure(bg=APP_BG)
        tk.Label(win, text=r["baslik"], bg=APP_BG, fg=TEXT, font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=22, pady=(18, 4))
        tk.Label(win, text=f"{r['baslangic']} → {r['bitis']} • {r.get('tip','')} • {r.get('durum','')}", bg=APP_BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", padx=22)
        sf = ScrollFrame(win, bg=APP_BG)
        sf.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        info = Card(sf.inner, title="Rota Bilgileri")
        info.pack(fill="x", pady=8)
        for line in [
            f"Tarih: {r['tarih']}",
            f"Tahmini bütçe: {int(float(r.get('butce',0)))} TL",
            f"Toplam durak: {len(r.get('duraklar', []))}",
            f"Durum: {r.get('durum','Planlanıyor')}",
        ]:
            tk.Label(info, text="• " + line, bg=CARD, fg=TEXT, font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=3)
        stops = Card(sf.inner, title="Duraklar ve Şehir Kartları")
        stops.pack(fill="x", pady=8)
        if not r.get("duraklar"):
            tk.Label(stops, text="Henüz durak eklenmemiş.", bg=CARD, fg=MUTED).pack(anchor="w", padx=18, pady=10)
        for d in r.get("duraklar", []):
            tk.Label(stops, text=f"📍 {d.get('sehir','')} • {d.get('gun','?')} gün • {d.get('harcama','0')} TL", bg=CARD, fg=GREEN, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=(8,2))
            tk.Label(stops, text=f"Gezilecek yerler: {d.get('yerler','-')}", bg=CARD, fg=TEXT, font=("Segoe UI", 9)).pack(anchor="w", padx=36)
            tk.Label(stops, text=f"Not: {d.get('not','-')}", bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=36, pady=(0,6))


class DayPlanPage(BasePage):
    title = "Günlük Program"
    subtitle = "Saat saat aktivite ekle, günlük akışı timeline görünümünde takip et."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.vars = {k: tk.StringVar() for k in ["gun","saat","aktivite","not"]}
        self.vars["gun"].set("1. Gün")
        self.vars["saat"].set("10:00")
        self.build()

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        form = Card(body, title="Aktivite Ekle")
        form.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        for lab,key in [("Gün","gun"),("Saat","saat"),("Aktivite","aktivite"),("Not","not")]:
            tk.Label(form, text=lab, bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(8,2))
            tk.Entry(form, textvariable=self.vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=16, ipady=8)
        Button(form, "Plana Ekle", command=self.add, bg=GREEN).pack(fill="x", padx=16, pady=18)
        tl = Card(body, title="Günlük Akış")
        tl.grid(row=0, column=1, sticky="nsew")
        sf = ScrollFrame(tl, bg=CARD)
        sf.pack(fill="both", expand=True, padx=16, pady=16)
        for p in sorted(self.db.veri["planlar"], key=lambda x: (x["gun"], x["saat"])):
            item = tk.Frame(sf.inner, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            item.pack(fill="x", pady=6)
            tk.Label(item, text=f"{p['gun']} • {p['saat']} • {p['aktivite']}", bg=CARD2, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(8,2))
            tk.Label(item, text=p["not"], bg=CARD2, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(0,8))

    def add(self):
        data = {k:v.get() for k,v in self.vars.items()}
        if not data["aktivite"]:
            messagebox.showwarning("Eksik", "Aktivite yaz.")
            return
        self.db.plan_ekle(data)
        self.shell.show("days")


class BudgetPage(BasePage):
    title = "Bütçe Belirleme"
    subtitle = "Seyahat için toplam bütçeni gir. Rota planlarken bu bütçe aşılırsa uyarı gösterilir."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.limit_var = tk.StringVar(value=str(int(float(self.db.veri.get("ayarlar", {}).get("butce_limiti", 0) or 0))) if self.db.veri.get("ayarlar", {}).get("butce_limiti", 0) else "")
        self.build()

    def spent_total(self):
        total = 0
        try:
            for item in self.db.veri.get("butce", []):
                total += float(item.get("tutar", 0) or 0)
        except Exception:
            pass
        return total

    def budget_limit(self):
        try:
            return float(self.db.veri.get("ayarlar", {}).get("butce_limiti", 0) or 0)
        except Exception:
            return 0

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)

        form = Card(body, title="Toplam Bütçe Gir")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        tk.Label(form, text="Toplam bütçe", bg=CARD, fg=MUTED, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(12, 2))
        tk.Entry(form, textvariable=self.limit_var, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 11, "bold")).pack(fill="x", padx=16, ipady=10)
        tk.Label(form, text="Örnek: 25000", bg=CARD, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=16, pady=(6, 0))
        Button(form, "Bütçeyi Kaydet", command=self.save_budget, bg=GREEN).pack(fill="x", padx=16, pady=18)

        info = Card(body, title="Bütçe Durumu")
        info.grid(row=0, column=1, sticky="nsew")
        self.draw_info(info)

    def draw_info(self, parent):
        limit = self.budget_limit()
        spent = self.spent_total()
        remaining = limit - spent if limit else 0

        tk.Label(parent, text=f"Tanımlı bütçe: {int(limit)} TL" if limit else "Henüz bütçe girilmedi.", bg=CARD, fg=TEXT, font=("Segoe UI", 15, "bold")).pack(anchor="w", padx=16, pady=(14, 8))
        tk.Label(parent, text=f"Planlardan oluşan harcama: {int(spent)} TL", bg=CARD, fg=YELLOW, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=4)

        if limit:
            if remaining < 0:
                msg = f"Bütçeniz {abs(int(remaining))} TL aşılmış. Bütçenizi artırın veya daha ekonomik rota seçin."
                color = RED
            else:
                msg = f"Kalan bütçe: {int(remaining)} TL"
                color = GREEN
            tk.Label(parent, text=msg, bg=CARD, fg=color, font=("Segoe UI", 13, "bold"), wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(10, 12))

            pct = min(100, int((spent / limit) * 100)) if limit else 0
            bar = tk.Canvas(parent, height=22, bg=CARD2, highlightthickness=0)
            bar.pack(fill="x", padx=16, pady=(6, 14))
            bar.update_idletasks()
            w = 520
            bar.create_rectangle(0, 0, w, 22, fill="#1F2A34", outline="")
            bar.create_rectangle(0, 0, int(w * pct / 100), 22, fill=RED if spent > limit else GREEN, outline="")
            bar.create_text(10, 11, text=f"%{pct}", anchor="w", fill=TEXT, font=("Segoe UI", 9, "bold"))

        tk.Label(parent, text="Not: Rota oluştururken seçtiğin otel ve ulaşım maliyeti bu bütçeyle karşılaştırılır.", bg=CARD, fg=MUTED, font=("Segoe UI", 10), wraplength=560, justify="left").pack(anchor="w", padx=16, pady=(8, 14))

    def save_budget(self):
        raw = self.limit_var.get().strip()
        try:
            value = float(raw)
        except Exception:
            messagebox.showwarning("Hata", "Bütçe sayısal olmalı.")
            return
        if value < 0:
            messagebox.showwarning("Hata", "Bütçe negatif olamaz.")
            return
        self.db.veri.setdefault("ayarlar", {})["butce_limiti"] = value
        self.db.kaydet()
        messagebox.showinfo("Bütçe", "Bütçe kaydedildi.")
        self.shell.show("budget")


class ReservationPage(BasePage):
    title = "Rezervasyon Takibi"
    subtitle = "Otel, uçak, restoran, müze ve araç rezervasyonlarını durumlarıyla takip et."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.vars = {k: tk.StringVar() for k in ["tur","ad","tarih","durum"]}
        self.vars["tur"].set("Otel")
        self.vars["tarih"].set((datetime.now()+timedelta(days=20)).strftime("%Y-%m-%d"))
        self.vars["durum"].set("Beklemede")
        self.build()

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        form = Card(body, title="Rezervasyon Ekle")
        form.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        for lab,key in [("Tür","tur"),("Ad","ad"),("Tarih","tarih")]:
            tk.Label(form, text=lab, bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(8,2))
            tk.Entry(form, textvariable=self.vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=16, ipady=8)
        tk.Label(form, text="Durum", bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(8,2))
        ttk.Combobox(form, textvariable=self.vars["durum"], values=["Onaylandı","Beklemede","İptal Edildi","Ödeme Gerekli"], state="readonly").pack(fill="x", padx=16)
        Button(form, "Kaydet", command=self.add, bg=GREEN).pack(fill="x", padx=16, pady=18)

        lst = Card(body, title="Rezervasyonlar")
        lst.grid(row=0, column=1, sticky="nsew")
        sf = ScrollFrame(lst, bg=CARD)
        sf.pack(fill="both", expand=True, padx=16, pady=16)
        for r in self.db.veri["rezervasyonlar"]:
            col = {"Onaylandı":GREEN,"Beklemede":YELLOW,"İptal Edildi":RED,"Ödeme Gerekli":ORANGE}.get(r["durum"], MUTED)
            item = tk.Frame(sf.inner, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            item.pack(fill="x", pady=7)
            tk.Label(item, text=f"{r['tur']} • {r['ad']}", bg=CARD2, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10,2))
            tk.Label(item, text=f"{r['tarih']} • {r['durum']}", bg=CARD2, fg=col, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(0,10))

    def add(self):
        data = {k:v.get() for k,v in self.vars.items()}
        if not data["ad"]:
            messagebox.showwarning("Eksik", "Rezervasyon adını yaz.")
            return
        self.db.rezervasyon_ekle(data)
        self.shell.show("reservations")


class JournalPage(BasePage):
    title = "Yolculuk Günlüğü ve Anılar"
    subtitle = "Anı, konum, duygu, puan ve tavsiye notlarını kaydet."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.vars = {k: tk.StringVar() for k in ["baslik","konum","duygu","puan","foto","metin","tavsiye"]}
        self.vars["duygu"].set("Mutlu")
        self.vars["puan"].set("5")
        self.build()

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        form = Card(body, title="Yeni Anı Ekle")
        form.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        for lab,key in [("Başlık","baslik"),("Konum","konum"),("Duygu","duygu"),("Puan 1-5","puan"),("Fotoğraf notu","foto"),("Metin","metin"),("Tavsiye","tavsiye")]:
            tk.Label(form, text=lab, bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(6,2))
            tk.Entry(form, textvariable=self.vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=16, ipady=7)
        Button(form, "Günlüğe Ekle", command=self.add, bg=GREEN).pack(fill="x", padx=16, pady=16)

        feed = Card(body, title="Anılarım")
        feed.grid(row=0, column=1, sticky="nsew")
        sf = ScrollFrame(feed, bg=CARD)
        sf.pack(fill="both", expand=True, padx=16, pady=16)
        for p in self.db.veri["gunlukler"]:
            item = tk.Frame(sf.inner, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            item.pack(fill="x", pady=7)
            tk.Label(item, text=f"{p['baslik']} • {p.get('konum','')}", bg=CARD2, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(10,2))
            tk.Label(item, text=f"Duygu: {p.get('duygu','-')} • Puan: {p.get('puan','-')}/5 • Foto: {p.get('foto','-')}", bg=CARD2, fg=YELLOW, font=("Segoe UI", 9)).pack(anchor="w", padx=14)
            tk.Label(item, text=p.get("metin",""), bg=CARD2, fg=MUTED, wraplength=620, justify="left").pack(anchor="w", padx=14, pady=3)
            tk.Label(item, text=f"Tavsiye: {p.get('tavsiye','-')}", bg=CARD2, fg=GREEN, wraplength=620, justify="left").pack(anchor="w", padx=14, pady=(0,10))

    def add(self):
        data = {k:v.get() for k,v in self.vars.items()}
        if not data["baslik"]:
            messagebox.showwarning("Eksik", "Başlık yaz.")
            return
        self.db.gunluk_ekle(data)
        self.shell.show("journal")


class SimpleListPage(BasePage):
    list_key = ""
    fields = []
    add_title = ""
    def build_simple(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        self.vars = {key: tk.StringVar() for _, key in self.fields}
        form = Card(body, title=self.add_title)
        form.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        for lab,key in self.fields:
            tk.Label(form, text=lab, bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(8,2))
            tk.Entry(form, textvariable=self.vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=16, ipady=8)
        Button(form, "Ekle", command=self.add_item, bg=GREEN).pack(fill="x", padx=16, pady=18)
        lst = Card(body, title="Liste")
        lst.grid(row=0, column=1, sticky="nsew")
        sf = ScrollFrame(lst, bg=CARD)
        sf.pack(fill="both", expand=True, padx=16, pady=16)
        for item in self.db.veri[self.list_key]:
            self.item_card(sf.inner, item)

    def add_item(self):
        data = {k:v.get() for k,v in self.vars.items()}
        self.db.liste_ekle(self.list_key, data)
        self.shell.show(self.page_key)

    def item_card(self, master, item):
        f = tk.Frame(master, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=6)
        line = " • ".join(str(v) for v in item.values())
        tk.Label(f, text=line, bg=CARD2, fg=TEXT, font=("Segoe UI", 10, "bold"), wraplength=650, justify="left").pack(anchor="w", padx=14, pady=10)


class PackingPage(SimpleListPage):
    title = "Valiz / Eşya Listesi"
    subtitle = "Seyahat öncesi alınacak eşyaları tik mantığıyla takip et."
    page_key = "packing"
    list_key = "valiz"
    add_title = "Eşya Ekle"
    fields = [("Eşya adı","ad"),("Kategori","kategori"),("Durum","durum")]
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build_simple()


class DocumentsPage(SimpleListPage):
    title = "Belge Kasası"
    subtitle = "Pasaport, vize, bilet, otel ve sigorta belgelerini link veya dosya yolu olarak sakla."
    page_key = "documents"
    list_key = "belgeler"
    add_title = "Belge Ekle"
    fields = [("Belge adı","ad"),("Tür","tur"),("Link / Dosya yolu","link")]
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build_simple()
    def item_card(self, master, item):
        f = tk.Frame(master, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=6)
        tk.Label(f, text=f"{item.get('tur','Belge')} • {item.get('ad','')}", bg=CARD2, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(side="left", padx=14, pady=10)
        Button(f, "Aç", command=lambda l=item.get("link",""): webbrowser.open(l) if l else None, bg=BLUE).pack(side="right", padx=10, pady=8)


class EmergencyPage(SimpleListPage):
    title = "Acil Durum Bilgileri"
    subtitle = "Acil kişi, konsolosluk, otel, sigorta ve iletişim bilgilerini sakla."
    page_key = "emergency"
    list_key = "acil"
    add_title = "Acil Bilgi Ekle"
    fields = [("Başlık","baslik"),("Telefon / Bilgi","bilgi"),("Not","not")]
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build_simple()


class CompanionsPage(BasePage):
    title = "Seyahat Arkadaşları ve Görev Paylaşımı"
    subtitle = "Yol arkadaşlarını ekle, kişi rolü ve görevlerini takip et."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.vars = {k: tk.StringVar() for k in ["ad","telefon","rol","gorev"]}
        self.vars["rol"].set("Gezgin")
        self.build()

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        form = Card(body, title="Arkadaş / Görev Ekle")
        form.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        for lab,key in [("Ad Soyad","ad"),("Telefon","telefon"),("Rol","rol"),("Görev","gorev")]:
            tk.Label(form, text=lab, bg=CARD, fg=MUTED).pack(anchor="w", padx=16, pady=(8,2))
            tk.Entry(form, textvariable=self.vars[key], bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat").pack(fill="x", padx=16, ipady=8)
        Button(form, "Ekle", command=self.add, bg=GREEN).pack(fill="x", padx=16, pady=18)
        lst = Card(body, title="Ekip ve Görevler")
        lst.grid(row=0, column=1, sticky="nsew")
        sf = ScrollFrame(lst, bg=CARD)
        sf.pack(fill="both", expand=True, padx=16, pady=16)
        for a in self.db.veri["arkadaslar"]:
            f = tk.Frame(sf.inner, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            f.pack(fill="x", pady=6)
            tk.Label(f, text=f"{a['ad']} • {a['rol']}", bg=CARD2, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10,2))
            tk.Label(f, text=f"Telefon: {a['telefon']} • Görev: {a['gorev']}", bg=CARD2, fg=MUTED).pack(anchor="w", padx=14, pady=(0,10))

    def add(self):
        self.db.liste_ekle("arkadaslar", {k:v.get() for k,v in self.vars.items()})
        self.shell.show("companions")


class ChecklistPage(SimpleListPage):
    title = "Seyahat Checklist"
    subtitle = "Pasaport, vize, otel, bilet, bavul ve döviz gibi hazırlıkları takip et."
    page_key = "checklist"
    list_key = "checklist"
    add_title = "Hazırlık Maddesi Ekle"
    fields = [("Madde","madde"),("Durum","durum")]
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build_simple()


class RemindersPage(SimpleListPage):
    title = "Hatırlatıcılar"
    subtitle = "Uçuşa, otele, müzeye veya rezervasyona kaç gün kaldığını takip et."
    page_key = "reminders"
    list_key = "hatirlaticilar"
    add_title = "Hatırlatıcı Ekle"
    fields = [("Başlık","baslik"),("Tarih YYYY-MM-DD","tarih"),("Not","not")]
    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build_simple()
    def item_card(self, master, item):
        left = days_left(item.get("tarih",""))
        col = RED if left <= 2 else YELLOW if left <= 7 else GREEN
        f = tk.Frame(master, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=6)
        tk.Label(f, text=f"{item.get('baslik','')} • {item.get('tarih','')} • {left} gün kaldı", bg=CARD2, fg=col, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(10,2))
        tk.Label(f, text=item.get("not",""), bg=CARD2, fg=MUTED).pack(anchor="w", padx=14, pady=(0,10))


class ReportsPage(BasePage):
    title = "Seyahat Raporu"
    subtitle = "Toplam seyahat, harcama, en pahalı kategori, yaklaşan rota ve tamamlanan rotaları özetler."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        stats = Card(body, title="Genel Rapor")
        stats.pack(fill="x")
        total_exp = sum(float(x["tutar"]) for x in self.db.veri["butce"])
        totals = {}
        for b in self.db.veri["butce"]:
            totals[b["kategori"]] = totals.get(b["kategori"], 0) + float(b["tutar"])
        maxcat = max(totals, key=totals.get) if totals else "-"
        completed = len([s for s in self.db.veri["seyahatler"] if s.get("durum") == "Tamamlandı"])
        lines = [
            f"Toplam seyahat sayısı: {len(self.db.veri['seyahatler'])}",
            f"Toplam harcama: {int(total_exp)} TL",
            f"En pahalı kategori: {maxcat}",
            f"Tamamlanan rota: {completed}",
            f"Yaklaşan hatırlatıcı: {len(self.db.veri['hatirlaticilar'])}",
            f"Toplam rezervasyon: {len(self.db.veri['rezervasyonlar'])}",
            f"Toplam günlük paylaşımı: {len(self.db.veri['gunlukler'])}",
        ]
        for l in lines:
            tk.Label(stats, text="• " + l, bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=5)

        archive = Card(body, title="Rota Durumları")
        archive.pack(fill="both", expand=True, pady=12)
        sf = ScrollFrame(archive, bg=CARD)
        sf.pack(fill="both", expand=True, padx=16, pady=16)
        for r in self.db.veri["seyahatler"]:
            col = {"Planlanıyor":YELLOW,"Yaklaşıyor":CYAN,"Devam Ediyor":GREEN,"Tamamlandı":PURPLE,"İptal Edildi":RED}.get(r.get("durum"), MUTED)
            tk.Label(sf.inner, text=f"{r['baslik']} • {r.get('durum','Planlanıyor')} • {r['tarih']}", bg=CARD, fg=col, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=4)







class WorldMapPage(tk.Frame):
    """Harita odaklı, daha gösterişli dünya haritası sayfası."""
    title = "İnteraktif Dünya Haritası"
    subtitle = "Tüm ülke sınırlarını keşfet, ülkeye odaklan ve il/eyalet/bölge sınırlarını görüntüle."

    COUNTRY_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    ADMIN1_URL = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson"

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, bg=APP_BG)
        self.db = db
        self.shell = shell
        self.extra = kwargs
        self.data_dir = Path(__file__).with_name("harita_verileri")
        self.data_dir.mkdir(exist_ok=True)
        self.country_file = self.data_dir / "ulkeler_sinirlari.geojson"
        self.admin1_file = self.data_dir / "idari_bolgeler_adm1.geojson"
        self.subdiv_file = self.data_dir / "idari_bolgeler_liste.json"
        self.countries = None
        self.admin1 = None
        self.subdivisions = {}
        self.selected_country = None
        self.selected_mode = 'world'
        self.country_items = {}
        self.drag_start = None
        self.drag_moved = False
        self.scale = 5.20
        self.min_scale = 5.20
        self.max_scale = 80.0
        self.offset_x = 500
        self.offset_y = 280
        self.admin1_cache = {}
        self.region_panel_key = None
        self.current_region_records = []
        self.selected_region_name = None
        self.selected_region_idx = None
        self.region_info_card = None
        self.map_region_info_card = None
        self.map_region_info_window = None
        self.build()

    def build(self):
        self.main = tk.Frame(self, bg=APP_BG)
        self.main.pack(fill="both", expand=True, padx=20, pady=18)
        self.main.columnconfigure(0, weight=1)
        self.main.columnconfigure(1, weight=0, minsize=230)
        self.main.rowconfigure(0, weight=1)

        self.map_wrap = tk.Frame(self.main, bg="#050B14", highlightbackground="#1E3A5A", highlightthickness=1, bd=0)
        self.map_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.map_wrap.rowconfigure(1, weight=1)
        self.map_wrap.columnconfigure(0, weight=1)

        head = tk.Frame(self.map_wrap, bg="#08111F")
        head.grid(row=0, column=0, sticky="ew")
        tk.Label(head, text="🌍 Dünya Keşif Haritası", bg="#08111F", fg=TEXT, font=("Segoe UI", 22, "bold")).pack(side="left", padx=18, pady=(14, 10))
        self.status = tk.Label(head, text="", bg="#08111F", fg=GREEN, font=("Segoe UI", 9, "bold"))

        self.canvas = tk.Canvas(self.map_wrap, bg="#06101E", highlightthickness=0, bd=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self.on_wheel_linux(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self.on_wheel_linux(e, -1))
        self.canvas.bind("<Configure>", lambda e: self.draw())

        # Kontrol paneli sadeleştirildi: +, -, Dünya ve indirme butonları kaldırıldı.
        self.hint_badge = tk.Label(self.canvas, text="Ülke seçilmedi", bg="#0B1828", fg=TEXT, font=("Segoe UI", 10, "bold"), padx=14, pady=7)
        self.hint_window = self.canvas.create_window(18, 18, window=self.hint_badge, anchor="nw")

        self.side = tk.Frame(self.main, bg="#0B1626", highlightbackground="#1E3A5A", highlightthickness=1, width=230)
        self.side.grid(row=0, column=1, sticky="ns")
        self.side.grid_propagate(False)
        self.side.pack_propagate(False)
        tk.Label(self.side, text="Seçim", bg="#0B1626", fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=12, pady=(14, 2))
        tk.Label(self.side, text="Ülkeye tıklayınca o ülkenin bölge haritası açılır.", bg="#0B1626", fg=MUTED, font=("Segoe UI", 8), wraplength=190, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        self.stat_country = self.stat_card("Seçilen", "Yok", CYAN)
        self.stat_country.pack(fill="x", padx=10, pady=4)
        self.stat_regions = self.stat_card("Bölge sayısı", "0", GREEN)
        self.stat_regions.pack(fill="x", padx=10, pady=4)
        tk.Label(self.side, text="Bölgeler", bg="#0B1626", fg=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.region_list = ScrollFrame(self.side, bg="#0B1626")
        self.region_list.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        self.load_if_exists()
        self.draw()

    def stat_card(self, title, value, color):
        f = tk.Frame(self.side, bg="#101E31", highlightbackground="#253B56", highlightthickness=1)
        tk.Label(f, text=title, bg="#101E31", fg=MUTED, font=("Segoe UI", 7, "bold")).pack(anchor="w", padx=9, pady=(6, 0))
        lbl = tk.Label(f, text=value, bg="#101E31", fg=color, font=("Segoe UI", 11, "bold"), wraplength=185, justify="left")
        lbl.pack(anchor="w", padx=9, pady=(0, 6))
        f.value_label = lbl
        return f

    def ensure_data(self):
        try:
            if not self.country_file.exists():
                self.status.configure(text="Ülke sınırları indiriliyor...")
                self.update_idletasks()
                urllib.request.urlretrieve(self.COUNTRY_URL, self.country_file)
            if not self.admin1_file.exists():
                self.status.configure(text="İdari bölgeler indiriliyor... Büyük dosya olabilir.")
                self.update_idletasks()
                urllib.request.urlretrieve(self.ADMIN1_URL, self.admin1_file)
            self.status.configure(text="Harita verileri hazır")
            self.load_if_exists(force=True)
            self.draw()
            messagebox.showinfo("Harita verisi hazır", "Ülke sınırları ve ADM1 il/eyalet/bölge verisi indirildi.")
        except Exception as e:
            self.status.configure(text="İndirme başarısız")
            messagebox.showerror("Harita verisi indirilemedi", "İlk indirme için internet gerekir." + chr(10) + chr(10) + "Hata: " + str(e))

    def load_if_exists(self, force=False):
        try:
            if (self.countries is None or force) and self.country_file.exists():
                self.countries = json.loads(self.country_file.read_text(encoding="utf-8"))
            if (self.admin1 is None or force) and self.admin1_file.exists():
                self.admin1 = json.loads(self.admin1_file.read_text(encoding="utf-8"))
            if (not self.subdivisions or force) and self.subdiv_file.exists():
                self.subdivisions = json.loads(self.subdiv_file.read_text(encoding="utf-8"))
            if self.countries:
                self.status.configure(text=str(len(self.countries.get("features", []))) + " ülke hazır")
        except Exception as e:
            messagebox.showerror("Veri okuma hatası", str(e))

    def ensure_admin1_loaded(self):
        """Tüm ülkelerin gerçek il/eyalet/bölge sınırlarını yükler.
        Dosya yoksa ilk seçimde otomatik indirir ve sonra harita_verileri klasöründe saklar.
        """
        if self.admin1:
            return True
        try:
            if not self.admin1_file.exists():
                self.hint_badge.configure(text="Gerçek il/eyalet sınırları indiriliyor...")
                self.update_idletasks()
                urllib.request.urlretrieve(self.ADMIN1_URL, self.admin1_file)
            self.admin1 = json.loads(self.admin1_file.read_text(encoding="utf-8"))
            return True
        except Exception as e:
            self.hint_badge.configure(text="Gerçek sınır verisi indirilemedi")
            messagebox.showerror(
                "Gerçek il/eyalet sınırları indirilemedi",
                "Bu ülkenin gerçek iç sınırlarını çizmek için ilk seferde internet gerekir.\n\n"
                "Dosya indikten sonra tekrar indirme gerekmez.\n\n"
                f"Hata: {e}"
            )
            return False

    def props(self, feature):
        return {str(k).lower(): v for k, v in feature.get("properties", {}).items()}
    def get_country_name(self, feature):
        p = self.props(feature)
        return p.get("name_tr") or p.get("name") or p.get("admin") or p.get("sovereignt") or "Bilinmeyen Ülke"
    def get_country_code(self, feature):
        p = self.props(feature)
        return p.get("adm0_a3") or p.get("iso_a3") or p.get("sov_a3") or p.get("gu_a3") or p.get("iso_a2") or ""

    def get_country_iso2(self, feature):
        p = self.props(feature)
        code = p.get("iso_a2") or p.get("wb_a2") or p.get("postal") or ""
        return code if code and len(str(code)) == 2 else ""

    def get_country_label(self, feature):
        name = self.get_country_name(feature)
        if not name:
            return ""
        if len(name) > 12:
            return name[:10] + "…"
        return name

    def feature_center(self, feature):
        minx, miny, maxx, maxy = self.feature_bbox(feature)
        return (minx + maxx) / 2, (miny + maxy) / 2
    def get_admin_country_code(self, feature):
        p = self.props(feature)
        code = (
            p.get("adm0_a3")
            or p.get("adm0_a3_us")
            or p.get("adm0_a3_un")
            or p.get("gu_a3")
            or p.get("sov_a3")
            or p.get("iso_a3")
            or p.get("iso_a2")
            or ""
        )
        return str(code).upper()

    def get_admin_country_name(self, feature):
        p = self.props(feature)
        return (
            p.get("admin")
            or p.get("geonunit")
            or p.get("adm0_name")
            or p.get("sovereignt")
            or p.get("name")
            or p.get("name_en")
            or ""
        )

    def same_country_for_admin1(self, country_code, country_name, admin_feature):
        p = self.props(admin_feature)
        acode = self.get_admin_country_code(admin_feature)
        code = str(country_code or "").upper()
        if code and acode and acode == code:
            return True

        def norm(v):
            return str(v or "").translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")).lower().strip()

        target = norm(country_name)
        aliases = {
            "united kingdom": {"united kingdom", "england", "scotland", "wales", "northern ireland", "great britain", "britain"},
            "france": {"france", "metropolitan france", "french republic"},
            "turkey": {"turkey", "turkiye", "türkiye"},
            "united states of america": {"united states of america", "united states", "usa"},
        }
        possible = {
            norm(p.get("admin")),
            norm(p.get("geonunit")),
            norm(p.get("adm0_name")),
            norm(p.get("sovereignt")),
            norm(p.get("name")),
            norm(p.get("name_en")),
        }
        if target and target in possible:
            return True
        if target in aliases and possible.intersection(aliases[target]):
            return True
        return False
    def get_region_name(self, feature):
        p = self.props(feature)
        return p.get("name_tr") or p.get("name") or p.get("name_en") or p.get("region") or p.get("gn_name") or "Bölge"

    def geom_rings(self, geom):
        if not geom:
            return []
        gtype = geom.get("type")
        coords = geom.get("coordinates", [])
        rings = []
        if gtype == "Polygon":
            rings.extend(coords[:1])
        elif gtype == "MultiPolygon":
            for poly in coords:
                if poly:
                    rings.append(poly[0])
        return rings

    def project(self, lon, lat):
        return lon * self.scale + self.offset_x, -lat * self.scale + self.offset_y

    def draw_ocean(self):
        w = self.canvas.winfo_width() or 900
        h = self.canvas.winfo_height() or 560
        self.canvas.create_rectangle(0, 0, w, h, fill="#06101E", outline="")
        for i, col in enumerate(["#071B2D", "#08213A", "#0A2947", "#0B3154"]):
            self.canvas.create_oval(-w*0.35 + i*60, -h*0.45 + i*36, w*1.25 - i*50, h*1.50 - i*24, outline=col, width=2)
        for lon in range(-180, 181, 30):
            pts=[]
            for lat in range(-80, 81, 8):
                x,y=self.project(lon,lat); pts.extend([x,y])
            self.canvas.create_line(pts, fill="#11324A", width=1, smooth=True)
        for lat in range(-60, 61, 20):
            pts=[]
            for lon in range(-180, 181, 8):
                x,y=self.project(lon,lat); pts.extend([x,y])
            self.canvas.create_line(pts, fill="#11324A", width=1, smooth=True)

    def draw(self):
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        self.country_items.clear()
        self.draw_ocean()
        self.hint_window = self.canvas.create_window(18, 18, window=self.hint_badge, anchor="nw")
        # Zoom yazısı kaldırıldı.
        if not self.countries:
            self.canvas.create_text(36, 128, anchor="nw", text="Harita verisi henüz yok." + chr(10) + "Veriyi indir butonuna basınca tüm ülke sınırları gelir.", fill=TEXT, font=("Segoe UI", 15, "bold"))
            self.canvas.create_text((self.canvas.winfo_width() or 900)/2, (self.canvas.winfo_height() or 560)/2, text="🌍", font=("Segoe UI Emoji", 88))
            return
        features = self.countries.get("features", [])
        if self.selected_country:
            # Ülke seçildikten sonra dünya arka planda kalsın, seçili ülke ve bölgeler öne çıksın.
            for idx, f in enumerate(features):
                tag = f"country_{idx}"
                if f is self.selected_country:
                    continue
                items = self.draw_feature(f, fill="#132034", outline="#1F3448", width=1, tag=tag, sample=2)
                for item_id in items:
                    self.canvas.tag_bind(item_id, "<Button-1>", lambda e, i=idx: self.select_country(i))
            self.draw_feature(self.selected_country, fill="#1B6B78", outline="#87F7FF", width=3, tag="selected_country", sample=1)
            self.draw_admin1_for_selected()
            if self.selected_region_name:
                self.show_region_info_card(self.selected_region_name)
        else:
            for idx, f in enumerate(features):
                item_ids = self.draw_feature(f, fill="#1F475A", outline="#5B8BA4", width=1, tag=f"country_{idx}", sample=1)
                for item_id in item_ids:
                    self.country_items[item_id] = idx
                    self.canvas.tag_bind(item_id, "<Button-1>", lambda e, i=idx: self.select_country(i))
                    self.canvas.tag_bind(item_id, "<Enter>", lambda e, item=item_id: self.canvas.itemconfigure(item, fill="#2B8A9E", outline="#A8FFFF"))
                    self.canvas.tag_bind(item_id, "<Leave>", lambda e, item=item_id: self.canvas.itemconfigure(item, fill="#1F475A", outline="#5B8BA4"))
            for f in features:
                self.draw_country_name(f)



    def draw_country_name(self, feature):
        label = self.get_country_label(feature)
        if not label:
            return
        minx, miny, maxx, maxy = self.feature_bbox(feature)
        # Çok küçük ülkelerde isim yazıları birbirine girmesin.
        if (maxx - minx) * self.scale < 22 or (maxy - miny) * self.scale < 12:
            return
        lon, lat = self.feature_center(feature)
        x, y = self.project(lon, lat)
        size = 8 if self.scale < 8 else 9
        self.canvas.create_text(
            x, y,
            text=label,
            fill="#06101E",
            font=("Segoe UI", size, "bold"),
            tags=("country_name",)
        )

    def generated_region_shapes(self, feature, names):
        """Gerçek ADM1 polygon dosyası yoksa bölge isimlerini ülkenin bbox'ında harita gibi yerleştirir.
        Bu gerçek sınır yerine görsel/etkileşimli bölge görünümüdür.
        """
        if not names:
            return []
        minx, miny, maxx, maxy = self.feature_bbox(feature)
        dx = max(1, maxx - minx)
        dy = max(1, maxy - miny)
        n = len(names)

        cols = max(2, min(6, int(n ** 0.5) + 1))
        rows = max(1, (n + cols - 1) // cols)

        shapes = []
        pad_x = dx * 0.05
        pad_y = dy * 0.05
        usable_x = max(0.1, dx - 2 * pad_x)
        usable_y = max(0.1, dy - 2 * pad_y)
        cell_w = usable_x / cols
        cell_h = usable_y / rows

        for i, name in enumerate(names):
            r = i // cols
            c = i % cols
            x1 = minx + pad_x + c * cell_w
            y1 = miny + pad_y + r * cell_h
            x2 = x1 + cell_w * 0.92
            y2 = y1 + cell_h * 0.82

            # Satır/sütuna göre hafif kaydırma, yapay da olsa organik dursun.
            wig = ((i * 37) % 9 - 4) / 100
            x1 += dx * wig * 0.12
            x2 += dx * wig * 0.12

            poly = [
                (x1, y1),
                (x2, y1 + cell_h * 0.08),
                (x2 - cell_w * 0.08, y2),
                (x1 + cell_w * 0.05, y2 - cell_h * 0.05),
            ]
            shapes.append((name, poly))
        return shapes

    def draw_generated_regions(self, feature, names):
        shapes = self.generated_region_shapes(feature, names)
        colors = ["#1F6F8B", "#1B7A63", "#7056B8", "#A36A1D", "#8B3A5B", "#4F6FA8"]
        for i, (name, poly) in enumerate(shapes):
            pts = []
            for lon, lat in poly:
                x, y = self.project(lon, lat)
                pts.extend([x, y])
            item = self.canvas.create_polygon(
                pts,
                fill=colors[i % len(colors)],
                outline="#B4FFD8",
                width=1,
                tags=("generated_region",)
            )
            cx = sum(p[0] for p in poly) / len(poly)
            cy = sum(p[1] for p in poly) / len(poly)
            x, y = self.project(cx, cy)
            short = name
            if len(short) > 16:
                short = short[:14] + "…"
            self.canvas.create_text(
                x, y,
                text=short,
                fill="#EAFBFF",
                font=("Segoe UI", 7, "bold"),
                width=90,
                tags=("generated_region_label",)
            )


    def draw_feature(self, feature, fill, outline, width=1, tag=None, sample=1):
        item_ids = []
        for ring in self.geom_rings(feature.get("geometry")):
            if len(ring) < 3:
                continue
            pts = []
            for pair in ring[::max(1, sample)]:
                try:
                    x, y = self.project(pair[0], pair[1])
                    pts.extend([x, y])
                except Exception:
                    pass
            if len(pts) >= 6:
                item_ids.append(self.canvas.create_polygon(pts, fill=fill, outline=outline, width=width, tags=(tag or "")))
        return item_ids

    def draw_admin1_for_selected(self):
        country_code = self.get_country_code(self.selected_country)
        country_name = self.get_country_name(self.selected_country)
        cache_key = country_code or country_name

        # Artık yapay kutu/şerit yok: gerçek ADM1 polygon verisi zorunlu.
        if not self.ensure_admin1_loaded():
            if self.region_panel_key != cache_key:
                self.update_region_panel([], names=[])
                self.region_panel_key = cache_key
            return

        if cache_key in self.admin1_cache:
            regions = self.admin1_cache[cache_key]
        else:
            regions = []
            for f in self.admin1.get("features", []):
                if self.same_country_for_admin1(country_code, country_name, f):
                    regions.append(f)

            self.admin1_cache[cache_key] = regions

        colors = [
            "#2B8A9E", "#2E7D63", "#7C5CB8", "#C07A25", "#B34B6D",
            "#4E80C4", "#36A37D", "#D18F2C", "#8B65D8", "#C75D5D",
            "#3A96A8", "#6F9D3A", "#9A6A2A", "#5E78B8"
        ]

        self.current_region_records = regions
        for idx, f in enumerate(regions):
            ids = self.draw_feature(
                f,
                fill=colors[idx % len(colors)],
                outline="#D9FFF3",
                width=1,
                tag=f"region_{idx}",
                sample=1
            )
            for item_id in ids:
                self.canvas.tag_bind(item_id, "<Button-1>", lambda e, i=idx: self.select_region_by_index(i))
                self.canvas.tag_bind(item_id, "<ButtonRelease-1>", lambda e, i=idx: self.select_region_by_index(i))
            try:
                minx, miny, maxx, maxy = self.feature_bbox(f)
                # Çok küçük bölgelerde yazı yazma; yoksa karmaşa olur.
                if (maxx - minx) * self.scale > 34 and (maxy - miny) * self.scale > 14:
                    lon, lat = self.feature_center(f)
                    x, y = self.project(lon, lat)
                    nm = self.get_region_name(f)
                    if len(nm) > 15:
                        nm = nm[:13] + "…"
                    self.canvas.create_text(
                        x, y,
                        text=nm,
                        fill="#F5FFFF",
                        font=("Segoe UI", 7, "bold"),
                        width=90
                    )
            except Exception:
                pass

        if self.region_panel_key != cache_key:
            self.update_region_panel(regions)
            self.region_panel_key = cache_key


    def get_subdivision_names(self, country_code):
        info = self.subdivisions.get(country_code or "", {}) if isinstance(self.subdivisions, dict) else {}
        return info.get("bolgeler", []) if isinstance(info, dict) else []

    def update_region_panel(self, regions, names=None):
        for w in self.region_list.inner.winfo_children():
            w.destroy()
        cname = self.get_country_name(self.selected_country) if self.selected_country else "Yok"
        self.stat_country.value_label.configure(text=cname)
        names = names if names is not None else sorted(set(self.get_region_name(r) for r in regions))
        self.current_region_records = list(regions or [])
        self.stat_regions.value_label.configure(text=str(len(names) if names else len(regions)))
        self.hint_badge.configure(text=f"Seçili ülke: {cname}" if self.selected_country else "Ülke seçilmedi")

        if not names:
            tk.Label(
                self.region_list.inner,
                text="Gerçek il/eyalet/bölge sınırı bulunamadı veya veri indirilemedi.",
                bg="#0B1626",
                fg=YELLOW,
                font=("Segoe UI", 8, "bold"),
                wraplength=190,
                justify="left"
            ).pack(anchor="w", padx=8, pady=8)
            return

        tk.Label(
            self.region_list.inner,
            text="İl / eyalet / bölge seç",
            bg="#0B1626",
            fg=GREEN,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", padx=8, pady=(4, 4))

        for idx, name in enumerate(names):
            row = tk.Label(
                self.region_list.inner,
                text=f"⚑ {name}",
                anchor="w",
                bg="#101E31",
                fg=TEXT,
                font=("Segoe UI", 8, "bold"),
                padx=8,
                pady=6,
                cursor="hand2"
            )
            row.pack(fill="x", padx=3, pady=2)
            row.bind("<Enter>", lambda e, w=row: w.configure(bg="#1E3248"))
            row.bind("<Leave>", lambda e, w=row: w.configure(bg="#101E31"))
            row.bind("<Button-1>", lambda e, n=name, i=idx: self.select_region_by_name(n, i))

        # Daha önce seçilmiş bölge varsa panel yenilenince kartı tekrar göster.
        if self.selected_region_name and self.selected_region_name in names:
            self.show_region_info_card(self.selected_region_name)



    def stable_number(self, text, low, high):
        if high <= low:
            return low
        return low + (abs(hash(str(text))) % (high - low + 1))

    def region_info_data(self, region_name):
        cname = self.get_country_name(self.selected_country) if self.selected_country else "Ülke"
        seed = f"{cname}-{region_name}"
        population = self.stable_number(seed + "population", 120, 15700)
        if population >= 1000:
            pop_text = f"{population/1000:.1f} milyon".replace(".", ",")
        else:
            pop_text = f"{population} bin"
        postal = str(self.stable_number(seed + "postal", 10, 98)) + "XXX"
        area_code = "+" + str(self.stable_number(seed + "area", 100, 999))
        low_point = self.stable_number(seed + "low", 0, 950)
        hdi = self.stable_number(seed + "hdi", 610, 910) / 1000
        zones = [
            "Merkez Bölgesi, Tarihi Bölge, Sahil Bölgesi",
            "Yeni Yerleşim, Sanayi Bölgesi, Üniversite Bölgesi",
            "Kuzey Bölgesi, Güney Bölgesi, Kent Merkezi",
            "Doğa Bölgesi, Eski Şehir, Pazar Alanı",
            "Kültür Caddesi, Meydan Bölgesi, Turizm Alanı",
        ]
        return [
            ("Nüfus", pop_text),
            ("Mahalleler", zones[self.stable_number(seed + "zone", 0, len(zones)-1)]),
            ("Posta kodu", postal),
            ("İl / Bölge", region_name),
            ("Ülke", cname),
            ("Alan kodu", area_code),
            ("En alçak nokta", f"{low_point} m"),
            ("İGE", f"{hdi:.3f}".replace(".", ",")),
        ]

    def clear_region_info_card(self):
        try:
            if self.map_region_info_window:
                self.canvas.delete(self.map_region_info_window)
        except Exception:
            pass
        try:
            if self.map_region_info_card and self.map_region_info_card.winfo_exists():
                self.map_region_info_card.destroy()
        except Exception:
            pass
        try:
            if self.region_info_card and self.region_info_card.winfo_exists():
                self.region_info_card.destroy()
        except Exception:
            pass
        self.map_region_info_window = None
        self.map_region_info_card = None
        self.region_info_card = None

    def show_region_info_card(self, region_name):
        # Bilgi kartı artık haritanın sol üst tarafında görünür; sağdaki il listesi bozulmaz.
        self.clear_region_info_card()
        if not hasattr(self, "canvas") or not self.canvas.winfo_exists():
            return

        cname = self.get_country_name(self.selected_country) if self.selected_country else "Ülke"
        card = tk.Frame(
            self.canvas,
            bg="#111B2B",
            highlightbackground="#38BDF8",
            highlightthickness=1
        )
        self.map_region_info_card = card
        self.region_info_card = card

        tk.Label(
            card,
            text=f"{region_name}",
            bg="#111B2B",
            fg=TEXT,
            font=("Segoe UI", 12, "bold"),
            wraplength=220,
            justify="left"
        ).pack(anchor="w", padx=10, pady=(10, 6))

        for key, value in self.region_info_data(region_name):
            row = tk.Frame(card, bg="#263142")
            row.pack(fill="x", padx=8, pady=1)
            tk.Label(
                row,
                text=key,
                bg="#263142",
                fg=MUTED,
                font=("Segoe UI", 8),
                width=12,
                anchor="w"
            ).pack(side="left", padx=(6, 4), pady=5)
            tk.Label(
                row,
                text=value,
                bg="#263142",
                fg=TEXT,
                font=("Segoe UI", 8, "bold"),
                wraplength=110,
                justify="left"
            ).pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)

        Button(
            card,
            "Turistik Yerler",
            command=lambda r=region_name, c=cname: self.open_region_tourism_places(c, r),
            bg=ORANGE
        ).pack(fill="x", padx=8, pady=(10, 10))

        # Hemen sol tarafta dursun; başlık/hint ile çakışmasın diye biraz aşağı aldım.
        self.map_region_info_window = self.canvas.create_window(
            18,
            58,
            window=card,
            anchor="nw"
        )
        try:
            card.lift()
        except Exception:
            pass


    def select_region_by_index(self, idx):
        try:
            if self.current_region_records and 0 <= idx < len(self.current_region_records):
                name = self.get_region_name(self.current_region_records[idx])
            else:
                name = f"Bölge {idx + 1}"
            self.select_region_by_name(name, idx)
        except Exception as e:
            messagebox.showerror("Bölge seçilemedi", str(e))

    def select_region_by_name(self, name, idx=None):
        self.selected_region_name = name
        self.selected_region_idx = idx
        self.hint_badge.configure(text=f"Seçili bölge: {name}")
        self.show_region_info_card(name)
        try:
            for item in self.canvas.find_withtag("region_selected_outline"):
                self.canvas.delete(item)
            if idx is not None:
                for item in self.canvas.find_withtag(f"region_{idx}"):
                    coords = self.canvas.coords(item)
                    if len(coords) >= 6:
                        self.canvas.create_line(
                            coords + coords[:2],
                            fill=YELLOW,
                            width=3,
                            tags=("region_selected_outline",)
                        )
        except Exception:
            pass

    def tourist_places_for_region(self, country, region):
        categories = [
            ("Tarihi Merkez", "Tarihi merkez", "Bölgenin eski sokakları, meydanları ve kültürel dokusu."),
            ("Kent Müzesi", "Müze", "Bölgenin tarihini ve yerel yaşamını tanıtan müze rotası."),
            ("Seyir Tepesi", "Manzara", "Şehir fotoğrafları ve gün batımı için önerilen nokta."),
            ("Yerel Pazar", "Yerel deneyim", "Yöresel ürünler, sokak lezzetleri ve alışveriş için ideal."),
            ("Doğa Parkı", "Doğa", "Yürüyüş, piknik ve açık hava planı için uygun rota."),
            ("Ana Meydan", "Meydan", "Şehir atmosferini hızlıca hissetmek için merkezi durak."),
            ("Kültür Caddesi", "Kültür", "Kafe, galeri, mağaza ve şehir yaşamını bir arada gör."),
            ("Fotoğraf Rotası", "Fotoğraf", "Sosyal medya ve anı fotoğrafları için seçilmiş rota."),
            ("Lezzet Durağı", "Yeme içme", "Yerel yemekleri denemek için önerilen bölge."),
            ("Tarihi Yapı", "Mimari", "Bölgenin öne çıkan mimari ve tarih noktası."),
        ]
        items = []
        for i, (suffix, cat, desc) in enumerate(categories, 1):
            score = self.stable_number(f"{country}-{region}-{suffix}", 78, 99) / 10
            items.append({
                "ad": f"{region} {suffix}",
                "kategori": cat,
                "puan": f"{score:.1f}",
                "aciklama": desc,
                "tarihce": (
                    f"{region} {suffix}, {country} içindeki en çok ziyaret edilen noktalardan biri olarak "
                    f"bölgenin kültürünü, günlük yaşamını ve tarihî dokusunu tanıtır. "
                    f"Yerel halkın kullandığı alanlarla turistik yürüyüş rotalarını bir araya getirir. "
                    f"Ziyaretçiler burada fotoğraf çekebilir, kısa gezi planı yapabilir ve bölgenin karakterini yakından görebilir."
                ),
            })
        return items

    def open_region_tourism_places(self, country, region):
        win = tk.Toplevel(self)
        win.title(f"{region} - Turistik Yerler")
        win.geometry("1080x720")
        win.configure(bg=APP_BG)

        header = tk.Frame(win, bg=APP_BG)
        header.pack(fill="x", padx=24, pady=(20, 10))
        tk.Label(header, text=f"{region} Turistik Yerler", bg=APP_BG, fg=TEXT, font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(header, text=f"{country} içindeki seçili il/bölge için popüler 10 turistik mekan.", bg=APP_BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        sf = ScrollFrame(win, bg=APP_BG)
        sf.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        places = self.tourist_places_for_region(country, region)
        for i, p in enumerate(places):
            card = tk.Frame(sf.inner, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=i//2, column=i%2, sticky="nsew", padx=8, pady=8)
            sf.inner.columnconfigure(i%2, weight=1)

            tk.Label(card, text=f"{i+1}. {p['ad']}", bg=CARD, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=14, pady=(14, 4))
            tk.Label(card, text=f"{p['kategori']} • Puan {p['puan']}", bg=CARD, fg=GREEN, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=2)
            tk.Label(card, text=p["aciklama"], bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=440, justify="left").pack(anchor="w", padx=14, pady=(8, 12))

            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", padx=14, pady=(0, 14))
            Button(row, "Detay", command=lambda place=p, c=country, r=region: self.open_tourist_place_detail(c, r, place), bg=BLUE).pack(side="left", padx=(0, 8))
            Button(row, "Rota Ekle", command=lambda place=p, c=country, r=region: self.shell.show("route_create", arrive_country=c, arrive_region=r, destination_place=place["ad"]), bg=GREEN).pack(side="left")

    def open_tourist_place_detail(self, country, region, place):
        win = tk.Toplevel(self)
        win.title(place["ad"])
        win.geometry("760x520")
        win.configure(bg=APP_BG)

        tk.Label(win, text=place["ad"], bg=APP_BG, fg=TEXT, font=("Segoe UI", 24, "bold")).pack(anchor="w", padx=24, pady=(24, 6))
        tk.Label(win, text=f"{country} • {region} • {place['kategori']} • Puan {place['puan']}", bg=APP_BG, fg=GREEN, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=24)

        card = Card(win, title="Kısa Tarihçe")
        card.pack(fill="both", expand=True, padx=24, pady=20)
        tk.Label(card, text=place["tarihce"], bg=CARD, fg=TEXT, font=("Segoe UI", 11), wraplength=680, justify="left").pack(anchor="w", padx=16, pady=(10, 16))

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x", padx=16, pady=(0, 16))
        Button(row, "Rota Ekle", command=lambda: self.shell.show("route_create", arrive_country=country, arrive_region=region, destination_place=place["ad"]), bg=GREEN).pack(side="left", padx=(0, 8))
        Button(row, "Google'da Ara", command=lambda: webbrowser.open("https://www.google.com/search?q=" + place["ad"].replace(" ", "+")), bg=BLUE).pack(side="left")

    def select_country(self, idx):
        try:
            self.selected_country = self.countries["features"][idx]
            self.selected_mode = 'country'
            self.region_panel_key = None
            self.selected_region_name = None
            self.selected_region_idx = None
            self.clear_region_info_card()
            self.drag_moved = False
            self.drag_start = None
            self.fit_feature(self.selected_country)
            self.draw()
        except Exception as e:
            messagebox.showerror("Ülke seçilemedi", str(e))

    def reset_world(self):
        self.selected_country = None
        self.selected_mode = 'world'
        self.region_panel_key = None
        self.selected_region_name = None
        self.selected_region_idx = None
        self.clear_region_info_card()
        self.scale = self.min_scale
        self.offset_x = (self.canvas.winfo_width() or 900) / 2
        self.offset_y = (self.canvas.winfo_height() or 520) / 2
        self.stat_country.value_label.configure(text="Yok")
        self.stat_regions.value_label.configure(text="0")
        self.hint_badge.configure(text="Ülke seçilmedi")
        self.drag_moved = False
        self.drag_start = None
        for w in self.region_list.inner.winfo_children():
            w.destroy()
        self.draw()

    def feature_bbox(self, feature):
        xs, ys = [], []
        for ring in self.geom_rings(feature.get("geometry")):
            for pair in ring:
                try:
                    xs.append(pair[0]); ys.append(pair[1])
                except Exception:
                    pass
        if not xs or not ys:
            return (-180, -90, 180, 90)
        return min(xs), min(ys), max(xs), max(ys)

    def fit_feature(self, feature):
        minx, miny, maxx, maxy = self.feature_bbox(feature)
        w = max(300, self.canvas.winfo_width())
        h = max(300, self.canvas.winfo_height())
        dx = max(1, maxx - minx)
        dy = max(1, maxy - miny)
        self.scale = max(self.min_scale, min(self.max_scale, min((w * 0.76) / dx, (h * 0.76) / dy)))
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        self.offset_x = w / 2 - cx * self.scale
        self.offset_y = h / 2 + cy * self.scale

    def on_press(self, event):
        self.drag_start = (event.x, event.y)
        self.drag_moved = False

    def on_release(self, event):
        if self.drag_moved:
            return

        items = self.canvas.find_overlapping(event.x - 4, event.y - 4, event.x + 4, event.y + 4)
        tags = set()
        for item in items:
            tags.update(self.canvas.gettags(item))

        if self.selected_country:
            # Bölge polygonuna veya etiketine tek tıkla bilgi kartı aç.
            for t in tags:
                m = re.fullmatch(r"region_(\d+)", str(t))
                if m:
                    self.select_region_by_index(int(m.group(1)))
                    return

            hit_map_shape = any(
                str(t).startswith("country_") or str(t).startswith("region_") or str(t) in {"selected_country", "country_name"}
                for t in tags
            )
            if not hit_map_shape:
                self.reset_world()
            return

        # Dünya modunda ülke adının üstüne de bassan alttaki ülkeyi bulup aç.
        for t in tags:
            m = re.fullmatch(r"country_(\d+)", str(t))
            if m:
                self.select_country(int(m.group(1)))
                return


    def on_drag(self, event):
        if not self.drag_start:
            return
        dx = event.x - self.drag_start[0]
        dy = event.y - self.drag_start[1]
        if abs(dx) + abs(dy) > 3:
            self.drag_moved = True
        self.offset_x += dx
        self.offset_y += dy
        self.drag_start = (event.x, event.y)
        self.draw()
    def on_wheel(self, event):
        self.zoom_at(1.15 if event.delta > 0 else 0.87, event.x, event.y)
    def on_wheel_linux(self, event, direction):
        self.zoom_at(1.15 if direction > 0 else 0.87, event.x, event.y)
    def zoom_at(self, factor, x=None, y=None):
        if x is None:
            x = (self.canvas.winfo_width() or 900) / 2
        if y is None:
            y = (self.canvas.winfo_height() or 520) / 2
        lon = (x - self.offset_x) / self.scale
        lat = -(y - self.offset_y) / self.scale
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
        self.scale = new_scale
        self.offset_x = x - lon * self.scale
        self.offset_y = y + lat * self.scale
        self.draw()




class ToolsHubPage(BasePage):
    title = "Seyahat Araçları"
    subtitle = "Gerçekten gerekli yardımcı ekranlar burada toplandı."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def build(self):
        area = tk.Frame(self, bg=APP_BG)
        area.pack(fill="both", expand=True, padx=26, pady=10)
        tools = [
            ("budget", "Bütçe", "Harcama, kategori ve kişi başı hesap"),
            ("reservations", "Rezervasyon", "Otel, uçak, restoran ve müze takibi"),
            ("packing", "Valiz Listesi", "Eşya ve hazırlık kontrolü"),
            ("documents", "Belge Kasası", "Pasaport, bilet, sigorta linkleri"),
            ("emergency", "Acil Bilgiler", "Acil kişi, konsolosluk, otel bilgileri"),
        ]
        for i, (key, title, desc) in enumerate(tools):
            card = tk.Frame(area, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
            card.grid(row=i//3, column=i%3, sticky="nsew", padx=8, pady=8)
            area.columnconfigure(i%3, weight=1)
            tk.Label(card, text=title, bg=CARD, fg=TEXT, font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
            tk.Label(card, text=desc, bg=CARD, fg=MUTED, font=("Segoe UI", 9), wraplength=260, justify="left").pack(anchor="w", padx=16, pady=(0, 12))
            Button(card, "Aç", command=lambda k=key: self.shell.show(k), bg=BLUE).pack(anchor="w", padx=16, pady=(0, 14))


class SmartTravelPage(BasePage):
    title = "Akıllı Seyahat Kontrol Paneli"
    subtitle = "Hazırlık yüzdesi, riskler, seyahat önerileri ve başarımları tek ekranda gösterir."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def build(self):
        body = tk.Frame(self, bg=APP_BG)
        body.pack(fill="both", expand=True, padx=26, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        prep = Card(body, title="Seyahat Hazırlık Yüzdeleri")
        prep.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 10))
        for r in self.db.veri.get("seyahatler", []):
            score = readiness_score(self.db, r)
            tk.Label(prep, text=f"{r.get('baslik')}  •  %{score}", bg=CARD, fg=readiness_color(score), font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
            bar = tk.Canvas(prep, height=12, bg=CARD2, highlightthickness=0)
            bar.pack(fill="x", padx=16, pady=(0, 4))
            bar.update_idletasks()
            bar.create_rectangle(0, 0, int(340 * score / 100), 12, fill=readiness_color(score), outline="")

        risks = Card(body, title="Risk Kontrol Paneli")
        risks.grid(row=0, column=1, sticky="nsew", pady=(0, 10))
        for text, color in risk_list(self.db):
            tk.Label(risks, text="⚠ " + text, bg=CARD, fg=color, font=("Segoe UI", 10, "bold"), wraplength=430, justify="left").pack(anchor="w", padx=16, pady=7)

        rec = Card(body, title="Seyahat Öneri Motoru")
        rec.grid(row=1, column=0, sticky="nsew", padx=(0, 10))
        self.recommendations(rec)

        ach = Card(body, title="Seyahat Başarımları")
        ach.grid(row=1, column=1, sticky="nsew")
        sf = ScrollFrame(ach, bg=CARD)
        sf.pack(fill="both", expand=True, padx=12, pady=12)
        for name, val, target, desc in achievement_data(self.db):
            pct = min(100, int((val / target) * 100)) if target else 100
            col = GREEN if pct >= 100 else YELLOW if pct >= 50 else MUTED
            item = tk.Frame(sf.inner, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            item.pack(fill="x", pady=5)
            tk.Label(item, text=f"{name}  {min(val,target)}/{target}", bg=CARD2, fg=col, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
            tk.Label(item, text=desc, bg=CARD2, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=12)
            bar = tk.Canvas(item, height=10, bg="#0E1725", highlightthickness=0)
            bar.pack(fill="x", padx=12, pady=(4, 8))
            bar.create_rectangle(0, 0, int(300*pct/100), 10, fill=GREEN if pct >= 100 else BLUE, outline="")

    def recommendations(self, master):
        budgets = [float(r.get("butce", 0) or 0) for r in self.db.veri.get("seyahatler", [])]
        avg = sum(budgets) / len(budgets) if budgets else 0
        tips = []
        if avg <= 15000:
            tips += ["Ekonomik bütçe için Kapadokya, Ege ve yakın şehir rotaları daha uygundur.", "Uçak yerine tren/otobüs seçeneği maliyeti azaltabilir."]
        else:
            tips += ["Yurt dışı veya çok duraklı kültür rotaları için bütçen uygun görünüyor.", "Müze ve restoran rezervasyonlarını önceden yapmak plan kalitesini artırır."]
        if not self.db.veri.get("belgeler"):
            tips.append("Belge kasasına uçak bileti ve otel rezervasyonu eklenmeli.")
        if len(self.db.veri.get("planlar", [])) < 5:
            tips.append("Daha güçlü bir seyahat planı için en az 5 aktivite eklenebilir.")
        if len(self.db.veri.get("valiz", [])) < 5:
            tips.append("Valiz listesine temel eşyalar eklenmeli.")
        for t in tips:
            tk.Label(master, text="💡 " + t, bg=CARD, fg=TEXT, font=("Segoe UI", 10), wraplength=420, justify="left").pack(anchor="w", padx=16, pady=7)


class ComparePage(BasePage):
    title = "Rota Karşılaştırma"
    subtitle = "İki rotayı bütçe, durak, tarih, durum ve hazırlık yüzdesi açısından karşılaştır."

    def __init__(self, master, db, shell, **kwargs):
        super().__init__(master, db, shell, **kwargs)
        routes = db.veri.get("seyahatler", [])
        names = [r["baslik"] for r in routes]
        self.a = tk.StringVar(value=names[0] if names else "")
        self.b = tk.StringVar(value=names[1] if len(names)>1 else (names[0] if names else ""))
        self.build()

    def build(self):
        top = Card(self, title="Karşılaştırılacak Rotalar")
        top.pack(fill="x", padx=26, pady=10)
        row = tk.Frame(top, bg=CARD)
        row.pack(fill="x", padx=16, pady=14)
        names = [r["baslik"] for r in self.db.veri.get("seyahatler", [])]
        ttk.Combobox(row, textvariable=self.a, values=names, state="readonly", width=30).pack(side="left", padx=6)
        ttk.Combobox(row, textvariable=self.b, values=names, state="readonly", width=30).pack(side="left", padx=6)
        Button(row, "Karşılaştır", command=self.refresh, bg=GREEN).pack(side="left", padx=6)

        self.area = tk.Frame(self, bg=APP_BG)
        self.area.pack(fill="both", expand=True, padx=26, pady=(0,18))
        self.refresh()

    def find(self, name):
        return next((r for r in self.db.veri.get("seyahatler", []) if r["baslik"] == name), None)

    def refresh(self):
        for w in self.area.winfo_children():
            w.destroy()
        ra, rb = self.find(self.a.get()), self.find(self.b.get())
        if not ra or not rb:
            return
        self.area.columnconfigure(0, weight=1)
        self.area.columnconfigure(1, weight=1)
        self.compare_card(self.area, ra).grid(row=0, column=0, sticky="nsew", padx=(0,8))
        self.compare_card(self.area, rb).grid(row=0, column=1, sticky="nsew", padx=(8,0))

    def compare_card(self, master, r):
        c = Card(master, title=r["baslik"])
        lines = [
            ("Başlangıç", r.get("baslangic","-")),
            ("Bitiş", r.get("bitis","-")),
            ("Tarih", r.get("tarih","-")),
            ("Rota tipi", r.get("tip","-")),
            ("Durum", r.get("durum","-")),
            ("Bütçe", f"{int(float(r.get('butce',0)))} TL"),
            ("Durak sayısı", len(r.get("duraklar", []))),
            ("Hazırlık", f"%{readiness_score(self.db, r)}"),
        ]
        for k, v in lines:
            tk.Label(c, text=f"{k}: {v}", bg=CARD, fg=TEXT if k!="Hazırlık" else readiness_color(readiness_score(self.db, r)), font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=18, pady=7)
        tk.Label(c, text=route_summary(self.db, r), bg=CARD, fg=MUTED, font=("Segoe UI", 9), justify="left", wraplength=460).pack(anchor="w", padx=18, pady=12)
        return c


class GlobalSearchPage(BasePage):
    title = "Global Arama"
    subtitle = "Rota, belge, rezervasyon, plan, harcama, günlük, valiz ve hatırlatıcılar içinde ara."

    def __init__(self, master, db, shell, **kwargs):
        self.q = tk.StringVar()
        super().__init__(master, db, shell, **kwargs)
        self.build()

    def build(self):
        top = Card(self)
        top.pack(fill="x", padx=26, pady=10)
        row = tk.Frame(top, bg=CARD)
        row.pack(fill="x", padx=16, pady=14)
        tk.Entry(row, textvariable=self.q, bg=CARD2, fg=TEXT, insertbackground=TEXT, relief="flat", font=("Segoe UI", 11)).pack(side="left", fill="x", expand=True, ipady=10, padx=(0,8))
        Button(row, "Ara", command=self.search, bg=GREEN).pack(side="left")

        self.results = Card(self, title="Sonuçlar")
        self.results.pack(fill="both", expand=True, padx=26, pady=(0,18))
        self.sf = ScrollFrame(self.results, bg=CARD)
        self.sf.pack(fill="both", expand=True, padx=16, pady=16)

    def search(self):
        for w in self.sf.inner.winfo_children():
            w.destroy()
        q = self.q.get().lower().strip()
        if not q:
            tk.Label(self.sf.inner, text="Arama yapmak için kelime yaz.", bg=CARD, fg=MUTED).pack(anchor="w")
            return

        def add(kind, title, desc):
            f = tk.Frame(self.sf.inner, bg=CARD2, highlightbackground=BORDER, highlightthickness=1)
            f.pack(fill="x", pady=6)
            tk.Label(f, text=f"{kind} • {title}", bg=CARD2, fg=TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(8,2))
            tk.Label(f, text=desc, bg=CARD2, fg=MUTED, font=("Segoe UI", 9), wraplength=760, justify="left").pack(anchor="w", padx=14, pady=(0,8))

        count = 0
        for key, label in [("seyahatler","Rota"),("planlar","Plan"),("butce","Bütçe"),("rezervasyonlar","Rezervasyon"),("gunlukler","Günlük"),("valiz","Valiz"),("belgeler","Belge"),("acil","Acil"),("arkadaslar","Arkadaş"),("checklist","Checklist"),("hatirlaticilar","Hatırlatıcı")]:
            for item in self.db.veri.get(key, []):
                text = json.dumps(item, ensure_ascii=False).lower()
                if q in text:
                    title = item.get("baslik") or item.get("ad") or item.get("aktivite") or item.get("madde") or item.get("kategori") or item.get("tur") or key
                    add(label, title, json.dumps(item, ensure_ascii=False))
                    count += 1
        if count == 0:
            tk.Label(self.sf.inner, text="Sonuç bulunamadı.", bg=CARD, fg=MUTED).pack(anchor="w")


if __name__ == "__main__":
    App().mainloop()
