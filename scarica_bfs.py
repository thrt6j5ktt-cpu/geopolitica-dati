"""
Acquisizione UST/BFS (frontalieri) — eseguito da GitHub Actions, non sul PC.

Versione 2: se l'UST rifiuta la richiesta, lo script non si limita a fallire
ma stampa la risposta dell'UST e l'elenco delle tabelle "frontalieri" che
l'API conosce davvero, così capiamo subito il codice tabella corretto.
"""
import os
import sys
import json
import hashlib
import datetime as dt
import urllib.request
import urllib.error

TABLE_ID = "px-x-0302010000_105"
LANG = "it"
BASE = "https://www.pxweb.bfs.admin.ch/api/v1"
URL = f"{BASE}/{LANG}/{TABLE_ID}/{TABLE_ID}.px"
OUT_DIR = os.path.join("bronze", "bfs", TABLE_ID, "metadata")
HEADERS = {"User-Agent": "geopolitica-dati/1.0 (GitHub Actions)", "Accept": "application/json"}


def get(url):
    """Esegue una GET e restituisce (codice HTTP, contenuto in byte)."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def diagnostica():
    """Elenca le tabelle disponibili che riguardano i frontalieri (codici px-x-03020...)."""
    print("\n--- DIAGNOSTICA: tabelle frontalieri disponibili nell'API ---")
    status, body = get(f"{BASE}/{LANG}/")
    print("Elenco tabelle, codice HTTP:", status)
    try:
        items = json.loads(body)
    except ValueError:
        print("Risposta non leggibile:", body[:500])
        return
    print("Struttura dei primi 3 elementi:")
    for i in items[:3]:
        print("  ", json.dumps(i, ensure_ascii=False))
    parole = ("frontal", "0302", "grenzg")
    trovate = [i for i in items
               if any(p in json.dumps(i, ensure_ascii=False).lower() for p in parole)]
    for i in trovate:
        print("TROVATA:", json.dumps(i, ensure_ascii=False))
    print(f"Tabelle frontalieri trovate: {len(trovate)} (su {len(items)} totali)")


def main():
    status, raw = get(URL)
    print("Codice HTTP:", status)
    if status != 200:
        print("Risposta dell'UST:", raw[:500].decode("utf-8", "replace"))
        diagnostica()
        sys.exit(1)

    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, f"{ts}_metadata.json"), "wb") as f:
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

    meta = json.loads(raw)
    print("TITOLO:", meta.get("title"))
    tot = 1
    for v in meta["variables"]:
        tot *= len(v["values"])
        print(f"{v['code']} | {v['text']} | {len(v['values'])} valori")
        print("   primi :", list(zip(v["values"][:4], v["valueTexts"][:4])))
        print("   ultimi:", list(zip(v["values"][-4:], v["valueTexts"][-4:])))
    print(f"Celle totali: {tot:,}")


if __name__ == "__main__":
    main()
