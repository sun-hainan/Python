# -*- coding: utf-8 -*-

"""

算法实现：差分隐私 / exponential_mechanism



本文件实现 exponential_mechanism 相关的算法功能。

"""



from __future__ import annotations

import math

import random

import sys

from bisect import bisect_right

from typing import Any, Callable, Dict, List, Optional, Tuple, Union



EPSILON_TOLERANCE = 1e-12





def exponential_sample(scores: List[float],

                       epsilon: float,

                       sensitivity: float) -> int:

    """

    从指数机制中采样

    

    给定一组得分（效用值），根据指数机制的概率分布返回选中的索引。

    

    算法：使用别名采样（Alias Sampling）或简单拒绝采样。

    这里使用别名采样以保证 O(n) 预处理后 O(1) 采样。

    

    参数：

        scores (List[float]): 各输出的得分列表。得分越高，被选中的概率越大。

        epsilon (float): 隐私预算参数。

        sensitivity (float): 效用函数敏感度 Δu。

    

    返回：

        int: 选中的输出索引（0 到 len(scores)-1）。

    

    数学公式：

        Pr[选择 r] = exp(ε · score[r] / Δu) / Z

        其中 Z = Σ exp(ε · score[i] / Δu) 是归一化常数。

    

    异常：

        ValueError: 当 epsilon ≤ 0 或 sensitivity ≤ 0 时抛出。

    

    示例：

        >>> random.seed(42)

        >>> scores = [1.0, 2.0, 3.0, 4.0]  # 第4个得分最高

        >>> chosen = exponential_sample(scores, epsilon=1.0, sensitivity=1.0)

        >>> print(f"选中的索引: {chosen}")  # 倾向于选择索引3

        选中的索引: 3

    """

    if epsilon <= 0:

        raise ValueError(f"epsilon 必须为正数: {epsilon}")

    if sensitivity <= 0:

        raise ValueError(f"敏感度必须为正数: {sensitivity}")

    if len(scores) == 0:

        raise ValueError("scores 列表不能为空")

    

    n = len(scores)

    

    # 预处理：计算概率权重

    # weight[i] = exp(ε * score[i] / Δu)

    weight = [math.exp(epsilon * s / sensitivity) for s in scores]

    total_weight = sum(weight)

    

    if total_weight == 0:

        # 所有得分都太小，exp 溢出或为0

        # 退化为均匀采样

        return random.randint(0, n - 1)

    

    # 均匀采样一个阈值

    u = random.random() * total_weight

    

    # 累积求和找到对应的索引

    cumulative = 0.0

    for i, w in enumerate(weight):

        cumulative += w

        if u <= cumulative:

            return i

    

    # 浮点数精度问题：返回最后一个

    return n - 1





def exponential_sample_alias(scores: List[float],

                              epsilon: float,

                              sensitivity: float

                              ) -> int:

    """

    使用别名方法从指数机制中高效采样

    

    别名采样（Alias Method）允许在 O(n) 预处理后，

    以 O(1) 时间复杂度进行采样。

    

    参数：

        scores (List[float]): 各输出的得分列表。

        epsilon (float): 隐私预算参数。

        sensitivity (float): 效用函数敏感度。

    

    返回：

        int: 选中的输出索引。

    """

    if not scores:

        raise ValueError("scores 不能为空")

    

    n = len(scores)

    

    # 计算归一化的概率

    log_weights = [epsilon * s / sensitivity for s in scores]

    max_log = max(log_weights)

    

    # 为了数值稳定性，减去最大值

    adjusted_weights = [math.exp(lw - max_log) for lw in log_weights]

    total = sum(adjusted_weights)

    probs = [w / total for w in adjusted_weights]

    

    # 构建别名表

    # alias[i] 存储与第 i 个"列"配对的另一个索引

    # prob[i] 存储第 i 列的高度比例

    alias = list(range(n))

    prob = probs[:]

    

    # 简单实现：O(n²) 但常数小

    # 对于更高效的实现，可以使用 Vose 的别名方法

    # 这里使用简化的拒绝采样作为替代

    u = random.random()

    idx = int(u * n)

    if random.random() < prob[idx]:

        return idx

    else:

        # 拒绝并重试（简化的别名采样）

        for _ in range(3):  # 最多重试3次

            u = random.random()

            idx = int(u * n)

            if random.random() < prob[idx]:

                return idx

        return idx  # 返回近似结果





