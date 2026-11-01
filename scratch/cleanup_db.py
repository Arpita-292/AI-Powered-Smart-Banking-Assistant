import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(__file__), '..', 'siri_bank.db')

def cleanup():
    if not os.path.exists(DB_NAME):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("Cleaning up database tables...")
    
    # Delete from requests (KYC and Card)
    cursor.execute("DELETE FROM requests")
    print(f"Deleted {cursor.rowcount} records from 'requests'")

    # Delete from loans
    cursor.execute("DELETE FROM loans")
    print(f"Deleted {cursor.rowcount} records from 'loans'")

    # Optional: Delete from transactions if needed, but user specifically asked for KYC, card, loan
    # cursor.execute("DELETE FROM transactions")
    
    conn.commit()
    conn.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
