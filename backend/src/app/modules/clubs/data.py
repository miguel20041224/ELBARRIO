from dataclasses import dataclass


@dataclass(frozen=True)
class League:
    id: str
    name: str
    country: str
    tier: int
    reputation: int
    average_salary: float


@dataclass(frozen=True)
class Club:
    id: str
    name: str
    short_name: str
    league_id: str
    city: str
    prestige: int
    budget: int
    nickname: str = ""


LEAGUES: dict[str, League] = {}
CLUBS: dict[str, Club] = {}


def _add_league(league: League, clubs: list[Club]) -> None:
    LEAGUES[league.id] = league
    for club in clubs:
        CLUBS[club.id] = club


_add_league(
    League("col-primera-a", "Liga BetPlay Dimayor", "CO", 3, 68, 2200),
    [
        Club("col-nacional", "Atlético Nacional", "Nacional", "col-primera-a", "Medellín", 88, 12000000, "El Verdolaga"),
        Club("col-millonarios", "Millonarios FC", "Millos", "col-primera-a", "Bogotá", 84, 10000000, "El Embajador"),
        Club("col-america", "América de Cali", "América", "col-primera-a", "Cali", 82, 9000000, "La Mechita"),
        Club("col-junior", "Junior FC", "Junior", "col-primera-a", "Barranquilla", 80, 8500000, "El Tiburón"),
        Club("col-medellin", "Independiente Medellín", "DIM", "col-primera-a", "Medellín", 76, 7000000, "El Poderoso"),
        Club("col-santafe", "Independiente Santa Fe", "Santa Fe", "col-primera-a", "Bogotá", 74, 6500000, "El Cardenal"),
        Club("col-deportivocali", "Deportivo Cali", "Depor", "col-primera-a", "Cali", 74, 6800000, "El Azucarero"),
        Club("col-tolima", "Deportes Tolima", "Tolima", "col-primera-a", "Ibagué", 70, 5500000, "El Pijao"),
        Club("col-oncecaldas", "Once Caldas", "Once", "col-primera-a", "Manizales", 68, 5000000, "El Blanco Blanco"),
        Club("col-bucaramanga", "Atlético Bucaramanga", "Buca", "col-primera-a", "Bucaramanga", 62, 4200000, "El Leopardo"),
        Club("col-pereira", "Deportivo Pereira", "Pereira", "col-primera-a", "Pereira", 58, 3800000, "El Matecaña"),
        Club("col-pasto", "Deportivo Pasto", "Pasto", "col-primera-a", "Pasto", 56, 3500000, "El Volcánico"),
        Club("col-aguilas", "Águilas Doradas", "Águilas", "col-primera-a", "Rionegro", 55, 3400000, ""),
        Club("col-equidad", "La Equidad", "Equidad", "col-primera-a", "Bogotá", 52, 3200000, "El Asegurador"),
        Club("col-alianza", "Alianza FC", "Alianza", "col-primera-a", "Valledupar", 50, 3000000, ""),
        Club("col-envigado", "Envigado FC", "Envigado", "col-primera-a", "Envigado", 45, 2500000, "La Cantera de Héroes"),
        Club("col-boyacachico", "Boyacá Chicó", "Chicó", "col-primera-a", "Tunja", 42, 2200000, "El Ajedrezado"),
        Club("col-fortaleza", "Fortaleza CEIF", "Fortaleza", "col-primera-a", "Bogotá", 40, 2000000, ""),
    ],
)

