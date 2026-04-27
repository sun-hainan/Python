# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / pointer_analysis

本文件实现 pointer_analysis 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple, Union
from collections import defaultdict, deque
from abc import ABC, abstractmethod


class PointsToGraph:
    """
    指向图 (Points-to Graph)
    
    节点：
    - 变量节点 (Variable Node)
    - 位置节点 (Location Node/Object Node)
    
    边：
    - points_to: variable -> location
    """
    
    def __init__(self):
        """初始化指向图"""
        # 变量节点到位置节点的映射：variable -> {locations}
        self.points_to: Dict[str, Set[str]] = defaultdict(set)
        # 位置节点的字段：location -> {field -> location}
        self.fields: Dict[str, Dict[str, str]] = defaultdict(dict)
        # 地址-of 节点：用于 &x 产生的节点
        self.address_of: Set[str] = set()
        # 节点类型标签
        self.is_variable: Set[str] = set()
        self.is_location: Set[str] = set()
    
    def add_points_to(self, var: str, location: str):
        """
        添加指向关系
        
        Args:
            var: 变量名
            location: 位置名
        """
        self.points_to[var].add(location)
        self.is_variable.add(var)
        self.is_location.add(location)
    
    def get_points_to(self, var: str) -> Set[str]:
        """
        获取变量的指向集合
        
        Args:
            var: 变量名
            
        Returns:
            可能的指向位置集合
        """
        return self.points_to.get(var, set()).copy()
    
    def add_field(self, location: str, field: str, target: str):
        """
        添加结构字段指向关系
        
        Args:
            location: 结构体位置
            field: 字段名
            target: 字段指向的目标位置
        """
        self.fields[location][field] = target
    
    def get_field_target(self, location: str, field: str) -> Optional[str]:
        """
        获取结构字段的指向
        
        Args:
            location: 结构体位置
            field: 字段名
            
        Returns:
            字段指向的位置
        """
        return self.fields.get(location, {}).get(field)
    
    def merge(self, other: 'PointsToGraph') -> bool:
        """
        合并另一个指向图到当前图
        
        Args:
            other: 另一个指向图
            
        Returns:
            如果图有变化返回True
        """
        changed = False
        
        for var, locations in other.points_to.items():
            for loc in locations:
                if loc not in self.points_to[var]:
                    self.points_to[var].add(loc)
                    changed = True
        
        return changed
    
    def __str__(self) -> str:
        lines = ["Points-To Graph:"]
        for var in sorted(self.points_to.keys()):
            locs = sorted(self.points_to[var])
            lines.append(f"  {var} -> {{{', '.join(locs)}}}")
        
        if self.fields:
            lines.append("\nFields:")
            for loc, fields in sorted(self.fields.items()):
                for field, target in sorted(fields.items()):
                    lines.append(f"  {loc}.{field} -> {target}")
        
        return "\n".join(lines)


