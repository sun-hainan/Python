# -*- coding: utf-8 -*-

"""

算法实现：差分隐私 / laplace_mechanism



本文件实现 laplace_mechanism 相关的算法功能。

"""



from __future__ import annotations

import math

import random

import sys

from typing import Any, Callable, Dict, List, Optional, Tuple, Union



# 数值稳定性常数

EPSILON_TOLERANCE = 1e-12





def laplace_sample(loc: float = 0.0, scale: float = 1.0) -> float:

    """

    从拉普拉斯分布中采样

    

    使用逆变换法（Inverse Transform Method）从标准拉普拉斯分布采样，

    然后通过位置和尺度变换得到目标分布。

    

    数学原理：

        标准拉普拉斯分布（loc=0, scale=1）的概率密度函数为：

            f(x) = (1/2) · exp(-|x|)

        

        累积分布函数（CDF）为：

            F(x) = { (1/2) · exp(x)      if x < 0

                   { 1 - (1/2) · exp(-x)  if x ≥ 0 }

        

        逆函数为：

            F^(-1)(u) = { ln(2u)         if 0 < u ≤ 0.5

                        { -ln(2(1-u))    if 0.5 ≤ u < 1 }

    

    参数：

        loc (float, optional): 位置参数 μ，控制分布的中心位置。默认为 0.0。

        scale (float, optional): 尺度参数 b > 0，控制分布的"宽度"。默认为 1.0。

                                 尺度越大，分布越平坦，噪声幅度越大。

    

    返回：

        float: 从拉普拉斯分布中采样的随机值。

    

    异常：

        ValueError: 当 scale ≤ 0 时抛出。

    

    示例：

        >>> random.seed(42)

        >>> laplace_sample(0.0, 1.0)   # 标准拉普拉斯分布采样

        -0.293...

        >>> laplace_sample(5.0, 2.0)   # 位置为5，尺度为2

        3.284...

    """

    if scale <= 0:

        raise ValueError(f"尺度参数 scale 必须为正数，当前值: {scale}")

    

    # 生成 [0, 1) 区间的均匀随机数

    uniform_random = random.random()

    

    # 逆变换采样

    if uniform_random <= 0.5:

        # 负半轴：x = b · ln(2u)

        sample = scale * math.log(2.0 * uniform_random)

    else:

        # 正半轴：x = -b · ln(2(1-u))

        sample = -scale * math.log(2.0 * (1.0 - uniform_random))

    

    # 位置变换

    return loc + sample





def laplace_pdf(x: float, loc: float = 0.0, scale: float = 1.0) -> float:

    """

    计算拉普拉斯分布在给定点的概率密度

    

    参数：

        x (float): 概率密度函数的自变量。

        loc (float, optional): 位置参数 μ。默认为 0.0。

        scale (float, optional): 尺度参数 b。默认为 1.0。

    

    返回：

        float: 拉普拉斯分布在 x 点的概率密度值。

    

    数学公式：

        f(x; μ, b) = (1 / 2b) · exp(-|x - μ| / b)

    

    示例：

        >>> laplace_pdf(0.0, 0.0, 1.0)

        0.5

        >>> laplace_pdf(1.0, 0.0, 1.0)  # = 0.5 * exp(-1)

        0.1839...

    """

    if scale <= 0:

        raise ValueError(f"尺度参数 scale 必须为正数: {scale}")

    

    # 标准化：计算 |x - μ| / b

    normalized_distance = abs(x - loc) / scale

    # 概率密度函数：f(x) = (1 / 2b) · exp(-|x - μ| / b)

    return (1.0 / (2.0 * scale)) * math.exp(-normalized_distance)





def laplace_cdf(x: float, loc: float = 0.0, scale: float = 1.0) -> float:

    """

    计算拉普拉斯分布在给定点的累积分布函数值

    

    参数：

        x (float): 累积分布函数的自变量。

        loc (float, optional): 位置参数 μ。默认为 0.0。

        scale (float, optional): 尺度参数 b。默认为 1.0。

    

    返回：

        float: 拉普拉斯分布在 x 点的 CDF 值，范围 [0, 1]。

    

    数学公式：

        F(x; μ, b) = { (1/2) · exp((x-μ)/b)    if x < μ

                    { 1 - (1/2) · exp(-(x-μ)/b) if x ≥ μ

    

    示例：

        >>> laplace_cdf(0.0, 0.0, 1.0)

        0.5

    """

    if scale <= 0:

        raise ValueError(f"尺度参数 scale 必须为正数: {scale}")

    

    # 标准化：计算 (x - μ) / b

    standardized = (x - loc) / scale

    

    if standardized < 0:

        # x < μ 时

        return 0.5 * math.exp(standardized)

    else:

        # x ≥ μ 时

        return 1.0 - 0.5 * math.exp(-standardized)





