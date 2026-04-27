# -*- coding: utf-8 -*-
"""
算法实现：编译器优化 / dataflow_framework

本文件实现 dataflow_framework 相关的算法功能。
"""

from typing import List, Dict, Set, Tuple, Optional, Callable
from collections import defaultdict
from abc import ABC, abstractmethod


class DataFlowAnalysis(ABC):
    """数据流分析基类"""
    
    @abstractmethod
    def transfer(self, state, node) -> state:
        """转移函数"""
        pass
    
    @abstractmethod
    def meet(self, states) -> state:
        """交汇运算"""
        pass
    
    def analyze(self, cfg, entry_state, fixpoint_threshold=100):
        """执行数据流分析"""
        pass


class LatticeElement:
    """格元素"""
    def __init__(self, value):
        self.value = value
    
    def __le__(self, other):
        return self.value <= other.value
    
    def __ge__(self, other):
        return self.value >= other.value
    
    def __eq__(self, other):
        return self.value == other.value


class ReachingDefinitionsAnalysis(DataFlowAnalysis):
    """
    到达定义分析
    找出哪些定义可以到达每个程序点
    """
    
    def __init__(self):
        self.gen = {}  # 产生的定义
        self.kill = {}  # 杀死的定义
    
    def transfer(self, in_state: Set[Tuple], stmt) -> Set[Tuple]:
        """转移函数: out = (in - kill) U gen"""
        out = in_state.copy()
        
        if hasattr(stmt, 'lhs'):
            var = stmt.lhs
            # 杀死该变量的旧定义
            out = {(v, loc) for v, loc in out if v != var}
            # 添加新定义
            out.add((var, id(stmt)))
        
        return out
    
    def meet(self, states: List[Set]) -> Set:
        """交汇运算: union"""
        if not states:
            return set()
        result = states[0].copy()
        for s in states[1:]:
            result |= s
        return result


class AvailableExpressionsAnalysis(DataFlowAnalysis):
    """
    可用表达式分析
    找出哪些表达式在每个程序点一定被计算且值不变
    """
    
    def __init__(self):
        self.gen = {}
        self.kill = {}
    
    def transfer(self, in_state: Set[str], stmt) -> Set[str]:
        """out = (in - kill) U gen"""
        out = in_state.copy()
        
        if hasattr(stmt, 'op'):
            # 表达式 e = x op y
            expr = f"{stmt.lhs}{stmt.op}{stmt.rhs1}" if hasattr(stmt, 'rhs1') else str(stmt)
            
            # 杀死涉及x的定义产生的表达式
            if hasattr(stmt, 'lhs'):
                out = {e for e in out if stmt.lhs not in e}
                out.add(expr)
        
        return out
    
    def meet(self, states: List[Set]) -> Set:
        """交汇运算: intersection"""
        if not states:
            return set()
        result = states[0].copy()
        for s in states[1:]:
            result &= s
        return result


class VeryBusyExpressionsAnalysis(DataFlowAnalysis):
    """
    非常忙表达式分析
    找出在每个程序点之后一定还会使用的表达式
    """
    
    def transfer(self, in_state: Set[str], stmt) -> Set[str]:
        """in = out - uses(stmt) U gen(stmt)"""
        out = in_state.copy()
        
        # 移除在语句中使用的表达式
        if hasattr(stmt, 'uses'):
            for var in stmt.uses():
                out = {e for e in out if var not in e}
        
        return out
    
    def meet(self, states: List[Set]) -> Set:
        """交汇运算: union"""
        if not states:
            return set()
        result = states[0].copy()
        for s in states[1:]:
            result |= s
        return result


class ControlFlowGraph:
    """控制流图"""
    
    def __init__(self):
        self.blocks = []
        self.edges = defaultdict(list)
    
    def add_block(self, block_id, stmts):
        self.blocks.append({'id': block_id, 'stmts': stmts})
    
    def add_edge(self, from_id, to_id):
        self.edges[from_id].append(to_id)


