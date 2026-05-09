import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

print('=== 印刷标准 ===')
cursor.execute('SELECT * FROM pricing_standards WHERE type="printing" ORDER BY id')
for r in cursor.fetchall():
    print(f'ID:{r[0]}, 名称:{r[2]}, 长度:{r[3]}-{r[4]}, 宽度:{r[5]}-{r[6]}, 基础价:{r[9]}, 平方价:{r[10]}')

print('\n=== 光油标准 ===')
cursor.execute('SELECT * FROM pricing_standards WHERE type="varnish" ORDER BY id')
for r in cursor.fetchall():
    print(f'ID:{r[0]}, 名称:{r[2]}, 长度:{r[3]}-{r[4]}, 宽度:{r[5]}-{r[6]}, 基础价:{r[9]}, 平方价:{r[10]}')

print('\n=== 模切标准 ===')
cursor.execute('SELECT * FROM pricing_standards WHERE type="die-cutting" ORDER BY id')
for r in cursor.fetchall():
    print(f'ID:{r[0]}, 名称:{r[2]}, 长度:{r[3]}-{r[4]}, 宽度:{r[5]}-{r[6]}, 基础价:{r[9]}, 平方价:{r[10]}')

print('\n=== 测试1200x1600尺寸匹配 ===')
length, width, quantity = 1200, 1600, 1

# 测试印刷匹配
cursor.execute('''
    SELECT * FROM pricing_standards 
    WHERE type="printing" AND is_active=1 
    AND ? >= min_length AND ? <= max_length
    AND ? >= min_width AND ? <= max_width
    AND ? >= min_quantity AND ? <= max_quantity
    ORDER BY created_at DESC
    LIMIT 1
''', (length, length, width, width, quantity, quantity))
result = cursor.fetchone()
if result:
    print(f'印刷匹配: {result[2]} (基础价:{result[9]}, 平方价:{result[10]})')
else:
    print('印刷无匹配')

# 测试光油匹配
cursor.execute('''
    SELECT * FROM pricing_standards 
    WHERE type="varnish" AND is_active=1 
    AND ? >= min_length AND ? <= max_length
    AND ? >= min_width AND ? <= max_width
    AND ? >= min_quantity AND ? <= max_quantity
    ORDER BY created_at DESC
    LIMIT 1
''', (length, length, width, width, quantity, quantity))
result = cursor.fetchone()
if result:
    print(f'光油匹配: {result[2]} (基础价:{result[9]}, 平方价:{result[10]})')
else:
    print('光油无匹配')

conn.close()