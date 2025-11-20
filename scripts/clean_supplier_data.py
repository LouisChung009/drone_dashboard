#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 drone_tenders.db 中的 supplier_name 資料
將混在一起的JSON資料分解為獨立欄位
"""

import sqlite3
import json
from datetime import datetime

def clean_supplier_data():
    # 連接資料庫
    conn = sqlite3.connect('data/drone_tenders.db')
    conn.text_factory = str
    cursor = conn.cursor()
    
    print("開始清理 supplier_name 資料...")
    print("="*80)
    
    # 檢查新欄位是否存在，如果存在則刪除
    cursor.execute("PRAGMA table_info(drone_tenders)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    
    if 'supplier_name_cleaned' in existing_cols:
        print("刪除現有的新欄位...")
        cursor.execute("ALTER TABLE drone_tenders DROP COLUMN supplier_name_cleaned")
    if 'uei_sam' in existing_cols:
        cursor.execute("ALTER TABLE drone_tenders DROP COLUMN uei_sam")
    if 'cage_code' in existing_cols:
        cursor.execute("ALTER TABLE drone_tenders DROP COLUMN cage_code")
    
    # 新增三個欄位
    print("新增欄位: supplier_name_cleaned, uei_sam, cage_code")
    cursor.execute("ALTER TABLE drone_tenders ADD COLUMN supplier_name_cleaned TEXT")
    cursor.execute("ALTER TABLE drone_tenders ADD COLUMN uei_sam TEXT")
    cursor.execute("ALTER TABLE drone_tenders ADD COLUMN cage_code TEXT")
    
    # 查詢所有記錄
    cursor.execute("SELECT id, supplier_name FROM drone_tenders")
    all_records = cursor.fetchall()
    
    total = len(all_records)
    json_count = 0
    text_count = 0
    empty_count = 0
    
    print(f"\n處理 {total} 筆記錄...")
    print("-"*80)
    
    # 處理每一筆記錄
    for id, supplier_name in all_records:
        cleaned_name = None
        uei_sam = None
        cage_code = None
        
        if supplier_name and supplier_name.strip():
            # 嘗試解析為JSON
            if supplier_name.startswith('{'):
                try:
                    data = json.loads(supplier_name)
                    if data:  # 不是空的JSON物件
                        cleaned_name = data.get('name')
                        uei_sam = data.get('ueiSAM')
                        cage_code = data.get('cageCode')
                        json_count += 1
                    else:
                        # 空的JSON物件
                        empty_count += 1
                except json.JSONDecodeError as e:
                    print(f"  [警告] ID {id}: JSON解析失敗: {str(e)[:50]}")
                    cleaned_name = supplier_name
                    text_count += 1
            else:
                # 普通文字
                cleaned_name = supplier_name
                text_count += 1
        else:
            empty_count += 1
        
        # 更新資料庫
        cursor.execute("""
            UPDATE drone_tenders 
            SET supplier_name_cleaned = ?, uei_sam = ?, cage_code = ?
            WHERE id = ?
        """, (cleaned_name, uei_sam, cage_code, id))
    
    # 提交變更
    conn.commit()
    
    print(f"\n資料清理完成!")
    print("="*80)
    print(f"總記錄數: {total}")
    print(f"  - JSON格式: {json_count} 筆")
    print(f"  - 文字格式: {text_count} 筆")
    print(f"  - 空值: {empty_count} 筆")
    print("="*80)
    
    # 顯示清理後的結果
    print("\n清理後的資料範例:")
    print("-"*80)
    cursor.execute("""
        SELECT id, supplier_name_cleaned, uei_sam, cage_code 
        FROM drone_tenders 
        WHERE supplier_name_cleaned IS NOT NULL 
        LIMIT 10
    """)
    
    for id, name, uei, cage in cursor.fetchall():
        print(f"\nID: {id}")
        print(f"  Supplier Name: {name}")
        print(f"  UEI SAM: {uei}")
        print(f"  CAGE Code: {cage}")
    
    conn.close()
    print("\n" + "="*80)
    print("完成！資料已保存到資料庫")

if __name__ == "__main__":
    clean_supplier_data()
