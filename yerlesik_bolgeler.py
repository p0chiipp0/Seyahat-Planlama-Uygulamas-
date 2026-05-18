# -*- coding: utf-8 -*-
"""Routify yerleşik bölge veri paketi.

Bu paket uygulamanın internet/geoBoundaries olmadan da her ülkeyi açabilmesini sağlar.
Gerçek sınır verisi varsa harita polygonları çizilir; yoksa bu yerleşik liste ana kaynak olur.
"""

LOCAL_REGIONS = {
    "TUR": [
        "Adana","Adıyaman","Afyonkarahisar","Ağrı","Aksaray","Amasya","Ankara","Antalya","Ardahan","Artvin",
        "Aydın","Balıkesir","Bartın","Batman","Bayburt","Bilecik","Bingöl","Bitlis","Bolu","Burdur",
        "Bursa","Çanakkale","Çankırı","Çorum","Denizli","Diyarbakır","Düzce","Edirne","Elazığ","Erzincan",
        "Erzurum","Eskişehir","Gaziantep","Giresun","Gümüşhane","Hakkari","Hatay","Iğdır","Isparta","İstanbul",
        "İzmir","Kahramanmaraş","Karabük","Karaman","Kars","Kastamonu","Kayseri","Kırıkkale","Kırklareli","Kırşehir",
        "Kilis","Kocaeli","Konya","Kütahya","Malatya","Manisa","Mardin","Mersin","Muğla","Muş",
        "Nevşehir","Niğde","Ordu","Osmaniye","Rize","Sakarya","Samsun","Siirt","Sinop","Sivas",
        "Şanlıurfa","Şırnak","Tekirdağ","Tokat","Trabzon","Tunceli","Uşak","Van","Yalova","Yozgat","Zonguldak"
    ],
    "USA": [
        "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware","Florida","Georgia",
        "Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana","Maine","Maryland",
        "Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada","New Hampshire","New Jersey",
        "New Mexico","New York","North Carolina","North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina",
        "South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia","Wisconsin","Wyoming","District of Columbia"
    ],
    "CAN": [
        "Alberta","British Columbia","Manitoba","New Brunswick","Newfoundland and Labrador","Nova Scotia","Ontario",
        "Prince Edward Island","Quebec","Saskatchewan","Northwest Territories","Nunavut","Yukon"
    ],
    "JPN": [
        "Hokkaidō","Aomori","Iwate","Miyagi","Akita","Yamagata","Fukushima","Ibaraki","Tochigi","Gunma",
        "Saitama","Chiba","Tokyo","Kanagawa","Niigata","Toyama","Ishikawa","Fukui","Yamanashi","Nagano",
        "Gifu","Shizuoka","Aichi","Mie","Shiga","Kyoto","Osaka","Hyōgo","Nara","Wakayama",
        "Tottori","Shimane","Okayama","Hiroshima","Yamaguchi","Tokushima","Kagawa","Ehime","Kōchi","Fukuoka",
        "Saga","Nagasaki","Kumamoto","Ōita","Miyazaki","Kagoshima","Okinawa"
    ],
    "KOR": [
        "Seoul","Busan","Daegu","Incheon","Gwangju","Daejeon","Ulsan","Sejong","Gyeonggi","Gangwon",
        "North Chungcheong","South Chungcheong","North Jeolla","South Jeolla","North Gyeongsang","South Gyeongsang","Jeju"
    ],
    "MNG": [
        "Arkhangai","Bayan-Ölgii","Bayankhongor","Bulgan","Darkhan-Uul","Dornod","Dornogovi","Dundgovi","Govi-Altai",
        "Govisümber","Khentii","Khovd","Khövsgöl","Ömnögovi","Orkhon","Övörkhangai","Selenge","Sükhbaatar",
        "Töv","Uvs","Zavkhan","Ulaanbaatar"
    ],
    "IRN": [
        "Alborz","Ardabil","Bushehr","Chaharmahal and Bakhtiari","East Azerbaijan","Fars","Gilan","Golestan","Hamadan","Hormozgan",
        "Ilam","Isfahan","Kerman","Kermanshah","Khuzestan","Kohgiluyeh and Boyer-Ahmad","Kurdistan","Lorestan","Markazi","Mazandaran",
        "North Khorasan","Qazvin","Qom","Razavi Khorasan","Semnan","Sistan and Baluchestan","South Khorasan","Tehran","West Azerbaijan","Yazd","Zanjan"
    ],
    "IRQ": [
        "Al Anbar","Babil","Baghdad","Basra","Dhi Qar","Diyala","Dohuk","Erbil","Halabja","Karbala",
        "Kirkuk","Maysan","Muthanna","Najaf","Nineveh","Qadisiyyah","Saladin","Sulaymaniyah","Wasit"
    ],
    "OMN": [
        "Ad Dakhiliyah","Al Batinah North","Al Batinah South","Al Buraimi","Al Wusta","Ash Sharqiyah North",
        "Ash Sharqiyah South","Dhofar","Musandam","Muscat","Ad Dhahirah"
    ],
    "KAZ": [
        "Abai","Akmola","Aktobe","Almaty Region","Atyrau","East Kazakhstan","Jambyl","Jetisu","Karaganda","Kostanay",
        "Kyzylorda","Mangystau","North Kazakhstan","Pavlodar","Turkistan","Ulytau","West Kazakhstan","Astana","Almaty","Shymkent"
    ],
    "IDN": [
        "Aceh","North Sumatra","West Sumatra","Riau","Riau Islands","Jambi","Bengkulu","South Sumatra","Bangka Belitung Islands","Lampung",
        "Banten","Jakarta","West Java","Central Java","Yogyakarta","East Java","Bali","West Nusa Tenggara","East Nusa Tenggara",
        "West Kalimantan","Central Kalimantan","South Kalimantan","East Kalimantan","North Kalimantan","North Sulawesi","Gorontalo",
        "Central Sulawesi","West Sulawesi","South Sulawesi","Southeast Sulawesi","Maluku","North Maluku","West Papua","Southwest Papua",
        "Central Papua","Highland Papua","Papua","South Papua"
    ],
    "FRA": [
        "Auvergne-Rhône-Alpes","Bourgogne-Franche-Comté","Bretagne","Centre-Val de Loire","Corse","Grand Est",
        "Hauts-de-France","Île-de-France","Normandie","Nouvelle-Aquitaine","Occitanie","Pays de la Loire",
        "Provence-Alpes-Côte d’Azur","Guadeloupe","Martinique","Guyane","La Réunion","Mayotte"
    ],
    "DEU": [
        "Baden-Württemberg","Bavaria","Berlin","Brandenburg","Bremen","Hamburg","Hesse","Lower Saxony","Mecklenburg-Vorpommern",
        "North Rhine-Westphalia","Rhineland-Palatinate","Saarland","Saxony","Saxony-Anhalt","Schleswig-Holstein","Thuringia"
    ],
    "CHN": [
        "Anhui","Beijing","Chongqing","Fujian","Gansu","Guangdong","Guangxi","Guizhou","Hainan","Hebei",
        "Heilongjiang","Henan","Hong Kong","Hubei","Hunan","Inner Mongolia","Jiangsu","Jiangxi","Jilin","Liaoning",
        "Macau","Ningxia","Qinghai","Shaanxi","Shandong","Shanghai","Shanxi","Sichuan","Tianjin","Tibet",
        "Xinjiang","Yunnan","Zhejiang"
    ],
    "IND": [
        "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand",
        "Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab",
        "Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu and Kashmir",
        "Ladakh","Puducherry","Chandigarh","Andaman and Nicobar Islands","Dadra and Nagar Haveli and Daman and Diu","Lakshadweep"
    ],
    "BRA": [
        "Acre","Alagoas","Amapá","Amazonas","Bahia","Ceará","Distrito Federal","Espírito Santo","Goiás","Maranhão",
        "Mato Grosso","Mato Grosso do Sul","Minas Gerais","Pará","Paraíba","Paraná","Pernambuco","Piauí","Rio de Janeiro",
        "Rio Grande do Norte","Rio Grande do Sul","Rondônia","Roraima","Santa Catarina","São Paulo","Sergipe","Tocantins"
    ],
    "AUS": [
        "New South Wales","Victoria","Queensland","Western Australia","South Australia","Tasmania","Australian Capital Territory","Northern Territory"
    ],
    "GBR": ["England","Scotland","Wales","Northern Ireland"],
    "ESP": [
        "Andalusia","Aragon","Asturias","Balearic Islands","Basque Country","Canary Islands","Cantabria","Castile and León",
        "Castilla-La Mancha","Catalonia","Extremadura","Galicia","La Rioja","Madrid","Murcia","Navarre","Valencian Community"
    ],
    "ITA": [
        "Abruzzo","Aosta Valley","Apulia","Basilicata","Calabria","Campania","Emilia-Romagna","Friuli Venezia Giulia","Lazio","Liguria",
        "Lombardy","Marche","Molise","Piedmont","Sardinia","Sicily","Tuscany","Trentino-Alto Adige","Umbria","Veneto"
    ],
    "RUS": [
        "Central Federal District","Northwestern Federal District","Southern Federal District","North Caucasian Federal District",
        "Volga Federal District","Ural Federal District","Siberian Federal District","Far Eastern Federal District"
    ],
    "ZAF": ["Eastern Cape","Free State","Gauteng","KwaZulu-Natal","Limpopo","Mpumalanga","Northern Cape","North West","Western Cape"],
    "MEX": [
        "Aguascalientes","Baja California","Baja California Sur","Campeche","Chiapas","Chihuahua","Coahuila","Colima","Durango","Guanajuato",
        "Guerrero","Hidalgo","Jalisco","Mexico City","México","Michoacán","Morelos","Nayarit","Nuevo León","Oaxaca",
        "Puebla","Querétaro","Quintana Roo","San Luis Potosí","Sinaloa","Sonora","Tabasco","Tamaulipas","Tlaxcala","Veracruz","Yucatán","Zacatecas"
    ],    "PRT": ["Aveiro","Beja","Braga","Bragança","Castelo Branco","Coimbra","Évora","Faro","Guarda","Leiria","Lisbon","Portalegre","Porto","Santarém","Setúbal","Viana do Castelo","Vila Real","Viseu","Azores","Madeira"],
    "ISL": ["Capital Region","Southern Peninsula","West","Westfjords","Northwest","Northeast","East","South"],
    "SWE": ["Stockholm","Uppsala","Södermanland","Östergötland","Jönköping","Kronoberg","Kalmar","Gotland","Blekinge","Skåne","Halland","Västra Götaland","Värmland","Örebro","Västmanland","Dalarna","Gävleborg","Västernorrland","Jämtland","Västerbotten","Norrbotten"],
    "NOR": ["Oslo","Rogaland","Møre og Romsdal","Nordland","Viken","Innlandet","Vestfold og Telemark","Agder","Vestland","Trøndelag","Troms og Finnmark"],
    "CZE": ["Prague","Central Bohemian","South Bohemian","Plzeň","Karlovy Vary","Ústí nad Labem","Liberec","Hradec Králové","Pardubice","Vysočina","South Moravian","Olomouc","Zlín","Moravian-Silesian"],
    "SVN": ["Pomurska","Podravska","Koroška","Savinjska","Zasavska","Posavska","Jugovzhodna Slovenija","Osrednjeslovenska","Gorenjska","Primorsko-notranjska","Goriška","Obalno-kraška"],
    "UKR": ["Cherkasy","Chernihiv","Chernivtsi","Dnipropetrovsk","Donetsk","Ivano-Frankivsk","Kharkiv","Kherson","Khmelnytskyi","Kirovohrad","Kyiv","Luhansk","Lviv","Mykolaiv","Odesa","Poltava","Rivne","Sumy","Ternopil","Vinnytsia","Volyn","Zakarpattia","Zaporizhzhia","Zhytomyr","Kyiv City"],
    "EST": ["Harju","Hiiu","Ida-Viru","Jõgeva","Järva","Lääne","Lääne-Viru","Põlva","Pärnu","Rapla","Saare","Tartu","Valga","Viljandi","Võru"],
    "LVA": ["Riga","Daugavpils","Jelgava","Jūrmala","Liepāja","Rēzekne","Ventspils","Vidzeme","Kurzeme","Zemgale","Latgale"],
    "LTU": ["Alytus","Kaunas","Klaipėda","Marijampolė","Panevėžys","Šiauliai","Tauragė","Telšiai","Utena","Vilnius"],
    "GRC": ["Attica","Central Greece","Central Macedonia","Crete","Eastern Macedonia and Thrace","Epirus","Ionian Islands","North Aegean","Peloponnese","South Aegean","Thessaly","Western Greece","Western Macedonia"],
    "CHL": ["Arica and Parinacota","Tarapacá","Antofagasta","Atacama","Coquimbo","Valparaíso","Santiago Metropolitan","O’Higgins","Maule","Ñuble","Biobío","Araucanía","Los Ríos","Los Lagos","Aysén","Magallanes"],
    "ARG": ["Buenos Aires","Catamarca","Chaco","Chubut","Córdoba","Corrientes","Entre Ríos","Formosa","Jujuy","La Pampa","La Rioja","Mendoza","Misiones","Neuquén","Río Negro","Salta","San Juan","San Luis","Santa Cruz","Santa Fe","Santiago del Estero","Tierra del Fuego","Tucumán","Buenos Aires City"],
    "SUR": ["Brokopondo","Commewijne","Coronie","Marowijne","Nickerie","Para","Paramaribo","Saramacca","Sipaliwini","Wanica"],
    "GUY": ["Barima-Waini","Cuyuni-Mazaruni","Demerara-Mahaica","East Berbice-Corentyne","Essequibo Islands-West Demerara","Mahaica-Berbice","Pomeroon-Supenaam","Potaro-Siparuni","Upper Demerara-Berbice","Upper Takutu-Upper Essequibo"],
    "VEN": ["Amazonas","Anzoátegui","Apure","Aragua","Barinas","Bolívar","Carabobo","Cojedes","Delta Amacuro","Falcón","Guárico","Lara","Mérida","Miranda","Monagas","Nueva Esparta","Portuguesa","Sucre","Táchira","Trujillo","Vargas","Yaracuy","Zulia","Capital District"],
    "ECU": ["Azuay","Bolívar","Cañar","Carchi","Chimborazo","Cotopaxi","El Oro","Esmeraldas","Galápagos","Guayas","Imbabura","Loja","Los Ríos","Manabí","Morona Santiago","Napo","Orellana","Pastaza","Pichincha","Santa Elena","Santo Domingo de los Tsáchilas","Sucumbíos","Tungurahua","Zamora Chinchipe"],
    "GRL": ["Avannaata","Kujalleq","Qeqertalik","Qeqqata","Sermersooq","Northeast Greenland National Park"],
    "GEO": ["Abkhazia","Adjara","Guria","Imereti","Kakheti","Kvemo Kartli","Mtskheta-Mtianeti","Racha-Lechkhumi and Kvemo Svaneti","Samegrelo-Zemo Svaneti","Samtskhe-Javakheti","Shida Kartli","Tbilisi"],
    "SYR": ["Aleppo","Damascus","Rif Dimashq","Homs","Hama","Latakia","Tartus","Idlib","Al-Hasakah","Deir ez-Zor","Raqqa","Daraa","As-Suwayda","Quneitra"],
    "PAK": ["Balochistan","Khyber Pakhtunkhwa","Punjab","Sindh","Islamabad Capital Territory","Gilgit-Baltistan","Azad Jammu and Kashmir"],
    "NZL": ["Northland","Auckland","Waikato","Bay of Plenty","Gisborne","Hawke’s Bay","Taranaki","Manawatū-Whanganui","Wellington","Tasman","Nelson","Marlborough","West Coast","Canterbury","Otago","Southland"],
    "PNG": ["Central","Chimbu","Eastern Highlands","East New Britain","East Sepik","Enga","Gulf","Hela","Jiwaka","Madang","Manus","Milne Bay","Morobe","New Ireland","Northern","Southern Highlands","West New Britain","West Sepik","Western","Western Highlands","Bougainville","National Capital District"],

}

