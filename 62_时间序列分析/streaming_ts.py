# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / streaming_ts



本文件实现 streaming_ts 相关的算法功能。

"""



import numpy as np

from typing import Deque, Optional

from collections import deque

from dataclasses import dataclass





@dataclass

class StreamingStats:

    """流式统计结果"""

    mean: float

    variance: float

    std: float

    min: float

    max: float

    count: int





class StreamingMean:

    """

    流式均值计算器

    

    使用 Welford's online algorithm 精确计算

    """

    

    def __init__(self):

        self.count = 0

        self.mean = 0.0

        self.M2 = 0.0  # 平方偏差和

    

    def add(self, value: float) -> float:

        """

        添加新值，更新均值

        

        返回:

            当前均值

        """

        self.count += 1

        delta = value - self.mean

        self.mean += delta / self.count

        delta2 = value - self.mean

        self.M2 += delta * delta2

        

        return self.mean

    

    def get_variance(self) -> float:

        """获取方差"""

        if self.count < 2:

            return 0.0

        return self.M2 / (self.count - 1)

    

    def get_std(self) -> float:

        """获取标准差"""

        return np.sqrt(self.get_variance())

    

    def get_stats(self) -> StreamingStats:

        """获取完整统计"""

        return StreamingStats(

            mean=self.mean,

            variance=self.get_variance(),

            std=self.get_std(),

            min=0.0,  # 需要额外维护

            max=0.0,  # 需要额外维护

            count=self.count

        )





class SlidingWindowStats:

    """

    滑动窗口统计计算器

    

    维护固定大小的窗口，计算窗口内统计量

    """

    

    def __init__(self, window_size: int):

        self.window_size = window_size

        self.buffer = deque(maxlen=window_size)

        

        # Welford算法需要的变量

        self.mean = 0.0

        self.M2 = 0.0

        self.count = 0

    

    def add(self, value: float) -> StreamingStats:

        """

        添加新值，计算窗口统计

        

        返回:

            当前窗口统计

        """

        # 如果窗口已满，需要移除最老的值来更新统计

        if len(self.buffer) == self.window_size:

            old_value = self.buffer[0]

            self._remove(old_value)

        

        self.buffer.append(value)

        self._add(value)

        

        return self.get_stats()

    

    def _add(self, value: float):

        """Welford's online algorithm for adding"""

        self.count += 1

        delta = value - self.mean

        self.mean += delta / self.count

        delta2 = value - self.mean

        self.M2 += delta * delta2

    

    def _remove(self, value: float):

        """Welford's online algorithm for removing"""

        if self.count <= 1:

            self.count = 0

            self.mean = 0.0

            self.M2 = 0.0

            return

        

        old_count = self.count

        old_mean = self.mean

        

        self.count -= 1

        delta = value - self.mean

        self.mean = (old_count * old_mean - value) / self.count

        delta2 = value - self.mean

        self.M2 -= delta * delta2

    

    def get_stats(self) -> StreamingStats:

        """获取统计"""

        return StreamingStats(

            mean=self.mean,

            variance=self.M2 / max(1, self.count - 1),

            std=np.sqrt(self.M2 / max(1, self.count - 1)),

            min=min(self.buffer) if len(self.buffer) > 0 else 0.0,

            max=max(self.buffer) if len(self.buffer) > 0 else 0.0,

            count=len(self.buffer)

        )

    

    def get_all_values(self) -> np.ndarray:

        """获取窗口内所有值"""

        return np.array(self.buffer)





class ExponentialWeightedMean:

    """

    指数加权移动平均 (EWMA)

    

    y[t] = alpha * x[t] + (1 - alpha) * y[t-1]

    

    特点：

    - 越近期的数据权重越大

    - 无需存储历史数据

    """

    

    def __init__(self, alpha: float = 0.3):

        """

        参数:

            alpha: 平滑系数，范围(0, 1)

        """

        self.alpha = alpha

        self.ema = None

        self.count = 0

    

    def add(self, value: float) -> float:

        """

        添加新值，更新EMA

        

        返回:

            当前EMA

        """

        self.count += 1

        

        if self.ema is None:

            self.ema = value

        else:

            self.ema = self.alpha * value + (1 - self.alpha) * self.ema

        

        return self.ema

    

    def reset(self):

        """重置"""

        self.ema = None

        self.count = 0