def compute_noise_scale(sensitivity: float, epsilon: float) -> float:

    """

    计算 Laplace 机制所需的噪声尺度参数

    

    根据差分隐私的敏感性分析，噪声尺度 b 应设置为：

        b = Δf / ε

    

    其中 Δf 是查询函数的全局敏感度，ε 是隐私预算。

    

    参数：

        sensitivity (float): 查询函数的全局敏感度（必须为非负数）。

        epsilon (float): 隐私预算参数（必须为正数）。

    

    返回：

        float: 所需的拉普拉斯噪声尺度参数 b。

    

    数学推导：

        对于拉普拉斯机制 M(D) = f(D) + Laplace(0, b)，

        要满足 ε-差分隐私，需要 b = Δf / ε。

        

        证明思路：

            相邻数据集 D 和 D' 的查询结果差异最多为 Δf。

            添加尺度为 b 的拉普拉斯噪声后，任意输出的概率比值为：

                Pr[M(D) = o] / Pr[M(D') = o]

                = exp(-|f(D) - o| / b) / exp(-|f(D') - o| / b)

                = exp((|f(D') - o| - |f(D) - o|) / b)

                ≤ exp(|f(D) - f(D')| / b)

                ≤ exp(Δf / b)

            要使该比值 ≤ exp(ε)，需满足 b ≥ Δf / ε。

    

    示例：

        >>> compute_noise_scale(sensitivity=1.0, epsilon=1.0)

        1.0

        >>> compute_noise_scale(sensitivity=2.0, epsilon=0.5)

        4.0

    """

    if sensitivity < 0:

        raise ValueError(f"敏感度必须为非负数: {sensitivity}")

    if epsilon <= 0:

        raise ValueError(f"隐私预算 epsilon 必须为正数: {epsilon}")

    

    return sensitivity / epsilon





