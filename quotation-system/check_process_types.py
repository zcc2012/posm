import sqlite3

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查询模切、光油、光膜相关工艺
print('=== 模切、光油、光膜相关工艺 ===')
cursor.execute("SELECT * FROM processes WHERE name LIKE '%模切%' OR name LIKE '%光油%' OR name LIKE '%光膜%'")
results = cursor.fetchall()

if results:
    for row in results:
        print(f'ID: {row[0]}, 名称: {row[1]}, 价格: {row[2]}元')
else:
    print('未找到模切、光油、光膜相关工艺')

print('\n=== 所有工艺列表 ===')
cursor.execute("SELECT * FROM processes ORDER BY name")
all_processes = cursor.fetchall()

for row in all_processes:
    print(f'ID: {row[0]}, 名称: {row[1]}, 价格: {row[2]}元')

conn.close()