GENERIC_REGIONS = [
    "Başkent Bölgesi",
    "Merkez Bölgesi",
    "Kuzey Bölgesi",
    "Güney Bölgesi",
    "Doğu Bölgesi",
    "Batı Bölgesi",
    "Sahil Bölgesi",
    "İç Bölge",
    "Tarihi Bölge",
    "Doğa ve Dağlık Bölge",
]

NAME_ALIASES = {
    "TURKEY": "TUR", "TÜRKİYE": "TUR",
    "UNITED STATES OF AMERICA": "USA", "UNITED STATES": "USA",
    "CANADA": "CAN", "JAPAN": "JPN", "SOUTH KOREA": "KOR", "REPUBLIC OF KOREA": "KOR",
    "MONGOLIA": "MNG", "IRAN": "IRN", "IRAQ": "IRQ", "OMAN": "OMN", "KAZAKHSTAN": "KAZ",
    "INDONESIA": "IDN", "FRANCE": "FRA", "GERMANY": "DEU", "CHINA": "CHN", "INDIA": "IND",
    "BRAZIL": "BRA", "AUSTRALIA": "AUS", "UNITED KINGDOM": "GBR", "SPAIN": "ESP", "ITALY": "ITA",
    "RUSSIA": "RUS", "RUSSIAN FEDERATION": "RUS", "SOUTH AFRICA": "ZAF", "MEXICO": "MEX",
}

def regions_for(iso3="", country_name=""):
    iso3 = str(iso3 or "").upper().strip()
    country_name = str(country_name or "").upper().strip()

    if iso3 in LOCAL_REGIONS:
        return list(LOCAL_REGIONS[iso3])

    alias = NAME_ALIASES.get(country_name)
    if alias and alias in LOCAL_REGIONS:
        return list(LOCAL_REGIONS[alias])

    # Her ülke en azından stabil açılabilsin diye deterministik yerleşik fallback.
    return list(GENERIC_REGIONS)