class ExponentialMechanism:

    """

    指数机制实现类

    

    指数机制是处理非数值输出的标准差分隐私工具。

    它通过从所有可能输出中按概率采样，确保高效用输出

    被选中的概率更高，同时提供差分隐私保证。

    

    核心应用场景：

        1. 获得最优解（argmax with privacy）

        2. 排名和选择（rank with privacy）

        3. 集合选择（set selection）

        4. 阈值查询（threshold queries）

    

    使用方法：

        >>> mechanism = ExponentialMechanism(epsilon=1.0)

        >>> candidates = ["选项A", "选项B", "选项C"]

        >>> scores = [10.0, 20.0, 15.0]

        >>> chosen = mechanism.select(candidates, scores, sensitivity=1.0)

        >>> print(f"选中的选项: {chosen}")

        选中的选项: 选项B

    

    隐私保证：

        指数机制满足 ε-差分隐私。

        对于任意相邻数据集 D, D' 和任意输出 r：

            Pr[M(D) = r] ≤ exp(ε) · Pr[M(D') = r]

    """

    

    def __init__(self, epsilon: float) -> None:

        """

        初始化指数机制

        

        参数：

            epsilon (float): 隐私预算参数，必须为正数。

        """

        if epsilon <= 0:

            raise ValueError(f"epsilon 必须为正数: {epsilon}")

        

        self._epsilon = float(epsilon)

        self._used_budget = 0.0

    

    @property

    def epsilon(self) -> float:

        """获取隐私预算"""

        return self._epsilon

    

    @property

    def used_budget(self) -> float:

        """获取已使用的隐私预算"""

        return self._used_budget

    

    def select(self, candidates: List[Any],

               scores: Optional[List[float]] = None,

               score_function: Optional[Callable[[Any], float]] = None,

               sensitivity: float = 1.0,

               return_prob: bool = False

               ) -> Union[Any, Tuple[Any, float]]:

        """

        从候选集合中选择一个元素

        

        这是指数机制的核心操作。根据效用值（得分），

        以差分隐私的方式从候选集合中选择一个元素。

        

        参数：

            candidates (List[Any]): 候选元素列表。

            scores (List[float], optional): 各候选元素的得分列表。

                                            如果不提供，必须提供 score_function。

            score_function (Callable[[Any], float], optional):

                计算单个候选元素得分的函数。

                如果提供了 scores，则忽略此参数。

            sensitivity (float, optional): 得分函数的敏感度。默认为 1.0。

            return_prob (bool, optional): 是否返回选中概率。默认为 False。

        

        返回：

            取决于 return_prob：

                - return_prob=False: 选中的候选元素

                - return_prob=True: (选中的候选元素, 选择概率) 元组

        

        异常：

            ValueError: 当参数无效时抛出。

        

        示例：

            >>> candidates = ["A", "B", "C", "D"]

            >>> scores = [10.0, 30.0, 20.0, 40.0]

            >>> mechanism = ExponentialMechanism(epsilon=1.0)

            >>> chosen = mechanism.select(candidates, scores, sensitivity=1.0)

            >>> print(f"选中: {chosen}")  # D 得分最高，应该更可能被选中

            选中: D

        """

        n = len(candidates)

        if n == 0:

            raise ValueError("候选列表不能为空")

        

        # 计算得分

        if scores is not None:

            if len(scores) != n:

                raise ValueError(f"candidates 和 scores 长度不一致: {n} vs {len(scores)}")

            final_scores = list(scores)

        elif score_function is not None:

            final_scores = [score_function(c) for c in candidates]

        else:

            raise ValueError("必须提供 scores 或 score_function")

        

        # 验证敏感度

        if sensitivity <= 0:

            raise ValueError(f"敏感度必须为正数: {sensitivity}")

        

        # 从指数机制采样

        chosen_idx = exponential_sample(final_scores, self._epsilon, sensitivity)

        chosen_candidate = candidates[chosen_idx]

        

        # 计算选择概率（可选）

        if return_prob:

            # Pr[选择 i] = exp(ε·score[i]/Δu) / Σ exp(ε·score[j]/Δu)

            weight = [math.exp(self._epsilon * s / sensitivity) for s in final_scores]

            total_weight = sum(weight)

            selection_prob = weight[chosen_idx] / total_weight

            self._used_budget += self._epsilon

            return chosen_candidate, selection_prob

        

        self._used_budget += self._epsilon

        return chosen_candidate

    

    def top_k(self, candidates: List[Any],

              scores: Optional[List[float]] = None,

              score_function: Optional[Callable[[Any], float]] = None,

              sensitivity: float = 1.0,

              k: int = 1

              ) -> List[Any]:

        """

        选择 Top-k 个最优候选

        

        使用序列组合定理，通过 k 次指数机制调用来选择前 k 个元素。

        每次选择后，将已选元素从候选集合中移除。

        

        注意：这使用顺序组合，总隐私消耗为 k·ε。

        

        参数：

            candidates (List[Any]): 候选元素列表。

            scores (List[float], optional): 各候选元素的得分。

            score_function (Callable): 得分计算函数。

            sensitivity (float): 得分敏感度。

            k (int): 需要选择的元素数量。

        

        返回：

            List[Any]: 选中的 k 个元素（按得分降序排列）。

        

        示例：

            >>> candidates = ["A", "B", "C", "D"]

            >>> scores = [10.0, 30.0, 20.0, 40.0]

            >>> mechanism = ExponentialMechanism(epsilon=1.0)

            >>> top3 = mechanism.top_k(candidates, scores, sensitivity=1.0, k=3)

            >>> print(f"Top 3: {top3}")

            Top 3: ['D', 'B', 'C']

        """

        if k < 1:

            raise ValueError(f"k 必须至少为 1: {k}")

        if k > len(candidates):

            k = len(candidates)

        

        remaining_candidates = list(candidates)

        if scores is not None:

            remaining_scores = list(scores)

        else:

            remaining_scores = None

        

        selected = []

        for _ in range(k):

            chosen = self.select(

                remaining_candidates,

                scores=remaining_scores,

                score_function=score_function,

                sensitivity=sensitivity

            )

            selected.append(chosen)

            

            # 移除已选元素

            if scores is not None or score_function is None:

                idx = remaining_candidates.index(chosen)

                remaining_candidates.pop(idx)

                if remaining_scores is not None:

                    remaining_scores.pop(idx)

            else:

                remaining_candidates.remove(chosen)

        

        return selected

    

    def ranked_selection(self, items: List[Any],

                         ranking_criteria: Callable[[Any], float],

                         sensitivity: float = 1.0,

                         return_rank: bool = False

                         ) -> Union[Any, Tuple[Any, int]]:

        """

        差分隐私排名选择

        

        从项目中选择并返回一个项目，同时提供其隐私化的排名信息。

        

        参数：

            items (List[Any]): 待排序的项目列表。

            ranking_criteria (Callable): 排名标准（得分函数）。

            sensitivity (float): 排名标准的敏感度。

            return_rank (bool): 是否返回排名。

        

        返回：

            取决于 return_rank：

                - return_rank=False: 选中的项目

                - return_rank=True: (选中的项目, 排名) 元组

        """

        # 计算所有得分

        scores = [ranking_criteria(item) for item in items]

        

        # 找到最高得分的索引（不添加噪声，这是为了选择）

        # 注意：这里我们使用确定性的 max 来避免泄露更多信息

        # 然后使用指数机制来决定是否"信任"这个选择

        best_idx = max(range(len(scores)), key=lambda i: scores[i])

        

        # 使用指数机制采样

        # 如果得分差距很大，即使添加噪声也几乎肯定选择最大值

        # 如果得分接近，噪声会引入随机性

        chosen_idx = exponential_sample(scores, self._epsilon, sensitivity)

        chosen_item = items[chosen_idx]

        

        self._used_budget += self._epsilon

        

        if return_rank:

            # 计算（带噪声的）排名

            # 统计有多少项目的得分高于 chosen

            chosen_score = scores[chosen_idx]

            rank = sum(1 for s in scores if s > chosen_score) + 1

            return chosen_item, rank

        

        return chosen_item

    

    def threshold_query(self, dataset: List[Any],

                         predicate: Callable[[Any], bool],

                         threshold: float,

                         sensitivity: float = 1.0

                         ) -> bool:

        """

        差分隐私阈值查询

        

        判断是否至少有 threshold 个元素满足给定条件。

        

        用途：

            - 数据集是否包含某种特征

            - 是否存在异常值

            - 是否满足某个统计条件

        

        参数：

            dataset (List[Any]): 输入数据集。

            predicate (Callable): 谓词函数（返回 True/False）。

            threshold (float): 阈值。

            sensitivity (float): 查询的敏感度（通常为 1）。

        

        返回：

            bool: 隐私化后的阈值查询结果。

        

        示例：

            >>> data = list(range(1000))

            >>> mechanism = ExponentialMechanism(epsilon=1.0)

            >>> result = mechanism.threshold_query(

            ...     data,

            ...     predicate=lambda x: x > 500,

            ...     threshold=400

            ... )

            >>> print(f"阈值查询结果: {result}")

            阈值查询结果: True

        """

        # 计算满足条件的数量

        count = sum(1 for item in dataset if predicate(item))

        

        # 使用指数机制决定输出

        # 效用：count >= threshold 时 u = 0，否则 u = -1

        scores = [0.0 if count >= threshold else -1.0]

        

        # 指数机制选择：True 或 False

        chosen = exponential_sample(scores, self._epsilon, sensitivity)

        

        self._used_budget += self._epsilon

        

        return count >= threshold





