import sqlite3
import pandas as pd
import plotly.express as px
import os

# Database path
db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"
# Output file path
output_path = r"F:\Drone_Tender_Reptile\drone_tenders_chart.html"

def create_chart():
    try:
        print("Connecting to database...")
        # Connect to the database
        conn = sqlite3.connect(db_path)
        
        # Query data
        query = """
        SELECT 
            supplier_name,
            title,
            award_amount
        FROM drone_tenders
        WHERE supplier_name IS NOT NULL AND supplier_name != ''
        """
        
        # Read data into a DataFrame
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("No data found to visualize.")
            return

        print(f"Data loaded: {len(df)} records.")

        # Create stacked bar chart
        print("Generating chart...")
        fig = px.bar(
            df, 
            x="supplier_name", 
            y="award_amount", 
            color="title", 
            title="Drone Tenders by Supplier and Case (無人機標案廠商得標金額統計)",
            labels={"supplier_name": "廠商名", "award_amount": "得標金額", "title": "得標案件"},
            height=800
        )
        
        # Update layout for better readability
        fig.update_layout(
            xaxis_tickangle=-45,
            xaxis_title="廠商名",
            yaxis_title="得標金額 (累計)",
            legend_title="得標案件"
        )
        
        # Save as HTML
        print(f"Saving chart to {output_path}...")
        fig.write_html(output_path)
        print(f"Successfully created chart at {output_path}")
        
    except ImportError as e:
        print(f"ImportError: {e}. Please install required packages (pandas, plotly).")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_chart()
