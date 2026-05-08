import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查找平方价为9.7的材料
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials WHERE square_price = 9.7')
results = cursor.fetchall()

print('平方价为9.7的材料:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

# 查找平方价接近9.7的材料（可能是浮点数精度问题）
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials WHERE square_price > 9.6 AND square_price < 9.8')
results2 = cursor.fetchall()

print('\n平方价接近9.7的材料:')
for r in results2:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

# 查找所有包含"300g"的材料
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials WHERE name LIKE "%300g%"')
results3 = cursor.fetchall()

print('\n所有包含300g的材料:')
for r in results3:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

conn.close()