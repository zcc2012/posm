import sqlite3

def auto_sync_processes_with_standards():
    """
    自动同步工艺库与判定标准
    当添加新的判定标准时，自动在工艺库中创建对应的工艺
    """
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 获取所有判定标准的工艺类型
    cursor.execute("SELECT DISTINCT type FROM pricing_standards")
    standard_types = [row[0] for row in cursor.fetchall()]
    
    # 获取当前工艺库中的工艺名称
    cursor.execute("SELECT name FROM processes")
    existing_processes = [row[0] for row in cursor.fetchall()]
    
    # 定义工艺类型与基础工艺的映射
    type_to_base_process = {
        'printing': '印刷',
        'cutting': '切割', 
        'die-cutting': '模切',
        'varnish': '光油',
        'lamination': '覆膜',
        'hot-stamping': '烫金',
        'embossing': '压痕',
        'binding': '装订',
        'folding': '折页'
    }
    
    added_processes = []
    
    # 为每个判定标准类型确保有对应的基础工艺
    for standard_type in standard_types:
        if standard_type in type_to_base_process:
            base_process_name = type_to_base_process[standard_type]
            
            if base_process_name not in existing_processes:
                # 添加基础工艺
                description = f"{base_process_name}工艺"
                components = base_process_name
                
                cursor.execute("""
                    INSERT INTO processes (name, description, base_price, created_at, square_price, wastage, components)
                    VALUES (?, ?, 0.0, datetime('now'), 0.0, 0.0, ?)
                """, (base_process_name, description, components))
                
                added_processes.append(base_process_name)
                existing_processes.append(base_process_name)
    
    conn.commit()
    conn.close()
    
    return added_processes

def update_process_options_in_frontend():
    """
    更新前端工艺选项，确保与数据库同步
    """
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 获取所有工艺
    cursor.execute("SELECT id, name FROM processes ORDER BY name")
    processes = cursor.fetchall()
    
    conn.close()
    
    print("当前可用的工艺选项:")
    for process_id, process_name in processes:
        print(f"ID: {process_id}, 名称: {process_name}")
    
    return processes

if __name__ == "__main__":
    print("执行自动同步...")
    added = auto_sync_processes_with_standards()
    
    if added:
        print(f"新增工艺: {', '.join(added)}")
    else:
        print("无需新增工艺，已保持同步")
    
    print("\n更新工艺选项:")
    update_process_options_in_frontend()