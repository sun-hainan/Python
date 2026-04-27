# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / time_series_segmentation

本文件实现 time_series_segmentation 相关的算法功能。
"""

import numpy as np
from typing import Tuple, List, Optional
from scipy.spatial.distance import euclidean


class SlidingWindowSegmenter:
    """
    滑动窗口分割器
    
    将时间序列按固定窗口大小切分
    
    参数:
        window_size: 窗口大小
        step: 滑动步长
    """
    
    def __init__(self, window_size: int = 50, step: Optional[int] = None):
        self.window_size = window_size
        self.step = step if step is not None else window_size // 2
    
    def segment(self, y: np.ndarray) -> List[np.ndarray]:
        """
        执行滑动窗口分割
        
        参数:
            y: 时间序列
        
        返回:
            片段列表
        """
        n = len(y)
        segments = []
        
        start = 0
        while start + self.window_size <= n:
            segment = y[start:start + self.window_size]
            segments.append(segment)
            start += self.step
        
        return segments
    
    def segment_with_labels(self, y: np.ndarray, labels: np.ndarray) -> List[Tuple[np.ndarray, int]]:
        """
        分割并保留标签
        
        返回:
            [(片段, 标签)] 列表
        """
        n = len(y)
        result = []
        
        start = 0
        while start + self.window_size <= n:
            segment = y[start:start + self.window_size]
            # 使用窗口中心的标签
            center_idx = start + self.window_size // 2
            label = labels[center_idx]
            result.append((segment, label))
            start += self.step
        
        return result


class OnlineSlidingWindow:
    """
    在线滑动窗口 - 用于流式数据处理
    
    维护一个固定大小的窗口，支持流式更新
    
    参数:
        size: 窗口大小
    """
    
    def __init__(self, size: int = 50):
        self.size = size
        self.buffer = []
        self.values = np.array([])
    
    def add(self, value: float):
        """添加新数据点"""
        self.buffer.append(value)
        self.values = np.array(self.buffer[-self.size:])
    
    def get_window(self) -> np.ndarray:
        """获取当前窗口"""
        return self.values
    
    def get_features(self) -> dict:
        """计算窗口特征"""
        if len(self.values) < 2:
            return {}
        
        return {
            'mean': np.mean(self.values),
            'std': np.std(self.values),
            'min': np.min(self.values),
            'max': np.max(self.values),
            'median': np.median(self.values),
            'trend': self.values[-1] - self.values[0] if len(self.values) > 1 else 0
        }


class BottomUpSegmenter:
    """
    自底向上分割算法
    
    1. 初始将序列分为n个单点段
    2. 计算相邻段的距离
    3. 合并距离最小的相邻段
    4. 重复直到达到目标段数
    
    参数:
        distance_func: 段间距离函数
        n_segments: 目标段数
    """
    
    def __init__(self, n_segments: int = 5, distance_func: Optional[callable] = None):
        self.n_segments = n_segments
        self.distance_func = distance_func or self._default_distance
    
    @staticmethod
    def _default_distance(seg1: np.ndarray, seg2: np.ndarray) -> float:
        """默认距离：两个段首尾差的绝对值"""
        return abs(seg1[-1] - seg2[0])
    
    def fit(self, y: np.ndarray) -> Tuple[List[np.ndarray], List[int]]:
        """
        拟合模型
        
        参数:
            y: 时间序列
        
        返回:
            (分段列表, 分段起始位置列表)
        """
        n = len(y)
        
        # 初始化：每个点作为一段
        segments = [[i] for i in range(n)]
        
        # 计算相邻段间的距离
        distances = []
        for i in range(len(segments) - 1):
            d = self.distance_func(y[segments[i]], y[segments[i+1]])
            distances.append(d)
        
        # 迭代合并
        while len(segments) > self.n_segments:
            # 找到距离最小的相邻段
            min_idx = np.argmin(distances)
            
            # 合并
            segments[min_idx] = segments[min_idx] + segments[min_idx + 1]
            segments.pop(min_idx + 1)
            
            # 更新距离
            if min_idx > 0:
                d = self.distance_func(y[segments[min_idx - 1]], y[segments[min_idx]])
                distances[min_idx - 1] = d
            
            if min_idx < len(distances) - 1:
                d = self.distance_func(y[segments[min_idx]], y[segments[min_idx + 1]])
                distances[min_idx] = d
            
            if min_idx < len(distances) - 1:
                distances.pop(min_idx + 1)
        
        # 提取分段
        result_segments = [np.array(y[s]) for s in segments]
        boundaries = [s[0] for s in segments]
        
        return result_segments, boundaries


class SWABSegmenter:
    """
    SWAB (Sliding Window And Bottom-Up) 分割算法
    
    结合滑动窗口和自底向上的优点
    
    参数:
        window_size: 窗口大小
        max_distance: 最大允许段内距离
    """
    
    def __init__(self, window_size: int = 100, max_distance: float = 2.0):
        self.window_size = window_size
        self.max_distance = max_distance
    
    def segment(self, y: np.ndarray) -> Tuple[List[np.ndarray], List[int]]:
        """
        执行SWAB分割
        
        参数:
            y: 时间序列
        
        返回:
            (分段列表, 边界位置列表)
        """
        n = len(y)
        segments = []
        boundaries = []
        
        start = 0
        
        while start < n:
            # 取一个窗口
            end = min(start + self.window_size, n)
            window = y[start:end]
            
            # 自底向上合并
            segs = [[i] for i in range(len(window))]
            distances = []
            
            for i in range(len(segs) - 1):
                d = abs(window[segs[i][-1]] - window[segs[i+1][0]])
                distances.append(d)
            
            while len(segs) > 2:
                min_idx = np.argmin(distances)
                if distances[min_idx] > self.max_distance:
                    break
                
                segs[min_idx] = segs[min_idx] + segs[min_idx + 1]
                segs.pop(min_idx + 1)
                
                if min_idx > 0:
                    distances[min_idx - 1] = abs(window[segs[min_idx - 1][-1]] - window[segs[min_idx][0]])
                if min_idx < len(distances) - 1:
                    distances[min_idx] = abs(window[segs[min_idx][-1]] - window[segs[min_idx + 1][0]])
                
                if min_idx < len(distances) - 1:
                    distances.pop(min_idx + 1)
            
            # 保留第一个完整段
            seg = window[segs[0]]
            segments.append(seg)
            boundaries.append(start)
            
            start += len(seg)
        
        return segments, boundaries


def piecewise_aggregate_approximation(y: np.ndarray, n_segments: int) -> np.ndarray:
    """
    分段聚合近似（PAA）
    
    将时间序列映射到低维空间
    
    参数:
        y: 时间序列
        n_segments: 分段数
    
    返回:
        降维后的序列
    """
    n = len(y)
    segment_size = n / n_segments
    
    result = np.zeros(n_segments)
    
    for i in range(n_segments):
        start = int(i * segment_size)
        end = int((i + 1) * segment_size)
        result[i] = np.mean(y[start:end])
    
    return result


def sax_representation(y: np.ndarray, n_segments: int, alphabet_size: int = 4) -> str:
    """
    符号聚合近似（SAX）
    
    将连续值转换为符号序列
    
    参数:
        y: 时间序列
        n_segments: 分段数
        alphabet_size: 字母表大小
    
    返回:
        符号字符串
    """
    # PAA降维
    paa = piecewise_aggregate_approximation(y, n_segments)
    
    # 计算分位数断点
    breakpoints = np.zeros(alphabet_size - 1)
    for i in range(1, alphabet_size):
        breakpoints[i - 1] = np.percentile(paa, i * 100 / alphabet_size)
    
    # 映射到符号
    symbols = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = []
    
    for val in paa:
        for i, bp in enumerate(breakpoints):
            if val < bp:
                result.append(symbols[i])
                break
        else:
            result.append(symbols[alphabet_size - 1])
    
    return ''.join(result)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("时间序列分割测试")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 生成多段测试数据
    n = 300
    
    # 段1：低幅高频
    seg1 = np.sin(np.linspace(0, 4 * np.pi, 100)) * 2
    # 段2：高幅低频
    seg2 = np.sin(np.linspace(0, 2 * np.pi, 100)) * 5
    # 段3：随机游走
    seg3 = np.cumsum(np.random.randn(100) * 0.5)
    # 段4：线性趋势
    seg4 = np.linspace(0, 5, 100)
    
    y = np.concatenate([seg1, seg2, seg3, seg4])
    true_boundaries = [100, 200, 300]
    
    print(f"\n数据生成: n={len(y)}, 真实边界={true_boundaries}")
    
    # 滑动窗口分割
    print("\n--- 滑动窗口分割 ---")
    sw = SlidingWindowSegmenter(window_size=30, step=15)
    segments = sw.segment(y)
    print(f"分割成 {len(segments)} 个片段")
    print(f"片段形状: {[s.shape for s in segments[:3]]}...")
    
    # 在线滑动窗口
    print("\n--- 在线滑动窗口测试 ---")
    online_window = OnlineSlidingWindow(size=20)
    for i in range(50):
        online_window.add(y[i])
    features = online_window.get_features()
    print(f"窗口特征: 均值={features['mean']:.2f}, 标准差={features['std']:.2f}")
    
    # 自底向上分割
    print("\n--- 自底向上分割 ---")
    bub = BottomUpSegmenter(n_segments=4)
    segments, boundaries = bub.fit(y)
    print(f"检测到的边界: {boundaries}")
    
    # SWAB分割
    print("\n--- SWAB分割 ---")
    swab = SWABSegmenter(window_size=80, max_distance=1.5)
    segments, boundaries = swab.segment(y)
    print(f"分割成 {len(segments)} 段")
    print(f"边界位置: {boundaries}")
    
    # PAA降维
    print("\n--- PAA降维 ---")
    paa = piecewise_aggregate_approximation(y, n_segments=20)
    print(f"PAA序列: {paa[:5]}...")
    
    # SAX符号化
    print("\n--- SAX符号表示 ---")
    sax = sax_representation(y, n_segments=30, alphabet_size=5)
    print(f"SAX表示: {sax[:50]}...")
    
    print("\n" + "=" * 50)
    print("测试完成")
