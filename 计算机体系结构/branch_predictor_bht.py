# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构 / branch_predictor_bht



本文件实现 branch_predictor_bht 相关的算法功能。

"""



# 分支历史表容量（BHT条目的数量）

BHT_SIZE = 1024



# 饱和计数器状态枚举

class SaturatingCounter:

    """2位饱和计数器，4个状态表示分支预测强度"""

    STRONG_NOT_TAKEN = 0  # 强不跳：计数器值为0

    WEAK_NOT_TAKEN = 1    # 弱不跳：计数器值为1

    WEAK_TAKEN = 2        # 弱跳：计数器值为2

    STRONG_TAKEN = 3      # 强跳：计数器值为3





class BranchPredictorBHT:

    """

    基于BHT的分支预测器

    使用饱和计数器（2位）预测分支是否被采取

    """



    def __init__(self, size=BHT_SIZE):

        # bht_entries: 分支历史表，每个条目是一个饱和计数器值(0-3)

        self.bht_entries = [0] * size

        # 记录预测统计

        self.total_predictions = 0

        self.correct_predictions = 0



    def _get_index(self, pc):

        """

        根据PC计算BHT索引

        使用PC的低位作为索引（哈希）

        """

        return pc % len(self.bht_entries)



    def predict(self, pc):

        """

        预测给定PC的分支是否被采取

        param pc: 程序计数器地址

        return: True表示预测跳，False表示预测不跳

        """

        index = self._get_index(pc)

        counter = self.bht_entries[index]

        # 计数器值 >= 2 预测为跳

        return counter >= 2



    def update(self, pc, actual_taken):

        """

        根据实际分支结果更新饱和计数器

        param pc: 程序计数器地址

        param actual_taken: 实际是否跳转为True

        """

        index = self._get_index(pc)

        counter = self.bht_entries[index]



        if actual_taken:

            # 实际跳转：计数器递增，上限为3

            self.bht_entries[index] = min(3, counter + 1)

        else:

            # 实际不跳：计数器递减，下限为0

            self.bht_entries[index] = max(0, counter - 1)



    def update_prediction_result(self, pc, actual_taken):

        """

        更新预测统计信息

        param pc: 程序计数器地址

        param actual_taken: 实际分支结果

        """

        self.total_predictions += 1

        predicted_taken = self.predict(pc)

        if predicted_taken == actual_taken:

            self.correct_predictions += 1



    def get_accuracy(self):

        """

        获取预测准确率

        return: 准确率百分比

        """

        if self.total_predictions == 0:

            return 0.0

        return 100.0 * self.correct_predictions / self.total_predictions





class BimodalPredictor:

    """

    双峰预测器 (Bimodal Predictor)

    使用两个独立的BHT，一个用于预测跳转，一个用于预测不跳，

    选择哪个BHT取决于分支的全局历史。

    这是最简单的双峰预测器实现。

    """



    def __init__(self, size=BHT_SIZE):

        # bht_taken: 预测跳转的BHT

        self.bht_taken = [0] * size

        # bht_not_taken: 预测不跳的BHT

        self.bht_not_taken = [0] * size

        # 选择器：决定使用哪个BHT (0=not_taken更好, 1=taken更好)

        self.bht_selector = [1] * size

        # 预测统计

        self.total_predictions = 0

        self.correct_predictions = 0



    def _get_index(self, pc):

        """根据PC哈希获取索引"""

        return pc % len(self.bht_taken)



    def predict(self, pc):

        """

        预测分支是否跳转

        param pc: 程序计数器地址

        return: True表示预测跳

        """

        index = self._get_index(pc)

        # 根据选择器决定使用哪个BHT

        if self.bht_selector[index] == 0:

            # 使用bht_not_taken的预测

            return self.bht_not_taken[index] >= 2

        else:

            # 使用bht_taken的预测

            return self.bht_taken[index] >= 2



    def update(self, pc, actual_taken):

        """

        更新双峰预测器

        param pc: 程序计数器地址

        param actual_taken: 实际是否跳转

        """

        index = self._get_index(pc)



        # 更新被选中的BHT

        if self.bht_selector[index] == 0:

            # 更新bht_not_taken

            counter = self.bht_not_taken[index]

            if actual_taken:

                self.bht_not_taken[index] = min(3, counter + 1)

            else:

                self.bht_not_taken[index] = max(0, counter - 1)

            # 如果实际跳转，选择器向taken方向移动

            if actual_taken and self.bht_selector[index] < 3:

                self.bht_selector[index] += 1

            elif not actual_taken and self.bht_selector[index] > 0:

                self.bht_selector[index] -= 1

        else:

            # 更新bht_taken

            counter = self.bht_taken[index]

            if actual_taken:

                self.bht_taken[index] = min(3, counter + 1)

            else:

                self.bht_taken[index] = max(0, counter - 1)

            # 选择器调整

            if actual_taken and self.bht_selector[index] < 3:

                self.bht_selector[index] += 1

            elif not actual_taken and self.bht_selector[index] > 0:

                self.bht_selector[index] -= 1



    def update_prediction_result(self, pc, actual_taken):

        """更新预测统计"""

        self.total_predictions += 1

        if self.predict(pc) == actual_taken:

            self.correct_predictions += 1





def simulate_branch_predictor():

    """

    模拟分支预测器行为

    演示BHT和双峰预测器的工作过程

    """

    print("=" * 60)

    print("分支预测器模拟 - BHT饱和计数器")

    print("=" * 60)



    # 创建BHT预测器

    predictor = BranchPredictorBHT(size=16)



    # 模拟分支历史序列

    # (pc, actual_taken): PC地址和实际是否跳转

    branch_history = [

        (0x1000, True),   # 第一次见到此PC，跳转

        (0x1000, True),   # 再次跳转，计数器增加到强跳

        (0x1000, False),  # 不跳，计数器减少

        (0x2000, False),  # 新PC，不跳

        (0x2000, False),  # 再次不跳

        (0x1000, True),   # 回到0x1000，跳转

        (0x3000, True),   # 新PC，跳转

        (0x1000, True),   # 跳转

    ]



    print("\n模拟分支执行序列:")

    print("-" * 40)

    for pc, actual in branch_history:

        predicted = predictor.predict(pc)

        predictor.update(pc, actual)

        result = "✓正确" if predicted == actual else "✗错误"

        print(f"PC=0x{pc:04X} | 预测:{predicted} | 实际:{actual} | {result}")



    print(f"\n总预测次数: {predictor.total_predictions}")

    print(f"正确次数: {predictor.correct_predictions}")

    print(f"准确率: {predictor.get_accuracy():.1f}%")



    print("\n" + "=" * 60)

    print("双峰预测器模拟")

    print("=" * 60)



    bimodal = BimodalPredictor(size=16)

    print("\n双峰预测器分支执行:")

    for pc, actual in branch_history:

        predicted = bimodal.predict(pc)

        bimodal.update(pc, actual)

        result = "✓" if predicted == actual else "✗"

        print(f"PC=0x{pc:04X} | 预测:{predicted} | 实际:{actual} | {result}")



    print(f"\n双峰准确率: {100.0 * bimodal.correct_predictions / bimodal.total_predictions:.1f}%")





if __name__ == "__main__":

    simulate_branch_predictor()

