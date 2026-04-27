# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / change_point_detection

本文件实现 change_point_detection 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional


class CUSUMDetector:
    """
    CUSUM（累积和）变点检测器
    
    检测统计量: S_n = max(0, S_{n-1} + x_n - μ - k)
    当 S_n > h 时，触发报警
    
    参数:
        mu: 目标均值
        k: 参考值（允许偏差）
        h: 检测阈值
    """
    
    def __init__(self, mu: float = 0.0, k: float = 0.5, h: float = 5.0):
        self.mu = mu
        self.k = k
        self.h = h
        self.S = 0.0  # 累积和
        self.change_points = []  # 检测到的变点位置
        self.fitted = False
    
    def reset(self):
        """重置检测器状态"""
        self.S = 0.0
        self.change_points = []
    
    def detect(self, x: float) -> Tuple[float, bool]:
        """
        单点检测
        
        参数:
            x: 当前观测值
        
        返回:
            (当前累积和, 是否触发报警)
        """
        # 更新累积和
        self.S = max(0, self.S + x - self.mu - self.k)
        
        # 检测变点
        alarm = self.S > self.h
        
        if alarm:
            self.change_points.append(self.S)
            self.S = 0.0  # 重置
        
        return self.S, alarm
    
    def detect_batch(self, y: np.ndarray) -> dict:
        """
        批量检测
        
        参数:
            y: 时间序列
        
        返回:
            检测结果字典
        """
        self.reset()
        
        n = len(y)
        cusum_stats = np.zeros(n)
        alarms = np.zeros(n, dtype=bool)
        
        for i, x in enumerate(y):
            cusum_stats[i] = self.S
            _, alarm = self.detect(x)
            alarms[i] = alarm
        
        self.fitted = True
        
        return {
            'cusum_stats': cusum_stats,
            'alarms': alarms,
            'change_points': np.where(alarms)[0].tolist()
        }
    
    @staticmethod
    def estimate_change_point(y: np.ndarray, window: int = 50) -> int:
        """
        估计变点位置（离线版本，使用滑动窗口）
        
        参数:
            y: 时间序列
            window: 分析窗口大小
        
        返回:
            变点估计位置
        """
        n = len(y)
        scores = np.zeros(n - 2 * window)
        
        for i in range(window, n - window):
            # 窗口内均值差异
            left = y[i - window:i]
            right = y[i:i + window]
            
            # t统计量
            diff = np.mean(right) - np.mean(left)
            pooled_std = np.sqrt(np.var(left) / window + np.var(right) / window)
            
            scores[i - window] = abs(diff) / (pooled_std + 1e-10)
        
        return np.argmax(scores) + window


class PageHinkleyDetector:
    """
    Page-Hinkley变点检测器（在线）
    
    检测统计量: PH_n = PH_{n-1} + x_n - μ - ν
    当 PH_n > λ 时，触发报警
    
    参数:
        mu: 目标均值
        nu: 允许的漂移速率
        lambda_: 检测阈值
        alpha: 更新因子（遗忘因子）
    """
    
    def __init__(self, mu: float = 0.0, nu: float = 0.0, 
                 lambda_: float = 50.0, alpha: float = 0.99):
        self.mu = mu
        self.nu = nu
        self.lambda_ = lambda_
        self.alpha = alpha
        self.PH = 0.0  # 累积统计量
        self.x_bar = mu  # 移动均值估计
        self.change_points = []
        self.fitted = False
    
    def reset(self):
        """重置检测器"""
        self.PH = 0.0
        self.x_bar = self.mu
        self.change_points = []
    
    def detect(self, x: float, n: int = 1) -> Tuple[float, bool]:
        """
        单点检测
        
        参数:
            x: 当前观测值
            n: 时间步
        
        返回:
            (当前PH统计量, 是否报警)
        """
        # 更新移动均值
        self.x_bar = self.alpha * self.x_bar + (1 - self.alpha) * x
        
        # 更新PH统计量
        self.PH = self.PH + x - self.mu - self.nu - self.x_bar
        
        # 检测变点
        alarm = self.PH > self.lambda_
        
        if alarm:
            self.change_points.append(n)
            self.PH = 0.0  # 重置
        
        return self.PH, alarm
    
    def detect_batch(self, y: np.ndarray) -> dict:
        """
        批量检测
        
        参数:
            y: 时间序列
        
        返回:
            检测结果字典
        """
        self.reset()
        
        n = len(y)
        ph_stats = np.zeros(n)
        alarms = np.zeros(n, dtype=bool)
        
        for i, x in enumerate(y):
            ph_stats[i] = self.PH
            _, alarm = self.detect(x, i + 1)
            alarms[i] = alarm
        
        self.fitted = True
        
        return {
            'ph_stats': ph_stats,
            'alarms': alarms,
            'change_points': np.where(alarms)[0].tolist()
        }


