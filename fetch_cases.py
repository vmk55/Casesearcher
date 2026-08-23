import os, io, zipfile, requests, csv
url = os.environ["EDRSR_ZIP_URL"]
r = requests.get(url, timeout=600)
z = zipfile.ZipFile(io.BytesIO(r.content))

with z.open("courts.csv") as f:
    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
    next(reader)
    kyiv_courts = {row[0] for row in reader if len(row) > 3 and row[3] == "26"}

target_cats = {"10260", "10300", "40394", "13519"}
count = 0
with z.open("documents.csv") as f:
    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
    next(reader)
    for row in reader:
        if len(row) < 5:
            continue
        if row[3] == "1" and row[1] in kyiv_courts and row[4] in target_cats:
            count += 1

with open("log.txt", "w", encoding="utf-8") as f:
    f.write(f"Цивільних, Київ, категорії боргу за послуги: {count}\n")
