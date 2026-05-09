import sqlite3

def check_printing_conflicts():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print('=== 检查印刷标准冲突 ===')
    
    # 获取所有激活的印刷标准
    cursor.execute("""
        SELECT id, name, min_length, max_length, min_width, max_width, 
               base_price, square_price, is_active, created_at
        FROM pricing_standards 
        WHERE type = 'printing' AND is_active = 1
        ORDER BY created_at DESC
    """)
    
    standards = cursor.fetchall()
    
    print(f'\n找到 {len(standards)} 个激活的印刷标准:')
    for std in standards:
        print(f'ID: {std[0]}, 名称: {std[1]}')
        print(f'  尺寸范围: {std[2]}-{std[3]} x {std[4]}-{std[5]} mm')
        print(f'  价格: 基础价 {std[6]}, 平方价 {std[7]}')
        print(f'  创建时间: {std[9]}')
        print()
    
    # 检查尺寸范围重叠
    print('=== 检查尺寸范围重叠 ===')
    conflicts = []
    
    for i, std1 in enumerate(standards):
        for j, std2 in enumerate(standards):
            if i >= j:  # 避免重复检查
                continue
                
            # 检查长度范围是否重叠
            length_overlap = not (std1[3] < std2[2] or std2[3] < std1[2])
            # 检查宽度范围是否重叠
            width_overlap = not (std1[5] < std2[4] or std2[5] < std1[4])
            
            if length_overlap and width_overlap:
                conflicts.append((std1, std2))
                print(f'发现冲突:')
                print(f'  {std1[1]} ({std1[2]}-{std1[3]} x {std1[4]}-{std1[5]})')
                print(f'  {std2[1]} ({std2[2]}-{std2[3]} x {std2[4]}-{std2[5]})')
                print()
    
    if not conflicts:
        print('未发现尺寸范围重叠冲突。')
    
    # 测试特定尺寸 300x500
    print('=== 测试尺寸 300x500 的匹配情况 ===')
    test_length, test_width = 300, 500
    
    matching_standards = []
    for std in standards:
        if (test_length >= std[2] and test_length <= std[3] and 
            test_width >= std[4] and test_width <= std[5]):
            matching_standards.append(std)
    
    print(f'尺寸 {test_length}x{test_width} 匹配到 {len(matching_standards)} 个标准:')
    for std in matching_standards:
        print(f'  {std[1]} (ID: {std[0]}) - 创建时间: {std[9]}')
    
    if len(matching_standards) > 1:
        print('\n警告: 发现多个匹配标准! 这可能导致判定错误。')
        print('根据API逻辑，会选择创建时间最新的标准:')
        latest = max(matching_standards, key=lambda x: x[9])
        print(f'  最新标准: {latest[1]} (创建时间: {latest[9]})')
    elif len(matching_standards) == 1:
        print(f'\n正常: 唯一匹配标准为 {matching_standards[0][1]}')
    else:
        print('\n错误: 没有找到匹配的标准!')
    
    # 检查边界情况
    print('\n=== 检查边界情况 ===')
    boundary_tests = [
        (719, 519, '4开机器边界'),
        (720, 520, '对开机边界'),
        (1019, 719, '对开机边界'),
        (1020, 720, '全开机边界')
    ]
    
    for length, width, desc in boundary_tests:
        matches = []
        for std in standards:
            if (length >= std[2] and length <= std[3] and 
                width >= std[4] and width <= std[5]):
                matches.append(std[1])
        print(f'{desc} ({length}x{width}): {matches if matches else "无匹配"}')
    
    conn.close()

if __name__ == '__main__':
    check_printing_conflicts()