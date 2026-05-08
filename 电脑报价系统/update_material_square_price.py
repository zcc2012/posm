import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查看现有材料
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials LIMIT 10')
results = cursor.fetchall()

print('更新前的材料信息:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

# 更新一些材料的平方单价
updates = [
    (50.0, 1),  # 假设ID为1的材料设置平方单价为50元/平方米
    (80.0, 2),  # 假设ID为2的材料设置平方单价为80元/平方米
    (120.0, 3), # 假设ID为3的材料设置平方单价为120元/平方米
]

for square_price, material_id in updates:
    cursor.execute('UPDATE materials SET square_price = ? WHERE id = ?', (square_price, material_id))
    print(f'更新材料ID {material_id} 的平方单价为 {square_price} 元/平方米')

conn.commit()

# 查看更新后的材料
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials LIMIT 10')
results = cursor.fetchall()

print('\n更新后的材料信息:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

conn.close()
print('\n材料平方单价更新完成！')