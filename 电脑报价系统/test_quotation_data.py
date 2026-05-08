import sqlite3
import json

# 连接数据库
conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 查看材料数据
print('=== 材料数据检查 ===')
cursor.execute('SELECT id, name, specification, unit_price, square_price FROM materials WHERE square_price > 0 LIMIT 5')
results = cursor.fetchall()

for r in results:
    print(f'ID: {r[0]}, 名称: {r[1]}, 规格: {r[2]}, 单价: {r[3]}, 平方价: {r[4]}')

# 模拟报价单数据
print('\n=== 模拟报价单数据 ===')
test_quotation_data = {
    "project_sets": 1,
    "items": [
        {
            "material_id": "1",
            "material_name": "300g单涂白卡",
            "quantity": 1,
            "length": 1000,
            "width": 700,
            "process_id": "1",
            "process_name": "模切",
            "unit_price": 0,
            "total_price": 0,
            "area": 1.029,  # (1000+30)*(700+30)/1000000
            "material_square_price": 50.0
        },
        {
            "material_id": "2",
            "material_name": "写真纸 低档",
            "quantity": 1,
            "length": 1000,
            "width": 700,
            "process_id": "2",
            "process_name": "印刷",
            "unit_price": 0,
            "total_price": 0,
            "area": 1.029,
            "material_square_price": 80.0
        }
    ]
}

print('测试数据:')
print(json.dumps(test_quotation_data, indent=2, ensure_ascii=False))

# 模拟主材料费用计算
print('\n=== 主材料费用计算测试 ===')
project_sets = test_quotation_data['project_sets']
main_material_cost = 0

for item in test_quotation_data['items']:
    # 简化判断条件：不是画面、印刷相关的都算主材料
    if (not '画面' in item['material_name'] and not '印刷' in item['material_name'] and 
        not '印刷' in item['process_name'] and not '写真' in item['process_name'] and 
        not 'UV' in item['process_name']):
        
        quantity = item['quantity'] or 1
        area = item['area']
        material_square_price = item['material_square_price'] or 0
        
        # 主材料费用 = 材料平方单价 * 面积 * 项目套数
        material_cost = material_square_price * area * project_sets
        
        main_material_cost += material_cost
        print(f'主材料: {item["material_name"]}, 平方单价: {material_square_price}, 面积: {area:.4f}, 项目套数: {project_sets}, 费用: {material_cost:.2f}元')
        print(f'主材料判断条件通过: 材料名称不包含画面/印刷，工艺名称不包含印刷/写真/UV')
    else:
        print(f'跳过非主材料: {item["material_name"]}, 工艺: {item["process_name"]}')

print(f'\n总主材料费用: {main_material_cost:.2f}元')

conn.close()