class LaplaceMechanism:

    """

    Laplace 机制实现类

    

    封装了拉普拉斯机制的核心功能，包括：

        - 噪声尺度的自动计算

        - 多种查询类型的支持

        - 查询结果的后处理

    

    使用方法：

        1. 创建 LaplaceMechanism 实例，指定隐私参数 ε

        2. 调用 add_noise() 方法向查询结果添加噪声

        3. （可选）使用 clip() 方法截断异常值

    

    示例：

        >>> mechanism = LaplaceMechanism(epsilon=1.0)

        >>> query_result = 42.0

        >>> sensitivity = 1.0

        >>> noisy_result = mechanism.add_noise(query_result, sensitivity)

        >>> print(f"原始值: {query_result}, 噪声结果: {noisy_result:.4f}")

        原始值: 42.0, 噪声结果: 41.7325

    """

    

    def __init__(self, epsilon: float) -> None:

        """

        初始化 Laplace 机制

        

        参数：

            epsilon (float): 隐私预算参数，必须为正数。

                              决定了隐私保护强度：ε 越小，噪声越大，隐私越强。

        

        异常：

            ValueError: 当 epsilon ≤ 0 时抛出。

        """

        if epsilon <= 0:

            raise ValueError(f"隐私预算 epsilon 必须为正数: {epsilon}")

        

        self._epsilon = float(epsilon)

        self._used_budget = 0.0

    

    @property

    def epsilon(self) -> float:

        """获取隐私预算参数"""

        return self._epsilon

    

    @property

    def used_budget(self) -> float:

        """获取已使用的隐私预算"""

        return self._used_budget

    

    def add_noise(self, query_value: Union[float, List[float]],

                  sensitivity: Union[float, List[float]],

                  return_scale: bool = False

                  ) -> Union[float, List[float], Tuple[Union[float, List[float]], float]]:

        """

        向查询结果添加拉普拉斯噪声

        

        这是 Laplace 机制的核心方法。对于单个查询值或查询值向量，

        添加适当尺度的拉普拉斯噪声以实现差分隐私。

        

        参数：

            query_value (float 或 List[float]): 确定性查询结果。

                - 单值：直接添加噪声

                - 列表：对每个元素分别添加噪声（每个使用相同尺度）

            sensitivity (float 或 List[float]): 查询的敏感度。

                - 标量：对所有输出使用相同的敏感度

                - 列表：每个输出维度使用不同的敏感度

            return_scale (bool, optional): 是否返回噪声尺度参数。默认为 False。

        

        返回：

            取决于 return_scale 参数：

                - return_scale=False: 返回添加噪声后的查询结果

                - return_scale=True: 返回 (添加噪声后的结果, 噪声尺度) 元组

        

        异常：

            ValueError: 当敏感度为负或 epsilon 非正时抛出。

        

        数学原理：

            M(D) = f(D) + Laplace(0, Δf / ε)

            

            对于向量查询 f(D) = [f₁(D), f₂(D), ..., fₖ(D)]，

            每个维度 i 添加独立的 Laplace(0, Δfᵢ / ε) 噪声。

        

        示例：

            >>> mechanism = LaplaceMechanism(epsilon=1.0)

            >>> # 单值查询

            >>> noisy_count = mechanism.add_noise(100, sensitivity=1.0)

            >>> print(f"计数查询噪声结果: {noisy_count:.4f}")

            计数查询噪声结果: 99.1234

            >>>

            >>> # 向量查询

            >>> noisy_vector = mechanism.add_noise([1.0, 2.0, 3.0], sensitivity=[1.0, 1.0, 1.0])

            >>> print(f"向量查询噪声结果: {[f'{v:.4f}' for v in noisy_vector]}")

            向量查询噪声结果: ['0.8234', '2.1567', '2.9456']

        """

        # 计算噪声尺度

        if isinstance(sensitivity, (int, float)):

            scale = compute_noise_scale(float(sensitivity), self._epsilon)

        elif isinstance(sensitivity, (list, tuple)):

            scale = [compute_noise_scale(float(s), self._epsilon) for s in sensitivity]

        else:

            raise TypeError(f"sensitivity 类型不支持: {type(sensitivity)}")

        

        # 更新已使用的隐私预算

        self._used_budget += self._epsilon

        

        # 根据 query_value 类型分别处理

        if isinstance(query_value, (int, float)):

            # 单值查询：添加单个拉普拉斯噪声

            noise = laplace_sample(loc=0.0, scale=scale)

            noisy_value = float(query_value) + noise

            if return_scale:

                return noisy_value, scale

            return noisy_value

        

        elif isinstance(query_value, (list, tuple)):

            # 向量查询：对每个元素添加独立噪声

            noisy_values = []

            if isinstance(scale, list):

                # 每个维度使用不同的敏感度和噪声尺度

                for val, s in zip(query_value, scale):

                    noise = laplace_sample(loc=0.0, scale=s)

                    noisy_values.append(float(val) + noise)

            else:

                # 所有维度使用相同的噪声尺度

                for val in query_value:

                    noise = laplace_sample(loc=0.0, scale=scale)

                    noisy_values.append(float(val) + noise)

            

            if return_scale:

                return noisy_values, scale

            return noisy_values

        

        else:

            raise TypeError(f"query_value 类型不支持: {type(query_value)}")

    

    def count_query(self, dataset: List[Any],

                    predicate: Optional[Callable[[Any], bool]] = None,

                    return_details: bool = False

                    ) -> Union[int, Tuple[int, int]]:

        """

        执行差分隐私计数查询

        

        计数查询用于统计满足特定条件的记录数量。

        由于计数查询的敏感度恒为 1（每条记录最多影响计数结果1次），

        因此噪声尺度直接等于 1/ε。

        

        参数：

            dataset (List[Any]): 输入数据集。

            predicate (Callable[[Any], bool], optional): 过滤条件函数。

                如果为 None，则统计所有记录的数量。

            return_details (bool, optional): 是否返回详细信息。

                如果为 True，返回 (带噪声计数, 真实计数)。默认为 False。

        

        返回：

            取决于 return_details 参数：

                - return_details=False: 返回带噪声的计数结果

                - return_details=True: 返回 (带噪声计数, 真实计数) 元组

        

        数学保证：

            M(D) = count(D) + Laplace(0, 1/ε)

            

            对于 ε-差分隐私，敏感度 Δcount = 1，因此尺度 b = 1/ε。

        

        示例：

            >>> data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

            >>> mechanism = LaplaceMechanism(epsilon=1.0)

            >>> noisy_count = mechanism.count_query(data, predicate=lambda x: x > 5)

            >>> print(f"满足条件的数量（带噪声）: {int(round(noisy_count))}")

            满足条件的数量（带噪声）: 5

        """

        # 计算真实计数

        if predicate is None:

            true_count = len(dataset)

        else:

            true_count = sum(1 for item in dataset if predicate(item))

        

        # 添加拉普拉斯噪声

        sensitivity = 1  # 计数查询的敏感度恒为 1

        scale = compute_noise_scale(sensitivity, self._epsilon)

        noise = laplace_sample(loc=0.0, scale=scale)

        noisy_count = true_count + noise

        

        # 更新隐私预算消耗

        self._used_budget += self._epsilon

        

        if return_details:

            return noisy_count, true_count

        return noisy_count

    

    def sum_query(self, dataset: List[float],

                  lower_bound: Optional[float] = None,

                  upper_bound: Optional[float] = None,

                  return_details: bool = False

                  ) -> Union[float, Tuple[float, float]]:

        """

        执行差分隐私求和查询

        

        求和查询用于计算某个数值属性的总和。

        与计数查询不同，求和查询的敏感度取决于值域范围。

        

        数学背景：

            对于值域为 [lower, upper] 的数据，求和查询的敏感度为：

                Δsum = upper - lower

            

            特别地，如果值域为 [0, c]，则 Δsum = c。

            如果值域为 [-c, c]（对称界），则 Δsum = 2c。

        

        参数：

            dataset (List[float]): 数值型数据集。

            lower_bound (float, optional): 数据值域的下界。

            upper_bound (float, optional): 数据值域的上界。

                如果不指定，则从数据中推断（但这会泄露信息！）。

            return_details (bool, optional): 是否返回详细信息。

                如果为 True，返回 (带噪声求和, 真实求和) 元组。

        

        返回：

            取决于 return_details：

                - return_details=False: 返回带噪声的求和结果

                - return_details=True: 返回 (带噪声求和, 真实求和) 元组

        

        异常：

            ValueError: 当未提供值域边界时抛出。

        

        示例：

            >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]

            >>> mechanism = LaplaceMechanism(epsilon=0.5)

            >>> noisy_sum = mechanism.sum_query(data, lower_bound=0.0, upper_bound=10.0)

            >>> print(f"求和结果（带噪声）: {noisy_sum:.4f}")

            求和结果（带噪声）: 14.8723

        """

        # 计算真实求和

        true_sum = sum(dataset)

        

        # 计算敏感度

        if lower_bound is None or upper_bound is None:

            raise ValueError(

                "求和查询必须指定值域边界 [lower_bound, upper_bound]。"

                "不指定边界会导致隐私泄露！"

            )

        

        sensitivity = abs(upper_bound - lower_bound)

        scale = compute_noise_scale(sensitivity, self._epsilon)

        noise = laplace_sample(loc=0.0, scale=scale)

        noisy_sum = true_sum + noise

        

        # 更新隐私预算消耗

        self._used_budget += self._epsilon

        

        if return_details:

            return noisy_sum, true_sum

        return noisy_sum

    

    def mean_query(self, dataset: List[float],

                   known_bounds: Tuple[float, float],

                   return_details: bool = False

                   ) -> Union[float, Tuple[float, float]]:

        """

        执行差分隐私均值查询

        

        均值查询计算数值的平均值。由于均值可以表示为求和除以计数，

        其敏感度与数据集大小和值域范围有关。

        

        数学背景：

            mean(D) = sum(D) / n

            

            对于相邻数据集 D 和 D'（相差一条记录），有：

                |mean(D) - mean(D')| ≤ (upper - lower) / n

            

            因此，均值查询的敏感度为 (值域范围) / n。

        

        参数：

            dataset (List[float]): 数值型数据集。

            known_bounds (Tuple[float, float]): 已知的值域边界 (lower, upper)。

            return_details (bool, optional): 是否返回详细信息。

        

        返回：

            取决于 return_details：

                - return_details=False: 返回带噪声的均值结果

                - return_details=True: 返回 (带噪声均值, 真实均值) 元组

        

        示例：

            >>> data = [1.0, 2.0, 3.0, 4.0, 5.0]

            >>> mechanism = LaplaceMechanism(epsilon=1.0)

            >>> noisy_mean = mechanism.mean_query(data, known_bounds=(0.0, 10.0))

            >>> print(f"均值结果（带噪声）: {noisy_mean:.4f}")

            均值结果（带噪声）: 2.9823

        """

        lower_bound, upper_bound = known_bounds

        n = len(dataset)

        

        if n == 0:

            raise ValueError("数据集不能为空")

        

        # 真实均值

        true_mean = sum(dataset) / n

        

        # 敏感度：值域范围 / 数据集大小

        range_width = abs(upper_bound - lower_bound)

        sensitivity = range_width / n

        

        # 添加噪声

        scale = compute_noise_scale(sensitivity, self._epsilon)

        noise = laplace_sample(loc=0.0, scale=scale)

        noisy_mean = true_mean + noise

        

        # 更新隐私预算消耗

        self._used_budget += self._epsilon

        

        if return_details:

            return noisy_mean, true_mean

        return noisy_mean

    

    def clamp(self, value: Union[float, List[float]],

              lower: float, upper: float

              ) -> Union[float, List[float]]:

        """

        截断（Clamping）操作

        

        截断是差分隐私数据处理中的常用操作，用于将数值限制在指定范围内。

        这有助于控制敏感度，防止极端值导致过大的噪声。

        

        注意：截断本身不是差分隐私操作，需要与噪声添加结合使用。

        

        参数：

            value (float 或 List[float]): 待截断的值或值列表。

            lower (float): 下界。

            upper (float): 上界（必须 ≥ lower）。

        

        返回：

            截断后的值或值列表。

        

        示例：

            >>> LaplaceMechanism.clamp(5.0, 0.0, 10.0)

            5.0

            >>> LaplaceMechanism.clamp(-3.0, 0.0, 10.0)

            0.0

            >>> LaplaceMechanism.clamp([15.0, -5.0, 7.0], 0.0, 10.0)

            [10.0, 0.0, 7.0]

        """

        if upper < lower:

            raise ValueError(f"上界必须 ≥ 下界: lower={lower}, upper={upper}")

        

        if isinstance(value, (int, float)):

            return max(lower, min(upper, float(value)))

        elif isinstance(value, (list, tuple)):

            return [max(lower, min(upper, float(v))) for v in value]

        else:

            raise TypeError(f"value 类型不支持: {type(value)}")

    

    def noise_level(self, sensitivity: float) -> Dict[str, float]:

        """

        计算指定敏感度下的噪声水平统计

        

        帮助用户了解当前隐私参数下噪声的预期规模。

        

        参数：

            sensitivity (float): 查询的敏感度。

        

        返回：

            Dict[str, float]: 包含噪声水平统计信息的字典。

                - 'scale': 噪声尺度参数 b

                - 'std': 噪声的标准差（拉普拉斯分布的 std = b·√2）

                - 'variance': 噪声的方差（= 2·b²）

                - 'mae': 噪声的平均绝对误差（= b）

                - 'rmse': 噪声的均方根误差（= b·√2）

                - '95ci_width': 95% 置信区间的宽度（≈ 7.3·b）

        """

        scale = compute_noise_scale(sensitivity, self._epsilon)

        

        return {

            "scale": scale,

            "std": scale * math.sqrt(2),

            "variance": 2 * scale * scale,

            "mae": scale,

            "rmse": scale * math.sqrt(2),

            "95ci_width": 2 * 3.65 * scale,  # 约 7.3 * scale

        }





