from flask import Blueprint, jsonify, request
from database import get_db_connection
from services.pricing_matcher import match_pricing_standard

bp = Blueprint('pricing_standards_api', __name__)

@bp.route('/api/pricing_standards', methods=['GET', 'POST'])
def api_pricing_standards():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT 
                ps.id, ps.type, ps.name, ps.material_category_id,
                ps.min_length, ps.max_length, ps.min_width, ps.max_width,
                ps.min_quantity, ps.max_quantity, ps.base_price, ps.square_price,
                ps.description, ps.is_active, ps.priority, ps.created_at,
                ps.wastage_0_100, ps.wastage_100_3000, ps.wastage_3000_plus,
                ps.order_length_increase, ps.order_width_increase,
                mc.name as category_name
            FROM pricing_standards ps 
            LEFT JOIN material_categories mc ON ps.material_category_id = mc.id 
            ORDER BY ps.type, ps.min_length, ps.min_width, ps.max_length, ps.max_width, ps.min_quantity, ps.max_quantity, ps.created_at DESC
        ''')
        standards = cursor.fetchall()
        conn.close()
        return jsonify([{
            'id': row[0], 'type': row[1], 'name': row[2],
            'material_category_id': row[3],
            'min_length': row[4], 'max_length': row[5],
            'min_width': row[6], 'max_width': row[7],
            'min_quantity': row[8], 'max_quantity': row[9],
            'base_price': row[10], 'square_price': row[11],
            'description': row[12], 'is_active': bool(row[13]),
            'priority': row[14], 'created_at': row[15],
            'wastage_0_100': row[16] if len(row) > 16 and row[16] is not None else 80,
            'wastage_100_3000': row[17] if len(row) > 17 and row[17] is not None else 40,
            'wastage_3000_plus': row[18] if len(row) > 18 and row[18] is not None else 20,
            'order_length_increase': row[19] if len(row) > 19 and row[19] is not None else 0,
            'order_width_increase': row[20] if len(row) > 20 and row[20] is not None else 0,
            'category_name': row[21] if len(row) > 21 and row[21] else '通用标准'
        } for row in standards])
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO pricing_standards (type, name, material_category_id, min_length, max_length, min_width, max_width,
                                         min_quantity, max_quantity, base_price, square_price, description, is_active, priority,
                                         wastage_0_100, wastage_100_3000, wastage_3000_plus,
                                         order_length_increase, order_width_increase)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['type'], data['name'], data.get('material_category_id'), data.get('min_length', 0), data.get('max_length', 999999),
              data.get('min_width', 0), data.get('max_width', 999999), data.get('min_quantity', 1),
              data.get('max_quantity', 999999), data.get('base_price', 0), data.get('square_price', 0),
              data.get('description', ''), data.get('is_active', True), data.get('priority', 1),
              data.get('wastage_0_100', 80), data.get('wastage_100_3000', 40), data.get('wastage_3000_plus', 20),
              data.get('order_length_increase', 0), data.get('order_width_increase', 0)))
        conn.commit()
        standard_id = cursor.lastrowid
        
        # 自动同步工艺库 - 确保新的判定标准类型在工艺库中有对应的工艺
        standard_type = data['type']
        type_to_process_mapping = {
            'printing': '印刷',
            'cutting': '切割', 
            'die-cutting': '模切',
            'varnish': '光油',
            'lamination': '覆膜',
            'hot-stamping': '烫金',
            'embossing': '压痕',
            'binding': '装订',
            'folding': '折页',
            'punching': '打孔'
        }
        
        if standard_type in type_to_process_mapping:
            base_process_name = type_to_process_mapping[standard_type]
            
            # 检查工艺是否已存在
            cursor.execute("SELECT COUNT(*) FROM processes WHERE name = ?", (base_process_name,))
            if cursor.fetchone()[0] == 0:
                # 添加对应的基础工艺
                description = f"{base_process_name}工艺"
                
                cursor.execute("""
                    INSERT INTO processes (name, description, base_price, created_at, square_price)
                    VALUES (?, ?, 0.0, datetime('now'), 0.0)
                """, (base_process_name, description))
                conn.commit()
                print(f"自动添加工艺: {base_process_name}")
        
        conn.close()
        return jsonify({'id': standard_id, 'message': '判定标准添加成功，工艺库已同步'})

@bp.route('/api/pricing_standards/<int:standard_id>', methods=['PUT', 'DELETE'])
def api_pricing_standard_detail(standard_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE pricing_standards SET type=?, name=?, material_category_id=?, min_length=?, max_length=?, min_width=?, max_width=?,
                                       min_quantity=?, max_quantity=?, base_price=?, square_price=?, description=?, is_active=?, priority=?,
                                       wastage_0_100=?, wastage_100_3000=?, wastage_3000_plus=?,
                                       order_length_increase=?, order_width_increase=?
            WHERE id=?
        ''', (data['type'], data['name'], data.get('material_category_id'), data.get('min_length', 0), data.get('max_length', 999999),
              data.get('min_width', 0), data.get('max_width', 999999), data.get('min_quantity', 1),
              data.get('max_quantity', 999999), data.get('base_price', 0), data.get('square_price', 0),
              data.get('description', ''), data.get('is_active', True), data.get('priority', 1),
              data.get('wastage_0_100', 80), data.get('wastage_100_3000', 40), data.get('wastage_3000_plus', 20),
              data.get('order_length_increase', 0), data.get('order_width_increase', 0), standard_id))
        conn.commit()
        conn.close()
        return jsonify({'message': '判定标准更新成功'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM pricing_standards WHERE id=?', (standard_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '判定标准删除成功'})

# API接口 - 获取匹配的判定标准

@bp.route('/api/pricing_standards/match', methods=['POST'])
def api_match_pricing_standard():
    return jsonify(match_pricing_standard(request.json or {}))

