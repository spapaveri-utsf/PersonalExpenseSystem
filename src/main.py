"""Sistema spese personali: Python 3 + SQLite, interfaccia console."""
# Librerie standard: database SQLite, percorsi dei file, date e calcoli decimali precisi.
import sqlite3
from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation

# Percorso del database locale: si trova nella cartella principale del progetto.
DB = Path(__file__).resolve().parent.parent / 'spese.db'
# Percorso dello script SQL contenente la struttura delle tabelle e i dati di esempio.
SCHEMA = Path(__file__).resolve().parent.parent / 'sql' / 'database.sql'


# Converte un importo espresso in centesimi in una stringa in euro con due decimali.
# Parametro: centesimi (numero intero). Restituisce: testo, ad esempio '25.50 EUR'.
def euro(centesimi):
    return f'{centesimi / 100:.2f} EUR'


# Controlla un importo inserito dall'utente e lo converte in centesimi interi.
# Accetta il punto o la virgola decimale; rifiuta valori non numerici, non finiti,
# nulli, negativi, con più di due decimali o superiori al limite previsto.
# Parametro: testo (stringa digitata). Restituisce: centesimi (intero positivo).
# In caso di valore non valido solleva ValueError con un messaggio esplicativo.
def importo_positivo(testo):
    try:
        # Decimal evita gli errori di approssimazione tipici dei numeri float.
        valore = Decimal(testo.strip().replace(',', '.'))
        # Verifica che il numero sia finito, positivo e con al massimo due decimali.
        if not valore.is_finite() or valore <= 0 or valore.as_tuple().exponent < -2:
            raise ValueError
        # Converte gli euro in centesimi per memorizzarli come INTEGER in SQLite.
        centesimi = int(valore * 100)
        # Applica i limiti minimo e massimo ammessi dal programma.
        if centesimi <= 0 or centesimi > 9_000_000_000_000:
            raise ValueError
        return centesimi
    except (InvalidOperation, ValueError):
        # Uniforma gli errori di conversione e validazione in un unico messaggio.
        raise ValueError('Errore: importo non valido; usare un numero positivo con massimo due decimali.')


# Cerca nel database una categoria in base al nome, ignorando maiuscole e minuscole.
# Parametri: db (connessione SQLite), nome (nome della categoria).
# Restituisce: identificativo numerico della categoria, oppure None se assente.
def categoria_id(db, nome):
    # Il segnaposto ? consente di passare il nome come parametro SQL in sicurezza.
    r = db.execute('SELECT id FROM categorie WHERE nome = ? COLLATE NOCASE', (nome.strip(),)).fetchone()
    return r[0] if r else None


# Verifica che una data sia valida e scritta esattamente nel formato YYYY-MM-DD.
# Parametro: testo (data inserita). Restituisce: la stessa stringa se valida.
# Solleva ValueError se la data è inesistente oppure non rispetta il formato.
def valida_data(testo):
    # fromisoformat verifica anche la correttezza del calendario (giorni e mesi).
    d = date.fromisoformat(testo)
    # Il confronto impedisce di accettare rappresentazioni diverse dal formato richiesto.
    if d.isoformat() != testo:
        raise ValueError('Formato non valido')
    return testo


# Verifica il formato YYYY-MM del mese usato per i budget.
# Parametro: testo (mese inserito). Restituisce: la stringa se valida.
# Solleva ValueError in caso di formato errato o mese inesistente.
def valida_mese(testo):
    # Controlla lunghezza e posizione del separatore tra anno e mese.
    if len(testo) != 7 or testo[4] != '-':
        raise ValueError('Formato non valido')
    # Aggiunge il primo giorno del mese per sfruttare il controllo del calendario.
    date.fromisoformat(testo + '-01')
    return testo


# Gestisce la creazione di una nuova categoria di spesa.
# Parametro: db (connessione SQLite). Non restituisce valori.
# Evita nomi vuoti e categorie già esistenti prima di eseguire l'INSERT.
def categorie(db):
    nome = input('Nome categoria: ').strip()
    # Non consente di creare categorie con nome vuoto o composto da soli spazi.
    if not nome:
        print('Errore: nome categoria vuoto.'); return
    # Controlla i duplicati senza distinguere tra maiuscole e minuscole.
    if categoria_id(db, nome) is not None:
        print('La categoria esiste gia.'); return
    # Il contesto with db conferma automaticamente la transazione se non ci sono errori.
    with db:
        db.execute('INSERT INTO categorie(nome) VALUES (?)', (nome,))
    print('Categoria inserita correttamente.')