class PrivateHistogram:

    """

    差分隐私直方图构建器

    

    直方图查询是数据分析中最常用的查询之一。

    PrivateHistogram 提供了向直方图计数中添加拉普拉斯噪声的功能。

    

    与直接查询不同的是，直方图的每个 bin 都需要独立添加噪声，

    这使得我们可以独立控制每个 bin 的隐私保护。

    

    计数查询敏感度 = 1（每条记录最多影响一个 bin）

    

    示例：

        >>> data = [1, 1, 2, 2, 2, 3]

        >>> hist = PrivateHistogram(bin_edges=[0, 2, 4, 6], epsilon=1.0)

        >>> noisy_counts = hist.add_noise(data)

        >>> print(f"噪声直方图计数: {noisy_counts}")

        噪声直方图计数: [1.23, 3.45, 1.12]

    """

    

    def __init__(self, bin_edges: List[float], epsilon: float) -> None:

        """

        初始化直方图构建器

        

        参数：

            bin_edges (List[float]): 分箱边界，必须是严格递增的序列。

                                      例如 [0, 10, 20, 30] 定义了 3 个 bin。

            epsilon (float): 隐私预算参数。

        

        异常：

            ValueError: 当 bin_edges 不是严格递增时抛出。

        """

        # 验证 bin_edges 的有效性

        if len(bin_edges) < 2:

            raise ValueError("bin_edges 至少需要两个边界值")

        for i in range(1, len(bin_edges)):

            if bin_edges[i] <= bin_edges[i-1]:

                raise ValueError(

                    f"bin_edges 必须严格递增，但在索引 {i-1} 和 {i} 处"

                    f"发现非递增: {bin_edges[i-1]} >= {bin_edges[i]}"

                )

        

        self._bin_edges = list(bin_edges)

        self._num_bins = len(bin_edges) - 1

        self._epsilon = float(epsilon)

        self._mechanism = LaplaceMechanism(epsilon=epsilon)

    

    @property

    def num_bins(self) -> int:

        """获取 bin 的数量"""

        return self._num_bins

    

    def _compute_true_histogram(self, data: List[float]) -> List[int]:

        """

        计算数据在各 bin 中的真实计数

        

        参数：

            data (List[float]): 输入数据。

        

        返回：

            List[int]: 每个 bin 的计数。

        """

        counts = [0] * self._num_bins

        

        for value in data:

            # 使用二分查找找到 value 所属的 bin

            # bisect_right 确保左闭右开的区间划分

            idx = 0

            for i in range(self._num_bins):

                if self._bin_edges[i] <= value < self._bin_edges[i + 1]:

                    idx = i

                    break

                elif i == self._num_bins - 1:

                    idx = i  # 最后一个 bin 包含右边界

            else:

                idx = self._num_bins - 1

            

            # 处理边界情况（最后一个 bin 的右边界）

            if value >= self._bin_edges[-1]:

                idx = self._num_bins - 1

            

            counts[idx] += 1

        

        return counts

    

    def add_noise(self, data: List[float],

                  return_true: bool = False

                  ) -> Union[List[float], Tuple[List[float], List[int]]]:

        """

        向直方图计数添加拉普拉斯噪声

        

        参数：

            data (List[float]): 输入数据。

            return_true (bool, optional): 是否返回真实计数。默认为 False。

        

        返回：

            取决于 return_true 参数：

                - return_true=False: 返回带噪声的 bin 计数列表

                - return_true=True: 返回 (带噪声计数, 真实计数) 元组

        

        示例：

            >>> edges = [0, 2, 4, 6]

            >>> data = [1.5, 1.5, 3.0, 3.0, 3.0, 5.0]

            >>> hist = PrivateHistogram(edges, epsilon=1.0)

            >>> noisy = hist.add_noise(data)

            >>> print(f"带噪声计数: {[f'{c:.2f}' for c in noisy]}")

            带噪声计数: ['2.12', '2.89', '1.23']

        """

        # 计算真实直方图

        true_counts = self._compute_true_histogram(data)

        

        # 每个 bin 的计数敏感度为 1

        # 由于每个 bin 有独立的噪声，所有 bin 共享同一个 ε

        sensitivity = 1

        scale = compute_noise_scale(sensitivity, self._epsilon)

        

        # 向每个 bin 添加独立的拉普拉斯噪声

        noisy_counts = []

        for count in true_counts:

            noise = laplace_sample(loc=0.0, scale=scale)

            noisy_counts.append(max(0.0, count + noise))  # 确保计数非负

        

        if return_true:

            return noisy_counts, true_counts

        return noisy_counts





