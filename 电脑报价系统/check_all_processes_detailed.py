import sqlite3

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

print('=== 所有工艺详细信息 ===')
cursor.execute("SELECT * FROM processes ORDER BY id")
processes = cursor.fetchall()

for row in processes:
    print(f'ID: {row[0]}, 名称: {row[1]}, 描述: {row[2]}, 价格: {row[3]}, 创建时间: {row[4]}, 单价: {row[5]}, 平方价格: {row[6]}')

print('\n=== 所有定价标准 ===')
cursor.execute("SELECT * FROM pricing_standards ORDER BY id")
standards = cursor.fetchall()

for row in standards:
    print(f'ID: {row[0]}, 类型: {row[1]}, 名称: {row[2]}, 尺寸范围: {row[3]}-{row[4]} x {row[5]}-{row[6]}, 数量: {row[7]}-{row[8]}, 基础价格: {row[9]}, 平方价格: {row[10]}')

# 查找所有包含"光"字的记录
print('\n=== 包含"光"字的工艺和标准 ===')
cursor.execute("SELECT * FROM processes WHERE name LIKE '%光%'")
light_processes = cursor.fetchall()
print('工艺表中包含"光"字的记录:')
for row in light_processes:
    print(f'  {row}')

cursor.execute("SELECT * FROM pricing_standards WHERE name LIKE '%光%'")
light_standards = cursor.fetchall()
print('定价标准表中包含"光"字的记录:')
for row in light_standards:
    print(f'  {row}')

# 查找所有包含"膜"字的记录
print('\n=== 包含"膜"字的工艺和标准 ===')
cursor.execute("SELECT * FROM processes WHERE name LIKE '%膜%'")
film_processes = cursor.fetchall()
print('工艺表中包含"膜"字的记录:')
for row in film_processes:
    print(f'  {row}')

cursor.execute("SELECT * FROM pricing_standards WHERE name LIKE '%膜%'")
film_standards = cursor.fetchall()
print('定价标准表中包含"膜"字的记录:')
for row in film_standards:
    print(f'  {row}')

conn.close()