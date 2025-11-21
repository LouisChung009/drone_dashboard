import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Configuration
DB_GLOBAL = r"F:\Drone_Tender_Reptile\data\drone_tenders.db"
DB_TW = r"F:\Drone_Tender_Reptile\data\TW\drone_awards.db"
OUTPUT_FILE = r"F:\Drone_Tender_Reptile\drone_dashboard.html"

def get_global_data():
    if not os.path.exists(DB_GLOBAL):
        print(f"Database not found: {DB_GLOBAL}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_GLOBAL)
    query = """
    SELECT 
        buyer_country as country,
        supplier_name as vendor,
        award_amount as amount,
        currency,
        title as tender_name
    FROM drone_tenders
    WHERE award_amount IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_tw_data():
    if not os.path.exists(DB_TW):
        print(f"Database not found: {DB_TW}")
        return pd.DataFrame()
    
    conn = sqlite3.connect(DB_TW)
    query = """
    SELECT 
        'Taiwan' as country,
        winning_bidder_name as vendor,
        amount,
        'TWD' as currency,
        job_name as tender_name
    FROM awards
    WHERE amount IS NOT NULL
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def generate_dashboard():
    print("Fetching data...")
    df_global = get_global_data()
    df_tw = get_tw_data()
    
    # Combine data
    df = pd.concat([df_global, df_tw], ignore_index=True)
    
    # Clean data
    df['vendor'] = df['vendor'].fillna('Unknown')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    # Define country order
    countries = ['Canada', 'USA', 'Australia', 'Japan', 'Taiwan']
    
    # Create subplot figure
    fig = make_subplots(
        rows=5, cols=1,
        subplot_titles=[f"{c} Drone Tenders" for c in countries],
        vertical_spacing=0.05,
        shared_xaxes=False
    )
    
    # Store vendor lists for checkboxes
    country_vendors = {}
    
    # Color palette for tenders (optional, or let Plotly handle it)
    # Since we want stacked bars, we add traces for each tender? 
    # No, that's too many traces. 
    # Better approach: One trace per Vendor, with y=Total? 
    # User asked for "Stacked Bar Chart" where X=Vendor, Y=Amount.
    # "Stacked" usually means multiple segments per bar (e.g. multiple tenders).
    # So for each Vendor, we have a stack of Tenders.
    # To do this in Plotly efficiently with many vendors:
    # We can use `px.bar` but that might be slow with thousands of tenders.
    # Let's try `go.Bar`. If we want individual tenders to be hoverable segments, 
    # we need a trace per tender group or use "stack" mode with many traces.
    # Actually, if we have 1000 tenders, 1000 traces is heavy but manageable.
    # But if we have 10k, it's bad.
    # Optimization: Group by Vendor and Tender?
    # Let's assume we want to see the breakdown.
    # If we just want the total, it's one bar.
    # User said "Stacked bar chart... from top to bottom... X axis is vendor, Y is amount".
    # And "Mouse hover... show tender name and amount".
    # This implies we need the segments.
    
    # Let's iterate by country
    full_html_parts = []
    
    # We will build a custom HTML because Plotly's legend is not a good filter for this.
    # We will generate 5 separate Plotly divs or one big one.
    # One big one is easier for alignment.
    
    # However, to make the "Checkboxes" work efficiently for filtering VENDORS,
    # we need to be able to hide/show specific X-axis categories (Vendors).
    # In Plotly, hiding a category on X-axis is done by updating layout.xaxis.range or filtering data.
    
    # Let's construct the data structure for the custom JS.
    # We will pass the full dataset to JS and let JS build/update the Plotly charts?
    # Or generate the Plotly chart with all data and use JS to update `transforms` or `visible`.
    
    # Simpler approach for "Filtering Vendors":
    # The user wants to filter *out* specific vendors (likely the big ones to see small ones).
    # So we need a list of vendors per country.
    
    # Let's create the traces.
    # To allow "stacking" of tenders, we can't easily have one trace per tender if they share the same X (Vendor).
    # Actually we can. If we have Vendor A with Tender 1 and Tender 2.
    # Trace 1: x=[A], y=[100], name=Tender1
    # Trace 2: x=[A], y=[200], name=Tender2
    # This explodes the number of traces.
    
    # Alternative: One trace per Vendor? No, then we lose the "stack" visual of individual tenders.
    # Alternative: One trace per "Tender Category"? We don't have categories.
    
    # Let's look at the data size.
    # If it's huge, we might need to aggregate.
    # But user wants "Tender Name" on hover.
    # Maybe we can use `customdata` and a single bar per vendor, but that loses the "stack" visual (it would be one solid block).
    # Unless we just stack *everything*.
    # If we have 500 tenders for one vendor, that's a lot of stacks.
    # Maybe the user means "Stacked by Vendor" (which is just a bar chart).
    # "5個堆疊長條圖... X軸代表得標廠商... Y軸代表得標金額... 浮動視窗顯示該標案的名稱"
    # "Stacked bar chart... X=Vendor... Hover=Tender Name".
    # This strongly implies the bar for a vendor is composed of segments (Tenders).
    
    # To avoid 10,000 traces, we can use ONE trace per "Tender" but that's still 10,000 traces.
    # Wait, Plotly `go.Bar` can take arrays.
    # x=[Vendor A, Vendor A, Vendor B], y=[100, 200, 50]
    # If we set `barmode='stack'`, Plotly aggregates them?
    # No, if we provide multiple y values for the same x in *one* trace, it sums them? No, it usually expects unique X.
    # Actually, if we have:
    # Trace 1: x=['A', 'B'], y=[10, 20]
    # Trace 2: x=['A', 'B'], y=[5, 15]
    # This stacks Trace 2 on Trace 1.
    
    # If we have variable tenders per vendor, we can't easily align them into "Series 1", "Series 2".
    # The only way to get true stacks for arbitrary items is:
    # 1. One trace per Tender (heavy).
    # 2. Use a "Histogram" or similar? No.
    
    # Compromise:
    # If the number of tenders is small (< 5000 total), One trace per Tender is okay-ish but slow.
    # If large, we might need to simplify.
    # Let's check the data size first.
    
    print(f"Total records: {len(df)}")
    
    # If we have many records, maybe we group by Vendor and just show "Top 5 Tenders + Others"?
    # Or just try to render it.
    
    # Let's try to generate the traces.
    # To make filtering easy, we assign a "class" or "group" to traces?
    # Plotly doesn't support CSS classes on traces easily for external JS manipulation without `Plotly.restyle`.
    # But `Plotly.restyle` takes indices.
    
    # Better approach for the User's goal ("Filter specific vendors"):
    # If I filter a Vendor, I want to hide ALL tenders (traces) associated with that vendor.
    # OR, if the X-axis is Vendor, I just remove that Vendor from the X-axis?
    # If I remove "Vendor A" from X-axis, all its stacks disappear.
    # This is much easier!
    # We don't need to hide traces. We just need to filter the data shown.
    
    # So, the "Filter" should trigger a re-layout or re-data.
    # Since we want a standalone HTML, we need to embed the data and use JS.
    
    # Strategy:
    # 1. Prepare the full JSON data: { 'Canada': [ {vendor: 'V1', amount: 100, tender: 'T1'}, ... ], ... }
    # 2. Write a JS function that takes a list of "Hidden Vendors" and rebuilds the Plotly traces.
    # 3. On initial load, build all.
    # 4. On checkbox change, update "Hidden Vendors" and call rebuild.
    
    # This is robust and performant enough for < 10k rows.
    
    # Let's prepare the data for export to JSON.
    export_data = {}
    for c in countries:
        country_df = df[df['country'] == c]
        # Get unique vendors for checkboxes
        vendors = sorted(country_df['vendor'].unique().tolist())
        
        # Serialize records
        records = country_df[['vendor', 'amount', 'tender_name', 'currency']].to_dict('records')
        
        export_data[c] = {
            'vendors': vendors,
            'data': records,
            'currency': country_df['currency'].iloc[0] if not country_df.empty else 'USD'
        }
        
    import json
    json_data = json.dumps(export_data)
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Drone Tender Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; display: flex; }}
        #sidebar {{ width: 250px; padding-right: 20px; border-right: 1px solid #ccc; height: 100vh; overflow-y: auto; position: fixed; }}
        #main {{ margin-left: 270px; width: calc(100% - 270px); }}
        .country-section {{ margin-bottom: 20px; }}
        .country-title {{ font-weight: bold; margin-bottom: 5px; cursor: pointer; }}
        .vendor-list {{ display: none; margin-left: 10px; }}
        .vendor-item {{ font-size: 12px; }}
        .chart-container {{ height: 500px; margin-bottom: 50px; }}
    </style>
