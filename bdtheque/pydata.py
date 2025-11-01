import sqlite3

# Connexion à la base de données
conn = sqlite3.connect('db.sqlite3')

# Créer un curseur
cursor = conn.cursor()

# Exécuter une requête SQL
cursor.execute("SELECT serie, tome, outof FROM tomes")

cursor.execute("DROP INDEX IF EXISTS outof")

conn.commit()

# Fermer la connexion
conn.close()