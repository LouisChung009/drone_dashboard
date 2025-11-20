import sqlite3
import pandas as pd

db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"

try:
    conn = sqlite3.connect(db_path)
    
    # Query for negative amounts
    query = """
    SELECT title, award_amount, award_date, description, source_name, supplier_name
    FROM drone_tenders
    WHERE award_amount < 0
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if not df.empty:
        print("Record details:")
        for index, row in df.iterrows():
            print(f"Title: {row['title']}")
            print(f"Amount: {row['award_amount']}")
            print(f"Date: {row['award_date']}")
            print(f"Supplier: {row['supplier_name']}")
            print(f"Source: {row['source_name']}")
            print(f"Description: {row['description']}")
            print("-" * 20)
        
except Exception as e:
    print(f"Error: {e}")
