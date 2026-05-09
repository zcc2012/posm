#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 检查是否已有印刷标准
cursor.execute("SELECT * FROM pricing_standards WHERE type = 'printing'")
existing_printing = cursor.fetchall()

if existing_printing:
    print('=== 现有印刷工艺定价标准 ===')
    for row in existing_printing:
        print(f'ID: {row[0]}, 类型: {row[1]}, 名称: {row[2]}, 基础价格: {row[9]}, 平方价格: {row[10]}')
else:
    print('=== 添加印刷工艺定价标准 ===')
    
    # 添加印刷工艺的定价标准
    printing_standards = [
        ('printing', '4开印刷', 480, 720, 340, 520, 1, 10000, 200, 0.05),
        ('printing', '对开印刷', 650, 1020, 450, 720, 1, 100000, 300, 0.08),
        ('printing', '全开印刷', 1020, 1420, 720, 1020, 1, 999999, 400, 0.1)
    ]
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    for standard in printing_standards:
        cursor.execute('''
            INSERT INTO pricing_standards 
            (type, name, min_length, max_length, min_width, max_width, 
             min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', standard + ('印刷工艺定价标准', 1, current_time))
        print(f'添加印刷标准: {standard[1]}')
    
    # 提交更改
    conn.commit()
    
    # 验证添加结果
    print('\n=== 验证添加结果 ===')
    cursor.execute("SELECT * FROM pricing_standards WHERE type = 'printing'")
    results = cursor.fetchall()
    
    for row in results:
        print(f'ID: {row[0]}, 类型: {row[1]}, 名称: {row[2]}, 基础价格: {row[9]}, 平方价格: {row[10]}')
    
    print('\n印刷定价标准添加完成！')

conn.close()