def worklist_algorithm(analysis: DataFlowAnalysis, cfg: ControlFlowGraph,
                      direction: str = 'forward') -> Dict:
    """
    工作表算法
    
    Args:
        analysis: 数据流分析实例
        cfg: 控制流图
        direction: 'forward' 或 'backward'
    
    Returns:
        每个块的输入/输出状态
    """
    # 初始化
    if direction == 'forward':
        in_state = set()  # 初始输入为空(BOT)
        result = {block['id']: {'in': set(), 'out': set()} for block in cfg.blocks}
    else:
        in_state = set()  # 假设全集
        result = {block['id']: {'in': set(), 'out': set()} for block in cfg.blocks}
    
    worklist = list(range(len(cfg.blocks)))
    
    while worklist:
        block_id = worklist.pop(0)
        block = cfg.blocks[block_id]
        
        # 获取前驱/后继的输出/输入状态
        if direction == 'forward':
            pred_states = []
            for pred in range(len(cfg.blocks)):
                if block_id in cfg.edges.get(pred, []):
                    pred_states.append(result[pred]['out'])
            
            if pred_states:
                in_state = analysis.meet(pred_states)
            else:
                in_state = set()
            
            # 应用转移函数
            current_in = in_state
            for stmt in block['stmts']:
                current_in = analysis.transfer(current_in, stmt)
            
            new_out = current_in
        else:
            succ_states = [result[succ]['in'] for succ in cfg.edges.get(block_id, [])]
            
            if succ_states:
                out_state = analysis.meet(succ_states)
            else:
                out_state = set()
            
            # 反向应用转移函数
            current_out = out_state
            for stmt in reversed(block['stmts']):
                current_out = analysis.transfer_backward(current_out, stmt)
            
            new_in = current_out
        
        # 更新结果
        if direction == 'forward':
            if new_out != result[block_id]['out']:
                result[block_id]['in'] = in_state
                result[block_id]['out'] = new_out
                # 将后继加入工作表
                for succ in cfg.edges.get(block_id, []):
                    if succ not in worklist:
                        worklist.append(succ)
        else:
            if new_in != result[block_id]['in']:
                result[block_id]['in'] = new_in
                result[block_id]['out'] = out_state
                # 将前驱加入工作表
                for pred in range(len(cfg.blocks)):
                    if block_id in cfg.edges.get(pred, []):
                        if pred not in worklist:
                            worklist.append(pred)
    
    return result


# 测试代码
if __name__ == "__main__":
    # 测试1: 到达定义分析
    print("测试1 - 到达定义分析:")
    
    cfg = ControlFlowGraph()
    
    class Stmt:
        def __init__(self, lhs):
            self.lhs = lhs
    
    # Block 0: x = 1
    # Block 1: y = x + 1
    # Block 2: x = y + 1
    cfg.add_block(0, [Stmt('x')])
    cfg.add_block(1, [Stmt('y')])
    cfg.add_block(2, [Stmt('x')])
    
    cfg.add_edge(0, 1)
    cfg.add_edge(1, 2)
    cfg.add_edge(2, 1)  # 循环
    
    analysis = ReachingDefinitionsAnalysis()
    result = worklist_algorithm(analysis, cfg, direction='forward')
    
    print("  到达定义分析结果:")
    for block_id, state in result.items():
        print(f"    Block{block_id}: in={len(state['in'])}, out={len(state['out'])}")
    
    # 测试2: 可用表达式分析
    print("\n测试2 - 可用表达式分析:")
    
    cfg2 = ControlFlowGraph()
    
    class ExprStmt:
        def __init__(self, lhs, op, rhs):
            self.lhs = lhs
            self.op = op
            self.rhs1 = rhs
    
    # x = a + b
    # y = x + c
    # z = x + y
    cfg2.add_block(0, [ExprStmt('x', '+', 'a+b')])
    cfg2.add_block(1, [ExprStmt('y', '+', 'x+c')])
    cfg2.add_block(2, [ExprStmt('z', '+', 'x+y')])
    
    cfg2.add_edge(0, 1)
    cfg2.add_edge(1, 2)
    cfg2.add_edge(2, 1)
    
    analysis2 = AvailableExpressionsAnalysis()
    result2 = worklist_algorithm(analysis2, cfg2, direction='forward')
    
    print("  可用表达式分析结果:")
    for block_id, state in result2.items():
        print(f"    Block{block_id}: in={state['in']}, out={state['out']}")
    
    print("\n所有测试完成!")
