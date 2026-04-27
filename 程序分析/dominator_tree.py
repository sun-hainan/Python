# -*- coding: utf-8 -*-
"""
算法实现：程序分析 / dominator_tree

本文件实现 dominator_tree 相关的算法功能。
"""

from typing import Dict, List, Set, Optional
from collections import defaultdict, deque


class DominatorTree:
    """
    Dominator树类
    
    存储和查询程序中各基本块的支配关系。
    """
    
    def __init__(self, num_blocks: int, entry_block: int = 0):
        """
        初始化Dominator树
        
        Args:
            num_blocks: 基本块总数
            entry_block: 入口基本块的ID（默认为0）
        """
        self.num_blocks = num_blocks
        self.entry_block = entry_block
        # 每个块的immediate dominator
        self.idom: Dict[int, Optional[int]] = {i: None for i in range(num_blocks)}
        # Dominator树的孩子节点
        self.children: Dict[int, List[int]] = {i: [] for i in range(num_blocks)}
        # 每个块的支配集合
        self.dominators: Dict[int, Set[int]] = {i: set() for i in range(num_blocks)}
        # 半支配者（用于Lengauer-Tarjan算法）
        self.semi: Dict[int, int] = {}
        # 祖先（用于Lengauer-Tarjan算法）
        self.ancestor: Dict[int, int] = {}
        # 标签（用于Lengauer-Tarjan算法）
        self.label: Dict[int, int] = {}
        # 后代（用于Lengauer-Tarjan算法）
        self.parent: Dict[int, int] = {}
        # 预处理顺序
        self.vertlist: List[int] = []
        # 前驱列表
        self.predecessors: Dict[int, List[int]] = defaultdict(list)
        # 后继列表
        self.successors: Dict[int, List[int]] = defaultdict(list)
    
    def add_edge(self, from_id: int, to_id: int):
        """
        添加控制流边
        
        Args:
            from_id: 起始块ID
            to_id: 目标块ID
        """
        self.successors[from_id].append(to_id)
        self.predecessors[to_id].append(from_id)
    
    def build(self):
        """
        构建Dominator树
        
        使用Lengauer-Tarjan算法的简化版本。
        """
        # 初始化
        for v in range(self.num_blocks):
            self.semi[v] = v
            self.ancestor[v] = 0
            self.label[v] = v
            self.parent[v] = 0
        
        # 深度优先排序
        self.vertlist = []
        visited = set()
        
        def dfs(v: int):
            """深度优先搜索构建顺序"""
            visited.add(v)
            self.vertlist.append(v)
            for w in self.successors[v]:
                if w not in visited:
                    self.parent[w] = v
                    dfs(w)
        
        dfs(self.entry_block)
        
        # 逆序处理（除了根节点）
        for v in reversed(self.vertlist[1:],):
            # 计算半支配者
            for w in self.predecessors[v]:
                if w in visited:
                    r = self.eval(w)
                    self.semi[v] = min(self.semi[v], self.semi[r])
            
            # 将v加入semi[v]的子树
            self.ancestor[self.semi[v]] = v
            
            # 路径压缩
            for w in self.successors[self.semi[v]]:
                if self.semi[w] == self.semi[v]:
                    continue
                w_idom = self.idom.get(w)
                if w_idom is None:
                    continue
                if self.semi[w] in self.dominators.get(w_idom, set()) or w_idom == self.semi[v]:
                    pass
        
        # 第二遍：计算immediate dominator
        for v in self.vertlist[1:]::
            w = self.idom.get(v)
            if w is None:
                continue
            # 从v向上追溯到w的孩子
            while w != self.semi[v]:
                if self.idom.get(w) is not None and self.idom[w] not in self.dominators.get(self.semi[v], set()):
                    break
                w = self.parent.get(w, self.idom.get(w, self.entry_block))
            
            self.idom[v] = self.semi[v]
        
        # 手动计算完整的支配集合
        self._compute_dominators()
        
        # 构建树结构
        for v in range(self.num_blocks):
            if v == self.entry_block:
                continue
            idom_v = self.idom.get(v)
            if idom_v is not None:
                self.children[idom_v].append(v)
    
    def _compute_dominators(self):
        """计算每个块的完整支配集合"""
        # 入口块只支配自己
        self.dominators[self.entry_block] = {self.entry_block}
        
        changed = True
        while changed:
            changed = False
            for v in range(self.num_blocks):
                if v == self.entry_block:
                    continue
                # D[n] = {n} ∪ ∩_{p∈pred(n)} D[p]
                new_dom = {v}
                preds = self.predecessors.get(v, [])
                if preds:
                    intersection = None
                    for p in preds:
                        if p in self.dominators:
                            if intersection is None:
                                intersection = self.dominators[p].copy()
                            else:
                                intersection &= self.dominators[p]
                    if intersection is not None:
                        new_dom |= intersection
                
                if new_dom != self.dominators.get(v, set()):
                    self.dominators[v] = new_dom
                    changed = True
    
    def is_dominated_by(self, block_id: int, dominator: int) -> bool:
        """
        检查一个块是否被指定块支配
        
        Args:
            block_id: 待检查的块ID
            dominator: 可能的支配者
            
        Returns:
            如果dominator支配block_id则返回True
        """
        return dominator in self.dominators.get(block_id, set())
    
    def get_immediate_dominator(self, block_id: int) -> Optional[int]:
        """
        获取指定块的immediate dominator
        
        Args:
            block_id: 基本块ID
            
        Returns:
            immediate dominator的ID，如果不存在则返回None
        """
        return self.idom.get(block_id)
    
    def get_dominance_frontier(self, block_id: int) -> Set[int]:
        """
        获取指定块的支配边界（Dominance Frontier）
        
        支配边界用于计算phi函数的位置。
        
        Args:
            block_id: 基本块ID
            
        Returns:
            支配边界集合
        """
        df = set()
        
        for s in self.successors.get(block_id, []):
            if s != block_id:
                df.add(s)
        
        for c in self.children.get(block_id, []):
            for y in self.get_dominance_frontier(c):
                if not self.is_dominated_by(y, block_id) or y == block_id:
                    df.add(y)
        
        return df
    
    def get_dom_tree_path(self, from_block: int, to_block: int) -> List[int]:
        """
        获取从from_block到to_block在支配树中的路径
        
        Args:
            from_block: 起始块
            to_block: 目标块
            
        Returns:
            路径上的块ID列表（包含两端）
        """
        if not self.is_dominated_by(to_block, from_block):
            return []
        
        path = [to_block]
        current = to_block
        while current != from_block:
            idom = self.get_immediate_dominator(current)
            if idom is None or idom == current:
                break
            path.append(idom)
            current = idom
        
        path.append(from_block)
        return list(reversed(path))
    
    def find_common_dominator(self, block1: int, block2: int) -> int:
        """
        找到两个块的最近公共支配者
        
        Args:
            block1: 第一个块ID
            block2: 第二个块ID
            
        Returns:
            最近公共支配者的块ID
        """
        if block1 == block2:
            return block1
        
        # 收集block1的所有支配者
        doms1 = self.dominators.get(block1, set())
        doms2 = self.dominators.get(block2, set())
        
        # 找交集
        common = doms1 & doms2
        if not common:
            return self.entry_block
        
        # 返回编号最大的（即最接近两个块的）
        return max(common)
    
    def display(self):
        """打印Dominator树（用于调试）"""
        print("=" * 60)
        print("Dominator Tree")
        print("=" * 60)
        
        print("\nImmediate Dominators:")
        for v in range(self.num_blocks):
            idom_v = self.idom.get(v)
            idom_str = f"Block {idom_v}" if idom_v is not None else "None"
            print(f"  Block {v}: idom = {idom_str}")
        
        print("\nDominators Sets:")
        for v in range(self.num_blocks):
            doms = sorted(self.dominators.get(v, set()))
            print(f"  Block {v}: {{{', '.join(str(d) for d in doms)}}}")
        
        print("\nDominator Tree Structure:")
        def print_tree(block_id: int, indent: int = 0):
            prefix = "  " * indent
            idom_v = self.idom.get(block_id)
            print(f"{prefix}Block {block_id}" + (f" (idom=Block{idom_v})" if idom_v is not None else " (root)"))
            for child in sorted(self.children.get(block_id, [])):
                print_tree(child, indent + 1)
        
        print_tree(self.entry_block)


