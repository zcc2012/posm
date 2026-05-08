from datetime import datetime
from flask import Blueprint, jsonify, request
from database import get_db_connection

bp = Blueprint('customers_api', __name__)

@bp.route('/api/customers', methods=['GET', 'POST'])
def api_customers():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM customers ORDER BY created_at DESC')
        customers = cursor.fetchall()
        conn.close()
        return jsonify([{
            'id': row[0], 'name': row[1], 'company': row[2],
            'phone': row[3], 'email': row[4], 'address': row[5],
            'created_at': row[6]
        } for row in customers])
    
    elif request.method == 'POST':
        data = request.json
        cursor.execute('''
            INSERT INTO customers (name, company, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['name'], data.get('company', ''), data.get('phone', ''),
              data.get('email', ''), data.get('address', '')))
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': customer_id, 'message': '客户添加成功'})

@bp.route('/api/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def api_customer_detail(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        cursor.execute('''
            UPDATE customers SET name=?, company=?, phone=?, email=?, address=?
            WHERE id=?
        ''', (data['name'], data.get('company', ''), data.get('phone', ''),
              data.get('email', ''), data.get('address', ''), customer_id))
        conn.commit()
        conn.close()
        return jsonify({'message': '客户信息更新成功'})
    
    elif request.method == 'DELETE':
        cursor.execute('DELETE FROM customers WHERE id=?', (customer_id,))
        conn.commit()
        conn.close()
        return jsonify({'message': '客户删除成功'})
