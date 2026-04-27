# -*- coding: utf-8 -*-

"""

算法实现：差分隐私 / local_privacy



本文件实现 local_privacy 相关的算法功能。

"""



import random

import hashlib

from typing import List, Tuple





class LocalDifferentialPrivacy:

    """本地差分隐私"""



    def __init__(self, epsilon: float):

        """

        参数：

            epsilon: 隐私预算

        """

        self.epsilon = epsilon

        self.p = 1.0 / (1.0 + self._exp_epsilon())



    def _exp_epsilon(self) -> float:

        """计算 e^ε"""

        import math

        return math.exp(self.epsilon)



    def random_response(self, value: int, domain_size: int = 2) -> int:

        """

        随机响应



        参数：

            value: 真实值

            domain_size: 值域大小



        返回：扰动后的值

        """

        # 以概率 p 保持真实值

        if random.random() < self.p:

            return value

        else:

            # 以概率 1-p 随机选择其他值

            others = [i for i in range(domain_size) if i != value]

            return random.choice(others)



    def k_rr_encode(self, value: int, k: int) -> int:

        """

        k-RR编码



        参数：

            value: 真实值

            k: 编码基数



        返回：编码值

        """

        # 概率 p 返回真实值

        if random.random() < self.p:

            return value % k

        else:

            # 随机返回其他值

            return random.randint(0, k - 1)



    def estimate_frequency(self, observations: List[int],

                          domain_size: int,

                          n_total: int) -> List[float]:

        """

        从扰动数据估计频率



        参数：

            observations: 扰动后的观测

            domain_size: 值域大小

            n_total: 总样本数



        返回：频率估计

        """

        counts = [0] * domain_size



        for obs in observations:

            # 反转随机响应

            # P(obs = v) = p * I{v = true} + (1-p) * 1/k

            # 所以 true 的概率需要校正

            for true_val in range(domain_size):

                if self._probability_match(true_val, obs, domain_size):

                    counts[true_val] += 1



        # 校正计数

        adjusted = []

        for count in counts:

            # 校正公式

            adj_count = (count - (1 - self.p) * n_total / domain_size) / self.p

            adjusted.append(max(0, adj_count))



        # 归一化

        total = sum(adjusted)

        if total > 0:

            adjusted = [c / total for c in adjusted]



        return adjusted



    def _probability_match(self, true_val: int, obs: int, k: int) -> bool:

        """判断是否可能匹配"""

        if true_val == obs:

            return random.random() < self.p

        else:

            return random.random() < (1 - self.p) / (k - 1)





def ldp_applications():

    """LDP应用"""

    print("=== LDP应用 ===")

    print()

    print("1. Chrome遥测")

    print("   - 谷歌使用LDP收集用户数据")

    print("   - 保护用户隐私")

    print()

    print("2. 苹果键盘")

    print("   - 预测下一个词")

    print("   - 使用本地隐私保护")

    print()

    print("3. 联邦学习")

    print("   - 结合LDP保护梯度")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 本地差分隐私测试 ===\n")



    epsilon = 1.0

    ldp = LocalDifferentialPrivacy(epsilon)



    print(f"隐私预算: ε = {epsilon}")

    print(f"保持概率: p = {ldp.p:.4f}")

    print()



    # 随机响应

    n = 1000

    true_values = [0] * 600 + [1] * 400  # 60% 是0



    perturbed = [ldp.random_response(v, 2) for v in true_values]



    print(f"真实分布: 0={true_values.count(0)}, 1={true_values.count(1)}")

    print(f"扰动分布: 0={perturbed.count(0)}, 1={perturbed.count(1)}")

    print()



    # 估计

    estimate = ldp.estimate_frequency(perturbed, 2, n)

    print(f"频率估计: 0={estimate[0]:.3f}, 1={estimate[1]:.3f}")

    print(f"真实频率: 0=0.600, 1=0.400")



    print()

    ldp_applications()



    print()

    print("说明：")

    print("  - 本地差分隐私是最强隐私保护")

    print("  - 不需要可信第三方")

    print("  - 代价是估计精度降低")

