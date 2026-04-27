"""
Actualizador diario de datos bancarios para la Calculadora de Hipotecas.
Scrapea tasas Euribor desde euribor-rates.eu y ofertas hipotecarias desde helpmycash.com.
Genera data/euribor.json y data/bank_offers.json.
"""

import json
import logging
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOG_FILE = DATA_DIR / "fetch.log"

EURIBOR_URL = "https://www.euribor-rates.eu/es/"
HELPMYCASH_URL = "https://www.helpmycash.com/mejores-hipotecas/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}

MAX_RETRIES = 3
RETRY_DELAY = 5

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def parse_es_float(text: str) -> float | None:
    """Parse a Spanish-format number: '2,739 %' -> 2.739"""
    if not text:
        return None
    cleaned = text.replace("%", "").replace("€", "").replace("\xa0", "").strip()
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return round(float(cleaned), 4)
    except ValueError:
        return None


def fetch_with_retry(url: str) -> requests.Response:
    """Fetch URL with retry logic."""
    session = requests.Session()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.RequestException as e:
            log.warning(f"Intento {attempt}/{MAX_RETRIES} fallido para {url}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    raise ConnectionError(f"No se pudo conectar a {url} tras {MAX_RETRIES} intentos")


# ─── EURIBOR ────────────────────────────────────────────────────────────────────

EURIBOR_PERIODS = {
    "1 semana": "1_week",
    "1 mes": "1_month",
    "3 meses": "3_months",
    "6 meses": "6_months",
    "12 meses": "12_months",
}

ECB_LABELS = {
    "facilidad de depósito": "deposito",
    "depósito": "deposito",
    "operaciones principales": "operaciones",
    "refinanciación": "operaciones",
    "facilidad marginal": "marginal",
    "marginal de crédito": "marginal",
}


def fetch_euribor() -> dict | None:
    """Scrape current Euribor rates and ECB rates."""
    log.info("Descargando tasas Euribor...")
    try:
        resp = fetch_with_retry(EURIBOR_URL)
    except ConnectionError as e:
        log.error(str(e))
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    text_full = soup.get_text(separator="\n")

    # Parse Euribor rates by searching for period text patterns
    rates = {}
    for es_label, key in EURIBOR_PERIODS.items():
        pattern = re.compile(
            rf"eur[ií]bor\s+{re.escape(es_label)}\s*[:\-]?\s*([\-]?\d+[.,]\d+)\s*%",
            re.IGNORECASE,
        )
        match = pattern.search(text_full)
        if match:
            val = parse_es_float(match.group(1) + "%")
            if val is not None:
                rates[key] = val
                log.info(f"  Euribor {es_label}: {val}%")

    # Also try parsing from tables
    if len(rates) < 3:
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    for es_label, key in EURIBOR_PERIODS.items():
                        if es_label in label and key not in rates:
                            val = parse_es_float(cells[-1].get_text(strip=True))
                            if val is not None:
                                rates[key] = val
                                log.info(f"  Euribor {es_label} (tabla): {val}%")

    # Parse ECB rates
    ecb_rates = {}
    for pattern_label, key in ECB_LABELS.items():
        pattern = re.compile(
            rf"{re.escape(pattern_label)}[^0-9]*(\d+[.,]\d+)\s*%",
            re.IGNORECASE,
        )
        match = pattern.search(text_full)
        if match and key not in ecb_rates:
            val = parse_es_float(match.group(1) + "%")
            if val is not None:
                ecb_rates[key] = val

    if len(rates) < 3:
        log.error(f"Solo se encontraron {len(rates)} tasas Euribor (mínimo 3)")
        return None

    result = {
        "lastUpdated": datetime.now().isoformat(timespec="seconds"),
        "rates": rates,
        "ecb_rates": ecb_rates,
    }
    log.info(f"Euribor OK: {len(rates)} tasas, {len(ecb_rates)} tipos BCE")
    return result


# ─── BANK OFFERS ────────────────────────────────────────────────────────────────

# Map bank names to normalized display names
BANK_NORMALIZE = {
    "bróker hipoteca": "Broker",
    "bróker": "Broker",
    "broker": "Broker",
    "ibercaja": "Ibercaja",
    "pibank": "Pibank",
    "kutxabank": "Kutxabank",
    "banco sabadell": "Sabadell",
    "sabadell": "Sabadell",
    "banca march": "Banca March",
    "caixabank": "CaixaBank",
    "bbva": "BBVA",
    "openbank": "Openbank",
    "bankinter": "Bankinter",
    "ing": "ING",
    "unicaja": "Unicaja",
    "cajamar": "Cajamar",
    "abanca": "ABANCA",
    "coinc": "COINC",
    "laboral kutxa": "Laboral Kutxa",
    "imaginbank": "imaginBank",
    "santander": "Santander",
    "banco santander": "Santander",
    "caixa enginyers": "Caixa Enginyers",
    "myinvestor": "MyInvestor",
    "evo banco": "EVO Banco",
    "deutsche bank": "Deutsche Bank",
}


def normalize_bank(raw: str) -> str:
    """Normalize a bank name extracted from the page."""
    lower = raw.strip().lower()
    for key, val in BANK_NORMALIZE.items():
        if key in lower:
            return val
    return raw.strip().title()


def extract_conditions_from_bonif(bonif_desc: str) -> list[str]:
    """Extract bonding conditions from a bonificaciones description string."""
    conditions = []
    cond_patterns = [
        (r"n[oó]mina|[Dd]omiciliar", "Nómina"),
        (r"[Ss]eguro\s+de?\s*hogar", "Seguro hogar"),
        (r"[Ss]eguro\s+de?\s*vida", "Seguro vida"),
        (r"[Pp]lan\s+de?\s*pensiones", "Plan pensiones"),
        (r"[Tt]arjeta", "Tarjeta"),
        (r"[Ss]eguro\s+de?\s*protecci[oó]n", "Seguro protección"),
    ]
    for pat, label in cond_patterns:
        if re.search(pat, bonif_desc) and label not in conditions:
            conditions.append(label)
    return conditions if conditions else ["Consultar condiciones"]


def parse_product_cards(html: str) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Parse product cards from HelpMyCash's embedded JSON data.
    The page contains structured JSON blocks with brand, title, and sheetInfo
    for each mortgage offer, encoded with HTML entities.
    """
    from html import unescape
    text = unescape(html)

    fijo, variable, mixto = [], [], []
    seen = {"fixed": set(), "variable": set(), "mixed": set()}

    # Find each product card: "name":"BankName"},"title":"ProductTitle"...,"sheetInfo":{...}
    for m in re.finditer(r'"name":"([^"]+)"\},"title":"([^"]+)"', text):
        raw_bank = m.group(1).encode("raw_unicode_escape").decode("unicode_escape", errors="replace")
        title = m.group(2).encode("raw_unicode_escape").decode("unicode_escape", errors="replace")
        bank_name = normalize_bank(raw_bank)

        # Extract sheetInfo using brace counting (the block is a nested JSON object)
        after = text[m.end():m.end() + 4000]
        sheet_start = after.find('"sheetInfo":{')
        if sheet_start < 0:
            continue
        # Find matching closing brace
        brace_start = sheet_start + len('"sheetInfo":')
        depth = 0
        sheet_end = -1
        for i in range(brace_start, len(after)):
            if after[i] == "{":
                depth += 1
            elif after[i] == "}":
                depth -= 1
                if depth == 0:
                    sheet_end = i + 1
                    break
        if sheet_end < 0:
            continue
        sheet = after[brace_start:sheet_end]

        # Parse key fields
        tae_m = re.search(r'"tae":([\d.]+)', sheet)
        init_int_m = re.search(r'"initialInterest":([\d.]+)', sheet)
        after_int_m = re.search(r'"afterInterest":([\d.]+)', sheet)
        mtype_m = re.search(r'"mortgageType":"(\w+)"', sheet)
        vinc_m = re.search(r'"vinculaciones":(\d+)', sheet)
        bonif_m = re.search(r'"description":"([^"]+)"', sheet)
        init_term_m = re.search(r'"initialTerm":(\d+)', sheet)
        # "formattedAfterInterest":"E + 0,49%" contains the clean spread
        formatted_after_m = re.search(r'"formattedAfterInterest":"([^"]+)"', sheet)

        if not tae_m or not mtype_m or not init_int_m:
            continue

        tae = round(float(tae_m.group(1)), 2)
        tin_initial = round(float(init_int_m.group(1)), 2)
        tin_after = round(float(after_int_m.group(1)), 2) if after_int_m else 0
        mort_type = mtype_m.group(1)  # "fixed", "variable", "mixed"
        vinculaciones = int(vinc_m.group(1)) if vinc_m else 0
        init_term = int(init_term_m.group(1)) if init_term_m else 0  # months

        # Extract the spread from formatted field: "E + 0,49%" -> 0.49
        spread = None
        if formatted_after_m:
            spread_m = re.search(r"([\d,]+)%", formatted_after_m.group(1))
            if spread_m:
                spread = parse_es_float(spread_m.group(1) + "%")

        # Extract conditions from all bonificaciones descriptions
        bonif_descs = re.findall(r'"description":"([^"]+)"', sheet)
        bonif_desc = " ".join(bonif_descs)
        # Decode unicode escapes (e.g. \u00f3 -> ó) safely
        bonif_desc = re.sub(
            r"\\u([0-9a-fA-F]{4})",
            lambda m: chr(int(m.group(1), 16)),
            bonif_desc,
        )
        conditions = extract_conditions_from_bonif(bonif_desc)
        if vinculaciones == 0:
            conditions = ["Sin vinculaciones"]

        # Skip exact duplicates (same bank + same rate)
        dup_key = f"{bank_name}_{tin_initial}_{tae}_{mort_type}"
        if dup_key in seen[mort_type]:
            continue
        seen[mort_type].add(dup_key)

        if mort_type == "fixed":
            offer = {"banco": bank_name, "tin": tin_initial, "tae": tae, "condiciones": conditions}
            fijo.append(offer)
            log.info(f"  FIJO - {bank_name}: TIN={tin_initial}%, TAE={tae}%")

        elif mort_type == "variable":
            # Use the clean spread from formattedAfterInterest
            diferencial = spread if spread is not None else round(tin_after, 2)
            offer = {
                "banco": bank_name,
                "diferencial": diferencial,
                "tae": tae,
                "condiciones": conditions,
            }
            variable.append(offer)
            log.info(f"  VARIABLE - {bank_name}: E+{diferencial}%, TAE={tae}%")

        elif mort_type == "mixed":
            periodo_anos = max(1, init_term // 12) if init_term > 0 else 5
            diferencial = spread if spread is not None else round(tin_after, 2)
            offer = {
                "banco": bank_name,
                "tinFijo": tin_initial,
                "diferencial": diferencial,
                "periodoFijo": f"{periodo_anos} años",
                "tae": tae,
                "condiciones": conditions,
            }
            mixto.append(offer)
            log.info(f"  MIXTO - {bank_name}: TIN fijo={tin_initial}%, E+{diferencial}%, {periodo_anos} años, TAE={tae}%")

    return fijo, variable, mixto


def fetch_bank_offers() -> dict | None:
    """Scrape current bank mortgage offers from HelpMyCash."""
    log.info("Descargando ofertas bancarias...")
    try:
        resp = fetch_with_retry(HELPMYCASH_URL)
    except ConnectionError as e:
        log.error(str(e))
        return None

    fijo, variable, mixto = parse_product_cards(resp.text)

    # Sort by best rate
    fijo.sort(key=lambda x: x.get("tin", 99))
    variable.sort(key=lambda x: x.get("diferencial", 99))
    mixto.sort(key=lambda x: x.get("tinFijo", 99))

    total = len(fijo) + len(variable) + len(mixto)
    if total < 3:
        log.error(f"Solo se encontraron {total} ofertas totales (mínimo 3)")
        return None

    now = datetime.now()
    meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    result = {
        "lastUpdated": f"{meses[now.month]} {now.year}",
        "fetchDate": now.isoformat(timespec="seconds"),
        "source": "helpmycash.com",
        "fijo": fijo,
        "variable": variable,
        "mixto": mixto,
    }
    log.info(f"Ofertas OK: {len(fijo)} fijo, {len(variable)} variable, {len(mixto)} mixto")
    return result


# ─── SAVE ────────────────────────────────────────────────────────────────────────

def save_json(data: dict, filepath: Path):
    """Save JSON with backup of previous version."""
    if filepath.exists():
        backup = filepath.with_suffix(".backup.json")
        shutil.copy2(filepath, backup)
        log.info(f"Backup: {backup}")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    log.info(f"Guardado: {filepath}")


# ─── MAIN ────────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info(f"Inicio actualización: {datetime.now().isoformat()}")
    log.info("=" * 60)

    DATA_DIR.mkdir(exist_ok=True)
    exit_code = 0

    # Fetch Euribor
    euribor_data = fetch_euribor()
    if euribor_data:
        save_json(euribor_data, DATA_DIR / "euribor.json")
    else:
        log.error("FALLO: No se pudieron obtener tasas Euribor")
        exit_code = 1

    # Fetch bank offers
    offers_data = fetch_bank_offers()
    if offers_data:
        save_json(offers_data, DATA_DIR / "bank_offers.json")
    else:
        log.error("FALLO: No se pudieron obtener ofertas bancarias")
        exit_code = max(exit_code, 1)

    if exit_code == 0:
        log.info("Actualización completada con éxito")
    else:
        log.warning("Actualización completada con errores parciales")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
