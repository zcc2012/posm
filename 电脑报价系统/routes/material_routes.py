import sqlite3
from flask import Blueprint, jsonify, request
from database import get_db_connection

bp = Blueprint('materials_api', __name__)

@bp.route('/api/material_categories', methods=['GET', 'POST'])
def api_material_categories():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM material_categories ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        return jsonify([{
            'id': row[0], 'name': row[1], 'description': row[2], 'created_at': row[3]
        } for row in categories])
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO material_categories (name, description)
            VALUES (?, ?)
        ''', (data['name'], data.get('description', '')))
        conn.commit()
        category_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': category_id, 'message': '材料分类添加成功'})

# API接口 - 客户管理

@bp.route('/api/material_categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
def api_material_category_detail(category_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM material_categories WHERE id=?', (category_id,))
        category = cursor.fetchone()
        conn.close()
        if category:
            return jsonify({
                'id': category[0], 'name': category[1], 'description': category[2], 'created_at': category[3]
            })
        else:
            return jsonify({'error': '分类不存在'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        try:
            cursor.execute('''
                UPDATE material_categories SET name=?, description=?
                WHERE id=?
            ''', (data['name'], data.get('description', ''), category_id))
            conn.commit()
            conn.close()
            return jsonify({'message': '分类信息更新成功'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'error': '分类名称已存在'}), 400
    
    elif request.method == 'DELETE':
        # 检查是否有材料使用此分类
        cursor.execute('SELECT COUNT(*) FROM materials WHERE category_id=?', (category_id,))
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return jsonify({'error': f'该分类下还有{count}个材料，无法删除'}), 400
        
        cursor.execute('DELETE FROM material_categories WHERE id=?', (category_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '分类删除成功'})

# API接口 - 材料管理

@bp.route('/api/materials', methods=['GET', 'POST'])
def api_materials():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT m.*, c.name as category_name 
            FROM materials m 
            LEFT JOIN material_categories c ON m.category_id = c.id 
            ORDER BY m.created_at DESC
        ''')
        materials = cursor.fetchall()
        conn.close()
        return jsonify([{
            'id': row[0], 'name': row[1], 'specification': row[2],
            'unit': row[3], 'unit_price': float(row[4]) if row[4] else 0, 'square_price': float(row[7]) if row[7] else 0,
            'supplier': row[5], 'category_id': row[8], 'created_at': row[6],
            'category_name': row[9] if row[9] else '未分类'
        } for row in materials])
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO materials (name, specification, unit, unit_price, supplier, square_price, category_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['name'], data.get('specification', ''), data.get('unit', ''),
              data.get('unit_price', 0), data.get('supplier', ''), data.get('square_price', 0), 
              data.get('category_id') if data.get('category_id') else None))
        conn.commit()
        material_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': material_id, 'message': '材料添加成功'})

@bp.route('/api/materials/<int:material_id>', methods=['GET', 'PUT', 'DELETE'])
def api_material_detail(material_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT m.*, c.name as category_name 
            FROM materials m 
            LEFT JOIN material_categories c ON m.category_id = c.id 
            WHERE m.id=?
        ''', (material_id,))
        material = cursor.fetchone()
        conn.close()
        if material:
            return jsonify({
                'id': material[0], 'name': material[1], 'specification': material[2],
                'unit': material[3], 'unit_price': float(material[4]) if material[4] else 0, 'square_price': float(material[7]) if material[7] else 0,
                'supplier': material[5], 'category_id': material[8], 'created_at': material[6],
                'category_name': material[9] if material[9] else '未分类'
            })
        else:
            return jsonify({'error': '材料不存在'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE materials SET name=?, specification=?, unit=?, unit_price=?, supplier=?, square_price=?, category_id=?
            WHERE id=?
        ''', (data['name'], data.get('specification', ''), data.get('unit', ''),
              data.get('unit_price', 0), data.get('supplier', ''), data.get('square_price', 0),
              data.get('category_id') if data.get('category_id') else None, material_id))
        conn.commit()
        conn.close()
        return jsonify({'message': '材料信息更新成功'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM materials WHERE id=?', (material_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '材料删除成功'})

# API接口 - 工艺管理
