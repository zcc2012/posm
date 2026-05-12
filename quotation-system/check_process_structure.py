import sqlite3

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查看processes表结构
print('=== processes表结构 ===')
cursor.execute("PRAGMA table_info(processes)")
columns = cursor.fetchall()
for col in columns:
    print(f'列名: {col[1]}, 类型: {col[2]}, 非空: {col[3]}, 默认值: {col[4]}, 主键: {col[5]}')

print('\n=== processes表所有数据 ===')
cursor.execute("SELECT * FROM processes")
results = cursor.fetchall()

for row in results:
    print(f'完整记录: {row}')

# 检查是否有pricing_standards表
print('\n=== 检查pricing_standards表 ===')
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pricing_standards'")
    table_exists = cursor.fetchone()
    if table_exists:
        print('pricing_standards表存在')
        cursor.execute("SELECT * FROM pricing_standards WHERE process_name LIKE '%模切%' OR process_name LIKE '%光油%' OR process_name LIKE '%光膜%'")
        pricing_results = cursor.fetchall()
        print('相关定价标准:')
        for row in pricing_results:
            print(f'ID: {row[0]}, 工艺名: {row[1]}, 基础价格: {row[2]}, 平方价格: {row[3]}')
    else:
        print('pricing_standards表不存在')
except Exception as e:
    print(f'检查pricing_standards表时出错: {e}')

conn.close()