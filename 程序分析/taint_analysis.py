# -*- coding: utf-8 -*-
"""
污点分析（Taint Analysis）
功能：追踪不可信数据（taint）在程序中的传播

核心概念：
- Source（污点源）：用户输入、网络数据等不可信数据
- Sink（污点汇）：危险操作（SQL执行、系统调用等）
- Taint传播：数据流经污点源后被标记为污点

应用：
1. 安全漏洞检测（SQL注入、XSS等）
2. 隐私数据泄露检测
3. 敏感信息追踪

作者：Taint Analysis Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class TaintDomain:
    """污点域"""
    
    CLEAN = 0      # 干净数据
    TAINTED = 1   # 污点数据
    SANITIZED = 2  # 已消毒数据


class TaintValue:
    """带污点标记的值"""
    
    def __init__(self, value, taint_level: int = TaintDomain.CLEAN):
        self.value = value
        self.taint_level = taint_level
    
    def __repr__(self):
        taint_mark = "🔴" if self.taint_level == TaintDomain.TAINTED else "🟢"
        return f"{taint_mark}{self.value}"
    
    @staticmethod
    def merge(t1: 'TaintValue', t2: 'TaintValue') -> 'TaintValue':
        """合并两个污点值（悲观估计）"""
        result_taint = max(t1.taint_level, t2.taint_level)
        return TaintValue(None, result_taint)


class TaintAnalysis:
    """
    污点分析器
    
    使用流敏感的污点追踪
    """

    def __init__(self):
        # 每个变量的污点状态
        self.var_taint: Dict[str, int] = defaultdict(int)
        # 发现的污点漏洞
        self.vulnerabilities: List[Tuple[str, str, str]] = []  # (source_var, sink_func, location)
        # 污染源列表
        self.sources: Set[str] = {'read', 'input', 'getenv', 'recv', 'socket_read'}
        # 危险汇函数列表
        self.sinks: Set[str] = {'exec', 'system', 'eval', 'sql_query', 'execute', 'printf'}

    def set_source(self, var: str):
        """将变量标记为污点源"""
        self.var_taint[var] = TaintDomain.TAINTED

    def set_sanitizer(self, var: str):
        """将变量标记为已消毒"""
        self.var_taint[var] = TaintDomain.SANITIZED

    def check_sink(self, func_name: str, args: List[str], location: str = ""):
        """检查危险函数调用是否使用污点参数"""
        for arg in args:
            if self.var_taint.get(arg, TaintDomain.CLEAN) == TaintDomain.TAINTED:
                self.vulnerabilities.append((arg, func_name, location))

    def handle_assignment(self, lhs: str, rhs: 'TaintValue'):
        """处理赋值语句"""
        self.var_taint[lhs] = rhs.taint_level

    def handle_call(self, lhs: str, func_name: str, args: List[str]):
        """处理函数调用"""
        if func_name in self.sources:
            # 从source获取值：污点
            self.var_taint[lhs] = TaintDomain.TAINTED
        else:
            # 一般函数调用：参数决定返回值污点
            max_taint = max(self.var_taint.get(a, TaintDomain.CLEAN) for a in args)
            self.var_taint[lhs] = max_taint
        
        # 检查sink
        if func_name in self.sinks:
            self.check_sink(func_name, args)

    def is_tainted(self, var: str) -> bool:
        """检查变量是否被污染"""
        return self.var_taint.get(var, TaintDomain.CLEAN) == TaintDomain.TAINTED

    def get_taint_status(self, var: str) -> str:
        """获取污点状态字符串"""
        status = self.var_taint.get(var, TaintDomain.CLEAN)
        if status == TaintDomain.CLEAN:
            return "clean"
        if status == TaintDomain.TAINTED:
            return "tainted"
        if status == TaintDomain.SANITIZED:
            return "sanitized"
        return "unknown"


class TaintAnalysisFramework:
    """
    数据流框架形式的污点分析
    
    支持前向和后向分析
    """

    def __init__(self, sources: Set[str], sinks: Set[str]):
        self.sources = sources
        self.sinks = sinks
        self.var_taint: Dict[str, Set[int]] = defaultdict(set)

    def transfer(self, stmt: Dict, in_state: Dict[str, Set[int]]) -> Dict[str, Set[int]]:
        """
        转换函数
        
        Args:
            stmt: 语句信息
            in_state: 输入状态
            
        Returns:
            输出状态
        """
        out_state = dict(in_state)
        stmt_type = stmt.get('type')
        
        if stmt_type == 'assignment':
            lhs = stmt['lhs']
            rhs_expr = stmt['rhs']
            
            # 污点传播：expr的污点传播到lhs
            taint_set = self._compute_taint(rhs_expr, in_state)
            out_state[lhs] = taint_set
        
        elif stmt_type == 'call':
            func = stmt['func']
            args = stmt['args']
            lhs = stmt.get('lhs')
            
            if func in self.sources:
                # Source产生污点
                out_state[func] = {TaintDomain.TAINTED}
            
            if lhs:
                # 返回值从参数继承污点
                arg_taint: Set[int] = set()
                for arg in args:
                    arg_taint |= in_state.get(arg, set())
                out_state[lhs] = arg_taint
        
        return out_state

    def _compute_taint(self, expr: any, state: Dict[str, Set[int]]) -> Set[int]:
        """计算表达式的污点集合"""
        taint: Set[int] = set()
        
        if isinstance(expr, str):
            return state.get(expr, set())
        
        if isinstance(expr, (int, float, str)) and not isinstance(expr, str):
            return set()
        
        if isinstance(expr, dict):
            op = expr.get('op')
            args = expr.get('args', [])
            
            for arg in args:
                taint |= self._compute_taint(arg, state)
        
        return taint


def example_basic_taint():
    """基本污点分析"""
    analyzer = TaintAnalysis()
    
    # x = input()  → x是污点源
    analyzer.handle_assignment('x', TaintValue(0, TaintDomain.TAINTED))
    
    # y = x  → y被污染
    analyzer.handle_assignment('y', TaintValue(0, TaintDomain.TAINTED))
    
    # z = sanitize(x)  → z被消毒
    analyzer.handle_assignment('z', TaintValue(0, TaintDomain.SANITIZED))
    
    print("污点状态:")
    for var in ['x', 'y', 'z']:
        print(f"  {var}: {analyzer.get_taint_status(var)}")


def example_sink_check():
    """Sink检查示例"""
    analyzer = TaintAnalysis()
    
    # 用户输入
    user_input = TaintValue(0, TaintDomain.TAINTED)
    analyzer.handle_assignment('data', user_input)
    
    # 直接执行（危险！）
    analyzer.check_sink('system', ['data'], location="line 5")
    
    print("\n发现的漏洞:")
    for source, sink, loc in analyzer.vulnerabilities:
        print(f"  ⚠️  变量'{source}' (污点) → {sink}() @ {loc}")


def example_dataflow_framework():
    """数据流框架示例"""
    sources = {'read', 'input'}
    sinks = {'exec', 'system'}
    
    framework = TaintAnalysisFramework(sources, sinks)
    
    # 模拟语句
    stmts = [
        {'type': 'assignment', 'lhs': 'x', 'rhs': {'op': 'call', 'func': 'read', 'args': []}},
        {'type': 'assignment', 'lhs': 'y', 'rhs': 'x'},
        {'type': 'call', 'func': 'system', 'args': ['y'], 'lhs': None},
    ]
    
    state: Dict[str, Set[int]] = {}
    for stmt in stmts:
        state = framework.transfer(stmt, state)
        print(f"After {stmt}: {dict(state)}")


if __name__ == "__main__":
    print("=" * 50)
    print("污点分析 测试")
    print("=" * 50)
    
    example_basic_taint()
    print()
    example_sink_check()
    print()
    example_dataflow_framework()
