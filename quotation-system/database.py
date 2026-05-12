import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().with_name('quotation_system.db')

def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

def ensure_column(cursor, table_name, column_name, definition):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

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

def init_db():
    conn = get_db_connection()
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
    
    # 判定标准表结构升级
    for column_name, definition in {
        'material_category_id': 'INTEGER',
        'priority': 'INTEGER DEFAULT 1',
        'wastage': 'INTEGER DEFAULT 0',
        'order_length_increase': 'REAL DEFAULT 0',
        'order_width_increase': 'REAL DEFAULT 0',
        'wastage_0_100': 'INTEGER DEFAULT 0',
        'wastage_100_3000': 'INTEGER DEFAULT 0',
        'wastage_3000_plus': 'INTEGER DEFAULT 0',
    }.items():
        try:
            ensure_column(cursor, 'pricing_standards', column_name, definition)
        except Exception as e:
            print(f'升级pricing_standards.{column_name}时出错: {e}')

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

