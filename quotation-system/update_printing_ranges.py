import sqlite3

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

print('更新前的印刷标准:')
cursor.execute("SELECT * FROM pricing_standards WHERE type='printing' ORDER BY id")
records = cursor.fetchall()
for r in records:
    print(f'ID: {r[0]}, 名称: {r[2]}, 长度范围: {r[3]}-{r[4]}, 宽度范围: {r[5]}-{r[6]}')

# 按照小于和大于等于的方式更新尺寸范围
print('\n开始更新尺寸范围...')

# 更新4开机器：长度 0-719, 宽度 0-519
cursor.execute("""
    UPDATE pricing_standards 
    SET min_length = 0, max_length = 719, min_width = 0, max_width = 519
    WHERE id = 4 AND name = '4开机器'
""")
print('已更新4开机器: 长度 0-719, 宽度 0-519')

# 更新对开机：长度 720-1019, 宽度 520-719
cursor.execute("""
    UPDATE pricing_standards 
    SET min_length = 720, max_length = 1019, min_width = 520, max_width = 719
    WHERE id = 2 AND name = '对开机'
""")
print('已更新对开机: 长度 720-1019, 宽度 520-719')

# 更新全开机：长度 1020-1419, 宽度 720-1019
cursor.execute("""
    UPDATE pricing_standards 
    SET min_length = 1020, max_length = 1419, min_width = 720, max_width = 1019
    WHERE id = 1 AND name = '全开机'
""")
print('已更新全开机: 长度 1020-1419, 宽度 720-1019')

# 更新大全开：长度 1420-1620, 宽度 1020-1220 (保持不变)
cursor.execute("""
    UPDATE pricing_standards 
    SET min_length = 1420, max_length = 1620, min_width = 1020, max_width = 1220
    WHERE id = 34 AND name = '大全开'
""")
print('已更新大全开: 长度 1420-1620, 宽度 1020-1220')

# 提交更改
conn.commit()

print('\n更新后的印刷标准:')
cursor.execute("SELECT * FROM pricing_standards WHERE type='printing' ORDER BY id")
records = cursor.fetchall()
for r in records:
    print(f'ID: {r[0]}, 名称: {r[2]}, 长度范围: {r[3]}-{r[4]}, 宽度范围: {r[5]}-{r[6]}')

print('\n验证重叠情况:')
print('测试尺寸 720x520:')
for r in records:
    if (720 >= r[3] and 720 <= r[4] and 520 >= r[5] and 520 <= r[6]):
        print(f'  匹配: {r[2]}')

print('测试尺寸 1020x720:')
for r in records:
    if (1020 >= r[3] and 1020 <= r[4] and 720 >= r[5] and 720 <= r[6]):
        print(f'  匹配: {r[2]}')

print('测试尺寸 1420x1020:')
for r in records:
    if (1420 >= r[3] and 1420 <= r[4] and 1020 >= r[5] and 1020 <= r[6]):
        print(f'  匹配: {r[2]}')

conn.close()
print('\n更新完成！')