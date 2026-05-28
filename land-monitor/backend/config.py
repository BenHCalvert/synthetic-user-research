import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = os.getenv("DATABASE_PATH", str(DATA_DIR / "listings.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

BUDGET_MIN = 75_000
BUDGET_MAX = 250_000
ACREAGE_MIN = 0.5
ACREAGE_MAX = 20.0

# Zone definitions: keywords matched against title + address + description
ZONES = {
    "Lowman": {
        "counties": ["boise"],
        "keywords": ["lowman", "banner creek", "warm lake road", "kirkham"],
        "priority": 1,
    },
    "Garden Valley": {
        "counties": ["boise"],
        "keywords": ["garden valley", "crouch", "banks", "horseshoe bend", "clear creek"],
        "priority": 2,
    },
    "Atlanta/Trinity": {
        "counties": ["elmore"],
        "keywords": ["atlanta", "trinity", "pine", "featherville", "mtn home", "mountain home"],
        "priority": 2,
    },
    "Mackay/Lost River": {
        "counties": ["custer"],
        "keywords": ["mackay", "lost river", "arco", "challis", "pahsimeroi", "moore"],
        "priority": 1,
    },
    "Salmon/Elk Bend": {
        "counties": ["lemhi"],
        "keywords": ["salmon", "elk bend", "gibbonsville", "cobalt", "north fork", "leadore"],
        "priority": 2,
    },
    "Stanley/Sawtooth": {
        "counties": ["custer", "blaine"],
        "keywords": ["stanley", "sawtooth", "redfish", "robinson bar", "sunbeam", "clayton"],
        "priority": 3,
    },
}

# LandWatch search URLs — update acreage/price filters as needed.
# URL pattern: /[county]-idaho-land-for-sale/acreage,[min]-to-[max],acres/price,[min]-to-[max]
LANDWATCH_URLS = [
    # Boise County (Lowman / Garden Valley)
    "https://www.landwatch.com/boise-county-idaho-land-for-sale/acreage,0.5-to-20,acres/price,75000-to-250000",
    # Elmore County (Atlanta / Trinity)
    "https://www.landwatch.com/elmore-county-idaho-land-for-sale/acreage,0.5-to-20,acres/price,75000-to-250000",
    # Custer County (Mackay / Stanley)
    "https://www.landwatch.com/custer-county-idaho-land-for-sale/acreage,0.5-to-20,acres/price,75000-to-250000",
    # Lemhi County (Salmon / Elk Bend)
    "https://www.landwatch.com/lemhi-county-idaho-land-for-sale/acreage,0.5-to-20,acres/price,75000-to-250000",
]

# Homes.com search URLs
HOMES_URLS = [
    "https://www.homes.com/lowman-id/land-for-sale/",
    "https://www.homes.com/garden-valley-id/land-for-sale/",
    "https://www.homes.com/mackay-id/land-for-sale/",
    "https://www.homes.com/salmon-id/land-for-sale/",
]

IDL_URL = "https://www.idl.idaho.gov/real-estate/state-land-for-sale/"

LANDWATCH_INTERVAL_HOURS = 6
HOMES_INTERVAL_HOURS = 8
IDL_INTERVAL_HOURS = 24

# Playwright browser settings
BROWSER_TIMEOUT_MS = 30_000
PAGE_LOAD_TIMEOUT_MS = 45_000
SCRAPE_DELAY_SECONDS = 2  # polite delay between page requests

# Keyword patterns for description analysis
KEYWORDS = {
    "nf_adjacency": {
        "inholding": ["inholding", "within national forest", "within the forest", "surrounded by national forest",
                      "surrounded by forest service", "completely surrounded by"],
        "adjacent": ["borders national forest", "borders forest service", "adjacent to national forest",
                     "adjacent to forest service", "borders usfs", "usfs boundary", "forest service boundary",
                     "abuts national forest", "abuts forest service"],
        "near": ["near national forest", "near forest service", "close to national forest",
                 "national forest nearby", "minutes from national forest"],
        "none": [],
    },
    "access_type": {
        "year_round_paved": ["year-round paved", "year round paved", "paved road year", "maintained paved"],
        "year_round_gravel": ["year-round access", "year round access", "year-round road", "gravel road year-round",
                              "maintained gravel", "county road access"],
        "seasonal": ["seasonal access", "seasonal road", "seasonal use", "spring through fall",
                     "not accessible in winter", "closed in winter"],
        "hike_in": ["hike in", "hike-in", "ski in", "ski-in", "foot access", "pack in", "walk in"],
        "unknown": [],
    },
    "water": {
        "drilled_well": ["drilled well", "domestic well", "existing well", "well on site", "well in place"],
        "creek_river": ["creek frontage", "river frontage", "creek on property", "borders creek",
                        "seasonal creek", "spring on property", "year-round creek"],
        "community": ["community water", "water district", "rural water", "shared well"],
        "none": ["no water", "no well", "no water rights", "no water source"],
        "unknown": [],
    },
    "utilities": {
        "power": ["power available", "electricity available", "power on site", "electric to site",
                  "power at road", "utility easement"],
        "off_grid": ["off grid", "off-grid", "solar power", "solar panels", "generator", "no utilities",
                     "no power", "no electricity"],
        "unknown": [],
    },
    "is_mining_claim": ["patented mining claim", "patented claim", "mining claim"],
    "in_snra": ["sawtooth nra", "sawtooth national recreation area", "stanley basin snra",
                "sawtooth national recreation"],
}
