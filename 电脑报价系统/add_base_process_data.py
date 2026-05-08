#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def add_base_process_data():
    """添加基础工艺数据"""
    db_path = 'quotation_system.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    # 基础工艺数据
    base_processes = [
        {
            'name': '印刷',
            'description': '各种印刷工艺，包括数码印刷、胶印等',
            'base_processes': '印刷'
        },
        {
            'name': '模切',
            'description': '模切成型工艺，用于裁切各种形状',
            'base_processes': '模切'
        },
        {
            'name': '光油',
            'description': '表面光油处理，增加光泽度和保护性',
            'base_processes': '光油'
        },
        {
            'name': '覆膜',
            'description': '覆膜工艺，提供保护和美观效果',
            'base_processes': '覆膜'
        },
        {
            'name': '切割',
            'description': '精密切割工艺，用于各种材料切割',
            'base_processes': '切割'
        },
        {
            'name': '烫金',
            'description': '烫金工艺，增加产品档次和美观度',
            'base_processes': '烫金'
        },
        {
            'name': '压痕',
            'description': '压痕工艺，便于折叠和成型',
            'base_processes': '压痕'
        },
        {
            'name': '印刷+模切',
            'description': '印刷后进行模切的组合工艺',
            'base_processes': '印刷,模切'
        },
        {
            'name': '印刷+光油',
            'description': '印刷后进行光油处理的组合工艺',
            'base_processes': '印刷,光油'
        },
        {
            'name': '印刷+覆膜',
            'description': '印刷后进行覆膜的组合工艺',
            'base_processes': '印刷,覆膜'
        }
    ]
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("开始添加基础工艺数据...")
        
        # 检查每个工艺是否已存在
        added_count = 0
        updated_count = 0
        
        for process in base_processes:
            # 检查工艺是否已存在
            cursor.execute('SELECT id FROM processes WHERE name = ?', (process['name'],))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有工艺的base_processes字段
                cursor.execute(
                    'UPDATE processes SET base_processes = ?, description = ? WHERE name = ?',
                    (process['base_processes'], process['description'], process['name'])
                )
                updated_count += 1
                print(f"更新工艺: {process['name']}")
            else:
                # 添加新工艺
                cursor.execute(
                    'INSERT INTO processes (name, description, base_processes) VALUES (?, ?, ?)',
                    (process['name'], process['description'], process['base_processes'])
                )
                added_count += 1
                print(f"添加工艺: {process['name']}")
        
        conn.commit()
        
        print(f"\n基础工艺数据处理完成！")
        print(f"新增工艺: {added_count} 个")
        print(f"更新工艺: {updated_count} 个")
        
        # 验证数据
        cursor.execute('SELECT COUNT(*) FROM processes')
        total_count = cursor.fetchone()[0]
        print(f"当前工艺总数: {total_count} 个")
        
        conn.close()
        
    except Exception as e:
        print(f"添加基础工艺数据时出错: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    add_base_process_data()