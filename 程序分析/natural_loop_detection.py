# -*- coding: utf-8 -*-
"""
支配树构建（Dominator Tree Construction）
功能：构建程序的支配关系树

支配关系：
- d dom n: 从入口到n的所有路径都经过d
- idom(n): n的直接支配者（最近的父亲节点）

算法：Lengauer-Tarjan（最快） 或 简单迭代算法

作者：Dominator Tree Team
"""

from typing import List, Dict, Set, Optional
from collections import defaultdict


class DominatorTree:
    """
    支配树构建器
    """

    def __init__(self):
        self.idom: Dict[int, int] = {}  # node → immediate dominator
        self.dom_tree: Dict[int, List[int]] = defaultdict(list)  # dominator → children

    def build(self, cfg: 'CFG', entry_id: int) -> Dict[int, int]:
        """
        构建支配树
        
        使用简化的迭代算法
        
        Returns:
            idom映射
        """
        nodes = [b.id for b in cfg.blocks]
        
        # 初始化：除入口外所有节点都暂时支配自己
        dom_sets: Dict[int, Set[int]] = {}
        for n in nodes:
            if n == entry_id:
                dom_sets[n] = {n}
            else:
                dom_sets[n] = set(nodes)

        # 迭代直到不动点
        changed = True
        while changed:
            changed = False
            for n in nodes:
                if n == entry_id:
                    continue
                
                # 新支配者 = (∩ predecessors' dom) ∪ {n}
                new_dom = None
                preds = cfg.blocks[n].preds if hasattr(cfg.blocks[n], 'preds') else []
                
                if preds:
                    for p in preds:
                        if p.id in dom_sets:
                            if new_dom is None:
                                new_dom = set(dom_sets[p.id])
                            else:
                                new_dom &= dom_sets[p.id]
                
                if new_dom is None:
                    new_dom = set()
                
                new_dom.add(n)
                
                if new_dom != dom_sets[n]:
                    dom_sets[n] = new_dom
                    changed = True
        
        # 计算直接支配者
        for n in nodes:
            if n == entry_id:
                self.idom[n] = n
                continue
            
            doms = dom_sets[n] - {n}
            if doms:
                # 直接支配者是dom集中最接近的
                self.idom[n] = max(doms, key=lambda x: len(dom_sets[x]))
        
        # 构建树
        for n, parent in self.idom.items():
            if n != parent:
                self.dom_tree[parent].append(n)
        
        return self.idom

    def get_ancestors(self, node_id: int) -> Set[int]:
        """获取节点的所有祖先（支配者）"""
        ancestors = set()
        current = node_id
        while current in self.idom:
            parent = self.idom[current]
            if parent == current:
                break
            ancestors.add(parent)
            current = parent
        return ancestors


class CFG:
    """简化CFG"""
    def __init__(self):
        self.blocks: List = []


def example_dominator_tree():
    """支配树构建示例"""
    builder = DominatorTree()
    
    # 简单CFG
    class Block:
        def __init__(self, bid, preds=None, succs=None):
            self.id = bid
            self.preds = preds or []
            self.succs = succs or []
    
    b1 = Block(1, [], [2])
    b2 = Block(2, [1], [3])
    b3 = Block(3, [2], [4])
    b4 = Block(4, [3])
    
    cfg = CFG()
    cfg.blocks = [b1, b2, b3, b4]
    
    idom = builder.build(cfg, 1)
    
    print("支配树:")
    for node, parent in idom.items():
        print(f"  idom({node}) = {parent}")


if __name__ == "__main__":
    print("=" * 50)
    print("支配树构建 测试")
    print("=" * 50)
    example_dominator_tree()
