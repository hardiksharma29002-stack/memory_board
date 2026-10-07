import sqlite3

conn = sqlite3.connect('data/app.db')
c = conn.cursor()
c.execute("UPDATE photos SET path = replace(path, '\\', '/')")
conn.commit()

c.execute("SELECT id, path FROM photos LIMIT 5")
for row in c.fetchall():
    print(row)

c.execute("SELECT count(*) FROM photos WHERE instr(path, '\\') > 0")
remaining = c.fetchone()[0]
print(f"Remaining paths with backslash: {remaining}")
conn.close()
