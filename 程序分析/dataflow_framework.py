# -*- coding: utf-8 -*-
"""
数据流分析框架
功能：一般化的数据流分析引擎，支持前向/后向、may/must分析

数据流分析核心概念：
- 语义域（Semantic Domain）：值的表示
- 转换函数（Transfer Function）：语句对状态的影响
- 控制流合并（Control Flow Merge）：分支汇合时的值合并

框架组件：
1. Direction：前向(Forward)或后向(Backward)
2. Lattice：半格，定义值的抽象域
3. Transfer：转换函数
4. Meet Operator (∧)：合并操作

作者：Dataflow Framework Team
"""

from typing import List, Dict, Set, Tuple, Optional, Callable, Any
from abc import ABC, abstractmethod
from collections import deque


class Lattice(ABC):
    """格的抽象基类"""
    
    @abstractmethod
    def lub(self, other: 'Lattice') -> 'Lattice':
        """最小上界（Least Upper Bound）/ Join"""
        pass
    
    @abstractmethod
    def glb(self, other: 'Lattice') -> 'Lattice':
        """最大下界（Greatest Lower Bound）/ Meet"""
        pass
    
    @abstractmethod
    def eq(self, other: 'Lattice') -> bool:
        """相等比较"""
        pass
    
    @abstractmethod
    def le(self, other: 'Lattice') -> bool:
        """偏序比较"""
        pass


class PowerSetLattice(Lattice):
    """幂集格：值的集合"""
    
    def __init__(self, elements: Set = None):
        self.elements = elements or set()
    
    def lub(self, other: 'Lattice') -> 'PowerSetLattice':
        if isinstance(other, PowerSetLattice):
            return PowerSetLattice(self.elements | other.elements)
        return self
    
    def glb(self, other: 'Lattice') -> 'PowerSetLattice':
        if isinstance(other, PowerSetLattice):
            return PowerSetLattice(self.elements & other.elements)
        return self
    
    def eq(self, other: 'Lattice') -> bool:
        if isinstance(other, PowerSetLattice):
            return self.elements == other.elements
        return False
    
    def le(self, other: 'Lattice') -> bool:
        if isinstance(other, PowerSetLattice):
            return self.elements <= other.elements
        return False
    
    def __repr__(self):
        return f"{{{', '.join(str(e) for e in self.elements)}}}"
    
    def __hash__(self):
        return hash(frozenset(self.elements))


class SignLattice(Lattice):
    """
    符号格：表示数值的符号
        ⊤ (top) - 未知
       / | \
     neg 0 pos
       \ | /
        ⊥ (bottom) - 矛盾
    """
    
    TOP = -2
    NEG = -1
    ZERO = 0
    POS = 1
    BOTTOM = 2
    
    def __init__(self, sign: int = TOP):
        self.sign = sign
    
    def lub(self, other: 'SignLattice') -> 'SignLattice':
        if not isinstance(other, SignLattice):
            return self
        s1, s2 = self.sign, other.sign
        
        if s1 == SignLattice.BOTTOM or s2 == SignLattice.BOTTOM:
            return SignLattice(SignLattice.BOTTOM)
        if s1 == SignLattice.TOP or s2 == SignLattice.TOP:
            return SignLattice(SignLattice.TOP)
        if s1 == s2:
            return SignLattice(s1)
        # 不同符号合并为TOP
        return SignLattice(SignLattice.TOP)
    
    def glb(self, other: 'SignLattice') -> 'SignLattice':
        if not isinstance(other, SignLattice):
            return self
        s1, s2 = self.sign, other.sign
        
        if s1 == SignLattice.TOP:
            return SignLattice(s2)
        if s2 == SignLattice.TOP:
            return SignLattice(s1)
        if s1 == s2:
            return SignLattice(s1)
        # 不同符号相遇 → 矛盾
        return SignLattice(SignLattice.BOTTOM)
    
    def eq(self, other: 'Lattice') -> bool:
        if isinstance(other, SignLattice):
            return self.sign == other.sign
        return False
    
    def le(self, other: 'Lattice') -> bool:
        if isinstance(other, SignLattice):
            return self.sign == other.sign or self.sign == SignLattice.BOTTOM
        return False
    
    def __repr__(self):
        names = {-2: '⊤', -1: '-', 0: '0', 1: '+', 2: '⊥'}
        return names.get(self.sign, '?')


class CFGNode:
    """控制流图节点"""
    def __init__(self, node_id: str, stmt: Any = None):
        self.id = node_id
        self.stmt = stmt
        self.preds: List['CFGNode'] = []
        self.succs: List['CFGNode'] = []