_add_league(
    League("col-primera-b", "Torneo BetPlay Dimayor", "CO", 2, 45, 900),
    [
        Club("col-cucuta", "Cúcuta Deportivo", "Cúcuta", "col-primera-b", "Cúcuta", 42, 1800000, "El Motilón"),
        Club("col-huila", "Atlético Huila", "Huila", "col-primera-b", "Neiva", 40, 1600000, "El Opita"),
        Club("col-cartagena", "Real Cartagena", "Cartagena", "col-primera-b", "Cartagena", 38, 1500000, "El Heroico"),
        Club("col-patriotas", "Patriotas Boyacá", "Patriotas", "col-primera-b", "Tunja", 34, 1200000, ""),
        Club("col-barranquilla", "Barranquilla FC", "BFC", "col-primera-b", "Barranquilla", 32, 1100000, ""),
        Club("col-quindio", "Deportes Quindío", "Quindío", "col-primera-b", "Armenia", 30, 1000000, "El Cuyabro"),
        Club("col-bogotafc", "Bogotá FC", "Bogotá FC", "col-primera-b", "Bogotá", 30, 950000, ""),
        Club("col-llaneros", "Llaneros FC", "Llaneros", "col-primera-b", "Villavicencio", 28, 900000, ""),
        Club("col-leones", "Leones FC", "Leones", "col-primera-b", "Itagüí", 28, 900000, ""),
        Club("col-realsantander", "Real Santander", "Real Santander", "col-primera-b", "Bucaramanga", 24, 800000, ""),
        Club("col-orsomarso", "Orsomarso SC", "Orsomarso", "col-primera-b", "Palmira", 22, 700000, ""),
        Club("col-tigres", "Tigres FC", "Tigres", "col-primera-b", "Bogotá", 22, 700000, ""),
        Club("col-bocajuniorscali", "Boca Juniors de Cali", "Boca Cali", "col-primera-b", "Cali", 20, 650000, ""),
        Club("col-inter-palmira", "Inter Palmira", "Palmira", "col-primera-b", "Palmira", 20, 600000, ""),
    ],
)

_add_league(
    League("arg-primera", "Liga Profesional Argentina", "AR", 3, 78, 3500),
    [
        Club("arg-riverplate", "River Plate", "River", "arg-primera", "Buenos Aires", 92, 18000000, "El Millonario"),
        Club("arg-bocajuniors", "Boca Juniors", "Boca", "arg-primera", "Buenos Aires", 92, 17500000, "El Xeneize"),
        Club("arg-racing", "Racing Club", "Racing", "arg-primera", "Avellaneda", 82, 11000000, "La Academia"),
        Club("arg-independiente", "Independiente", "Rojo", "arg-primera", "Avellaneda", 80, 10500000, "El Rey de Copas"),
        Club("arg-sanlorenzo", "San Lorenzo", "Cuervo", "arg-primera", "Buenos Aires", 78, 9500000, "El Ciclón"),
        Club("arg-estudiantes", "Estudiantes LP", "Pincha", "arg-primera", "La Plata", 78, 9000000, ""),
        Club("arg-velez", "Vélez Sarsfield", "Vélez", "arg-primera", "Buenos Aires", 76, 8500000, "El Fortín"),
        Club("arg-huracan", "Huracán", "Huracán", "arg-primera", "Buenos Aires", 68, 6000000, "El Globo"),
        Club("arg-newells", "Newell's Old Boys", "Newell's", "arg-primera", "Rosario", 70, 6500000, "La Lepra"),
        Club("arg-rosariocentral", "Rosario Central", "Central", "arg-primera", "Rosario", 70, 6500000, "El Canalla"),
        Club("arg-defensa", "Defensa y Justicia", "Defensa", "arg-primera", "Florencio Varela", 62, 4500000, ""),
        Club("arg-argentinos", "Argentinos Juniors", "Bicho", "arg-primera", "Buenos Aires", 60, 4200000, ""),
        Club("arg-lanus", "Club Atlético Lanús", "Lanús", "arg-primera", "Lanús", 65, 5000000, "El Granate"),
        Club("arg-banfield", "Banfield", "Taladro", "arg-primera", "Banfield", 58, 3800000, ""),
        Club("arg-godoycruz", "Godoy Cruz", "Tomba", "arg-primera", "Mendoza", 55, 3400000, ""),
        Club("arg-talleres", "Talleres de Córdoba", "Talleres", "arg-primera", "Córdoba", 68, 5800000, "La T"),
    ],
)