# Registra una spesa associandola a una categoria esistente.
# Parametro: db (connessione SQLite). Non restituisce valori.
# Richiede data, importo, categoria e descrizione facoltativa; valida i dati
# prima dell'inserimento nella tabella spese.
def spesa(db):
    try:
        # Controlla che data e importo rispettino i requisiti del programma.
        giorno = valida_data(input('Data (YYYY-MM-DD): ').strip())
        importo = importo_positivo(input('Importo (EUR): '))
    except ValueError as exc:
        # In caso di input non valido interrompe l'operazione senza salvare nulla.
        print(f'Errore: {exc}'); return
    nome = input('Nome categoria: ').strip()
    # Recupera la chiave primaria della categoria da usare come chiave esterna.
    cat = categoria_id(db, nome)
    if cat is None:
        print('Errore: la categoria non esiste.'); return
    descrizione = input('Descrizione (facoltativa): ').strip()
    # Memorizza l'importo in centesimi e la descrizione vuota come NULL.
    with db:
        db.execute('INSERT INTO spese(data,importo_centesimi,categoria_id,descrizione) VALUES (?,?,?,?)',
                   (giorno, importo, cat, descrizione or None))
    print('Spesa inserita correttamente.')


# Crea o aggiorna il budget mensile di una categoria.
# Parametro: db (connessione SQLite). Non restituisce valori.
# Ogni coppia mese/categoria può avere un solo budget grazie al vincolo UNIQUE.
def definisci_budget(db):
    try:
        # Verifica il mese e controlla che la categoria indicata esista.
        mese = valida_mese(input('Mese (YYYY-MM): ').strip())
        nome = input('Nome categoria: ').strip()
        cat = categoria_id(db, nome)
        if cat is None:
            print('Errore: la categoria non esiste.'); return
        # Il budget deve essere positivo e viene convertito in centesimi.
        importo = importo_positivo(input('Budget (EUR): '))
    except ValueError as exc:
        print(f'Errore: {exc}'); return
    # ON CONFLICT aggiorna l'importo se esiste già un budget per lo stesso mese
    # e la stessa categoria; altrimenti inserisce una nuova riga.
    with db:
        db.execute('''INSERT INTO budget(mese,categoria_id,importo_centesimi) VALUES (?,?,?)
                      ON CONFLICT(mese,categoria_id) DO UPDATE SET importo_centesimi=excluded.importo_centesimi''',
                   (mese, cat, importo))
    print('Budget mensile salvato correttamente.')


# Report 1: calcola il totale complessivo delle spese per ogni categoria.
# Parametro: db (connessione SQLite). Stampa i risultati, senza restituire valori.
# LEFT JOIN include anche le categorie che non hanno spese; COALESCE mostra zero.
def report_categorie(db):
    rows = db.execute('''SELECT c.nome, COALESCE(SUM(s.importo_centesimi),0)
                         FROM categorie c LEFT JOIN spese s ON s.categoria_id=c.id
                         GROUP BY c.id,c.nome ORDER BY c.nome''').fetchall()
    # Stampa nome e totale formattato in euro per ogni categoria.
    for nome, totale in rows:
        print(f'{nome:25} {euro(totale):>15}')
    # Gestisce il caso in cui il database non contenga ancora categorie.
    if not rows: print('Nessuna categoria presente.')


# Report 2: confronta i budget mensili con le spese realmente registrate.
# Parametro: db (connessione SQLite). Stampa il confronto per ogni budget.
# La JOIN collega i budget alle categorie; la LEFT JOIN considera anche mesi
# senza spese e il filtro substr limita la somma al mese del budget.
def report_budget(db):
    rows = db.execute('''SELECT b.mese,c.nome,b.importo_centesimi,
                            COALESCE(SUM(s.importo_centesimi),0) AS speso
                         FROM budget b JOIN categorie c ON c.id=b.categoria_id
                         LEFT JOIN spese s ON s.categoria_id=b.categoria_id
                           AND substr(s.data,1,7)=b.mese
                         GROUP BY b.id,b.mese,c.nome,b.importo_centesimi
                         ORDER BY b.mese,c.nome''').fetchall()
    # Confronta importi in centesimi e segnala gli eventuali superamenti.
    for mese, nome, limite, speso in rows:
        stato = 'SUPERAMENTO BUDGET' if speso > limite else 'NEL BUDGET'
        print(f'Mese: {mese} | Categoria: {nome} | Budget: {euro(limite)} | Speso: {euro(speso)} | {stato}')
    if not rows: print('Nessun budget definito.')


