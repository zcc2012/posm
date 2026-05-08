import sqlite3

def test_300x500():
    """专门测试300x500尺寸的匹配情况"""
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print('=== 专门测试 300x500 尺寸匹配 ===')
    
    length = 300
    width = 500
    quantity = 1000
    process_type = 'printing'
    
    print(f'测试参数: 长度={length}, 宽度={width}, 数量={quantity}, 工艺类型={process_type}')
    
    # 完全模拟API的SQL查询
    query = """
        SELECT * FROM pricing_standards 
        WHERE type = ? 
        AND min_length <= ? AND max_length >= ? 
        AND min_width <= ? AND max_width >= ? 
        AND min_quantity <= ? AND max_quantity >= ? 
        AND is_active = 1 
        ORDER BY created_at DESC 
        LIMIT 1
    """
    
    print('\n执行SQL查询...')
    cursor.execute(query, (process_type, length, length, width, width, quantity, quantity))
    result = cursor.fetchone()
    
    if result:
        print(f'\n✓ 匹配成功!')
        print(f'标准名称: {result[2]}')
        print(f'标准ID: {result[0]}')
        print(f'尺寸范围: {result[3]}-{result[4]} x {result[5]}-{result[6]} mm')
        print(f'数量范围: {result[7]}-{result[8]}')
        print(f'基础价: {result[9]}')
        print(f'平方价: {result[10]}')
        print(f'激活状态: {result[11]}')
        print(f'创建时间: {result[12]}')
    else:
        print('\n✗ 未找到匹配的标准!')
        
        # 详细调试
        print('\n=== 调试信息 ===')
        
        # 检查所有印刷标准
        cursor.execute("""
            SELECT id, name, min_length, max_length, min_width, max_width, 
                   min_quantity, max_quantity, is_active
            FROM pricing_standards 
            WHERE type = ?
        """, (process_type,))
        
        all_standards = cursor.fetchall()
        print(f'\n找到 {len(all_standards)} 个印刷标准:')
        
        for std in all_standards:
            std_id, name, min_l, max_l, min_w, max_w, min_q, max_q, is_active = std
            
            length_ok = min_l <= length <= max_l
            width_ok = min_w <= width <= max_w
            quantity_ok = min_q <= quantity <= max_q
            active_ok = is_active == 1
            
            all_ok = length_ok and width_ok and quantity_ok and active_ok
            
            print(f'\n标准: {name} (ID: {std_id})')
            print(f'  长度条件: {length} ∈ [{min_l}, {max_l}] = {length_ok}')
            print(f'  宽度条件: {width} ∈ [{min_w}, {max_w}] = {width_ok}')
            print(f'  数量条件: {quantity} ∈ [{min_q}, {max_q}] = {quantity_ok}')
            print(f'  激活状态: {is_active} = {active_ok}')
            print(f'  总体匹配: {all_ok}')
    
    conn.close()

if __name__ == '__main__':
    test_300x500()