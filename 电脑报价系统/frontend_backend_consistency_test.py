#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import sqlite3

def test_frontend_backend_consistency():
    print("=== 前后端一致性测试 ===")
    
    # 测试用例
    test_cases = [
        {
            'name': '印刷+模切组合',
            'material_id': 1,
            'length': 300,
            'width': 200,
            'quantity': 1000,
            'processes': ['印刷', '模切']
        },
        {
            'name': '单一光油工艺',
            'material_id': 2,
            'length': 400,
            'width': 300,
            'quantity': 500,
            'processes': ['光油']
        },
        {
            'name': '三工艺组合',
            'material_id': 1,
            'length': 250,
            'width': 180,
            'quantity': 2000,
            'processes': ['印刷', '模切', '覆膜']
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        # 1. 后端API计算
        backend_result = calculate_backend_price(test_case)
        
        # 2. 前端页面计算（模拟）
        frontend_result = simulate_frontend_calculation(test_case)
        
        # 3. 比较结果
        consistency_check = compare_results(backend_result, frontend_result)
        
        results.append({
            'test_case': test_case['name'],
            'backend': backend_result,
            'frontend': frontend_result,
            'consistent': consistency_check
        })
        
        print(f"后端计算结果: {backend_result}")
        print(f"前端计算结果: {frontend_result}")
        print(f"一致性检查: {'✓ 一致' if consistency_check else '✗ 不一致'}")
    
    # 总结
    print("\n" + "="*50)
    print("=== 一致性测试总结 ===")
    
    consistent_count = sum(1 for r in results if r['consistent'])
    total_count = len(results)
    
    print(f"总测试数: {total_count}")
    print(f"一致: {consistent_count}")
    print(f"不一致: {total_count - consistent_count}")
    print(f"一致性比例: {(consistent_count/total_count)*100:.1f}%")
    
    return consistent_count == total_count

def calculate_backend_price(test_case):
    """使用后端API计算价格"""
    try:
        # 1. 获取材料价格
        material_response = requests.get(f'http://localhost:5000/api/materials/{test_case["material_id"]}')
        if material_response.status_code != 200:
            return {'error': '材料获取失败'}
        
        material = material_response.json()
        material_square_price = material['square_price']
        
        # 2. 获取工艺匹配
        process_name = '+'.join(test_case['processes'])
        match_data = {
            'process_name': process_name,
            'length': test_case['length'],
            'width': test_case['width'],
            'quantity': test_case['quantity']
        }
        
        match_response = requests.post('http://localhost:5000/api/pricing_standards/match', json=match_data)
        if match_response.status_code != 200:
            return {'error': '工艺匹配失败'}
        
        match_result = match_response.json()
        if not match_result.get('standard'):
            return {'error': '未找到匹配的工艺标准'}
        
        standard = match_result['standard']
        
        # 3. 计算价格
        area = (test_case['length'] + 30) * (test_case['width'] + 30) / 1000000
        material_cost = area * material_square_price
        
        base_price = standard['base_price']
        square_price = standard['square_price']
        quantity = test_case['quantity']
        
        base_cost_per_unit = base_price / quantity
        square_cost_per_unit = area * square_price
        total_unit_price = base_cost_per_unit + square_cost_per_unit + material_cost
        total_price = total_unit_price * quantity
        
        return {
            'success': True,
            'material_cost': material_cost,
            'base_cost_per_unit': base_cost_per_unit,
            'square_cost_per_unit': square_cost_per_unit,
            'total_unit_price': total_unit_price,
            'total_price': total_price,
            'area': area,
            'components': len(standard.get('components', []))
        }
        
    except Exception as e:
        return {'error': str(e)}

def simulate_frontend_calculation(test_case):
    """模拟前端计算逻辑"""
    try:
        # 获取数据库数据进行模拟计算
        conn = sqlite3.connect('quotation_system.db')
        cursor = conn.cursor()
        
        # 1. 获取材料价格
        cursor.execute('SELECT square_price FROM materials WHERE id=?', (test_case['material_id'],))
        material_result = cursor.fetchone()
        if not material_result:
            return {'error': '材料不存在'}
        
        material_square_price = material_result[0]
        
        # 2. 模拟工艺匹配（简化版本）
        process_types = []
        for process in test_case['processes']:
            if process == '印刷':
                process_types.append('printing')
            elif process == '模切':
                process_types.append('die-cutting')
            elif process == '光油':
                process_types.append('varnish')
            elif process == '覆膜':
                process_types.append('lamination')
            elif process == '切割':
                process_types.append('cutting')
        
        total_base_price = 0
        total_square_price = 0
        matched_components = 0
        
        for process_type in process_types:
            cursor.execute('''
                SELECT base_price, square_price
                FROM pricing_standards 
                WHERE type=? AND is_active=1 
                AND ? >= min_length AND ? <= max_length
                AND ? >= min_width AND ? <= max_width
                AND ? >= min_quantity AND ? <= max_quantity
                ORDER BY priority ASC
                LIMIT 1
            ''', (process_type, test_case['length'], test_case['length'], 
                  test_case['width'], test_case['width'], 
                  test_case['quantity'], test_case['quantity']))
            
            result = cursor.fetchone()
            if result:
                total_base_price += result[0]
                total_square_price += result[1]
                matched_components += 1
        
        conn.close()
        
        if matched_components == 0:
            return {'error': '未找到匹配的工艺标准'}
        
        # 3. 计算价格（模拟前端逻辑）
        area = (test_case['length'] + 30) * (test_case['width'] + 30) / 1000000
        material_cost = area * material_square_price
        
        base_cost_per_unit = total_base_price / test_case['quantity']
        square_cost_per_unit = area * total_square_price
        total_unit_price = base_cost_per_unit + square_cost_per_unit + material_cost
        total_price = total_unit_price * test_case['quantity']
        
        return {
            'success': True,
            'material_cost': material_cost,
            'base_cost_per_unit': base_cost_per_unit,
            'square_cost_per_unit': square_cost_per_unit,
            'total_unit_price': total_unit_price,
            'total_price': total_price,
            'area': area,
            'components': matched_components
        }
        
    except Exception as e:
        return {'error': str(e)}

def compare_results(backend_result, frontend_result):
    """比较前后端计算结果"""
    if not backend_result.get('success') or not frontend_result.get('success'):
        return False
    
    # 允许的误差范围（0.01元）
    tolerance = 0.01
    
    # 比较关键价格字段
    price_fields = ['material_cost', 'base_cost_per_unit', 'square_cost_per_unit', 'total_unit_price', 'total_price']
    
    for field in price_fields:
        backend_value = backend_result.get(field, 0)
        frontend_value = frontend_result.get(field, 0)
        
        if abs(backend_value - frontend_value) > tolerance:
            print(f"  差异字段 {field}: 后端{backend_value:.4f} vs 前端{frontend_value:.4f}")
            return False
    
    # 比较组件数量
    if backend_result.get('components', 0) != frontend_result.get('components', 0):
        print(f"  组件数量差异: 后端{backend_result.get('components', 0)} vs 前端{frontend_result.get('components', 0)}")
        return False
    
    return True

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*50)
    print("=== 边界情况测试 ===")
    
    edge_cases = [
        {
            'name': '最小尺寸',
            'process_name': '印刷',
            'length': 50,
            'width': 30,
            'quantity': 100
        },
        {
            'name': '最大尺寸',
            'process_name': '印刷',
            'length': 1400,
            'width': 1000,
            'quantity': 1000
        },
        {
            'name': '最小数量',
            'process_name': '模切',
            'length': 300,
            'width': 200,
            'quantity': 1
        },
        {
            'name': '超大数量',
            'process_name': '光油',
            'length': 300,
            'width': 200,
            'quantity': 50000
        }
    ]
    
    for case in edge_cases:
        print(f"\n--- {case['name']} ---")
        
        try:
            response = requests.post('http://localhost:5000/api/pricing_standards/match', json=case)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('standard'):
                    print(f"✓ 成功匹配: {result['standard']['name']}")
                else:
                    print("✗ 未找到匹配的标准")
            else:
                print(f"✗ API调用失败: {response.status_code}")
                
        except Exception as e:
            print(f"✗ 测试失败: {e}")

def test_calculation_accuracy():
    """测试计算精度"""
    print("\n" + "="*50)
    print("=== 计算精度测试 ===")
    
    # 精确的测试用例
    test_case = {
        'process_name': '印刷+模切',
        'length': 300,
        'width': 200,
        'quantity': 1000
    }
    
    try:
        response = requests.post('http://localhost:5000/api/pricing_standards/match', json=test_case)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get('standard'):
                standard = result['standard']
                
                print(f"工艺组合: {test_case['process_name']}")
                print(f"尺寸: {test_case['length']}×{test_case['width']}mm")
                print(f"数量: {test_case['quantity']}件")
                print(f"\n匹配标准: {standard['name']}")
                print(f"基础价格: {standard['base_price']}元")
                print(f"平方价格: {standard['square_price']}元/m²")
                
                # 详细计算过程
                area = (test_case['length'] + 30) * (test_case['width'] + 30) / 1000000
                base_cost_per_unit = standard['base_price'] / test_case['quantity']
                square_cost_per_unit = area * standard['square_price']
                total_unit_price = base_cost_per_unit + square_cost_per_unit
                total_price = total_unit_price * test_case['quantity']
                
                print(f"\n计算过程:")
                print(f"  面积: ({test_case['length']}+30) × ({test_case['width']}+30) ÷ 1000000 = {area:.6f}m²")
                print(f"  基础费用公摊: {standard['base_price']}元 ÷ {test_case['quantity']}件 = {base_cost_per_unit:.6f}元/件")
                print(f"  平方费用: {area:.6f}m² × {standard['square_price']}元/m² = {square_cost_per_unit:.6f}元/件")
                print(f"  总单价: {base_cost_per_unit:.6f} + {square_cost_per_unit:.6f} = {total_unit_price:.6f}元/件")
                print(f"  总价: {total_unit_price:.6f}元/件 × {test_case['quantity']}件 = {total_price:.2f}元")
                
                # 验证组件累加
                if 'components' in standard:
                    print(f"\n组件验证:")
                    manual_base = sum(comp['base_price'] for comp in standard['components'])
                    manual_square = sum(comp['square_price'] for comp in standard['components'])
                    
                    print(f"  手动累加基础价格: {manual_base}元")
                    print(f"  API返回基础价格: {standard['base_price']}元")
                    print(f"  基础价格一致: {'✓' if abs(manual_base - standard['base_price']) < 0.01 else '✗'}")
                    
                    print(f"  手动累加平方价格: {manual_square}元/m²")
                    print(f"  API返回平方价格: {standard['square_price']}元/m²")
                    print(f"  平方价格一致: {'✓' if abs(manual_square - standard['square_price']) < 0.01 else '✗'}")
                
            else:
                print("未找到匹配的标准")
        else:
            print(f"API调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == '__main__':
    # 运行一致性测试
    consistency_ok = test_frontend_backend_consistency()
    
    # 运行边界情况测试
    test_edge_cases()
    
    # 运行计算精度测试
    test_calculation_accuracy()
    
    print("\n" + "="*50)
    print("=== 最终结果 ===")
    if consistency_ok:
        print("✅ 前后端计算一致性测试通过")
    else:
        print("❌ 前后端计算存在不一致")