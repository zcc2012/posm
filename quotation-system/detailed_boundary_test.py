import sqlite3
import requests
import json

def test_boundary_overlaps():
    """详细测试边界重叠和临界值"""
    
    print('=== 详细边界重叠测试 ===')
    
    # 连接数据库
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 获取所有印刷标准
    cursor.execute("""
        SELECT id, name, min_length, max_length, min_width, max_width, 
               min_quantity, max_quantity, is_active, created_at
        FROM pricing_standards 
        WHERE type = 'printing' AND is_active = 1
        ORDER BY min_length, min_width
    """)
    
    standards = cursor.fetchall()
    
    print(f'\n印刷标准详情:')
    for std in standards:
        print(f'{std[1]}: 长度[{std[2]}-{std[3]}] x 宽度[{std[4]}-{std[5]}] 数量[{std[6]}-{std[7]}] 激活:{std[8]} 创建:{std[9]}')
    
    # 检查边界重叠
    print('\n=== 检查边界重叠 ===')
    overlaps = []
    
    for i, std1 in enumerate(standards):
        for j, std2 in enumerate(standards):
            if i >= j:
                continue
                
            # 检查长度重叠
            length_overlap = not (std1[3] < std2[2] or std2[3] < std1[2])
            # 检查宽度重叠
            width_overlap = not (std1[5] < std2[4] or std2[5] < std1[4])
            
            if length_overlap and width_overlap:
                overlaps.append((std1, std2))
                print(f'发现重叠: {std1[1]} 与 {std2[1]}')
                print(f'  {std1[1]}: 长度[{std1[2]}-{std1[3]}] x 宽度[{std1[4]}-{std1[5]}]')
                print(f'  {std2[1]}: 长度[{std2[2]}-{std2[3]}] x 宽度[{std2[4]}-{std2[5]}]')
    
    if not overlaps:
        print('未发现边界重叠。')
    
    # 测试关键边界点
    print('\n=== 测试关键边界点 ===')
    
    boundary_tests = [
        # 4开机器边界
        (719, 519, '4开机器最大边界'),
        (719.5, 519, '4开机器边界+0.5'),
        (720, 519, '长度刚好超出4开机器'),
        (719, 519.5, '宽度刚好超出4开机器'),
        (720, 520, '刚好进入对开机'),
        
        # 对开机边界
        (1019, 719, '对开机最大边界'),
        (1019.5, 719, '对开机边界+0.5'),
        (1020, 719, '长度刚好超出对开机'),
        (1019, 719.5, '宽度刚好超出对开机'),
        (1020, 720, '刚好进入全开机'),
        
        # 全开机边界
        (1419, 1019, '全开机最大边界'),
        (1419.5, 1019, '全开机边界+0.5'),
        (1420, 1019, '长度刚好超出全开机'),
        (1419, 1019.5, '宽度刚好超出全开机'),
        (1420, 1020, '刚好进入大全开'),
        
        # 特殊测试点
        (300, 500, '用户报告问题点'),
        (500, 300, '长宽互换'),
        (0, 0, '最小值'),
        (719.9, 519.9, '接近4开机器边界'),
        (720.1, 520.1, '刚超过4开机器边界')
    ]
    
    for length, width, desc in boundary_tests:
        print(f'\n测试点: {desc} ({length}x{width})')
        
        # 数据库查询
        cursor.execute("""
            SELECT name, min_length, max_length, min_width, max_width, created_at
            FROM pricing_standards 
            WHERE type = 'printing' AND is_active = 1
            AND min_length <= ? AND max_length >= ? 
            AND min_width <= ? AND max_width >= ? 
            AND min_quantity <= 1000 AND max_quantity >= 1000
            ORDER BY created_at DESC
        """, (length, length, width, width))
        
        matches = cursor.fetchall()
        
        if len(matches) == 0:
            print(f'  数据库: 无匹配')
        elif len(matches) == 1:
            print(f'  数据库: {matches[0][0]} ✓')
        else:
            print(f'  数据库: 发现多个匹配! 这是问题!')
            for match in matches:
                print(f'    - {match[0]} (范围: {match[1]}-{match[2]} x {match[3]}-{match[4]}, 创建: {match[5]})')
            print(f'    选择: {matches[0][0]} (最新创建)')
        
        # API测试
        try:
            response = requests.post('http://localhost:5000/api/pricing_standards/match', json={
                'length': length,
                'width': width,
                'quantity': 1000,
                'process_name': '印刷'
            }, timeout=3)
            
            if response.status_code == 200:
                data = response.json()
                if 'standard' in data and data['standard']:
                    if data['standard']['type'] == 'combined' and 'components' in data['standard']:
                        if data['standard']['components']:
                            api_result = data['standard']['components'][0]['name']
                        else:
                            api_result = 'None'
                    else:
                        api_result = data['standard']['name']
                else:
                    api_result = 'None'
                    
                print(f'  API: {api_result}')
                
                # 比较结果
                db_result = matches[0][0] if matches else 'None'
                if api_result == db_result:
                    print(f'  结果: 一致 ✓')
                else:
                    print(f'  结果: 不一致 ✗ (DB: {db_result}, API: {api_result})')
            else:
                print(f'  API: 错误 {response.status_code}')
                
        except Exception as e:
            print(f'  API: 异常 {str(e)}')
    
    conn.close()

def check_gap_coverage():
    """检查是否存在尺寸覆盖空隙"""
    
    print('\n=== 检查尺寸覆盖空隙 ===')
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, min_length, max_length, min_width, max_width
        FROM pricing_standards 
        WHERE type = 'printing' AND is_active = 1
        ORDER BY min_length, min_width
    """)
    
    standards = cursor.fetchall()
    
    # 检查长度维度的连续性
    print('\n长度维度连续性检查:')
    length_ranges = [(std[1], std[2], std[0]) for std in standards]
    length_ranges.sort()
    
    for i in range(len(length_ranges) - 1):
        current_max = length_ranges[i][1]
        next_min = length_ranges[i+1][0]
        
        if current_max + 1 < next_min:
            print(f'  发现长度空隙: {current_max} 到 {next_min} ({length_ranges[i][2]} -> {length_ranges[i+1][2]})')
        elif current_max >= next_min:
            print(f'  发现长度重叠: {length_ranges[i][2]}({current_max}) 与 {length_ranges[i+1][2]}({next_min})')
    
    # 检查宽度维度的连续性
    print('\n宽度维度连续性检查:')
    width_ranges = [(std[3], std[4], std[0]) for std in standards]
    width_ranges.sort()
    
    for i in range(len(width_ranges) - 1):
        current_max = width_ranges[i][1]
        next_min = width_ranges[i+1][0]
        
        if current_max + 1 < next_min:
            print(f'  发现宽度空隙: {current_max} 到 {next_min} ({width_ranges[i][2]} -> {width_ranges[i+1][2]})')
        elif current_max >= next_min:
            print(f'  发现宽度重叠: {width_ranges[i][2]}({current_max}) 与 {width_ranges[i+1][2]}({next_min})')
    
    conn.close()

if __name__ == '__main__':
    test_boundary_overlaps()
    check_gap_coverage()