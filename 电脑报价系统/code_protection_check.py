#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印刷标准判定逻辑代码保护检查工具
用于检测核心业务逻辑是否被意外修改
"""

import hashlib
import re
import os
from datetime import datetime

class CodeProtectionChecker:
    def __init__(self):
        self.template_file = r'e:\电脑报价系统\templates\quotation_new.html'
        # 预期的代码哈希值（基于当前受保护的印刷标准逻辑）
        self.expected_hash = None
        self.protection_markers = [
            '核心业务逻辑保护区域',
            'PRINT_LOGIC_v2.1_PROTECTED',
            '核心参数-请勿随意修改'
        ]
        
    def extract_printing_logic(self):
        """提取印刷标准判定逻辑代码"""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 查找印刷逻辑保护区域
            start_pattern = r'// ==================== 核心业务逻辑保护区域 ===================='
            end_pattern = r'// ==================== 保护区域结束 ========================'
            
            start_match = re.search(start_pattern, content)
            end_match = re.search(end_pattern, content)
            
            if start_match and end_match:
                logic_code = content[start_match.start():end_match.end()]
                return logic_code
            else:
                return None
                
        except Exception as e:
            print(f"❌ 读取文件失败: {e}")
            return None
    
    def calculate_code_hash(self, code):
        """计算代码哈希值"""
        if code:
            # 移除空白字符和注释，只计算核心逻辑的哈希
            clean_code = re.sub(r'\s+', '', code)
            clean_code = re.sub(r'//.*?\n', '', clean_code)
            return hashlib.md5(clean_code.encode('utf-8')).hexdigest()
        return None
    
    def check_protection_markers(self, code):
        """检查保护标记是否完整"""
        if not code:
            return False
            
        missing_markers = []
        for marker in self.protection_markers:
            if marker not in code:
                missing_markers.append(marker)
        
        if missing_markers:
            print(f"⚠️ 缺失保护标记: {missing_markers}")
            return False
        return True
    
    def check_printing_parameters(self, code):
        """检查印刷参数是否正确"""
        if not code:
            return False
            
        # 检查关键参数
        expected_params = [
            ('4开机器', 'basePrice: 600', 'squarePrice: 0.15'),
            ('对开机', 'basePrice: 1000', 'squarePrice: 0.25'),
            ('全开机', 'basePrice: 1500', 'squarePrice: 0.3'),
            ('大全开', 'basePrice: 2000', 'squarePrice: 0.35'),
            ('大幅面印刷', 'basePrice: 2000', 'squarePrice: 0.4')
        ]
        
        issues = []
        for machine, base_price, square_price in expected_params:
            if machine not in code:
                issues.append(f"缺失机器类型: {machine}")
            elif base_price not in code or square_price not in code:
                issues.append(f"参数异常: {machine}")
        
        if issues:
            print(f"❌ 参数检查失败: {issues}")
            return False
        return True
    
    def generate_baseline(self):
        """生成基线哈希值"""
        code = self.extract_printing_logic()
        if code:
            hash_value = self.calculate_code_hash(code)
            print(f"📋 生成基线哈希值: {hash_value}")
            
            # 保存基线到文件
            baseline_file = 'printing_logic_baseline.txt'
            with open(baseline_file, 'w', encoding='utf-8') as f:
                f.write(f"基线时间: {datetime.now()}\n")
                f.write(f"哈希值: {hash_value}\n")
                f.write(f"代码长度: {len(code)}\n")
            
            print(f"✅ 基线已保存到: {baseline_file}")
            return hash_value
        return None
    
    def load_baseline(self):
        """加载基线哈希值"""
        baseline_file = 'printing_logic_baseline.txt'
        if os.path.exists(baseline_file):
            try:
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    hash_match = re.search(r'哈希值: ([a-f0-9]+)', content)
                    if hash_match:
                        return hash_match.group(1)
            except Exception as e:
                print(f"⚠️ 加载基线失败: {e}")
        return None
    
    def perform_check(self):
        """执行完整的保护检查"""
        print("🔍 开始印刷标准判定逻辑保护检查...")
        print("=" * 50)
        
        # 提取当前代码
        current_code = self.extract_printing_logic()
        if not current_code:
            print("❌ 无法提取印刷标准判定逻辑代码")
            return False
        
        print(f"📄 代码长度: {len(current_code)} 字符")
        
        # 检查保护标记
        print("\n🔒 检查保护标记...")
        if not self.check_protection_markers(current_code):
            print("❌ 保护标记检查失败")
            return False
        print("✅ 保护标记完整")
        
        # 检查印刷参数
        print("\n🔧 检查印刷参数...")
        if not self.check_printing_parameters(current_code):
            print("❌ 印刷参数检查失败")
            return False
        print("✅ 印刷参数正确")
        
        # 计算当前哈希
        current_hash = self.calculate_code_hash(current_code)
        print(f"\n🔢 当前代码哈希: {current_hash}")
        
        # 加载基线哈希
        baseline_hash = self.load_baseline()
        if baseline_hash:
            print(f"📋 基线代码哈希: {baseline_hash}")
            
            if current_hash == baseline_hash:
                print("\n✅ 代码完整性验证通过 - 印刷标准判定逻辑未被修改")
                return True
            else:
                print("\n⚠️ 代码完整性验证失败 - 检测到印刷标准判定逻辑可能被修改")
                print("🔍 请检查是否有未授权的修改")
                return False
        else:
            print("\n📋 未找到基线，正在生成...")
            self.generate_baseline()
            print("✅ 基线生成完成，下次检查时将进行对比")
            return True
    
    def show_protection_status(self):
        """显示保护状态"""
        print("\n📊 印刷标准判定逻辑保护状态:")
        print("=" * 40)
        print("🔒 保护级别: 高")
        print("🛡️ 保护机制: 代码标记 + 哈希验证 + 访问控制")
        print("📋 检查项目: 保护标记、参数完整性、代码完整性")
        print("⚠️ 修改要求: 管理员授权 + 密钥验证")
        print("📝 建议: 定期运行此检查脚本以确保代码安全")

def main():
    checker = CodeProtectionChecker()
    
    print("🛡️ 印刷标准判定逻辑代码保护检查工具")
    print("=" * 50)
    
    # 执行检查
    result = checker.perform_check()
    
    # 显示保护状态
    checker.show_protection_status()
    
    if result:
        print("\n🎉 检查完成 - 系统安全")
    else:
        print("\n⚠️ 检查完成 - 发现问题，请及时处理")
    
    return result

if __name__ == '__main__':
    main()