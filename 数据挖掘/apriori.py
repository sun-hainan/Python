# -*- coding: utf-8 -*-
"""
算法实现：数据挖掘 / apriori

本文件实现 apriori 相关的算法功能。
"""

import itertools
from typing import List, Dict, Set, Tuple, FrozenSet
from collections import defaultdict


class Apriori:
    """
    Apriori算法实现
    
    参数:
        min_support: 最小支持度（0-1之间的比例）
        min_confidence: 最小置信度
    """
    
    def __init__(self, min_support: float = 0.01, min_confidence: float = 0.5):
        self.min_support = min_support
        self.min_confidence = min_confidence
        
        # 频繁项集
        self.frequent_itemsets: List[Dict[FrozenSet, float]] = []  # 按长度组织的频繁项集
        
        # 关联规则
        self.rules: List[Tuple[FrozenSet, FrozenSet, float, float]] = []  # ( antecedent, consequent, support, confidence )
        
        # 统计
        self.n_transactions = 0
        self.candidate_count = 0
        self.scan_count = 0
    
    def fit(self, transactions: List[List]) -> 'Apriori':
        """
        从交易数据中挖掘频繁项集和关联规则
        
        参数:
            transactions: 交易列表，每笔交易是item列表
        """
        self.n_transactions = len(transactions)
        self.frequent_itemsets = []
        self.rules = []
        
        # 获取所有唯一的item
        item_set = set()
        for trans in transactions:
            item_set.update(trans)
        
        # 转换为frozenset以便哈希
        trans_set = [frozenset(t) for t in transactions]
        
        # L1: 找出所有频繁1-项集
        L1, item_counts = self._get_L1(trans_set, item_set)
        
        if not L1:
            return self
        
        # 保存L1
        self.frequent_itemsets.append({
            frozenset([item]): count / self.n_transactions
            for item, count in item_counts.items()
        })
        
        # 逐层搜索
        Lk = L1  # 当前层的频繁项集
        
        while Lk:
            # 生成候选(k+1)-项集
            Ck_plus_1 = self._generate_candidates(Lk)
            self.candidate_count += len(Ck_plus_1)
            
            # 计数支持度
            item_counts = self._count_support(trans_set, Ck_plus_1)
            
            # 找出频繁项集
            min_count = self.min_support * self.n_transactions
            Lk_plus_1 = {
                itemset: count for itemset, count in item_counts.items()
                if count >= min_count
            }
            
            if Lk_plus_1:
                self.frequent_itemsets.append({
                    itemset: count / self.n_transactions
                    for itemset, count in Lk_plus_1.items()
                })
                
                # 生成关联规则
                self._generate_rules(Lk_plus_1, trans_set)
            
            Lk = Lk_plus_1
            self.scan_count += 1
        
        return self
    
    def _get_L1(self, trans_set: List[FrozenSet], item_set: Set) -> Tuple[List[FrozenSet], Dict[FrozenSet, int]]:
        """生成频繁1-项集"""
        item_counts = defaultdict(int)
        
        for trans in trans_set:
            for item in trans:
                item_counts[frozenset([item])] += 1
        
        min_count = self.min_support * self.n_transactions
        L1 = [frozenset([item]) for item, count in item_counts.items() if count >= min_count]
        
        return L1, dict(item_counts)
    
    def _generate_candidates(self, Lk: List[FrozenSet]) -> Set[FrozenSet]:
        """
        通过连接生成候选(k+1)-项集
        
        连接条件：两个k-项集前k-1个元素相同
        """
        Ck_plus_1 = set()
        k = len(Lk[0]) if Lk else 1
        
        # 连接
        for i, itemset1 in enumerate(Lk):
            for itemset2 in Lk[i+1:]:
                # 检查前k-1个元素
                if list(itemset1)[:-1] == list(itemset2)[:-1]:
                    # 连接：合并两个项集
                    new_itemset = itemset1 | itemset2
                    if len(new_itemset) == k + 1:
                        Ck_plus_1.add(new_itemset)
        
        # 先验剪枝：移除含非频繁子集的候选项
        if k > 0:
            pruned = set()
            for itemset in Ck_plus_1:
                # 检查所有k-1子集是否都频繁
                valid = True
                for subset in itertools.combinations(itemset, k):
                    if frozenset(subset) not in Lk:
                        valid = False
                        break
                if valid:
                    pruned.add(itemset)
            
            return pruned
        
        return Ck_plus_1
    
    def _count_support(self, trans_set: List[FrozenSet], candidates: Set[FrozenSet]) -> Dict[FrozenSet, int]:
        """计算候选项的支持度计数"""
        counts = defaultdict(int)
        
        for trans in trans_set:
            for candidate in candidates:
                if candidate.issubset(trans):
                    counts[candidate] += 1
        
        return dict(counts)
    
    def _generate_rules(self, Lk: Dict[FrozenSet, int], trans_set: List[FrozenSet]) -> None:
        """从频繁项集生成关联规则"""
        for itemset, itemset_count in Lk.items():
            if len(itemset) < 2:
                continue
            
            # 生成所有非空真子集
            for i in range(1, len(itemset)):
                for antecedent in itertools.combinations(itemset, i):
                    antecedent = frozenset(antecedent)
                    consequent = itemset - antecedent
                    
                    if not consequent:
                        continue
                    
                    # 计算置信度
                    # 需要antecedent的支持度
                    antecedent_count = sum(1 for trans in trans_set if antecedent.issubset(trans))
                    
                    if antecedent_count > 0:
                        confidence = itemset_count / antecedent_count
                        
                        if confidence >= self.min_confidence:
                            support = itemset_count / self.n_transactions
                            self.rules.append((antecedent, consequent, support, confidence))
    
    def get_frequent_itemsets(self, min_length: int = 1, max_length: int = None) -> List[Tuple[FrozenSet, float]]:
        """获取频繁项集"""
        result = []
        max_len = max_length or len(self.frequent_itemsets)
        
        for length in range(min_length - 1, max_len):
            if length < len(self.frequent_itemsets):
                for itemset, support in self.frequent_itemsets[length].items():
                    result.append((itemset, support))
        
        return result
    
    def get_rules(self, min_confidence: float = None) -> List[Tuple[FrozenSet, FrozenSet, float, float]]:
        """获取关联规则"""
        if min_confidence is None:
            return self.rules
        
        return [(a, c, s, conf) for a, c, s, conf in self.rules if conf >= min_confidence]
    
    def print_results(self) -> None:
        """打印结果"""
        print("=" * 50)
        print("频繁项集:")
        print("=" * 50)
        
        for i, itemset_dict in enumerate(self.frequent_itemsets):
            print(f"\n长度 {i+1} 的频繁项集 ({len(itemset_dict)} 个):")
            for itemset, support in sorted(itemset_dict.items(), key=lambda x: -x[1])[:5]:
                print(f"  {set(itemset)}: 支持度 = {support:.4f}")
            if len(itemset_dict) > 5:
                print(f"  ... 还有 {len(itemset_dict) - 5} 个")
        
        print("\n" + "=" * 50)
        print("关联规则:")
        print("=" * 50)
        
        for antecedent, consequent, support, confidence in sorted(self.rules, key=lambda x: -x[3])[:10]:
            print(f"  {set(antecedent)} -> {set(consequent)}")
            print(f"    支持度 = {support:.4f}, 置信度 = {confidence:.4f}")


