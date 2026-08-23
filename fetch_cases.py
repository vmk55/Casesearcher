import os, io, zipfile, requests
url = os.environ["EDRSR_ZIP_URL"]
r = requests.get(url, timeout=600)
z = zipfile.ZipFile(io.BytesIO(r.content))
out = []
for name in ["documents.csv", "courts.csv", "justice_kinds.csv", "judgment_forms.csv", "cause_categories.csv"]:
    with z.open(name) as f:
        lines = [f.readline().decode("utf-8", errors="replace") for _ in range(3)]
    out.append(f"==== {name} ====\n" + "".join(lines))
with open("log.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
