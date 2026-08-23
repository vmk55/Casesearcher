import os, io, csv, json, zipfile, requests, time
from striprtf.striprtf import rtf_to_text

ZIP_URL = os.environ["EDRSR_ZIP_URL"]
KEYWORD = "київводоканал"
TARGET_CATS = {"10260", "10300", "40394", "13519"}
OUTPUT_FILE = "cases.json"
LOG_FILE = "log.txt"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

def load_lookup(z, name, key_idx=0, val_idx=1):
    d = {}
    with z.open(name) as f:
        reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        next(reader)
        for row in reader:
            if len(row) > max(key_idx, val_idx):
                d[row[key_idx]] = row[val_idx]
    return d

def main():
    open(LOG_FILE, "w", encoding="utf-8").close()
    log("Завантажую архів...")
    r = requests.get(ZIP_URL, timeout=600)
    z = zipfile.ZipFile(io.BytesIO(r.content))

    courts = load_lookup(z, "courts.csv")
    with z.open("courts.csv") as f:
        reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        next(reader)
        kyiv_courts = {row[0] for row in reader if len(row) > 3 and row[3] == "26"}
    judgment_forms = load_lookup(z, "judgment_forms.csv")
    cause_categories = load_lookup(z, "cause_categories.csv")

    candidates = []
    with z.open("documents.csv") as f:
        reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
        next(reader)
        for row in reader:
            if len(row) < 10:
                continue
            if row[3] == "1" and row[1] in kyiv_courts and row[4] in TARGET_CATS:
                candidates.append(row)

    log(f"Кандидатів для перевірки: {len(candidates)}")

    existing = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)
    known = {r["case_no"] for r in existing}

    matched = []
    errors = 0
    for i, row in enumerate(candidates):
        doc_id, court_code, judgment_code, justice_kind, category_code, cause_num, adj_date, receipt_date, judge, doc_url = row[:10]
        if cause_num in known:
            continue
        if i % 200 == 0:
            log(f"Оброблено {i}/{len(candidates)}, знайдено {len(matched)}")
        try:
            resp = requests.get(doc_url, timeout=20)
            text = rtf_to_text(resp.content.decode("cp1251", errors="replace"))
        except Exception:
            errors += 1
            continue
        low = text.lower()
        if KEYWORD not in low:
            continue
        idx = low.find(KEYWORD)
        snippet = text[max(0, idx-150): idx+250]
        matched.append({
            "case_no": cause_num,
            "court": courts.get(court_code, court_code),
            "judge": judge,
            "proceeding": "Цивільне",
            "doc_type": judgment_forms.get(judgment_code, judgment_code),
            "decision_date": adj_date,
            "category": cause_categories.get(category_code, category_code),
            "snippet": snippet,
            "source_url": doc_url,
        })
        known.add(cause_num)

    log(f"Помилок завантаження: {errors}")
    log(f"Нових знайдено: {len(matched)}")
    all_records = existing + matched
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, indent=2)
    log(f"Всього в базі: {len(all_records)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n---- ПОМИЛКА ----\n")
            f.write(traceback.format_exc())
