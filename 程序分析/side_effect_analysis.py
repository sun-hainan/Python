# -*- coding: utf-8 -*-
"""
副作用分析（Side Effect Analysis）
功能：分析函数对全局状态和参数的修改

纯函数：没有副作用，输出只依赖输入
有副作用的函数：修改全局变量、引用参数、IO等

用途：
1. 编译器优化（纯函数可以安全重排）
2. 并行化分析
3. 引用透明性分析

作者：Side Effect Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict


class Effect:
    """副作用描述"""
    
    def __init__(self, kind: str, target: str, location: str = ""):
        self.kind = kind  # 'read', 'write', 'call', 'io'
        self.target = target  # 变量名、内存位置等
        self.location = location

    def __repr__(self):
        return f"{self.kind}({self.target})"

    def __hash__(self):
        return hash((self.kind, self.target))

    def __eq__(self, other):
        return isinstance(other, Effect) and self.kind == other.kind and self.target == other.target


class FunctionEffect:
    """函数的副作用"""
    
    def __init__(self, name: str):
        self.name = name
        self.effects: Set[Effect] = set()
        self.reads: Set[str] = set()  # 读取的变量
        self.writes: Set[str] = set()  # 写入的变量
        self.globals_read: Set[str] = set()
        self.globals_written: Set[str] = set()
        self.params_modified: Set[int] = set()  # 修改的参数索引
        self.calls: Set[str] = set()  # 调用的函数

    def add_read(self, var: str):
        self.reads.add(var)
        self.effects.add(Effect('read', var))

    def add_write(self, var: str):
        self.writes.add(var)
        self.effects.add(Effect('write', var))

    def is_pure(self) -> bool:
        """检查函数是否纯"""
        return (len(self.writes) == 0 and 
                len(self.globals_written) == 0 and
                len(self.params_modified) == 0 and
                len(self.calls) == 0)

    def __repr__(self):
        return f"{self.name}: reads={self.reads}, writes={self.writes}"


class SideEffectAnalysis:
    """
    副作用分析器
    """

    def __init__(self):
        self.function_effects: Dict[str, FunctionEffect] = {}
        self.global_vars: Set[str] = set()

    def declare_global(self, var: str):
        self.global_vars.add(var)

    def analyze_function(self, func: FunctionEffect):
        self.function_effects[func.name] = func

    def may_read(self, func_name: str, var: str) -> bool:
        """检查函数是否可能读取变量"""
        if func_name not in self.function_effects:
            return True  # 未知函数，保守估计
        
        effect = self.function_effects[func_name]
        return var in effect.reads or var in effect.globals_read

    def may_write(self, func_name: str, var: str) -> bool:
        """检查函数是否可能写入变量"""
        if func_name not in self.function_effects:
            return True  # 未知函数，保守估计
        
        effect = self.function_effects[func_name]
        return var in effect.writes or var in effect.globals_written

    def is_pure(self, func_name: str) -> bool:
        """检查函数是否纯"""
        if func_name not in self.function_effects:
            return False
        return self.function_effects[func_name].is_pure()

    def can_reorder(self, func1: str, func2: str) -> bool:
        """
        检查两个函数是否可以重排
        
        如果func1写的和func2读/写的没有交集，可以重排
        """
        if func1 not in self.function_effects or func2 not in self.function_effects:
            return False
        
        e1 = self.function_effects[func1]
        e2 = self.function_effects[func2]
        
        # e1写的 ∩ e2读/写 = ∅ 才能重排
        e1_writes = e1.writes | e1.globals_written
        e2_reads = e2.reads | e2.globals_read
        e2_writes = e2.writes | e2.globals_written
        
        return len(e1_writes & (e2_reads | e2_writes)) == 0


def example_pure_function():
    """纯函数示例"""
    analysis = SideEffectAnalysis()
    
    # 纯函数：square
    square = FunctionEffect("square")
    square.add_read('x')
    # 不写入任何东西
    
    analysis.analyze_function(square)
    
    print(f"square是纯函数: {analysis.is_pure('square')}")
    print(f"square可能写x: {analysis.may_write('square', 'x')}")


def example_impure_function():
    """有副作用函数示例"""
    analysis = SideEffectAnalysis()
    
    # 有副作用的函数：increment_global
    inc = FunctionEffect("increment_global")
    inc.add_read('counter')
    inc.add_write('counter')
    
    analysis.analyze_function(inc)
    
    print(f"increment_global是纯函数: {analysis.is_pure('increment_global')}")
    print(f"increment_global可能写counter: {analysis.may_write('increment_global', 'counter')}")


def example_reordering():
    """函数重排分析"""
    analysis = SideEffectAnalysis()
    
    # f1写a，读b
    f1 = FunctionEffect("f1")
    f1.add_write('a')
    f1.add_read('b')
    analysis.analyze_function(f1)
    
    # f2写b，读c
    f2 = FunctionEffect("f2")
    f2.add_write('b')
    f2.add_read('c')
    analysis.analyze_function(f2)
    
    # f3写c
    f3 = FunctionEffect("f3")
    f3.add_write('c')
    analysis.analyze_function(f3)
    
    print(f"f1和f2可重排: {analysis.can_reorder('f1', 'f2')}")
    print(f"f1和f3可重排: {analysis.can_reorder('f1', 'f3')}")
    print(f"f2和f3可重排: {analysis.can_reorder('f2', 'f3')}")


if __name__ == "__main__":
    print("=" * 50)
    print("副作用分析 测试")
    print("=" * 50)
    
    example_pure_function()
    print()
    example_impure_function()
    print()
    example_reordering()