class DataflowFramework:
    """
    数据流分析框架
    
    支持一般化的前向/后向分析
    """

    def __init__(self, cfg: Dict[str, CFGNode], 
                 direction: str = 'forward',
                 lattice_factory: Callable = None):
        """
        Args:
            cfg: 控制流图 {node_id: CFGNode}
            direction: 'forward' 或 'backward'
            lattice_factory: 创建初始格值的函数
        """
        self.cfg = cfg
        self.direction = direction
        self.lattice_factory = lattice_factory
        # IN[node_id] = lattice value
        self.in_state: Dict[str, Any] = {}
        self.out_state: Dict[str, Any] = {}
        self.worklist: deque = deque()

    def analyze(self, entry_id: str, 
                transfer_fn: Callable[[CFGNode, Any], Any],
                meet_fn: Callable[[List[Any]], Any]) -> Dict[str, Any]:
        """
        执行数据流分析
        
        Args:
            entry_id: 入口节点ID
            transfer_fn: 转换函数 (node, in_value) → out_value
            meet_fn: 合并函数 (list of values) → merged_value
            
        Returns:
            每个节点的OUT状态
        """
        # 初始化
        for node_id in self.cfg:
            self.in_state[node_id] = None
            self.out_state[node_id] = None
        
        # 入口节点初始化
        if self.direction == 'forward':
            self.in_state[entry_id] = self.lattice_factory()
            self.worklist.append(entry_id)
        else:
            # 后向分析：出口节点初始化
            self.out_state[entry_id] = self.lattice_factory()
            self.worklist.append(entry_id)
        
        # Worklist迭代
        while self.worklist:
            node_id = self.worklist.popleft()
            node = self.cfg[node_id]
            
            if self.direction == 'forward':
                # 合并所有前驱的OUT
                if node.preds:
                    pred_outs = [self.out_state[p.id] for p in node.preds 
                                if self.out_state.get(p.id) is not None]
                    if pred_outs:
                        self.in_state[node_id] = meet_fn(pred_outs)
                
                # 应用转换
                new_out = transfer_fn(node, self.in_state[node_id])
                
                if new_out != self.out_state.get(node_id):
                    self.out_state[node_id] = new_out
                    for succ in node.succs:
                        self.worklist.append(succ.id)
            else:
                # 后向：合并所有后继的IN
                if node.succs:
                    succ_ins = [self.in_state[s.id] for s in node.succs
                                if self.in_state.get(s.id) is not None]
                    if succ_ins:
                        self.out_state[node_id] = meet_fn(succ_ins)
                
                # 应用转换
                new_in = transfer_fn(node, self.out_state[node_id])
                
                if new_in != self.in_state.get(node_id):
                    self.in_state[node_id] = new_in
                    for pred in node.preds:
                        self.worklist.append(pred.id)
        
        return self.out_state


def example_sign_analysis():
    """符号分析示例"""
    # 创建格工厂
    def sign_lattice_factory():
        return SignLattice(SignLattice.TOP)
    
    # 创建CFG
    nodes = {
        'entry': CFGNode('entry'),
        'x_gt_0': CFGNode('x_gt_0', {'type': 'if', 'cond': 'x > 0'}),
        'then': CFGNode('then', {'type': 'assign', 'var': 's', 'val': '+'}),
        'else': CFGNode('else', {'type': 'assign', 'var': 's', 'val': '-'}),
        'join': CFGNode('join'),
    }
    
    # 设置边
    nodes['entry'].succs = [nodes['x_gt_0']]
    nodes['x_gt_0'].preds = [nodes['entry']]
    nodes['x_gt_0'].succs = [nodes['then'], nodes['else']]
    nodes['then'].preds = [nodes['x_gt_0']]
    nodes['then'].succs = [nodes['join']]
    nodes['else'].preds = [nodes['x_gt_0']]
    nodes['else'].succs = [nodes['join']]
    nodes['join'].preds = [nodes['then'], nodes['else']]
    
    # 转换函数
    def transfer(node: CFGNode, in_val):
        if in_val is None:
            return SignLattice(SignLattice.TOP)
        
        if node.stmt and node.stmt.get('type') == 'assign':
            return SignLattice(SignLattice.POS if node.stmt.get('val') == '+' else SignLattice.NEG)
        
        return in_val
    
    # 合并函数（join合并）
    def meet_fn(values):
        result = values[0]
        for v in values[1:]:
            result = result.lub(v)
        return result
    
    framework = DataflowFramework(nodes, direction='forward', 
                                  lattice_factory=sign_lattice_factory)
    framework.analyze('entry', transfer, meet_fn)
    
    print("符号分析结果:")
    for node_id in ['entry', 'x_gt_0', 'then', 'else', 'join']:
        out = framework.out_state.get(node_id)
        print(f"  {node_id}: OUT = {out}")


def example_reaching_definitions():
    """到达定义分析"""
    # 简化版：使用幂集格
    def set_factory():
        return PowerSetLattice(set())
    
    nodes = {
        'd1': CFGNode('d1', {'type': 'def', 'var': 'x'}),
        'd2': CFGNode('d2', {'type': 'def', 'var': 'y'}),
        'use': CFGNode('use', {'type': 'use', 'var': 'x'}),
    }
    
    nodes['d1'].succs = [nodes['d2']]
    nodes['d2'].preds = [nodes['d1']]
    nodes['d2'].succs = [nodes['use']]
    nodes['use'].preds = [nodes['d2']]
    
    def transfer(node: CFGNode, in_val: PowerSetLattice):
        if node.stmt.get('type') == 'def':
            return PowerSetLattice(in_val.elements | {node.stmt['var']})
        return in_val
    
    def meet_fn(values):
        result = values[0]
        for v in values[1:]:
            result = result.lub(v)
        return result
    
    framework = DataflowFramework(nodes, 'forward', set_factory)
    framework.analyze('d1', transfer, meet_fn)
    
    print("\n到达定义分析:")
    for node_id, out in framework.out_state.items():
        print(f"  {node_id}: {out}")


if __name__ == "__main__":
    print("=" * 50)
    print("数据流分析框架 测试")
    print("=" * 50)
    
    example_sign_analysis()
    print()
    example_reaching_definitions()
