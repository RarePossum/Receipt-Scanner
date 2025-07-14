import sqlite3

def db_establish():
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS files (id VARCHAR(9) PRIMARY KEY, file_type VARCHAR(6), file BLOB(32768), scan VARCHAR(4096));")
    cur.execute("CREATE TABLE IF NOT EXISTS receipts (id VARCHAR(9) PRIMARY KEY, merchant TEXT, date TEXT, total REAL, is_work INTEGER, receipt VARCHAR(2048));")
    con.commit()
    con.close
    
def add_file(id, type, file, scan):
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    
    query = """
    INSERT INTO files (id, file_type, file, scan)
    VALUES (?, ?, ?, ?)
    """
    data = (id, type, file, scan)
    
    cur.execute(query, data)
    
    con.commit()
    con.close()
    
def add_receipt(form_data, id):
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    
    merchant = form_data["store"]
    date = form_data["date"]
    total = form_data["total"]
    is_work = 0
    if form_data["work_related"]:
        is_work = 1
    
    data = (id, merchant, date, total, is_work, str(form_data))
    
    query = """
    INSERT INTO receipts (id, merchant, date, total, is_work, receipt)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    cur.execute(query, data)
    
    con.commit()
    con.close()

def create_itemised_receipt(items, id):
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
        
    query = "CREATE TABLE '" + id + "' (id INTEGER PRIMARY KEY AUTOINCREMENT, item VARCHAR(64), price REAL, quantity REAL, subtotal REAL);"
    print(query)
    cur.execute(query)
    
    query = "INSERT INTO '" + id + "' (item, price, quantity, subtotal) VALUES (:name, :price, :quantity, :subtotal);"
    
    cur.executemany(query, items)
    
    con.commit()
    con.close()
    
def get_receipts():
    con = sqlite3.connect("db.sqlite3")
    cur = con.cursor()
    
    query = "SELECT * FROM receipts ORDER BY date desc"
    cur.execute(query)
    rows = cur.fetchall()
        
    con.commit()
    con.close()
    return [
            {
                "id": row[0],
                "store": row[1],
                "date": row[2],
                "total": row[3],
                "work_related": bool(row[4]),
                "dump": row[5]
            }
            for row in rows
        ]