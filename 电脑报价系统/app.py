from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

DEFAULT_BASE_PROCESS_OPTIONS = ['印刷', '模切', '光油', '覆膜', '切割', '烫金', '压痕', '装订', '打孔']

def ensure_process_columns(cursor):
    cursor.execute("PRAGMA table_info(processes)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'base_price' not in columns:
        cursor.execute('ALTER TABLE processes ADD COLUMN base_price REAL DEFAULT 0')
    if 'square_price' not in columns:
        cursor.execute('ALTER TABLE processes ADD COLUMN square_price REAL DEFAULT 0')
    if 'base_processes' not in columns:
        cursor.execute("ALTER TABLE processes ADD COLUMN base_processes TEXT DEFAULT ''")

def ensure_base_process_options(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS base_process_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM base_process_options')
    if cursor.fetchone()[0] == 0:
        for process_name in DEFAULT_BASE_PROCESS_OPTIONS:
            cursor.execute('INSERT OR IGNORE INTO base_process_options (name) VALUES (?)', (process_name,))

    ensure_process_columns(cursor)
    cursor.execute("SELECT base_processes FROM processes WHERE base_processes IS NOT NULL AND base_processes != ''")
    for row in cursor.fetchall():
        for process_name in str(row[0]).split(','):
            process_name = process_name.strip()
            if process_name:
                cursor.execute('INSERT OR IGNORE INTO base_process_options (name) VALUES (?)', (process_name,))

def split_base_processes(value):
    return [item.strip() for item in str(value or '').split(',') if item.strip()]

# 数据库初始化
def init_db():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 创建客户信息表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建材料分类表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS material_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建材料库表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specification TEXT,
            unit TEXT,
            unit_price REAL,
            square_price REAL DEFAULT 0,
            supplier TEXT,
            category_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES material_categories (id)
        )
    ''')
    
    # 创建报价单表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER,
            quotation_number TEXT UNIQUE,
            title TEXT,
            total_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
    ''')
    
    # 创建工艺库表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            base_price REAL DEFAULT 0,
            square_price REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建判定标准表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing_standards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            material_category_id INTEGER,
            min_length REAL DEFAULT 0,
            max_length REAL DEFAULT 999999,
            min_width REAL DEFAULT 0,
            max_width REAL DEFAULT 999999,
            min_quantity INTEGER DEFAULT 1,
            max_quantity INTEGER DEFAULT 999999,
            base_price REAL DEFAULT 0,
            square_price REAL DEFAULT 0,
            description TEXT,
            is_active BOOLEAN DEFAULT 1,
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (material_category_id) REFERENCES material_categories (id)
        )
    ''')
    
    # 检查并添加工艺表新字段（用于数据库迁移）
    try:
        cursor.execute("PRAGMA table_info(processes)")
        old_columns = [column[1] for column in cursor.fetchall()]
        ensure_process_columns(cursor)
        if 'unit_price' in old_columns:
            cursor.execute('UPDATE processes SET base_price = unit_price WHERE base_price = 0')
        ensure_base_process_options(cursor)
    except sqlite3.OperationalError:
        pass
    
    # 为判定标准表添加新字段
    try:
        cursor.execute('ALTER TABLE pricing_standards ADD COLUMN material_category_id INTEGER')
        cursor.execute('ALTER TABLE pricing_standards ADD COLUMN priority INTEGER DEFAULT 1')
        print("已添加material_category_id和priority列到pricing_standards表")
    except sqlite3.OperationalError:
        # 字段已存在，忽略错误
        pass
    
    # 添加3个损耗区间字段
    try:
        cursor.execute("PRAGMA table_info(pricing_standards)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'wastage_0_100' not in columns:
            cursor.execute('ALTER TABLE pricing_standards ADD COLUMN wastage_0_100 INTEGER DEFAULT 0')
            print("已添加wastage_0_100列到pricing_standards表")
        if 'wastage_100_3000' not in columns:
            cursor.execute('ALTER TABLE pricing_standards ADD COLUMN wastage_100_3000 INTEGER DEFAULT 0')
            print("已添加wastage_100_3000列到pricing_standards表")
        if 'wastage_3000_plus' not in columns:
            cursor.execute('ALTER TABLE pricing_standards ADD COLUMN wastage_3000_plus INTEGER DEFAULT 0')
            print("已添加wastage_3000_plus列到pricing_standards表")
    except Exception as e:
        print(f"添加pricing_standards表损耗区间列时出错: {e}")
    
    # 创建报价项目明细表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quotation_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quotation_id INTEGER,
            material_id INTEGER,
            process_id INTEGER,
            quantity REAL,
            length REAL DEFAULT 0,
            width REAL DEFAULT 0,
            process_type TEXT,
            unit_price REAL,
            subtotal REAL,
            FOREIGN KEY (quotation_id) REFERENCES quotations (id),
            FOREIGN KEY (material_id) REFERENCES materials (id),
            FOREIGN KEY (process_id) REFERENCES processes (id)
        )
    ''')
    
    # 检查并添加缺失的列（用于数据库迁移）
    try:
        # 检查materials表是否有square_price列和category_id列
        cursor.execute("PRAGMA table_info(materials)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'square_price' not in columns:
            cursor.execute('ALTER TABLE materials ADD COLUMN square_price REAL DEFAULT 0')
            print("已添加square_price列到materials表")
        if 'category_id' not in columns:
            cursor.execute('ALTER TABLE materials ADD COLUMN category_id INTEGER')
            print("已添加category_id列到materials表")
    except Exception as e:
        print(f"添加materials表列时出错: {e}")
    
    try:
        # 检查quotation_items表是否有新增的列
        cursor.execute("PRAGMA table_info(quotation_items)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'length' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN length REAL DEFAULT 0')
            print("已添加length列到quotation_items表")
        if 'width' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN width REAL DEFAULT 0')
            print("已添加width列到quotation_items表")
        if 'process_type' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN process_type TEXT')
            print("已添加process_type列到quotation_items表")
        if 'process_id' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN process_id INTEGER')
            print("已添加process_id列到quotation_items表")
        if 'name' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN name TEXT')
            print("已添加name列到quotation_items表")
        if 'specification' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN specification TEXT')
            print("已添加specification列到quotation_items表")
        if 'unit' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN unit TEXT DEFAULT "个"')
            print("已添加unit列到quotation_items表")
        if 'category_id' not in columns:
            cursor.execute('ALTER TABLE quotation_items ADD COLUMN category_id TEXT')
            print("已添加category_id列到quotation_items表")
    except Exception as e:
        print(f"添加quotation_items列时出错: {e}")
    
    conn.commit()
    conn.close()

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customers')
def customers():
    return render_template('customers.html')

@app.route('/materials')
def materials():
    return render_template('materials.html')

@app.route('/processes')
def processes():
    return render_template('processes.html')

@app.route('/quotations')
def quotations():
    return redirect('/quotation_new')

@app.route('/quotation_display/<int:quotation_id>')
def quotation_display(quotation_id):
    return render_template('quotation_display.html', quotation_id=quotation_id)

@app.route('/test_standards')
def test_standards():
    return send_from_directory('.', 'test_standards_display.html')

@app.route('/quotation_new')
def quotation_new():
    return render_template('quotation_new.html')

@app.route('/price_breakdown')
def price_breakdown():
    return render_template('price_breakdown.html')

@app.route('/graphics')
def graphics():
    return render_template('graphics.html')

# API接口 - 画面管理
@app.route('/api/graphics', methods=['GET', 'POST'])
def api_graphics():
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/graphics/<int:graphic_id>', methods=['GET', 'PUT', 'DELETE'])
def api_graphic_detail(graphic_id):
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/pricing_standards')
def pricing_standards():
    return render_template('pricing_standards.html')

@app.route('/printing_standards_admin')
def printing_standards_admin():
    return render_template('printing_standards_admin.html')

# API接口 - 材料分类管理
@app.route('/api/material_categories', methods=['GET', 'POST'])
def api_material_categories():
    conn = sqlite3.connect('quotation_system.db')
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
@app.route('/api/customers', methods=['GET', 'POST'])
def api_customers():
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/customers/<int:customer_id>', methods=['PUT', 'DELETE'])
def api_customer_detail(customer_id):
    conn = sqlite3.connect('quotation_system.db')
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



@app.route('/api/material_categories/<int:category_id>', methods=['GET', 'PUT', 'DELETE'])
def api_material_category_detail(category_id):
    conn = sqlite3.connect('quotation_system.db')
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
@app.route('/api/materials', methods=['GET', 'POST'])
def api_materials():
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/materials/<int:material_id>', methods=['GET', 'PUT', 'DELETE'])
def api_material_detail(material_id):
    conn = sqlite3.connect('quotation_system.db')
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
@app.route('/api/base_processes', methods=['GET', 'POST'])
def api_base_processes():
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/base_processes/<int:option_id>', methods=['DELETE'])
def api_base_process_detail(option_id):
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/processes', methods=['GET', 'POST'])
def api_processes():
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/processes/<int:process_id>', methods=['PUT', 'DELETE'])
def api_process_detail(process_id):
    conn = sqlite3.connect('quotation_system.db')
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
@app.route('/api/quotations', methods=['GET', 'POST'])
def api_quotations():
    conn = sqlite3.connect('quotation_system.db')
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

@app.route('/api/quotations/<int:quotation_id>', methods=['GET', 'PUT', 'DELETE'])
def api_quotation_detail(quotation_id):
    conn = sqlite3.connect('quotation_system.db')
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
@app.route('/api/quotations/<int:quotation_id>/items', methods=['POST'])
def api_quotation_items(quotation_id):
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    data = request.json
    
    # 计算小计
    quantity = data.get('quantity', 1)
    unit_price = data.get('unit_price', 0)
    subtotal = quantity * unit_price
    
    cursor.execute('''
        INSERT INTO quotation_items (quotation_id, name, specification, quantity, unit, unit_price, subtotal, 
                                   category_id, material_id, process_id, process_type, length, width)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (quotation_id, data.get('name', ''), data.get('specification', ''), quantity, 
          data.get('unit', '个'), unit_price, subtotal, data.get('category_id', ''), 
          data.get('material_id'), data.get('process_id'), data.get('process_type', ''), 
          data.get('length', 0), data.get('width', 0)))
    
    # 更新报价单总金额
    cursor.execute('SELECT SUM(subtotal) FROM quotation_items WHERE quotation_id=?', (quotation_id,))
    total_amount = cursor.fetchone()[0] or 0
    cursor.execute('UPDATE quotations SET total_amount=? WHERE id=?', (total_amount, quotation_id))
    
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': item_id, 'message': '报价项目添加成功'})

# API接口 - 报价单明细管理（新版本）
@app.route('/api/quotation_items', methods=['POST'])
def api_add_quotation_item():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    data = request.json
    
    # 计算小计
    quantity = data.get('quantity', 1)
    unit_price = data.get('unit_price', 0)
    subtotal = quantity * unit_price
    
    cursor.execute('''
        INSERT INTO quotation_items (quotation_id, name, specification, quantity, unit, unit_price, subtotal, 
                                   category_id, material_id, process_id, process_type, length, width)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (data.get('quotation_id'), data.get('name', ''), data.get('specification', ''), quantity, 
          data.get('unit', '个'), unit_price, subtotal, data.get('category_id', ''), 
          data.get('material_id'), data.get('process_id'), data.get('process_type', ''), 
          data.get('length', 0), data.get('width', 0)))
    
    # 更新报价单总金额
    quotation_id = data.get('quotation_id')
    cursor.execute('SELECT SUM(subtotal) FROM quotation_items WHERE quotation_id=?', (quotation_id,))
    total_amount = cursor.fetchone()[0] or 0
    cursor.execute('UPDATE quotations SET total_amount=? WHERE id=?', (total_amount, quotation_id))
    
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'id': item_id, 'message': '报价项目添加成功'})

