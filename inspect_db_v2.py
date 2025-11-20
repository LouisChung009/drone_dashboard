import sqlite3

db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get columns for drone_tenders
    cursor.execute("PRAGMA table_info(drone_tenders)")
    columns = cursor.fetchall()
    
    print("Columns in drone_tenders:")
    for col in columns:
        print(f"{col[1]}")
            
    conn.close()
except Exception as e:
    print(f"Error: {e}")