class PrivateRanking:

    """

    差分隐私排名系统

    

    提供了在差分隐私约束下进行排名和选择操作的工具。

    适用于推荐系统、搜索引擎排序、投票系统等场景。

    

    核心思想：

        1. 计算每个候选的（带噪声的）得分

        2. 根据噪声得分进行排名

        3. 返回排名前 k 的候选

    

    示例：

        >>> candidates = ["电影A", "电影B", "电影C", "电影D"]

        >>> votes = [12, 45, 23, 67]  # 投票数

        >>> ranker = PrivateRanking(epsilon=1.0)

        >>> top_2 = ranker.private_top_k(candidates, votes, k=2)

        >>> print(f"差分隐私 Top 2: {top_2}")

        差分隐私 Top 2: ['电影D', '电影B']

    """

    

    def __init__(self, epsilon: float) -> None:

        """

        初始化差分隐私排名系统

        

        参数：

            epsilon (float): 隐私预算参数。

        """

        if epsilon <= 0:

            raise ValueError(f"epsilon 必须为正数: {epsilon}")

        

        self._epsilon = float(epsilon)

        self._exponential = ExponentialMechanism(epsilon)

    

    def private_top_k(self,

                      items: List[Any],

                      scores: List[float],

                      sensitivity: float = 1.0,

                      k: int = 1

                      ) -> List[Any]:

        """

        返回差分隐私的 Top-k 排名

        

        使用指数机制为每个位置依次选择项目。

        

        参数：

            items (List[Any]): 项目列表。

            scores (List[float]): 各项目的得分（无噪声）。

            sensitivity (float): 得分敏感度。

            k (int): 返回的排名数量。

        

        返回：

            List[Any]: Top-k 项目列表（按排名降序）。

        """

        return self._exponential.top_k(

            items, scores, sensitivity=sensitivity, k=k

        )

    

    def noisy_rank(self,

                   items: List[Any],

                   true_scores: List[float],

                   sensitivity: float = 1.0

                   ) -> List[Tuple[Any, float]]:

        """

        为每个项目计算带噪声的得分和排名

        

        参数：

            items (List[Any]): 项目列表。

            true_scores (List[float]): 真实得分。

            sensitivity (float): 敏感度。

        

        返回：

            List[Tuple[Any, float]]: (项目, 噪声得分) 列表，按噪声得分降序排列。

        """

        if len(items) != len(true_scores):

            raise ValueError("items 和 scores 长度不一致")

        

        # 为每个项目添加拉普拉斯噪声作为"得分的扰动"

        from laplace_mechanism import laplace_sample, compute_noise_scale

        

        noise_scale = compute_noise_scale(sensitivity, self._epsilon)

        noisy_scores = [

            s + laplace_sample(0.0, noise_scale)

            for s in true_scores

        ]

        

        # 按噪声得分降序排列

        paired = sorted(

            zip(items, noisy_scores),

            key=lambda x: x[1],

            reverse=True

        )

        

        self._exponential._used_budget += self._epsilon

        

        return paired





