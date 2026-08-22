import os, io, zipfile, requests
import xml.etree.ElementTree as ET

ZIP_URL = os.environ["EDRSR_ZIP_URL"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
PARTY_KEYWORD = "київводоканал"
PROCEEDING_FILTER = "цивільне"
RAW_DEBUG = os.environ.get("RAW_DEBUG", "0") == "1"

def download_archive(url):
    resp = requests.get(url, timeout=600, stream=True)
    resp.raise_for_status()
    return zipfile.ZipFile(io.BytesIO(resp.content))

def parse_record(xml_bytes):
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
    if RAW_DEBUG:
        print("---- RAW XML ----")
        print(xml_bytes[:3000])
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

def upload_to_supabase(records):
    if not records:
        return
    url = f"{SUPABASE_URL}/rest/v1/cases"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
               "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
    resp = requests.post(url, headers=headers, json=records, timeout=60)
    print(f"Supabase: {resp.status_code}, {len(records)} записів")
    if resp.status_code >= 400:
        print(resp.text[:1000])

def main():
    archive = download_archive(ZIP_URL)
    names = [n for n in archive.namelist() if n.lower().endswith(".xml")]
    print(f"Файлів у архіві: {len(names)}")
    matched = []
    for name in names:
        with archive.open(name) as f:
            raw = f.read()
        try:
            record = parse_record(raw)
        except ET.ParseError:
            continue
        if record and record["case_no"]:
            matched.append(record)
    print(f"Знайдено: {len(matched)}")
    for i in range(0, len(matched), 200):
        upload_to_supabase(matched[i:i+200])

if __name__ == "__main__":
    main()
