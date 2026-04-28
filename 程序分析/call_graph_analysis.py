# -*- coding: utf-8 -*-
"""
调用图分析（Call Graph Analysis）
功能：构建程序的过程间调用图

调用图：节点是函数，边表示调用关系

构建方法：
1. Class Hierarchy Analysis (CHA)：基于类层次结构的快速分析
2. Rapid Type Analysis (RTA)：结合类信息的分析
3. Flow-Sensitive Analysis：流敏感的上下文敏感分析

作者：Call Graph Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class Function:
    """函数节点"""
    def __init__(self, name: str, class_name: str = None, signature: str = None):
        self.name = name
        self.class_name = class_name  # 对于OOP方法
        self.signature = signature  # 方法签名
        self.params: List[str] = []
        self.body: List = []
        self.calls: List[str] = []  # 直接调用的函数

    def full_name(self) -> str:
        if self.class_name:
            return f"{self.class_name}::{self.name}"
        return self.name

    def __repr__(self):
        return self.full_name()


class CallGraph:
    """调用图"""
    
    def __init__(self):
        self.functions: Dict[str, Function] = {}  # name → Function
        # 调用边: caller → set of callee
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        # 反向边: callee → set of caller
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)

    def add_function(self, func: Function):
        self.functions[func.full_name()] = func

    def add_call(self, caller: str, callee: str):
        self.edges[caller].add(callee)
        self.reverse_edges[callee].add(caller)

    def get_callees(self, func: str) -> Set[str]:
        return self.edges.get(func, set())

    def get_callers(self, func: str) -> Set[str]:
        return self.reverse_edges.get(func, set())

    def get_entry_points(self) -> Set[str]:
        """获取入口函数（没有被调用的函数）"""
        return {f for f in self.functions if not self.reverse_edges.get(f)}


class ClassHierarchyAnalysis:
    """
    Class Hierarchy Analysis (CHA)
    
    快速但保守的调用图构建算法
    
    规则：
    1. 直接调用：c.f(...) → 解析c的类型T，调用T及T的祖先中的所有f
    2. 虚调用：动态分派
    3. 静态调用：直接解析
    """

    def __init__(self):
        self.class_hierarchy: Dict[str, Set[str]] = defaultdict(set)
        # method_table[class] = {method_name → target_methods}
        self.method_table: Dict[str, Dict[str, Set[str]]]] = defaultdict(dict)

    def add_class(self, class_name: str, parent: str = None):
        """添加类到层次结构"""
        if parent:
            self.class_hierarchy[class_name].add(parent)
        else:
            self.class_hierarchy[class_name] = set()

    def add_method(self, class_name: str, method_name: str, 
                   targets: Set[str] = None):
        """添加方法到方法表"""
        if targets is None:
            targets = {f"{class_name}::{method_name}"}
        self.method_table[class_name][method_name] = targets

    def resolve_virtual_call(self, class_type: str, method_name: str) -> Set[str]:
        """
        解析虚调用
        
        规则：调用class_type及其所有祖先类中的method_name
        """
        result = set()
        to_visit = [class_type]
        visited = set()
        
        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue
            visited.add(current)
            
            # 获取当前类的方法
            if method_name in self.method_table.get(current, {}):
                result |= self.method_table[current][method_name]
            
            # 访问父类
            for parent in self.class_hierarchy.get(current, []):
                if parent not in visited:
                    to_visit.append(parent)
        
        return result

    def build_call_graph(self, program: List[Dict]) -> CallGraph:
        """
        构建调用图
        
        Args:
            program: 程序语句列表
        """
        call_graph = CallGraph()
        
        for stmt in program:
            if stmt['type'] == 'function':
                func = Function(stmt['name'], stmt.get('class'))
                call_graph.add_function(func)
            
            elif stmt['type'] == 'call':
                caller = stmt.get('caller', 'unknown')
                callee = stmt.get('callee')
                
                if stmt.get('is_virtual'):
                    # 虚调用：解析所有可能的接收者
                    receiver_type = stmt.get('receiver_type', 'Object')
                    targets = self.resolve_virtual_call(receiver_type, callee)
                    for target in targets:
                        call_graph.add_call(caller, target)
                else:
                    # 静态调用
                    call_graph.add_call(caller, callee)
        
        return call_graph


def build_simple_call_graph():
    """构建简单调用图示例"""
    # 模拟OOP程序
    class_hierarchy = {
        'Object': set(),
        'Animal': {'Object'},
        'Dog': {'Animal'},
        'Cat': {'Animal'},
    }
    
    cha = ClassHierarchyAnalysis()
    for cls, parents in class_hierarchy.items():
        for parent in parents:
            cha.add_class(cls, parent)
    
    # 添加方法
    cha.add_method('Animal', 'speak', {'Animal::speak'})
    cha.add_method('Dog', 'speak', {'Dog::speak'})
    cha.add_method('Cat', 'speak', {'Cat::speak'})
    
    # 解析虚调用
    targets = cha.resolve_virtual_call('Dog', 'speak')
    print(f"Dog.speak 可能的实现: {targets}")
    
    targets = cha.resolve_virtual_call('Animal', 'speak')
    print(f"Animal.speak 可能的实现: {targets}")


def example_call_graph():
    """调用图构建示例"""
    # 程序
    program = [
        {'type': 'function', 'name': 'main', 'class': None},
        {'type': 'function', 'name': 'foo', 'class': None},
        {'type': 'function', 'name': 'bar', 'class': None},
        {'type': 'call', 'caller': 'main', 'callee': 'foo', 'is_virtual': False},
        {'type': 'call', 'caller': 'main', 'callee': 'bar', 'is_virtual': False},
        {'type': 'call', 'caller': 'foo', 'callee': 'bar', 'is_virtual': False},
    ]
    
    cha = ClassHierarchyAnalysis()
    call_graph = cha.build_call_graph(program)
    
    print("调用图:")
    print(f"  函数: {list(call_graph.functions.keys())}")
    print(f"  入口点: {call_graph.get_entry_points()}")
    
    print(f"  调用关系:")
    for caller, callees in call_graph.edges.items():
        for callee in callees:
            print(f"    {caller} → {callee}")


def example_virtual_call():
    """虚调用解析示例"""
    cha = ClassHierarchyAnalysis()
    
    # Animal → Dog, Cat
    cha.add_class('Animal')
    cha.add_class('Dog', 'Animal')
    cha.add_class('Cat', 'Animal')
    
    # speak方法
    cha.add_method('Animal', 'speak', {'Animal::speak'})
    cha.add_method('Dog', 'speak', {'Dog::speak'})
    cha.add_method('Cat', 'speak', {'Cat::speak'})
    
    # 代码: Animal a = new Dog(); a.speak();
    # a的类型静态分析为Animal
    targets = cha.resolve_virtual_call('Animal', 'speak')
    print(f"Animal类型对象的speak调用目标: {targets}")


if __name__ == "__main__":
    print("=" * 50)
    print("调用图分析 测试")
    print("=" * 50)
    
    example_call_graph()
    print()
    example_virtual_call()
    print()
    build_simple_call_graph()
