# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / prophet_simplified

本文件实现 prophet_simplified 相关的算法功能。
"""

import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class TrendConfig:
    """趋势配置"""
    growth: str = 'linear'        # 'linear' 或 'logistic'
    n_changepoints: int = 25      # 变点数量
    changepoint_prior: float = 0.05  # 变点先验强度
    cap: Optional[float] = None    # 上限（logistic增长用）
    floor: Optional[float] = None  # 下限


@dataclass
class SeasonalityConfig:
    """季节性配置"""
    yearly_seasonality: bool = True
    weekly_seasonality: bool = True
    daily_seasonality: bool = False
    yearly_fourier_order: int = 10
    weekly_fourier_order: int = 3
    daily_fourier_order: int = 4
    seasonality_prior: float = 10.0  # 季节性先验强度


class SimplifiedProphet:
    """
    Prophet简化版
    
    核心公式:
    y(t) = trend(t) + seasonality(t) + noise
    
    趋势: 分段线性回归 + 自动变点检测
    季节性: 傅里叶级数
    """
    
    def __init__(self, 
                 trend_config: Optional[TrendConfig] = None,
                 seasonality_config: Optional[SeasonalityConfig] = None):
        self.trend_config = trend_config or TrendConfig()
        self.seasonality_config = seasonality_config or SeasonalityConfig()
        
        # 拟合参数
        self.k = None   # 趋势增长率
        self.m = None   # 趋势偏移
        self.delta = None  # 变点增长率调整
        self.beta = None   # 季节性系数
        
        # 变点位置
        self.changepoints = None
        
        # 历史数据
        self.t = None
        self.y = None
    
    def _get_changepoints(self, t: np.ndarray) -> np.ndarray:
        """确定变点位置"""
        n = len(t)
        n_changepoints = self.trend_config.n_changepoints
        
        if n_changepoints > n:
            n_changepoints = n // 2
        
        # 均匀分布变点
        indices = np.linspace(n // 10, n * 9 // 10, n_changepoints).astype(int)
        
        return t[indices]
    
    def _linear_trend(self, t: np.ndarray) -> np.ndarray:
        """
        计算分段线性趋势
        
        y(t) = k + sum(delta_i * (t - s_i)_+) + m
        
        其中 s_i 是变点，delta_i 是增长率调整
        """
        k = self.k  # 基础增长率
        m = self.m  # 偏移
        delta = self.delta  # 变点调整
        s = self.changepoints  # 变点位置
        
        trend = k * t + m
        
        # 添加变点调整
        for i, s_i in enumerate(s):
            adjustment = delta[i] * np.maximum(t - s_i, 0)
            trend += adjustment
        
        return trend
    
    def _fourier_series(self, t: np.ndarray, period: float, n: int) -> np.ndarray:
        """
        傅里叶级数
        
        用于表示周期性季节性
        
        参数:
            t: 时间
            period: 周期长度
            n: 傅里叶阶数（项数）
        
        返回:
            傅里叶特征矩阵 (len(t), 2n)
        """
        features = []
        
        for k in range(1, n + 1):
            features.append(np.sin(2 * np.pi * k * t / period))
            features.append(np.cos(2 * np.pi * k * t / period))
        
        return np.column_stack(features)
    
    def _compute_seasonality_features(self, t: np.ndarray) -> List[np.ndarray]:
        """计算各季节性成分的特征"""
        features = []
        config = self.seasonality_config
        
        if config.yearly_seasonality:
            features.append(self._fourier_series(t, 365.25, config.yearly_fourier_order))
        
        if config.weekly_seasonality:
            features.append(self._fourier_series(t, 7, config.weekly_fourier_order))
        
        if config.daily_seasonality:
            features.append(self._fourier_series(t, 24, config.daily_fourier_order))
        
        return features
    
    def fit(self, t: np.ndarray, y: np.ndarray) -> dict:
        """
        拟合模型
        
        参数:
            t: 时间戳（可以是天数）
            y: 观测值
        
        返回:
            拟合结果
        """
        self.t = np.array(t, dtype=float)
        self.y = np.array(y, dtype=float)
        n = len(t)
        
        # 初始化趋势参数
        self.k = (y[-1] - y[0]) / (t[-1] - t[0] + 1e-10)
        self.m = y[0]
        
        # 变点
        self.changepoints = self._get_changepoints(t)
        n_changepoints = len(self.changepoints)
        
        # 变点调整
        self.delta = np.zeros(n_changepoints)
        
        # 季节性特征
        seasonality_features = self._compute_seasonality_features(self.t)
        n_seasonal = sum(f.shape[1] for f in seasonality_features)
        
        # 构建设计矩阵
        # 趋势特征：t + 变点调整
        trend_features = np.column_stack([
            self.t,
            *[np.maximum(self.t - s, 0) for s in self.changepoints]
        ])
        
        # 合并所有特征
        if seasonality_features:
            all_features = np.hstack([trend_features] + seasonality_features)
        else:
            all_features = trend_features
        
        # 使用贝叶斯回归估计参数（简化版：使用OLS + 正则化）
        # 构建回归：y = X @ theta + noise
        
        # 先拟合趋势（粗略）
        X_trend = trend_features
        theta_trend = np.linalg.lstsq(X_trend, y, rcond=None)[0]
        
        # 分离趋势残差
        trend = X_trend @ theta_trend
        residual = y - trend
        
        # 拟合季节性
        if seasonality_features:
            X_seasonal = np.hstack(seasonality_features)
            # 正则化拟合
            lambda_reg = self.seasonality_config.seasonality_prior
            XTX = X_seasonal.T @ X_seasonal + lambda_reg * np.eye(X_seasonal.shape[1])
            XTy = X_seasonal.T @ residual
            self.beta = np.linalg.solve(XTX + 1e-6, XTy)
        
        # 更新趋势参数
        self.k = theta_trend[0]
        self.m = theta_trend[1]
        
        # 计算残差
        y_pred = self._linear_trend(self.t)
        if self.beta is not None and len(seasonality_features) > 0:
            seasonal = np.hstack(seasonality_features) @ self.beta
            y_pred += seasonal
        
        residuals = y - y_pred
        
        # 评估
        sse = np.sum(residuals ** 2)
        sigma2 = sse / n
        
        return {
            'k': self.k,
            'm': self.m,
            'delta': self.delta,
            'beta': self.beta,
            'sigma2': sigma2,
            'residuals': residuals
        }
    
    def predict(self, t_new: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        预测
        
        参数:
            t_new: 新时间点
        
        返回:
            (预测值, 预测不确定性)
        """
        t_new = np.array(t_new, dtype=float)
        
        # 趋势预测
        trend_pred = self._linear_trend(t_new)
        
        # 季节性预测
        seasonal_pred = np.zeros(len(t_new))
        if self.beta is not None:
            seasonality_features = self._compute_seasonality_features(t_new)
            if seasonality_features:
                X = np.hstack(seasonality_features)
                seasonal_pred = X @ self.beta
        
        # 总预测
        y_pred = trend_pred + seasonal_pred
        
        # 简单的不确定性估计（假设噪声方差恒定）
        sigma2 = getattr(self, 'sigma2', 1.0)
        uncertainty = np.sqrt(sigma2) * np.ones(len(t_new))
        
        return y_pred, uncertainty


