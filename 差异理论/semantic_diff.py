# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / semantic_diff

本文件实现 semantic_diff 相关的算法功能。
"""

import ast
import re
from collections import defaultdict


class CodeEntity:
    """
    代码实体类，表示一个代码结构元素
    """
    def __init__(self, name, entity_type, lineno, end_lineno, code, docstring=None):
        self.name = name          # 实体名称
        self.entity_type = entity_type  # 类型：function, class, method
        self.lineno = lineno      # 起始行号
        self.end_lineno = end_lineno  # 结束行号
        self.code = code          # 代码文本
        self.docstring = docstring  # 文档字符串
        self.signature = None     # 函数签名


class SemanticAnalyzer(ast.NodeVisitor):
    """
    语义分析器，遍历AST提取代码结构
    """
    
    def __init__(self):
        self.entities = []  # 存储所有代码实体
        self.current_class = None  # 当前所在的类
    
    def visit_FunctionDef(self, node):
        """
        处理函数定义
        """
        # 获取函数签名
        sig_parts = [node.name]
        for arg in node.args.args:
            sig_parts.append(arg.arg)
        
        entity = CodeEntity(
            name=node.name,
            entity_type='method' if self.current_class else 'function',
            lineno=node.lineno,
            end_lineno=node.end_lineno,
            code=ast.get_source_segment(None, node) or '',
            docstring=ast.get_docstring(node)
        )
        entity.signature = '(' + ', '.join(sig_parts) + ')'
        
        self.entities.append(entity)
        
        # 如果在类中，继续遍历
        if self.current_class is None:
            self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node):
        """
        处理异步函数定义
        """
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node):
        """
        处理类定义
        """
        old_class = self.current_class
        self.current_class = node.name
        
        entity = CodeEntity(
            name=node.name,
            entity_type='class',
            lineno=node.lineno,
            end_lineno=node.end_lineno,
            code=ast.get_source_segment(None, node) or '',
            docstring=ast.get_docstring(node)
        )
        
        self.entities.append(entity)
        self.generic_visit(node)
        self.current_class = old_class


def extract_entities(source_code):
    """
    从源代码中提取代码实体
    
    参数:
        source_code: Python源代码字符串
    
    返回:
        代码实体列表
    """
    try:
        tree = ast.parse(source_code)
        analyzer = SemanticAnalyzer()
        analyzer.visit(tree)
        return analyzer.entities
    except SyntaxError:
        return []


def compute_entity_similarity(entity_a, entity_b):
    """
    计算两个代码实体的相似度
    
    使用基于签名的简单相似度计算
    实际应用中可以使用更复杂的代码相似度算法
    
    参数:
        entity_a: 第一个代码实体
        entity_b: 第二个代码实体
    
    返回:
        0-1之间的相似度分数
    """
    if entity_a.entity_type != entity_b.entity_type:
        return 0.0
    
    # 名称相似度
    name_similarity = 0.0
    if entity_a.name == entity_b.name:
        name_similarity = 1.0
    else:
        # 使用简单的编辑距离计算名称相似度
        name_similarity = 1.0 - edit_distance(entity_a.name, entity_b.name) / max(len(entity_a.name), len(entity_b.name))
    
    # 签名相似度
    sig_similarity = 0.0
    if entity_a.signature == entity_b.signature:
        sig_similarity = 1.0
    
    return (name_similarity * 0.6 + sig_similarity * 0.4)


def edit_distance(str_a, str_b):
    """
    计算编辑距离（Levenshtein距离）
    
    参数:
        str_a: 第一个字符串
        str_b: 第二个字符串
    
    返回:
        编辑距离
    """
    n = len(str_a)
    m = len(str_b)
    
    # DP表
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    
    # 初始化边界
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    
    # 填充DP表
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if str_a[i-1] == str_b[j-1]:
                dp[i][j] = dp[i-1][j-1]
            else:
                dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
    
    return dp[n][m]


def semantic_diff(source_a, source_b):
    """
    语义级别的代码差异分析
    
    参数:
        source_a: 原始源代码
        source_b: 新源代码
    
    返回:
        差异分析结果字典
    """
    entities_a = extract_entities(source_a)
    entities_b = extract_entities(source_b)
    
    # 按类型分组
    by_type_a = defaultdict(list)
    by_type_b = defaultdict(list)
    
    for entity in entities_a:
        by_type_a[entity.entity_type].append(entity)
    for entity in entities_b:
        by_type_b[entity.entity_type].append(entity)
    
    result = {
        'added': [],      # 新增的实体
        'removed': [],    # 删除的实体
        'modified': [],   # 修改的实体
        'renamed': []     # 重命名的实体（通过相似度检测）
    }
    
    # 检测新增
    for entity_b in entities_b:
        found = False
        for entity_a in entities_a:
            if compute_entity_similarity(entity_a, entity_b) > 0.8:
                found = True
                break
        if not found:
            result['added'].append(entity_b)
    
    # 检测删除
    for entity_a in entities_a:
        found = False
        for entity_b in entities_b:
            if compute_entity_similarity(entity_a, entity_b) > 0.8:
                found = True
                break
        if not found:
            result['removed'].append(entity_a)
    
    # 检测修改和重命名
    for entity_a in entities_a:
        for entity_b in entities_b:
            similarity = compute_entity_similarity(entity_a, entity_b)
            if 0.5 < similarity <= 0.8:
                # 可能是重命名
                result['renamed'].append((entity_a, entity_b, similarity))
            elif similarity > 0.8 and entity_a.code != entity_b.code:
                # 代码被修改
                result['modified'].append((entity_a, entity_b))
    
    return result


def format_semantic_diff(diff_result):
    """
    格式化语义差异结果
    
    参数:
        diff_result: semantic_diff的返回结果
    
    返回:
        格式化的字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append("语义差异分析报告")
    lines.append("=" * 60)
    
    if diff_result['added']:
        lines.append("\n【新增】")
        for entity in diff_result['added']:
            lines.append(f"  + {entity.entity_type}: {entity.name} (行 {entity.lineno}-{entity.end_lineno})")
    
    if diff_result['removed']:
        lines.append("\n【删除】")
        for entity in diff_result['removed']:
            lines.append(f"  - {entity.entity_type}: {entity.name} (行 {entity.lineno}-{entity.end_lineno})")
    
    if diff_result['modified']:
        lines.append("\n【修改】")
        for entity_a, entity_b in diff_result['modified']:
            lines.append(f"  ~ {entity_a.entity_type}: {entity_a.name}")
            lines.append(f"    行范围: {entity_a.lineno}-{entity_a.end_lineno} -> {entity_b.lineno}-{entity_b.end_lineno}")
    
    if diff_result['renamed']:
        lines.append("\n【重命名】")
        for entity_a, entity_b, sim in diff_result['renamed']:
            lines.append(f"  > {entity_a.name} -> {entity_b.name} (相似度: {sim:.2f})")
    
    if not any(diff_result.values()):
        lines.append("\n无语义差异（代码结构未改变）")
    
    return '\n'.join(lines)


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：简单的函数添加
    print("=" * 50)
    print("测试1: 函数添加检测")
    print("=" * 50)
    
    source_a = """
def hello():
    print('hello')
"""
    source_b = """
def hello():
    print('hello')

def goodbye():
    print('goodbye')
"""
    
    result = semantic_diff(source_a, source_b)
    print(format_semantic_diff(result))
    
    # 测试用例2：函数重命名检测
    print("\n" + "=" * 50)
    print("测试2: 函数重命名检测")
    print("=" * 50)
    
    source_a = """
def old_function_name(a, b):
    return a + b
"""
    source_b = """
def new_function_name(a, b):
    return a + b
"""
    
    result = semantic_diff(source_a, source_b)
    print(format_semantic_diff(result))
    
    # 测试用例3：类方法修改
    print("\n" + "=" * 50)
    print("测试3: 类方法修改")
    print("=" * 50)
    
    source_a = """
class MyClass:
    def method_a(self, x):
        return x * 2
    
    def method_b(self):
        pass
"""
    source_b = """
class MyClass:
    def method_a(self, x):
        return x * 3
    
    def method_b(self):
        return True
"""
    
    result = semantic_diff(source_a, source_b)
    print(format_semantic_diff(result))
    
    # 测试用例4：复杂场景
    print("\n" + "=" * 50)
    print("测试4: 复杂代码差异")
    print("=" * 50)
    
    source_a = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, x):
        self.result += x
"""
    
    source_b = """
def multiply(a, b):
    return a * b

def add(a, b, c=0):
    return a + b + c

class Calculator:
    def __init__(self):
        self.result = 0
        self.history = []
    
    def add(self, x):
        self.history.append(x)
        self.result += x
"""
    
    result = semantic_diff(source_a, source_b)
    print(format_semantic_diff(result))