_add_league(
    League("arg-primera-nacional", "Primera Nacional", "AR", 2, 55, 1200),
    [
        Club("arg-atletico-rafaela", "Atlético Rafaela", "Rafaela", "arg-primera-nacional", "Rafaela", 42, 1400000, ""),
        Club("arg-quilmes", "Quilmes AC", "Quilmes", "arg-primera-nacional", "Quilmes", 55, 2200000, "El Cervecero"),
        Club("arg-alldechicago", "All Boys", "All Boys", "arg-primera-nacional", "Buenos Aires", 45, 1500000, ""),
        Club("arg-nueva-chicago", "Nueva Chicago", "Chicago", "arg-primera-nacional", "Buenos Aires", 42, 1400000, ""),
        Club("arg-gimnasiajujuy", "Gimnasia Jujuy", "Gimnasia Jujuy", "arg-primera-nacional", "Jujuy", 40, 1300000, ""),
        Club("arg-sanmiguel", "San Miguel FC", "San Miguel", "arg-primera-nacional", "San Miguel", 32, 900000, ""),
        Club("arg-ferro", "Ferro Carril Oeste", "Ferro", "arg-primera-nacional", "Buenos Aires", 52, 2000000, ""),
        Club("arg-tigre", "Tigre", "Matador", "arg-primera-nacional", "Victoria", 58, 2500000, "El Matador"),
    ],
)

_add_league(
    League("bra-brasileirao", "Brasileirão Série A", "BR", 3, 82, 5000),
    [
        Club("bra-flamengo", "Flamengo", "Fla", "bra-brasileirao", "Río de Janeiro", 94, 22000000, "Mengão"),
        Club("bra-palmeiras", "Palmeiras", "Verdão", "bra-brasileirao", "São Paulo", 92, 20000000, "El Verdão"),
        Club("bra-corinthians", "Corinthians", "Timão", "bra-brasileirao", "São Paulo", 88, 17000000, "El Timão"),
        Club("bra-saopaulo", "São Paulo FC", "SPFC", "bra-brasileirao", "São Paulo", 86, 15000000, "El Tricolor"),
        Club("bra-santos", "Santos", "Peixe", "bra-brasileirao", "Santos", 84, 13000000, "O Peixe"),
        Club("bra-fluminense", "Fluminense", "Flu", "bra-brasileirao", "Río de Janeiro", 82, 12000000, ""),
        Club("bra-atleticomineiro", "Atlético Mineiro", "Galo", "bra-brasileirao", "Belo Horizonte", 84, 13500000, "El Galo"),
        Club("bra-internacional", "Internacional", "Inter", "bra-brasileirao", "Porto Alegre", 82, 12000000, "El Colorado"),
        Club("bra-gremio", "Grêmio", "Grêmio", "bra-brasileirao", "Porto Alegre", 80, 11000000, "El Tricolor Gaúcho"),
        Club("bra-cruzeiro", "Cruzeiro", "Cruzeiro", "bra-brasileirao", "Belo Horizonte", 78, 9500000, "El Cabuloso"),
        Club("bra-botafogo", "Botafogo", "Fogão", "bra-brasileirao", "Río de Janeiro", 76, 9000000, ""),
        Club("bra-vasco", "Vasco da Gama", "Vasco", "bra-brasileirao", "Río de Janeiro", 74, 8000000, ""),
        Club("bra-bahia", "Bahia", "Bahia", "bra-brasileirao", "Salvador", 68, 6000000, ""),
        Club("bra-fortaleza", "Fortaleza", "Fortaleza", "bra-brasileirao", "Fortaleza", 65, 5000000, ""),
        Club("bra-cuiaba", "Cuiabá", "Cuiabá", "bra-brasileirao", "Cuiabá", 52, 3000000, ""),
        Club("bra-goias", "Goiás", "Goiás", "bra-brasileirao", "Goiânia", 58, 4000000, ""),
    ],
)

