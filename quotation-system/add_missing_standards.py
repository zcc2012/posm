import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 添加光油工艺的定价标准
varnish_standards = [
    ('varnish', '4开光油', 0, 650, 0, 450, 1, 10000, 80, 0.1),
    ('varnish', '对开光油', 650, 1020, 450, 720, 1, 100000, 120, 0.15),
    ('varnish', '全开光油', 1020, 1420, 720, 1020, 1, 999999, 150, 0.2)
]

# 添加覆膜工艺的定价标准
lamination_standards = [
    ('lamination', '4开覆膜', 0, 650, 0, 450, 1, 10000, 100, 0.2),
    ('lamination', '对开覆膜', 650, 1020, 450, 720, 1, 100000, 150, 0.25),
    ('lamination', '全开覆膜', 1020, 1420, 720, 1020, 1, 999999, 200, 0.3)
]

current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

print('=== 添加光油工艺定价标准 ===')
for standard in varnish_standards:
    cursor.execute('''
        INSERT INTO pricing_standards 
        (type, name, min_length, max_length, min_width, max_width, 
         min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', standard + ('光油工艺定价标准', 1, current_time))
    print(f'添加光油标准: {standard[1]}')

print('\n=== 添加覆膜工艺定价标准 ===')
for standard in lamination_standards:
    cursor.execute('''
        INSERT INTO pricing_standards 
        (type, name, min_length, max_length, min_width, max_width, 
         min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', standard + ('覆膜工艺定价标准', 1, current_time))
    print(f'添加覆膜标准: {standard[1]}')

# 提交更改
conn.commit()

# 验证添加结果
print('\n=== 验证添加结果 ===')
cursor.execute("SELECT * FROM pricing_standards WHERE type IN ('varnish', 'lamination')")
results = cursor.fetchall()

for row in results:
    print(f'ID: {row[0]}, 类型: {row[1]}, 名称: {row[2]}, 基础价格: {row[9]}, 平方价格: {row[10]}')

conn.close()
print('\n定价标准添加完成！')