#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加工艺基础组合字段的数据库迁移脚本
"""

import sqlite3
import os

def add_base_processes_field():
    """为processes表添加base_processes字段"""
    
    # 连接数据库
    db_path = 'quotation_system.db'
    if not os.path.exists(db_path):
        print(f"错误：数据库文件 {db_path} 不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(processes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'base_processes' in columns:
            print("base_processes字段已存在，无需添加")
            conn.close()
            return True
        
        # 添加base_processes字段
        cursor.execute('''
            ALTER TABLE processes 
            ADD COLUMN base_processes TEXT DEFAULT ''
        ''')
        
        conn.commit()
        print("成功添加base_processes字段到processes表")
        
        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(processes)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'base_processes' in columns:
            print("字段添加验证成功")
            
            # 为现有工艺数据设置base_processes值
            cursor.execute("SELECT id, name FROM processes")
            existing_processes = cursor.fetchall()
            
            for process_id, process_name in existing_processes:
                # 如果工艺名称包含+号，说明是组合工艺
                if '+' in process_name:
                    base_processes = process_name.split('+')
                    base_processes_str = ','.join([bp.strip() for bp in base_processes])
                else:
                    # 单一工艺，base_processes就是自己
                    base_processes_str = process_name.strip()
                
                cursor.execute('''
                    UPDATE processes 
                    SET base_processes = ? 
                    WHERE id = ?
                ''', (base_processes_str, process_id))
            
            conn.commit()
            print(f"已为{len(existing_processes)}个现有工艺设置base_processes值")
            
        else:
            print("错误：字段添加失败")
            conn.close()
            return False
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"数据库操作错误：{e}")
        return False
    except Exception as e:
        print(f"未知错误：{e}")
        return False

if __name__ == '__main__':
    print("开始添加base_processes字段...")
    success = add_base_processes_field()
    
    if success:
        print("\n迁移完成！")
        print("现在工艺表支持基础工艺组合功能。")
    else:
        print("\n迁移失败！请检查错误信息。")