from flask import Blueprint, jsonify, request
from database import get_db_connection

bp = Blueprint('graphics_api', __name__)

@bp.route('/api/graphics', methods=['GET', 'POST'])
def api_graphics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 确保graphics表存在
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS graphics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            length REAL DEFAULT 0,
            width REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    if request.method == 'GET':
        cursor.execute('SELECT id, name, description, length, width, created_at FROM graphics ORDER BY created_at DESC')
        graphics = cursor.fetchall()
        conn.close()
        return jsonify([{
            'id': row[0], 'name': row[1], 'description': row[2],
            'length': row[3], 'width': row[4], 'created_at': row[5]
        } for row in graphics])
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO graphics (name, description, length, width)
            VALUES (?, ?, ?, ?)
        ''', (data['name'], data.get('description', ''), data.get('length', 0), data.get('width', 0)))
        conn.commit()
        graphic_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': graphic_id, 'message': '画面添加成功'})

@bp.route('/api/graphics/<int:graphic_id>', methods=['GET', 'PUT', 'DELETE'])
def api_graphic_detail(graphic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT id, name, description, length, width, created_at FROM graphics WHERE id=?', (graphic_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return jsonify({
                'id': result[0], 'name': result[1], 'description': result[2],
                'length': result[3], 'width': result[4], 'created_at': result[5]
            })
        else:
            return jsonify({'error': '画面不存在'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE graphics SET name=?, description=?, length=?, width=?
            WHERE id=?
        ''', (data['name'], data.get('description', ''), data.get('length', 0), data.get('width', 0), graphic_id))
        conn.commit()
        conn.close()
        return jsonify({'message': '画面信息更新成功'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM graphics WHERE id=?', (graphic_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '画面删除成功'})
