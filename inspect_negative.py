import sqlite3
import pandas as pd

db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"

try:
    conn = sqlite3.connect(db_path)
    
    # Query for negative amounts
    query = """
    SELECT *
    FROM drone_tenders
    WHERE award_amount < 0
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if df.empty:
        print("No negative award amounts found.")
    else:
        print(f"Found {len(df)} records with negative award amounts:")
        # Print relevant columns to understand context
        print(df[['title', 'award_amount', 'award_date', 'description', 'source_name']].to_string())
        
except Exception as e:
    print(f"Error: {e}")
