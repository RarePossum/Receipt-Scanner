import sqlite3

def db_establish():
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS files (id VARCHAR(36) PRIMARY KEY, file_type VARCHAR(6), file BLOB(32768));")
    cur.execute("CREATE TABLE IF NOT EXISTS receipts (id VARCHAR(36) PRIMARY KEY, merchant TEXT, date TEXT, total INTEGER, is_work INTEGER, receipt VARCHAR(32768));")
    con.commit()
    con.close
    
def add_file(id, type, file):
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    
    query = """
    INSERT INTO files (id, file_type, file)
    VALUES (?, ?, ?)
    """
    data = (id, type, file)
    
    cur.execute(query, data)
    
    con.commit()
    con.close()