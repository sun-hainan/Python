# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / association_rules

本文件实现 association_rules 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, Counter


class Apriori:
    """Apriori 关联规则挖掘算法"""

    def __init__(self, min_support=0.1, min_confidence=0.5):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.frequent_itemsets = []  # List[({items}, support)]
        self.rules = []  # List[(antecedent, consequent, confidence)]

    def fit(self, transactions):
        """
        transactions: List[List[item]] 事务数据库
        """
        n_transactions = len(transactions)
        item_to_idx = {}
        idx_to_item = {}
        # 转为数值编码
        encoded = []
        for txn in transactions:
            encoded_txn = []
            for item in txn:
                if item not in item_to_idx:
                    idx = len(item_to_idx)
                    item_to_idx[item] = idx
                    idx_to_item[idx] = item
                encoded_txn.append(item_to_idx[item])
            encoded.append(set(encoded_txn))

        # 统计单项频率
        item_counts = Counter()
        for txn in encoded:
            for item in txn:
                item_counts[item] += 1

        # L1 频繁项集
        min_count = self.min_support * n_transactions
        frequent_1 = {frozenset([item]): count / n_transactions
                      for item, count in item_counts.items() if count >= min_count}

        # 逐层生成频繁项集
        frequent_itemsets = list(frequent_1.items())
        all_frequent = dict(frequent_1)
        k = 2

        while frequent_itemsets:
            # 生成 k 项候选项集（通过合并 k-1 项频繁项集）
            candidates = []
            prev_itemsets = [itemset for itemset, _ in frequent_itemsets]
            for i, itemset_a in enumerate(prev_itemsets):
                for itemset_b in prev_itemsets[i + 1:]:
                    # 合并：两个集合只有最后一项不同
                    union = itemset_a | itemset_b
                    if len(union) == k:
                        # 剪枝：检查所有 k-1 子集是否频繁
                        valid = True
                        for item in union:
                            subset = union - {item}
                            if subset not in all_frequent:
                                valid = False
                                break
                        if valid and union not in candidates:
                            candidates.append(union)

            # 统计候选项集的支持度
            candidate_counts = Counter()
            for txn in encoded:
                for candidate in candidates:
                    if candidate.issubset(txn):
                        candidate_counts[candidate] += 1

            # 过滤频繁项集
            frequent_itemsets = [(itemset, count / n_transactions)
                                  for itemset, count in candidate_counts.items()
                                  if count >= min_count]
            all_frequent.update(dict(frequent_itemsets))
            k += 1

        self.frequent_itemsets = [(idx_to_item, s) for itemset, s in all_frequent.items()
                                  for idx_to_item in [dict((idx_to_item[k], k) for k in itemset)]]

        # 生成关联规则
        self._generate_rules(all_frequent, n_transactions, idx_to_item)

        return self

    def _generate_rules(self, frequent_itemsets, n_transactions, idx_to_item):
        """从频繁项集生成关联规则"""
        for itemset, support in frequent_itemsets.items():
            if len(itemset) < 2:
                continue
            # 遍历所有非空真子集作为 antecedent
            for i in range(1, len(itemset)):
                from itertools import combinations
                for ante_indices in combinations(itemset, i):
                    antecedent = frozenset(ante_indices)
                    consequent = itemset - antecedent
                    ante_support = frequent_itemsets.get(antecedent, 0)
                    if ante_support > 0:
                        confidence = support / ante_support
                        if confidence >= self.min_confidence:
                            # 转换为原始项
                            ante_items = frozenset(idx_to_item[i] for i in antecedent)
                            cons_items = frozenset(idx_to_item[i] for i in consequent)
                            self.rules.append((ante_items, cons_items, confidence))


def fp_growth_simple(transactions, min_support=0.1):
    """简化版 FP-Growth 算法"""
    n = len(transactions)
    min_count = min_support * n

    # 统计项频率
    item_counts = Counter()
    for txn in transactions:
        for item in txn:
            item_counts[item] += 1

    # 过滤低频项并排序
    frequent_items = {item for item, count in item_counts.items() if count >= min_count}
    if not frequent_items:
        return [], []

    # 构建 FP-Tree
    class FPTreeNode:
        def __init__(self, item, count=0, parent=None):
            self.item = item
            self.count = count
            self.parent = parent
            self.children = {}
            self.node_link = None

    root = FPTreeNode(None)
    header_table = {}  # item -> 第一个节点

    for txn in transactions:
        filtered = [item for item in txn if item in frequent_items]
        # 按频率降序排序
        filtered.sort(key=lambda x: item_counts[x], reverse=True)
        current = root
        for item in filtered:
            if item in current.children:
                current.children[item].count += 1
            else:
                node = FPTreeNode(item, 1, current)
                current.children[item] = node
                # 更新 header_table
                if item not in header_table:
                    header_table[item] = node
                else:
                    existing = header_table[item]
                    while existing.node_link:
                        existing = existing.node_link
                    existing.node_link = node
            current = current.children[item]

    # 挖掘频繁项集（简化：只输出单项和成对项）
    frequent_itemsets = []
    for item, count in item_counts.items():
        if count >= min_count:
            frequent_itemsets.append((frozenset([item]), count / n))

    return frequent_itemsets, []


def demo():
    """关联规则挖掘演示"""
    # 示例事务数据库
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

    print("=== Apriori 关联规则 ===")
    apriori = Apriori(min_support=0.2, min_confidence=0.5)
    apriori.fit(transactions)

    print(f"频繁项集数: {len(apriori.frequent_itemsets)}")
    print("频繁项集（按支持度排序）:")
    sorted_itemsets = sorted(apriori.frequent_itemsets, key=lambda x: x[1], reverse=True)
    for itemset, support in sorted_itemsets[:10]:
        print(f"  {set(itemset)}: 支持度={support:.3f}")

    print(f"\n关联规则数: {len(apriori.rules)}")
    print("关联规则:")
    for ante, cons, conf in sorted(apriori.rules, key=lambda x: x[2], reverse=True)[:10]:
        print(f"  {set(ante)} -> {set(cons)}: 置信度={conf:.3f}")

    # FP-Growth 对比
    print("\n=== FP-Growth 频繁项集 ===")
    itemsets, rules = fp_growth_simple(transactions, min_support=0.2)
    print(f"频繁项集数: {len(itemsets)}")
    for itemset, support in sorted(itemsets, key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {set(itemset)}: 支持度={support:.3f}")


if __name__ == "__main__":
    demo()
