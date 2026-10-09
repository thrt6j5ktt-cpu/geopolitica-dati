"""
Acquisizione UST/BFS — Frontalieri stranieri (Swiss Stats Explorer, SDMX)
Eseguito da GitHub Actions, non sul PC.

Fonte: UST, dataflow DF_GGS_1 (agenzia CH1.GGS)
"Frontalieri stranieri secondo il Cantone di lavoro, l'attività economica,
il Paese di residenza e il sesso" — trimestrale dal 2002.
Sostituisce la vecchia tabella PX px-x-0302010000_105, interrotta al 3° trim. 2025.

Salva nel livello Bronze (mai modificati):
  bronze/bfs_sse/DF_GGS_1/<timestamp>_struttura.json   -> dimensioni e codici
  bronze/bfs_sse/DF_GGS_1/<timestamp>_dati.csv.gz      -> tutti i dati, con etichette
  bronze/bfs_sse/DF_GGS_1/<timestamp>_provenance.json  -> da dove, quando, impronta
"""
import os
import sys
import csv
import io
import gzip
import json
import hashlib
import datetime as dt
import urllib.request
import urllib.error

AGENCY = "CH1.GGS"
DATAFLOW = "DF_GGS_1"
VERSION = "1.0.0"
BASE = "https://disseminate.stats.swiss/rest"
URL_DATI = (f"{BASE}/data/{AGENCY},{DATAFLOW},{VERSION}/all"
            "?dimensionAtObservation=AllDimensions&format=csvfilewithlabels")
URL_STRUTTURA = (f"{BASE}/v2/structure/dataflow/{AGENCY}/{DATAFLOW}/{VERSION}"
                 "?references=all&detail=referencepartial")
OUT_DIR = os.path.join("bronze", "bfs_sse", DATAFLOW)


def get(url, accept):
    req = urllib.request.Request(url, headers={
        "User-Agent": "geopolitica-dati/1.0 (GitHub Actions)",
        "Accept": accept,
        "Accept-Language": "it",
    })
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def main():
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    os.makedirs(OUT_DIR, exist_ok=True)

    # 1. Struttura (quali dimensioni e codici esistono)
    st_s, st_raw = get(URL_STRUTTURA, "application/vnd.sdmx.structure+json; charset=utf-8; version=1.0")
    print("Struttura, codice HTTP:", st_s)
    if st_s != 200:
        print("Risposta:", st_raw[:500].decode("utf-8", "replace"))
        sys.exit(1)
    with open(os.path.join(OUT_DIR, f"{ts}_struttura.json"), "wb") as f:
        f.write(st_raw)

    # 2. Dati completi in CSV con etichette
    d_s, d_raw = get(URL_DATI, "text/csv")
    print("Dati, codice HTTP:", d_s, "| dimensione:", f"{len(d_raw)/1e6:.1f} MB")
    if d_s != 200:
        print("Risposta:", d_raw[:500].decode("utf-8", "replace"))
        sys.exit(1)
    with gzip.open(os.path.join(OUT_DIR, f"{ts}_dati.csv.gz"), "wb") as f:
        f.write(d_raw)

    # 3. Provenienza
    prov = {
        "fonte": "UST/BFS — Swiss Stats Explorer (SDMX REST)",
        "dataflow": f"{AGENCY}:{DATAFLOW}({VERSION})",
        "url_dati": URL_DATI,
        "url_struttura": URL_STRUTTURA,
        "scaricato_utc": ts,
        "sha256_dati": hashlib.sha256(d_raw).hexdigest(),
        "byte_dati": len(d_raw),
        "licenza": "OGD UST: uso libero con citazione della fonte; uso commerciale previo consenso",
    }
    with open(os.path.join(OUT_DIR, f"{ts}_provenance.json"), "w") as f:
        json.dump(prov, f, indent=2, ensure_ascii=False)

    # 4. Riepilogo da incollare in chat
    righe = list(csv.reader(io.StringIO(d_raw.decode("utf-8-sig"))))
    intest, dati = righe[0], righe[1:]
    print("\nCOLONNE:", intest)
    print("RIGHE DI DATI:", len(dati))
    for r in dati[:3]:
        print("ESEMPIO:", r)
    tcol = next((i for i, c in enumerate(intest) if c.startswith("TIME_PERIOD")), None)
    if tcol is not None:
        periodi = sorted({r[tcol] for r in dati if len(r) > tcol})
        print("PERIODO:", periodi[0], "->", periodi[-1], f"({len(periodi)} trimestri)")


if __name__ == "__main__":
    main()