_add_league(
    League("esp-laliga", "LaLiga EA Sports", "ES", 5, 95, 45000),
    [
        Club("esp-realmadrid", "Real Madrid", "Madrid", "esp-laliga", "Madrid", 99, 400000000, "Los Blancos"),
        Club("esp-barcelona", "FC Barcelona", "Barça", "esp-laliga", "Barcelona", 97, 380000000, "Blaugrana"),
        Club("esp-atletico", "Atlético de Madrid", "Atleti", "esp-laliga", "Madrid", 91, 200000000, "Colchoneros"),
        Club("esp-sevilla", "Sevilla FC", "Sevilla", "esp-laliga", "Sevilla", 84, 90000000, ""),
        Club("esp-villarreal", "Villarreal CF", "Villarreal", "esp-laliga", "Villarreal", 82, 75000000, "Submarino Amarillo"),
        Club("esp-realsociedad", "Real Sociedad", "Real", "esp-laliga", "San Sebastián", 82, 70000000, "La Real"),
        Club("esp-athletic", "Athletic Club", "Athletic", "esp-laliga", "Bilbao", 82, 65000000, "Los Leones"),
        Club("esp-betis", "Real Betis", "Betis", "esp-laliga", "Sevilla", 78, 55000000, ""),
        Club("esp-valencia", "Valencia CF", "Valencia", "esp-laliga", "Valencia", 76, 50000000, "Los Chés"),
        Club("esp-girona", "Girona FC", "Girona", "esp-laliga", "Girona", 72, 30000000, ""),
        Club("esp-osasuna", "CA Osasuna", "Osasuna", "esp-laliga", "Pamplona", 68, 22000000, "Los Rojillos"),
        Club("esp-celta", "Celta de Vigo", "Celta", "esp-laliga", "Vigo", 68, 22000000, ""),
        Club("esp-getafe", "Getafe CF", "Getafe", "esp-laliga", "Getafe", 65, 18000000, "Azulones"),
        Club("esp-mallorca", "RCD Mallorca", "Mallorca", "esp-laliga", "Palma", 65, 18000000, ""),
        Club("esp-rayo", "Rayo Vallecano", "Rayo", "esp-laliga", "Madrid", 64, 15000000, ""),
        Club("esp-alaves", "Deportivo Alavés", "Alavés", "esp-laliga", "Vitoria", 60, 12000000, ""),
    ],
)

_add_league(
    League("esp-laliga2", "LaLiga Hypermotion", "ES", 3, 68, 4500),
    [
        Club("esp-oviedo", "Real Oviedo", "Oviedo", "esp-laliga2", "Oviedo", 62, 8000000, ""),
        Club("esp-eibar", "SD Eibar", "Eibar", "esp-laliga2", "Eibar", 58, 6500000, ""),
        Club("esp-elche", "Elche CF", "Elche", "esp-laliga2", "Elche", 62, 8000000, ""),
        Club("esp-zaragoza", "Real Zaragoza", "Zaragoza", "esp-laliga2", "Zaragoza", 65, 9000000, ""),
        Club("esp-tenerife", "CD Tenerife", "Tenerife", "esp-laliga2", "Santa Cruz", 55, 5500000, ""),
        Club("esp-sporting", "Sporting Gijón", "Sporting", "esp-laliga2", "Gijón", 62, 8000000, ""),
        Club("esp-cadiz", "Cádiz CF", "Cádiz", "esp-laliga2", "Cádiz", 60, 7000000, ""),
        Club("esp-huesca", "SD Huesca", "Huesca", "esp-laliga2", "Huesca", 48, 4000000, ""),
    ],
)

_add_league(
    League("eng-premier", "Premier League", "EN", 5, 98, 75000),
    [
        Club("eng-mancity", "Manchester City", "City", "eng-premier", "Manchester", 98, 500000000, "The Sky Blues"),
        Club("eng-arsenal", "Arsenal FC", "Arsenal", "eng-premier", "Londres", 94, 350000000, "Gunners"),
        Club("eng-liverpool", "Liverpool FC", "Liverpool", "eng-premier", "Liverpool", 95, 380000000, "The Reds"),
        Club("eng-manunited", "Manchester United", "United", "eng-premier", "Manchester", 92, 400000000, "Red Devils"),
        Club("eng-chelsea", "Chelsea FC", "Chelsea", "eng-premier", "Londres", 90, 300000000, "The Blues"),
        Club("eng-tottenham", "Tottenham Hotspur", "Spurs", "eng-premier", "Londres", 88, 250000000, ""),
        Club("eng-newcastle", "Newcastle United", "Newcastle", "eng-premier", "Newcastle", 84, 180000000, "The Magpies"),
        Club("eng-astonvilla", "Aston Villa", "Villa", "eng-premier", "Birmingham", 82, 130000000, ""),
        Club("eng-brighton", "Brighton & Hove Albion", "Brighton", "eng-premier", "Brighton", 76, 90000000, ""),
        Club("eng-westham", "West Ham United", "West Ham", "eng-premier", "Londres", 76, 90000000, "The Hammers"),
        Club("eng-brentford", "Brentford FC", "Brentford", "eng-premier", "Londres", 72, 60000000, "The Bees"),
        Club("eng-crystalpalace", "Crystal Palace", "Palace", "eng-premier", "Londres", 70, 55000000, ""),
        Club("eng-fulham", "Fulham FC", "Fulham", "eng-premier", "Londres", 70, 55000000, ""),
        Club("eng-nottingham", "Nottingham Forest", "Forest", "eng-premier", "Nottingham", 68, 45000000, ""),
        Club("eng-bournemouth", "AFC Bournemouth", "Bournemouth", "eng-premier", "Bournemouth", 66, 40000000, ""),
        Club("eng-wolves", "Wolverhampton Wanderers", "Wolves", "eng-premier", "Wolverhampton", 70, 55000000, ""),
    ],
)

