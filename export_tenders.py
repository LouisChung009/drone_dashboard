import sqlite3
import pandas as pd
import os

# Database path
db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"
# Output file path
output_path = r"F:\Drone_Tender_Reptile\data\drone_tenders_export.xlsx"

def export_data():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Query to select distinct records
        query = """
        SELECT DISTINCT 
            supplier_name AS "得標廠商",
            title AS "得標案件",
            award_amount AS "得標金額",
            award_date AS "得標時間"
        FROM drone_tenders
        WHERE supplier_name IS NOT NULL AND supplier_name != ''
        ORDER BY award_date DESC;
        """
        
        # Read data into a DataFrame
        df = pd.read_sql_query(query, conn)
        
        # Close the connection
        conn.close()
        
        # Check if data was retrieved
        if df.empty:
            print("No data found to export.")
            return

        # Export to Excel
        df.to_excel(output_path, index=False)
        print(f"Successfully exported {len(df)} records to {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    export_data()