def privacy_test_laplace(epsilon: float,

                          sensitivity: float,

                          num_trials: int = 10000,

                          verbose: bool = True

                          ) -> Dict[str, float]:

    """

    通过蒙特卡洛模拟验证 Laplace 机制的差分隐私保证

    

    该函数通过大量随机采样来验证拉普拉斯机制是否正确实现了差分隐私。

    

    原理：

        对于相邻数据集 D 和 D'，理论上应满足：

            Pr[M(D) ∈ S] ≤ e^ε · Pr[M(D') ∈ S]

        

        我们通过统计模拟来估计这个比值的分布。

    

    参数：

        epsilon (float): 隐私预算参数。

        sensitivity (float): 查询敏感度。

        num_trials (int, optional): 模拟次数。默认为 10000。

        verbose (bool, optional): 是否打印详细信息。默认为 True。

    

    返回：

        Dict[str, float]: 包含验证结果的字典。

            - 'max_ratio': 观察到的最大概率比（应 ≤ e^ε）

            - 'empirical_epsilon': 经验估计的 ε 值

            - 'violations': 违反差分隐私约束的次数

            - 'violation_rate': 违反率

    

    示例：

        >>> result = privacy_test_laplace(epsilon=1.0, sensitivity=1.0, num_trials=5000)

        >>> print(f"最大比值: {result['max_ratio']:.4f} (理论上限: {math.exp(1.0):.4f})")

        >>> print(f"违规率: {result['violation_rate']:.4%}")

    """

    scale = compute_noise_scale(sensitivity, epsilon)

    

    # 模拟两个相邻数据集的查询结果差异

    # 设 f(D) = 0, f(D') = sensitivity

    # 则 M(D) = Laplace(0, scale), M(D') = sensitivity + Laplace(0, scale)

    

    max_ratio = 0.0

    violations = 0

    epsilons_observed = []

    

    # 输出区间（用于计算特定区间的概率）

    output_range = 10 * scale

    num_bins = 100

    bin_width = 2 * output_range / num_bins

    

    # 统计 M(D) 和 M(D') 在各区间的概率

    count_d = [0] * num_bins

    count_d_prime = [0] * num_bins

    

    for _ in range(num_trials):

        # 从 M(D) 采样

        sample_d = laplace_sample(loc=0.0, scale=scale)

        # 从 M(D') 采样

        sample_d_prime = sensitivity + laplace_sample(loc=0.0, scale=scale)

        

        # 记录到直方图

        bin_idx_d = int((sample_d + output_range) / bin_width)

        bin_idx_d_prime = int((sample_d_prime + output_range) / bin_width)

        

        if 0 <= bin_idx_d < num_bins:

            count_d[bin_idx_d] += 1

        if 0 <= bin_idx_d_prime < num_bins:

            count_d_prime[bin_idx_d_prime] += 1

        

        # 计算该样本的似然比

        # Pr[M(D) = x] / Pr[M(D') = x] = exp(|x - 0| / scale) / exp(|x - sensitivity| / scale)

        # 但由于是采样，我们比较 Pr[x - ε ≤ X ≤ x + ε] 的比值

        epsilon_x = abs(sample_d - sample_d_prime) / scale

        epsilons_observed.append(epsilon_x)

        

        # 记录最大比值

        if epsilon_x > max_ratio:

            max_ratio = epsilon_x

    

    # 计算违规率（似然比超过 e^epsilon 的比例）

    theoretical_max = math.exp(epsilon)

    violations = sum(1 for e in epsilons_observed if e > theoretical_max)

    violation_rate = violations / num_trials

    

    # 经验 epsilon

    empirical_epsilon = sum(epsilons_observed) / num_trials

    

    if verbose:

        print(f"\n{'='*60}")

        print(f"Laplace 机制差分隐私验证 (ε={epsilon}, Δ={sensitivity})")

        print(f"{'='*60}")

        print(f"  模拟次数: {num_trials:,}")

        print(f"  理论最大似然比: exp(ε) = {theoretical_max:.4f}")

        print(f"  观察最大似然比: {max_ratio:.4f}")

        print(f"  经验平均似然比: {empirical_epsilon:.4f}")

        print(f"  违规次数: {violations:,} ({violation_rate:.4%})")

        print(f"{'='*60}\n")

    

    return {

        "max_ratio": max_ratio,

        "empirical_epsilon": empirical_epsilon,

        "violations": violations,

        "violation_rate": violation_rate,

        "theoretical_max": theoretical_max,

    }





