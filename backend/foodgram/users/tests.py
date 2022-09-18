import csv, sqlite3

con = sqlite3.connect("db.sqlite3")  # change to 'sqlite:///your_filename.db'
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())
