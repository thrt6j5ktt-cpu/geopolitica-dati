# Geopolitica & Dati — Svizzera e Italia

Sistema di analisi geopolitica basato su dati ufficiali, automatizzato e verificabile.
Ogni numero pubblicato deve poter essere ricondotto alla sua fonte, alla data di download e al codice che lo ha calcolato.

**Autore:** Luca Tarantino
**Documentazione completa (diario, decisioni, errori):** [DOCUMENTAZIONE.md](DOCUMENTAZIONE.md)

---

## Progetto 1 — Frontalieri italiani in Svizzera

**Domanda di ricerca**
> Dopo il nuovo accordo fiscale italo-svizzero (in vigore dal 17.7.2023, applicato dal 1.1.2024), il frontalierato italiano verso la Svizzera ha cambiato traiettoria? In quali cantoni e settori? Che cosa significa per i rapporti di forza lungo il confine insubrico?

**Prodotti finali previsti:** articolo LinkedIn + paper in PDF.

---

## Come funziona (architettura)

```
 UST / Swiss Stats Explorer (dati ufficiali, API SDMX)
            │  1° di ogni mese, automatico
            ▼
 GitHub Actions  ──►  scarica_bfs.py  ──►  bronze/  (dati grezzi, mai modificati)
            │
            ▼  Git folder (Pull)
 Databricks Free Edition
   02_silver_frontalieri  ──►  tabelle Silver (pulite + controlli qualità)
   03_gold_...            ──►  tabelle Gold (indicatori)            [da fare]
            │
            ▼
 Grafici  ──►  Articolo LinkedIn + Paper PDF                       [da fare]
```

| Livello | Dove | Contenuto |
|---|---|---|
| **Bronze** | GitHub, cartella `bronze/` | File originali UST, uno per download, con provenienza e impronta SHA-256 |
| **Silver** | Databricks, `workspace.frontalieri.silver_*` | Dati puliti, nomi italiani, controlli di qualità superati |
| **Gold** | Databricks, `workspace.frontalieri.gold_*` | Indicatori per grafici e articolo *(da fare)* |

---

## Struttura del repository

```
geopolitica-dati/
├── README.md                          questo file
├── DOCUMENTAZIONE.md                  diario dei lavori, decisioni, errori e soluzioni
├── scarica_bfs.py                     download dati UST (eseguito da GitHub, non sul PC)
├── 02_silver_frontalieri.ipynb        notebook Databricks: Bronze → Silver
├── .github/workflows/scarica_bfs.yml  il "robot": quando eseguire il download
└── bronze/bfs_sse/DF_GGS_1/           dati grezzi scaricati
```

---

## Come si aggiorna

1. **Automatico:** il 1° di ogni mese alle 06:00 UTC GitHub scarica i dati nuovi in `bronze/`.
2. **Manuale (se serve subito):** GitHub → *Actions* → *Scarica dati UST* → *Run workflow*.
3. **In Databricks:** nel Git folder `geopolitica-dati` → *Pull* → aprire `02_silver_frontalieri` → *Run all*.

---

## Stato del progetto

| Fase | Stato |
|---|---|
| 1. Definizione della domanda | completata |
| 2. Fattibilità (fonti, costi, strumenti) | completata |
| 3. Progettazione (architettura Bronze/Silver/Gold) | completata |
| 4. Implementazione — acquisizione automatica (Bronze) | **verificata** (9.10.2026) |
| 4. Implementazione — pulizia (Silver) | in corso |
| 4. Implementazione — indicatori (Gold) | non iniziata |
| 5–8. Validazione, analisi, grafici, consegna | non iniziate |
| 9–10. Riutilizzo e manutenzione | aggiornamento mensile già attivo |

---

## Fonti e licenza dei dati

Dati: **Ufficio federale di statistica (UST/BFS)**, statistica dei frontalieri (dataflow `CH1.GGS:DF_GGS_1`).
Uso libero con citazione della fonte; uso commerciale previo consenso dell'UST.
Dettagli in [DOCUMENTAZIONE.md](DOCUMENTAZIONE.md#2-fonti).

**Costi del sistema: 0 CHF** (GitHub pubblico + Databricks Free Edition).
