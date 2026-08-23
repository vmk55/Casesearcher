import os, io, zipfile, requests
url = os.environ["EDRSR_ZIP_URL"]
r = requests.get(url, timeout=600)
z = zipfile.ZipFile(io.BytesIO(r.content))
names = z.namelist()
with open("log.txt", "w", encoding="utf-8") as f:
    f.write(f"Всього: {len(names)}\n" + "\n".join(names[:40]))