_add_league(
    League("eng-championship", "EFL Championship", "EN", 4, 78, 12000),
    [
        Club("eng-leeds", "Leeds United", "Leeds", "eng-championship", "Leeds", 78, 45000000, ""),
        Club("eng-southampton", "Southampton FC", "Saints", "eng-championship", "Southampton", 75, 35000000, ""),
        Club("eng-norwich", "Norwich City", "Norwich", "eng-championship", "Norwich", 68, 20000000, ""),
        Club("eng-westbrom", "West Bromwich Albion", "WBA", "eng-championship", "West Bromwich", 66, 18000000, ""),
        Club("eng-sheffield", "Sheffield United", "Sheffield", "eng-championship", "Sheffield", 68, 20000000, ""),
        Club("eng-birmingham", "Birmingham City", "Birmingham", "eng-championship", "Birmingham", 62, 15000000, ""),
        Club("eng-swansea", "Swansea City", "Swansea", "eng-championship", "Swansea", 60, 12000000, ""),
        Club("eng-hull", "Hull City", "Hull", "eng-championship", "Hull", 58, 10000000, ""),
    ],
)

_add_league(
    League("ita-seriea", "Serie A TIM", "IT", 5, 92, 40000),
    [
        Club("ita-inter", "Inter Milán", "Inter", "ita-seriea", "Milán", 94, 250000000, "Nerazzurri"),
        Club("ita-juventus", "Juventus FC", "Juve", "ita-seriea", "Turín", 92, 240000000, "Bianconeri"),
        Club("ita-milan", "AC Milan", "Milan", "ita-seriea", "Milán", 92, 230000000, "Rossoneri"),
        Club("ita-napoli", "SSC Napoli", "Napoli", "ita-seriea", "Nápoles", 90, 200000000, "Partenopei"),
        Club("ita-roma", "AS Roma", "Roma", "ita-seriea", "Roma", 86, 150000000, "Giallorossi"),
        Club("ita-lazio", "SS Lazio", "Lazio", "ita-seriea", "Roma", 84, 130000000, "Biancocelesti"),
        Club("ita-atalanta", "Atalanta BC", "Atalanta", "ita-seriea", "Bérgamo", 84, 130000000, "La Dea"),
        Club("ita-fiorentina", "ACF Fiorentina", "Fiorentina", "ita-seriea", "Florencia", 78, 90000000, "Viola"),
        Club("ita-bologna", "Bologna FC", "Bologna", "ita-seriea", "Bolonia", 74, 55000000, "Rossoblù"),
        Club("ita-torino", "Torino FC", "Torino", "ita-seriea", "Turín", 72, 45000000, "Granata"),
        Club("ita-udinese", "Udinese Calcio", "Udinese", "ita-seriea", "Udine", 70, 40000000, ""),
        Club("ita-genoa", "Genoa CFC", "Genoa", "ita-seriea", "Génova", 68, 32000000, ""),
        Club("ita-sassuolo", "US Sassuolo", "Sassuolo", "ita-seriea", "Sassuolo", 66, 28000000, ""),
        Club("ita-empoli", "Empoli FC", "Empoli", "ita-seriea", "Empoli", 62, 22000000, ""),
        Club("ita-verona", "Hellas Verona", "Verona", "ita-seriea", "Verona", 62, 22000000, ""),
        Club("ita-monza", "AC Monza", "Monza", "ita-seriea", "Monza", 60, 18000000, ""),
    ],
)

