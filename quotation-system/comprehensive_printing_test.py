import sqlite3
import requests
import json

def test_all_printing_standards():
    """全面测试所有印刷标准的判定规则"""
    
    print('=== 全面检查印刷判定规则 ===')
    
    # 连接数据库获取所有印刷标准
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, name, min_length, max_length, min_width, max_width, 
               min_quantity, max_quantity, base_price, square_price, is_active
        FROM pricing_standards 
        WHERE type = 'printing' AND is_active = 1
        ORDER BY min_length, min_width
    """)
    
    standards = cursor.fetchall()
    conn.close()
    
    print(f'\n找到 {len(standards)} 个激活的印刷标准:')
    for i, std in enumerate(standards, 1):
        print(f'{i}. {std[1]}: {std[2]}-{std[3]} x {std[4]}-{std[5]} mm')
    
    # 定义测试用例
    test_cases = []
    
    # 为每个标准生成测试用例
    for std in standards:
        std_id, name, min_l, max_l, min_w, max_w, min_q, max_q = std[:8]
        
        # 边界测试用例
        test_cases.extend([
            # 最小边界
            {'length': min_l, 'width': min_w, 'quantity': min_q, 'expected': name, 'desc': f'{name}-最小边界'},
            # 最大边界
            {'length': max_l, 'width': max_w, 'quantity': max_q, 'expected': name, 'desc': f'{name}-最大边界'},
            # 中间值
            {'length': (min_l + max_l) / 2, 'width': (min_w + max_w) / 2, 'quantity': (min_q + max_q) / 2, 'expected': name, 'desc': f'{name}-中间值'}
        ])
    
    # 添加一些特殊测试用例
    special_cases = [
        {'length': 300, 'width': 500, 'quantity': 1000, 'expected': '4开机器', 'desc': '用户报告的问题案例'},
        {'length': 500, 'width': 300, 'quantity': 1000, 'expected': '4开机器', 'desc': '长宽互换'},
        {'length': 719, 'width': 519, 'quantity': 1000, 'expected': '4开机器', 'desc': '4开机器上边界'},
        {'length': 720, 'width': 520, 'quantity': 1000, 'expected': '对开机', 'desc': '对开机下边界'},
        {'length': 1019, 'width': 719, 'quantity': 1000, 'expected': '对开机', 'desc': '对开机上边界'},
        {'length': 1020, 'width': 720, 'quantity': 1000, 'expected': '全开机', 'desc': '全开机下边界'},
        # 边界外测试
        {'length': 100, 'width': 100, 'quantity': 1000, 'expected': '4开机器', 'desc': '小尺寸测试'},
        {'length': 2000, 'width': 1500, 'quantity': 1000, 'expected': None, 'desc': '超大尺寸测试'}
    ]
    
    test_cases.extend(special_cases)
    
    print(f'\n=== 开始测试 {len(test_cases)} 个案例 ===')
    
    # 数据库直接测试
    print('\n1. 数据库直接查询测试:')
    db_results = test_database_matching(test_cases)
    
    # API测试
    print('\n2. Web API测试:')
    api_results = test_api_matching(test_cases)
    
    # 结果对比
    print('\n=== 结果分析 ===')
    analyze_results(test_cases, db_results, api_results)

def test_database_matching(test_cases):
    """测试数据库直接查询"""
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    results = []
    
    for case in test_cases:
        length = case['length']
        width = case['width']
        quantity = case['quantity']
        
        query = """
            SELECT name FROM pricing_standards 
            WHERE type = 'printing' 
            AND min_length <= ? AND max_length >= ? 
            AND min_width <= ? AND max_width >= ? 
            AND min_quantity <= ? AND max_quantity >= ? 
            AND is_active = 1 
            ORDER BY created_at DESC 
            LIMIT 1
        """
        
        cursor.execute(query, (length, length, width, width, quantity, quantity))
        result = cursor.fetchone()
        
        matched_name = result[0] if result else None
        results.append(matched_name)
        
        status = '✓' if matched_name == case['expected'] else '✗'
        print(f'  {status} {case["desc"]}: {length}x{width} -> {matched_name} (期望: {case["expected"]})')
    
    conn.close()
    return results

def test_api_matching(test_cases):
    """测试Web API"""
    
    api_url = 'http://localhost:5000/api/pricing_standards/match'
    results = []
    
    for case in test_cases:
        try:
            response = requests.post(api_url, json={
                'length': case['length'],
                'width': case['width'],
                'quantity': case['quantity'],
                'process_name': '印刷'
            }, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                # 从API响应中提取实际的标准名称
                if 'standard' in data and data['standard']:
                    if data['standard']['type'] == 'combined' and 'components' in data['standard']:
                        # 组合工艺，提取第一个组件的名称
                        if data['standard']['components']:
                            matched_name = data['standard']['components'][0]['name']
                        else:
                            matched_name = None
                    else:
                        matched_name = data['standard']['name']
                else:
                    matched_name = None
            else:
                matched_name = None
                
        except Exception as e:
            matched_name = f'错误: {str(e)}'
        
        results.append(matched_name)
        
        status = '✓' if matched_name == case['expected'] else '✗'
        print(f'  {status} {case["desc"]}: {case["length"]}x{case["width"]} -> {matched_name} (期望: {case["expected"]})')
    
    return results

def analyze_results(test_cases, db_results, api_results):
    """分析测试结果"""
    
    db_correct = sum(1 for i, case in enumerate(test_cases) if db_results[i] == case['expected'])
    api_correct = sum(1 for i, case in enumerate(test_cases) if api_results[i] == case['expected'])
    
    total = len(test_cases)
    
    print(f'数据库查询正确率: {db_correct}/{total} ({db_correct/total*100:.1f}%)')
    print(f'API查询正确率: {api_correct}/{total} ({api_correct/total*100:.1f}%)')
    
    # 找出不一致的案例
    inconsistent = []
    for i, case in enumerate(test_cases):
        if db_results[i] != api_results[i]:
            inconsistent.append({
                'case': case,
                'db_result': db_results[i],
                'api_result': api_results[i]
            })
    
    if inconsistent:
        print(f'\n发现 {len(inconsistent)} 个数据库与API结果不一致的案例:')
        for item in inconsistent:
            case = item['case']
            print(f'  {case["desc"]}: DB={item["db_result"]}, API={item["api_result"]}')
    else:
        print('\n数据库与API结果完全一致。')
    
    # 找出错误的案例
    errors = []
    for i, case in enumerate(test_cases):
        if case['expected'] and (db_results[i] != case['expected'] or api_results[i] != case['expected']):
            errors.append({
                'case': case,
                'db_result': db_results[i],
                'api_result': api_results[i]
            })
    
    if errors:
        print(f'\n发现 {len(errors)} 个判定错误的案例:')
        for item in errors:
            case = item['case']
            print(f'  {case["desc"]} ({case["length"]}x{case["width"]}): 期望={case["expected"]}, DB={item["db_result"]}, API={item["api_result"]}')
    else:
        print('\n所有测试案例判定正确！')

if __name__ == '__main__':
    test_all_printing_standards()