def generate_prophet_data(n: int = 300, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    生成类似Prophet的测试数据
    
    包含：趋势变化 + 年度季节性 + 周季节性 + 噪声
    
    参数:
        n: 数据点数量
        seed: 随机种子
    
    返回:
        (t, y)
    """
    np.random.seed(seed)
    
    t = np.arange(n)
    
    # 趋势：带有变点的线性增长
    trend = 10 + 0.05 * t
    
    # 变点1（第100天）：增长率增加
    changepoint1 = 100
    trend[changepoint1:] += 0.03 * (t[changepoint1:] - t[changepoint1])
    
    # 变点2（第200天）：增长率减少
    changepoint2 = 200
    trend[changepoint2:] -= 0.04 * (t[changepoint2:] - t[changepoint2])
    
    # 年度季节性（傅里叶）
    yearly = (2.5 * np.sin(2 * np.pi * t / 365.25) + 
              1.2 * np.sin(4 * np.pi * t / 365.25) +
              0.8 * np.sin(6 * np.pi * t / 365.25))
    
    # 周季节性
    weekly = 1.5 * np.sin(2 * np.pi * (t % 7) / 7)
    
    # 噪声
    noise = np.random.randn(n) * 0.8
    
    y = trend + yearly + weekly + noise
    
    return t, y


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("Prophet简化版测试")
    print("=" * 50)
    
    # 生成测试数据
    t, y = generate_prophet_data(n=300)
    
    print(f"\n数据生成: n={len(y)}")
    print(f"数据范围: [{np.min(y):.2f}, {np.max(y):.2f}]")
    
    # 拟合
    print("\n--- 拟合模型 ---")
    model = SimplifiedProphet()
    result = model.fit(t, y)
    
    print(f"趋势增长率 k: {result['k']:.4f}")
    print(f"趋势偏移 m: {result['m']:.4f}")
    print(f"残差方差: {result['sigma2']:.4f}")
    
    # 预测
    print("\n--- 预测未来30天 ---")
    t_future = np.arange(300, 330)
    y_pred, y_uncertainty = model.predict(t_future)
    
    print(f"预测值前5天: {y_pred[:5]}")
    print(f"不确定性前5天: {y_uncertainty[:5]}")
    
    # 预测与真实值对比（生成更多数据）
    t_full, y_full = generate_prophet_data(n=330, seed=42)
    mae = np.mean(np.abs(y_pred - y_full[300:]))
    print(f"\n预测MAE: {mae:.2f}")
    
    print("\n" + "=" * 50)
    print("测试完成")
