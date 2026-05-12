import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查看pricing_standards表结构
cursor.execute('PRAGMA table_info(pricing_standards)')
columns = cursor.fetchall()
print('pricing_standards表结构:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 查看所有工艺数据
cursor.execute('SELECT * FROM pricing_standards')
results = cursor.fetchall()
print('\n所有工艺数据:')
for r in results:
    print(f'ID: {r[0]}, 类型: {r[1]}, 名称: {r[2]}, 基础价格: {r[9]}, 平方价格: {r[10]}')

conn.close()