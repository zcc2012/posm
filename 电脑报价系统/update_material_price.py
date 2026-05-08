import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 更新300g灰底白板的平方价格为5.0元
cursor.execute('UPDATE materials SET square_price = 5.0 WHERE name = "300g灰底白板"')
conn.commit()
print('已更新300g灰底白板的平方价格为5.0元')

# 查看更新后的结果
cursor.execute('SELECT id, name, square_price FROM materials WHERE name LIKE "%300g%"')
results = cursor.fetchall()
print('更新后的材料价格:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 平方价: {r[2]}')

conn.close()