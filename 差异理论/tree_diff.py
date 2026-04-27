# -*- coding: utf-8 -*-
"""
算法实现：差异理论 / tree_diff

本文件实现 tree_diff 相关的算法功能。
"""

import ast
import hashlib
from enum import Enum


class DiffType(Enum):
    """
    差异类型枚举
    """
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    MOVED = "moved"


class ASTNodeInfo:
    """
    AST节点信息包装类
    """
    def __init__(self, node, path=""):
        self.node = node
        self.path = path  # 节点在树中的路径
        self.node_type = type(node).__name__
        self.hash_value = self._compute_hash()
        
        # 获取节点的关键属性
        self.name = getattr(node, 'name', None)
        self.lineno = getattr(node, 'lineno', None)
        self.col_offset = getattr(node, 'col_offset', None)
        self.end_lineno = getattr(node, 'end_lineno', None)
    
    def _compute_hash(self):
        """
        计算节点的哈希值，用于快速比较
        """
        content = f"{self.node_type}:{self.lineno}:{self._get_node_key()}"
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _get_node_key(self):
        """
        获取节点的关键标识
        """
        if isinstance(self.node, ast.Name):
            return self.node.id
        elif isinstance(self.node, ast.Constant):
            return str(self.node.value)
        elif isinstance(self.node, ast.FunctionDef):
            return f"func:{self.node.name}"
        elif isinstance(self.node, ast.ClassDef):
            return f"class:{self.node.name}"
        elif isinstance(self.node, ast.Attribute):
            return self.node.attr
        else:
            return ""
    
    def __repr__(self):
        return f"ASTNodeInfo({self.node_type}, line={self.lineno}, name={self.name})"


class TreeDiffResult:
    """
    树形差异结果
    """
    def __init__(self):
        self.added = []      # 新增的节点
        self.removed = []    # 删除的节点
        self.modified = []   # 修改的节点
        self.moved = []      # 移动的节点
        self.structure_changes = []  # 结构变化


def ast_to_dict(node, path="root"):
    """
    将AST节点转换为可比较的字典格式
    
    参数:
        node: AST节点
        path: 当前路径
    
    返回:
        表示AST的字典
    """
    if node is None:
        return None
    
    result = {
        'type': type(node).__name__,
        'path': path,
        'lineno': getattr(node, 'lineno', None),
    }
    
    # 添加特定类型的属性
    if isinstance(node, ast.Name):
        result['value'] = node.id
    elif isinstance(node, ast.Constant):
        result['value'] = str(node.value)
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        result['name'] = node.name
        result['args'] = [arg.arg for arg in node.args.args]
    elif isinstance(node, ast.ClassDef):
        result['name'] = node.name
    elif isinstance(node, ast.Attribute):
        result['attr'] = node.attr
    
    # 处理子节点
    children = []
    for name, child in ast.iter_fields(node):
        if isinstance(child, list):
            for i, item in enumerate(child):
                if isinstance(item, ast.AST):
                    child_path = f"{path}.{name}[{i}]"
                    children.append(ast_to_dict(item, child_path))
        elif isinstance(child, ast.AST):
            child_path = f"{path}.{name}"
            children.append(ast_to_dict(child, child_path))
    
    if children:
        result['children'] = children
    
    return result


def compute_tree_edit_script(tree_a, tree_b):
    """
    计算两棵AST之间的编辑脚本
    
    这是一个简化版本，使用深度优先遍历和简单的差异检测
    
    参数:
        tree_a: 原始AST的字典表示
        tree_b: 新AST的字典表示
    
    返回:
        TreeDiffResult差异结果
    """
    result = TreeDiffResult()
    
    # 构建节点映射
    nodes_a = {}
    nodes_b = {}
    
    def collect_nodes(tree, node_map):
        """收集树中的所有节点"""
        if tree is None:
            return
        
        key = f"{tree['type']}:{tree.get('name', '')}:{tree.get('lineno', 0)}"
        if key not in node_map:
            node_map[key] = []
        node_map[key].append(tree)
        
        for child in tree.get('children', []):
            collect_nodes(child, node_map)
    
    collect_nodes(tree_a, nodes_a)
    collect_nodes(tree_b, nodes_b)
    
    # 检测新增
    for key in nodes_b:
        if key not in nodes_a:
            for node in nodes_b[key]:
                result.added.append(node)
    
    # 检测删除
    for key in nodes_a:
        if key not in nodes_b:
            for node in nodes_a[key]:
                result.removed.append(node)
    
    # 检测修改（相同类型但行号不同）
    for key in nodes_a:
        if key in nodes_b:
            len_a = len(nodes_a[key])
            len_b = len(nodes_b[key])
            
            if len_a != len_b:
                # 数量变化
                result.structure_changes.append({
                    'type': key,
                    'old_count': len_a,
                    'new_count': len_b
                })
    
    return result