@app.route('/api/quotation_items/<int:item_id>', methods=['PUT', 'DELETE'])
def api_quotation_item_detail(item_id):
    conn = sqlite3.connect('quotation_system.db')
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
        
        if material:
            base_price = material[0] or 0  # 基础单价
            square_price = material[1] or 0  # 平方单价
            length = data.get('length', 0)
            width = data.get('width', 0)
            quantity = data.get('quantity', 1)
            
            # 计算单价：基础单价 + (长(mm)*宽(mm)/1000000*平方单价)
            area_in_square_meters = (length * width) / 1000000  # 将mm²转换为m²
            calculated_unit_price = base_price + (area_in_square_meters * square_price)
            subtotal = quantity * calculated_unit_price
        else:
            calculated_unit_price = data.get('unit_price', 0)
            subtotal = data.get('quantity', 1) * calculated_unit_price
        
        cursor.execute('''
            UPDATE quotation_items SET quantity=?, length=?, width=?, process_id=?, process_type=?, unit_price=?, subtotal=?
            WHERE id=?
        ''', (data.get('quantity', 1), data.get('length', 0), data.get('width', 0), 
              data.get('process_id'), data.get('process_type', ''), calculated_unit_price, subtotal, item_id))
        
        # 更新报价单总金额
        cursor.execute('SELECT SUM(subtotal) FROM quotation_items WHERE quotation_id=?', (quotation_id,))
        total_amount = cursor.fetchone()[0] or 0
        cursor.execute('UPDATE quotations SET total_amount=? WHERE id=?', (total_amount, quotation_id))
        
        conn.commit()
        conn.close()
        return jsonify({'message': '报价项目更新成功'})
    
    elif request.method == 'DELETE':
        # 获取quotation_id
        cursor.execute('SELECT quotation_id FROM quotation_items WHERE id=?', (item_id,))
        quotation_id = cursor.fetchone()[0]
        
        cursor.execute('DELETE FROM quotation_items WHERE id=?', (item_id,))
        
        # 更新报价单总金额
        cursor.execute('SELECT SUM(subtotal) FROM quotation_items WHERE quotation_id=?', (quotation_id,))
        total_amount = cursor.fetchone()[0] or 0
        cursor.execute('UPDATE quotations SET total_amount=? WHERE id=?', (total_amount, quotation_id))
        
        conn.commit()
        conn.close()
        return jsonify({'message': '报价项目删除成功'})

# API接口 - 判定标准管理
@app.route('/api/pricing_standards', methods=['GET', 'POST'])
def api_pricing_standards():
    conn = sqlite3.connect('quotation_system.db')
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
                components = base_process_name
                
                cursor.execute("""
                    INSERT INTO processes (name, description, base_price, created_at, square_price)
                    VALUES (?, ?, 0.0, datetime('now'), 0.0)
                """, (base_process_name, description))
                conn.commit()
                print(f"自动添加工艺: {base_process_name}")
        
        conn.close()
        return jsonify({'id': standard_id, 'message': '判定标准添加成功，工艺库已同步'})

@app.route('/api/pricing_standards/<int:standard_id>', methods=['PUT', 'DELETE'])
def api_pricing_standard_detail(standard_id):
    conn = sqlite3.connect('quotation_system.db')
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
@app.route('/api/pricing_standards/match', methods=['POST'])
def api_match_pricing_standard():
    data = request.json
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
    
    conn = sqlite3.connect('quotation_system.db')
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
        return jsonify({'standard': combined_standard, 'message': f'找到{len(matched_standards)}项匹配的标准'})
    else:
        return jsonify({'standard': None, 'message': '未找到匹配的标准'})

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