# Report 3: visualizza tutte le spese in ordine cronologico decrescente.
# Parametro: db (connessione SQLite). Stampa una tabella senza restituire valori.
# A parità di data, le spese con identificativo maggiore vengono mostrate prima.
def report_spese(db):
    rows = db.execute('''SELECT s.data,c.nome,s.importo_centesimi,COALESCE(s.descrizione,'')
                         FROM spese s JOIN categorie c ON c.id=s.categoria_id
                         ORDER BY s.data DESC,s.id DESC''').fetchall()
    # Intestazione delle colonne del report.
    print(f'{"Data":12} {"Categoria":20} {"Importo":15} Descrizione')
    # Stampa ogni spesa convertendo l'importo dai centesimi agli euro.
    for giorno, nome, importo, descrizione in rows:
        print(f'{giorno:12} {nome:20} {euro(importo):15} {descrizione}')
    if not rows: print('Nessuna spesa registrata.')


# Gestisce il sottomenu per scegliere uno dei tre report disponibili.
# Parametro: db (connessione SQLite). Non restituisce valori utili.
# Il ciclo continua finché l'utente non seleziona il ritorno al menu principale.
def reports(db):
    while True:
        print('\n1. Totale spese per categoria\n2. Spese mensili vs budget\n3. Elenco completo spese\n4. Ritorna al menu principale')
        scelta = input('Scelta: ').strip()
        # Richiama la funzione corrispondente alla scelta effettuata.
        if scelta == '1': report_categorie(db)
        elif scelta == '2': report_budget(db)
        elif scelta == '3': report_spese(db)
        elif scelta == '4': return
        else: print('Scelta non valida. Riprovare.')


# Funzione principale: inizializza il database e gestisce il menu dell'applicazione.
# Non richiede parametri e non restituisce valori.
# Apre la connessione SQLite, prepara le tabelle e mantiene attivo il programma
# fino alla scelta di uscita o all'interruzione da tastiera.
def main():
    # Apre il database locale; SQLite crea il file se non esiste.
    with sqlite3.connect(DB) as db:
        # Attiva il controllo delle chiavi esterne per questa connessione.
        db.execute('PRAGMA foreign_keys = ON')
        # Crea soltanto le tabelle; i dati di esempio sono caricabili separatamente.
        # Legge lo script SQL ed esclude la parte con gli INSERT dimostrativi.
        ddl = SCHEMA.read_text(encoding='utf-8').split('INSERT OR IGNORE INTO categorie')[0]
        # Esegue le istruzioni DDL per creare le tabelle, se non sono già presenti.
        db.executescript(ddl)
        print('Benvenuto nel Sistema Spese Personali')
        # Variabile booleana che controlla la permanenza nel menu principale.
        esecuzione = True
        # Ripete il menu principale fino alla richiesta di uscita.
        while esecuzione:
            print('\n--- SISTEMA SPESE PERSONALI ---\n1. Gestione Categorie\n2. Inserisci Spesa\n3. Definisci Budget Mensile\n4. Visualizza Report\n5. Esci')
            scelta = input('Inserisci la tua scelta: ').strip()
            try:
                # Smista la scelta alla funzione operativa corrispondente.
                if scelta == '1': categorie(db)
                elif scelta == '2': spesa(db)
                elif scelta == '3': definisci_budget(db)
                elif scelta == '4': reports(db)
                elif scelta == '5': print('Arrivederci.'); esecuzione = False
                else: print('Scelta non valida. Riprovare.')
            except (EOFError, KeyboardInterrupt):
                # Consente di interrompere il programma in modo controllato.
                print('\nUscita richiesta.'); esecuzione = False
            except sqlite3.Error as exc:
                # Mostra gli errori generati dal database senza chiudere il menu.
                print(f'Errore database: {exc}')


# Avvia main() soltanto quando questo file viene eseguito direttamente,
# evitando l'avvio automatico se il modulo viene importato da un altro script.
if __name__ == '__main__':
    main()
