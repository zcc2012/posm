import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查询四开印刷相关记录
cursor.execute("SELECT * FROM pricing_standards WHERE name LIKE '%4开印刷%' OR name LIKE '%四开印刷%'")
records = cursor.fetchall()

print('四开印刷记录:')
for r in records:
    print(f'ID: {r[0]}, 类型: {r[1]}, 名称: {r[2]}, 长度范围: {r[3]}-{r[4]}, 宽度范围: {r[5]}-{r[6]}, 基础价格: {r[9]}, 平方价格: {r[10]}')

# 查询所有印刷相关记录
print('\n所有印刷记录:')
cursor.execute("SELECT * FROM pricing_standards WHERE type='printing'")
records = cursor.fetchall()
for r in records:
    print(f'ID: {r[0]}, 类型: {r[1]}, 名称: {r[2]}, 长度范围: {r[3]}-{r[4]}, 宽度范围: {r[5]}-{r[6]}, 基础价格: {r[9]}, 平方价格: {r[10]}')

conn.close()