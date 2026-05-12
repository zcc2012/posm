import sqlite3

def check_table_structure():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("检查processes表结构:")
    cursor.execute('PRAGMA table_info(processes)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"列: {col[1]}, 类型: {col[2]}, 非空: {col[3]}, 默认值: {col[4]}, 主键: {col[5]}")
    
    print("\n检查pricing_standards表结构:")
    cursor.execute('PRAGMA table_info(pricing_standards)')
    columns = cursor.fetchall()
    for col in columns:
        print(f"列: {col[1]}, 类型: {col[2]}, 非空: {col[3]}, 默认值: {col[4]}, 主键: {col[5]}")
    
    print("\n当前processes表数据:")
    cursor.execute("SELECT * FROM processes")
    processes = cursor.fetchall()
    for process in processes:
        print(process)
    
    print("\n当前pricing_standards表的工艺类型:")
    cursor.execute("SELECT DISTINCT type FROM pricing_standards")
    types = cursor.fetchall()
    for t in types:
        print(f"类型: {t[0]}")
    
    conn.close()

if __name__ == "__main__":
    check_table_structure()