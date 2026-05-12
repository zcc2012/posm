import sqlite3

def sync_process_standards():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("同步工艺库与判定标准...")
    
    # 获取判定标准中的工艺类型
    cursor.execute("SELECT DISTINCT type FROM pricing_standards")
    standard_types = [row[0] for row in cursor.fetchall()]
    print(f"判定标准中的工艺类型: {standard_types}")
    
    # 定义工艺类型与工艺名称的映射关系
    type_to_process_mapping = {
        'printing': ['印刷', '印刷+模切', '印刷+光油', '印刷+覆膜', '印刷+光油+模切', '印刷+覆膜+模切'],
        'cutting': ['切割'],
        'die-cutting': ['模切', '覆膜+模切'],
        'varnish': ['光油'],
        'lamination': ['覆膜']
    }
    
    # 收集所有应该存在的工艺名称
    required_processes = []
    for process_type in standard_types:
        if process_type in type_to_process_mapping:
            required_processes.extend(type_to_process_mapping[process_type])
    
    print(f"应该存在的工艺: {required_processes}")
    
    # 获取当前工艺库中的工艺
    cursor.execute("SELECT id, name FROM processes")
    current_processes = cursor.fetchall()
    current_process_names = [row[1] for row in current_processes]
    
    print(f"当前工艺库中的工艺: {current_process_names}")
    
    # 删除多余的工艺
    deleted_count = 0
    for process_id, process_name in current_processes:
        if process_name not in required_processes:
            print(f"删除多余工艺: {process_name}")
            cursor.execute("DELETE FROM processes WHERE id = ?", (process_id,))
            deleted_count += 1
    
    # 添加缺失的工艺
    added_count = 0
    process_definitions = {
        '印刷': ('基础印刷工艺', '印刷'),
        '模切': ('模切成型工艺', '模切'),
        '光油': ('表面光油处理', '光油'),
        '覆膜': ('覆膜保护工艺', '覆膜'),
        '切割': ('精密切割工艺', '切割'),
        '印刷+模切': ('印刷后模切组合工艺', '印刷,模切'),
        '印刷+光油': ('印刷后光油组合工艺', '印刷,光油'),
        '印刷+覆膜': ('印刷后覆膜组合工艺', '印刷,覆膜'),
        '覆膜+模切': ('覆膜后模切组合工艺', '覆膜,模切'),
        '印刷+光油+模切': ('印刷光油模切组合工艺', '印刷,光油,模切'),
        '印刷+覆膜+模切': ('印刷覆膜模切组合工艺', '印刷,覆膜,模切')
    }
    
    # 重新获取当前工艺名称（删除后的）
    cursor.execute("SELECT name FROM processes")
    remaining_process_names = [row[0] for row in cursor.fetchall()]
    
    for process_name in required_processes:
        if process_name not in remaining_process_names:
            if process_name in process_definitions:
                description, components = process_definitions[process_name]
                print(f"添加缺失工艺: {process_name}")
                cursor.execute("""
                    INSERT INTO processes (name, description, base_price, created_at, square_price, wastage, components)
                    VALUES (?, ?, 0.0, datetime('now'), 0.0, 0.0, ?)
                """, (process_name, description, components))
                added_count += 1
    
    conn.commit()
    
    # 验证同步结果
    print("\n同步后的工艺库:")
    cursor.execute("SELECT name FROM processes ORDER BY name")
    final_processes = [row[0] for row in cursor.fetchall()]
    for process in final_processes:
        print(f"- {process}")
    
    conn.close()
    
    print(f"\n同步完成:")
    print(f"- 删除了 {deleted_count} 个多余工艺")
    print(f"- 添加了 {added_count} 个缺失工艺")
    print(f"- 工艺库现在包含 {len(final_processes)} 个工艺")
    print("工艺库与判定标准已保持一致")

if __name__ == "__main__":
    sync_process_standards()