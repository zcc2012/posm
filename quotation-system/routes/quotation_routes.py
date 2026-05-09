from datetime import datetime
from flask import Blueprint, jsonify, request
from database import get_db_connection
from services.price_calculator import calculate_subtotal, calculate_material_unit_price, refresh_quotation_total

bp = Blueprint('quotations_api', __name__)

@bp.route('/api/quotations', methods=['GET', 'POST'])
def api_quotations():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT q.*, c.name as customer_name
            FROM quotations q
            LEFT JOIN customers c ON q.customer_id = c.id
            ORDER BY q.created_at DESC
        ''')
        quotations = cursor.fetchall()
        conn.close()
        return jsonify([{
            'id': row[0], 'customer_id': row[1], 'quotation_number': row[2],
            'title': row[3], 'total_amount': row[4], 'status': row[5],
            'created_at': row[6], 'customer_name': row[7]
        } for row in quotations])
    
    elif request.method == 'POST':
        data = request.json
        # 生成报价单号
        quotation_number = f"QT{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute('''
            INSERT INTO quotations (customer_id, quotation_number, title)
            VALUES (?, ?, ?)
        ''', (data['customer_id'], quotation_number, data.get('title', '')))
        conn.commit()
        quotation_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': quotation_id, 'quotation_number': quotation_number, 'message': '报价单创建成功'})

@bp.route('/api/quotations/<int:quotation_id>', methods=['GET', 'PUT', 'DELETE'])
def api_quotation_detail(quotation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        # 获取报价单基本信息
        cursor.execute('''
            SELECT q.*, c.name as customer_name, c.company, c.phone, c.email, c.address
            FROM quotations q
            LEFT JOIN customers c ON q.customer_id = c.id
            WHERE q.id = ?
        ''', (quotation_id,))
        quotation = cursor.fetchone()
        
        # 获取报价单明细
        cursor.execute('''
            SELECT qi.*, m.name as material_name, m.specification, m.unit, p.name as process_name
            FROM quotation_items qi
            LEFT JOIN materials m ON qi.material_id = m.id
            LEFT JOIN processes p ON qi.process_id = p.id
            WHERE qi.quotation_id = ?
        ''', (quotation_id,))
        items = cursor.fetchall()
        
        conn.close()
        
        if quotation:
            return jsonify({
                'quotation': {
                    'id': quotation[0], 'customer_id': quotation[1],
                    'quotation_number': quotation[2], 'title': quotation[3],
                    'total_amount': quotation[4], 'status': quotation[5],
                    'created_at': quotation[6], 'customer_name': quotation[7],
                    'customer_company': quotation[8], 'customer_phone': quotation[9],
                    'customer_email': quotation[10], 'customer_address': quotation[11]
                },
                'items': [{
                    'id': item[0], 'quotation_id': item[1], 'material_id': item[2],
                    'quantity': item[3], 'length': item[4], 'width': item[5],
                    'process_id': item[6], 'process_type': item[7], 'unit_price': item[8], 'subtotal': item[9],
                    'material_name': item[10], 'specification': item[11], 'unit': item[12], 'process_name': item[13]
                } for item in items]
            })
        else:
            return jsonify({'error': '报价单不存在'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE quotations SET title=?, status=?
            WHERE id=?
        ''', (data.get('title', ''), data.get('status', 'draft'), quotation_id))
        conn.commit()
        conn.close()
        return jsonify({'message': '报价单更新成功'})
    
    elif request.method == 'DELETE':
        # 删除报价单明细
        cursor.execute('DELETE FROM quotation_items WHERE quotation_id=?', (quotation_id,))
        # 删除报价单
        cursor.execute('DELETE FROM quotations WHERE id=?', (quotation_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '报价单删除成功'})

# API接口 - 报价单明细管理

@bp.route('/api/quotations/<int:quotation_id>/items', methods=['POST'])
def api_quotation_items(quotation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data = request.json
    
    quantity = data.get('quantity', 1)
    unit_price = data.get('unit_price', 0)
    subtotal = calculate_subtotal(quantity, unit_price)
    
    cursor.execute('''
        INSERT INTO quotation_items (quotation_id, name, specification, quantity, unit, unit_price, subtotal, 
                                   category_id, material_id, process_id, process_type, length, width)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (quotation_id, data.get('name', ''), data.get('specification', ''), quantity, 
          data.get('unit', '个'), unit_price, subtotal, data.get('category_id', ''), 
          data.get('material_id'), data.get('process_id'), data.get('process_type', ''), 
          data.get('length', 0), data.get('width', 0)))
    
    refresh_quotation_total(cursor, quotation_id)
    
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': item_id, 'message': '报价项目添加成功'})

# API接口 - 报价单明细管理（新版本）

@bp.route('/api/quotation_items', methods=['POST'])
def api_add_quotation_item():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    data = request.json
    
    quantity = data.get('quantity', 1)
    unit_price = data.get('unit_price', 0)
    subtotal = calculate_subtotal(quantity, unit_price)
    
    cursor.execute('''
        INSERT INTO quotation_items (quotation_id, name, specification, quantity, unit, unit_price, subtotal, 
                                   category_id, material_id, process_id, process_type, length, width)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('quotation_id'), data.get('name', ''), data.get('specification', ''), quantity, 
          data.get('unit', '个'), unit_price, subtotal, data.get('category_id', ''), 
          data.get('material_id'), data.get('process_id'), data.get('process_type', ''), 
          data.get('length', 0), data.get('width', 0)))
    
    quotation_id = data.get('quotation_id')
    refresh_quotation_total(cursor, quotation_id)
    
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': item_id, 'message': '报价项目添加成功'})

@bp.route('/api/quotation_items/<int:item_id>', methods=['PUT', 'DELETE'])
def api_quotation_item_detail(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        
        # 获取quotation_id和material_id
        cursor.execute('SELECT quotation_id, material_id FROM quotation_items WHERE id=?', (item_id,))
        result = cursor.fetchone()
        quotation_id = result[0]
        material_id = result[1]
        
        # 获取材料信息计算单价
        cursor.execute('SELECT unit_price, square_price FROM materials WHERE id=?', (material_id,))
        material = cursor.fetchone()
        
        quantity = data.get('quantity', 1)
        calculated_unit_price = calculate_material_unit_price(
            material,
            data.get('length', 0),
            data.get('width', 0),
            data.get('unit_price', 0)
        )
        subtotal = calculate_subtotal(quantity, calculated_unit_price)
        
        cursor.execute('''
            UPDATE quotation_items SET quantity=?, length=?, width=?, process_id=?, process_type=?, unit_price=?, subtotal=?
            WHERE id=?
        ''', (data.get('quantity', 1), data.get('length', 0), data.get('width', 0), 
              data.get('process_id'), data.get('process_type', ''), calculated_unit_price, subtotal, item_id))
        
        refresh_quotation_total(cursor, quotation_id)
        
        conn.commit()
        conn.close()
        return jsonify({'message': '报价项目更新成功'})
    
    elif request.method == 'DELETE':
        # 获取quotation_id
        cursor.execute('SELECT quotation_id FROM quotation_items WHERE id=?', (item_id,))
        quotation_id = cursor.fetchone()[0]
        
        cursor.execute('DELETE FROM quotation_items WHERE id=?', (item_id,))
        
        refresh_quotation_total(cursor, quotation_id)
        
        conn.commit()
        conn.close()
        return jsonify({'message': '报价项目删除成功'})

