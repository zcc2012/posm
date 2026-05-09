from database import get_db_connection, split_base_processes


PROCESS_KEYWORD_MAP = [
    ('printing', ['印刷', '打印']),
    ('die-cutting', ['模切']),
    ('cutting', ['切割', '裁切']),
    ('varnish', ['光油', '上光']),
    ('lamination', ['覆膜', '光膜', '哑膜', '亮膜']),
    ('hot-stamping', ['烫金']),
    ('embossing', ['压痕']),
    ('binding', ['装订']),
    ('folding', ['折页']),
    ('punching', ['打孔', '钻孔']),
    ('wastage', ['损耗']),
]

MATERIAL_KEYWORDS = ['写真', '画面', 'uv', '喷绘', '背胶', '亚克力', '卡纸', '坑纸', '纸', '木板', '金属', 'pvc']


def to_float(value, default=0):
    try:
        if value in (None, ''):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    try:
        if value in (None, ''):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def in_range(value, min_value, max_value):
    min_value = to_float(min_value, 0)
    max_value = to_float(max_value, 999999)
    return min_value <= value <= max_value


def size_matches(length, width, standard):
    """严格判断尺寸，同时支持长宽旋转匹配。

    例：标准长 0-500、宽 0-300 时，输入 400×250 正常命中；
    标准长 300-500、宽 0-300 时，输入 250×400 也可以旋转命中。
    """
    min_length = standard['min_length']
    max_length = standard['max_length']
    min_width = standard['min_width']
    max_width = standard['max_width']

    normal_match = in_range(length, min_length, max_length) and in_range(width, min_width, max_width)
    rotated_match = in_range(width, min_length, max_length) and in_range(length, min_width, max_width)
    return normal_match or rotated_match


def quantity_matches(quantity, standard):
    return in_range(quantity, standard['min_quantity'], standard['max_quantity'])


def get_wastage_by_quantity(standard, quantity):
    quantity = to_float(quantity, 1)
    if quantity <= 100:
        return to_int(standard.get('wastage_0_100'), to_int(standard.get('wastage'), 0)) or 0
    if quantity <= 3000:
        return to_int(standard.get('wastage_100_3000'), to_int(standard.get('wastage'), 0)) or 0
    return to_int(standard.get('wastage_3000_plus'), to_int(standard.get('wastage'), 0)) or 0


def standard_from_row(row):
    return {
        'id': row[0],
        'type': row[1],
        'name': row[2],
        'material_category_id': row[3],
        'min_length': to_float(row[4], 0),
        'max_length': to_float(row[5], 999999),
        'min_width': to_float(row[6], 0),
        'max_width': to_float(row[7], 999999),
        'min_quantity': to_float(row[8], 1),
        'max_quantity': to_float(row[9], 999999),
        'base_price': to_float(row[10], 0),
        'square_price': to_float(row[11], 0),
        'wastage': to_int(row[12], 0) or 0,
        'wastage_0_100': to_int(row[13], 0) or 0,
        'wastage_100_3000': to_int(row[14], 0) or 0,
        'wastage_3000_plus': to_int(row[15], 0) or 0,
        'order_length_increase': to_float(row[16], 0),
        'order_width_increase': to_float(row[17], 0),
        'priority': to_int(row[18], 1) or 1,
        'created_at': row[19] or '',
    }


def get_standard_rows(cursor, standard_type, material_category_id):
    cursor.execute(
        '''
        SELECT
            id, type, name, material_category_id,
            min_length, max_length, min_width, max_width,
            min_quantity, max_quantity,
            base_price, square_price,
            wastage, wastage_0_100, wastage_100_3000, wastage_3000_plus,
            order_length_increase, order_width_increase,
            priority, created_at
        FROM pricing_standards
        WHERE type=?
          AND is_active=1
          AND (material_category_id IS NULL OR material_category_id=?)
        ''',
        (standard_type, material_category_id),
    )
    return [standard_from_row(row) for row in cursor.fetchall()]


def get_candidate_score(standard, full_match_text):
    standard_name_text = str(standard.get('name') or '').lower()

    name_score = 0
    if standard_name_text and standard_name_text in full_match_text:
        name_score += 4

    for keyword in MATERIAL_KEYWORDS:
        if keyword in standard_name_text:
            name_score += 3 if keyword in full_match_text else -3

    length_span = max(standard['max_length'] - standard['min_length'], 0)
    width_span = max(standard['max_width'] - standard['min_width'], 0)
    quantity_span = max(standard['max_quantity'] - standard['min_quantity'], 0)
    size_area_span = length_span * width_span

    # 分数越大越优先：priority 越大越优先，尺寸/数量范围越窄越优先。
    return (
        standard.get('priority', 1),
        name_score,
        -size_area_span,
        -quantity_span,
        standard.get('id', 0),
    )


def choose_best_standard(standards, length, width, quantity, full_match_text):
    matched = [
        standard for standard in standards
        if size_matches(length, width, standard) and quantity_matches(quantity, standard)
    ]
    if not matched:
        return None
    return max(matched, key=lambda standard: get_candidate_score(standard, full_match_text))