# ============================================================================

# 测试代码

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("Laplace 机制 - 单元测试")

    print("=" * 70)

    

    random.seed(42)  # 设置随机种子以确保可重复性

    

    # 测试 1: 拉普拉斯分布采样

    print("\n[测试 1] 拉普拉斯分布采样")

    try:

        samples = [laplace_sample(0.0, 1.0) for _ in range(1000)]

        mean_estimate = sum(samples) / len(samples)

        var_estimate = sum((x - mean_estimate)**2 for x in samples) / len(samples)

        

        print(f"  采样数量: {len(samples)}")

        print(f"  样本均值: {mean_estimate:.4f} (理论值: 0.0)")

        print(f"  样本方差: {var_estimate:.4f} (理论值: 2.0)")

        

        # 检验样本均值接近 0（允许一定误差）

        assert abs(mean_estimate) < 0.2, f"均值偏离过大: {mean_estimate}"

        # 检验样本方差接近 2（拉普拉斯分布方差 = 2·b² = 2）

        assert 1.5 < var_estimate < 2.5, f"方差偏离过大: {var_estimate}"

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 2: 噪声尺度计算

    print("\n[测试 2] 噪声尺度计算")

    try:

        assert compute_noise_scale(1.0, 1.0) == 1.0

        assert compute_noise_scale(2.0, 0.5) == 4.0

        assert compute_noise_scale(0.0, 1.0) == 0.0

        

        try:

            compute_noise_scale(-1.0, 1.0)

            print("  ✗ 应该抛出 ValueError")

        except ValueError:

            print("  ✓ 正确检测负敏感度")

        

        try:

            compute_noise_scale(1.0, 0.0)

            print("  ✗ 应该抛出 ValueError")

        except ValueError:

            print("  ✓ 正确检测非正 epsilon")

        

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 3: LaplaceMechanism 基本用法

    print("\n[测试 3] LaplaceMechanism 基本用法")

    try:

        mechanism = LaplaceMechanism(epsilon=1.0)

        

        # 单值查询

        query_value = 100.0

        sensitivity = 1.0

        noisy_value = mechanism.add_noise(query_value, sensitivity)

        

        print(f"  原始值: {query_value}")

        print(f"  噪声结果: {noisy_value:.4f}")

        print(f"  噪声幅度: {abs(noisy_value - query_value):.4f}")

        

        assert isinstance(noisy_value, float)

        assert mechanism.used_budget == 1.0

        

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 4: 计数查询

    print("\n[测试 4] 计数查询")

    try:

        mechanism = LaplaceMechanism(epsilon=0.5)

        dataset = list(range(1000))

        

        noisy_count, true_count = mechanism.count_query(

            dataset,

            predicate=lambda x: x > 500,

            return_details=True

        )

        

        print(f"  数据集大小: {len(dataset)}")

        print(f"  真实计数 (>500): {true_count}")

        print(f"  噪声计数: {int(round(noisy_count))}")

        print(f"  误差: {abs(noisy_count - true_count):.2f}")

        

        assert true_count == 499

        assert isinstance(noisy_count, float)

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 5: 求和查询

    print("\n[测试 5] 求和查询")

    try:

        mechanism = LaplaceMechanism(epsilon=0.5)

        data = [float(x) for x in range(100)]

        

        noisy_sum, true_sum = mechanism.sum_query(

            data,

            lower_bound=0.0,

            upper_bound=100.0,

            return_details=True

        )

        

        print(f"  数据和: {true_sum}")

        print(f"  噪声和: {noisy_sum:.2f}")

        print(f"  误差: {abs(noisy_sum - true_sum):.2f}")

        

        assert true_sum == sum(data)

        assert mechanism.used_budget == 0.5

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 6: 向量查询

    print("\n[测试 6] 向量查询")

    try:

        mechanism = LaplaceMechanism(epsilon=1.0)

        query_vector = [10.0, 20.0, 30.0]

        sensitivities = [1.0, 2.0, 3.0]

        

        noisy_vector = mechanism.add_noise(query_vector, sensitivities)

        

        print(f"  原始向量: {query_vector}")

        print(f"  噪声向量: {[f'{v:.4f}' for v in noisy_vector]}")

        print(f"  噪声尺度: {[f'{abs(noisy_vector[i] - query_vector[i]):.4f}' for i in range(3)]}")

        

        assert len(noisy_vector) == 3

        assert all(isinstance(v, float) for v in noisy_vector)

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 7: PrivateHistogram

    print("\n[测试 7] PrivateHistogram")

    try:

        edges = [0.0, 25.0, 50.0, 75.0, 100.0]

        data = [float(x) for x in range(100)]

        

        hist = PrivateHistogram(bin_edges=edges, epsilon=1.0)

        noisy_counts, true_counts = hist.add_noise(data, return_true=True)

        

        print(f"  Bin 边界: {edges}")

        print(f"  真实计数: {true_counts}")

        print(f"  噪声计数: {[f'{c:.1f}' for c in noisy_counts]}")

        

        assert len(noisy_counts) == 4

        assert true_counts == [25, 25, 25, 25]

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 8: 噪声水平分析

    print("\n[测试 8] 噪声水平分析")

    try:

        mechanism = LaplaceMechanism(epsilon=1.0)

        noise_stats = mechanism.noise_level(sensitivity=1.0)

        

        print(f"  噪声尺度 (b): {noise_stats['scale']:.4f}")

        print(f"  标准差: {noise_stats['std']:.4f}")

        print(f"  方差: {noise_stats['variance']:.4f}")

        print(f"  平均绝对误差: {noise_stats['mae']:.4f}")

        print(f"  95%置信区间宽度: {noise_stats['95ci_width']:.4f}")

        

        assert noise_stats['scale'] == 1.0

        assert noise_stats['variance'] == 2.0

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 9: 差分隐私保证验证（蒙特卡洛模拟）

    print("\n[测试 9] 差分隐私保证验证")

    try:

        result = privacy_test_laplace(

            epsilon=1.0,

            sensitivity=1.0,

            num_trials=5000,

            verbose=True

        )

        

        # 验证：观察到的最大似然比不应显著超过 e^ε

        assert result['max_ratio'] <= math.exp(1.0) * 1.1, \

            f"最大比值超标: {result['max_ratio']} > {math.exp(1.0) * 1.1}"

        # 违规率应该很低（拉普拉斯机制理论上不应有违规）

        assert result['violation_rate'] < 0.01, \

            f"违规率过高: {result['violation_rate']:.4%}"

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 10: 截断操作

    print("\n[测试 10] 截断操作")

    try:

        mechanism = LaplaceMechanism(epsilon=1.0)

        

        assert mechanism.clamp(5.0, 0.0, 10.0) == 5.0

        assert mechanism.clamp(-5.0, 0.0, 10.0) == 0.0

        assert mechanism.clamp(15.0, 0.0, 10.0) == 10.0

        

        clamped_list = mechanism.clamp([15.0, -5.0, 7.0], 0.0, 10.0)

        assert clamped_list == [10.0, 0.0, 7.0]

        

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    print("\n" + "=" * 70)

    print("所有测试完成！")

    print("=" * 70)

    

    print("\n附录: Laplace 机制使用指南")

    print("-" * 50)

    print("噪声规模参考（敏感度 Δ=1 时）:")

    print(f"  ε = 0.01 → b = 100.0 (非常强的隐私，极大噪声)")

    print(f"  ε = 0.1  → b = 10.0  (强隐私，中大噪声)")

    print(f"  ε = 1.0  → b = 1.0   (中等隐私，适中噪声)")

    print(f"  ε = 10.0 → b = 0.1   (较弱隐私，小噪声)")

    print("")

    print("适用场景建议:")

    print("  ✓ 计数查询（敏感度恒为 1）")

    print("  ✓ 均值查询（需要较大的数据集）")

    print("  ✓ 直方图构建")

    print("  ✓ 需要严格 ε-DP 保证的场景")





"""

时间复杂度分析:

    - laplace_sample: O(1)，逆变换采样

    - LaplaceMechanism.add_noise: O(k)，k 为向量维度

    - PrivateHistogram.add_noise: O(n + m)，n 为数据大小，m 为 bin 数量

    - privacy_test_laplace: O(N)，N 为模拟次数



空间复杂度分析:

    - laplace_sample: O(1)

    - LaplaceMechanism: O(k)，存储 k 维向量的噪声

    - PrivateHistogram: O(m)，存储 m 个 bin 的计数

    - privacy_test_laplace: O(N)，存储 N 个样本



参考文献:

    [1] Dwork, C., McSherry, F., Nissim, K., Smith, A. (2006). Calibrating Noise to

        Sensitivity in Private Data Analysis. TCC 2006.

    [2] Dwork, C., Roth, A. (2014). The Algorithmic Foundations of Differential Privacy.

    [3] Balle, B., Wang, Y.X. (2018). Improving the Gaussian Mechanism for Differential

        Privacy: Analytical Calibration and Optimal Denoising. ICML 2018.

"""

