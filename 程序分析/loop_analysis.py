# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / loop_analysis

本文件实现 loop_analysis 相关的算法功能。
"""

from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, deque


class Loop:
    """
    循环类，表示检测到的循环
    """
    
    def __init__(self, header: int):
        """
        初始化循环
        
        Args:
            header: 循环入口节点ID
        """
        self.header = header
        self.body: Set[int] = {header}  # 循环体节点集合
        self.exit_nodes: Set[int] = set()  # 出口节点集合
        self.preheader: Optional[int] = None  # 循环前置节点
        self.depth: int = 0  # 嵌套深度
    
    def add_node(self, node: int):
        """添加节点到循环体"""
        self.body.add(node)
    
    def __repr__(self):
        return f"Loop(header={self.header}, size={len(self.body)})"


class LoopDetector:
    """
    循环检测器
    
    使用Dominator树和回边检测循环。
    """
    
    def __init__(self, num_nodes: int, entry_node: int = 0):
        """
        初始化循环检测器
        
        Args:
            num_nodes: 节点总数
            entry_node: 入口节点ID
        """
        self.num_nodes = num_nodes
        self.entry_node = entry_node
        # 后继关系
        self.successors: Dict[int, List[int]] = defaultdict(list)
        # 前驱关系
        self.predecessors: Dict[int, List[int]] = defaultdict(list)
        # Dominator信息
        self.idom: Dict[int, Optional[int]] = {i: None for i in range(num_nodes)}
        self.dominators: Dict[int, Set[int]] = {i: set() for i in range(num_nodes)}
        # 检测到的循环
        self.loops: List[Loop] = []
    
    def add_edge(self, from_node: int, to_node: int):
        """添加边"""
        self.successors[from_node].append(to_node)
        self.predecessors[to_node].append(from_node)
    
    def compute_dominators(self):
        """计算Dominator集合"""
        # 入口节点支配自己
        self.dominators[self.entry_node] = {self.entry_node}
        
        changed = True
        while changed:
            changed = False
            for node in range(self.num_nodes):
                if node == self.entry_node:
                    continue
                
                # D[n] = {n} ∪ (∩_{p∈pred(n)} D[p])
                preds = self.predecessors.get(node, [])
                if not preds:
                    continue
                
                new_dom = {node}
                intersection = None
                
                for pred in preds:
                    if pred in self.dominators:
                        if intersection is None:
                            intersection = self.dominators[pred].copy()
                        else:
                            intersection &= self.dominators[pred]
                
                if intersection is not None:
                    new_dom |= intersection
                
                if new_dom != self.dominators.get(node, set()):
                    self.dominators[node] = new_dom
                    changed = True
        
        # 计算immediate dominator
        for node in range(self.num_nodes):
            doms = self.dominators[node] - {node}
            if doms:
                # 找到最接近的支配者
                for candidate in sorted(doms, key=lambda x: -len(self.dominators.get(x, set()))):
                    if candidate in self.dominators[node]:
                        self.idom[node] = candidate
                        break
    
    def detect_loops(self) -> List[Loop]:
        """
        检测所有循环
        
        使用回边检测算法：
        - 回边 (u, v)：如果 v dominates u，则 (u, v) 是回边
        - 包含回边起点的节点及其所有能到达u而不经过v的节点构成循环
        
        Returns:
            检测到的循环列表
        """
        self.loops = []
        
        # 遍历所有边
        for from_node in range(self.num_nodes):
            for to_node in self.successors.get(from_node, []):
                # 检查是否是回边：to_node dominates from_node
                if to_node in self.dominators.get(from_node, set()):
                    # 找到了回边，提取循环
                    loop = self._extract_loop(from_node, to_node)
                    if loop:
                        self.loops.append(loop)
        
        # 计算嵌套深度
        self._compute_loop_depth()
        
        return self.loops
    
    def _extract_loop(self, back_edge_from: int, back_edge_to: int) -> Optional[Loop]:
        """
        从回边提取循环
        
        Args:
            back_edge_from: 回边起点
            back_edge_to: 回边终点（循环入口）
            
        Returns:
            循环对象
        """
        loop = Loop(back_edge_to)
        
        # 使用工作列表收集循环体节点
        worklist = deque([back_edge_from])
        visited = set()
        
        while worklist:
            node = worklist.popleft()
            
            if node in visited:
                continue
            if node == back_edge_to:
                continue
            
            visited.add(node)
            loop.add_node(node)
            
            # 将前驱加入工作列表
            for pred in self.predecessors.get(node, []):
                if pred not in visited and pred != back_edge_to:
                    worklist.append(pred)
        
        # 识别出口节点：循环中有边指向循环外的节点
        for node in loop.body:
            for succ in self.successors.get(node, []):
                if succ not in loop.body:
                    loop.exit_nodes.add(node)
        
        return loop
    
    def _compute_loop_depth(self):
        """计算循环嵌套深度"""
        for loop in self.loops:
            depth = 1
            for other_loop in self.loops:
                if other_loop != loop and other_loop.header in loop.body:
                    depth += 1
            loop.depth = depth


class InductionVariable:
    """
    归纳变量类
    """
    
    def __init__(self, name: str, basic_loop: 'BasicIndVar'):
        """
        初始化归纳变量
        
        Args:
            name: 变量名
            basic_loop: 基础归纳变量
        """
        self.name = name
        self.basic_loop = basic_loop
        self.coeff_a: int = 1  # 系数 a: a * basic_var
        self.coeff_b: int = 0  # 系数 b: + b
    
    def get_value_at_iteration(self, iteration: int) -> str:
        """
        获取第n次迭代的值表达式
        
        Args:
            iteration: 迭代次数
            
        Returns:
            值表达式字符串
        """
        if self.coeff_a == 1 and self.coeff_b == 0:
            return f"{self.basic_loop.name} + {iteration * self.basic_loop.increment}"
        else:
            return f"{self.coeff_a}*{self.basic_loop.name} + {self.coeff_b} + {iteration * self.coeff_a * self.basic_loop.increment}"


class BasicIndVar:
    """
    基本归纳变量
    """
    
    def __init__(self, name: str, initial_value: str, increment: int):
        """
        初始化基本归纳变量
        
        Args:
            name: 变量名
            initial_value: 初始值表达式
            increment: 增量
        """
        self.name = name
        self.initial_value = initial_value
        self.increment = increment


class InductionVariableAnalyzer:
    """
    归纳变量分析器
    """
    
    def __init__(self):
        """初始化归纳变量分析器"""
        self.basic_vars: Dict[int, List[BasicIndVar]] = defaultdict(list)
        self.ind_vars: Dict[int, List[InductionVariable]] = defaultdict(list)
    
    def analyze_loop(self, loop: Loop, definitions: Dict[int, List[Tuple[str, str]]]) -> List[InductionVariable]:
        """
        分析循环中的归纳变量
        
        Args:
            loop: 循环
            definitions: 循环中变量定义的映射：node_id -> [(var, expr)]
            
        Returns:
            归纳变量列表
        """
        result = []
        
        # 简化实现：查找形如 i = i + const 的变量
        for node_id, defs in definitions.items():
            if node_id not in loop.body:
                continue
            
            for var, expr in defs:
                # 检查是否是基本归纳变量
                if self._is_basic_induction(var, expr, definitions, loop):
                    basic_var = BasicIndVar(var, "0", self._extract_increment(expr))
                    self.basic_vars[loop.header].append(basic_var)
                    result.append(InductionVariable(var, basic_var))
                
                # 检查是否是导出归纳变量
                elif self._is_derived_induction(var, expr, loop):
                    # 找到相关的基本归纳变量
                    for bv in self.basic_vars.get(loop.header, []):
                        if bv.name in expr:
                            ind_var = InductionVariable(var, bv)
                            ind_var.coeff_a = self._extract_coefficient(expr, bv.name)
                            ind_var.coeff_b = self._extract_constant(expr)
                            result.append(ind_var)
        
        self.ind_vars[loop.header] = result
        return result
    
    def _is_basic_induction(self, var: str, expr: str, 
                           definitions: Dict[int, List[Tuple[str, str]]],
                           loop: Loop) -> bool:
        """检查是否是基本归纳变量"""
        if f"{var} +" not in expr and f"{var} -" not in expr:
            return False
        
        # 检查初始值定义在循环外
        for node_id, defs in definitions.items():
            if node_id not in loop.body:
                for v, e in defs:
                    if v == var and var not in e:
                        return True
        
        return False
    
    def _is_derived_induction(self, var: str, expr: str, loop: Loop) -> bool:
        """检查是否是导出归纳变量"""
        # 简化：变量表达式中包含循环内的基本归纳变量
        return False  # 简化实现
    
    def _extract_increment(self, expr: str) -> int:
        """从表达式中提取增量"""
        import re
        match = re.search(r'([+-]\s*\d+)', expr)
        if match:
            return int(match.group(1).replace(' ', ''))
        return 1
    
    def _extract_coefficient(self, expr: str, var_name: str) -> int:
        """提取系数"""
        if f"{var_name} *" in expr:
            return 2
        return 1
    
    def _extract_constant(self, expr: str) -> int:
        """提取常数项"""
        import re
        match = re.search(r'([+-]\s*\d+)(?!\s*\*)', expr)
        if match:
            return int(match.group(1).replace(' ', ''))
        return 0


class LoopInvariantCodeMotion:
    """
    循环不变代码移动（LICM）分析器
    """
    
    def __init__(self):
        """初始化"""
        self.loop_invariant: Dict[int, Set[str]] = defaultdict(set)  # loop_header -> invariant_stmts
        self.can_move: Dict[int, Set[str]] = defaultdict(set)  # 可以移动的语句
    
    def analyze(self, loop: Loop, 
                statements: Dict[int, str],
                definitions: Dict[int, Set[str]],
                uses: Dict[int, Set[str]]) -> Set[int]:
        """
        分析循环中哪些语句可以移动
        
        循环不变代码的条件：
        1. 语句中所有引用的变量在循环外定义，或者在循环中定义但本身也是不变的
        2. 语句的赋值变量在循环中不被使用（或者使用但可以处理）
        
        Args:
            loop: 循环
            statements: 语句映射
            definitions: 每条语句定义的变量
            uses: 每条语句使用的变量
            
        Returns:
            可以移动的语句ID集合
        """
        can_move = set()
        
        for stmt_id in loop.body:
            if self._is_loop_invariant(stmt_id, loop, definitions, uses):
                can_move.add(stmt_id)
        
        self.can_move[loop.header] = can_move
        return can_move
    
    def _is_loop_invariant(self, stmt_id: int, loop: Loop,
                          definitions: Dict[int, Set[str]],
                          uses: Dict[int, Set[str]]) -> bool:
        """检查语句是否是循环不变的"""
        stmt_uses = uses.get(stmt_id, set())
        stmt_defs = definitions.get(stmt_id, set())
        
        # 如果语句使用的变量都在循环外定义，则是循环不变的
        for var in stmt_uses:
            # 检查变量是否在循环中被定义
            defined_in_loop = False
            for node_id in loop.body:
                if var in definitions.get(node_id, set()):
                    defined_in_loop = True
                    break
            
            if defined_in_loop:
                return False
        
        # 如果语句定义的变量在循环外被使用，则不能移动
        # 简化处理
        
        return True


def create_loop_example() -> Tuple[LoopDetector, List[int]]:
    """
    创建带循环的CFG示例
    
    结构：
        0 -> 1 -> 2 -> 3 -> 4
                  ^    |
                  |    v
                  +----5
    
    循环：2 -> 3 -> 5 -> 2
    """
    detector = LoopDetector(num_nodes=6, entry_node=0)
    
    # 添加边
    detector.add_edge(0, 1)
    detector.add_edge(1, 2)
    detector.add_edge(2, 3)
    detector.add_edge(3, 4)
    detector.add_edge(3, 5)  # 条件分支
    detector.add_edge(5, 2)  # 回边：5 -> 2（循环）
    
    return detector, [0, 1, 2, 3, 4, 5]


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：循环检测")
    print("=" * 60)
    
    detector, nodes = create_loop_example()
    detector.compute_dominators()
    
    print("\nDominator关系:")
    for node in nodes:
        doms = sorted(detector.dominators.get(node, set()))
        print(f"  Node {node}: dominates {{{', '.join(str(d) for d in doms)}}}")
    
    loops = detector.detect_loops()
    
    print(f"\n检测到 {len(loops)} 个循环:")
    for loop in loops:
        print(f"  循环入口: Block {loop.header}")
        print(f"  循环体: {sorted(loop.body)}")
        print(f"  出口节点: {sorted(loop.exit_nodes)}")
        print(f"  嵌套深度: {loop.depth}")
        print()
    
    print("=" * 60)
    print("测试2：归纳变量分析")
    print("=" * 60)
    
    # 模拟循环中的定义
    definitions = {
        2: [("i", "i + 1")],  # i = i + 1（基本归纳变量）
        3: [("sum", "sum + i")],  # sum = sum + i（导出归纳变量）
    }
    
    analyzer = InductionVariableAnalyzer()
    
    if loops:
        loop = loops[0]
        ind_vars = analyzer.analyze_loop(loop, definitions)
        
        print(f"\n循环 {loop.header} 的归纳变量:")
        for iv in ind_vars:
            print(f"  {iv.name}: {iv.coeff_a} * {iv.basic_loop.name} + {iv.coeff_b}")
    
    print("\n" + "=" * 60)
    print("测试3：循环不变代码移动分析")
    print("=" * 60)
    
    licm = LoopInvariantCodeMotion()
    
    # 模拟语句
    statements = {
        2: "i = i + 1",
        3: "sum = sum + i",
        4: "x = a + b",  # 循环不变
    }
    
    # 定义和使用
    stmt_definitions = {
        2: {"i"},
        3: {"sum"},
        4: {"x"},
    }
    
    stmt_uses = {
        2: {"i"},
        3: {"sum", "i"},
        4: {"a", "b"},
    }
    
    if loops:
        loop = loops[0]
        can_move = licm.analyze(loop, statements, stmt_definitions, stmt_uses)
        
        print(f"\n循环 {loop.header} 中可以移动的语句:")
        for stmt_id in sorted(can_move):
            print(f"  [{stmt_id}] {statements.get(stmt_id, 'unknown')}")
    
    print("\n循环分析测试完成!")
    print("\n注意：实际循环优化还需要：")
    print("  1. 精确的循环不变性判断")
    print("  2. 循环前置节点的创建")
    print("  3. 依赖分析（确保移动不破坏依赖）")