_add_league(
    League("ger-bundesliga", "Bundesliga", "DE", 5, 93, 42000),
    [
        Club("ger-bayern", "FC Bayern München", "Bayern", "ger-bundesliga", "Múnich", 98, 450000000, "Die Roten"),
        Club("ger-leverkusen", "Bayer 04 Leverkusen", "Leverkusen", "ger-bundesliga", "Leverkusen", 92, 200000000, "Werkself"),
        Club("ger-dortmund", "Borussia Dortmund", "BVB", "ger-bundesliga", "Dortmund", 91, 220000000, "Die Schwarzgelben"),
        Club("ger-leipzig", "RB Leipzig", "Leipzig", "ger-bundesliga", "Leipzig", 86, 150000000, "Die Roten Bullen"),
        Club("ger-stuttgart", "VfB Stuttgart", "Stuttgart", "ger-bundesliga", "Stuttgart", 82, 90000000, ""),
        Club("ger-frankfurt", "Eintracht Frankfurt", "Frankfurt", "ger-bundesliga", "Fráncfort", 80, 80000000, "SGE"),
        Club("ger-mgladbach", "Borussia M'gladbach", "Gladbach", "ger-bundesliga", "Mönchengladbach", 76, 55000000, "Die Fohlen"),
        Club("ger-wolfsburg", "VfL Wolfsburg", "Wolfsburg", "ger-bundesliga", "Wolfsburgo", 74, 50000000, "Die Wölfe"),
        Club("ger-hoffenheim", "TSG Hoffenheim", "Hoffenheim", "ger-bundesliga", "Sinsheim", 72, 40000000, ""),
        Club("ger-freiburg", "SC Freiburg", "Freiburg", "ger-bundesliga", "Friburgo", 72, 38000000, ""),
        Club("ger-unionberlin", "1. FC Union Berlin", "Union", "ger-bundesliga", "Berlín", 68, 30000000, "Die Eisernen"),
        Club("ger-mainz", "1. FSV Mainz 05", "Mainz", "ger-bundesliga", "Maguncia", 66, 25000000, ""),
        Club("ger-werder", "SV Werder Bremen", "Werder", "ger-bundesliga", "Bremen", 66, 25000000, "Die Werderaner"),
        Club("ger-augsburg", "FC Augsburg", "Augsburg", "ger-bundesliga", "Augsburgo", 62, 20000000, ""),
        Club("ger-koln", "1. FC Köln", "Köln", "ger-bundesliga", "Colonia", 62, 20000000, "Die Geissböcke"),
        Club("ger-bochum", "VfL Bochum", "Bochum", "ger-bundesliga", "Bochum", 55, 12000000, ""),
    ],
)

_add_league(
    League("fra-ligue1", "Ligue 1 McDonald's", "FR", 4, 88, 30000),
    [
        Club("fra-psg", "Paris Saint-Germain", "PSG", "fra-ligue1", "París", 96, 400000000, "Les Parisiens"),
        Club("fra-marseille", "Olympique Marseille", "OM", "fra-ligue1", "Marsella", 84, 130000000, "Les Phocéens"),
        Club("fra-monaco", "AS Monaco", "Monaco", "fra-ligue1", "Mónaco", 82, 120000000, "Les Rouge et Blanc"),
        Club("fra-lyon", "Olympique Lyonnais", "OL", "fra-ligue1", "Lyon", 82, 110000000, "Les Gones"),
        Club("fra-lille", "LOSC Lille", "Lille", "fra-ligue1", "Lille", 78, 75000000, "Les Dogues"),
        Club("fra-nice", "OGC Nice", "Nice", "fra-ligue1", "Niza", 76, 60000000, "Les Aiglons"),
        Club("fra-rennes", "Stade Rennais", "Rennes", "fra-ligue1", "Rennes", 76, 55000000, ""),
        Club("fra-lens", "RC Lens", "Lens", "fra-ligue1", "Lens", 74, 45000000, "Sang et Or"),
        Club("fra-strasbourg", "RC Strasbourg", "Strasbourg", "fra-ligue1", "Estrasburgo", 68, 30000000, ""),
        Club("fra-toulouse", "Toulouse FC", "Toulouse", "fra-ligue1", "Toulouse", 66, 25000000, "TéFéCé"),
        Club("fra-brest", "Stade Brestois", "Brest", "fra-ligue1", "Brest", 66, 25000000, ""),
        Club("fra-nantes", "FC Nantes", "Nantes", "fra-ligue1", "Nantes", 68, 30000000, "Les Canaris"),
        Club("fra-reims", "Stade de Reims", "Reims", "fra-ligue1", "Reims", 64, 22000000, ""),
        Club("fra-montpellier", "Montpellier HSC", "Montpellier", "fra-ligue1", "Montpellier", 62, 20000000, ""),
        Club("fra-lehavre", "Le Havre AC", "Le Havre", "fra-ligue1", "Le Havre", 55, 15000000, ""),
    ],
)

