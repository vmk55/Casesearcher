import os, io, zipfile, requests, csv
url = os.environ["EDRSR_ZIP_URL"]
r = requests.get(url, timeout=600)
z = zipfile.ZipFile(io.BytesIO(r.content))
out = []
for name in ["justice_kinds.csv", "judgment_forms.csv", "regions.csv"]:
    with z.open(name) as f:
        text = f.read().decode("utf-8", errors="replace")
    out.append(f"==== {name} ====\n{text}")
with z.open("courts.csv") as f:
    kyiv = [l for l in f.read().decode("utf-8", errors="replace").splitlines() if "Київ" in l][:20]
out.append("==== courts.csv (Київ) ====\n" + "\n".join(kyiv))
with open("log.txt", "w", encoding="utf-8") as f:
    f.write("\n\n".join(out))
