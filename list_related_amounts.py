import sqlite3
import pandas as pd

db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"

try:
    conn = sqlite3.connect(db_path)
    
    # Query for related records
    query = """
    SELECT title, award_amount, award_date
    FROM drone_tenders
    WHERE title LIKE '%Integrated CUAS Vehicle%' OR supplier_name LIKE '%CACI%'
    ORDER BY award_date
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("Related Records:")
    for index, row in df.iterrows():
        print(f"Date: {row['award_date']}, Amount: {row['award_amount']}, Title: {row['title']}")
        
except Exception as e:
    print(f"Error: {e}")