def compare_ast(source_a, source_b):
    """
    比较两个Python源代码的AST
    
    参数:
        source_a: 原始源代码
        source_b: 新源代码
    
    返回:
        TreeDiffResult差异结果
    """
    try:
        tree_a = ast.parse(source_a)
        tree_b = ast.parse(source_b)
    except SyntaxError as e:
        return None, str(e)
    
    # 转换为可比较的格式
    dict_a = ast_to_dict(tree_a)
    dict_b = ast_to_dict(tree_b)
    
    # 计算编辑脚本
    diff_result = compute_tree_edit_script(dict_a, dict_b)
    
    return diff_result, None


def format_tree_diff(diff_result):
    """
    格式化树形差异结果
    
    参数:
        diff_result: TreeDiffResult对象
    
    返回:
        格式化的字符串
    """
    lines = []
    lines.append("=" * 60)
    lines.append("AST树形差异分析")
    lines.append("=" * 60)
    
    if diff_result.added:
        lines.append(f"\n【新增节点】({len(diff_result.added)}个)")
        for node in diff_result.added[:10]:  # 限制显示数量
            lines.append(f"  + {node['type']} at line {node.get('lineno', '?')}")
        if len(diff_result.added) > 10:
            lines.append(f"  ... 还有 {len(diff_result.added) - 10} 个")
    
    if diff_result.removed:
        lines.append(f"\n【删除节点】({len(diff_result.removed)}个)")
        for node in diff_result.removed[:10]:
            lines.append(f"  - {node['type']} at line {node.get('lineno', '?')}")
        if len(diff_result.removed) > 10:
            lines.append(f"  ... 还有 {len(diff_result.removed) - 10} 个")
    
    if diff_result.structure_changes:
        lines.append(f"\n【结构变化】")
        for change in diff_result.structure_changes:
            lines.append(f"  ~ {change['type']}: {change['old_count']} -> {change['new_count']}")
    
    if not any([diff_result.added, diff_result.removed, diff_result.structure_changes]):
        lines.append("\n未检测到结构差异")
    
    return '\n'.join(lines)


def get_node_path(node, root):
    """
    获取从根节点到指定节点的路径
    
    参数:
        node: 目标节点
        root: 根节点
    
    返回:
        路径字符串
    """
    def find_path(current, target, path):
        if current is target:
            return path
        for child in current.get('children', []):
            result = find_path(child, target, path + [child.get('name', child['type'])])
            if result:
                return result
        return None
    
    result = find_path(root, node, [root.get('type', 'root')])
    return '.'.join(result) if result else 'unknown'


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：简单函数添加
    print("=" * 50)
    print("测试1: AST检测函数添加")
    print("=" * 50)
    
    source_a = """
def hello():
    return 'hello'
"""
    source_b = """
def hello():
    return 'hello'

def goodbye():
    return 'goodbye'
"""
    
    diff, err = compare_ast(source_a, source_b)
    if err:
        print(f"解析错误: {err}")
    else:
        print(format_tree_diff(diff))
    
    # 测试用例2：函数修改
    print("\n" + "=" * 50)
    print("测试2: AST检测函数修改")
    print("=" * 50)
    
    source_a = """
def calculate(x, y):
    return x + y
"""
    source_b = """
def calculate(x, y, z=0):
    return x + y + z
"""
    
    diff, err = compare_ast(source_a, source_b)
    if err:
        print(f"解析错误: {err}")
    else:
        print(format_tree_diff(diff))
    
    # 测试用例3：类结构变化
    print("\n" + "=" * 50)
    print("测试3: AST检测类结构变化")
    print("=" * 50)
    
    source_a = """
class MyClass:
    def __init__(self):
        self.x = 1
    
    def method_a(self):
        return self.x
"""
    source_b = """
class MyClass:
    def __init__(self):
        self.x = 1
        self.y = 2
    
    def method_a(self):
        return self.x + self.y
    
    def method_b(self):
        return self.y
"""
    
    diff, err = compare_ast(source_a, source_b)
    if err:
        print(f"解析错误: {err}")
    else:
        print(format_tree_diff(diff))
    
    # 测试用例4：AST字典结构展示
    print("\n" + "=" * 50)
    print("测试4: AST结构示例")
    print("=" * 50)
    
    source = """
def example(a, b):
    return a + b
"""
    tree = ast.parse(source)
    dict_repr = ast_to_dict(tree)
    print(f"AST类型: {dict_repr['type']}")
    print(f"子节点数: {len(dict_repr.get('children', []))}")
