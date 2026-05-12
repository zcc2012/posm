import sqlite3

def check_database_schema_and_data():
    """检查数据库模式和数据类型"""
    
    print('=== 检查数据库模式和数据类型 ===')
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 检查表结构
    print('\n1. pricing_standards 表结构:')
    cursor.execute("PRAGMA table_info(pricing_standards)")
    columns = cursor.fetchall()
    
    for col in columns:
        print(f'  {col[1]}: {col[2]} (NOT NULL: {col[3]}, DEFAULT: {col[4]})')
    
    # 检查实际数据
    print('\n2. 印刷标准的实际数据:')
    cursor.execute("""
        SELECT id, name, min_length, max_length, min_width, max_width, 
               typeof(min_length), typeof(max_length), typeof(min_width), typeof(max_width)
        FROM pricing_standards 
        WHERE type = 'printing' AND is_active = 1
        ORDER BY min_length, min_width
    """)
    
    records = cursor.fetchall()
    
    for record in records:
        print(f'\n{record[1]} (ID: {record[0]}):')
        print(f'  长度: {record[2]} - {record[3]} (类型: {record[6]}, {record[7]})')
        print(f'  宽度: {record[4]} - {record[5]} (类型: {record[8]}, {record[9]})')
    
    # 测试浮点数查询
    print('\n3. 测试浮点数查询:')
    
    test_values = [
        (719, 519, '整数边界'),
        (719.0, 519.0, '浮点数边界'),
        (719.9, 519.9, '接近边界的浮点数'),
        (719.5, 519.5, '中间浮点数')
    ]
    
    for length, width, desc in test_values:
        print(f'\n测试 {desc}: {length} x {width}')
        
        # 精确匹配查询
        cursor.execute("""
            SELECT name, min_length, max_length, min_width, max_width
            FROM pricing_standards 
            WHERE type = 'printing' AND is_active = 1
            AND ? >= min_length AND ? <= max_length
            AND ? >= min_width AND ? <= max_width
            ORDER BY created_at DESC
            LIMIT 1
        """, (length, length, width, width))
        
        result = cursor.fetchone()
        
        if result:
            print(f'  匹配: {result[0]}')
            print(f'  范围: 长度[{result[1]}-{result[2]}] 宽度[{result[3]}-{result[4]}]')
            
            # 验证条件
            length_ok = result[1] <= length <= result[2]
            width_ok = result[3] <= width <= result[4]
            print(f'  验证: 长度条件={length_ok}, 宽度条件={width_ok}')
        else:
            print(f'  无匹配')
            
            # 查看所有标准的匹配情况
            cursor.execute("""
                SELECT name, min_length, max_length, min_width, max_width,
                       (? >= min_length) as length_min_ok,
                       (? <= max_length) as length_max_ok,
                       (? >= min_width) as width_min_ok,
                       (? <= max_width) as width_max_ok
                FROM pricing_standards 
                WHERE type = 'printing' AND is_active = 1
            """, (length, length, width, width))
            
            all_results = cursor.fetchall()
            print(f'  详细检查:')
            for r in all_results:
                print(f'    {r[0]}: 长度[{r[1]}-{r[2]}] 宽度[{r[3]}-{r[4]}]')
                print(f'      条件: {length}>={r[1]}({r[5]}) {length}<={r[2]}({r[6]}) {width}>={r[3]}({r[7]}) {width}<={r[4]}({r[8]})')
    
    # 检查数据精度问题
    print('\n4. 检查数据精度:')
    cursor.execute("""
        SELECT name, 
               CAST(min_length AS TEXT), CAST(max_length AS TEXT),
               CAST(min_width AS TEXT), CAST(max_width AS TEXT)
        FROM pricing_standards 
        WHERE type = 'printing' AND is_active = 1
    """)
    
    precision_records = cursor.fetchall()
    for record in precision_records:
        print(f'{record[0]}: 长度[{record[1]}-{record[2]}] 宽度[{record[3]}-{record[4]}]')
    
    conn.close()

def test_edge_cases():
    """测试边缘情况"""
    
    print('\n=== 测试边缘情况 ===')
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 测试边界值的各种表示方式
    edge_tests = [
        # 4开机器边界 (0-719 x 0-519)
        (719, 519, '4开机器整数边界'),
        (719.0, 519.0, '4开机器浮点边界'),
        (719.1, 519.0, '超出4开机器长度0.1'),
        (719.0, 519.1, '超出4开机器宽度0.1'),
        (719.99, 519.99, '接近4开机器边界'),
        
        # 对开机边界 (720-1019 x 520-719)
        (720, 520, '对开机整数下边界'),
        (720.0, 520.0, '对开机浮点下边界'),
        (719.99, 519.99, '刚好不到对开机'),
        (720.01, 520.01, '刚好进入对开机'),
    ]
    
    for length, width, desc in edge_tests:
        print(f'\n{desc}: {length} x {width}')
        
        # 使用不同的查询方式
        queries = [
            ('标准查询', """
                SELECT name FROM pricing_standards 
                WHERE type = 'printing' AND is_active = 1
                AND ? >= min_length AND ? <= max_length
                AND ? >= min_width AND ? <= max_width
                ORDER BY created_at DESC LIMIT 1
            """),
            ('反向查询', """
                SELECT name FROM pricing_standards 
                WHERE type = 'printing' AND is_active = 1
                AND min_length <= ? AND max_length >= ?
                AND min_width <= ? AND max_width >= ?
                ORDER BY created_at DESC LIMIT 1
            """)
        ]
        
        for query_name, query in queries:
            cursor.execute(query, (length, length, width, width))
            result = cursor.fetchone()
            
            result_name = result[0] if result else 'None'
            print(f'  {query_name}: {result_name}')
    
    conn.close()

if __name__ == '__main__':
    check_database_schema_and_data()
    test_edge_cases()