def create_simple_cfg():
    """
    创建简单CFG用于测试
    
    结构：
        [0] -> [1] -> [2] -> [3]
                  \-> [4]
    
    预期Dominator关系：
        Block 0: dominates {0}
        Block 1: dominates {0, 1}
        Block 2: dominates {0, 1, 2}
        Block 3: dominates {0, 1, 2, 3}
        Block 4: dominates {0, 1, 4}
    """
    dt = DominatorTree(num_blocks=5, entry_block=0)
    
    # 添加边
    dt.add_edge(0, 1)
    dt.add_edge(1, 2)
    dt.add_edge(1, 4)
    dt.add_edge(2, 3)
    dt.add_edge(3, 4)
    
    return dt


def create_loop_cfg():
    """
    创建带循环的CFG用于测试
    
    结构：
        [0] -> [1] -> [2] -> [3]
                  ^         |
                  |         v
                  +---- [4] <+
    
    预期：
        Block 0支配所有块
        Block 1支配1,2,3,4
        Block 2支配2,3
        Block 3支配3,4
    """
    dt = DominatorTree(num_blocks=5, entry_block=0)
    
    dt.add_edge(0, 1)
    dt.add_edge(1, 2)
    dt.add_edge(2, 3)
    dt.add_edge(3, 4)
    dt.add_edge(4, 1)  # 循环回到1
    
    return dt


if __name__ == "__main__":
    print("=" * 60)
    print("测试1：简单顺序CFG的Dominator树")
    print("=" * 60)
    
    dt1 = create_simple_cfg()
    dt1.build()
    dt1.display()
    
    print("\n支配关系验证:")
    print(f"  Block 3 dominated by Block 0: {dt1.is_dominated_by(3, 0)}")  # True
    print(f"  Block 3 dominated by Block 1: {dt1.is_dominated_by(3, 1)}")  # True
    print(f"  Block 3 dominated by Block 2: {dt1.is_dominated_by(3, 2)}")  # True
    print(f"  Block 3 dominated by Block 4: {dt1.is_dominated_by(3, 4)}")  # False
    print(f"  Block 4 dominated by Block 2: {dt1.is_dominated_by(4, 2)}")  # False
    
    print(f"\n最近公共支配者(3, 4): Block {dt1.find_common_dominator(3, 4)}")
    
    print("\n" + "=" * 60)
    print("测试2：带循环CFG的Dominator树")
    print("=" * 60)
    
    dt2 = create_loop_cfg()
    dt2.build()
    dt2.display()
    
    print("\n支配边界（用于SSA phi函数放置）:")
    for i in range(5):
        df = dt2.get_dominance_frontier(i)
        print(f"  Block {i}: DF = {{{', '.join(str(d) for d in sorted(df))}}}")
    
    print("\nDominator树测试完成!")
