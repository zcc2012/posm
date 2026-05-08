import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('数据库中的表:')
for table in tables:
    print(f'- {table[0]}')

# 查看工艺相关的表
for table_name in ['processes', 'process', 'pricing_standards']:
    try:
        cursor.execute(f'SELECT * FROM {table_name} LIMIT 5')
        results = cursor.fetchall()
        print(f'\n{table_name}表数据:')
        for r in results:
            print(r)
    except sqlite3.OperationalError as e:
        print(f'\n{table_name}表不存在: {e}')

conn.close()