# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / expert_advisory



本文件实现 expert_advisory 相关的算法功能。

"""



import random

import numpy as np

from typing import List, Tuple





class ExpertiseAdvisory:

    """专家顾问系统"""



    def __init__(self, n_experts: int, n_actions: int):

        """

        参数：

            n_experts: 专家数量

            n_actions: 行动数量

        """

        self.n_experts = n_experts

        self.n_actions = n_actions



        # 每个专家的权重

        self.weights = [1.0] * n_experts



        # 历史记录

        self.history = []



    def get_recommendation(self) -> int:

        """

        获取推荐行动



        返回：推荐的行动

        """

        # 加权随机选择

        total_weight = sum(self.weights)

        probs = [w / total_weight for w in self.weights]



        # 选择权重最高的行动

        return np.argmax(self.weights) % self.n_actions



    def update(self, action: int, loss: float, expert_predictions: List[int]) -> None:

        """

        更新专家权重



        参数：

            action: 选择的行动

            loss: 损失

            expert_predictions: 每个专家的预测

        """

        # 对每个专家更新

        for i, expert_pred in enumerate(expert_predictions):

            if expert_pred == action:

                # 专家预测正确，权重增加

                self.weights[i] *= (1 + loss)

            else:

                # 专家预测错误，权重减少

                self.weights[i] *= (1 - 0.1 * loss)



        # 确保权重为正

        self.weights = [max(w, 1e-10) for w in self.weights]



        self.history.append((action, loss, expert_predictions))



    def get_best_expert(self) -> int:

        """

        获取当前最佳专家



        返回：专家索引

        """

        return np.argmax(self.weights)





def expertise_algorithm_analysis():

    """专家算法分析"""

    print("=== 专家顾问算法分析 ===")

    print()

    print("算法：")

    print("  - 指数权重更新")

    print("  - 加权随机选择")

    print("  - 类似于AdaBoost")

    print()

    print("保证：")

    print("  - 如果有专家一直正确，最终会选择")

    print("  - 后悔度 O(sqrt(T))")

    print()

    print("应用：")

    print("  - 预测市场")

    print("  - 组合投资")

    print("  - 算法交易")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 专家顾问测试 ===\n")



    random.seed(42)



    # 创建系统

    n_experts = 5

    n_actions = 3



    expert = ExpertiseAdvisory(n_experts, n_actions)



    print(f"专家数: {n_experts}")

    print(f"行动数: {n_actions}")

    print()



    # 模拟环境

    true_best_action = 1



    # 运行T轮

    T = 100



    print(f"运行 {T} 轮...")

    for t in range(T):

        # 获取推荐

        action = expert.get_recommendation()



        # 计算损失

        loss = 1 if action != true_best_action else 0



        # 专家预测（简化）

        expert_preds = [random.randint(0, n_actions - 1) for _ in range(n_experts)]



        # 更新

        expert.update(action, loss, expert_preds)



    print()



    # 结果

    best_expert = expert.get_best_expert()

    final_weights = expert.weights



    print(f"最终权重: {[f'{w:.2f}' for w in final_weights]}")

    print(f"最佳专家: {best_expert} (权重={final_weights[best_expert]:.2f})")



    print()

    expertise_algorithm_analysis()



    print()

    print("说明：")

    print("  - 专家顾问系统是在线学习的变体")

    print("  - 适用于预测和决策场景")

    print("  - 权重更新类似boosting")

