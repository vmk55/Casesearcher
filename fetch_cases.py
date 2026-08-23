import os, io, json, zipfile, requests, traceback
import xml.etree.ElementTree as ET

ZIP_URL = os.environ.get("EDRSR_ZIP_URL", "")
PARTY_KEYWORD = "київводоканал"
PROCEEDING_FILTER = "цивільне"
OUTPUT_FILE = "cases.json"
LOG_FILE = "log.txt"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def download_archive(url):
    resp = requests.get(url, timeout=600, stream=True)
    resp.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(resp.content))

def parse_record(xml_bytes, debug_capture):
    root = ET.fromstring(xml_bytes)
    def find_text(*tags):
        for tag in tags:
            el = root.find(f".//{tag}")
            if el is not None and el.text:
                return el.text.strip()
        return ""
    proceeding = find_text("JUSTICE_KIND", "FORM_OF_PROCEEDING", "JusticeKind")
    doc_type = find_text("DOC_TYPE", "JUDGMENT_FORM", "DocForm")
    court = find_text("COURT_NAME", "CourtName")
    judge = find_text("JUDGE", "Judge")
    case_no = find_text("CASE_NUMBER", "CauseNumber", "DOC_NUMBER")
    date = find_text("ADJUDICATION_DATE", "DATE", "AdjudicationDate")
    text_body = find_text("TEXT", "DOC_TEXT", "Body")
    plaintiff = find_text("PLAINTIFF", "Claimant")
    defendant = find_text("DEFENDANT", "Respondent")

    if debug_capture["done"] is False:
        debug_capture["done"] = True
        debug_capture["raw"] = xml_bytes[:2000].decode("utf-8", errors="replace")

    haystack = f"{text_body} {plaintiff} {defendant}".lower()
    if PARTY_KEYWORD not in haystack:
        return None
    if proceeding and PROCEEDING_FILTER not in proceeding.lower():
        return None
    idx = haystack.find(PARTY_KEYWORD)
    snippet = text_body[max(0, idx-150): idx+250] if text_body else ""
    return {"case_no": case_no, "court": court, "judge": judge, "proceeding": proceeding or "Цивільне",
            "doc_type": doc_type, "decision_date": date, "plaintiff": plaintiff,
            "defendant": defendant, "snippet": snippet}

def main():
    open(LOG_FILE, "w", encoding="utf-8").close()

    log(f"Старт. ZIP_URL заданий: {'так' if ZIP_URL else 'НІ — секрет порожній!'}")
    if not ZIP_URL:
        log("ПОМИЛКА: змінна EDRSR_ZIP_URL порожня. Перевірте секрет у Settings -> Secrets -> Actions.")
        return

    log(f"ZIP_URL (перші 60 символів): {ZIP_URL[:60]}")
    log("Завантажую архів...")
    archive = download_archive(ZIP_URL)
    names = [n for n in archive.namelist() if n.lower().endswith(".xml")]
    log(f"Файлів у архіві: {len(names)}")

    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    known_numbers = {r["case_no"] for r in existing}

    debug_capture = {"done": False, "raw": ""}
    matched = []
    for name in names:
        with archive.open(name) as f:
            raw = f.read()
        try:
            record = parse_record(raw, debug_capture)
        except ET.ParseError:
            continue
        if record and record["case_no"] and record["case_no"] not in known_numbers:
            matched.append(record)
            known_numbers.add(record["case_no"])

    log("---- ПРИКЛАД СИРОГО XML (перший запис у архіві) ----")
    log(debug_capture["raw"])
    log("-----------------------------------------------------")

    log(f"Нових знайдено: {len(matched)}")
    all_records = existing + matched
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    log(f"Всього в базі: {len(all_records)}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n---- ПОМИЛКА ----\n")
            f.write(traceback.format_exc())
        print("Сталася помилка, деталі в log.txt")
