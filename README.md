# 無人機標案資料分析專案 (Drone Tender Analysis)

本專案旨在分析無人機相關的政府標案資料，並產出視覺化報表。

## 功能
1. **資料匯出**: 將 SQLite 資料庫中的標案資料匯出為 Excel 檔案 (`data/drone_tenders_export.xlsx`)。
2. **資料視覺化**: 
   - 產生互動式堆疊長條圖 (`drone_tenders_chart.html`)。
   - **進階儀表板**: 包含廠商篩選功能的客製化圖表 (`drone_tenders_chart_v2.html`)。

## 檔案說明
- `export_tenders.py`: 匯出資料至 Excel 的 Python 腳本。
- `visualize_tenders.py`: 產生基本圖表的 Python 腳本。
- `generate_custom_chart.py`: 產生含篩選功能儀表板的 Python 腳本。
- `data/drone_tenders.db`: 原始資料庫 (SQLite)。
- `data/drone_tenders_export.xlsx`: 匯出的 Excel 報表。
- `drone_tenders_chart_v2.html`: **推薦使用**的互動式儀表板。

## 如何使用
1. 確保已安裝 Python 及相關套件 (`pandas`, `plotly`, `openpyxl`)。
2. 執行 `python generate_custom_chart.py` 以更新圖表。
3. 直接用瀏覽器開啟 `drone_tenders_chart_v2.html` 檢視分析結果。