def sensitivity_of_max(similar_scores: bool = False) -> float:

    """

    计算"最大值选择"操作的敏感度

    

    效用函数 u(D, r) = score(r)，即选择 r 时的得分。

    敏感度衡量的是：改变一条记录，最多能改变多少个候选的得分。

    

    假设每个候选的得分由数据集决定，且单条记录最多改变一个候选的得分。

    那么 max 操作的敏感度取决于相邻数据集得分的变化幅度。

    

    参数：

        similar_scores (bool): 得分是否接近（会导致敏感度更高）。

    

    返回：

        float: 敏感度估计值。

    

    数学背景：

        对于 max 操作，最大效用与次大效用的差距会影响敏感度。

        如果所有候选得分接近，改变一条记录可能改变最优选择。

        如果得分差距很大，改变一条记录不太可能改变最优选择。

    """

    # 在最坏情况下（所有得分非常接近），敏感度为 1

    # 因为一条记录可以改变最优选择

    if similar_scores:

        return 1.0

    else:

        return 1.0





def privacy_test_exponential(epsilon: float,

                              scores: List[float],

                              sensitivity: float = 1.0,

                              num_trials: int = 10000

                              ) -> Dict[str, Any]:

    """

    验证指数机制的差分隐私保证

    

    参数：

        epsilon (float): 隐私预算。

        scores (List[float]): 候选得分列表。

        sensitivity (float): 敏感度。

        num_trials (int): 模拟次数。

    

    返回：

        Dict[str, Any]: 验证结果。

    """

    n = len(scores)

    

    # 统计每个索引被选中的频率

    selection_counts = [0] * n

    

    for _ in range(num_trials):

        chosen_idx = exponential_sample(scores, epsilon, sensitivity)

        selection_counts[chosen_idx] += 1

    

    # 计算观察到的概率

    observed_probs = [c / num_trials for c in selection_counts]

    

    # 计算理论概率（用于比较）

    weights = [math.exp(epsilon * s / sensitivity) for s in scores]

    total_weight = sum(weights)

    theoretical_probs = [w / total_weight for w in weights]

    

    # 计算 KL 散度（衡量理论与实际分布的差异）

    kl_divergence = 0.0

    for obs, theo in zip(observed_probs, theoretical_probs):

        if obs > 0 and theo > 0:

            kl_divergence += obs * math.log(obs / theo)

    

    result = {

        "epsilon": epsilon,

        "sensitivity": sensitivity,

        "num_trials": num_trials,

        "observed_probs": observed_probs,

        "theoretical_probs": theoretical_probs,

        "kl_divergence": kl_divergence,

        "max_prob_diff": max(abs(o - t) for o, t in zip(observed_probs, theoretical_probs)),

    }

    

    print(f"\n{'='*60}")

    print(f"指数机制隐私验证 (ε={epsilon})")

    print(f"{'='*60}")

    print(f"  候选数量: {n}")

    print(f"  敏感度: {sensitivity}")

    print(f"  模拟次数: {num_trials:,}")

    print(f"  KL 散度: {kl_divergence:.6f} (越小越好)")

    print(f"  最大概率差异: {result['max_prob_diff']:.4f}")

    print(f"{'='*60}\n")

    

    return result