class PointerAnalyzer:
    """
    指针分析器
    
    实现基本的指针分析算法。
    这里实现的是一个简化版的流不敏感、上下文不敏感的指针分析。
    """
    
    def __init__(self):
        """初始化指针分析器"""
        # 指向图
        self.ptg = PointsToGraph()
        # 语句列表
        self.statements: List[Tuple[str, ...]] = []
        # 约束列表
        self.constraints: List[Tuple[str, str, str]] = []  # (lhs, rhs, op)
    
    def add_statement(self, stmt_type: str, *args):
        """
        添加指针相关语句
        
        语句类型：
        - 'addr': x = &y (x指向y的地址)
        - 'assign': x = y (x和y指向相同)
        - 'load': x = *y (x指向y指向的内容)
        - 'store': *x = y (x指向的内容是y)
        - 'new': x = new T (x指向新分配的对象)
        
        Args:
            stmt_type: 语句类型
            *args: 语句参数
        """
        self.statements.append((stmt_type, *args))
    
    def _process_statements(self):
        """处理所有语句，构建约束"""
        for stmt in self.statements:
            stmt_type = stmt[0]
            
            if stmt_type == 'addr':
                # x = &y
                x, y = stmt[1], stmt[2]
                # 创建y的位置节点
                location = f"loc_{y}"
                self.ptg.add_address_of(location)
                self.ptg.add_points_to(x, location)
            
            elif stmt_type == 'assign':
                # x = y
                x, y = stmt[1], stmt[2]
                # x和y指向相同
                self.constraints.append((x, y, 'same'))
            
            elif stmt_type == 'load':
                # x = *y
                x, y = stmt[1], stmt[2]
                # x指向 y指向的内容
                self.constraints.append((x, y, 'deref'))
            
            elif stmt_type == 'store':
                # *x = y
                x, y = stmt[1], stmt[2]
                # x指向的内容是y
                self.constraints.append((x, y, 'store'))
            
            elif stmt_type == 'new':
                # x = new T
                x, type_name = stmt[1], stmt[2]
                location = f"obj_{type_name}_{id(stmt)}"
                self.ptg.add_points_to(x, location)
            
            elif stmt_type == 'field':
                # x = y.f
                x, y, field = stmt[1], stmt[2], stmt[3]
                # x指向 y.field
                self.constraints.append((x, y, field, 'field'))
    
    def analyze(self) -> PointsToGraph:
        """
        执行指针分析
        
        Returns:
            分析结果指向图
        """
        # 处理语句，构建约束
        self._process_statements()
        
        # 迭代求解约束不动点
        changed = True
        iteration = 0
        max_iterations = 1000
        
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            
            for constraint in self.constraints:
                if len(constraint) == 3:
                    lhs, rhs, op = constraint
                    
                    if op == 'same':
                        # x points_to whatever y points_to
                        rhs_pts = self.ptg.get_points_to(rhs)
                        for loc in rhs_pts:
                            if loc not in self.ptg.get_points_to(lhs):
                                self.ptg.add_points_to(lhs, loc)
                                changed = True
                    
                    elif op == 'deref':
                        # x = *y: 需要处理解引用
                        # 这里简化处理
                        pass
                    
                    elif op == 'store':
                        # *x = y: 需要处理存储
                        # 这里简化处理
                        pass
                
                elif len(constraint) == 4:
                    lhs, rhs, field, _ = constraint
                    # x = y.f: 获取字段
                    rhs_pts = self.ptg.get_points_to(rhs)
                    for loc in rhs_pts:
                        field_loc = self.ptg.get_field_target(loc, field)
                        if field_loc:
                            self.ptg.add_points_to(lhs, field_loc)
                            changed = True
        
        return self.ptg
    
    def get_aliases(self, var1: str, var2: str) -> bool:
        """
        检查两个变量是否可能是别名（指向同一位置）
        
        Args:
            var1: 第一个变量
            var2: 第二个变量
            
        Returns:
            如果可能是别名返回True
        """
        pts1 = self.ptg.get_points_to(var1)
        pts2 = self.ptg.get_points_to(var2)
        
        # 如果指向集合有交集，则是别名
        return bool(pts1 & pts2)
    
    def may_point_to(self, var: str, location: str) -> bool:
        """
        检查变量是否可能指向指定位置
        
        Args:
            var: 变量名
            location: 位置名
            
        Returns:
            如果可能指向返回True
        """
        return location in self.ptg.get_points_to(var)


