import sqlite3
from flask import Blueprint, jsonify, request
from database import get_db_connection, ensure_base_process_options, split_base_processes

bp = Blueprint('processes_api', __name__)

@bp.route('/api/base_processes', methods=['GET', 'POST'])
def api_base_processes():
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_base_process_options(cursor)
    
    if request.method == 'GET':
        cursor.execute('SELECT id, name, created_at FROM base_process_options ORDER BY id ASC')
        options = cursor.fetchall()
        conn.commit()
        conn.close()
        return jsonify([{
            'id': row[0],
            'name': row[1],
            'created_at': row[2]
        } for row in options])
    
    data = request.json or {}
    name = str(data.get('name', '')).strip()
    if not name:
        conn.close()
        return jsonify({'message': '基础工艺名称不能为空'}), 400
    
    try:
        cursor.execute('INSERT INTO base_process_options (name) VALUES (?)', (name,))
        conn.commit()
        option_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': option_id, 'message': '基础工艺添加成功'})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'message': '该基础工艺已存在'}), 409

@bp.route('/api/base_processes/<int:option_id>', methods=['DELETE'])
def api_base_process_detail(option_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_base_process_options(cursor)
    
    cursor.execute('SELECT name FROM base_process_options WHERE id=?', (option_id,))
    option = cursor.fetchone()
    if not option:
        conn.close()
        return jsonify({'message': '基础工艺不存在'}), 404
    
    option_name = option[0]
    cursor.execute("SELECT id, name, base_processes FROM processes WHERE base_processes IS NOT NULL AND base_processes != ''")
    used_by = [
        row[1] for row in cursor.fetchall()
        if option_name in split_base_processes(row[2])
    ]
    if used_by:
        conn.close()
        return jsonify({
            'message': f'基础工艺“{option_name}”已被 {len(used_by)} 个组合工艺使用，请先编辑或删除相关工艺',
            'used_by': used_by
        }), 409
    
    cursor.execute('DELETE FROM base_process_options WHERE id=?', (option_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': '基础工艺删除成功'})

@bp.route('/api/processes', methods=['GET', 'POST'])
def api_processes():
    conn = get_db_connection()
    cursor = conn.cursor()
    ensure_base_process_options(cursor)
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT id, name, description, created_at, base_processes, base_price, square_price
            FROM processes
            ORDER BY created_at DESC
        ''')
        processes = cursor.fetchall()
        conn.commit()
        conn.close()
        return jsonify([{
            'id': row[0], 'name': row[1], 'description': row[2], 'created_at': row[3], 
            'base_processes': split_base_processes(row[4]),
            'base_price': row[5] or 0,
            'square_price': row[6] or 0
        } for row in processes])
    
    elif request.method == 'POST':
        data = request.json
        base_processes = [str(item).strip() for item in data.get('base_processes', []) if str(item).strip()]
        base_processes_str = ','.join(base_processes) if base_processes else ''
        for process_name in base_processes:
            cursor.execute('INSERT OR IGNORE INTO base_process_options (name) VALUES (?)', (process_name,))
        
        cursor.execute('''
            INSERT INTO processes (name, description, base_processes)
            VALUES (?, ?, ?)
        ''', (data['name'], data.get('description', ''), base_processes_str))
        conn.commit()
        process_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': process_id, 'message': '工艺添加成功'})

@bp.route('/api/processes/<int:process_id>', methods=['PUT', 'DELETE'])
def api_process_detail(process_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        ensure_base_process_options(cursor)
        base_processes = [str(item).strip() for item in data.get('base_processes', []) if str(item).strip()]
        base_processes_str = ','.join(base_processes) if base_processes else ''
        for process_name in base_processes:
            cursor.execute('INSERT OR IGNORE INTO base_process_options (name) VALUES (?)', (process_name,))
        
        cursor.execute('''
            UPDATE processes SET name=?, description=?, base_processes=?
            WHERE id=?
        ''', (data['name'], data.get('description', ''), base_processes_str, process_id))
        conn.commit()
        conn.close()
        return jsonify({'message': '工艺信息更新成功'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM processes WHERE id=?', (process_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '工艺删除成功'})

# API接口 - 报价单管理
