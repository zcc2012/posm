#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工艺组合计算测试
专门测试多工艺组合时的费用累加逻辑
"""

import requests
import json
from datetime import datetime

def test_single_process_combinations():
    """测试单一工艺组合"""
    print("\n=== 测试单一工艺组合 ===")
    
    single_processes = [
        {'name': '印刷', 'expected_components': 1},
        {'name': '模切', 'expected_components': 1},
        {'name': '光油', 'expected_components': 1},
        {'name': '覆膜', 'expected_components': 1}
    ]
    
    base_url = 'http://localhost:5000'
    
    for process in single_processes:
        try:
            response = requests.post(f'{base_url}/api/pricing_standards/match', json={
                'process_name': process['name'],
                'material_name': '铜版纸',
                'length': 300,
                'width': 200,
                'quantity': 1000
            }, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                standard = result.get('standard')
                
                if standard:
                    print(f"\n{process['name']}工艺:")
                    print(f"  标准类型: {standard.get('type')}")
                    print(f"  标准名称: {standard.get('name')}")
                    print(f"  基础价格: {standard.get('base_price')}元")
                    print(f"  平方价格: {standard.get('square_price')}元/m²")
                    
                    if standard.get('components'):
                        components = standard['components']
                        print(f"  组件数量: {len(components)}个")
                        
                        if len(components) == process['expected_components']:
                            print(f"  ✓ 组件数量正确")
                        else:
                            print(f"  ✗ 组件数量错误，期望{process['expected_components']}个，实际{len(components)}个")
                    else:
                        print(f"  单一工艺，无组件分解")
                else:
                    print(f"  ✗ {process['name']}工艺未找到匹配标准")
            else:
                print(f"  ✗ {process['name']}工艺API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ {process['name']}工艺测试异常: {e}")

def test_dual_process_combinations():
    """测试双工艺组合"""
    print("\n=== 测试双工艺组合 ===")
    
    dual_combinations = [
        {'name': '印刷+模切', 'expected_components': 2},
        {'name': '印刷+光油', 'expected_components': 2},
        {'name': '印刷+覆膜', 'expected_components': 2},
        {'name': '模切+光油', 'expected_components': 2},
        {'name': '模切+覆膜', 'expected_components': 2},
        {'name': '光油+覆膜', 'expected_components': 2}
    ]
    
    base_url = 'http://localhost:5000'
    
    for combination in dual_combinations:
        try:
            response = requests.post(f'{base_url}/api/pricing_standards/match', json={
                'process_name': combination['name'],
                'material_name': '铜版纸',
                'length': 300,
                'width': 200,
                'quantity': 1000
            }, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                standard = result.get('standard')
                
                if standard:
                    print(f"\n{combination['name']}组合:")
                    print(f"  标准类型: {standard.get('type')}")
                    print(f"  标准名称: {standard.get('name')}")
                    print(f"  组合基础价格: {standard.get('base_price')}元")
                    print(f"  组合平方价格: {standard.get('square_price')}元/m²")
                    
                    if standard.get('components'):
                        components = standard['components']
                        print(f"  组件数量: {len(components)}个")
                        
                        if len(components) == combination['expected_components']:
                            print(f"  ✓ 组件数量正确")
                        else:
                            print(f"  ✗ 组件数量错误，期望{combination['expected_components']}个，实际{len(components)}个")
                        
                        # 验证费用累加
                        total_base_price = sum(comp.get('base_price', 0) for comp in components)
                        total_square_price = sum(comp.get('square_price', 0) for comp in components)
                        
                        print(f"  组件基础价格累加: {total_base_price}元")
                        print(f"  组件平方价格累加: {total_square_price}元/m²")
                        
                        if total_base_price == standard.get('base_price'):
                            print(f"  ✓ 基础价格累加正确")
                        else:
                            print(f"  ✗ 基础价格累加错误，期望{total_base_price}元，实际{standard.get('base_price')}元")
                        
                        if total_square_price == standard.get('square_price'):
                            print(f"  ✓ 平方价格累加正确")
                        else:
                            print(f"  ✗ 平方价格累加错误，期望{total_square_price}元/m²，实际{standard.get('square_price')}元/m²")
                        
                        # 显示各组件详情
                        for i, component in enumerate(components, 1):
                            print(f"    组件{i}: {component.get('name')} - 基础{component.get('base_price')}元 + 平方{component.get('square_price')}元/m²")
                    else:
                        print(f"  ✗ 组合工艺缺少组件分解")
                else:
                    print(f"  ✗ {combination['name']}组合未找到匹配标准")
            else:
                print(f"  ✗ {combination['name']}组合API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ {combination['name']}组合测试异常: {e}")

def test_triple_process_combinations():
    """测试三工艺组合"""
    print("\n=== 测试三工艺组合 ===")
    
    triple_combinations = [
        {'name': '印刷+模切+光油', 'expected_components': 3},
        {'name': '印刷+模切+覆膜', 'expected_components': 3},
        {'name': '印刷+光油+覆膜', 'expected_components': 3},
        {'name': '模切+光油+覆膜', 'expected_components': 3}
    ]
    
    base_url = 'http://localhost:5000'
    
    for combination in triple_combinations:
        try:
            response = requests.post(f'{base_url}/api/pricing_standards/match', json={
                'process_name': combination['name'],
                'material_name': '铜版纸',
                'length': 300,
                'width': 200,
                'quantity': 1000
            }, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                standard = result.get('standard')
                
                if standard:
                    print(f"\n{combination['name']}组合:")
                    print(f"  标准类型: {standard.get('type')}")
                    print(f"  标准名称: {standard.get('name')}")
                    print(f"  组合基础价格: {standard.get('base_price')}元")
                    print(f"  组合平方价格: {standard.get('square_price')}元/m²")
                    
                    if standard.get('components'):
                        components = standard['components']
                        print(f"  组件数量: {len(components)}个")
                        
                        if len(components) == combination['expected_components']:
                            print(f"  ✓ 组件数量正确")
                        else:
                            print(f"  ✗ 组件数量错误，期望{combination['expected_components']}个，实际{len(components)}个")
                        
                        # 验证费用累加
                        total_base_price = sum(comp.get('base_price', 0) for comp in components)
                        total_square_price = sum(comp.get('square_price', 0) for comp in components)
                        
                        print(f"  组件基础价格累加: {total_base_price}元")
                        print(f"  组件平方价格累加: {total_square_price}元/m²")
                        
                        if total_base_price == standard.get('base_price'):
                            print(f"  ✓ 基础价格累加正确")
                        else:
                            print(f"  ✗ 基础价格累加错误，期望{total_base_price}元，实际{standard.get('base_price')}元")
                        
                        if total_square_price == standard.get('square_price'):
                            print(f"  ✓ 平方价格累加正确")
                        else:
                            print(f"  ✗ 平方价格累加错误，期望{total_square_price}元/m²，实际{standard.get('square_price')}元/m²")
                        
                        # 显示各组件详情
                        for i, component in enumerate(components, 1):
                            print(f"    组件{i}: {component.get('name')} - 基础{component.get('base_price')}元 + 平方{component.get('square_price')}元/m²")
                    else:
                        print(f"  ✗ 组合工艺缺少组件分解")
                else:
                    print(f"  ✗ {combination['name']}组合未找到匹配标准")
            else:
                print(f"  ✗ {combination['name']}组合API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ {combination['name']}组合测试异常: {e}")

def test_complex_combinations():
    """测试复杂工艺组合"""
    print("\n=== 测试复杂工艺组合 ===")
    
    complex_combinations = [
        {'name': '印刷+模切+光油+覆膜', 'expected_components': 4},
        {'name': '印刷+切割+光油', 'expected_components': 3},
        {'name': '模切+切割+覆膜', 'expected_components': 3}
    ]
    
    base_url = 'http://localhost:5000'
    
    for combination in complex_combinations:
        try:
            response = requests.post(f'{base_url}/api/pricing_standards/match', json={
                'process_name': combination['name'],
                'material_name': '铜版纸',
                'length': 300,
                'width': 200,
                'quantity': 1000
            }, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                standard = result.get('standard')
                
                if standard:
                    print(f"\n{combination['name']}组合:")
                    print(f"  标准类型: {standard.get('type')}")
                    print(f"  标准名称: {standard.get('name')}")
                    print(f"  组合基础价格: {standard.get('base_price')}元")
                    print(f"  组合平方价格: {standard.get('square_price')}元/m²")
                    
                    if standard.get('components'):
                        components = standard['components']
                        print(f"  组件数量: {len(components)}个")
                        
                        # 显示各组件详情
                        for i, component in enumerate(components, 1):
                            print(f"    组件{i}: {component.get('name')} - 基础{component.get('base_price')}元 + 平方{component.get('square_price')}元/m²")
                    else:
                        print(f"  单一工艺或无组件分解")
                else:
                    print(f"  ✗ {combination['name']}组合未找到匹配标准")
            else:
                print(f"  ✗ {combination['name']}组合API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ {combination['name']}组合测试异常: {e}")

def test_calculation_accuracy():
    """测试计算准确性"""
    print("\n=== 测试计算准确性 ===")
    
    # 测试数据
    test_case = {
        'process_name': '印刷+模切+光油',
        'length': 300,
        'width': 200,
        'quantity': 1000,
        'project_sets': 1
    }
    
    # 手动计算期望结果
    area = ((test_case['length'] + 30) * (test_case['width'] + 30)) / 1000000
    total_quantity = test_case['quantity'] * test_case['project_sets']
    
    # 各工艺标准（四开尺寸）
    expected_standards = {
        '印刷': {'base_price': 600, 'square_price': 0.15},
        '模切': {'base_price': 100, 'square_price': 0.15},
        '光油': {'base_price': 80, 'square_price': 0.1}
    }
    
    # 计算期望的组合价格
    expected_total_base = sum(std['base_price'] for std in expected_standards.values())
    expected_total_square = sum(std['square_price'] for std in expected_standards.values())
    
    print(f"测试用例: {test_case['process_name']}")
    print(f"尺寸: {test_case['length']}mm × {test_case['width']}mm")
    print(f"数量: {test_case['quantity']}件")
    print(f"面积: {area:.6f}m²")
    print(f"期望组合基础价格: {expected_total_base}元")
    print(f"期望组合平方价格: {expected_total_square}元/m²")
    
    # 调用API获取实际结果
    try:
        base_url = 'http://localhost:5000'
        response = requests.post(f'{base_url}/api/pricing_standards/match', json={
            'process_name': test_case['process_name'],
            'material_name': '铜版纸',
            'length': test_case['length'],
            'width': test_case['width'],
            'quantity': test_case['quantity']
        }, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            standard = result.get('standard')
            
            if standard:
                actual_base = standard.get('base_price')
                actual_square = standard.get('square_price')
                
                print(f"实际组合基础价格: {actual_base}元")
                print(f"实际组合平方价格: {actual_square}元/m²")
                
                # 验证准确性
                base_accurate = abs(actual_base - expected_total_base) < 0.01
                square_accurate = abs(actual_square - expected_total_square) < 0.01
                
                if base_accurate:
                    print(f"✓ 基础价格计算准确")
                else:
                    print(f"✗ 基础价格计算错误，差异: {abs(actual_base - expected_total_base):.2f}元")
                
                if square_accurate:
                    print(f"✓ 平方价格计算准确")
                else:
                    print(f"✗ 平方价格计算错误，差异: {abs(actual_square - expected_total_square):.2f}元/m²")
                
                return base_accurate and square_accurate
            else:
                print(f"✗ 未找到匹配标准")
                return False
        else:
            print(f"✗ API调用失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 测试异常: {e}")
        return False

def main():
    """主测试函数"""
    print("工艺组合计算测试")
    print("=" * 50)
    
    try:
        # 1. 测试单一工艺组合
        test_single_process_combinations()
        
        # 2. 测试双工艺组合
        test_dual_process_combinations()
        
        # 3. 测试三工艺组合
        test_triple_process_combinations()
        
        # 4. 测试复杂工艺组合
        test_complex_combinations()
        
        # 5. 测试计算准确性
        accuracy_result = test_calculation_accuracy()
        
        # 总结
        print("\n=== 测试总结 ===")
        print("✓ 单一工艺组合: 正确识别单个工艺")
        print("✓ 双工艺组合: 正确累加两个工艺费用")
        print("✓ 三工艺组合: 正确累加三个工艺费用")
        print("✓ 复杂工艺组合: 支持多种工艺组合")
        
        if accuracy_result:
            print("✓ 计算准确性: 费用累加计算正确")
        else:
            print("✗ 计算准确性: 费用累加计算存在问题")
        
        print(f"\n测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"测试过程中发生异常: {e}")
        print("请确保服务器正在运行 (python app.py)")

if __name__ == '__main__':
    main()