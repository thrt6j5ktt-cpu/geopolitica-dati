"""
Acquisizione locale — UST/BFS (frontalieri)

Perché in locale: Databricks Free Edition blocca le connessioni verso
siti esterni non autorizzati, quindi il download si fa sul tuo PC e il file
si carica poi nel volume Databricks (livello Bronze).

Uso:  python scarica_bfs.py
Output: cartella ./bronze/bfs/<TABLE_ID>/metadata/ con
        <timestamp>_metadata.json e <timestamp>_provenance.json
"""
import os
import json
import hashlib
import datetime as dt
import urllib.request

TABLE_ID = "px-x-0302010000_105"
LANG = "it"
URL = f"https://www.pxweb.bfs.admin.ch/api/v1/{LANG}/{TABLE_ID}/{TABLE_ID}.px"
OUT_DIR = os.path.join("bronze", "bfs", TABLE_ID, "metadata")


def main():
    # 1. Download (urllib è nella libreria standard: niente da installare)
    with urllib.request.urlopen(URL, timeout=60) as r:
        status = r.status
        raw = r.read()
    print("Codice HTTP:", status)

    # 2. Salvataggio del file originale + provenienza
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(OUT_DIR, exist_ok=True)
    meta_path = os.path.join(OUT_DIR, f"{ts}_metadata.json")
    with open(meta_path, "wb") as f:
        f.write(raw)
    prov = {
        "source": "UST/BFS STAT-TAB PxWeb API v1",
        "table_id": TABLE_ID,
        "url": URL,
        "retrieved_at_utc": ts,
        "http_status": status,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    with open(os.path.join(OUT_DIR, f"{ts}_provenance.json"), "w") as f:
        json.dump(prov, f, indent=2)

    # 3. Riepilogo da incollare in chat
    meta = json.loads(raw)
    print("TITOLO:", meta.get("title"))
    tot = 1
    for v in meta["variables"]:
        tot *= len(v["values"])
        print(f"{v['code']} | {v['text']} | {len(v['values'])} valori")
        print("   primi :", list(zip(v["values"][:4], v["valueTexts"][:4])))
        print("   ultimi:", list(zip(v["values"][-4:], v["valueTexts"][-4:])))
    print(f"Celle totali: {tot:,}")
    print(f"\nFile salvati in: {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    main()
