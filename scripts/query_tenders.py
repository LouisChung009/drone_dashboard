#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查詢 drone_tenders.db 資料的工具
可以分頁查看所有資料，或用 JSON 格式匯出
"""

import sqlite3
import json
import sys
from tabulate import tabulate

def view_tenders(page=1, page_size=20, output_format='table'):
    """
    查詢並顯示 drone_tenders 資料
    
    Args:
        page: 頁碼 (1 開始)
        page_size: 每頁筆數
        output_format: 'table' 或 'json'
    """
    conn = sqlite3.connect('data/drone_tenders.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 計算總數
    cursor.execute("SELECT COUNT(*) FROM drone_tenders")
    total = cursor.fetchone()[0]
    
    # 計算 OFFSET
    offset = (page - 1) * page_size
    
    # 查詢資料
    cursor.execute("""
        SELECT 
            id,
            source_name,
            title,
            supplier_name_cleaned as supplier_name,
            uei_sam,
            cage_code,
            award_amount,
            currency,
            award_date,
            agency
        FROM drone_tenders
        ORDER BY id
        LIMIT ? OFFSET ?
    """, (page_size, offset))
    
    rows = cursor.fetchall()
    
    if output_format == 'json':
        # JSON 格式輸出
        data = []
        for row in rows:
            data.append(dict(row))
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        # 表格格式輸出
        headers = list(rows[0].keys()) if rows else []
        data = [list(row) for row in rows]
        
        print(f"\n{'='*120}")
        print(f"第 {page} 頁 (每頁 {page_size} 筆，共 {total} 筆)")
        print(f"{'='*120}\n")
        print(tabulate(data, headers=headers, tablefmt='grid'))
        print(f"\n顯示 {offset + 1} - {min(offset + page_size, total)} 筆")
        print(f"總共 {total} 筆記錄")
    
    conn.close()

def search_supplier(keyword):
    """
    搜尋特定廠商
    """
    conn = sqlite3.connect('data/drone_tenders.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            title,
            supplier_name_cleaned as supplier_name,
            uei_sam,
            cage_code,
            award_amount,
            award_date
        FROM drone_tenders
        WHERE supplier_name_cleaned LIKE ? OR uei_sam LIKE ?
        ORDER BY id
    """, (f'%{keyword}%', f'%{keyword}%'))
    
    rows = cursor.fetchall()
    
    if rows:
        headers = list(rows[0].keys())
        data = [list(row) for row in rows]
        print(f"\n找到 {len(rows)} 筆記錄:\n")
        print(tabulate(data, headers=headers, tablefmt='grid'))
    else:
        print(f"找不到包含 '{keyword}' 的記錄")
    
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == 'search' and len(sys.argv) > 2:
            search_supplier(sys.argv[2])
        elif command.isdigit():
            view_tenders(page=int(command))
        else:
            print(f"用法:")
            print(f"  python scripts/query_tenders.py               # 查看第 1 頁")
            print(f"  python scripts/query_tenders.py 2             # 查看第 2 頁")
            print(f"  python scripts/query_tenders.py search KEYWORD  # 搜尋廠商")
    else:
        view_tenders(page=1)