_add_league(
    League("por-primeira", "Liga Portugal", "PT", 4, 82, 15000),
    [
        Club("por-benfica", "SL Benfica", "Benfica", "por-primeira", "Lisboa", 90, 150000000, "As Águias"),
        Club("por-porto", "FC Porto", "Porto", "por-primeira", "Oporto", 90, 145000000, "Dragões"),
        Club("por-sporting", "Sporting CP", "Sporting", "por-primeira", "Lisboa", 88, 140000000, "Leões"),
        Club("por-braga", "SC Braga", "Braga", "por-primeira", "Braga", 78, 60000000, "Arsenalistas"),
        Club("por-vitoria", "Vitória SC", "Vitória", "por-primeira", "Guimarães", 68, 25000000, ""),
        Club("por-boavista", "Boavista FC", "Boavista", "por-primeira", "Oporto", 62, 18000000, "Panteras"),
        Club("por-farense", "SC Farense", "Farense", "por-primeira", "Faro", 55, 12000000, ""),
        Club("por-estoril", "Estoril Praia", "Estoril", "por-primeira", "Estoril", 58, 14000000, ""),
    ],
)

_add_league(
    League("ned-eredivisie", "Eredivisie", "NL", 4, 80, 14000),
    [
        Club("ned-ajax", "AFC Ajax", "Ajax", "ned-eredivisie", "Ámsterdam", 90, 200000000, "De Godenzonen"),
        Club("ned-psv", "PSV Eindhoven", "PSV", "ned-eredivisie", "Eindhoven", 88, 160000000, "Boeren"),
        Club("ned-feyenoord", "Feyenoord", "Feyenoord", "ned-eredivisie", "Rotterdam", 86, 130000000, "De Trots van Zuid"),
        Club("ned-az", "AZ Alkmaar", "AZ", "ned-eredivisie", "Alkmaar", 76, 50000000, ""),
        Club("ned-twente", "FC Twente", "Twente", "ned-eredivisie", "Enschede", 72, 35000000, ""),
        Club("ned-utrecht", "FC Utrecht", "Utrecht", "ned-eredivisie", "Utrecht", 68, 28000000, ""),
        Club("ned-heerenveen", "SC Heerenveen", "Heerenveen", "ned-eredivisie", "Heerenveen", 62, 20000000, ""),
    ],
)

_add_league(
    League("mex-liga-mx", "Liga MX BBVA", "MX", 3, 75, 6500),
    [
        Club("mex-america", "Club América", "América", "mex-liga-mx", "CDMX", 88, 40000000, "Las Águilas"),
        Club("mex-guadalajara", "Club Guadalajara", "Chivas", "mex-liga-mx", "Guadalajara", 84, 35000000, "El Rebaño Sagrado"),
        Club("mex-cruzazul", "Cruz Azul", "Azul", "mex-liga-mx", "CDMX", 82, 30000000, "La Máquina"),
        Club("mex-unam", "Pumas UNAM", "Pumas", "mex-liga-mx", "CDMX", 78, 22000000, "Los Universitarios"),
        Club("mex-monterrey", "CF Monterrey", "Rayados", "mex-liga-mx", "Monterrey", 84, 35000000, "Rayados"),
        Club("mex-tigres", "Tigres UANL", "Tigres", "mex-liga-mx", "San Nicolás", 84, 35000000, ""),
        Club("mex-toluca", "Deportivo Toluca", "Toluca", "mex-liga-mx", "Toluca", 76, 20000000, "Diablos Rojos"),
        Club("mex-santoslaguna", "Santos Laguna", "Santos", "mex-liga-mx", "Torreón", 72, 15000000, ""),
        Club("mex-leon", "Club León", "León", "mex-liga-mx", "León", 72, 15000000, "La Fiera"),
        Club("mex-pachuca", "CF Pachuca", "Pachuca", "mex-liga-mx", "Pachuca", 72, 15000000, "Tuzos"),
        Club("mex-atlas", "Atlas FC", "Atlas", "mex-liga-mx", "Guadalajara", 68, 12000000, "Rojinegros"),
        Club("mex-necaxa", "Club Necaxa", "Necaxa", "mex-liga-mx", "Aguascalientes", 62, 8000000, "Rayos"),
    ],
)