class BinarySegmentation:
    """
    二叉分割变点检测（离线）
    
    通过递归二分寻找变点位置
    使用最小描述长度(MDL)或BIC作为分割准则
    
    参数:
        threshold: 分割阈值
        min_segment: 最小分段长度
    """
    
    def __init__(self, threshold: float = 0.05, min_segment: int = 30):
        self.threshold = threshold
        self.min_segment = min_segment
        self.change_points = []
    
    def cost_function(self, segment: np.ndarray) -> float:
        """
        计算分段代价（使用负对数似然）
        
        参数:
            segment: 数据片段
        
        返回:
            分段代价
        """
        n = len(segment)
        if n < 2:
            return 0
        
        var = np.var(segment)
        if var < 1e-10:
            var = 1e-10
        
        # 高斯负对数似然
        cost = n * 0.5 * np.log(2 * np.pi * var)
        return cost
    
    def find_best_split(self, y: np.ndarray, start: int, end: int) -> Tuple[float, int]:
        """
        在[start, end)区间内寻找最优分割点
        
        返回:
            (最小代价, 分割点位置)
        """
        best_cost = float('inf')
        best_split = -1
        
        for split in range(start + self.min_segment, end - self.min_segment):
            left = y[start:split]
            right = y[split:end]
            
            cost = self.cost_function(left) + self.cost_function(right)
            
            if cost < best_cost:
                best_cost = cost
                best_split = split
        
        return best_cost, best_split
    
    def fit(self, y: np.ndarray) -> list:
        """
        拟合模型，递归分割
        
        参数:
            y: 时间序列
        
        返回:
            变点位置列表
        """
        self.change_points = []
        
        def recursive_split(start: int, end: int, depth: int = 0):
            if end - start < 2 * self.min_segment:
                return
            
            cost, split = self.find_best_split(y, start, end)
            
            # 计算不分割的代价
            no_split_cost = self.cost_function(y[start:end])
            
            # 如果分割带来的代价减少显著，则接受分割
            if no_split_cost - cost > self.threshold * (end - start):
                self.change_points.append(split)
                recursive_split(start, split, depth + 1)
                recursive_split(split, end, depth + 1)
        
        recursive_split(0, len(y))
        self.change_points.sort()
        
        return self.change_points
    
    def predict(self) -> np.ndarray:
        """返回变点位置数组"""
        return np.array(self.change_points)


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("变点检测算法测试 - CUSUM & Page-Hinkley")
    print("=" * 50)
    
    np.random.seed(42)
    
    # 生成带有变点的测试数据
    n = 500
    
    # 第一段：均值0，方差1
    seg1 = np.random.randn(150) * 1 + 0
    
    # 变点1：均值从0跳到3
    seg2 = np.random.randn(150) * 1 + 3
    
    # 变点2：均值从3跳到-2
    seg3 = np.random.randn(200) * 1 - 2
    
    y = np.concatenate([seg1, seg2, seg3])
    true_change_points = [150, 300]
    
    print(f"\n数据生成: n={n}, 真实变点位置={true_change_points}")
    
    # CUSUM检测
    print("\n--- CUSUM检测 ---")
    cusum = CUSUMDetector(mu=0, k=0.5, h=10)
    result_cusum = cusum.detect_batch(y)
    print(f"检测到的变点: {result_cusum['change_points']}")
    
    # 离线估计变点
    est_cp = CUSUMDetector.estimate_change_point(y, window=50)
    print(f"离线估计变点: {est_cp}")
    
    # Page-Hinkley检测
    print("\n--- Page-Hinkley检测 ---")
    ph = PageHinkleyDetector(mu=0, nu=0.005, lambda_=30)
    result_ph = ph.detect_batch(y)
    print(f"检测到的变点: {result_ph['change_points']}")
    
    # 二叉分割检测
    print("\n--- 二叉分割检测 ---")
    binseg = BinarySegmentation(threshold=0.1, min_segment=30)
    cps = binseg.fit(y)
    print(f"检测到的变点: {cps}")
    
    print("\n" + "=" * 50)
    print("测试完成")
