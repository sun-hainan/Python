# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 07_privacy_budget



本文件实现 07_privacy_budget 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional

from dataclasses import dataclass

from enum import Enum





class PrivacyMechanism(Enum):

    """隐私机制类型"""

    LAPLACE = "laplace"

    GAUSSIAN = "gaussian"

    EXPONENTIAL = "exponential"

    RANDOMIZED_RESPONSE = "randomized_response"





@dataclass

class PrivacyParameters:

    """

    隐私参数



    Attributes:

        epsilon: ε参数,隐私损失上界

        delta: δ参数,失败概率

        mechanism: 使用的机制

        sensitivity: 查询敏感度

    """

    epsilon: float

    delta: float

    mechanism: PrivacyMechanism

    sensitivity: float = 1.0





class PrivacyBudget:

    """

    隐私预算管理器



    追踪和管理隐私消耗

    """



    def __init__(

        self,

        total_epsilon: float,

        total_delta: float = 0.0

    ):

        """

        初始化隐私预算



        Args:

            total_epsilon: 总ε预算

            total_delta: 总δ预算

        """

        self.total_epsilon = total_epsilon

        self.total_delta = total_delta

        self.spent_epsilon = 0.0

        self.spent_delta = 0.0

        self.query_history = []



    def spend(self, params: PrivacyParameters) -> bool:

        """

        花费隐私预算



        Args:

            params: 隐私参数



        Returns:

            是否成功(预算是否足够)

        """

        new_epsilon = self.spent_epsilon + params.epsilon

        new_delta = self.spent_delta + params.delta



        if new_epsilon > self.total_epsilon:

            return False

        if new_delta > self.total_delta:

            return False



        self.spent_epsilon = new_epsilon

        self.spent_delta = new_delta

        self.query_history.append(params)



        return True



    def get_remaining(self) -> Tuple[float, float]:

        """

        获取剩余预算



        Returns:

            (剩余ε, 剩余δ)

        """

        return (

            self.total_epsilon - self.spent_epsilon,

            self.total_delta - self.spent_delta

        )



    def get_spent(self) -> Tuple[float, float]:

        """

        获取已花费预算



        Returns:

            (已花费ε, 已花费δ)

        """

        return (self.spent_epsilon, self.spent_delta)





class PrivacyAccountant:

    """

    高级隐私会计



    使用精确的会计方法追踪隐私消耗

    """



    def __init__(self, epsilon: float, delta: float = 1e-5):

        """

        初始化隐私会计



        Args:

            epsilon: 目标ε

            delta: 目标δ

        """

        self.target_epsilon = epsilon

        self.target_delta = delta

        self.queries = []



    def add_gaussian_query(

        self,

        sigma: float,

        sensitivity: float,

        steps: int = 1

    ):

        """

        添加高斯机制查询



        使用RDP( Rényi Differential Privacy)会计



        Args:

            sigma: 噪声标准差

            sensitivity: L2敏感度

            steps: 查询次数

        """

        # 计算RDP的α和ε

        alpha = 1 + sensitivity / sigma

        epsilon_rdp = (sensitivity ** 2) / (2 * sigma ** 2)



        self.queries.append({

            "type": "gaussian",

            "sigma": sigma,

            "sensitivity": sensitivity,

            "alpha": alpha,

            "epsilon_rdp": epsilon_rdp,

            "steps": steps

        })



    def add_laplace_query(

        self,

        b: float,

        sensitivity: float,

        steps: int = 1

    ):

        """

        添加拉普拉斯机制查询



        Args:

            b: 拉普拉斯尺度参数

            sensitivity: L1敏感度

            steps: 查询次数

        """

        epsilon = sensitivity / b



        self.queries.append({

            "type": "laplace",

            "b": b,

            "sensitivity": sensitivity,

            "epsilon": epsilon,

            "steps": steps

        })



    def compute_epsilon(self) -> float:

        """

        计算当前累积的ε(使用强组合定理)



        Returns:

            累积的ε

        """

        total_epsilon = 0.0



        for query in self.queries:

            if query["type"] == "laplace":

                total_epsilon += query["epsilon"] * query["steps"]

            elif query["type"] == "gaussian":

                total_epsilon += query["epsilon_rdp"] * query["steps"]



        return total_epsilon



    def compute_delta(self, epsilon: float) -> float:

        """

        计算给定ε对应的δ



        Args:

            epsilon: ε值



        Returns:

            δ值

        """

        # 简化:使用线性估计

        current_epsilon = self.compute_epsilon()

        if current_epsilon == 0:

            return 0.0



        ratio = epsilon / current_epsilon

        return self.target_delta * ratio



    def is_within_budget(self, query_epsilon: float) -> bool:

        """

        检查查询是否在预算内



        Args:

            query_epsilon: 本次查询的ε



        Returns:

            是否可以执行

        """

        return self.compute_epsilon() + query_epsilon <= self.target_epsilon