_add_league(
    League("sau-pro-league", "Saudi Pro League", "SA", 3, 72, 90000),
    [
        Club("sau-alhilal", "Al-Hilal SFC", "Al-Hilal", "sau-pro-league", "Riad", 90, 500000000, "Al-Za'eem"),
        Club("sau-alnassr", "Al-Nassr FC", "Al-Nassr", "sau-pro-league", "Riad", 88, 450000000, "Al-Alami"),
        Club("sau-alittihad", "Al-Ittihad Club", "Al-Ittihad", "sau-pro-league", "Yeda", 86, 350000000, ""),
        Club("sau-alahli", "Al-Ahli SFC", "Al-Ahli", "sau-pro-league", "Yeda", 84, 300000000, ""),
        Club("sau-alettifaq", "Al-Ettifaq FC", "Al-Ettifaq", "sau-pro-league", "Dammam", 76, 100000000, ""),
        Club("sau-alfayha", "Al-Fayha FC", "Al-Fayha", "sau-pro-league", "Al Majma'ah", 65, 30000000, ""),
        Club("sau-altaawoun", "Al-Taawoun FC", "Al-Taawoun", "sau-pro-league", "Buraidah", 62, 25000000, ""),
        Club("sau-alwehda", "Al-Wehda Club", "Al-Wehda", "sau-pro-league", "La Meca", 58, 20000000, ""),
    ],
)

_add_league(
    League("usa-mls", "Major League Soccer", "US", 3, 70, 8500),
    [
        Club("usa-intermiami", "Inter Miami CF", "Miami", "usa-mls", "Miami", 82, 100000000, "The Herons"),
        Club("usa-lafc", "Los Angeles FC", "LAFC", "usa-mls", "Los Ángeles", 82, 80000000, ""),
        Club("usa-galaxy", "LA Galaxy", "Galaxy", "usa-mls", "Los Ángeles", 78, 60000000, ""),
        Club("usa-nycfc", "New York City FC", "NYCFC", "usa-mls", "Nueva York", 76, 45000000, ""),
        Club("usa-atlanta", "Atlanta United FC", "Atlanta", "usa-mls", "Atlanta", 76, 45000000, ""),
        Club("usa-seattle", "Seattle Sounders", "Seattle", "usa-mls", "Seattle", 76, 45000000, ""),
        Club("usa-portland", "Portland Timbers", "Timbers", "usa-mls", "Portland", 70, 30000000, ""),
        Club("usa-chicago", "Chicago Fire FC", "Chicago", "usa-mls", "Chicago", 66, 22000000, ""),
    ],
)


def get_league(league_id: str) -> League | None:
    return LEAGUES.get(league_id)


def get_club(club_id: str) -> Club | None:
    return CLUBS.get(club_id)


def get_clubs_for_league(league_id: str) -> list[Club]:
    return [c for c in CLUBS.values() if c.league_id == league_id]


def pick_starting_club(league_id: str, age: int, rng) -> Club | None:
    clubs = get_clubs_for_league(league_id)
    if not clubs:
        return None
    sorted_clubs = sorted(clubs, key=lambda c: c.prestige)
    if age <= 19:
        pool = sorted_clubs[: max(1, len(sorted_clubs) * 4 // 10)]
    elif age <= 24:
        pool = sorted_clubs[: max(1, len(sorted_clubs) * 6 // 10)]
    else:
        pool = sorted_clubs[: max(1, len(sorted_clubs) * 8 // 10)]
    return rng.choice(pool)


def clubs_above_prestige(threshold: int, exclude_league: str | None = None) -> list[Club]:
    return [
        c
        for c in CLUBS.values()
        if c.prestige >= threshold and c.league_id != exclude_league
    ]
