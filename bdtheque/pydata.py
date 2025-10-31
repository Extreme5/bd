# import sqlite3

# db = sqlite3.connect("data.db")
# db.execute("CREATE TABLE series (id INTEGER PRIMARY KEY, nom TEXT)")
# db.execute("CREATE TABLE episodes (id INTEGER PRIMARY KEY, serie_id INTEGER, num INTEGER, vu BOOLEAN)")
# # Exemple :
# db.execute("INSERT INTO series (nom) VALUES ('Breaking Bad')")
# for i in range(1, 51):
#     db.execute("INSERT INTO episodes (serie_id, num, vu) VALUES (1, ?, 0)", (i,))
# db.commit()
# db.close()
import sqlite3

# Connexion à la base
db = sqlite3.connect("data.db")

# Pour avoir des colonnes accessibles par nom
db.row_factory = sqlite3.Row
cursor = db.cursor()

# Lecture de toutes les séries
cursor.execute("SELECT * FROM series")
for row in cursor.fetchall():
    print(dict(row))  # Convertit chaque ligne en dictionnaire

db.close()
