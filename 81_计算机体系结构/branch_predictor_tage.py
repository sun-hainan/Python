# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / branch_predictor_tage



本文件实现 branch_predictor_tage 相关的算法功能。

"""



from typing import List, Optional





class TAGETableEntry:

    """

    TAGE表条目

    包含预测计数器和标签

    """

    def __init__(self):

        self.counter = 0          # 预测计数器（0-7，3位饱和）

        self.tag = 0               # 标签（用于匹配）





class TAGEPredictor:

    """

    TAGE (Tagged Geometric History Length) 分支预测器实现



    使用多个历史长度表，基础表使用短历史，备选表使用几何增长的全局历史。

    每个表条目包含一个标签用于验证历史上下文匹配。

    """



    # TAGE组件数量（不包括基础表）

    NUM_COMPONENTS = 4

    # 基础表历史长度（0表示无历史）

    BASE_HISTORY_LEN = 0

    # 各组件的历史长度（几何增长）

    HISTORY_LENGTHS = [4, 8, 16, 32]

    # 标签位数

    TAG_BITS = 10

    # 标签掩码

    TAG_MASK = (1 << TAG_BITS) - 1

    # 计数器最大值（3位）

    MAX_COUNTER = 7



    def __init__(self, table_size=256):

        """

        初始化TAGE预测器

        param table_size: 每个表的大小

        """

        self.table_size = table_size

        # 基础预测表（无历史）

        self.base_table = [TAGETableEntry() for _ in range(table_size)]

        # 带标签的组件表

        self.component_tables = [

            [TAGETableEntry() for _ in range(table_size)]

            for _ in range(self.NUM_COMPONENTS)

        ]

        # 全局分支历史（比特串）

        self.global_history = 0

        self.ghr_length = 0

        # 预测统计

        self.total_predictions = 0

        self.correct_predictions = 0



    def _compute_tag(self, pc: int, history: int) -> int:

        """

        计算给定PC和历史的标签

        标签通过PC和历史异或生成

        param pc: 程序计数器

        param history: 分支历史

        return: 标签值

        """

        return (pc ^ (history * 0x5A)) & self.TAG_MASK



    def _get_index(self, pc: int, history: int, table_idx: int) -> int:

        """

        计算表索引

        混合PC和历史信息生成索引

        """

        h = history & (self.table_size - 1)

        p = pc & (self.table_size - 1)

        return (p ^ h) % self.table_size



    def _get_prediction_from_entry(self, entry: TAGETableEntry) -> bool:

        """

        从条目获取预测

        计数器 >= 4 预测为跳转

        """

        return entry.counter >= 4



    def predict(self, pc: int) -> bool:

        """

        对给定PC进行分支预测

        尝试找到最长历史匹配的分量表

        param pc: 程序计数器地址

        return: True表示预测跳转

        """

        # 基础表预测

        base_idx = pc % self.table_size

        base_pred = self.base_table[base_idx].counter >= 4



        # 在各分量表中寻找标签匹配的条目

        best_pred = base_pred

        best_hit_idx = -1

        history = self.global_history



        for i in range(self.NUM_COMPONENTS):

            hist_len = self.HISTORY_LENGTHS[i]

            # 取历史低hist_len位

            history_bits = history & ((1 << hist_len) - 1)

            idx = self._get_index(pc, history_bits, i)

            entry = self.component_tables[i][idx]



            # 检查标签是否匹配

            tag = self._compute_tag(pc, history_bits)

            if entry.tag == tag:

                # 找到匹配，使用此预测（更长历史优先）

                best_pred = self._get_prediction_from_entry(entry)

                best_hit_idx = i

                break



        return best_pred



    def update(self, pc: int, actual_taken: bool):

        """

        更新TAGE预测器状态

        param pc: 程序计数器地址

        param actual_taken: 实际分支结果

        """

        # 更新全局历史寄存器

        self.global_history = ((self.global_history << 1) | (1 if actual_taken else 0))

        self.ghr_length = min(self.ghr_length + 1, max(self.HISTORY_LENGTHS))



        # 基础表更新

        base_idx = pc % self.table_size

        base_entry = self.base_table[base_idx]

        if actual_taken:

            base_entry.counter = min(self.MAX_COUNTER, base_entry.counter + 1)

        else:

            base_entry.counter = max(0, base_entry.counter - 1)



        # 在分量表中寻找匹配条目进行更新

        history = self.global_history

        matched = False

        hit_table_idx = -1



        for i in range(self.NUM_COMPONENTS):

            hist_len = self.HISTORY_LENGTHS[i]

            history_bits = history & ((1 << hist_len) - 1)

            idx = self._get_index(pc, history_bits, i)

            entry = self.component_tables[i][idx]

            tag = self._compute_tag(pc, history_bits)



            if entry.tag == tag:

                # 匹配，更新计数器

                if actual_taken:

                    entry.counter = min(self.MAX_COUNTER, entry.counter + 1)

                else:

                    entry.counter = max(0, entry.counter - 1)

                matched = True

                hit_table_idx = i

                break



        # 如果没有匹配且不是最长历史的表，在最长历史表中分配新条目

        if not matched:

            # 选择历史最长的分量表

            longest_table_idx = self.NUM_COMPONENTS - 1

            hist_len = self.HISTORY_LENGTHS[longest_table_idx]

            history_bits = history & ((1 << hist_len) - 1)

            idx = self._get_index(pc, history_bits, longest_table_idx)

            entry = self.component_tables[longest_table_idx][idx]



            # 设置标签和初始计数器

            entry.tag = self._compute_tag(pc, history_bits)

            entry.counter = 3 if actual_taken else 0



    def update_and_check(self, pc: int, actual_taken: bool) -> bool:

        """

        更新预测器并检查预测是否正确

        param pc: 程序计数器地址

        param actual_taken: 实际分支结果

        return: 预测是否正确

        """

        predicted = self.predict(pc)

        self.update(pc, actual_taken)

        self.total_predictions += 1

        if predicted == actual_taken:

            self.correct_predictions += 1

            return True

        return False



    def get_accuracy(self) -> float:

        """获取预测准确率"""

        if self.total_predictions == 0:

            return 0.0

        return 100.0 * self.correct_predictions / self.total_predictions





class GBHBPredictor:

    """

    全局分支历史缓冲器 (GBHB) 预测器

    GBHB是一个移位寄存器，存储最近N次分支的结果（跳转/不跳转）

    用于索引分支预测表

    """



    def __init__(self, history_length=16, table_size=256):

        """

        初始化GBHB预测器

        param history_length: 全局历史长度

        param table_size: 预测表大小

        """

        self.history_length = history_length

        self.table_size = table_size

        # 全局分支历史寄存器

        self.global_history = 0

        # 分支预测表

        self.prediction_table = [0] * table_size

        # 统计

        self.total_predictions = 0

        self.correct_predictions = 0



    def _get_index(self, pc: int) -> int:

        """

        根据PC和全局历史计算索引

        """

        # 混合PC和全局历史

        h = self.global_history & (self.table_size - 1)

        p = pc & (self.table_size - 1)

        return (p ^ h) % self.table_size



    def predict(self, pc: int) -> bool:

        """

        预测分支是否跳转

        """

        idx = self._get_index(pc)

        # 计数器 >= 2 预测为跳转

        return self.prediction_table[idx] >= 2



    def update(self, pc: int, actual_taken: bool):

        """

        更新GBHB和预测表

        """

        idx = self._get_index(pc)



        # 更新预测表

        if actual_taken:

            self.prediction_table[idx] = min(3, self.prediction_table[idx] + 1)

        else:

            self.prediction_table[idx] = max(0, self.prediction_table[idx] - 1)



        # 更新全局历史寄存器（左移一位，移入新结果）

        self.global_history = ((self.global_history << 1) | (1 if actual_taken else 0))

        # 限制历史长度

        mask = (1 << self.history_length) - 1

        self.global_history &= mask



    def update_and_check(self, pc: int, actual_taken: bool) -> bool:

        """更新并检查预测正确性"""

        predicted = self.predict(pc)

        self.update(pc, actual_taken)

        self.total_predictions += 1

        if predicted == actual_taken:

            self.correct_predictions += 1

            return True

        return False





def simulate_tage_predictor():

    """

    模拟TAGE和GBHB预测器

    """

    print("=" * 60)

    print("TAGE 分支预测器模拟")

    print("=" * 60)



    tage = TAGEPredictor(table_size=64)



    # 模拟分支序列

    # 某些PC会有固定模式，有些则随机

    import random

    random.seed(42)



    branch_sequence = [

        (0x1000, True),   # 循环分支，每次都跳

        (0x1000, True),

        (0x1000, True),

        (0x1000, False),  # 循环退出

        (0x2000, False),  # 条件不满足

        (0x2000, True),

        (0x3000, True),   # if分支

        (0x3000, True),

        (0x1000, True),   # 再次进入循环

        (0x1000, True),

    ]



    print("\n分支执行序列:")

    print("-" * 50)

    for pc, actual in branch_sequence:

        predicted = tage.predict(pc)

        tage.update(pc, actual)

        result = "✓" if predicted == actual else "✗"

        print(f"PC=0x{pc:04X} | 预测:{'跳' if predicted else '不跳'} | 实际:{'跳' if actual else '不跳'} | {result}")



    print(f"\nTAGE准确率: {tage.get_accuracy():.1f}%")



    print("\n" + "=" * 60)

    print("GBHB 预测器模拟")

    print("=" * 60)



    gbhb = GBHBPredictor(history_length=8, table_size=64)



    for pc, actual in branch_sequence:

        predicted = gbhb.predict(pc)

        gbhb.update(pc, actual)

        result = "✓" if predicted == actual else "✗"

        print(f"PC=0x{pc:04X} | 预测:{'跳' if predicted else '不跳'} | 实际:{'跳' if actual else '不跳'} | {result}")



    acc = 100.0 * gbhb.correct_predictions / gbhb.total_predictions if gbhb.total_predictions > 0 else 0

    print(f"\nGBHB准确率: {acc:.1f}%")





if __name__ == "__main__":

    simulate_tage_predictor()