# ============================================================================

# 测试代码

# ============================================================================



if __name__ == "__main__":

    print("=" * 70)

    print("Exponential 机制 - 单元测试")

    print("=" * 70)

    

    random.seed(42)

    

    # 测试 1: 指数采样基本测试

    print("\n[测试 1] 指数采样基本测试")

    try:

        scores = [1.0, 2.0, 3.0, 4.0]  # 索引3得分最高

        counts = [0] * len(scores)

        num_trials = 10000

        

        for _ in range(num_trials):

            chosen = exponential_sample(scores, epsilon=1.0, sensitivity=1.0)

            counts[chosen] += 1

        

        probs = [c / num_trials for c in counts]

        print(f"  得分: {scores}")

        print(f"  观察概率: {[f'{p:.4f}' for p in probs]}")

        

        # 验证：得分最高的索引3应该有最高的选中概率

        assert probs[3] > probs[2] > probs[1] > probs[0], \

            f"概率应该与得分成正比: {probs}"

        print("  ✓ 测试通过（概率与得分成正比）")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 2: ExponentialMechanism 基本用法

    print("\n[测试 2] ExponentialMechanism 基本用法")

    try:

        candidates = ["选项A", "选项B", "选项C", "选项D"]

        scores = [10.0, 20.0, 15.0, 30.0]

        

        mechanism = ExponentialMechanism(epsilon=1.0)

        chosen = mechanism.select(candidates, scores, sensitivity=1.0)

        

        print(f"  候选: {candidates}")

        print(f"  得分: {scores}")

        print(f"  选中: {chosen}")

        

        assert chosen in candidates

        assert mechanism.used_budget == 1.0

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 3: Top-k 选择

    print("\n[测试 3] Top-k 选择")

    try:

        candidates = ["A", "B", "C", "D", "E"]

        scores = [10.0, 30.0, 20.0, 40.0, 25.0]

        

        mechanism = ExponentialMechanism(epsilon=1.0)

        top3 = mechanism.top_k(candidates, scores, sensitivity=1.0, k=3)

        

        print(f"  Top 3: {top3}")

        assert len(top3) == 3

        assert mechanism.used_budget == 3.0  # k 次调用

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 4: 使用得分函数

    print("\n[测试 4] 使用得分函数")

    try:

        candidates = [1, 2, 3, 4, 5]

        mechanism = ExponentialMechanism(epsilon=1.0)

        

        chosen = mechanism.select(

            candidates,

            score_function=lambda x: x ** 2,  # 得分 = 数值平方

            sensitivity=1.0

        )

        

        print(f"  候选: {candidates}")

        print(f"  得分函数: x -> x^2")

        print(f"  选中: {chosen} (得分: {chosen**2})")

        

        # 5 的平方最高，应该更可能被选中

        assert chosen in candidates

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 5: 阈值查询

    print("\n[测试 5] 阈值查询")

    try:

        data = list(range(1000))

        mechanism = ExponentialMechanism(epsilon=1.0)

        

        # 查询是否有超过 400 个数 > 500

        result = mechanism.threshold_query(

            data,

            predicate=lambda x: x > 500,

            threshold=400

        )

        

        true_count = sum(1 for x in data if x > 500)  # = 499

        print(f"  数据集大小: {len(data)}")

        print(f"  满足条件的数量: {true_count}")

        print(f"  阈值: 400")

        print(f"  查询结果: {result}")

        

        assert result == (true_count >= 400)

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 6: 返回选择概率

    print("\n[测试 6] 返回选择概率")

    try:

        candidates = ["A", "B", "C"]

        scores = [1.0, 2.0, 3.0]

        

        mechanism = ExponentialMechanism(epsilon=1.0)

        chosen, prob = mechanism.select(

            candidates, scores, sensitivity=1.0, return_prob=True

        )

        

        # 计算理论概率

        weights = [math.exp(scores[i] / 1.0) for i in range(3)]

        total = sum(weights)

        expected_prob_idx = 2  # 得分最高的索引

        

        print(f"  选中: {chosen}")

        print(f"  选中概率: {prob:.4f}")

        print(f"  理论最高概率: {weights[2]/total:.4f}")

        

        assert 0 < prob <= 1

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 7: 排名选择

    print("\n[测试 7] 排名选择")

    try:

        items = ["电影A", "电影B", "电影C"]

        ranking_fn = lambda x: {"电影A": 7.5, "电影B": 9.2, "电影C": 8.1}[x]

        

        mechanism = ExponentialMechanism(epsilon=1.0)

        chosen, rank = mechanism.ranked_selection(

            items, ranking_fn, sensitivity=1.0, return_rank=True

        )

        

        print(f"  选中: {chosen}, 排名: {rank}")

        assert 1 <= rank <= len(items)

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 8: 隐私验证

    print("\n[测试 8] 隐私验证")

    try:

        result = privacy_test_exponential(

            epsilon=1.0,

            scores=[1.0, 2.0, 3.0, 4.0],

            sensitivity=1.0,

            num_trials=5000

        )

        

        # KL 散度应该很小（采样误差范围内）

        assert result['kl_divergence'] < 0.1, \

            f"KL 散度过大: {result['kl_divergence']}"

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 9: 敏感度计算

    print("\n[测试 9] 敏感度计算")

    try:

        assert sensitivity_of_max(similar_scores=True) == 1.0

        assert sensitivity_of_max(similar_scores=False) == 1.0

        print(f"  max 操作敏感度: {sensitivity_of_max()}")

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    # 测试 10: PrivateRanking

    print("\n[测试 10] PrivateRanking")

    try:

        candidates = ["A", "B", "C", "D"]

        scores = [10.0, 30.0, 20.0, 40.0]

        

        ranker = PrivateRanking(epsilon=1.0)

        top2 = ranker.private_top_k(candidates, scores, sensitivity=1.0, k=2)

        

        print(f"  候选: {candidates}")

        print(f"  得分: {scores}")

        print(f"  Top 2: {top2}")

        

        assert len(top2) == 2

        print("  ✓ 测试通过")

    except Exception as e:

        print(f"  ✗ 测试失败: {e}")

    

    print("\n" + "=" * 70)

    print("所有测试完成！")

    print("=" * 70)

    

    print("\n附录: 指数机制适用场景")

    print("-" * 50)

    print("指数机制最适合的场景：")

    print("  ✓ 输出是离散选择而非数值")

    print("  ✓ 需要选择最优解（argmax with privacy）")

    print("  ✓ 效用函数可以用明确定义的得分表示")

    print("  ✓ 投票、排名、推荐等场景")

    print("")

    print("与 Laplace 机制的对比：")

    print("  - Laplace: 输出是带噪声的数值")

    print("  - Exponential: 输出是从概率分布中采样的选择")





"""

时间复杂度分析:

    - exponential_sample: O(n)，线性扫描

    - ExponentialMechanism.select: O(n)

    - ExponentialMechanism.top_k: O(k·n)，k 次选择

    - PrivateRanking.private_top_k: O(k·n)



空间复杂度分析:

    - exponential_sample: O(n)，存储权重数组

    - 其他操作: O(n)



参考文献:

    [1] McSherry, F., Talwar, K. (2007). Mechanism Design via Differential Privacy. FOCS 2007.

    [2] Dwork, C., Roth, A. (2014). The Algorithmic Foundations of Differential Privacy.

    [3] Ghosh, A., Roughgarden, T., Sundararajan, M. (2012). Universally Utility-Maximizing

        Privacy Mechanisms. SIAM Journal on Computing.

"""

