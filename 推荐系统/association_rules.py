# -*- coding: utf-8 -*-
"""
算法实现：推荐系统 / association_rules

本文件实现 association_rules 相关的算法功能。
"""

from collections import defaultdict, Counter
from itertools import combinations


class AprioriAlgorithm:
    """Apriori关联规则挖掘算法"""

    def __init__(self, min_support=0.1, min_confidence=0.5):
        """
        初始化Apriori算法

        Args:
            min_support: float 最小支持度阈值
            min_confidence: float 最小置信度阈值
        """
        self.min_support = min_support  # 最小支持度
        self.min_confidence = min_confidence  # 最小置信度
        self.frequent_itemsets = []  # 频繁项集列表
        self.association_rules = []  # 关联规则列表
        self.transaction_count = 0  # 事务总数

    def fit(self, transactions):
        """
        从事务数据库挖掘频繁项集和关联规则

        Args:
            transactions: list of set/list 事务数据库，每行是一个事务（物品集合）
        """
        self.transaction_count = len(transactions)  # 记录事务总数
        min_count = self.min_support * self.transaction_count  # 最小支持度对应的计数

        # 第一步：找到所有频繁1-项集
        item_counts = Counter()
        for transaction in transactions:
            for item in transaction:
                item_counts[item] += 1  # 统计每个物品的出现次数

        # 过滤得到频繁1-项集
        current_frequent = {
            frozenset([item]): count
            for item, count in item_counts.items()
            if count >= min_count
        }

        self.frequent_itemsets.append(current_frequent)  # L1

        # 逐层搜索频繁k-项集 (k >= 2)
        k = 2
        while current_frequent:
            # 生成候选k-项集（通过合并频繁(k-1)项集）
            candidates = self._generate_candidates(list(current_frequent.keys()), k)

            # 统计候选k-项集的支持度计数
            candidate_counts = Counter()
            for transaction in transactions:
                # 找出事务中包含的候选项集
                for candidate in candidates:
                    if candidate.issubset(transaction):
                        candidate_counts[candidate] += 1

            # 过滤得到频繁k-项集
            current_frequent = {
                candidate: count
                for candidate, count in candidate_counts.items()
                if count >= min_count
            }

            if current_frequent:
                self.frequent_itemsets.append(current_frequent)  # Lk

            k += 1

        # 第二步：从频繁项集生成关联规则
        self._generate_rules()

    def _generate_candidates(self, frequent_itemsets, k):
        """
        通过合并频繁(k-1)项集生成候选k-项集

        Apriori性质：如果一个项集是频繁的，那么它的所有子集也必须是频繁的
        因此可以剪枝：只保留前(k-1)项相同的项集对

        Args:
            frequent_itemsets: list of frozenset 频繁(k-1)项集列表
            k: int 目标项集大小

        Returns:
            set of frozenset 候选k-项集
        """
        candidates = set()  # 候选项集集合

        # 两两合并
        for i in range(len(frequent_itemsets)):
            for j in range(i + 1, len(frequent_itemsets)):
                # 合并：取两个项集的并集
                union = frequent_itemsets[i] | frequent_itemsets[j]

                # 只保留大小为k的并集
                if len(union) != k:
                    continue

                # Apriori剪枝：检查所有(k-1)子集是否都是频繁的
                is_valid = True
                for item in union:
                    subset = union - {item}
                    if subset not in self.frequent_itemsets[-1]:
                        is_valid = False
                        break

                if is_valid:
                    candidates.add(union)  # 添加有效候选

        return candidates

    def _generate_rules(self):
        """从频繁项集生成关联规则"""
        self.association_rules = []  # 清空规则列表

        # 遍历每个频繁项集（从2-项集开始）
        for k in range(1, len(self.frequent_itemsets)):
            for itemset, support in self.frequent_itemsets[k].items():
                if len(itemset) < 2:
                    continue  # 至少需要2个元素才能生成规则

                # 生成所有非空真子集作为规则前件
                for subset_size in range(1, len(itemset)):
                    for antecedent in combinations(itemset, subset_size):
                        antecedent = frozenset(antecedent)  # 规则前件
                        consequent = itemset - antecedent  # 规则后件

                        # 计算置信度：confidence = support(itemset) / support(antecedent)
                        antecedent_support = self._get_support(antecedent)
                        if antecedent_support == 0:
                            continue

                        confidence = support / antecedent_support

                        if confidence >= self.min_confidence:
                            # 计算提升度
                            consequent_support = self._get_support(consequent)
                            lift = confidence / consequent_support if consequent_support > 0 else 0

                            self.association_rules.append({
                                'antecedent': antecedent,
                                'consequent': consequent,
                                'support': support / self.transaction_count,
                                'confidence': confidence,
                                'lift': lift
                            })

    def _get_support(self, itemset):
        """
        获取项集的支持度计数

        Args:
            itemset: frozenset 项集

        Returns:
            int 支持度计数
        """
        # 在频繁项集列表中查找
        k = len(itemset) - 1
        if k < len(self.frequent_itemsets):
            return self.frequent_itemsets[k].get(itemset, 0)
        return 0

    def get_rules(self, min_lift=None, sort_by='confidence'):
        """
        获取关联规则

        Args:
            min_lift: float 最小提升度过滤
            sort_by: str 排序依据 ('confidence', 'support', 'lift')

        Returns:
            list of dict 关联规则列表
        """
        rules = self.association_rules

        if min_lift is not None:
            rules = [r for r in rules if r['lift'] >= min_lift]

        # 按指定指标排序
        rules.sort(key=lambda x: x[sort_by], reverse=True)
        return rules


