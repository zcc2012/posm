#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_4k_printing():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("=== 检查4开机器尺寸设置 ===")
    cursor.execute('''
        SELECT name, min_length, max_length, min_width, max_width, min_quantity, max_quantity
        FROM pricing_standards 
        WHERE name LIKE '%4开%' AND type='printing'
    ''')
    
    row = cursor.fetchone()
    if row:
        print(f"4开机器尺寸: {row[1]}-{row[2]}mm × {row[3]}-{row[4]}mm")
        print(f"数量范围: {row[5]}-{row[6]}")
        print("\n测试尺寸300x200是否匹配:")
        print(f"长度匹配: {row[1]} <= 300 <= {row[2]} = {row[1] <= 300 <= row[2]}")
        print(f"宽度匹配: {row[3]} <= 200 <= {row[4]} = {row[3] <= 200 <= row[4]}")
        print(f"数量匹配: {row[5]} <= 1000 <= {row[6]} = {row[5] <= 1000 <= row[6]}")
        
        # 检查问题
        if not (row[1] <= 300 <= row[2]):
            print(f"❌ 长度不匹配: 300不在{row[1]}-{row[2]}范围内")
        if not (row[3] <= 200 <= row[4]):
            print(f"❌ 宽度不匹配: 200不在{row[3]}-{row[4]}范围内")
        if not (row[5] <= 1000 <= row[6]):
            print(f"❌ 数量不匹配: 1000不在{row[5]}-{row[6]}范围内")
    else:
        print("未找到4开机器标准")
    
    print("\n=== 修正4开机器尺寸范围 ===")
    # 4开纸张标准尺寸通常是390×543mm，但机器应该能处理更小的尺寸
    cursor.execute('''
        UPDATE pricing_standards 
        SET min_length = 1, min_width = 1
        WHERE name LIKE '%4开%' AND type='printing'
    ''')
    
    affected_rows = cursor.rowcount
    if affected_rows > 0:
        print(f"✅ 已修正4开机器尺寸范围，影响{affected_rows}行")
        conn.commit()
        
        # 重新检查
        cursor.execute('''
            SELECT name, min_length, max_length, min_width, max_width
            FROM pricing_standards 
            WHERE name LIKE '%4开%' AND type='printing'
        ''')
        
        row = cursor.fetchone()
        print(f"修正后尺寸: {row[1]}-{row[2]}mm × {row[3]}-{row[4]}mm")
        print(f"现在300x200匹配: 长度{row[1] <= 300 <= row[2]}, 宽度{row[3] <= 200 <= row[4]}")
    else:
        print("未找到需要修正的记录")
    
    conn.close()

if __name__ == '__main__':
    check_4k_printing()