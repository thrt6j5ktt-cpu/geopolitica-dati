# Documentazione — Progetto 1: Frontalieri italiani in Svizzera

Documento di lavoro: si aggiorna a ogni blocco completato.
Serve a tre cose: capire cosa è stato fatto e perché, ripetere il lavoro, riprendere il progetto in una nuova sessione.

**Ultimo aggiornamento:** 9 ottobre 2026

## Indice
1. [Domanda di ricerca e perimetro](#1-domanda-di-ricerca-e-perimetro)
2. [Fonti](#2-fonti)
3. [Decisioni di architettura e motivazioni](#3-decisioni-di-architettura-e-motivazioni)
4. [Pipeline dei dati](#4-pipeline-dei-dati)
5. [Diario dei lavori](#5-diario-dei-lavori)
6. [Errori incontrati e soluzioni](#6-errori-incontrati-e-soluzioni)
7. [Note metodologiche](#7-note-metodologiche)
8. [Costi](#8-costi)
9. [Prossimi passi](#9-prossimi-passi)

---

## 1. Domanda di ricerca e perimetro

**Domanda:** dopo il nuovo accordo fiscale italo-svizzero, il frontalierato italiano verso la Svizzera ha cambiato traiettoria? In quali cantoni e settori? Che cosa significa per i rapporti di forza lungo il confine insubrico?

**Contesto (da verificare su fonti ufficiali prima della pubblicazione):**
- Nuovo accordo in vigore dal 17.7.2023, applicato dal 1.1.2024; sostituisce l'accordo del 1974.
- "Nuovi frontalieri": la Svizzera trattiene l'80% dell'imposta alla fonte, tassazione anche in Italia.
- "Vecchi frontalieri" (TI, GR, VS): tassazione solo in Svizzera; ristorno del 40% ai comuni italiani di confine fino al 2033.
- 2026: tensioni sui ristorni (governo ticinese), riforma UE sui frontalieri disoccupati (fonte: RSI, da verificare).

**Metodo previsto:** confronto prima/dopo il 2023 dei frontalieri residenti in Italia (TI, GR, VS) con un gruppo di controllo non toccato dall'accordo (frontalieri residenti in Francia a GE e VD), totale e per settore economico.

**Limiti dichiarati:**
- I dati UST sono uno **stock** (persone con permesso G attive), non flussi di entrate/uscite.
- I dati **non distinguono** vecchi e nuovi frontalieri fiscali.
- Si potranno mostrare **associazioni temporali**, non dimostrare che la causa sia l'accordo. Altri fattori da considerare: cambio CHF/EUR, mercato del lavoro lombardo, congiuntura ticinese, telelavoro.

---

## 2. Fonti

### Fonte principale (dati)

| Campo | Valore |
|---|---|
| Ente | Ufficio federale di statistica (UST/BFS) |
| Statistica | Statistica dei frontalieri (GGS) |
| Dataset | `CH1.GGS:DF_GGS_1`, versione 1.0.0 — "Frontalieri stranieri secondo il Cantone di lavoro, l'attività economica, il Paese di residenza e il sesso" |
| Piattaforma | Swiss Stats Explorer, API SDMX REST: `https://disseminate.stats.swiss/rest` |
| Dimensioni (ordine della chiave) | `NOGA` . `CNTRY` . `FREQ` . `SEX` . `WORK_CANTON` (+ `TIME_PERIOD`) |
| Frequenza | Trimestrale, dal 3° trimestre 2002 |
| Ultimo dato al 9.10.2026 | 2° trimestre 2026 |
| Licenza | Uso libero con citazione della fonte; uso commerciale previo consenso UST |
| Accesso | Gratuito, senza chiave API |

**Codici utili:** cantoni `21` Ticino, `18` Grigioni, `23` Vallese, `25` Ginevra, `22` Vaud, `_T` Svizzera. Paesi `IT`, `FR`, `DE`, `AT`, `_T` totale. NOGA `_T` totale, `1`/`2`/`3` settori primario/secondario/terziario, `A`–`U` sezioni economiche.

**Fonte sostituita:** la tabella PX `px-x-0302010000_105` (STAT-TAB) **non è disponibile nell'API PxWeb ed è stata interrotta al 3° trimestre 2025**. Non usarla.

**Verifica di coerenza fatta:** valori 2° trim. 2026 dall'API = cifre ufficiali pubblicate (Svizzera 414'262; Ticino 79'121).

### Fonti di contesto consultate (secondarie)
- RSI, "Aumento dei frontalieri attivi in Svizzera" (agosto 2026)
- Tio.ch, "Frontalieri, calano ancora in Ticino" (agosto 2026)
- Swissinfo / Keystone-ATS, "Cala il numero dei frontalieri italiani" (agosto 2026)
- Espansione TV, entrata in vigore dell'accordo (luglio 2023)
- Cantone Ticino, Divisione delle contribuzioni, "Definizione di vecchi frontalieri, nuovi frontalieri" (febbraio 2024)

---

## 3. Decisioni di architettura e motivazioni

| Decisione | Motivazione | Alternativa scartata (per ora) |
|---|---|---|
| Download con **GitHub Actions** | Databricks Free Edition non può raggiungere siti esterni come l'UST; Luca non vuole installare Python sul PC | Script sul PC (scartato: niente installazioni locali) |
| Dati grezzi (**Bronze**) salvati **nel repository GitHub** | Il computer di GitHub si spegne a fine lavoro: serviva un archivio gratuito, senza credenziali, con storico automatico e trasparente | Caricamento diretto nel volume Databricks via API con token (richiede gestire una credenziale; da valutare per dataset grandi) |
| Repository **pubblico** | Gratuito senza limiti per GitHub Actions; funge da portfolio; dati ufficiali ripubblicabili con citazione | Privato (2.000 minuti/mese gratis; senza carta, si blocca invece di addebitare) |
| Download **filtrato** (non tutto il dataset) | Il dataset completo supera i 6 GB e la connessione si interrompe | — |
| File compressi `.csv.gz` | Riducono lo spazio nel repository; Databricks/pandas li leggono direttamente | CSV non compresso |
| Ogni download è un **nuovo file con data** (mai sovrascrivere) | Tracciabilità: si può sempre ricostruire "che dati avevamo in quella data" | Sovrascrivere l'ultimo file |
| Elaborazione in **Databricks Free Edition** (Git folder) | Gratuito, serverless; Databricks legge i file dal repository senza accesso a internet | — |
| Tabelle Silver scritte in **overwrite** | Idempotenza: rieseguire dà lo stesso risultato; lo storico resta nei file Bronze e nella cronologia Delta | Append (rischio duplicati) |
| File del workflow in **formato JSON** (dentro il `.yml`) | Il formato YAML con indentazione si rompe quando si incolla dal browser; il JSON è YAML valido e non dipende dagli spazi | YAML classico |

---

## 4. Pipeline dei dati

### Bronze — acquisizione (`scarica_bfs.py`, eseguito da GitHub Actions)

- **Quando:** automatico il 1° di ogni mese alle 06:00 UTC; manuale con *Run workflow*.
- **Cosa scarica:**
  - `totale_per_cantone`: tutta l'economia (NOGA `_T`), Paesi IT/FR/DE/AT/totale, **tutti i cantoni**, sesso totale. Chiave: `_T.IT+FR+DE+AT+_T.Q._T.` → 12.960 righe.
  - `settori_cantoni_confine`: totale + 3 settori + 21 sezioni NOGA, Paesi IT/FR/totale, cantoni TI/GR/VS/GE/VD/Svizzera. → 43.200 righe.
- **File prodotti** in `bronze/bfs_sse/DF_GGS_1/`, con prefisso data-ora UTC:
  - `<data>_struttura.json` — struttura del dataset (dimensioni, codici)
  - `<data>_totale_per_cantone.csv.gz`
  - `<data>_settori_cantoni_confine.csv.gz`
  - `<data>_provenance.json` — URL, data, impronta SHA-256, dimensione, licenza
- **Verifica completezza (9.10.2026):** 12.960 = 5 Paesi × 27 cantoni × 96 trimestri; 43.200 = 25 voci × 3 Paesi × 6 cantoni × 96 trimestri. Periodo 2002-Q3 → 2026-Q2.

### Silver — pulizia (`02_silver_frontalieri.ipynb`, Databricks)

**Regole di pulizia:**
- si tengono codici + etichette; si scartano le colonne tecniche SDMX;
- nomi colonna in italiano (`paese_cod`, `cantone_cod`, `trimestre`, `frontalieri`, …);
- il valore diventa numero decimale, **non arrotondato** (l'UST pubblica stime);
- da `trimestre` si ricavano `anno`, `trim`, `data_fine_trimestre`;
- si aggiungono `fonte_file` e `scaricato_utc` per la tracciabilità.

**Controlli di qualità** (se un controllo bloccante fallisce, il notebook si ferma e non scrive):
- [bloccante] nessun duplicato sulla chiave;
- [bloccante] nessun valore negativo;
- [bloccante] la somma dei cantoni ricostruisce il totale svizzero (scarto < 1%);
- [informativo] valori mancanti, completezza della griglia, periodo coperto.

**Tabelle prodotte:** `workspace.frontalieri.silver_frontalieri_cantone`, `workspace.frontalieri.silver_frontalieri_settori`.

### Gold — indicatori *(da fare)*

---

## 5. Diario dei lavori

### 9 ottobre 2026

| # | Passo | Esito |
|---|---|---|
| 1 | Scelta del tema (frontalieri) e degli output (articolo LinkedIn + paper PDF) | ✔ |
| 2 | Verifica fonti e condizioni di Databricks Free Edition | ✔ |
| 3 | Creazione in Databricks di `workspace.frontalieri` e del volume `raw` | ✔ (il volume per ora non è usato) |
| 4 | Tentativo di download da Databricks | ✘ Databricks non raggiunge siti esterni → vedi errore E2 |
| 5 | Creazione repository GitHub `geopolitica-dati` (pubblico) | ✔ |
| 6 | Creazione del workflow GitHub Actions | ✔ dopo correzione formato (E3) |
| 7 | Download dalla vecchia tabella PX | ✘ tabella non disponibile/interrotta (E4) |
| 8 | Passaggio allo Swiss Stats Explorer (SDMX) | ✔ struttura verificata |
| 9 | Download completo del dataset | ✘ oltre 6 GB, connessione interrotta (E5) |
| 10 | Download filtrato (due estrazioni) | ✔ dati completi, salvati in `bronze/` |
| 11 | Documentazione (README + questo file) | ✔ |
| 12 | Collegamento GitHub → Databricks (Git folder) | ✔ |
| 13 | Caricamento documentazione + notebook su GitHub, Pull, esecuzione notebook Silver | da fare |

---

## 6. Errori incontrati e soluzioni

| # | Errore | Causa | Soluzione / regola per il futuro |
|---|---|---|---|
| E1 | "Error importing" in Databricks | Import nella cartella *Workspace › Users* (condivisa) | Importare sempre nella propria **Home** |
| E2 | `NameResolutionError` su `pxweb.bfs.admin.ch` | Databricks Free Edition limita l'accesso a internet a pochi domini autorizzati | Download fuori da Databricks (GitHub Actions) |
| E3 | Workflow con il nome-percorso e fallito subito | Spazi YAML alterati dall'incolla nel browser | Scrivere il workflow in formato JSON |
| E4 | `HTTP 400 Bad Request` | La tabella PX `px-x-0302010000_105` non è nell'API PxWeb ed è interrotta al 2025-Q3 | Usare Swiss Stats Explorer, `DF_GGS_1` |
| E5 | `IncompleteRead` dopo 26 minuti | Dataset completo oltre 6 GB | Scaricare solo le combinazioni necessarie (chiave filtrata) |

---

## 7. Note metodologiche

- **Valori decimali:** l'UST pubblica stime (es. 164'717,66); nei testi si arrotonda, nei calcoli no.
- **Rottura di serie 2026:** dal 2026 il comune di Moutier passa dal Canton Berna al Canton Giura. Impatto atteso sui frontalieri minimo, ma da citare.
- **Etichetta tecnica:** i metadati dell'API indicano il dataflow come "non in produzione". I valori coincidono con le cifre ufficiali pubblicate; da segnalare in nota nel paper.
- **Cambio di fonte:** la serie storica PX (fino al 2025-Q3) e il nuovo dataset SSE coprono lo stesso fenomeno; usiamo solo il nuovo per evitare discontinuità.

---

## 8. Costi

| Servizio | Piano | Costo | Limite rilevante |
|---|---|---|---|
| GitHub (repo pubblico + Actions) | Free | 0 | Actions illimitate su repo pubblici; file max 100 MB |
| Databricks | Free Edition | 0 | Solo serverless; quote giornaliere; uso non commerciale; account inattivi possono essere eliminati |
| UST / Swiss Stats Explorer | Open data | 0 | Citazione obbligatoria |

---

## 9. Prossimi passi

> **PUNTO DI RIPRESA (9.10.2026, sera):** Git folder `geopolitica-dati` creato in Databricks e funzionante.
> Da fare: (A) caricare su GitHub `README.md`, `DOCUMENTAZIONE.md`, `02_silver_frontalieri.ipynb` → (B) in Databricks, pulsante **main** → **Pull** → (C) aprire `02_silver_frontalieri`, Serverless, **Run all**, verificare controlli di qualità e tabella finale.

1. Collegare il repository a Databricks (Git folder) ✔ — eseguire `02_silver_frontalieri` → verificare i controlli di qualità.
2. Notebook Gold: indicatori (variazioni annue, indice base 2019 = 100, quota italiani in Ticino, confronto con controllo francese, settori).
3. Grafici collegati alle tabelle Gold.
4. Verifica delle fonti di contesto (accordo, ristorni, riforma UE) su fonti ufficiali.
5. Interpretazione geopolitica (attori, interessi, leve) e scenari.
6. Articolo LinkedIn + paper PDF.
