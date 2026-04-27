# -*- coding: utf-8 -*-

"""

算法实现：计算机体系结构_2 / perceptron_branch



本文件实现 perceptron_branch 相关的算法功能。

"""



import random

from typing import List, Optional, Dict

from dataclasses import dataclass





@dataclass

class Perceptron:

    """单层感知器"""

    weights: List[int]          # 权值向量（历史长度+1个）

    history_length: int         # 历史长度

    threshold: int = 6          # 激活阈值





    def __post_init__(self):

        if not self.weights:

            # 初始化权值（可以是0或小随机数）

            self.weights = [0] * (self.history_length + 1)





    def compute_output(self, history: int) -> int:

        """

        计算感知器输出

        y = w0 + sum(wi * xi) for i in 1..n

        其中 x0 = 1（偏置），xi = 历史第i位

        """

        # 偏置

        output = self.weights[0]

        # 历史位点积

        for i in range(self.history_length):

            bit = (history >> i) & 1

            output += self.weights[i + 1] * (1 if bit else -1)

        return output





    def predict(self, history: int) -> bool:

        """基于当前权值预测"""

        return self.compute_output(history) >= 0





    def train(self, history: int, actual: bool, learning_rate: int = 1):

        """训练感知器（使用感知ron学习规则）"""

        output = self.compute_output(history)

        # 期望输出：+1 if taken, -1 if not taken

        desired = 1 if actual else -1

        # 预测错误或输出接近阈值时更新

        if (output >= 0) != actual or abs(output) < self.threshold:

            # 更新权值: wi = wi + lr * (desired - output) * xi

            # 简化：wi = wi + lr * desired * xi

            self.weights[0] += learning_rate * desired * 1  # 偏置

            for i in range(self.history_length):

                bit = (history >> i) & 1

                xi = 1 if bit else -1

                self.weights[i + 1] += learning_rate * desired * xi





class Perceptron_Branch_Predictor:

    """感知器分支预测器"""

    def __init__(self, history_length: int = 16, num_perceptrons: int = 256):

        self.history_length = history_length

        self.num_perceptrons = num_perceptrons

        self.index_mask = num_perceptrons - 1

        # 感知器表

        self.perceptrons: List[Perceptron] = []

        for _ in range(num_perceptrons):

            self.perceptrons.append(Perceptron(weights=[], history_length=history_length))

        # 全局分支历史

        self.global_history: int = 0

        # 统计

        self.total_predictions: int = 0

        self.correct_predictions: int = 0

        # 额外统计

        self.high_confidence_correct: int = 0

        self.low_confidence_correct: int = 0





    def _get_index(self, pc: int) -> int:

        """从PC计算感知器索引"""

        return pc & self.index_mask





    def predict(self, pc: int) -> bool:

        """预测分支方向"""

        idx = self._get_index(pc)

        perceptron = self.perceptrons[idx]

        history = self.global_history

        pred = perceptron.predict(history)

        self.total_predictions += 1

        return pred





    def update(self, pc: int, actual: bool, learning_rate: int = 1):

        """更新预测器"""

        idx = self._get_index(pc)

        perceptron = self.perceptrons[idx]

        history = self.global_history

        # 检查预测是否正确

        pred = perceptron.predict(history)

        if pred == actual:

            self.correct_predictions += 1

            # 高置信度正确（输出绝对值大）

            if abs(perceptron.compute_output(history)) >= perceptron.threshold * 2:

                self.high_confidence_correct += 1

            else:

                self.low_confidence_correct += 1

        # 训练感知器

        perceptron.train(history, actual, learning_rate)

        # 更新全局历史

        self.global_history = ((self.global_history << 1) | (1 if actual else 0)) & ((1 << self.history_length) - 1)





    def get_accuracy(self) -> float:

        """获取预测准确率"""

        if self.total_predictions == 0:

            return 0.0

        return self.correct_predictions / self.total_predictions





