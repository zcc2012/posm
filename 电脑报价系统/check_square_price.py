import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials LIMIT 20')
results = cursor.fetchall()

print('材料信息:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

conn.close()