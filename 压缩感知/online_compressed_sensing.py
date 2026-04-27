# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / online_compressed_sensing



本文件实现 online_compressed_sensing 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional

from dataclasses import dataclass





@dataclass

class StreamingSignal:

    """流式信号模型"""

    length: int

    sparsity: int

    current_position: int = 0

    support_history: list = None



    def __post_init__(self):

        self.support_history = []





class OnlineCS:

    """

    在线压缩感知恢复器

    策略：

    1. 滑动窗口：维护最近L个测量

    2. 增量更新：每个新测量到来时更新估计

    3. 支持追踪：跟踪信号支撑集变化

    """



    def __init__(self, n: int, m_window: int, s: int, A_init: Optional[np.ndarray] = None):

        self.n = n              # 信号维度

        self.m_window = m_window  # 滑动窗口大小

        self.s = s              # 稀疏度



        # 测量矩阵缓冲区

        if A_init is not None:

            self.A_buffer = A_init.copy()

        else:

            self.A_buffer = np.zeros((0, n))



        # 测量值缓冲区

        self.y_buffer = np.zeros(0)



        # 当前估计

        self.x_estimate = np.zeros(n)

        self.current_support = np.zeros(n, dtype=bool)



        # 统计

        self.update_count = 0



    def add_measurement(self, a_i: np.ndarray, y_i: float):

        """

        添加新的测量

        a_i: 新测量向量（n维）

        y_i: 测量值

        """

        # 滑动窗口：丢弃最旧测量

        if self.A_buffer.shape[0] >= self.m_window:

            # 移除第一行

            self.A_buffer = self.A_buffer[1:, :]

            self.y_buffer = self.y_buffer[1:]



        # 添加新测量

        self.A_buffer = np.vstack([self.A_buffer, a_i.reshape(1, -1)])

        self.y_buffer = np.append(self.y_buffer, y_i)



        self.update_count += 1



        # 更新估计

        self._update_estimate()



    def _update_estimate(self):

        """基于当前窗口更新信号估计"""

        m, n = self.A_buffer.shape



        if m < self.s:

            # 测量数不足，跳过

            return



        # 使用OMP恢复

        x_new = self._omp_recover(self.A_buffer, self.y_buffer, self.s)



        # 计算支撑变化

        new_support = np.abs(x_new) > 1e-6



        # 滑动平均（平滑估计）

        alpha = 0.7  # 平滑因子

        self.x_estimate = alpha * self.x_estimate + (1 - alpha) * x_new



    def _omp_recover(self, A: np.ndarray, y: np.ndarray, s: int) -> np.ndarray:

        """OMP恢复"""

        n = A.shape[1]

        x = np.zeros(n)

        support = []

        residual = y.copy()



        for _ in range(min(s, len(y))):

            c = A.T @ residual

            best_idx = np.argmax(np.abs(c))

            if best_idx in support:

                break

            support.append(best_idx)



            A_support = A[:, support]

            x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)



            residual = y - A_support @ x_support



        x[support] = x_support

        return x



    def get_current_estimate(self) -> np.ndarray:

        """获取当前信号估计"""

        return self.x_estimate.copy()



    def get_support(self) -> np.ndarray:

        """获取当前估计的支撑集"""

        return np.where(np.abs(self.x_estimate) > 1e-6)[0]





class AdaptiveSampling:

    """

    自适应采样策略

    根据当前估计选择最有信息量的测量方向

    """



    def __init__(self, n: int, A_fixed: np.ndarray):

        self.n = n

        self.A_fixed = A_fixed  # 候选测量方向

        self.confidence = np.ones(n)  # 每个方向的不确定性



    def select_next_measurement(self) -> Tuple[int, np.ndarray]:

        """

        选择下一个测量方向

        策略：选择当前最不确定的方向

        """

        # 基于不确定性加权选择

        weights = self.confidence / np.sum(self.confidence)

        idx = np.random.choice(self.n, p=weights)

        return idx, self.A_fixed[:, idx].reshape(-1)



    def update_confidence(self, x_estimate: np.ndarray):

        """

        根据当前估计更新不确定性

        非零系数方向的不确定性降低

        """

        active = np.abs(x_estimate) > 1e-6

        self.confidence[active] *= 0.9  # 降低不确定性

        self.confidence[~active] = min(self.confidence[~active] * 1.1, 1.0)  # 轻微增加





