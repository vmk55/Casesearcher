import os, io, zipfile, requests
url = os.environ["EDRSR_ZIP_URL"]
r = requests.get(url, timeout=600)
z = zipfile.ZipFile(io.BytesIO(r.content))
with z.open("cause_categories.csv") as f:
    text = f.read().decode("utf-8", errors="replace")
keywords = ["заборгован", "комунальн", "водопостачання", "водовідведення", "оплату послуг", "надані послуги"]
lines = [l for l in text.splitlines() if any(k in l.lower() for k in keywords)]
with open("log.txt", "w", encoding="utf-8") as f:
    f.write(f"Знайдено рядків: {len(lines)}\n\n" + "\n".join(lines))
