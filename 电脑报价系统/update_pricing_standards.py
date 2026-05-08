#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 添加适合1000x1000尺寸的标准
print('=== 添加适合1000x1000尺寸的标准 ===')

# 当前时间
current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 添加印刷标准
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, 
     min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('printing', '大幅面印刷', 900, 1100, 900, 1100, 1, 999999, 500, 0.1, '适用于1000x1000尺寸的印刷', 1, current_time))
print('添加印刷标准: 大幅面印刷')

# 添加模切标准
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, 
     min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('die-cutting', '大幅面模切', 900, 1100, 900, 1100, 1, 999999, 200, 0.25, '适用于1000x1000尺寸的模切', 1, current_time))
print('添加模切标准: 大幅面模切')

# 添加光油标准
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, 
     min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('varnish', '大幅面光油', 900, 1100, 900, 1100, 1, 999999, 150, 0.2, '适用于1000x1000尺寸的光油', 1, current_time))
print('添加光油标准: 大幅面光油')

# 添加覆膜标准
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, 
     min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('lamination', '大幅面覆膜', 900, 1100, 900, 1100, 1, 999999, 180, 0.3, '适用于1000x1000尺寸的覆膜', 1, current_time))
print('添加覆膜标准: 大幅面覆膜')

# 提交更改
conn.commit()

# 验证添加结果
print('\n=== 验证添加结果 ===')
cursor.execute("SELECT id, type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price FROM pricing_standards WHERE min_length=900 AND max_length=1100")
results = cursor.fetchall()

for row in results:
    print(f'ID: {row[0]}, 类型: {row[1]}, 名称: {row[2]}, 尺寸: {row[3]}-{row[4]}x{row[5]}-{row[6]}, 数量: {row[7]}-{row[8]}, 基础价格: {row[9]}, 平方价格: {row[10]}')

conn.close()
print('\n标准更新完成！')