def running_median_filter(signal: np.ndarray, window: int) -> np.ndarray:

    """运行中位数滤波器（去除尖峰）"""

    n = len(signal)

    filtered = np.zeros(n)

    half = window // 2



    for i in range(n):

        lo = max(0, i - half)

        hi = min(n, i + half + 1)

        filtered[i] = np.median(signal[lo:hi])



    return filtered





class ChangeDetection:

    """支撑集变化检测"""



    def __init__(self, threshold: float = 0.3):

        self.threshold = threshold

        self.previous_support = None

        self.change_count = 0



    def detect(self, x_new: np.ndarray) -> bool:

        """

        检测信号变化

        返回True表示检测到显著变化

        """

        current_support = set(np.where(np.abs(x_new) > 1e-6)[0])



        if self.previous_support is None:

            self.previous_support = current_support

            return True



        # 计算Jaccard距离

        if len(current_support | self.previous_support) == 0:

            change = 0.0

        else:

            change = 1 - len(current_support & self.previous_support) / len(current_support | self.previous_support)



        has_change = change > self.threshold



        if has_change:

            self.change_count += 1

            self.previous_support = current_support



        return has_change





def test_online_cs():

    """测试在线压缩感知"""

    np.random.seed(42)



    n = 200    # 信号维度

    m_window = 50  # 滑动窗口大小

    s = 15     # 稀疏度

    n_iterations = 100  # 总测量数



    print("=== 在线压缩感知测试 ===")

    print(f"信号维度: {n}, 窗口大小: {m_window}, 稀疏度: {s}")



    # 创建测量矩阵

    A = np.random.randn(n_iterations + m_window, n) / np.sqrt(n)



    # 创建稀疏信号流（带支撑集变化）

    online_cs = OnlineCS(n, m_window, s)



    x_history = []

    support_changes = []



    for t in range(n_iterations):

        # 生成动态信号

        x_true = np.zeros(n)



        if t < 30:

            # 阶段1：固定支撑

            support = np.random.choice(n, s, replace=False)

            x_true[support] = np.random.randn(s)

        elif t < 60:

            # 阶段2：支撑缓慢变化

            support = np.random.choice(n, s, replace=False)

            x_true[support] = np.random.randn(s) * (0.5 + t / 60)

        else:

            # 阶段3：新支撑

            support = np.random.choice(n, s, replace=False)

            x_true[support] = np.random.randn(s)



        # 生成测量

        y = A[t] @ x_true + 0.01 * np.random.randn()



        # 添加到在线CS

        online_cs.add_measurement(A[t], y)



        # 记录

        x_est = online_cs.get_current_estimate()

        x_history.append(x_est)



        # 检测支撑变化

        cd = ChangeDetection()

        if cd.detect(x_est):

            support_changes.append(t)



    # 计算平均误差

    x_history_arr = np.array(x_history)

    # 简化：计算恢复信号的能量变化

    energy_history = np.array([np.linalg.norm(x) for x in x_history])



    print(f"\n运行结果:")

    print(f"  更新次数: {online_cs.update_count}")

    print(f"  检测到支撑变化: {len(support_changes)} 次")

    print(f"  能量变化范围: {energy_history.min():.2f} - {energy_history.max():.2f}")



    # 自适应采样测试

    print("\n--- 自适应采样测试 ---")

    A_candidates = np.random.randn(n, 50) / np.sqrt(n)

    sampler = AdaptiveSampling(n, A_candidates)



    for i in range(20):

        idx, a = sampler.select_next_measurement()

        if i < 5:

            print(f"  测量方向 {i}: idx={idx}, 不确定性={sampler.confidence[idx]:.3f}")



        # 模拟更新

        x_fake = np.zeros(n)

        fake_support = np.random.choice(n, 5, replace=False)

        x_fake[fake_support] = np.random.randn(5)

        sampler.update_confidence(x_fake)



    # 最终不确定性

    active = sampler.confidence < 0.5

    print(f"  高置信度方向数: {np.sum(active)}")





if __name__ == "__main__":

    test_online_cs()

