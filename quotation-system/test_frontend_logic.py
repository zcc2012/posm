#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端判定逻辑修复后的效果
模拟前端getProcessStandard函数的逻辑
"""

def get_process_standard_frontend(process_type, length, width):
    """模拟前端的getProcessStandard函数逻辑"""
    # 确保长宽不受顺序影响，取较大值和较小值
    max_dimension = max(length, width)
    min_dimension = min(length, width)
    
    # 印刷工艺尺寸判定（与数据库标准一致）
    if process_type == 'printing':
        # 4开机器：长度0-719mm，宽度0-519mm
        if max_dimension <= 719 and min_dimension <= 519:
            return {'name': '4开机器', 'basePrice': 600, 'squarePrice': 0.15}
        # 对开机：长度720-1019mm，宽度520-719mm
        elif max_dimension >= 720 and max_dimension <= 1019 and min_dimension >= 520 and min_dimension <= 719:
            return {'name': '对开机', 'basePrice': 1000, 'squarePrice': 0.25}
        # 全开机：长度1020-1419mm，宽度720-1019mm
        elif max_dimension >= 1020 and max_dimension <= 1419 and min_dimension >= 720 and min_dimension <= 1019:
            return {'name': '全开机', 'basePrice': 1500, 'squarePrice': 0.3}
        # 大全开：长度1420-1620mm，宽度1020-1220mm
        elif max_dimension >= 1420 and max_dimension <= 1620 and min_dimension >= 1020 and min_dimension <= 1220:
            return {'name': '大全开', 'basePrice': 2000, 'squarePrice': 0.35}
        # 大幅面印刷：超过上述所有尺寸范围
        else:
            return {'name': '大幅面印刷', 'basePrice': 2000, 'squarePrice': 0.4}
    
    return None

def calculate_printing_cost(length, width, quantity):
    """计算印刷成本"""
    standard = get_process_standard_frontend('printing', length, width)
    if standard:
        # 计算面积（平方米）
        area = (length * width) / 1000000
        # 计算成本：基础价格 + 面积 * 平方价格 * 数量
        area_cost = area * standard['squarePrice'] * quantity
        total_cost = standard['basePrice'] + area_cost
        # 按数量均摊
        unit_cost = total_cost / quantity
        
        # 详细计算过程
        base_unit_cost = standard['basePrice'] / quantity
        area_unit_cost = area * standard['squarePrice']
        
        return {
            'standard': standard['name'],
            'base_price': standard['basePrice'],
            'square_price': standard['squarePrice'],
            'area': area,
            'total_cost': total_cost,
            'unit_cost': unit_cost,
            'base_unit_cost': base_unit_cost,
            'area_unit_cost': area_unit_cost,
            'area_cost': area_cost
        }
    return None

# 测试用例
test_cases = [
    {'length': 300, 'width': 500, 'quantity': 1000, 'expected': '4开机器'},
    {'length': 500, 'width': 300, 'quantity': 1000, 'expected': '4开机器'},
    {'length': 720, 'width': 520, 'quantity': 1000, 'expected': '对开机'},
    {'length': 1020, 'width': 720, 'quantity': 1000, 'expected': '全开机'},
    {'length': 719, 'width': 519, 'quantity': 1000, 'expected': '4开机器'},
    {'length': 720, 'width': 520, 'quantity': 1000, 'expected': '对开机'},
]

print("=== 前端判定逻辑测试 ===")
for i, case in enumerate(test_cases, 1):
    result = calculate_printing_cost(case['length'], case['width'], case['quantity'])
    if result:
        print(f"\n测试 {i}: {case['length']}x{case['width']}mm, {case['quantity']}套")
        print(f"匹配标准: {result['standard']} (预期: {case['expected']})")
        print(f"基础价格: {result['base_price']}元")
        print(f"平方价格: {result['square_price']}元/平方米")
        print(f"面积: {result['area']:.6f}平方米")
        print(f"总成本: {result['total_cost']:.2f}元")
        print(f"单套成本: {result['unit_cost']:.2f}元")
        
        # 检查是否匹配预期
        if result['standard'] == case['expected']:
            print("✓ 匹配正确")
        else:
            print("✗ 匹配错误")
    else:
        print(f"\n测试 {i}: {case['length']}x{case['width']}mm - 未找到匹配标准")

# 特别测试300x500的情况
print("\n=== 特别验证300x500尺寸 ===")
result = calculate_printing_cost(300, 500, 1000)
if result:
    print(f"300x500mm, 1000套的印刷成本计算:")
    print(f"匹配标准: {result['standard']}")
    print(f"基础价格: {result['base_price']}元")
    print(f"平方价格: {result['square_price']}元/平方米")
    print(f"面积: {result['area']:.6f}平方米")
    print(f"\n详细计算过程:")
    print(f"基础价格均摊: {result['base_price']} ÷ {1000} = {result['base_unit_cost']:.3f}元/套")
    print(f"面积成本: {result['area']:.6f} × {result['square_price']} = {result['area_unit_cost']:.3f}元/套")
    print(f"单套总成本: {result['base_unit_cost']:.3f} + {result['area_unit_cost']:.3f} = {result['unit_cost']:.3f}元/套")
    print(f"\n总成本: {result['total_cost']:.2f}元")
    print(f"单套成本: {result['unit_cost']:.3f}元")
    print(f"\n用户期望: 600元基础价格，1000套均摊应该是0.6元")
    print(f"实际计算: 基础价格{result['base_unit_cost']:.3f}元 + 面积成本{result['area_unit_cost']:.3f}元 = {result['unit_cost']:.3f}元")
    
    if abs(result['base_unit_cost'] - 0.6) < 0.01:
        print("✓ 基础价格均摊计算正确 (0.6元)")
    else:
        print(f"✗ 基础价格均摊计算错误 (应为0.6元，实际{result['base_unit_cost']:.3f}元)")
        
    print(f"\n说明: 用户期望的0.6元只是基础价格均摊，实际还需要加上面积成本{result['area_unit_cost']:.3f}元")