import sqlite3
from datetime import datetime

conn = sqlite3.connect('quotation_system.db')
cursor = conn.cursor()

# 添加大全开印刷标准（适用于1200x1600尺寸）
print('添加大全开印刷标准...')
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'printing', '大全开印刷', 
    1100.0, 1700.0,  # 长度范围：1100-1700mm
    1400.0, 1800.0,  # 宽度范围：1400-1800mm
    1, 999999,       # 数量范围
    400.0, 0.8,      # 基础价400元，平方价0.8元/平方米
    '适用于1200x1600等大全开尺寸的印刷', 
    1, 
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))

# 添加大全开光油标准
print('添加大全开光油标准...')
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'varnish', '大全开光油', 
    1100.0, 1700.0,  # 长度范围：1100-1700mm
    1400.0, 1800.0,  # 宽度范围：1400-1800mm
    1, 999999,       # 数量范围
    200.0, 0.4,      # 基础价200元，平方价0.4元/平方米
    '适用于1200x1600等大全开尺寸的光油', 
    1, 
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))

# 添加大全开模切标准
print('添加大全开模切标准...')
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'die-cutting', '大全开模切', 
    1100.0, 1700.0,  # 长度范围：1100-1700mm
    1400.0, 1800.0,  # 宽度范围：1400-1800mm
    1, 999999,       # 数量范围
    500.0, 0.6,      # 基础价500元，平方价0.6元/平方米
    '适用于1200x1600等大全开尺寸的模切', 
    1, 
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))

# 添加大全开切割标准
print('添加大全开切割标准...')
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'cutting', '大全开切割', 
    1100.0, 1700.0,  # 长度范围：1100-1700mm
    1400.0, 1800.0,  # 宽度范围：1400-1800mm
    1, 999999,       # 数量范围
    150.0, 0.2,      # 基础价150元，平方价0.2元/平方米
    '适用于1200x1600等大全开尺寸的切割', 
    1, 
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))

# 添加大全开覆膜标准
print('添加大全开覆膜标准...')
cursor.execute('''
    INSERT INTO pricing_standards 
    (type, name, min_length, max_length, min_width, max_width, min_quantity, max_quantity, base_price, square_price, description, is_active, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
    'lamination', '大全开覆膜', 
    1100.0, 1700.0,  # 长度范围：1100-1700mm
    1400.0, 1800.0,  # 宽度范围：1400-1800mm
    1, 999999,       # 数量范围
    250.0, 0.5,      # 基础价250元，平方价0.5元/平方米
    '适用于1200x1600等大全开尺寸的覆膜', 
    1, 
    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
))

conn.commit()
conn.close()

print('\n所有大全开标准添加完成！')
print('现在1200x1600mm尺寸应该能够正确匹配定价标准了。')