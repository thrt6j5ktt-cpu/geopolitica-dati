"""
Acquisizione UST/BFS — Frontalieri stranieri (Swiss Stats Explorer, SDMX)
Eseguito da GitHub Actions, non sul PC.

Fonte: UST, dataflow DF_GGS_1 (agenzia CH1.GGS)
"Frontalieri stranieri secondo il Cantone di lavoro, l'attività economica,
il Paese di residenza e il sesso" — trimestrale dal 2002.
Sostituisce la vecchia tabella PX px-x-0302010000_105, interrotta al 3° trim. 2025.

Salva nel livello Bronze (mai modificati):
  bronze/bfs_sse/DF_GGS_1/<timestamp>_struttura.json   -> dimensioni e codici
  bronze/bfs_sse/DF_GGS_1/<timestamp>_<estrazione>.csv.gz -> dati filtrati, con etichette
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
# La chiave filtra le dimensioni nell'ordine NOGA.CNTRY.FREQ.SEX.WORK_CANTON
# (vuoto = tutti i valori). Scaricare "all" produce oltre 6 GB: filtriamo.
SEZIONI = "_T+1+2+3+A+B+C+D+E+F+G+H+I+J+K+L+M+N+O+P+Q+R+S+T+U"   # totale, 3 settori, 21 sezioni NOGA
CANTONI_FOCUS = "21+18+23+25+22+_T"                             # TI, GR, VS, GE, VD, Svizzera
QUERY = {
    # A) Totale economia, per Paese di residenza e per TUTTI i cantoni
    "totale_per_cantone": "_T.IT+FR+DE+AT+_T.Q._T.",
    # B) Per settore/sezione economica, nei cantoni di confine con Italia e Francia
    "settori_cantoni_confine": f"{SEZIONI}.IT+FR+_T.Q._T.{CANTONI_FOCUS}",
}
URL_DATI = {nome: f"{BASE}/data/{AGENCY},{DATAFLOW},{VERSION}/{chiave}"
                  "?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
            for nome, chiave in QUERY.items()}
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
        with urllib.request.urlopen(req, timeout=600) as r:
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

    # 2. Dati filtrati (due estrazioni)
    prov = {
        "fonte": "UST/BFS — Swiss Stats Explorer (SDMX REST)",
        "dataflow": f"{AGENCY}:{DATAFLOW}({VERSION})",
        "url_struttura": URL_STRUTTURA,
        "scaricato_utc": ts,
        "licenza": "OGD UST: uso libero con citazione della fonte; uso commerciale previo consenso",
        "estrazioni": {},
    }
    for nome, url in URL_DATI.items():
        s, raw = get(url, "text/csv")
        print(f"\n[{nome}] codice HTTP: {s} | dimensione: {len(raw)/1e6:.2f} MB")
        if s != 200:
            print("Risposta:", raw[:500].decode("utf-8", "replace"))
            sys.exit(1)
        with gzip.open(os.path.join(OUT_DIR, f"{ts}_{nome}.csv.gz"), "wb") as f:
            f.write(raw)
        prov["estrazioni"][nome] = {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "byte": len(raw)}

        righe = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"))))
        intest, dati = righe[0], righe[1:]
        print("COLONNE:", intest)
        print("RIGHE DI DATI:", len(dati))
        for r in dati[:2]:
            print("ESEMPIO:", r)
        tcol = next((i for i, c in enumerate(intest) if c.startswith("TIME_PERIOD")), None)
        if tcol is not None and dati:
            periodi = sorted({r[tcol] for r in dati if len(r) > tcol})
            print("PERIODO:", periodi[0], "->", periodi[-1], f"({len(periodi)} trimestri)")

    # 3. Provenienza
    with open(os.path.join(OUT_DIR, f"{ts}_provenance.json"), "w") as f:
        json.dump(prov, f, indent=2, ensure_ascii=False)
    print("\nOK: file salvati in", OUT_DIR)


if __name__ == "__main__":
    main()
