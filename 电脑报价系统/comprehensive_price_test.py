#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sqlite3

def test_different_scenarios():
    print("=== 综合价格计算测试 ===")
    
    # 测试场景
    test_scenarios = [
        {
            'name': '小数量单一印刷',
            'process_name': '印刷',
            'length': 300, 'width': 200, 'quantity': 50,
            'expected_components': 1
        },
        {
            'name': '中等数量印刷+模切',
            'process_name': '印刷+模切',
            'length': 400, 'width': 300, 'quantity': 1500,
            'expected_components': 2
        },
        {
            'name': '大数量三工艺组合',
            'process_name': '印刷+模切+光油',
            'length': 500, 'width': 400, 'quantity': 5000,
            'expected_components': 3
        },
        {
            'name': '超大数量四工艺组合',
            'process_name': '印刷+模切+光油+覆膜',
            'length': 600, 'width': 500, 'quantity': 10000,
            'expected_components': 4
        },
        {
            'name': '小尺寸高数量',
            'process_name': '模切+光油',
            'length': 100, 'width': 80, 'quantity': 8000,
            'expected_components': 2
        }
    ]
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        print(f"工艺: {scenario['process_name']}")
        print(f"尺寸: {scenario['length']}mm × {scenario['width']}mm")
        print(f"数量: {scenario['quantity']}件")
        
        test_data = {
            'process_name': scenario['process_name'],
            'length': scenario['length'],
            'width': scenario['width'],
            'quantity': scenario['quantity']
        }
        
        try:
            response = requests.post('http://localhost:5000/api/pricing_standards/match', 
                                   json=test_data, 
                                   timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'standard' in result and result['standard']:
                    standard = result['standard']
                    
                    # 计算面积
                    area = (scenario['length'] + 30) * (scenario['width'] + 30) / 1000000
                    
                    # 计算价格
                    base_price = standard['base_price']
                    square_price = standard['square_price']
                    quantity = scenario['quantity']
                    
                    # 基础费用公摊
                    base_cost_per_unit = base_price / quantity
                    # 平方费用
                    square_cost_per_unit = area * square_price
                    # 总单价
                    total_unit_price = base_cost_per_unit + square_cost_per_unit
                    # 总价
                    total_price = total_unit_price * quantity
                    
                    # 验证组件数量
                    actual_components = len(standard.get('components', []))
                    components_ok = actual_components == scenario['expected_components']
                    
                    print(f"✓ 匹配成功: {standard['name']}")
                    print(f"  组件数量: {actual_components}/{scenario['expected_components']} {'✓' if components_ok else '✗'}")
                    print(f"  面积: {area:.6f}m²")
                    print(f"  基础价格: {base_price}元")
                    print(f"  平方价格: {square_price}元/m²")
                    print(f"  单价: {total_unit_price:.4f}元/件")
                    print(f"  总价: {total_price:.2f}元")
                    
                    # 显示组件详情
                    if 'components' in standard:
                        print(f"  组件详情:")
                        for i, comp in enumerate(standard['components'], 1):
                            print(f"    {i}. {comp['name']} - 基础{comp['base_price']}元 + 平方{comp['square_price']}元/m²")
                    
                    results.append({
                        'scenario': scenario['name'],
                        'success': True,
                        'components_ok': components_ok,
                        'total_price': total_price,
                        'unit_price': total_unit_price
                    })
                    
                else:
                    print("✗ 未找到匹配的标准")
                    results.append({
                        'scenario': scenario['name'],
                        'success': False,
                        'error': '未找到匹配的标准'
                    })
            else:
                print(f"✗ API调用失败: {response.status_code}")
                results.append({
                    'scenario': scenario['name'],
                    'success': False,
                    'error': f'API调用失败: {response.status_code}'
                })
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            results.append({
                'scenario': scenario['name'],
                'success': False,
                'error': str(e)
            })
    
    # 测试总结
    print("\n" + "="*60)
    print("=== 测试总结 ===")
    
    successful_tests = [r for r in results if r['success']]
    failed_tests = [r for r in results if not r['success']]
    
    print(f"总测试数: {len(results)}")
    print(f"成功: {len(successful_tests)}")
    print(f"失败: {len(failed_tests)}")
    
    if failed_tests:
        print("\n失败的测试:")
        for test in failed_tests:
            print(f"  - {test['scenario']}: {test.get('error', '未知错误')}")
    
    if successful_tests:
        print("\n成功的测试价格范围:")
        prices = [t['total_price'] for t in successful_tests]
        print(f"  最低价格: {min(prices):.2f}元")
        print(f"  最高价格: {max(prices):.2f}元")
        print(f"  平均价格: {sum(prices)/len(prices):.2f}元")
    
    return len(failed_tests) == 0

def test_wastage_calculation():
    print("\n" + "="*60)
    print("=== 损耗计算测试 ===")
    
    # 获取损耗设置
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT name, wastage_0_100, wastage_100_3000, wastage_3000_plus
        FROM pricing_standards 
        WHERE type='printing' 
        LIMIT 1
    ''')
    
    result = cursor.fetchone()
    if result:
        name, w1, w2, w3 = result
        print(f"印刷标准 '{name}' 的损耗设置:")
        print(f"  0-100件: {w1}件")
        print(f"  100-3000件: {w2}件")
        print(f"  3000+件: {w3}件")
        
        # 测试不同数量的损耗计算
        test_quantities = [50, 150, 1000, 2500, 5000, 10000]
        
        for qty in test_quantities:
            if qty <= 100:
                expected_wastage = w1
            elif qty <= 3000:
                expected_wastage = w2
            else:
                expected_wastage = w3
            
            actual_qty_with_wastage = qty + expected_wastage
            
            print(f"\n数量 {qty}件:")
            print(f"  预期损耗: {expected_wastage}件")
            print(f"  实际生产数量: {actual_qty_with_wastage}件")
            print(f"  损耗率: {(expected_wastage/qty)*100:.1f}%")
    
    conn.close()

def test_material_price_calculation():
    print("\n" + "="*60)
    print("=== 材料价格计算测试 ===")
    
    # 获取材料价格
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, square_price FROM materials LIMIT 3')
    materials = cursor.fetchall()
    
    test_sizes = [
        {'length': 200, 'width': 150},
        {'length': 400, 'width': 300},
        {'length': 600, 'width': 450}
    ]
    
    for material in materials:
        material_id, material_name, square_price = material
        print(f"\n材料: {material_name} (平方价格: {square_price}元/m²)")
        
        for size in test_sizes:
            # 计算面积（加上30mm边距）
            area = (size['length'] + 30) * (size['width'] + 30) / 1000000
            material_cost = area * square_price
            
            print(f"  尺寸 {size['length']}×{size['width']}mm:")
            print(f"    实际面积: {area:.6f}m²")
            print(f"    材料成本: {material_cost:.4f}元")
    
    conn.close()

if __name__ == '__main__':
    # 运行所有测试
    success = test_different_scenarios()
    test_wastage_calculation()
    test_material_price_calculation()
    
    print("\n" + "="*60)
    print("=== 最终结果 ===")
    if success:
        print("✅ 所有价格计算测试通过")
    else:
        print("❌ 部分测试失败，需要进一步检查")