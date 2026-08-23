import os, io, zipfile, requests, csv
url = os.environ["EDRSR_ZIP_URL"]
r = requests.get(url, timeout=600)
z = zipfile.ZipFile(io.BytesIO(r.content))

with z.open("courts.csv") as f:
    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
    header = next(reader)
    kyiv_courts = {row[0] for row in reader if len(row) > 3 and row[3] == "26"}

count_civil_kyiv = 0
count_civil_total = 0
with z.open("documents.csv") as f:
    reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"), delimiter="\t")
    header = next(reader)
    for row in reader:
        if len(row) < 4:
            continue
        if row[3] == "1":
            count_civil_total += 1
            if row[1] in kyiv_courts:
                count_civil_kyiv += 1

with open("log.txt", "w", encoding="utf-8") as f:
    f.write(f"Судів у Києві (код 26): {len(kyiv_courts)}\n")
    f.write(f"Усього цивільних справ у архіві: {count_civil_total}\n")
    f.write(f"З них у судах Києва: {count_civil_kyiv}\n")
