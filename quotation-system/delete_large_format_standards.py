import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查找所有大全开标准
cursor.execute("SELECT id, type, name, created_at FROM pricing_standards WHERE name LIKE '%大全开%' ORDER BY id DESC")
records = cursor.fetchall()

print('需要删除的大全开标准:')
for r in records:
    print(f'ID:{r[0]}, 类型:{r[1]}, 名称:{r[2]}, 创建时间:{r[3]}')
    
    # 删除记录
    cursor.execute("DELETE FROM pricing_standards WHERE id=?", (r[0],))
    print(f'已删除ID:{r[0]}的记录')

# 提交更改
conn.commit()
conn.close()

print('\n所有大全开标准已删除！')