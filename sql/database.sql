PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS categorie (
 id INTEGER PRIMARY KEY,
 nome TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK (length(trim(nome)) > 0)
);
CREATE TABLE IF NOT EXISTS spese (
 id INTEGER PRIMARY KEY,
 data TEXT NOT NULL CHECK (data GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
 importo_centesimi INTEGER NOT NULL CHECK (importo_centesimi > 0),
 categoria_id INTEGER NOT NULL,
 descrizione TEXT,
 FOREIGN KEY (categoria_id) REFERENCES categorie(id)
);
CREATE TABLE IF NOT EXISTS budget (
 id INTEGER PRIMARY KEY,
 mese TEXT NOT NULL CHECK (mese GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'),
 categoria_id INTEGER NOT NULL,
 importo_centesimi INTEGER NOT NULL CHECK (importo_centesimi > 0),
 UNIQUE (mese, categoria_id),
 FOREIGN KEY (categoria_id) REFERENCES categorie(id)
);
INSERT OR IGNORE INTO categorie(nome) VALUES ('Alimentari'), ('Trasporti'), ('Salute');
INSERT INTO spese(data,importo_centesimi,categoria_id,descrizione)
SELECT '2026-01-15',2550,id,'Pranzo' FROM categorie WHERE nome='Alimentari';
INSERT INTO spese(data,importo_centesimi,categoria_id,descrizione)
SELECT '2026-01-18',32000,id,'Spesa settimanale' FROM categorie WHERE nome='Alimentari';
INSERT INTO spese(data,importo_centesimi,categoria_id,descrizione)
SELECT '2026-01-20',4500,id,'Carburante' FROM categorie WHERE nome='Trasporti';
INSERT INTO budget(mese,categoria_id,importo_centesimi)
SELECT '2026-01',id,30000 FROM categorie WHERE nome='Alimentari'
ON CONFLICT(mese,categoria_id) DO UPDATE SET importo_centesimi=excluded.importo_centesimi;
INSERT INTO budget(mese,categoria_id,importo_centesimi)
SELECT '2026-01',id,10000 FROM categorie WHERE nome='Trasporti'
ON CONFLICT(mese,categoria_id) DO UPDATE SET importo_centesimi=excluded.importo_centesimi;