class FPGrowthAlgorithm:
    """FP-Growth关联规则挖掘算法（无需生成候选项集）"""

    class FPNode:
        """FP树节点"""
        def __init__(self, item, count=0, parent=None):
            self.item = item  # 节点项
            self.count = count  # 计数
            self.parent = parent  # 父节点
            self.children = {}  # 子节点字典 {item: node}
            self.node_link = None  # 相同项的下一个节点链接

    def __init__(self, min_support=0.1, min_confidence=0.5):
        """
        初始化FP-Growth算法

        Args:
            min_support: float 最小支持度
            min_confidence: float 最小置信度
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.transaction_count = 0
        self.header_table = {}  # 项头表 {item: (count, first_node)}
        self.fp_tree = None  # FP树根节点
        self.frequent_itemsets = []
        self.association_rules = []

    def fit(self, transactions):
        """构建FP树并挖掘频繁项集"""
        self.transaction_count = len(transactions)
        min_count = self.min_support * self.transaction_count

        # 第一次扫描：统计项频率
        item_counts = Counter()
        for transaction in transactions:
            for item in transaction:
                item_counts[item] += 1

        # 过滤非频繁项，按频率降序排序
        frequent_items = {item: count for item, count in item_counts.items()
                         if count >= min_count}

        if not frequent_items:
            return

        # 排序函数：按频率降序，频率相同按字典序
        def sort_key(item):
            return (-frequent_items[item], item)

        # 初始化项头表
        self.header_table = {item: [count, None] for item, count in frequent_items.items()}

        # 第二次扫描：构建FP树
        self.fp_tree = self.FPNode('NULL', 0, None)  # 根节点

        for transaction in transactions:
            # 过滤非频繁项并排序
            filtered_items = [item for item in transaction if item in frequent_items]
            sorted_items = sorted(filtered_items, key=sort_key)

            # 插入到FP树
            self._insert_tree(sorted_items, self.fp_tree)

        # 挖掘频繁项集
        self._mine_frequent_itemsets([])

        # 生成关联规则
        self._generate_rules()

    def _insert_tree(self, items, node):
        """将事务插入FP树"""
        if not items:
            return

        first_item = items[0]  # 第一个项

        # 如果子节点中已有该物品，增加计数；否则创建新节点
        if first_item in node.children:
            node.children[first_item].count += 1
        else:
            new_node = self.FPNode(first_item, 1, node)
            node.children[first_item] = new_node

            # 更新项头表的节点链接
            self._update_header(first_item, new_node)

        # 递归插入剩余项
        self._insert_tree(items[1:], node.children[first_item])

    def _update_header(self, item, node):
        """更新项头表的节点链接"""
        if self.header_table[item][1] is None:
            self.header_table[item][1] = node
        else:
            # 沿链表找到最后一个节点
            current = self.header_table[item][1]
            while current.node_link is not None:
                current = current.node_link
            current.node_link = node

    def _mine_frequent_itemsets(self, alpha):
        """
        递归挖掘频繁项集

        Args:
            alpha: list 当前条件模式基的前缀项集
        """
        # 按频率升序处理项（从最不频繁的项开始）
        items = sorted(
            self.header_table.keys(),
            key=lambda item: self.header_table[item][0]
        )

        for item in items:
            # 生成新的频繁项集 = alpha + item
            new_itemset = [item] + alpha
            support = self.header_table[item][0] / self.transaction_count

            self.frequent_itemsets.append((
                frozenset(new_itemset),
                support
            ))

            # 获取该 item 的条件模式基
            conditional_pattern_base = self._get_conditional_pattern_base(item)

            if conditional_pattern_base:
                # 构建条件FP树
                conditional_tree = self._build_conditional_fp_tree(
                    conditional_pattern_base,
                    self.header_table[item][0]
                )

                if conditional_tree:
                    # 递归挖掘
                    old_header_table = self.header_table
                    self.header_table = self.header_table  # 简化处理
                    self._mine_recursive(conditional_tree, new_itemset)
                    self.header_table = old_header_table

    def _get_conditional_pattern_base(self, item):
        """获取某项的条件模式基（从前缀路径收集）"""
        patterns = []  # 条件模式基列表

        # 沿节点链接遍历所有包含该item的节点
        node = self.header_table[item][1]
        while node is not None:
            # 从当前节点回溯到根节点，收集路径上的项（不含自身和根）
            prefix_path = []
            parent = node.parent
            while parent and parent.item != 'NULL':
                prefix_path.append(parent.item)
                parent = parent.parent

            if prefix_path:
                # 该路径出现次数等于当前节点的计数
                patterns.append((prefix_path, node.count))

            node = node.node_link

        return patterns

    def _build_conditional_fp_tree(self, patterns, min_count):
        """根据条件模式基构建条件FP树"""
        # 统计模式基中各物品的计数
        item_counts = Counter()
        for pattern, count in patterns:
            for item in pattern:
                item_counts[item] += count

        # 过滤不满足最小支持度的项
        frequent_items = {item: count for item, count in item_counts.items()
                         if count >= min_count}

        if not frequent_items:
            return None

        # 创建条件FP树
        root = self.FPNode('NULL', 0, None)

        for pattern, count in patterns:
            # 过滤并排序模式
            filtered_pattern = [item for item in pattern if item in frequent_items]
            filtered_pattern.sort(key=lambda x: -frequent_items[x])

            # 插入树
            self._insert_pattern_tree(filtered_pattern, count, root, frequent_items)

        return root

    def _insert_pattern_tree(self, items, count, node, frequent_items):
        """将条件模式基中的路径插入条件FP树"""
        if not items:
            return

        first_item = items[0]

        if first_item in node.children:
            node.children[first_item].count += count
        else:
            new_node = self.FPNode(first_item, count, node)
            node.children[first_item] = new_node

        self._insert_pattern_tree(items[1:], count, node.children[first_item], frequent_items)

    def _mine_recursive(self, tree, alpha):
        """递归挖掘条件FP树"""
        items = sorted(tree.header_table.keys() if hasattr(tree, 'header_table') else [],
                      key=lambda x: tree.header_table[x][0])

        for item in items:
            new_itemset = [item] + alpha
            support = tree.header_table[item][0] / self.transaction_count
            self.frequent_itemsets.append((frozenset(new_itemset), support))

    def _generate_rules(self):
        """从频繁项集生成关联规则"""
        self.association_rules = []

        for itemset, support in self.frequent_itemsets:
            if len(itemset) < 2:
                continue

            for subset_size in range(1, len(itemset)):
                for antecedent in combinations(itemset, subset_size):
                    antecedent = frozenset(antecedent)
                    consequent = itemset - antecedent

                    # 获取前件和后件的支持度
                    antecedent_support = self._get_support(antecedent)
                    consequent_support = self._get_support(consequent)

                    if antecedent_support == 0:
                        continue

                    confidence = support / antecedent_support

                    if confidence >= self.min_confidence:
                        lift = confidence / consequent_support if consequent_support > 0 else 0
                        self.association_rules.append({
                            'antecedent': antecedent,
                            'consequent': consequent,
                            'support': support,
                            'confidence': confidence,
                            'lift': lift
                        })

    def _get_support(self, itemset):
        """获取项集的支持度"""
        for itemset_f, support in self.frequent_itemsets:
            if itemset_f == itemset:
                return support
        return 0

    def get_rules(self, min_lift=None, sort_by='confidence'):
        """获取关联规则"""
        rules = self.association_rules
        if min_lift is not None:
            rules = [r for r in rules if r['lift'] >= min_lift]
        rules.sort(key=lambda x: x[sort_by], reverse=True)
        return rules


# ------------------- 单元测试 -------------------
if __name__ == '__main__':
    # 购物篮数据
    transactions = [
        {'牛奶', '面包', '尿布'},
        {'可乐', '面包', '尿布', '鸡蛋'},
        {'牛奶', '尿布', '鸡蛋', '面包'},
        {'面包', '鸡蛋'},
        {'牛奶', '面包', '鸡蛋'},
        {'可乐', '尿布', '鸡蛋', '面包'},
        {'牛奶', '面包', '尿布'},
        {'可乐', '面包', '尿布', '鸡蛋'},
        {'牛奶', '可乐', '面包', '尿布', '鸡蛋'},
        {'可乐', '面包', '尿布'},
    ]

    print("=" * 60)
    print("测试 Apriori 算法")
    print("=" * 60)

    apriori = AprioriAlgorithm(min_support=0.2, min_confidence=0.5)
    apriori.fit(transactions)

    print(f"\n频繁项集数量: {sum(len(f) for f in apriori.frequent_itemsets)}")
    print("\n频繁项集:")
    for k, itemsets in enumerate(apriori.frequent_itemsets):
        print(f"  L{k+1}: {itemsets}")

    print("\n关联规则:")
    rules = apriori.get_rules(sort_by='confidence')
    for rule in rules[:10]:
        print(f"  {set(rule['antecedent'])} -> {set(rule['consequent'])}")
        print(f"      支持度={rule['support']:.3f}, 置信度={rule['confidence']:.3f}, 提升度={rule['lift']:.3f}")

    print("\n" + "=" * 60)
    print("测试 FP-Growth 算法")
    print("=" * 60)

    fpgrowth = FPGrowthAlgorithm(min_support=0.2, min_confidence=0.5)
    fpgrowth.fit(transactions)

    print(f"\n频繁项集数量: {len(fpgrowth.frequent_itemsets)}")
    print("\n关联规则:")
    rules = fpgrowth.get_rules(sort_by='confidence')
    for rule in rules[:10]:
        print(f"  {set(rule['antecedent'])} -> {set(rule['consequent'])}")
        print(f"      支持度={rule['support']:.3f}, 置信度={rule['confidence']:.3f}, 提升度={rule['lift']:.3f}")

    print("\n✅ 关联规则挖掘算法测试通过！")
