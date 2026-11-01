import sqlite3

def check_schema():
    conn = sqlite3.connect('siri_bank.db')
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='transactions'")
    row = cursor.fetchone()
    if row:
        print(row[0])
    else:
        print("Table transactions not found")
    conn.close()

if __name__ == "__main__":
    check_schema()
