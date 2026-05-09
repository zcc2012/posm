#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_printing_standards():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("=== 检查印刷标准 ===")
    cursor.execute('''
        SELECT type, name, base_price, square_price, min_length, max_length, min_width, max_width
        FROM pricing_standards 
        WHERE type LIKE '%printing%' OR name LIKE '%印刷%'
        ORDER BY name
    ''')
    
    printing_standards = cursor.fetchall()
    
    if printing_standards:
        print(f"找到 {len(printing_standards)} 个印刷标准:")
        for row in printing_standards:
            print(f"  类型: {row[0]}")
            print(f"  名称: {row[1]}")
            print(f"  基础价格: {row[2]}元")
            print(f"  平方价格: {row[3]}元/m²")
            print(f"  尺寸范围: {row[4]}-{row[5]}mm × {row[6]}-{row[7]}mm")
            print("  ---")
    else:
        print("未找到印刷标准")
    
    print("\n=== 检查所有标准类型 ===")
    cursor.execute('SELECT DISTINCT type FROM pricing_standards ORDER BY type')
    types = cursor.fetchall()
    print("标准类型:")
    for type_row in types:
        print(f"  - {type_row[0]}")
    
    print("\n=== 检查300x200尺寸匹配的标准 ===")
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
        print("未找到匹配的标准")
    
    conn.close()

if __name__ == '__main__':
    check_printing_standards()