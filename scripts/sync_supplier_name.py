#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
將 supplier_name_cleaned 的資料同步回原始 supplier_name 欄位
"""

import sqlite3

def sync_supplier_name():
    # 連接資料庫
    conn = sqlite3.connect('data/drone_tenders.db')
    conn.text_factory = str
    cursor = conn.cursor()
    
    print("開始同步 supplier_name 資料...")
    print("="*80)
    
    # 更新所有有 supplier_name_cleaned 的記錄
    cursor.execute("""
        UPDATE drone_tenders 
        SET supplier_name = supplier_name_cleaned
        WHERE supplier_name_cleaned IS NOT NULL
    """)
    
    updated_count = cursor.rowcount
    conn.commit()
    
    print(f"已更新 {updated_count} 筆記錄的 supplier_name")
    print("="*80)
    
    # 驗證結果
    print("\n驗證結果 - 查看更新後的資料範例:")
    print("-"*80)
    
    cursor.execute("""
        SELECT id, supplier_name, uei_sam, cage_code 
        FROM drone_tenders 
        WHERE supplier_name IS NOT NULL 
        LIMIT 10
    """)
    
    for id, name, uei, cage in cursor.fetchall():
        print(f"\nID: {id}")
        print(f"  supplier_name: {name}")
        print(f"  uei_sam: {uei}")
        print(f"  cage_code: {cage}")
    
    # 統計
    cursor.execute("SELECT COUNT(*) FROM drone_tenders WHERE supplier_name IS NOT NULL")
    name_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM drone_tenders")
    total = cursor.fetchone()[0]
    
    print("\n\n統計:")
    print("="*80)
    print(f"總記錄數: {total}")
    print(f"有 supplier_name: {name_count}")
    
    conn.close()
    print("\n完成！原始 supplier_name 已更新為清理後的資料")

if __name__ == "__main__":
    sync_supplier_name()
