import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 检查材料数据
print('=== 检查材料数据 ===')
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials WHERE square_price > 0 LIMIT 10')
results = cursor.fetchall()

print('有平方单价的材料:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

# 检查工艺数据
print('\n=== 检查工艺数据 ===')
cursor.execute('SELECT id, name, unit_price, square_price FROM processes LIMIT 10')
results = cursor.fetchall()

print('工艺数据:')
for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 单价: {r[2]}, 平方价: {r[3]}')

conn.close()

print('\n=== 调试建议 ===')
print('1. 在浏览器中打开开发者工具 (F12)')
print('2. 切换到 Console 标签页')
print('3. 创建新报价单，选择材料和工艺')
print('4. 点击完成报价单')
print('5. 在报价单显示页面查看控制台输出')
print('6. 检查以下信息:')
print('   - 材料的 material_square_price 值')
print('   - 主材料判断条件是否通过')
print('   - 计算过程中的各个参数值')
print('\n如果 material_square_price 为 0，说明数据传递有问题')
print('如果 material_square_price 有值但主材料费用仍为 0，说明判断条件有问题')