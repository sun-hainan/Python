# -*- coding: utf-8 -*-
"""
ATMS - Assumption-based Truth Maintenance System
功能：基于假设的真值维护系统，用于追踪信念和假设之间的依赖关系

ATMS与CDCL的区别：
- CDCL学习的是子句约束（永久）
- ATMS维护的是假设→结论的依赖图（可撤销）

核心概念：
- Assumption（假设）：可被撤回的基本信念
- Datum（数据）：从假设推导出的结论
- Node（节点）：假设或数据
- Label（标签）：节点成立的假设集合的析取范式

作者：TMS Team
"""

from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict, deque


class ATMSNode:
    """ATMS节点"""
    def __init__(self, name: str, is_assumption: bool = False):
        self.name = name
        self.is_assumption = is_assumption
        # 标签：假设集合的列表（每个集合表示一种使该节点为真的方式）
        # 标签格式：[frozenset({a1, a2}), frozenset({a3}), ...]
        self.label: List[Set[str]] = []
        self.supporters: Dict[str, Set[str]] = {}  # assumption → its consequences
        self.justifications: List[Tuple['ATMSNode', ...]] = []  # 推导该节点的规则

    def add_to_label(self, assumptions: Set[str]):
        """添加假设集合到标签"""
        # 归一化：删除被包含的集合
        new_assumptions = frozenset(assumptions)
        
        # 检查是否已有等价集合
        for existing in self.label:
            if existing == new_assumptions:
                return
        
        # 删除被新集合包含的旧集合
        self.label = [s for s in self.label if not new_assumptions <= s]
        self.label.append(new_assumptions)

    def __repr__(self):
        return f"Node({self.name}, {self.is_assumption})"


class ATMS:
    """
    基于假设的真值维护系统
    
    使用ATMS维护推导关系，支持：
    - 多个假设同时成立
    - 快速回滚（通过标签而非回溯）
    - 冲突检测
    """

    def __init__(self):
        self.nodes: Dict[str, ATMSNode] = {}
        self.assumptions: Set[str] = set()
        self.contradictions: List[Set[str]] = []  # 已知冲突的假设集合

    def make_assumption(self, name: str) -> ATMSNode:
        """创建假设节点"""
        node = ATMSNode(name, is_assumption=True)
        self.nodes[name] = node
        self.assumptions.add(name)
        node.add_to_label({name})
        return node

    def declare_datum(self, name: str) -> ATMSNode:
        """声明数据节点（非假设结论）"""
        if name not in self.nodes:
            node = ATMSNode(name, is_assumption=False)
            self.nodes[name] = node
        return self.nodes[name]

    def add_justification(self, consequence: str, *antecedents: str):
        """
        添加推导规则: antecedent1 ∧ antecedent2 ∧ ... → consequence
        
        ATMS自动维护前向链
        """
        if consequence not in self.nodes:
            self.declare_datum(consequence)
        
        consequence_node = self.nodes[consequence]
        consequence_node.justifications.append(antecedents)
        
        # 前向链：从已知前提推导
        self._propagate(antecedents, consequence)

    def _propagate(self, antecedents: Tuple[str, ...], consequence: str):
        """
        前向传播：检查前提是否被满足，若满足则更新结论标签
        
        若所有antecedents在某个假设集合A中都为真，则consequence在A中也为真
        """
        consequence_node = self.nodes[consequence]
        
        # 收集所有前提节点的标签
        antecedent_labels: List[List[Set[str]]] = []
        all_assumptions: Set[str] = set()
        
        for ant in antecedents:
            if ant not in self.nodes:
                return  # 前提节点不存在，无法推导
            ant_node = self.nodes[ant]
            if not ant_node.label:
                return  # 前提节点无有效标签，无法推导
            antecedent_labels.append(ant_node.label)
            for label_set in ant_node.label:
                all_assumptions.update(label_set)
        
        # 寻找所有前提同时成立的假设集合
        # 即：在每个前提的标签中各选一个集合，它们的交集非空
        derived_labels: List[Set[str]] = []
        
        from itertools import product
        for combination in product(*antecedent_labels):
            intersection = set.intersection(*combination) if combination else set()
            if intersection:
                derived_labels.append(intersection)
        
        # 添加新标签
        for label in derived_labels:
            consequence_node.add_to_label(label)
        
        # 传播效果：consequence作为其他节点的前提
        self._forward_chain(consequence)

    def _forward_chain(self, node_name: str):
        """前向链：以node为前提推导其他节点"""
        node = self.nodes.get(node_name)
        if not node:
            return
        
        # 找出所有以node_name为前提的推导规则
        for name, n in self.nodes.items():
            for just in n.justifications:
                if node_name in just:
                    self._propagate(just, name)

    def is_true(self, name: str, current_assumptions: Set[str]) -> bool:
        """
        检查节点在当前假设集下是否为真
        
        Args:
            name: 节点名
            current_assumptions: 当前激活的假设集合
            
        Returns:
            True if node is true under current_assumptions
        """
        if name not in self.nodes:
            return False
        
        node = self.nodes[name]
        for label_set in node.label:
            if label_set <= current_assumptions:
                return True
        return False

    def check_contradiction(self, assumptions: Set[str]) -> Optional[Set[str]]:
        """
        检查假设集合是否导致矛盾
        
        Returns:
            导致矛盾的最小假设子集，或None
        """
        # 简化：检查是否有假设同时声明为真和假
        for conflict in self.contradictions:
            if conflict <= assumptions:
                return conflict
        return None

    def get_nogoods(self) -> List[Set[str]]:
        """
        获取已知的不良假设集合（Nogood）
        
        这些集合被证明会导致矛盾
        """
        return self.contradictions.copy()


