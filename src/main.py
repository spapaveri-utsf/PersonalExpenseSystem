"""Sistema spese personali: Python 3 + SQLite, interfaccia console."""
import sqlite3
from pathlib import Path
from datetime import date
from decimal import Decimal, InvalidOperation

DB = Path(__file__).resolve().parent.parent / 'spese.db'
SCHEMA = Path(__file__).resolve().parent.parent / 'sql' / 'database.sql'


def euro(centesimi):
    return f'{centesimi / 100:.2f} EUR'


def importo_positivo(testo):
    try:
        valore = Decimal(testo.strip().replace(',', '.'))
        if not valore.is_finite() or valore <= 0 or valore.as_tuple().exponent < -2:
            raise ValueError
        centesimi = int(valore * 100)
        if centesimi <= 0 or centesimi > 9_000_000_000_000:
            raise ValueError
        return centesimi
    except (InvalidOperation, ValueError):
        raise ValueError('Errore: importo non valido; usare un numero positivo con massimo due decimali.')


def categoria_id(db, nome):
    r = db.execute('SELECT id FROM categorie WHERE nome = ? COLLATE NOCASE', (nome.strip(),)).fetchone()
    return r[0] if r else None


def valida_data(testo):
    d = date.fromisoformat(testo)
    if d.isoformat() != testo:
        raise ValueError('Formato non valido')
    return testo


def valida_mese(testo):
    if len(testo) != 7 or testo[4] != '-':
        raise ValueError('Formato non valido')
    date.fromisoformat(testo + '-01')
    return testo


def categorie(db):
    nome = input('Nome categoria: ').strip()
    if not nome:
        print('Errore: nome categoria vuoto.'); return
    if categoria_id(db, nome) is not None:
        print('La categoria esiste gia.'); return
    with db:
        db.execute('INSERT INTO categorie(nome) VALUES (?)', (nome,))
    print('Categoria inserita correttamente.')


def spesa(db):
    try:
        giorno = valida_data(input('Data (YYYY-MM-DD): ').strip())
        importo = importo_positivo(input('Importo (EUR): '))
    except ValueError as exc:
        print(f'Errore: {exc}'); return
    nome = input('Nome categoria: ').strip()
    cat = categoria_id(db, nome)
    if cat is None:
        print('Errore: la categoria non esiste.'); return
    descrizione = input('Descrizione (facoltativa): ').strip()
    with db:
        db.execute('INSERT INTO spese(data,importo_centesimi,categoria_id,descrizione) VALUES (?,?,?,?)',
                   (giorno, importo, cat, descrizione or None))
    print('Spesa inserita correttamente.')


def definisci_budget(db):
    try:
        mese = valida_mese(input('Mese (YYYY-MM): ').strip())
        nome = input('Nome categoria: ').strip()
        cat = categoria_id(db, nome)
        if cat is None:
            print('Errore: la categoria non esiste.'); return
        importo = importo_positivo(input('Budget (EUR): '))
    except ValueError as exc:
        print(f'Errore: {exc}'); return
    with db:
        db.execute('''INSERT INTO budget(mese,categoria_id,importo_centesimi) VALUES (?,?,?)
                      ON CONFLICT(mese,categoria_id) DO UPDATE SET importo_centesimi=excluded.importo_centesimi''',
                   (mese, cat, importo))
    print('Budget mensile salvato correttamente.')


def report_categorie(db):
    rows = db.execute('''SELECT c.nome, COALESCE(SUM(s.importo_centesimi),0)
                         FROM categorie c LEFT JOIN spese s ON s.categoria_id=c.id
                         GROUP BY c.id,c.nome ORDER BY c.nome''').fetchall()
    for nome, totale in rows:
        print(f'{nome:25} {euro(totale):>15}')
    if not rows: print('Nessuna categoria presente.')


def report_budget(db):
    rows = db.execute('''SELECT b.mese,c.nome,b.importo_centesimi,
                            COALESCE(SUM(s.importo_centesimi),0) AS speso
                         FROM budget b JOIN categorie c ON c.id=b.categoria_id
                         LEFT JOIN spese s ON s.categoria_id=b.categoria_id
                           AND substr(s.data,1,7)=b.mese
                         GROUP BY b.id,b.mese,c.nome,b.importo_centesimi
                         ORDER BY b.mese,c.nome''').fetchall()
    for mese, nome, limite, speso in rows:
        stato = 'SUPERAMENTO BUDGET' if speso > limite else 'NEL BUDGET'
        print(f'Mese: {mese} | Categoria: {nome} | Budget: {euro(limite)} | Speso: {euro(speso)} | {stato}')
    if not rows: print('Nessun budget definito.')


def report_spese(db):
    rows = db.execute('''SELECT s.data,c.nome,s.importo_centesimi,COALESCE(s.descrizione,'')
                         FROM spese s JOIN categorie c ON c.id=s.categoria_id
                         ORDER BY s.data DESC,s.id DESC''').fetchall()
    print(f'{"Data":12} {"Categoria":20} {"Importo":15} Descrizione')
    for giorno, nome, importo, descrizione in rows:
        print(f'{giorno:12} {nome:20} {euro(importo):15} {descrizione}')
    if not rows: print('Nessuna spesa registrata.')


def reports(db):
    while True:
        print('\n1. Totale spese per categoria\n2. Spese mensili vs budget\n3. Elenco completo spese\n4. Ritorna al menu principale')
        scelta = input('Scelta: ').strip()
        if scelta == '1': report_categorie(db)
        elif scelta == '2': report_budget(db)
        elif scelta == '3': report_spese(db)
        elif scelta == '4': return
        else: print('Scelta non valida. Riprovare.')


def main():
    with sqlite3.connect(DB) as db:
        db.execute('PRAGMA foreign_keys = ON')
        # Crea soltanto le tabelle; i dati di esempio sono caricabili separatamente.
        ddl = SCHEMA.read_text(encoding='utf-8').split('INSERT OR IGNORE INTO categorie')[0]
        db.executescript(ddl)
        print('Benvenuto nel Sistema Spese Personali')
        while True:
            print('\n--- SISTEMA SPESE PERSONALI ---\n1. Gestione Categorie\n2. Inserisci Spesa\n3. Definisci Budget Mensile\n4. Visualizza Report\n5. Esci')
            scelta = input('Inserisci la tua scelta: ').strip()
            try:
                if scelta == '1': categorie(db)
                elif scelta == '2': spesa(db)
                elif scelta == '3': definisci_budget(db)
                elif scelta == '4': reports(db)
                elif scelta == '5': print('Arrivederci.'); break
                else: print('Scelta non valida. Riprovare.')
            except (EOFError, KeyboardInterrupt):
                print('\nUscita richiesta.'); break
            except sqlite3.Error as exc:
                print(f'Errore database: {exc}')


if __name__ == '__main__':
    main()
