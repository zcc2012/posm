import sqlite3

def clean_process_data():
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("清理工艺数据，确保与判定标准一致...")
    
    # 获取判定标准中使用的工艺类型
    cursor.execute("SELECT DISTINCT type FROM pricing_standards")
    standard_types = [row[0] for row in cursor.fetchall()]
    print(f"判定标准中的工艺类型: {standard_types}")
    
    # 获取当前工艺库中的所有工艺
    cursor.execute("SELECT id, name, components FROM processes")
    processes = cursor.fetchall()
    print(f"\n当前工艺库中的工艺:")
    for process in processes:
        print(f"ID: {process[0]}, 名称: {process[1]}, 组件: {process[2]}")
    
    # 定义标准工艺映射
    standard_processes = {
        'printing': ['印刷', '印刷+覆膜+模切', '印刷+光油+模切'],
        'cutting': ['切割'],
        'die-cutting': ['模切', '覆膜+模切']
    }
    
    # 找出需要保留的工艺
    valid_process_names = []
    for process_type, names in standard_processes.items():
        valid_process_names.extend(names)
    
    print(f"\n应该保留的工艺名称: {valid_process_names}")
    
    # 删除不匹配的工艺
    deleted_count = 0
    for process in processes:
        process_id, process_name, components = process
        if process_name not in valid_process_names:
            print(f"删除多余工艺: {process_name} (ID: {process_id})")
            cursor.execute("DELETE FROM processes WHERE id = ?", (process_id,))
            deleted_count += 1
    
    # 确保必要的工艺存在
    cursor.execute("SELECT name FROM processes")
    existing_names = [row[0] for row in cursor.fetchall()]
    
    missing_processes = [
        ('印刷', '基础印刷工艺', '印刷'),
        ('模切', '模切工艺', '模切'),
        ('覆膜+模切', '覆膜加模切组合工艺', '覆膜,模切'),
        ('印刷+覆膜+模切', '印刷覆膜模切组合工艺', '印刷,覆膜,模切'),
        ('印刷+光油+模切', '印刷光油模切组合工艺', '印刷,光油,模切'),
        ('切割', '精密切割工艺', '切割')
    ]
    
    added_count = 0
    for name, description, components in missing_processes:
        if name not in existing_names:
            print(f"添加缺失工艺: {name}")
            cursor.execute("""
                INSERT INTO processes (name, description, components, created_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (name, description, components))
            added_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n清理完成:")
    print(f"- 删除了 {deleted_count} 个多余工艺")
    print(f"- 添加了 {added_count} 个缺失工艺")
    print("工艺库现在与判定标准保持一致")

if __name__ == "__main__":
    clean_process_data()