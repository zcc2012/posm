import requests
import json

def test_web_api():
    """测试Web API的实际调用"""
    
    print('=== 测试Web API调用 ===')
    
    # 测试API端点
    base_url = 'http://localhost:5000'
    api_url = f'{base_url}/api/pricing_standards/match'
    
    # 测试数据
    test_data = {
        'length': 300,
        'width': 500,
        'quantity': 1000,
        'process_name': '印刷'
    }
    
    print(f'请求URL: {api_url}')
    print(f'请求数据: {json.dumps(test_data, ensure_ascii=False, indent=2)}')
    
    try:
        # 发送POST请求
        response = requests.post(api_url, json=test_data, timeout=10)
        
        print(f'\n响应状态码: {response.status_code}')
        print(f'响应头: {dict(response.headers)}')
        
        if response.status_code == 200:
            result = response.json()
            print(f'\n✓ API调用成功!')
            print(f'响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}')
            
            if 'name' in result:
                print(f'\n匹配到的标准: {result["name"]}')
                if result['name'] == '4开机器':
                    print('✓ 匹配结果正确!')
                else:
                    print(f'✗ 匹配结果错误! 期望: 4开机器, 实际: {result["name"]}')
        else:
            print(f'\n✗ API调用失败!')
            print(f'错误信息: {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('\n✗ 无法连接到服务器!')
        print('请确保Flask应用正在运行 (python app.py)')
        
    except Exception as e:
        print(f'\n✗ 请求异常: {str(e)}')

def test_multiple_cases():
    """测试多个案例"""
    
    print('\n=== 测试多个案例 ===')
    
    base_url = 'http://localhost:5000'
    api_url = f'{base_url}/api/pricing_standards/match'
    
    test_cases = [
        {'length': 300, 'width': 500, 'quantity': 1000, 'process_name': '印刷', 'expected': '4开机器'},
        {'length': 500, 'width': 300, 'quantity': 1000, 'process_name': '印刷', 'expected': '4开机器'},
        {'length': 720, 'width': 520, 'quantity': 1000, 'process_name': '印刷', 'expected': '对开机'},
        {'length': 1020, 'width': 720, 'quantity': 1000, 'process_name': '印刷', 'expected': '全开机'}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        expected = test_case.pop('expected')
        
        print(f'\n--- 案例 {i}: {test_case["length"]}x{test_case["width"]} ---')
        
        try:
            response = requests.post(api_url, json=test_case, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                actual = result.get('name', '未知')
                
                if actual == expected:
                    print(f'✓ 正确: {actual}')
                else:
                    print(f'✗ 错误: 期望 {expected}, 实际 {actual}')
            else:
                print(f'✗ API错误: {response.status_code}')
                
        except requests.exceptions.ConnectionError:
            print('✗ 服务器未运行')
            break
        except Exception as e:
            print(f'✗ 异常: {str(e)}')

if __name__ == '__main__':
    test_web_api()
    test_multiple_cases()