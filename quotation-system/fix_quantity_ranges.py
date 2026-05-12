#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def fix_quantity_ranges():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("=== 检查所有标准的数量范围 ===")
    cursor.execute('''
        SELECT type, name, min_quantity, max_quantity
        FROM pricing_standards 
        ORDER BY type, name
    ''')
    
    all_standards = cursor.fetchall()
    problematic_standards = []
    
    for row in all_standards:
        type_name, name, min_qty, max_qty = row
        print(f"{type_name} - {name}: {min_qty} - {max_qty}")
        
        # 检查异常的数量范围
        if min_qty > max_qty or min_qty > 100000 or max_qty < 100:
            problematic_standards.append(row)
            print(f"  ❌ 异常数量范围")
    
    print(f"\n发现 {len(problematic_standards)} 个异常的数量范围")
    
    if problematic_standards:
        print("\n=== 修正数量范围 ===")
        
        # 修正所有标准的数量范围为合理值
        cursor.execute('''
            UPDATE pricing_standards 
            SET min_quantity = 1, max_quantity = 999999
            WHERE min_quantity > max_quantity OR min_quantity > 100000 OR max_quantity < 100
        ''')
        
        affected_rows = cursor.rowcount
        print(f"✅ 已修正 {affected_rows} 个标准的数量范围")
        conn.commit()
        
        # 验证修正结果
        print("\n=== 验证修正结果 ===")
        cursor.execute('''
            SELECT type, name, min_quantity, max_quantity
            FROM pricing_standards 
            ORDER BY type, name
        ''')
        
        fixed_standards = cursor.fetchall()
        for row in fixed_standards:
            type_name, name, min_qty, max_qty = row
            print(f"{type_name} - {name}: {min_qty} - {max_qty}")
    
    print("\n=== 重新测试300x200x1000的匹配 ===")
    cursor.execute('''
        SELECT type, name, base_price, square_price
        FROM pricing_standards 
        WHERE 300 >= min_length AND 300 <= max_length
        AND 200 >= min_width AND 200 <= max_width
        AND 1000 >= min_quantity AND 1000 <= max_quantity
        ORDER BY type, name
    ''')
    
    matching_standards = cursor.fetchall()
    if matching_standards:
        print(f"找到 {len(matching_standards)} 个匹配的标准:")
        for row in matching_standards:
            print(f"  {row[0]} - {row[1]} - 基础{row[2]}元 - 平方{row[3]}元/m²")
    else:
        print("仍未找到匹配的标准")
    
    conn.close()

if __name__ == '__main__':
    fix_quantity_ranges()