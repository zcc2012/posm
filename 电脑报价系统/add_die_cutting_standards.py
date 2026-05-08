#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 添加模切工艺的定价标准
die_cutting_standards = [
    ('die-cutting', '4开模切', 0, 650, 0, 450, 1, 10000, 100, 0.15),
    ('die-cutting', '对开模切', 650, 1020, 450, 720, 1, 100000, 150, 0.2),
    ('die-cutting', '全开模切', 1020, 1420, 720, 1020, 1, 999999, 200, 0.25)
]

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print('=== 添加模切工艺定价标准 ===')
for standard in die_cutting_standards:
    cursor.execute('''
        INSERT INTO pricing_standards 
        (type, name, min_length, max_length, min_width, max_width, 
         min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', standard + ('模切工艺定价标准', 1, current_time))
    print(f'添加模切标准: {standard[1]}')

# 提交更改
conn.commit()

# 验证添加结果
print('\n=== 验证添加结果 ===')
cursor.execute("SELECT * FROM pricing_standards WHERE type = 'die-cutting'")
results = cursor.fetchall()

for row in results:
    print(f'ID: {row[0]}, 类型: {row[1]}, 名称: {row[2]}, 基础价格: {row[9]}, 平方价格: {row[10]}')

conn.close()
print('\n模切定价标准添加完成！')