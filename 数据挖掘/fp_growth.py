# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / fp_growth

本文件实现 fp_growth 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, Counter


class FPGrowth:
    """FP-Growth 频繁项集挖掘"""

    class Node:
        """FP-Tree 节点"""
        def __init__(self, item, count=0, parent=None):
            self.item = item  # 项名
            self.count = count  # 计数
            self.parent = parent  # 父节点
            self.children = {}  # 子节点字典 {item: node}
            self.node_link = None  # 相同项的下一个节点

    def __init__(self, min_support=0.1):
        self.min_support = min_support
        self.header_table = {}  # item -> 第一个节点指针
        self.frequent_itemsets = []

    def _build_fptree(self, transactions, item_counts):
        """构建 FP-Tree"""
        root = self.Node(None)
        min_count = self.min_support * len(transactions)

        for txn in transactions:
            # 过滤并按频率降序排序
            filtered = [item for item in txn if item_counts[item] >= min_count]
            filtered.sort(key=lambda x: item_counts[x], reverse=True)
            current = root
            for item in filtered:
                if item in current.children:
                    current.children[item].count += 1
                else:
                    node = self.Node(item, 1, current)
                    current.children[item] = node
                    # 更新 header table 的节点链
                    if self.header_table.get(item) is None:
                        self.header_table[item] = node
                    else:
                        link = self.header_table[item]
                        while link.node_link:
                            link = link.node_link
                        link.node_link = node
                current = current.children[item]

        return root

    def _get_prefix_path(self, node):
        """获取从节点到根的前缀路径"""
        path = []
        current = node.parent
        while current and current.item:
            path.append(current.item)
            current = current.parent
        return path

    def _mine_fptree(self, tree, prefix, min_count):
        """递归挖掘 FP-Tree"""
        if tree is None:
            return

        # 按频率升序遍历 header_table（低频先处理）
        sorted_items = sorted(self.header_table.keys(),
                              key=lambda x: self.item_counts.get(x, 0))
        for item in sorted_items:
            if self.item_counts.get(item, 0) < min_count:
                continue
            # 生成新的频繁项集
            new_pattern = prefix + [item]
            self.frequent_itemsets.append((tuple(new_pattern), self.item_counts[item] / self.n_transactions))

            # 收集条件模式基
            conditional_base = []
            node = self.header_table.get(item)
            while node:
                prefix_path = self._get_prefix_path(node)
                if prefix_path:
                    conditional_base.extend([prefix_path] * node.count)
                node = node.node_link

            if not conditional_base:
                continue

            # 构建条件 FP-Tree
            cond_item_counts = Counter()
            for base in conditional_base:
                for it in base:
                    cond_item_counts[it] += 1

            # 过滤
            cond_freq_items = {it for it, c in cond_item_counts.items() if c >= min_count}
            if not cond_freq_items:
                continue

            # 构建条件树
            class CondNode:
                def __init__(self, item=None, count=0, parent=None):
                    self.item = item
                    self.count = count
                    self.parent = parent
                    self.children = {}

            cond_root = CondNode()
            for base in conditional_base:
                filtered = [it for it in base if it in cond_freq_items]
                filtered.sort(key=lambda x: cond_item_counts[x], reverse=True)
                current = cond_root
                for it in filtered:
                    if it in current.children:
                        current.children[it].count += 1
                    else:
                        current.children[it] = CondNode(it, 1, current)
                    current = current.children[it]

            # 递归挖掘
            self._mine_fptree_cond(cond_root, cond_item_counts, new_pattern, min_count)

    def _mine_fptree_cond(self, tree, item_counts, prefix, min_count):
        """挖掘条件 FP-Tree（简化版）"""
        if tree is None:
            return

        sorted_items = sorted(item_counts.keys(),
                              key=lambda x: item_counts[x])
        for item in sorted_items:
            if item_counts[item] < min_count:
                continue
            new_pattern = prefix + [item]
            self.frequent_itemsets.append((tuple(new_pattern), item_counts[item] / self.n_transactions))

    def fit(self, transactions):
        """挖掘频繁项集"""
        self.n_transactions = len(transactions)
        min_count = self.min_support * self.n_transactions

        # 统计项频率
        self.item_counts = Counter()
        for txn in transactions:
            self.item_counts.update(txn)

        # 构建 FP-Tree
        root = self._build_fptree(transactions, self.item_counts)
        self.tree = root

        # 递归挖掘
        self._mine_fptree(root, [], min_count)

        return self

    def get_frequent_itemsets(self, min_support=None):
        """获取频繁项集"""
        if min_support is not None:
            min_count = min_support * self.n_transactions
            return [(itemset, sup / self.n_transactions)
                    for itemset, sup in self.frequent_itemsets
                    if sup >= min_count]
        return self.frequent_itemsets

    def generate_rules(self, min_confidence=0.5):
        """从频繁项集生成关联规则（简化版）"""
        rules = []
        for itemset, support in self.frequent_itemsets:
            if len(itemset) < 2:
                continue
            itemset_set = set(itemset)
            for i in range(1, len(itemset)):
                from itertools import combinations
                for ante in combinations(itemset, i):
                    ante_set = set(ante)
                    cons_set = itemset_set - ante_set
                    # 找到 antecedent 的支持度
                    ante_sup = next((s for it, s in self.frequent_itemsets
                                     if set(it) == ante_set), 0)
                    if ante_sup > 0:
                        confidence = support / ante_sup
                        if confidence >= min_confidence:
                            lift = confidence / support if support > 0 else 0
                            rules.append((tuple(ante_set), tuple(cons_set),
                                          confidence, support, lift))
        return rules


def demo():
    """FP-Growth 演示"""
    transactions = [
        ["牛奶", "面包", "鸡蛋"],
        ["面包", "尿布", "啤酒", "鸡蛋"],
        ["牛奶", "尿布", "啤酒", "可乐"],
        ["面包", "牛奶", "尿布", "啤酒"],
        ["面包", "牛奶", "尿布", "可乐"],
        ["牛奶", "面包", "尿布", "鸡蛋"],
        ["面包", "尿布", "可乐"],
        ["牛奶", "面包", "尿布", "可乐"],
        ["牛奶", "尿布", "啤酒", "面包"],
        ["鸡蛋", "面包", "牛奶"],
    ]

    print("=== FP-Growth 算法演示 ===")
    fp = FPGrowth(min_support=0.2)
    fp.fit(transactions)

    itemsets = fp.get_frequent_itemsets()
    itemsets_sorted = sorted(itemsets, key=lambda x: x[1], reverse=True)

    print(f"频繁项集总数: {len(itemsets_sorted)}")
    print("\n频繁项集（按支持度排序）:")
    for itemset, support in itemsets_sorted:
        print(f"  {set(itemset)}: 支持度={support:.3f}")

    # 关联规则
    rules = fp.generate_rules(min_confidence=0.5)
    rules_sorted = sorted(rules, key=lambda x: x[2], reverse=True)
    print(f"\n关联规则数: {len(rules_sorted)}")
    print("\n关联规则（按置信度排序）:")
    for ante, cons, conf, sup, lift in rules_sorted[:10]:
        print(f"  {set(ante)} -> {set(cons)}: conf={conf:.3f}, sup={sup:.3f}, lift={lift:.3f}")


if __name__ == "__main__":
    demo()
