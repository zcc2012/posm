#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def test_price_calculation():
    """测试价格计算逻辑"""
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("=== 测试价格计算逻辑 ===")
    
    # 首先检查数据库中的标准
    print("\n=== 数据库中的标准 ===")
    cursor.execute("SELECT id, type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price FROM pricing_standards")
    all_standards = cursor.fetchall()
    for std in all_standards:
        print(f"ID: {std[0]}, 类型: {std[1]}, 名称: {std[2]}, 尺寸: {std[3]}-{std[4]}x{std[5]}-{std[6]}, 数量: {std[7]}-{std[8]}, 基础价格: {std[9]}, 平方价格: {std[10]}")
    
    # 测试数据
    test_cases = [
        {
            'process_name': '印刷+光油+模切',
            'length': 1000,
            'width': 1000, 
            'quantity': 1000,
            'description': '组合工艺：印刷+光油+模切'
        },
        {
            'process_name': '覆膜+模切',
            'length': 1000,
            'width': 1000,
            'quantity': 2000,
            'description': '组合工艺：覆膜+模切'
        },
        {
            'process_name': '印刷+覆膜+模切',
            'length': 1000,
            'width': 1000,
            'quantity': 5000,
            'description': '组合工艺：印刷+覆膜+模切'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试案例 {i}: {test_case['description']} ---")
        print(f"工艺名称: {test_case['process_name']}")
        print(f"尺寸: {test_case['length']}mm x {test_case['width']}mm")
        print(f"数量: {test_case['quantity']}")
        
        # 模拟API匹配逻辑
        process_name = test_case['process_name']
        length = test_case['length']
        width = test_case['width']
        quantity = test_case['quantity']
        
        # 检查各种工艺类型
        process_types = []
        if '印刷' in process_name:
            process_types.append('printing')
        if '切割' in process_name:
            process_types.append('cutting')
        if '模切' in process_name:
            process_types.append('die-cutting')
        if '光油' in process_name:
            process_types.append('varnish')
        if '覆膜' in process_name or '光膜' in process_name:
            process_types.append('lamination')
        
        print(f"识别的工艺类型: {process_types}")
        
        # 查找匹配的标准
        matched_standards = []
        total_base_price = 0
        total_square_price = 0
        
        for process_type in process_types:
            print(f"\n查找 {process_type} 工艺标准:")
            print(f"  条件: 长度={length}mm, 宽度={width}mm, 数量={quantity}")
            
            # 先查询所有该类型的标准，用于调试
            cursor.execute('''
                SELECT id, type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price 
                FROM pricing_standards 
                WHERE type=? AND is_active=1
            ''', (process_type,))
            
            type_standards = cursor.fetchall()
            if type_standards:
                print(f"  找到 {len(type_standards)} 个 {process_type} 类型的标准:")
                for std in type_standards:
                    print(f"    ID: {std[0]}, 名称: {std[2]}, 尺寸: {std[3]}-{std[4]}x{std[5]}-{std[6]}, 数量: {std[7]}-{std[8]}")
                    # 检查每个条件是否匹配
                    length_match = length >= std[3] and length <= std[4]
                    width_match = width >= std[5] and width <= std[6]
                    quantity_match = quantity >= std[7] and quantity <= std[8]
                    print(f"      长度匹配: {length_match}, 宽度匹配: {width_match}, 数量匹配: {quantity_match}")
            else:
                print(f"  未找到任何 {process_type} 类型的标准")
            
            # 正式查询匹配的标准
            cursor.execute('''
                SELECT * FROM pricing_standards 
                WHERE type=? AND is_active=1 
                AND ? >= min_length AND ? <= max_length
                AND ? >= min_width AND ? <= max_width
                AND ? >= min_quantity AND ? <= max_quantity
                ORDER BY created_at DESC
                LIMIT 1
            ''', (process_type, length, length, width, width, quantity, quantity))
            
            result = cursor.fetchone()
            if result:
                base_price = result[9]
                square_price = result[10]
                total_base_price += base_price
                total_square_price += square_price
                
                standard_info = {
                    'type': result[1],
                    'name': result[2],
                    'base_price': base_price,
                    'square_price': square_price
                }
                matched_standards.append(standard_info)
                
                print(f"  匹配到标准: ID={result[0]}, {result[2]}, 基础价格={base_price}元, 平方价格={square_price}元/m²")
            else:
                print(f"  未找到匹配的 {process_type} 标准")
        
        if matched_standards:
            print(f"\n总计: 基础价格={total_base_price}元, 平方价格={total_square_price}元/m²")
            
            # 计算实际价格
            area_in_square_meters = (length * width) / 1000000  # 转换为平方米
            project_sets = 1  # 假设项目套数为1
            total_quantity = quantity * project_sets
            
            print(f"面积: {area_in_square_meters}m²")
            print(f"总数量: {total_quantity}")
            
            # 模拟前端计算逻辑
            total_process_cost = 0
            
            for component in matched_standards:
                component_cost = 0
                
                if component['type'] == 'printing':
                    # 印刷工艺：基础费用均摊 + 超量部分按平方计算
                    if total_quantity <= 3000:
                        component_cost = component['base_price'] / total_quantity
                    else:
                        excess_quantity = total_quantity - 3000
                        total_cost = component['base_price'] + (excess_quantity * area_in_square_meters * component['square_price'])
                        component_cost = total_cost / total_quantity
                else:
                    # 其他工艺：基础费用均摊 + 平方费用
                    component_cost = (component['base_price'] / total_quantity) + (area_in_square_meters * component['square_price'])
                
                total_process_cost += component_cost
                print(f"  - {component['type']} ({component['name']}): {component_cost:.4f}元/张")
            
            print(f"\n最终工艺价格: {total_process_cost:.4f}元/张")
        else:
            print("未找到任何匹配的标准")
    
    conn.close()
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_price_calculation()