class PrivacyCalibrator:

    """

    隐私校准器



    根据目标隐私参数校准噪声

    """



    @staticmethod

    def calibrate_laplace(

        epsilon: float,

        sensitivity: float

    ) -> float:

        """

        校准拉普拉斯机制参数



        b = sensitivity / epsilon



        Args:

            epsilon: 目标ε

            sensitivity: 敏感度



        Returns:

            拉普拉斯尺度参数b

        """

        return sensitivity / epsilon



    @staticmethod

    def calibrate_gaussian(

        epsilon: float,

        delta: float,

        sensitivity: float

    ) -> float:

        """

        校准高斯机制参数



        σ = √(2ln(1.25/δ)) * sensitivity / ε



        Args:

            epsilon: 目标ε

            delta: 目标δ

            sensitivity: 敏感度



        Returns:

            高斯噪声标准差σ

        """

        import math

        coefficient = math.sqrt(2 * math.log(1.25 / delta))

        sigma = coefficient * sensitivity / epsilon

        return sigma





class AdvancedComposition:

    """

    高级组合定理



    提供更紧的隐私保证

    """



    @staticmethod

    def compose_gaussian(

        epsilon: float,

        delta: float,

        num_queries: int

    ) -> Tuple[float, float]:

        """

        组合多个高斯机制查询



        使用强组合定理:

        ε' = ε * √(2k * ln(1/δ'))

        δ' = k * δ + δ'



        Args:

            epsilon: 单次查询的ε

            delta: 单次查询的δ

            num_queries: 查询次数



        Returns:

            (组合后ε, 组合后δ)

        """

        import math



        # 使用紧组合界

        delta_prime = delta * num_queries + 1e-10

        epsilon_composed = epsilon * np.sqrt(2 * num_queries * np.log(1 / delta_prime))



        return epsilon_composed, delta_prime



    @staticmethod

    def compose_laplace(

        epsilon: float,

        num_queries: int,

        delta: float = 0.0

    ) -> float:

        """

        组合多个拉普拉斯机制查询



        简单组合: ε_total = k * ε



        Args:

            epsilon: 单次查询的ε

            num_queries: 查询次数

            delta: 目标δ(用于紧界)



        Returns:

            组合后ε

        """

        # 简单组合

        simple_epsilon = epsilon * num_queries



        if delta > 0:

            # 使用紧界

            import math

            tight_epsilon = epsilon * np.sqrt(2 * num_queries * np.log(1 / delta))

            return tight_epsilon



        return simple_epsilon





class PrivacyBudgetManager:

    """

    隐私预算管理器



    完整的预算管理解决方案

    """



    def __init__(

        self,

        initial_epsilon: float,

        initial_delta: float = 1e-5,

        accounting_method: str = "simple"

    ):

        """

        初始化预算管理器



        Args:

            initial_epsilon: 初始ε预算

            initial_delta: 初始δ预算

            accounting_method: 会计方法,"simple"或"advanced"

        """

        self.initial_epsilon = initial_epsilon

        self.initial_delta = initial_delta

        self.accounting_method = accounting_method



        self.budget = PrivacyBudget(initial_epsilon, initial_delta)

        self.accountant = PrivacyAccountant(initial_epsilon, initial_delta)



        self.query_count = 0



    def query(

        self,

        mechanism: PrivacyMechanism,

        sensitivity: float,

        epsilon: float = None,

        delta: float = None

    ) -> Optional[Dict]:

        """

        执行差分隐私查询



        Args:

            mechanism: 隐私机制

            sensitivity: 敏感度

            epsilon: 隐私预算(可选)

            delta: 失败概率(可选)



        Returns:

            查询结果或None(如果超出预算)

        """

        if epsilon is None:

            epsilon = self.initial_epsilon / 10  # 默认分配



        params = PrivacyParameters(

            epsilon=epsilon,

            delta=delta or 0.0,

            mechanism=mechanism,

            sensitivity=sensitivity

        )



        # 检查预算

        if not self.budget.spend(params):

            return None



        # 计算噪声参数

        if mechanism == PrivacyMechanism.LAPLACE:

            b = PrivacyCalibrator.calibrate_laplace(epsilon, sensitivity)

            result = {"mechanism": "laplace", "b": b, "spent": epsilon}

        elif mechanism == PrivacyMechanism.GAUSSIAN:

            if delta is None:

                delta = self.initial_delta

            sigma = PrivacyCalibrator.calibrate_gaussian(epsilon, delta, sensitivity)

            result = {"mechanism": "gaussian", "sigma": sigma, "spent": epsilon}

        else:

            result = {"mechanism": "other", "spent": epsilon}



        self.query_count += 1

        return result



    def get_status(self) -> Dict:

        """

        获取预算状态



        Returns:

            状态字典

        """

        remaining_epsilon, remaining_delta = self.budget.get_remaining()

        spent_epsilon, spent_delta = self.budget.get_spent()



        return {

            "query_count": self.query_count,

            "total_epsilon": self.initial_epsilon,

            "spent_epsilon": spent_epsilon,

            "remaining_epsilon": remaining_epsilon,

            "utilization": spent_epsilon / self.initial_epsilon if self.initial_epsilon > 0 else 0,

            "accounting_method": self.accounting_method

        }