def load_process_tokens(cursor, process_name):
    tokens = [process_name]
    if not process_name:
        return tokens

    cursor.execute('SELECT base_processes FROM processes WHERE name=?', (process_name,))
    row = cursor.fetchone()
    if row and row[0]:
        tokens.extend(split_base_processes(row[0]))

    return [token for token in tokens if str(token).strip()]


def detect_process_types(process_tokens):
    process_types = []
    joined_text = ' '.join(process_tokens)

    for process_type, keywords in PROCESS_KEYWORD_MAP:
        if any(keyword in joined_text for keyword in keywords) and process_type not in process_types:
            process_types.append(process_type)

    return process_types


def find_process_types_by_standard_name(cursor, process_name):
    if not process_name.strip():
        return []

    cursor.execute(
        '''
        SELECT DISTINCT type
        FROM pricing_standards
        WHERE is_active=1
          AND (name=? OR ? LIKE '%' || name || '%' OR name LIKE '%' || ? || '%')
        ''',
        (process_name, process_name, process_name),
    )
    return [row[0] for row in cursor.fetchall()]


def match_material_standard(cursor, material_category_id, length, width, quantity, full_match_text):
    if material_category_id is None:
        return None

    material_standards = get_standard_rows(cursor, 'material', material_category_id)
    return choose_best_standard(material_standards, length, width, quantity, full_match_text)


def match_process_standard(cursor, process_type, material_category_id, length, width, quantity, full_match_text):
    process_standards = get_standard_rows(cursor, process_type, material_category_id)
    return choose_best_standard(process_standards, length, width, quantity, full_match_text)


def match_pricing_standard(data):
    process_name = str(data.get('process_name', '') or '').strip()
    material_name = str(data.get('material_name', '') or '').strip()
    material_category_name = str(data.get('material_category_name', '') or '').strip()
    material_category_id = to_int(data.get('material_category_id'), None)
    length = to_float(data.get('length'), 0)
    width = to_float(data.get('width'), 0)
    quantity = to_float(data.get('quantity'), 1)
    full_match_text = f"{process_name} {material_name} {material_category_name}".lower()

    conn = get_db_connection()
    cursor = conn.cursor()

    process_tokens = load_process_tokens(cursor, process_name)
    process_types = detect_process_types(process_tokens)
    if not process_types:
        process_types = find_process_types_by_standard_name(cursor, process_name)

    matched_material_standard = match_material_standard(
        cursor, material_category_id, length, width, quantity, full_match_text
    )

    matched_process_standards = []
    unmatched_process_types = []

    for process_type in process_types:
        matched_standard = match_process_standard(
            cursor, process_type, material_category_id, length, width, quantity, full_match_text
        )
        if matched_standard:
            matched_standard['wastage'] = get_wastage_by_quantity(matched_standard, quantity)
            matched_process_standards.append(matched_standard)
        else:
            unmatched_process_types.append(process_type)

    conn.close()

    debug = {
        'input': {
            'process_name': process_name,
            'process_tokens': process_tokens,
            'process_types': process_types,
            'material_name': material_name,
            'material_category_id': material_category_id,
            'material_category_name': material_category_name,
            'length': length,
            'width': width,
            'quantity': quantity,
        },
        'matched_process_count': len(matched_process_standards),
        'unmatched_process_types': unmatched_process_types,
        'matched_material_standard_id': matched_material_standard.get('id') if matched_material_standard else None,
    }

    if not matched_process_standards:
        return {
            'standard': None,
            'material_standard': matched_material_standard,
            'message': '未找到匹配的工艺判定标准',
            'debug': debug,
        }

    total_base_price = sum(standard.get('base_price', 0) for standard in matched_process_standards)
    total_square_price = sum(standard.get('square_price', 0) for standard in matched_process_standards)
    total_wastage = max([standard.get('wastage', 0) for standard in matched_process_standards] or [0])

    material_order_length_increase = matched_material_standard.get('order_length_increase', 0) if matched_material_standard else 0
    material_order_width_increase = matched_material_standard.get('order_width_increase', 0) if matched_material_standard else 0

    total_order_length_increase = max(
        [standard.get('order_length_increase', 0) for standard in matched_process_standards] + [material_order_length_increase]
    )
    total_order_width_increase = max(
        [standard.get('order_width_increase', 0) for standard in matched_process_standards] + [material_order_width_increase]
    )

    combined_standard = {
        'id': 0,
        'type': 'combined',
        'name': f'组合工艺({len(matched_process_standards)}项)',
        'base_price': total_base_price,
        'square_price': total_square_price,
        'wastage': total_wastage,
        'wastage_0_100': max([standard.get('wastage_0_100', 0) for standard in matched_process_standards] or [0]),
        'wastage_100_3000': max([standard.get('wastage_100_3000', 0) for standard in matched_process_standards] or [0]),
        'wastage_3000_plus': max([standard.get('wastage_3000_plus', 0) for standard in matched_process_standards] or [0]),
        'order_length_increase': total_order_length_increase,
        'order_width_increase': total_order_width_increase,
        'components': matched_process_standards,
        'material_standard': matched_material_standard,
    }

    return {
        'standard': combined_standard,
        'material_standard': matched_material_standard,
        'message': f'找到{len(matched_process_standards)}项匹配的工艺判定标准',
        'debug': debug,
    }
