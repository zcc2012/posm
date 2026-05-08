import sqlite3

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查看pricing_standards表结构
print('=== pricing_standards表结构 ===')
cursor.execute("PRAGMA table_info(pricing_standards)")
columns = cursor.fetchall()
for col in columns:
    print(f'列名: {col[1]}, 类型: {col[2]}, 非空: {col[3]}, 默认值: {col[4]}, 主键: {col[5]}')

print('\n=== pricing_standards表所有数据 ===')
cursor.execute("SELECT * FROM pricing_standards")
results = cursor.fetchall()

for row in results:
    print(f'完整记录: {row}')

# 查找包含模切、光油、光膜的记录
print('\n=== 查找模切、光油、光膜相关记录 ===')
cursor.execute("SELECT * FROM pricing_standards WHERE name LIKE '%模切%' OR name LIKE '%光油%' OR name LIKE '%光膜%'")
related_results = cursor.fetchall()

if related_results:
    for row in related_results:
        print(f'相关记录: {row}')
else:
    print('未找到模切、光油、光膜相关记录')

conn.close()