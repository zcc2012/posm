from database import get_db_connection

def match_pricing_standard(data):
    process_name = data.get('process_name', '')
    material_name = data.get('material_name', '')
    material_category_name = data.get('material_category_name', '')
    material_category_id = data.get('material_category_id')
    try:
        material_category_id = int(material_category_id) if material_category_id not in (None, '') else None
    except (TypeError, ValueError):
        material_category_id = None
    try:
        length = float(data.get('length', 0) or 0)
        width = float(data.get('width', 0) or 0)
        quantity = float(data.get('quantity', 1) or 1)
    except (TypeError, ValueError):
        length = 0
        width = 0
        quantity = 1
    
    max_dimension = max(length, width)
    min_dimension = min(length, width)
    full_match_text = f"{process_name} {material_name} {material_category_name}".lower()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 对于组合工艺，需要计算所有包含的工艺费用
    total_base_price = 0
    total_square_price = 0
    matched_standards = []
    
    process_keyword_map = [
        ('printing', ['印刷', '打印']),
        ('die-cutting', ['模切']),
        ('cutting', ['切割', '裁切']),
        ('varnish', ['光油', '上光']),
        ('lamination', ['覆膜', '光膜', '哑膜', '亮膜']),
        ('hot-stamping', ['烫金']),
        ('embossing', ['压痕']),
        ('binding', ['装订']),
        ('folding', ['折页']),
        ('punching', ['打孔', '钻孔'])
    ]
    
    process_types = []
    for process_type, keywords in process_keyword_map:
        if any(keyword in process_name for keyword in keywords) and process_type not in process_types:
            process_types.append(process_type)
    
    if not process_types and process_name.strip():
        cursor.execute('''
            SELECT DISTINCT type
            FROM pricing_standards
            WHERE is_active=1
            AND name=?
        ''', (process_name,))
        process_types = [row[0] for row in cursor.fetchall()]
    
    if not process_types and process_name.strip():
        cursor.execute('''
            SELECT DISTINCT type
            FROM pricing_standards
            WHERE is_active=1
            AND (? LIKE '%' || name || '%' OR name LIKE '%' || ? || '%')
        ''', (process_name, process_name))
        process_types = [row[0] for row in cursor.fetchall()]
    
    material_keywords = ['写真', '画面', 'uv', '喷绘', '背胶', '亚克力', '卡纸', '坑纸', '纸', '木板', '金属', 'pvc']
    
    def candidate_score(row):
        standard_id, standard_type, standard_name, standard_category_id = row[0], row[1], row[2], row[3]
        min_length, max_length, min_width, max_width = row[4], row[5], row[6], row[7]
        min_quantity, max_quantity = row[8], row[9]
        priority, created_at = row[15], row[16]
        standard_name_text = str(standard_name or '').lower()
        
        category_score = 0
        if material_category_id is not None and standard_category_id == material_category_id:
            category_score = 2
        elif standard_category_id is None:
            category_score = 1
        
        name_score = 0
        if standard_name_text and standard_name_text in full_match_text:
            name_score += 4
        for keyword in material_keywords:
            if keyword in standard_name_text:
                name_score += 3 if keyword in full_match_text else -3
        
        upper_long = max(max_length or 0, max_width or 0)
        upper_short = min(max_length or 0, max_width or 0)
        capacity_area = upper_long * upper_short
        oversize_margin = max(upper_long - max_dimension, 0) + max(upper_short - min_dimension, 0)
        quantity_span = max((max_quantity or 0) - (min_quantity or 0), 0)
        
        return (
            category_score,
            name_score,
            -capacity_area,
            -oversize_margin,
            -quantity_span,
            -(priority or 1),
            str(created_at or '')
        )
    
    # 为每种工艺类型查找匹配的标准
    for process_type in process_types:
        cursor.execute('''
            SELECT 
                id, type, name, material_category_id,
                min_length, max_length, min_width, max_width,
                min_quantity, max_quantity,
                base_price, square_price, 
                wastage, order_length_increase, order_width_increase,
                priority, created_at
            FROM pricing_standards 
            WHERE type=? AND is_active=1 
            AND (material_category_id IS NULL OR material_category_id=?)
            AND ? <= max(COALESCE(max_length, 0), COALESCE(max_width, 0))
            AND ? <= min(COALESCE(max_length, 0), COALESCE(max_width, 0))
            AND ? >= min_quantity AND ? <= max_quantity
        ''', (process_type, material_category_id, max_dimension, min_dimension, quantity, quantity))
        
        candidates = cursor.fetchall()
        result = max(candidates, key=candidate_score) if candidates else None
        if result:
            total_base_price += result[10]  # base_price
            total_square_price += result[11]  # square_price
            matched_standards.append({
                'id': result[0], 'type': result[1], 'name': result[2],
                'material_category_id': result[3],
                'min_length': result[4], 'max_length': result[5],
                'min_width': result[6], 'max_width': result[7],
                'min_quantity': result[8], 'max_quantity': result[9],
                'base_price': result[10], 'square_price': result[11],
                'wastage': result[12] if result[12] is not None else 0,
                'order_length_increase': result[13] if result[13] is not None else 0,
                'order_width_increase': result[14] if result[14] is not None else 0
            })
    
    conn.close()
    
    if matched_standards:
        # 计算总损耗（取最大值）
        total_wastage = max([std.get('wastage', 0) for std in matched_standards]) if matched_standards else 0
        
        # 计算组合的下单增加尺寸（取最大值）
        total_order_length_increase = max([std.get('order_length_increase', 0) for std in matched_standards]) if matched_standards else 0
        total_order_width_increase = max([std.get('order_width_increase', 0) for std in matched_standards]) if matched_standards else 0
        
        # 返回组合后的标准
        combined_standard = {
            'id': 0, 'type': 'combined', 'name': f'组合工艺({len(matched_standards)}项)',
            'base_price': total_base_price, 'square_price': total_square_price,
            'wastage': total_wastage,
            'order_length_increase': total_order_length_increase,
            'order_width_increase': total_order_width_increase,
            'components': matched_standards
        }
        return {'standard': combined_standard, 'message': f'找到{len(matched_standards)}项匹配的标准'}
    else:
        return {'standard': None, 'message': '未找到匹配的标准'}