</head>
<body>

<div id="sidebar">
    <h3>廠商篩選 (Vendor Filter)</h3>
    <div id="filter-container"></div>
</div>

<div id="main">
    <h1>各國無人機標案得標廠商統計</h1>
    <div id="charts"></div>
</div>

<script>
    const rawData = {json_data};
    const countries = ['Canada', 'USA', 'Australia', 'Japan', 'Taiwan'];
    
    // State to track unchecked vendors
    const hiddenVendors = {{}}; // {{ 'Canada': Set(['V1']), ... }}
    // State to track sort order
    const sortOrders = {{}}; // {{ 'Canada': 'amount' }} (default)

    function init() {{
        const filterContainer = document.getElementById('filter-container');
        const chartsContainer = document.getElementById('charts');
        
        countries.forEach(country => {{
            if (!rawData[country]) return;
            
            hiddenVendors[country] = new Set();
            sortOrders[country] = 'amount'; // Default sort by amount
            
            // 1. Create Filter Section
            const section = document.createElement('div');
            section.className = 'country-section';
            
            const title = document.createElement('div');
            title.className = 'country-title';
            title.textContent = country + ' (' + rawData[country].vendors.length + ')';
            title.onclick = () => {{
                const content = section.querySelector('.section-content');
                content.style.display = content.style.display === 'none' ? 'block' : 'none';
            }};
            section.appendChild(title);
            
            const content = document.createElement('div');
            content.className = 'section-content';
            content.style.display = 'none'; // Collapsed by default
            
            // Controls: Sort and Bulk Select
            const controls = document.createElement('div');
            controls.style.marginBottom = '10px';
            controls.style.fontSize = '12px';
            
            // Sort Select
            const sortLabel = document.createElement('span');
            sortLabel.textContent = 'Sort: ';
            const sortSelect = document.createElement('select');
            sortSelect.innerHTML = '<option value="amount">Amount (High-Low)</option><option value="name">Name (A-Z)</option>';
            sortSelect.onchange = (e) => {{
                sortOrders[country] = e.target.value;
                renderVendorList(country, list);
            }};
            controls.appendChild(sortLabel);
            controls.appendChild(sortSelect);
            
            controls.appendChild(document.createElement('br'));
            controls.appendChild(document.createElement('br'));

            // Bulk Buttons
            const btnAll = document.createElement('button');
            btnAll.textContent = 'Select All';
            btnAll.onclick = () => {{
                hiddenVendors[country].clear();
                renderVendorList(country, list);
                updateChart(country);
            }};
            
            const btnNone = document.createElement('button');
            btnNone.textContent = 'Deselect All';
            btnNone.onclick = () => {{
                rawData[country].vendors.forEach(v => hiddenVendors[country].add(v));
                renderVendorList(country, list);
                updateChart(country);
            }};
            
            controls.appendChild(btnAll);
            controls.appendChild(document.createTextNode(' '));
            controls.appendChild(btnNone);
            
            content.appendChild(controls);

            const list = document.createElement('div');
            list.className = 'vendor-list';
            list.style.display = 'block'; // Always visible inside content
            content.appendChild(list);
            
            section.appendChild(content);
            filterContainer.appendChild(section);
            
            // Render initial list
            renderVendorList(country, list);
            
            // 2. Create Chart Container
            const wrapper = document.createElement('div');
            wrapper.className = 'chart-wrapper';
            wrapper.style.overflowX = 'auto'; // Enable horizontal scroll
            wrapper.style.width = '100%';
            
            const chartDiv = document.createElement('div');
            chartDiv.id = `chart-${{country}}`;
            chartDiv.className = 'chart-container';
            chartDiv.style.height = '100vh';
            
            wrapper.appendChild(chartDiv);
            chartsContainer.appendChild(wrapper);
            
            // 3. Initial Draw
            updateChart(country);
        }});
    }}
    
    function renderVendorList(country, container) {{
        container.innerHTML = '';
        const vendors = [...rawData[country].vendors];
        const sortType = sortOrders[country];
        
        // Calculate totals for sorting by amount
        const vendorTotals = {{}};
        if (sortType === 'amount') {{
            rawData[country].data.forEach(d => {{
                vendorTotals[d.vendor] = (vendorTotals[d.vendor] || 0) + d.amount;
            }});
            vendors.sort((a, b) => (vendorTotals[b] || 0) - (vendorTotals[a] || 0));
        }} else {{
            vendors.sort();
        }}
        
        vendors.forEach(vendor => {{
            const item = document.createElement('div');
            item.className = 'vendor-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = !hiddenVendors[country].has(vendor);
            checkbox.id = `cb-${{country}}-${{vendor}}`;
            checkbox.onchange = (e) => {{
                if (e.target.checked) {{
                    hiddenVendors[country].delete(vendor);
                }} else {{
                    hiddenVendors[country].add(vendor);
                }}
                updateChart(country);
            }};
            
            const label = document.createElement('label');
            label.htmlFor = `cb-${{country}}-${{vendor}}`;
            label.textContent = vendor;
            
            item.appendChild(checkbox);
            item.appendChild(label);
            container.appendChild(item);
        }});
    }}
    
    function isCJK(str) {{
        // Regex to check for common CJK ranges
        return /[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\uff00-\uff9f\u4e00-\u9faf\u3400-\u4dbf]/.test(str);
    }}

    function formatVendorName(name) {{
        if (isCJK(name)) {{
            // Remove English characters and parentheses containing English
            // 1. Remove (English) or [English]
            let cleaned = name.replace(/\s*[\(\[\uff08\u3010][a-zA-Z\s\.\,\&\-]*[\)\]\uff09\u3011]/g, '');
            // 2. Remove remaining English words
            cleaned = cleaned.replace(/[a-zA-Z]+/g, '');
            // 3. Trim whitespace
            cleaned = cleaned.trim();
            
            // If CJK, split characters with <br> for vertical stacking
            return cleaned.split('').join('<br>');
        }}
        // If English/ASCII, keep horizontal
        return name;
    }}
    
    function updateChart(country) {{
        const data = rawData[country].data;
        const currency = rawData[country].currency;
        const hidden = hiddenVendors[country];
        
        // Filter data
        const filteredData = data.filter(d => !hidden.has(d.vendor));
        
        // Group by Vendor to calculate totals (for sorting X-axis)
        const vendorTotals = {{}};
        filteredData.forEach(d => {{
            vendorTotals[d.vendor] = (vendorTotals[d.vendor] || 0) + d.amount;
        }});
        
        // Sort vendors for X-axis based on current sort order
        const sortedVendors = Object.keys(vendorTotals);
        const sortType = sortOrders[country];
        
        if (sortType === 'amount') {{
            sortedVendors.sort((a, b) => vendorTotals[b] - vendorTotals[a]);
        }} else {{
            sortedVendors.sort();
        }}
        
        // Dynamic Width Calculation for Scrollbar
        // Assume ~30px per bar minimum
        const minBarWidth = 30;
        const calculatedWidth = Math.max(sortedVendors.length * minBarWidth, document.getElementById('main').offsetWidth);
        
        // Prepare annotations for X-axis labels
        const annotations = sortedVendors.map(v => {{
            const is_cjk = isCJK(v);
            return {{
                x: v,
                y: 0,
                xref: 'x',
                yref: 'paper',
                text: formatVendorName(v),
                showarrow: false,
                xanchor: 'center',
                yanchor: 'top',
                textangle: is_cjk ? 0 : -90,
                yshift: -10,
                font: {{ size: 11 }}
            }};
        }});
        
        const traces = [];
        
        filteredData.forEach(d => {{
            traces.push({{
                x: [d.vendor],
                y: [d.amount],
                name: d.tender_name,
                type: 'bar',
                text: d.tender_name,
                hovertemplate: '<b>Vendor</b>: %{{x}}<br><b>Tender</b>: ' + d.tender_name + '<br><b>Amount</b>: %{{y:,.0f}} ' + currency + '<extra></extra>',
                showlegend: false,
                marker: {{
                    line: {{ width: 0.5, color: 'white' }}
                }}
            }});
        }});
        
        const layout = {{
            title: country + ' Drone Tenders (' + currency + ')',
            barmode: 'stack',
            width: calculatedWidth, // Apply dynamic width
            xaxis: {{
                // Removed title as requested
                categoryorder: 'array',
                categoryarray: sortedVendors,
                showticklabels: false, // Hide standard ticks
                automargin: true
            }},
            yaxis: {{
                title: 'Amount (' + currency + ')',
                automargin: true
            }},
            annotations: annotations,
            hovermode: 'closest',
            margin: {{ b: 250 }}, // Large bottom margin for labels
            responsive: false // Disable responsive resizing to enforce width
        }};
        
        Plotly.react(`chart-${{country}}`, traces, layout);
    }}
    
    init();
</script>

</body>
</html>
    """
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Dashboard generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dashboard()
