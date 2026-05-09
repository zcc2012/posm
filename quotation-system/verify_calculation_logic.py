#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def verify_calculation_logic():
    """验证价格计算逻辑是否符合要求"""
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("=== 验证价格计算逻辑 ===")
    print("用户要求的公式：")
    print("- 印刷：3000以内 基础价格/(数量*项目数量)")
    print("- 印刷：3000以上 基础价格/(数量*项目数量) + 平方单价")
    print("- 模切：基础价格/(数量*项目数量) + 平方单价")
    print("- 光膜/光油：基础价格/(数量*项目数量) + 平方单价")
    print()
    
    # 测试案例
    test_cases = [
        {
            'name': '印刷工艺 - 3000以内',
            'process_name': '印刷',
            'quantity': 1000,
            'project_sets': 1,
            'area': 1.0,  # 1平方米
            'base_price': 500,
            'square_price': 0.1,
            'expected_formula': '基础价格/(数量*项目数量)'
        },
        {
            'name': '印刷工艺 - 3000以上',
            'process_name': '印刷',
            'quantity': 5000,
            'project_sets': 1,
            'area': 1.0,  # 1平方米
            'base_price': 500,
            'square_price': 0.1,
            'expected_formula': '基础价格/(数量*项目数量) + 平方单价'
        },
        {
            'name': '模切工艺',
            'process_name': '模切',
            'quantity': 2000,
            'project_sets': 1,
            'area': 1.0,  # 1平方米
            'base_price': 200,
            'square_price': 0.25,
            'expected_formula': '基础价格/(数量*项目数量) + 平方单价'
        },
        {
            'name': '覆膜工艺',
            'process_name': '覆膜',
            'quantity': 3000,
            'project_sets': 1,
            'area': 1.0,  # 1平方米
            'base_price': 180,
            'square_price': 0.3,
            'expected_formula': '基础价格/(数量*项目数量) + 平方单价'
        },
        {
            'name': '光油工艺',
            'process_name': '光油',
            'quantity': 1500,
            'project_sets': 1,
            'area': 1.0,  # 1平方米
            'base_price': 150,
            'square_price': 0.2,
            'expected_formula': '基础价格/(数量*项目数量) + 平方单价'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"--- 测试案例 {i}: {test_case['name']} ---")
        print(f"工艺: {test_case['process_name']}")
        print(f"数量: {test_case['quantity']}")
        print(f"项目套数: {test_case['project_sets']}")
        print(f"面积: {test_case['area']}m²")
        print(f"基础价格: {test_case['base_price']}元")
        print(f"平方价格: {test_case['square_price']}元/m²")
        print(f"预期公式: {test_case['expected_formula']}")
        
        # 计算总数量
        total_quantity = test_case['quantity'] * test_case['project_sets']
        print(f"总数量: {total_quantity}")
        
        # 根据用户要求的公式计算
        if test_case['process_name'] == '印刷':
            if total_quantity <= 3000:
                # 印刷 3000以内：基础价格/(数量*项目数量)
                calculated_price = test_case['base_price'] / total_quantity
                print(f"计算公式: {test_case['base_price']} / {total_quantity} = {calculated_price:.4f}元/张")
            else:
                # 印刷 3000以上：基础价格/(数量*项目数量) + 平方单价
                calculated_price = (test_case['base_price'] / total_quantity) + (test_case['area'] * test_case['square_price'])
                print(f"计算公式: ({test_case['base_price']} / {total_quantity}) + ({test_case['area']} * {test_case['square_price']}) = {calculated_price:.4f}元/张")
        else:
            # 其他工艺：基础价格/(数量*项目数量) + 平方单价
            calculated_price = (test_case['base_price'] / total_quantity) + (test_case['area'] * test_case['square_price'])
            print(f"计算公式: ({test_case['base_price']} / {total_quantity}) + ({test_case['area']} * {test_case['square_price']}) = {calculated_price:.4f}元/张")
        
        print(f"最终单价: {calculated_price:.4f}元/张")
        print()
    
    # 测试组合工艺
    print("--- 组合工艺测试：印刷+覆膜+模切 ---")
    print("数量: 5000, 项目套数: 1, 面积: 1.0m²")
    
    # 印刷部分 (5000 > 3000)
    printing_base = 500
    printing_square = 0.1
    printing_cost = (printing_base / 5000) + (1.0 * printing_square)
    print(f"印刷费用: ({printing_base} / 5000) + (1.0 * {printing_square}) = {printing_cost:.4f}元/张")
    
    # 覆膜部分
    lamination_base = 180
    lamination_square = 0.3
    lamination_cost = (lamination_base / 5000) + (1.0 * lamination_square)
    print(f"覆膜费用: ({lamination_base} / 5000) + (1.0 * {lamination_square}) = {lamination_cost:.4f}元/张")
    
    # 模切部分
    die_cutting_base = 200
    die_cutting_square = 0.25
    die_cutting_cost = (die_cutting_base / 5000) + (1.0 * die_cutting_square)
    print(f"模切费用: ({die_cutting_base} / 5000) + (1.0 * {die_cutting_square}) = {die_cutting_cost:.4f}元/张")
    
    # 总费用
    total_cost = printing_cost + lamination_cost + die_cutting_cost
    print(f"总工艺费用: {printing_cost:.4f} + {lamination_cost:.4f} + {die_cutting_cost:.4f} = {total_cost:.4f}元/张")
    
    conn.close()
    print("\n=== 验证完成 ===")

if __name__ == '__main__':
    verify_calculation_logic()