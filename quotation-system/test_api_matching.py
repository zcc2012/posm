import sqlite3
import json

def test_api_matching_logic():
    """测试API匹配逻辑，模拟 /api/pricing_standards/match 的行为"""
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print('=== 测试API匹配逻辑 ===')
    
    # 测试参数
    test_cases = [
        {'length': 300, 'width': 500, 'quantity': 1000, 'process_name': '印刷'},
        {'length': 500, 'width': 300, 'quantity': 1000, 'process_name': '印刷'},
        {'length': 720, 'width': 520, 'quantity': 1000, 'process_name': '印刷'},
        {'length': 1020, 'width': 720, 'quantity': 1000, 'process_name': '印刷'}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f'\n--- 测试案例 {i}: {test_case["length"]}x{test_case["width"]} ---')
        
        length = test_case['length']
        width = test_case['width']
        quantity = test_case['quantity']
        process_name = test_case['process_name']
        
        # 模拟API逻辑：确定工艺类型
        process_type = 'printing'  # 印刷对应printing
        
        print(f'输入参数: 长度={length}, 宽度={width}, 数量={quantity}, 工艺={process_name}')
        print(f'工艺类型: {process_type}')
        
        # 执行数据库查询（完全模拟API的SQL查询）
        query = """
            SELECT * FROM pricing_standards 
            WHERE type = ? 
            AND min_length <= ? AND max_length >= ? 
            AND min_width <= ? AND max_width >= ? 
            AND min_quantity <= ? AND max_quantity >= ? 
            AND is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 1
        """
        
        cursor.execute(query, (process_type, length, length, width, width, quantity, quantity))
        result = cursor.fetchone()
        
        if result:
            print(f'匹配结果: {result[2]} (ID: {result[0]})')
            print(f'  尺寸范围: {result[3]}-{result[4]} x {result[5]}-{result[6]}')
            print(f'  数量范围: {result[7]}-{result[8]}')
            print(f'  价格: 基础价 {result[9]}, 平方价 {result[10]}')
            print(f'  创建时间: {result[12]}')
        else:
            print('未找到匹配的标准!')
            
            # 如果没找到，显示所有可能的候选
            print('\n调试信息 - 检查各个条件:')
            
            # 检查工艺类型
            cursor.execute("SELECT COUNT(*) FROM pricing_standards WHERE type = ? AND is_active = 1", (process_type,))
            type_count = cursor.fetchone()[0]
            print(f'  工艺类型 "{process_type}" 的激活标准数量: {type_count}')
            
            # 检查尺寸条件
            cursor.execute("""
                SELECT name, min_length, max_length, min_width, max_width, min_quantity, max_quantity
                FROM pricing_standards 
                WHERE type = ? AND is_active = 1
            """, (process_type,))
            
            all_standards = cursor.fetchall()
            print('  所有标准的条件检查:')
            for std in all_standards:
                name, min_l, max_l, min_w, max_w, min_q, max_q = std
                length_ok = min_l <= length <= max_l
                width_ok = min_w <= width <= max_w
                quantity_ok = min_q <= quantity <= max_q
                
                print(f'    {name}:')
                print(f'      长度 {length} ∈ [{min_l}, {max_l}]: {length_ok}')
                print(f'      宽度 {width} ∈ [{min_w}, {max_w}]: {width_ok}')
                print(f'      数量 {quantity} ∈ [{min_q}, {max_q}]: {quantity_ok}')
                print(f'      总体匹配: {length_ok and width_ok and quantity_ok}')
    
    conn.close()

if __name__ == '__main__':
    test_api_matching_logic()