# Personal Expense System

Progetto finale di programmazione: sistema di gestione spese e budget da console.

## Requisiti
Python 3.10 o superiore. Solo librerie standard: `sqlite3`, `pathlib`, `datetime`, `decimal`.
Non serve installare pacchetti o un server SQL: SQLite e incluso in Python.

## Avvio
Dalla cartella principale del progetto eseguire:

```bash
python src/main.py
```

Su alcuni sistemi usare `python3 src/main.py` o, su Windows, `py src/main.py`.
Al primo avvio viene creato `spese.db` con le tabelle vuote.

## Dati dimostrativi
Per caricare i dati di esempio su un database nuovo, con il client SQLite:

```bash
sqlite3 spese.db < sql/database.sql
```

In alternativa eseguire lo script con un client SQL SQLite. Attenzione: lo script contiene INSERT dimostrativi; non rieseguirlo su un database gia popolato se non si vogliono duplicare le spese.

## Funzioni
1. Inserimento categorie senza duplicati.
2. Registrazione spese con data valida, importo positivo e categoria esistente.
3. Inserimento/aggiornamento del budget mensile per categoria.
4. Report aggregati SQL, confronto budget e elenco cronologico.

Gli importi sono memorizzati in centesimi interi per evitare errori di arrotondamento floating point.

## Demo video
Registrare un video dello schermo che mostri l'avvio, la creazione di una categoria, l'inserimento di una spesa, la definizione del budget e almeno un report. Salvare come `demo/demo_video.mp4`.

## Repository
Pubblicare soltanto `src/`, `sql/`, `demo/` e `README.md`; non pubblicare `spese.db` con dati personali.