def example_basic_atms():
    """基本ATMS示例"""
    atms = ATMS()
    
    # 创建假设
    a = atms.make_assumption("a")  # 假设A
    b = atms.make_assumption("b")  # 假设B
    c = atms.make_assumption("c")  # 假设C
    
    # 添加推导规则
    # A ∧ B → D
    atms.add_justification("d", "a", "b")
    # D → E
    atms.add_justification("e", "d")
    # A ∧ C → F
    atms.add_justification("f", "a", "c")
    
    # 检查节点状态
    print("节点d的标签:", atms.nodes["d"].label)
    print("节点e的标签:", atms.nodes["e"].label)
    print("节点f的标签:", atms.nodes["f"].label)
    
    # 在假设{a,b}下检查
    print(f"\n在{{a,b}}下d为真: {atms.is_true('d', {'a', 'b'})}")
    print(f"在{{a,b}}下f为真: {atms.is_true('f', {'a', 'b'})}")
    print(f"在{{a,c}}下d为真: {atms.is_true('d', {'a', 'c'})}")


def example_contradiction():
    """矛盾检测示例"""
    atms = ATMS()
    
    a = atms.make_assumption("a")
    b = atms.make_assumption("b")
    
    # a → p
    atms.add_justification("p", "a")
    # b → ¬p
    atms.add_justification("not_p", "b")
    
    # 同时激活a和b应该矛盾
    contradiction = atms.check_contradiction({'a', 'b'})
    print(f"假设{{a,b}}矛盾: {contradiction}")


def example_label_propagation():
    """标签传播示例"""
    atms = ATMS()
    
    a = atms.make_assumption("a")
    b = atms.make_assumption("b")
    c = atms.make_assumption("c")
    
    # A ∨ B → D (简化：用两个单前提规则表示)
    atms.add_justification("d1", "a")  # A → D
    atms.add_justification("d2", "b")  # B → D
    
    # D ∧ C → E
    atms.add_justification("e", "d", "c")
    
    print("D的标签:", atms.nodes["d"].label if "d" in atms.nodes else "无")
    # 应该从d1和d2传播得到
    print("E的标签:", atms.nodes["e"].label if "e" in atms.nodes else "无")


if __name__ == "__main__":
    print("=" * 50)
    print("ATMS求解器 测试")
    print("=" * 50)
    
    example_basic_atms()
    print()
    example_contradiction()
    print()
    example_label_propagation()
