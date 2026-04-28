# -*- coding: utf-8 -*-
"""
过程间分析（Interprocedural Analysis）
功能：跨函数边界的数据流分析

问题：
1. 调用点上下文敏感 vs 不敏感
2. 函数返回值和副作用
3. 参数传递（值传递vs引用传递）

方法：
1. 调用图可达性
2. 上下文不敏感分析
3. 上下文敏感分析（克隆/合并）
4. 指针分析+过程间分析

作者：Interprocedural Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict, deque


class Function:
    """函数"""
    def __init__(self, name: str):
        self.name = name
        self.params: List[str] = []
        self.local_vars: Set[str] = set()
        self.statements: List = []
        self.calls: List[Tuple[str, List[str]]] = []  # (callee, arg_names)

    def add_call(self, callee: str, args: List[str]):
        self.calls.append((callee, args))


class CallGraph:
    """调用图"""
    def __init__(self):
        self.functions: Dict[str, Function] = {}
        self.call_edges: Dict[str, Set[str]] = defaultdict(set)  # caller → callees
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)

    def add_function(self, func: Function):
        self.functions[func.name] = func

    def add_call(self, caller: str, callee: str):
        self.call_edges[caller].add(callee)
        self.reverse_edges[callee].add(caller)


class InterproceduralAnalysis:
    """
    过程间分析框架
    """

    def __init__(self, call_graph: CallGraph):
        self.call_graph = call_graph
        # 每个函数的摘要
        self.summaries: Dict[str, Dict[str, Any]] = {}

    def compute_reachable_functions(self, entry: str) -> Set[str]:
        """计算从入口函数可达的所有函数"""
        reachable = {entry}
        worklist = deque([entry])
        
        while worklist:
            current = worklist.popleft()
            for callee in self.call_graph.call_edges.get(current, []):
                if callee not in reachable:
                    reachable.add(callee)
                    worklist.append(callee)
        
        return reachable

    def may_modify_global(self, func_name: str, var: str) -> bool:
        """检查函数是否可能修改全局变量"""
        if func_name not in self.summaries:
            return True  # 未知，保守估计
        summary = self.summaries[func_name]
        return var in summary.get('globals_written', set())

    def may_read_global(self, func_name: str, var: str) -> bool:
        """检查函数是否可能读取全局变量"""
        if func_name not in self.summaries:
            return True
        summary = self.summaries[func_name]
        return var in summary.get('globals_read', set())

    def interproc_reaching_definitions(self, entry: str) -> Dict[str, Set[str]]:
        """
        过程间到达定义分析
        
        计算每个函数入口处可能的全局定义
        """
        reachable = self.compute_reachable_functions(entry)
        in_defs: Dict[str, Set[str]] = {f: set() for f in reachable}
        
        changed = True
        while changed:
            changed = False
            for func_name in reachable:
                func = self.call_graph.functions[func_name]
                
                # 合并所有调用者的效果
                for caller in self.call_graph.reverse_edges.get(func_name, []):
                    in_defs[func_name] |= in_defs.get(caller, set())
                
                # 添加函数内定义
                local_defs = set()
                for stmt in func.statements:
                    if stmt.get('type') == 'assign':
                        lhs = stmt.get('lhs')
                        if lhs:
                            local_defs.add(lhs)
                
                new_defs = in_defs[func_name] | local_defs
                if new_defs != in_defs[func_name]:
                    in_defs[func_name] = new_defs
                    changed = True
        
        return in_defs


def example_call_graph():
    """调用图示例"""
    cg = CallGraph()
    
    main = Function("main")
    main.add_call("foo", ['x'])
    cg.add_function(main)
    
    foo = Function("foo")
    foo.add_call("bar", ['y'])
    cg.add_function(foo)
    
    bar = Function("bar")
    cg.add_function(bar)
    
    cg.add_call("main", "foo")
    cg.add_call("foo", "bar")
    
    print("调用图:")
    for caller, callees in cg.call_edges.items():
        for callee in callees:
            print(f"  {caller} → {callee}")


def example_reachable():
    """可达函数分析"""
    cg = CallGraph()
    
    cg.add_call("main", "a")
    cg.add_call("main", "b")
    cg.add_call("a", "c")
    cg.add_call("b", "c")
    cg.add_call("c", "d")
    
    analysis = InterproceduralAnalysis(cg)
    reachable = analysis.compute_reachable_functions("main")
    
    print(f"从main可达: {reachable}")


def example_interproc_definitions():
    """过程间定义分析"""
    cg = CallGraph()
    
    main = Function("main")
    main.statements = [
        {'type': 'assign', 'lhs': 'global_var', 'rhs': 10}
    ]
    cg.add_function(main)
    cg.add_call("main", "foo")
    
    foo = Function("foo")
    foo.statements = [
        {'type': 'assign', 'lhs': 'global_var', 'rhs': 20}
    ]
    cg.add_function(foo)
    
    analysis = InterproceduralAnalysis(cg)
    in_defs = analysis.interproc_reaching_definitions("main")
    
    print("过程间到达定义:")
    for func, defs in in_defs.items():
        print(f"  {func}: {defs}")


if __name__ == "__main__":
    print("=" * 50)
    print("过程间分析 测试")
    print("=" * 50)
    
    example_call_graph()
    print()
    example_reachable()
    print()
    example_interproc_definitions()
