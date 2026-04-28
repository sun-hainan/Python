# -*- coding: utf-8 -*-
"""
程序切片（Program Slicing）
功能：提取与特定计算结果相关的程序语句

程序切片：给定程序点p和变量v，所有影响p点v值的语句集合

类型：
1. 前向切片：从变量定义向所有使用它的地方传播
2. 后向切片：找所有影响变量v的程序点

方法：
1. 依赖图（Dependence Graph）
2. 数据流分析
3. 符号执行

作者：Program Slicing Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class Statement:
    """语句节点"""
    def __init__(self, sid: int, stmt_type: str, **kwargs):
        self.id = sid
        self.type = stmt_type
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __repr__(self):
        return f"S{self.id}({self.type})"


class DependenceGraph:
    """
    程序依赖图（PDG）
    
    包含：
    - 控制依赖：语句的执行依赖于条件
    - 数据依赖：语句使用了先前定义的变量
    """

    def __init__(self):
        self.nodes: List[Statement] = []
        # 边: (src, dst)
        self.control_deps: Set[Tuple[int, int]] = set()
        self.data_deps: Set[Tuple[int, int]] = set()
        # 反向索引
        self.def_to_uses: Dict[Tuple[int, str], List[int]] = defaultdict(list)
        self.use_to_defs: Dict[Tuple[int, str], List[int]] = defaultdict(list)

    def add_statement(self, stmt: Statement):
        self.nodes.append(stmt)

    def add_data_dep(self, src_id: int, dst_id: int, var: str):
        """添加数据依赖边 src → dst (关于var)"""
        self.data_deps.add((src_id, dst_id))
        self.use_to_defs[(dst_id, var)].append(src_id)
        self.def_to_uses[(src_id, var)].append(dst_id)

    def add_control_dep(self, src_id: int, dst_id: int):
        """添加控制依赖边"""
        self.control_deps.add((src_id, dst_id))


class ProgramSlicer:
    """
    程序切片器
    
    使用后向可达性计算切片
    """

    def __init__(self, pdg: DependenceGraph):
        self.pdg = pdg

    def compute_backward_slice(self, criterion: Tuple[int, str]) -> Set[int]:
        """
        计算后向切片
        
        Args:
            criterion: (statement_id, variable_name)
            
        Returns:
            影响该变量的所有语句ID集合
        """
        start_stmt, var = criterion
        slice_set = {start_stmt}
        worklist = deque([start_stmt])
        
        while worklist:
            current = worklist.popleft()
            
            # 找所有数据依赖：定义→当前语句的边
            # 即：哪些语句的定义影响了当前
            for pred in self._get_data_pred(current, var):
                if pred not in slice_set:
                    slice_set.add(pred)
                    worklist.append(pred)
            
            # 控制依赖前驱
            for ctrl_pred in self._get_control_pred(current):
                if ctrl_pred not in slice_set:
                    slice_set.add(ctrl_pred)
                    worklist.append(ctrl_pred)
        
        return slice_set

    def _get_data_pred(self, stmt_id: int, var: str) -> List[int]:
        """获取关于var的数据依赖前驱"""
        preds = []
        # 反向遍历数据依赖边
        for src, dst in self.pdg.data_deps:
            if dst == stmt_id:
                # 检查这个依赖是否涉及var
                if (dst, var) in self.pdg.use_to_defs:
                    preds.extend(self.pdg.use_to_defs[(dst, var)])
        return preds

    def _get_control_pred(self, stmt_id: int) -> List[int]:
        """获取控制依赖前驱"""
        preds = []
        for src, dst in self.pdg.control_deps:
            if dst == stmt_id:
                preds.append(src)
        return preds

    def compute_forward_slice(self, start_stmt: int) -> Set[int]:
        """
        计算前向切片：从起点出发所有可达语句
        """
        reachable = {start_stmt}
        worklist = deque([start_stmt])
        
        while worklist:
            current = worklist.popleft()
            
            # 数据依赖后继
            for src, dst in self.pdg.data_deps:
                if src == current and dst not in reachable:
                    reachable.add(dst)
                    worklist.append(dst)
            
            # 控制依赖后继
            for src, dst in self.pdg.control_deps:
                if src == current and dst not in reachable:
                    reachable.add(dst)
                    worklist.append(dst)
        
        return reachable

    def interproc_slice(self, criterion: Tuple[int, str], 
                       call_graph: Dict[int, int]) -> Set[int]:
        """
        过程间切片
        
        Args:
            criterion: 切片标准
            call_graph: 语句ID → 被调用函数ID 的映射
        """
        slice_set = self.compute_backward_slice(criterion)
        
        # 过程间传播
        worklist = deque(list(slice_set))
        while worklist:
            current = worklist.popleft()
            
            # 检查是否是函数调用
            stmt = self.pdg.nodes[current]
            if hasattr(stmt, 'is_call') and stmt.is_call:
                # 添加被调用函数的切片
                callee_id = call_graph.get(current)
                if callee_id:
                    callee_slice = self.compute_backward_slice((callee_id, criterion[1]))
                    for sid in callee_slice:
                        if sid not in slice_set:
                            slice_set.add(sid)
                            worklist.append(sid)
        
        return slice_set


def build_simple_pdg() -> DependenceGraph:
    """构建简单PDG"""
    pdg = DependenceGraph()
    
    # 语句
    s1 = Statement(1, 'assign', lhs='x', rhs=10)
    s2 = Statement(2, 'assign', lhs='y', rhs={'op': '+', 'left': 'x', 'right': 1})
    s3 = Statement(3, 'if', cond={'op': '>', 'left': 'x', 'right': 5})
    s4 = Statement(4, 'assign', lhs='z', rhs={'op': '*', 'left': 'y', 'right': 2})
    s5 = Statement(5, 'assign', lhs='w', rhs='z')
    
    for s in [s1, s2, s3, s4, s5]:
        pdg.add_statement(s)
    
    # 数据依赖
    # x = 10 → y = x + 1 (关于x)
    pdg.add_data_dep(1, 2, 'x')
    # y = x + 1 → z = y * 2 (关于y)
    pdg.add_data_dep(2, 4, 'y')
    # z = y * 2 → w = z
    pdg.add_data_dep(4, 5, 'z')
    
    # 控制依赖
    # if → then块
    pdg.add_control_dep(3, 4)
    
    return pdg


def example_simple_slice():
    """简单切片示例"""
    pdg = build_simple_pdg()
    slicer = ProgramSlicer(pdg)
    
    # 切片标准: S5的z变量
    criterion = (5, 'z')
    slice_set = slicer.compute_backward_slice(criterion)
    
    print("切片计算:")
    print(f"  切片标准: S5的z")
    print(f"  切片: {sorted(slice_set)}")
    
    print("\n切片包含的语句:")
    for sid in sorted(slice_set):
        stmt = pdg.nodes[sid - 1]
        print(f"  S{sid}: {stmt.type}")


def example_y_slice():
    """y变量的切片"""
    pdg = build_simple_pdg()
    slicer = ProgramSlicer(pdg)
    
    # y = x + 1 之后使用y
    criterion = (4, 'y')
    slice_set = slicer.compute_backward_slice(criterion)
    
    print(f"y的切片: {sorted(slice_set)}")


def example_forward_slice():
    """前向切片"""
    pdg = build_simple_pdg()
    slicer = ProgramSlicer(pdg)
    
    # 从x的定义开始
    forward = slicer.compute_forward_slice(1)
    print(f"x定义的前向切片: {sorted(forward)}")


if __name__ == "__main__":
    print("=" * 50)
    print("程序切片 测试")
    print("=" * 50)
    
    example_simple_slice()
    print()
    example_y_slice()
    print()
    example_forward_slice()
