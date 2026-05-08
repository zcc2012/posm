#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def debug_calculation():
    print("=== 调试印刷+模切+光油组合计算 ===")
    
    # 测试参数 - 修正为API期望的格式
    test_data = {
        'process_name': '印刷+模切+光油',  # 修正：使用process_name而不是processes
        'length': 300,
        'width': 200,
        'quantity': 1000
    }
    
    print(f"测试参数: {test_data}")
    
    try:
        # 调用API
        response = requests.post('http://localhost:5000/api/pricing_standards/match', 
                               json=test_data, 
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\nAPI响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 分析各个组件
            print("\n=== 组件分析 ===")
            if 'standard' in result and result['standard'] and 'components' in result['standard']:
                total_base = 0
                total_square = 0
                
                for i, component in enumerate(result['standard']['components'], 1):
                    print(f"组件{i}: {component['name']}")
                    print(f"  类型: {component['type']}")
                    print(f"  基础价格: {component['base_price']}元")
                    print(f"  平方价格: {component['square_price']}元/m²")
                    total_base += component['base_price']
                    total_square += component['square_price']
                
                print(f"\n手动累加结果:")
                print(f"  总基础价格: {total_base}元")
                print(f"  总平方价格: {total_square}元/m²")
                
                print(f"\nAPI返回结果:")
                standard = result['standard']
                print(f"  组合基础价格: {standard.get('base_price', 0)}元")
                print(f"  组合平方价格: {standard.get('square_price', 0)}元/m²")
                
                # 检查是否一致
                api_base = standard.get('base_price', 0)
                api_square = standard.get('square_price', 0)
                
                if abs(total_base - api_base) < 0.01:
                    print("✓ 基础价格累加正确")
                else:
                    print(f"✗ 基础价格累加错误，差异: {abs(total_base - api_base)}元")
                
                if abs(total_square - api_square) < 0.01:
                    print("✓ 平方价格累加正确")
                else:
                    print(f"✗ 平方价格累加错误，差异: {abs(total_square - api_square)}元/m²")
                
                # 计算实际费用
                print("\n=== 实际费用计算 ===")
                area = (300 + 30) * (200 + 30) / 1000000  # 面积计算
                print(f"面积: {area:.6f}m²")
                
                base_price = standard.get('base_price', 0)
                square_price = standard.get('square_price', 0)
                quantity = 1000
                
                # 基础费用公摊
                base_cost_per_unit = base_price / quantity
                # 平方费用
                square_cost_per_unit = area * square_price
                # 总单价
                total_unit_price = base_cost_per_unit + square_cost_per_unit
                # 总价
                total_price = total_unit_price * quantity
                
                print(f"基础费用公摊: {base_price}元 ÷ {quantity}件 = {base_cost_per_unit:.4f}元/件")
                print(f"平方费用: {area:.6f}m² × {square_price}元/m² = {square_cost_per_unit:.4f}元/件")
                print(f"总单价: {base_cost_per_unit:.4f} + {square_cost_per_unit:.4f} = {total_unit_price:.4f}元/件")
                print(f"总价: {total_unit_price:.4f}元/件 × {quantity}件 = {total_price:.2f}元")
                
            else:
                print("未找到匹配的标准或组件信息")
                
        else:
            print(f"API调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
    except Exception as e:
        print(f"其他错误: {e}")

    # 测试其他组合
    print("\n" + "="*50)
    print("=== 测试其他工艺组合 ===")
    
    test_cases = [
        {'name': '单一印刷', 'process_name': '印刷'},
        {'name': '单一模切', 'process_name': '模切'},
        {'name': '单一光油', 'process_name': '光油'},
        {'name': '印刷+模切', 'process_name': '印刷+模切'},
        {'name': '模切+光油', 'process_name': '模切+光油'},
        {'name': '印刷+覆膜', 'process_name': '印刷+覆膜'}
    ]
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        test_data = {
            'process_name': test_case['process_name'],
            'length': 300,
            'width': 200,
            'quantity': 1000
        }
        
        try:
            response = requests.post('http://localhost:5000/api/pricing_standards/match', 
                                   json=test_data, 
                                   timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if 'standard' in result and result['standard']:
                    standard = result['standard']
                    print(f"匹配成功: {standard['name']}")
                    print(f"基础价格: {standard['base_price']}元")
                    print(f"平方价格: {standard['square_price']}元/m²")
                    if 'components' in standard:
                        print(f"组件数量: {len(standard['components'])}个")
                else:
                    print("未找到匹配的标准")
            else:
                print(f"API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"测试失败: {e}")

if __name__ == '__main__':
    debug_calculation()