class CUSUMOnline:

    """

    在线CUSUM变点检测

    

    用于检测均值漂移

    """

    

    def __init__(self, target_mean: float = 0.0, 

                 k: float = 0.5, h: float = 5.0):

        """

        参数:

            target_mean: 目标均值

            k: 参考值（允许偏差）

            h: 检测阈值

        """

        self.target_mean = target_mean

        self.k = k

        self.h = h

        

        self.S_pos = 0.0  # 正向累积和

        self.S_neg = 0.0  # 负向累积和

        self.change_points = []

        self.last_change_idx = 0

    

    def add(self, value: float, idx: Optional[int] = None) -> bool:

        """

        添加新值，检测变点

        

        返回:

            是否触发报警

        """

        # 更新正向累积和（大于目标）

        self.S_pos = max(0, self.S_pos + value - self.target_mean - self.k)

        

        # 更新负向累积和（小于目标）

        self.S_neg = max(0, self.S_neg - (value - self.target_mean) - self.k)

        

        alarm = (self.S_pos > self.h) or (self.S_neg > self.h)

        

        if alarm:

            self.change_points.append(idx if idx is not None else self.last_change_idx)

            self.S_pos = 0.0

            self.S_neg = 0.0

        

        self.last_change_idx += 1

        

        return alarm

    

    def reset(self):

        """重置"""

        self.S_pos = 0.0

        self.S_neg = 0.0

        self.change_points = []

        self.last_change_idx = 0





class StreamingAnomalyDetector:

    """

    流式异常检测器

    

    基于滑动窗口的Z分数检测

    """

    

    def __init__(self, window_size: int = 50, threshold: float = 3.0):

        self.window_size = window_size

        self.threshold = threshold

        self.window = SlidingWindowStats(window_size)

        self.is_anomaly = False

    

    def add(self, value: float) -> bool:

        """

        添加新值，检测异常

        

        返回:

            是否为异常

        """

        stats = self.window.add(value)

        

        if stats.count < 10:

            self.is_anomaly = False

        else:

            z_score = abs(value - stats.mean) / (stats.std + 1e-10)

            self.is_anomaly = z_score > self.threshold

        

        return self.is_anomaly





class OnlineSeasonalityDetector:

    """

    在线季节性检测

    

    检测数据中的周期性模式

    """

    

    def __init__(self, max_period: int = 100):

        self.max_period = max_period

        self.buffer = deque(maxlen=max_period * 2)

        self.period = 0

        self.confidence = 0.0

    

    def add(self, value: float) -> dict:

        """

        添加新值，尝试检测季节性

        

        返回:

            检测结果

        """

        self.buffer.append(value)

        

        result = {

            'detected': False,

            'period': 0,

            'confidence': 0.0

        }

        

        if len(self.buffer) < self.max_period:

            return result

        

        # 使用自相关检测周期

        buffer_array = np.array(self.buffer)

        

        # 计算自相关

        autocorr = []

        for lag in range(1, self.max_period):

            acf = np.corrcoef(buffer_array[:-lag], buffer_array[lag:])[0, 1]

            autocorr.append(acf if not np.isnan(acf) else 0)

        

        autocorr = np.array(autocorr)

        

        # 找第一个显著的正峰

        peaks = []

        for i in range(1, len(autocorr) - 1):

            if autocorr[i] > autocorr[i - 1] and autocorr[i] > autocorr[i + 1]:

                if autocorr[i] > 0.1:  # 阈值

                    peaks.append((i + 1, autocorr[i]))

        

        if peaks:

            # 选择自相关最高的峰

            peaks.sort(key=lambda x: x[1], reverse=True)

            self.period = peaks[0][0]

            self.confidence = peaks[0][1]

            

            result = {

                'detected': True,

                'period': self.period,

                'confidence': self.confidence

            }

        

        return result





