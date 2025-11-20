import sqlite3
import pandas as pd
import json
import os

# Database path
db_path = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"
# Output file path
output_path = r"F:\Drone_Tender_Reptile\drone_tenders_chart_v2.html"

def generate_chart():
    try:
        print("Connecting to database...")
        conn = sqlite3.connect(db_path)
        
        # Query data
        query = """
        SELECT 
            supplier_name,
            title,
            award_amount
        FROM drone_tenders
        WHERE supplier_name IS NOT NULL AND supplier_name != ''
        ORDER BY award_amount DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            print("No data found to visualize.")
            return

        print(f"Data loaded: {len(df)} records.")

        # Convert to records for JSON embedding
        records = df.to_dict('records')
        json_data = json.dumps(records, ensure_ascii=False)

        # HTML Template
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Drone Awards by Bidder</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; font-family: "Microsoft JhengHei", Arial, sans-serif; height: 100vh; display: flex; flex-direction: column; }}
        .header {{ padding: 15px 20px; background: #f8f9fa; border-bottom: 1px solid #dee2e6; }}
        .main-container {{ display: flex; flex: 1; overflow: hidden; }}
        .sidebar {{ width: 300px; background: #ffffff; border-right: 1px solid #dee2e6; display: flex; flex-direction: column; box-shadow: 2px 0 5px rgba(0,0,0,0.05); }}
        .sidebar-header {{ padding: 15px; border-bottom: 1px solid #eee; background: #f8f9fa; }}
        .sidebar-header h3 {{ margin: 0 0 10px 0; font-size: 18px; }}
        .vendor-list {{ flex: 1; overflow-y: auto; padding: 10px; }}
        .vendor-item {{ display: flex; align-items: center; margin-bottom: 8px; font-size: 14px; cursor: pointer; }}
        .vendor-item:hover {{ background-color: #f0f0f0; border-radius: 4px; }}
        .vendor-item label {{ flex: 1; cursor: pointer; padding: 5px; display: flex; align-items: center; }}
        .vendor-item input {{ margin-right: 10px; transform: scale(1.2); }}
        .chart-container {{ flex: 1; padding: 20px; overflow: hidden; position: relative; }}
        #chart {{ width: 100%; height: 100%; }}
        .btn-group {{ display: flex; gap: 10px; }}
        button {{ padding: 6px 12px; cursor: pointer; background: #fff; border: 1px solid #ccc; border-radius: 4px; font-size: 12px; transition: all 0.2s; }}
        button:hover {{ background: #e9ecef; border-color: #adb5bd; }}
    </style>
</head>
<body>
    <div class="header">
        <h2>Drone Awards by Bidder (無人機標案廠商得標金額統計)</h2>
    </div>
    <div class="main-container">
        <div class="sidebar">
            <div class="sidebar-header">
                <h3>Vendors (廠商)</h3>
                <div class="btn-group">
                    <button onclick="selectAll()">Select All (全選)</button>
                    <button onclick="deselectAll()">Deselect All (取消全選)</button>
                </div>
            </div>
            <div class="vendor-list" id="vendorList">
                <!-- Checkboxes will be injected here -->
            </div>
        </div>
        <div class="chart-container">
            <div id="chart"></div>
        </div>
    </div>

    <script>
        const rawData = {json_data};
        
        // Get unique vendors and cases
        const vendors = [...new Set(rawData.map(d => d.supplier_name))].sort();
        // Sort cases to ensure consistent legend order
        const cases = [...new Set(rawData.map(d => d.title))].sort();
        
        // State
        let selectedVendors = new Set(vendors);

        function init() {{
            const list = document.getElementById('vendorList');
            vendors.forEach(v => {{
                const div = document.createElement('div');
                div.className = 'vendor-item';
                div.innerHTML = `<label><input type="checkbox" value="${{v}}" checked onchange="updateSelection(this)"> ${{v}}</label>`;
                list.appendChild(div);
            }});
            renderChart();
        }}

        function updateSelection(checkbox) {{
            if (checkbox.checked) {{
                selectedVendors.add(checkbox.value);
            }} else {{
                selectedVendors.delete(checkbox.value);
            }}
            renderChart();
        }}

        function selectAll() {{
            selectedVendors = new Set(vendors);
            document.querySelectorAll('.vendor-item input').forEach(cb => cb.checked = true);
            renderChart();
        }}

        function deselectAll() {{
            selectedVendors = new Set();
            document.querySelectorAll('.vendor-item input').forEach(cb => cb.checked = false);
            renderChart();
        }}

        function renderChart() {{
            const filteredData = rawData.filter(d => selectedVendors.has(d.supplier_name));
            
            const traces = [];
            
            // Group by Case (Title) to create traces
            const dataByCase = {{}};
            cases.forEach(c => dataByCase[c] = {{ x: [], y: [] }});
            
            filteredData.forEach(d => {{
                if (dataByCase[d.title]) {{
                    dataByCase[d.title].x.push(d.supplier_name);
                    dataByCase[d.title].y.push(d.award_amount);
                }}
            }});

            Object.keys(dataByCase).forEach(caseTitle => {{
                if (dataByCase[caseTitle].x.length > 0) {{
                    traces.push({{
                        x: dataByCase[caseTitle].x,
                        y: dataByCase[caseTitle].y,
                        name: caseTitle,
                        type: 'bar'
                    }});
                }}
            }});

            const layout = {{
                barmode: 'stack',
                xaxis: {{ 
                    title: '廠商名', 
                    tickangle: -45, 
                    automargin: true 
                }},
                yaxis: {{ 
                    title: '得標金額 (累計)',
                    tickformat: ',.0f'
                }},
                margin: {{ l: 60, r: 50, t: 50, b: 150 }},
                legend: {{
                    title: {{ text: '得標案件' }},
                    orientation: 'v',
                    yanchor: 'top',
                    y: 1,
                    xanchor: 'left',
                    x: 1.02
                }},
                height: document.querySelector('.chart-container').clientHeight
            }};

            Plotly.react('chart', traces, layout, {{responsive: true}});
        }}

        // Handle window resize
        window.onresize = function() {{
            Plotly.Plots.resize(document.getElementById('chart'));
        }};

        init();
    </script>
</body>
</html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Successfully created custom chart at {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    generate_chart()