def generate_synthetic_data(n_transactions: int, n_items: int, avg_basket_size: int) -> List[List]:
    """
    生成合成交易数据
    
    参数:
        n_transactions: 交易数量
        n_items: 商品种类数
        avg_basket_size: 平均购物篮大小
    """
    import random
    
    random.seed(42)
    
    # 创建商品ID
    items = [f"item_{i}" for i in range(n_items)]
    
    transactions = []
    for _ in range(n_transactions):
        # 随机选择若干商品
        basket_size = max(1, int(random.gauss(avg_basket_size, avg_basket_size / 3)))
        basket_size = min(basket_size, n_items)
        
        basket = random.sample(items, basket_size)
        transactions.append(basket)
    
    return transactions


# ==================== 测试代码 ====================
if __name__ == "__main__":
    print("=" * 50)
    print("Apriori关联规则算法测试")
    print("=" * 50)
    
    # 测试数据：购物篮数据
    transactions = [
        ['milk', 'bread', 'eggs'],
        ['bread', 'butter'],
        ['milk', 'bread', 'butter', 'eggs'],
        ['bread', 'eggs'],
        ['milk', 'eggs'],
        ['bread', 'milk', 'eggs'],
        ['butter', 'eggs'],
        ['milk', 'bread', 'butter'],
        ['bread', 'eggs'],
        ['milk', 'butter', 'eggs'],
    ]
    
    print(f"\n交易数量: {len(transactions)}")
    print(f"示例交易: {transactions[:3]}")
    
    # 运行Apriori
    print("\n--- 运行Apriori (min_support=0.2, min_confidence=0.6) ---")
    
    apriori = Apriori(min_support=0.2, min_confidence=0.6)
    apriori.fit(transactions)
    
    apriori.print_results()
    
    print("\n--- 算法统计 ---")
    print(f"交易数: {apriori.n_transactions}")
    print(f"候选集总数: {apriori.candidate_count}")
    print(f"扫描次数: {apriori.scan_count}")
    
    # 合成数据测试
    print("\n" + "=" * 50)
    print("合成大数据测试")
    print("=" * 50)
    
    import time
    
    # 生成大规模测试数据
    n_trans = 10000
    n_items = 100
    avg_size = 10
    
    print(f"生成数据: {n_trans} 笔交易, {n_items} 种商品, 平均篮大小 {avg_size}")
    
    synthetic = generate_synthetic_data(n_trans, n_items, avg_size)
    
    # 运行Apriori
    apriori2 = Apriori(min_support=0.01, min_confidence=0.5)
    
    start = time.time()
    apriori2.fit(synthetic)
    elapsed = time.time() - start
    
    print(f"\n运行时间: {elapsed:.3f}秒")
    print(f"频繁项集数量: {sum(len(d) for d in apriori2.frequent_itemsets)}")
    print(f"关联规则数量: {len(apriori2.rules)}")
    
    # 按长度统计
    print("\n按长度统计频繁项集:")
    for i, itemset_dict in enumerate(apriori2.frequent_itemsets):
        print(f"  长度 {i+1}: {len(itemset_dict)} 个")
    
    # 前5条规则
    print("\n前5条规则:")
    for a, c, s, conf in apriori2.rules[:5]:
        print(f"  {set(a)} -> {set(c)} (sup={s:.3f}, conf={conf:.3f})")
    
    # 性能对比：不同min_support
    print("\n--- 性能对比 (不同min_support) ---")
    
    for min_sup in [0.05, 0.02, 0.01, 0.005]:
        ap = Apriori(min_support=min_sup, min_confidence=0.5)
        
        start = time.time()
        ap.fit(synthetic)
        elapsed = time.time() - start
        
        total_itemsets = sum(len(d) for d in ap.frequent_itemsets)
        print(f"  min_sup={min_sup}: {elapsed:.3f}秒, {total_itemsets}频繁项集, {len(ap.rules)}规则")