class FlowSensitivePointerAnalyzer:
    """
    流敏感指针分析器
    
    在控制流图上逐语句分析指针行为。
    """
    
    def __init__(self, num_blocks: int):
        """
        初始化流敏感指针分析器
        
        Args:
            num_blocks: 基本块数量
        """
        self.num_blocks = num_blocks
        # 每个块的入口状态
        self.in_state: Dict[int, PointsToGraph] = {}
        # 每个块的出口状态
        self.out_state: Dict[int, PointsToGraph] = {}
        # 每个块的语句
        self.block_statements: Dict[int, List] = defaultdict(list)
        # 前驱关系
        self.predecessors: Dict[int, List[int]] = defaultdict(list)
    
    def add_block_statement(self, block_id: int, stmt_type: str, *args):
        """
        添加块语句
        
        Args:
            block_id: 基本块ID
            stmt_type: 语句类型
            *args: 语句参数
        """
        self.block_statements[block_id].append((stmt_type, *args))
    
    def add_edge(self, from_id: int, to_id: int):
        """
        添加控制流边
        
        Args:
            from_id: 起始块ID
            to_id: 目标块ID
        """
        self.predecessors[to_id].append(from_id)
    
    def _copy_graph(self, ptg: PointsToGraph) -> PointsToGraph:
        """
        复制指向图
        
        Args:
            ptg: 原图
            
        Returns:
            复制的新图
        """
        new_ptg = PointsToGraph()
        new_ptg.points_to = defaultdict(set, {
            v: s.copy() for v, s in ptg.points_to.items()
        })
        new_ptg.fields = defaultdict(dict, {
            loc: fields.copy() for loc, fields in ptg.fields.items()
        })
        new_ptg.address_of = ptg.address_of.copy()
        return new_ptg
    
    def _transfer_function(self, block_id: int, ptg: PointsToGraph) -> PointsToGraph:
        """
        传输函数：应用块语句到指向图
        
        Args:
            block_id: 基本块ID
            ptg: 入口指向图
            
        Returns:
            出口指向图
        """
        new_ptg = self._copy_graph(ptg)
        
        for stmt in self.block_statements[block_id]:
            stmt_type = stmt[0]
            
            if stmt_type == 'addr':
                x, y = stmt[1], stmt[2]
                location = f"loc_{y}"
                new_ptg.address_of.add(location)
                new_ptg.add_points_to(x, location)
            
            elif stmt_type == 'assign':
                x, y = stmt[1], stmt[2]
                y_pts = new_ptg.get_points_to(y)
                for loc in y_pts:
                    new_ptg.add_points_to(x, loc)
            
            elif stmt_type == 'new':
                x, type_name = stmt[1], stmt[2]
                location = f"obj_{type_name}_{block_id}_{id(stmt)}"
                new_ptg.add_points_to(x, location)
        
        return new_ptg
    
    def analyze(self, entry_block: int = 0) -> bool:
        """
        执行流敏感指针分析
        
        Args:
            entry_block: 入口块ID
            
        Returns:
            是否收敛
        """
        # 初始化入口块
        self.in_state[entry_block] = PointsToGraph()
        
        worklist = deque([entry_block])
        visited = set()
        
        while worklist:
            block_id = worklist.popleft()
            
            if block_id in visited:
                continue
            visited.add(block_id)
            
            # 计算入口状态（合并所有前驱的出口状态）
            if block_id != entry_block:
                in_ptg = PointsToGraph()
                for pred_id in self.predecessors[block_id]:
                    if pred_id in self.out_state:
                        in_ptg.merge(self.out_state[pred_id])
                self.in_state[block_id] = in_ptg
            
            # 应用传输函数
            current_in = self.in_state.get(block_id, PointsToGraph())
            new_out = self._transfer_function(block_id, current_in)
            
            # 检查是否有变化
            old_out = self.out_state.get(block_id)
            if old_out is None:
                self.out_state[block_id] = new_out
                changed = True
            else:
                # 简单检查：比较指向集合大小
                old_size = sum(len(pts) for pts in old_out.points_to.values())
                new_size = sum(len(pts) for pts in new_out.points_to.values())
                changed = old_size != new_size
                self.out_state[block_id] = new_out
            
            # 将后继加入工作列表
            if changed:
                for stmt in self.block_statements[block_id]:
                    if stmt[0] == 'goto':
                        target = stmt[1]
                        if target not in visited:
                            worklist.append(target)
        
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：简单指针分析的流不敏感分析")
    print("=" * 60)
    
    analyzer = PointerAnalyzer()
    
    # 示例程序：
    # p = &a
    # q = &b
    # r = q
    # *p = c
    
    analyzer.add_statement('addr', 'p', 'a')  # p = &a
    analyzer.add_statement('addr', 'q', 'b')  # q = &b
    analyzer.add_statement('assign', 'r', 'q')  # r = q
    analyzer.add_statement('new', 'x', 'Node')  # x = new Node
    
    ptg = analyzer.analyze()
    
    print("\n指向关系:")
    print(f"  p -> {ptg.get_points_to('p')}")
    print(f"  q -> {ptg.get_points_to('q')}")
    print(f"  r -> {ptg.get_points_to('r')}")
    print(f"  x -> {ptg.get_points_to('x')}")
    
    print("\n别名分析:")
    print(f"  p 和 q 是别名: {analyzer.get_aliases('p', 'q')}")  # False
    print(f"  q 和 r 是别名: {analyzer.get_aliases('q', 'r')}")  # True
    
    print("\n" + "=" * 60)
    print("测试2：结构体字段指针分析")
    print("=" * 60)
    
    analyzer2 = PointerAnalyzer()
    
    # 示例：
    # p = &obj.field1
    # 等价于：tmp = obj; p = tmp.field1
    
    # 创建指向图
    ptg2 = analyzer2.analyze()
    
    # 手动添加结构体字段关系
    ptg2.add_field('loc_obj', 'field1', 'loc_field1_target')
    ptg2.add_points_to('p', 'loc_field1_target')
    
    print("\n结构体字段指向:")
    print(f"  obj.field1 -> {ptg2.get_field_target('loc_obj', 'field1')}")
    print(f"  p -> {ptg2.get_points_to('p')}")
    
    print("\n" + "=" * 60)
    print("测试3：流敏感指针分析")
    print("=" * 60)
    
    flow_analyzer = FlowSensitivePointerAnalyzer(num_blocks=4)
    
    # Block 0: p = &a
    flow_analyzer.add_block_statement(0, 'addr', 'p', 'a')
    
    # Block 1: q = p (q指向p指向的内容)
    flow_analyzer.add_block_statement(1, 'assign', 'q', 'p')
    
    # Block 2: p = &b (重新定义p)
    flow_analyzer.add_block_statement(2, 'addr', 'p', 'b')
    
    # Block 3: r = p
    flow_analyzer.add_block_statement(3, 'assign', 'r', 'p')
    
    # 添加控制流边
    flow_analyzer.add_edge(0, 1)
    flow_analyzer.add_edge(1, 2)
    flow_analyzer.add_edge(2, 3)
    flow_analyzer.add_edge(1, 3)  # 条件分支
    
    flow_analyzer.analyze(entry_block=0)
    
    print("\n流敏感分析结果:")
    for block_id in range(4):
        in_ptg = flow_analyzer.in_state.get(block_id)
        out_ptg = flow_analyzer.out_state.get(block_id)
        
        print(f"\n  Block {block_id}:")
        if in_ptg:
            for var in ['p', 'q', 'r']:
                pts = in_ptg.get_points_to(var)
                if pts:
                    print(f"    IN:  {var} -> {pts}")
        if out_ptg:
            for var in ['p', 'q', 'r']:
                pts = out_ptg.get_points_to(var)
                if pts:
                    print(f"    OUT: {var} -> {pts}")
    
    print("\n指针分析测试完成!")
    print("\n注意：实际指针分析还需要处理：")
    print("  1. 函数调用和返回")
    print("  2. 数组和动态分配")
    print("  3. 上下文敏感和线程分析")
    print("  4. 复杂的数据结构")