def demonstrate_privacy_budget():

    """

    演示隐私预算管理

    """



    print("隐私预算(ε-δ差分隐私)演示")

    print("=" * 60)



    np.random.seed(42)



    # 1. 基础预算管理

    print("\n1. 隐私预算管理")

    manager = PrivacyBudgetManager(

        initial_epsilon=10.0,

        initial_delta=1e-5,

        accounting_method="simple"

    )



    # 模拟多次查询

    true_count = 100

    sensitivity = 1.0



    results = []

    for i in range(10):

        result = manager.query(

            mechanism=PrivacyMechanism.LAPLACE,

            sensitivity=sensitivity,

            epsilon=0.5

        )



        if result:

            # 添加拉普拉斯噪声

            noisy_count = true_count + np.random.laplace(0, result["b"])

            results.append(noisy_count)

            print(f"   查询 {i+1}: ε消耗{result['spent']:.2f}, "

                  f"加噪结果: {noisy_count:.2f}")

        else:

            print(f"   查询 {i+1}: 超出预算!")



    # 2. 预算状态

    print("\n2. 预算状态")

    status = manager.get_status()

    print(f"   查询次数: {status['query_count']}")

    print(f"   总ε预算: {status['total_epsilon']:.2f}")

    print(f"   已消耗ε: {status['spent_epsilon']:.2f}")

    print(f"   剩余ε: {status['remaining_epsilon']:.2f}")

    print(f"   利用率: {status['utilization']*100:.1f}%")



    # 3. 高级组合

    print("\n3. 高级组合定理")

    epsilon, delta = AdvancedComposition.compose_gaussian(

        epsilon=1.0,

        delta=1e-5,

        num_queries=100

    )

    print(f"   100次高斯查询组合后: ε={epsilon:.4f}, δ={delta:.2e}")



    composed_eps = AdvancedComposition.compose_laplace(

        epsilon=1.0,

        num_queries=100,

        delta=1e-5

    )

    print(f"   100次拉普拉斯查询组合后: ε={composed_eps:.4f}")



    # 4. 隐私校准

    print("\n4. 隐私参数校准")

    sensitivity = 1.0



    b = PrivacyCalibrator.calibrate_laplace(epsilon=1.0, sensitivity=sensitivity)

    print(f"   拉普拉斯机制: ε=1.0, 敏感度=1.0 → b={b:.4f}")



    sigma = PrivacyCalibrator.calibrate_gaussian(

        epsilon=1.0, delta=1e-5, sensitivity=sensitivity

    )

    print(f"   高斯机制: ε=1.0, δ=1e-5, 敏感度=1.0 → σ={sigma:.4f}")



    # 5. RDP会计

    print("\n5. Rényi差分隐私(RDP)会计")

    accountant = PrivacyAccountant(epsilon=10.0, delta=1e-5)



    for i in range(5):

        sigma = PrivacyCalibrator.calibrate_gaussian(

            epsilon=1.0, delta=1e-5, sensitivity=1.0

        )

        accountant.add_gaussian_query(sigma=sigma, sensitivity=1.0)



    current_eps = accountant.compute_epsilon()

    print(f"   5次高斯查询后的累积ε: {current_eps:.4f}")





if __name__ == "__main__":

    demonstrate_privacy_budget()



    print("\n" + "=" * 60)

    print("隐私预算演示完成!")

    print("=" * 60)