class Hybrid_Perceptron_Predictor:

    """混合感知器预测器（结合多种历史长度）"""

    def __init__(self):

        # 多个不同历史长度的感知器预测器

        self.predictors: List[Perceptron_Branch_Predictor] = [

            Perceptron_Branch_Predictor(history_length=8, num_perceptrons=256),

            Perceptron_Branch_Predictor(history_length=16, num_perceptrons=256),

            Perceptron_Branch_Predictor(history_length=32, num_perceptrons=256),

        ]

        # 选择器（两位饱和计数器）

        self.selector: List[int] = [1] * 256  # 0=predictor0, 1=predictor1, 2=predictor2

        self.total_predictions: int = 0

        self.correct_predictions: int = 0





    def predict(self, pc: int) -> bool:

        """使用选择器选择预测器进行预测"""

        sel_idx = pc & 0xFF

        chosen = self.selector[sel_idx] % len(self.predictors)

        return self.predictors[chosen].predict(pc)





    def update(self, pc: int, actual: bool):

        """更新混合预测器"""

        sel_idx = pc & 0xFF

        # 更新所有感知器

        for i, pred in enumerate(self.predictors):

            pred.update(pc, actual)

        # 更新选择器

        # 选择最佳预测器

        best_idx = 0

        best_accuracy = 0.0

        for i, pred in enumerate(self.predictors):

            if pred.total_predictions > 0:

                acc = pred.correct_predictions / pred.total_predictions

                if acc > best_accuracy:

                    best_accuracy = acc

                    best_idx = i

        # 更新选择器计数器偏向最佳预测器

        current = self.selector[sel_idx]

        if current < best_idx:

            self.selector[sel_idx] = min(len(self.predictors) - 1, current + 1)

        elif current > best_idx:

            self.selector[sel_idx] = max(0, current - 1)

        self.total_predictions += 1

        if self.predict(pc) == actual:

            self.correct_predictions += 1





def basic_test():

    """基本功能测试"""

    print("=== 感知器分支预测器测试 ===")

    predictor = Perceptron_Branch_Predictor(history_length=16, num_perceptrons=256)

    print(f"历史长度: {predictor.history_length}")

    print(f"感知器数量: {predictor.num_perceptrons}")

    # 模拟分支序列

    print("\n模拟200条分支:")

    num_branches = 200

    branches = []

    for i in range(num_branches):

        # 模拟一些有规律的分支

        if i % 10 == 0:

            taken = True

        elif i % 5 == 0:

            taken = False

        else:

            taken = random.random() < 0.6

        branches.append(taken)

    for i, actual in enumerate(branches[:50]):  # 只显示前50条

        pred = predictor.predict(0x1000 + i * 4)

        predictor.update(0x1000 + i * 4, actual)

        match = "✓" if pred == actual else "✗"

        print(f"  分支{i:3d}: 预测={'T' if pred else 'N'}, 实际={'T' if actual else 'N'} {match}")

    print(f"\n统计:")

    print(f"  总预测: {predictor.total_predictions}")

    print(f"  正确: {predictor.correct_predictions}")

    print(f"  准确率: {predictor.get_accuracy():.2%}")

    print(f"  高置信度正确: {predictor.high_confidence_correct}")

    print(f"  低置信度正确: {predictor.low_confidence_correct}")

    # 测试混合预测器

    print("\n" + "=" * 50)

    print("\n混合感知器预测器测试:")

    hybrid = Hybrid_Perceptron_Predictor()

    for i in range(100):

        actual = random.random() < 0.7

        hybrid.update(0x1000 + i * 4, actual)

    print(f"  总预测: {hybrid.total_predictions}")

    print(f"  正确: {hybrid.correct_predictions}")

    print(f"  准确率: {hybrid.correct_predictions / hybrid.total_predictions:.2%}")





if __name__ == "__main__":

    basic_test()