class StreamingForecaster:

    """

    流式预测器

    

    基于简单指数平滑进行在线预测

    """

    

    def __init__(self, alpha: float = 0.3, h: int = 1):

        """

        参数:

            alpha: 平滑系数

            h: 预测步数

        """

        self.alpha = alpha

        self.h = h

        self.level = None

        self.trend = None

        self.count = 0

    

    def add(self, value: float) -> float:

        """

        添加新值，更新水平，更新预测

        

        返回:

            预测值

        """

        self.count += 1

        

        if self.level is None:

            self.level = value

            self.trend = 0

        else:

            # 更新水平

            new_level = self.alpha * value + (1 - self.alpha) * (self.level + self.trend)

            self.trend = (1 - self.alpha) * self.trend

            self.level = new_level

        

        # h步预测

        return self.level + self.h * self.trend





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("流式时间序列处理测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成测试数据：正常 + 变点 + 异常

    n = 500

    y = np.zeros(n)

    

    # 正常段

    y[:150] = np.random.randn(150) * 0.5

    # 变点：均值上移

    y[150:300] = 3 + np.random.randn(150) * 0.5

    # 变点：均值下移

    y[300:] = -2 + np.random.randn(200) * 0.5

    

    # 注入异常

    y[80] = 5

    y[230] = -5

    y[350] = 8

    

    print(f"\n数据生成: {n} 点, 含变点和异常")

    

    # 1. 流式均值

    print("\n--- 流式均值计算 ---")

    sm = StreamingMean()

    means = []

    for val in y[:100]:

        m = sm.add(val)

        means.append(m)

    print(f"前10个均值: {[f'{m:.3f}' for m in means[:10]]}")

    print(f"Welford方差: {sm.get_variance():.4f}, numpy方差: {np.var(y[:100]):.4f}")

    

    # 2. 滑动窗口统计

    print("\n--- 滑动窗口统计 ---")

    sw = SlidingWindowStats(window_size=50)

    for i in range(100):

        stats = sw.add(y[i])

        if i == 99:

            print(f"窗口[{i-49}, {i}] 统计: 均值={stats.mean:.3f}, 标准差={stats.std:.3f}")

    

    # 3. 在线CUSUM变点检测

    print("\n--- 在线CUSUM变点检测 ---")

    cusum = CUSUMOnline(target_mean=0, k=0.5, h=8)

    detected_cp = []

    for i, val in enumerate(y):

        alarm = cusum.add(val, i)

        if alarm:

            detected_cp.append(i)

    

    print(f"检测到的变点: {detected_cp}")

    print(f"真实变点: [150, 300]")

    

    # 4. 流式异常检测

    print("\n--- 流式异常检测 ---")

    detector = StreamingAnomalyDetector(window_size=30, threshold=3.0)

    anomalies = []

    for i, val in enumerate(y):

        is_anomaly = detector.add(val)

        if is_anomaly:

            anomalies.append(i)

    

    print(f"检测到的异常位置: {anomalies}")

    print(f"真实异常: [80, 230, 350]")

    

    # 5. 在线季节性检测

    print("\n--- 在线季节性检测 ---")

    seasonal = OnlineSeasonalityDetector(max_period=50)

    

    # 生成季节性数据

    seasonal_data = np.sin(np.linspace(0, 4 * np.pi, 200)) + np.random.randn(200) * 0.1

    

    detected = False

    for i, val in enumerate(seasonal_data):

        result = seasonal.add(val)

        if result['detected'] and not detected:

            print(f"在第{i}个点检测到周期: {result['period']}, 置信度: {result['confidence']:.3f}")

            detected = True

    

    # 6. 流式预测

    print("\n--- 流式预测 ---")

    forecaster = StreamingForecaster(alpha=0.3, h=1)

    predictions = []

    for val in y[:100]:

        pred = forecaster.add(val)

        predictions.append(pred)

    

    print(f"预测序列前5: {[f'{p:.3f}' for p in predictions[:5]]}")

    print(f"实际序列前5: {[f'{v:.3f}' for v in y[:5]]}")

    

    # 计算预测误差

    mse = np.mean((np.array(predictions) - y[:100])**2)

    print(f"预测MSE: {mse:.4f}")

    

    print("\n" + "=" * 50)

    print("测试完成")

