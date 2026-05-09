import sqlite3
import requests
import json

def test_auto_sync_functionality():
    """
    测试自动同步功能：添加新判定标准时自动创建对应工艺
    """
    print("=== 测试自动同步功能 ===")
    
    # 1. 查看当前工艺库状态
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    print("\n1. 当前工艺库状态:")
    cursor.execute("SELECT name FROM processes ORDER BY name")
    current_processes = [row[0] for row in cursor.fetchall()]
    for process in current_processes:
        print(f"  - {process}")
    
    # 2. 添加一个新的判定标准类型（如果不存在）
    test_standard = {
        'type': 'hot-stamping',
        'name': '烫金标准测试',
        'min_length': 100,
        'max_length': 500,
        'min_width': 100,
        'max_width': 400,
        'min_quantity': 1,
        'max_quantity': 10000,
        'base_price': 200,
        'square_price': 0.5,
        'description': '测试烫金工艺自动同步',
        'is_active': True,
        'priority': 1
    }
    
    print(f"\n2. 添加新判定标准: {test_standard['type']} - {test_standard['name']}")
    
    try:
        # 发送POST请求添加判定标准
        response = requests.post('http://localhost:5000/api/pricing_standards', 
                               json=test_standard,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print(f"  添加成功: {result['message']}")
            standard_id = result['id']
            
            # 3. 检查工艺库是否自动添加了对应工艺
            print("\n3. 检查工艺库更新:")
            cursor.execute("SELECT name FROM processes ORDER BY name")
            updated_processes = [row[0] for row in cursor.fetchall()]
            
            new_processes = set(updated_processes) - set(current_processes)
            if new_processes:
                print(f"  新增工艺: {', '.join(new_processes)}")
            else:
                print("  未发现新增工艺")
            
            # 4. 验证烫金工艺是否存在
            if '烫金' in updated_processes:
                print("  ✓ 烫金工艺已自动添加")
            else:
                print("  ✗ 烫金工艺未添加")
            
            # 5. 清理测试数据
            print("\n4. 清理测试数据...")
            delete_response = requests.delete(f'http://localhost:5000/api/pricing_standards/{standard_id}')
            if delete_response.status_code == 200:
                print("  测试判定标准已删除")
            
        else:
            print(f"  添加失败: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("  错误: 无法连接到服务器，请确保应用正在运行")
    except Exception as e:
        print(f"  错误: {str(e)}")
    
    conn.close()
    
    print("\n=== 测试完成 ===")

def test_existing_standards_sync():
    """
    测试现有判定标准与工艺库的同步状态
    """
    print("\n=== 检查现有标准同步状态 ===")
    
    conn = sqlite3.connect('quotation_system.db')
    cursor = conn.cursor()
    
    # 获取所有判定标准类型
    cursor.execute("SELECT DISTINCT type FROM pricing_standards")
    standard_types = [row[0] for row in cursor.fetchall()]
    
    # 获取所有工艺名称
    cursor.execute("SELECT name FROM processes")
    process_names = [row[0] for row in cursor.fetchall()]
    
    # 检查映射关系
    type_to_process_mapping = {
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
    
    print("\n判定标准类型与工艺对应关系:")
    for standard_type in standard_types:
        expected_process = type_to_process_mapping.get(standard_type, '未定义')
        exists = expected_process in process_names
        status = "✓" if exists else "✗"
        print(f"  {standard_type} -> {expected_process} {status}")
    
    conn.close()

if __name__ == "__main__":
    test_existing_standards_sync()
    test_auto_sync_functionality()