# -*- coding: utf-8 -*-
"""
算法实现：时间序列分析 / sarima_model

本文件实现 sarima_model 相关的算法功能。
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional


class SARIMAModel:
    """SARIMA模型类"""
    
    def __init__(self, p: int = 1, d: int = 1, q: int = 1, 
                 P: int = 1, D: int = 1, Q: int = 1, s: int = 12):
        """
        初始化SARIMA模型
        
        参数:
            p: 非季节性AR阶数
            d: 非季节性差分阶数
            q: 非季节性MA阶数
            P: 季节性AR阶数
            D: 季节性差分阶数
            Q: 季节性MA阶数
            s: 季节周期
        """
        self.p, self.d, self.q = p, d, q
        self.P, self.D, self.Q, self.s = P, D, Q, s
        self.ar_params = None
        self.seasonal_ar_params = None
        self.ma_params = None
        self.seasonal_ma_params = None
        self.residuals = None
        self.fitted = False
    
    def seasonal_difference(self, y: np.ndarray, s: int, D: int = 1) -> np.ndarray:
        """
        季节性差分
        
        参数:
            y: 原始序列
            s: 季节周期
            D: 季节差分阶数
        
        返回:
            季节差分后的序列
        """
        y_diff = y.copy()
        for _ in range(D):
            y_diff = y_diff[s:] - y_diff[:-s]
        return y_diff
    
    def difference(self, y: np.ndarray, d: int = 1) -> np.ndarray:
        """
        常规差分
        
        参数:
            y: 原始序列
            d: 差分阶数
        
        返回:
            差分后的序列
        """
        y_diff = y.copy()
        for _ in range(d):
            y_diff = np.diff(y_diff)
        return y_diff
    
    def fit(self, y: np.ndarray) -> dict:
        """
        拟合SARIMA模型
        
        参数:
            y: 时间序列数据
        
        返回:
            拟合结果字典
        """
        n = len(y)
        
        # 1. 季节性差分
        if self.D > 0:
            y_sd = self.seasonal_difference(y, self.s, self.D)
        else:
            y_sd = y.copy()
        
        # 2. 常规差分
        if self.d > 0:
            y_diff = self.difference(y_sd, self.d)
        else:
            y_diff = y_sd.copy()
        
        T = len(y_diff)
        
        # 构建回归矩阵
        # 非季节性AR: p个滞后
        # 季节性AR: P个滞后（s, 2s, ...）
        # 非季节性MA: q个滞后
        # 季节性MA: Q个滞后（s, 2s, ...）
        
        total_params = self.p + self.P + self.q + self.Q
        max_lag = max(self.p + self.P * self.s, self.q + self.Q * self.s, 1)
        
        if max_lag >= T:
            raise ValueError(f"数据点不足，无法拟合")
        
        X = np.zeros((T - max_lag, total_params))
        Y = y_diff[max_lag:]
        
        col_idx = 0
        
        # 非季节性AR项
        for i in range(1, self.p + 1):
            X[:, col_idx] = y_diff[max_lag - i : T - i]
            col_idx += 1
        
        # 季节性AR项
        for i in range(1, self.P + 1):
            X[:, col_idx] = y_diff[max_lag - i * self.s : T - i * self.s]
            col_idx += 1
        
        # MA项使用残差迭代，这里简化为0
        # 完整实现需要迭代估计
        
        # 最小二乘估计
        XTX = X.T @ X
        XTY = X.T @ Y
        XTX += np.eye(total_params) * 1e-6
        
        all_params = np.linalg.solve(XTX, XTY)
        
        # 分离参数
        self.ar_params = all_params[:self.p] if self.p > 0 else np.array([])
        seasonal_ar_idx = self.p
        self.seasonal_ar_params = all_params[seasonal_ar_idx:seasonal_ar_idx + self.P] if self.P > 0 else np.array([])
        ma_idx = seasonal_ar_idx + self.P
        self.ma_params = all_params[ma_idx:ma_idx + self.q] if self.q > 0 else np.array([])
        self.seasonal_ma_params = all_params[ma_idx + self.q:] if self.Q > 0 else np.array([])
        
        # 计算残差
        self.residuals = Y - X @ all_params
        
        # 统计量
        sigma2 = np.var(self.residuals)
        n_params = total_params + 1
        aic = len(y) * np.log(sigma2) + 2 * n_params
        bic = len(y) * np.log(sigma2) + n_params * np.log(len(y))
        
        self.fitted = True
        
        return {
            'ar_params': self.ar_params,
            'seasonal_ar_params': self.seasonal_ar_params,
            'ma_params': self.ma_params,
            'seasonal_ma_params': self.seasonal_ma_params,
            'sigma2': sigma2,
            'aic': aic,
            'bic': bic,
            'residuals': self.residuals
        }
    
    def predict(self, n_periods: int, y_history: np.ndarray) -> np.ndarray:
        """
        预测未来n_periods个时间点
        
        参数:
            n_periods: 预测步数
            y_history: 历史数据
        
        返回:
            预测值数组
        """
        if not self.fitted:
            raise ValueError("模型尚未拟合")
        
        # 对历史数据进行差分
        if self.D > 0:
            y_sd = self.seasonal_difference(y_history, self.s, self.D)
        else:
            y_sd = y_history.copy()
        
        if self.d > 0:
            y_diff = self.difference(y_sd, self.d)
        else:
            y_diff = y_sd.copy()
        
        predictions = []
        history = list(y_diff)
        
        for _ in range(n_periods):
            pred = 0
            
            # 非季节性AR
            for i, phi in enumerate(self.ar_params):
                if len(history) > self.p:
                    pred += phi * history[-(i + 1)]
            
            # 季节性AR
            for i, phi in enumerate(self.seasonal_ar_params):
                lag = (i + 1) * self.s
                if len(history) > lag:
                    pred += phi * history[-lag]
            
            predictions.append(pred)
            history.append(pred)
        
        # 逆差分（简化）
        # 实际实现需要逐级逆差分
        
        return np.array(predictions)


def generate_seasonal_data(n: int = 120, phi: float = 0.6, 
                           seasonal_phi: float = 0.3, s: int = 12) -> np.ndarray:
    """
    生成带有季节性的模拟时间序列
    
    参数:
        n: 数据点数量
        phi: AR参数
        seasonal_phi: 季节性AR参数
        s: 季节周期
    
    返回:
        模拟数据
    """
    np.random.seed(42)
    y = np.zeros(n)
    
    for t in range(n):
        # 非季节性部分
        ar_term = phi * y[t-1] if t > 0 else 0
        noise = np.random.randn() * 0.5
        
        # 季节性部分
        seasonal_term = 0
        if t >= s and seasonal_phi != 0:
            seasonal_term = seasonal_phi * y[t-s]
        
        y[t] = 10 + ar_term + seasonal_term + noise
    
    return y


def seasonal_decompose(y: np.ndarray, s: int = 12) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    简单的季节性分解（加法模型）
    
    参数:
        y: 时间序列
        s: 季节周期
    
    返回:
        (趋势, 季节性, 残差)
    """
    n = len(y)
    
    # 移动平均计算趋势
    kernel = np.ones(s) / s
    trend = np.convolve(y, kernel, mode='same')
    
    # 季节因子
    seasonal_factors = np.zeros(s)
    for i in range(s):
        indices = np.arange(i, n, s)
        seasonal_factors[i] = np.mean(y[indices] - trend[indices])
    
    seasonal = np.tile(seasonal_factors, n // s + 1)[:n]
    
    # 残差
    residual = y - trend - seasonal
    
    return trend, seasonal, residual


# 测试代码
if __name__ == "__main__":
    print("=" * 50)
    print("SARIMA模型测试")
    print("=" * 50)
    
    # 生成月度季节性数据
    y = generate_seasonal_data(n=120, phi=0.5, seasonal_phi=0.4, s=12)
    
    print(f"\n数据统计: n={len(y)}, 均值={np.mean(y):.2f}, 标准差={np.std(y):.2f}")
    
    # 季节性分解
    trend, seasonal, residual = seasonal_decompose(y, s=12)
    print(f"\n季节性分解:")
    print(f"  趋势均值: {np.mean(trend):.2f}")
    print(f"  季节因子范围: [{np.min(seasonal):.2f}, {np.max(seasonal):.2f}]")
    print(f"  残差标准差: {np.std(residual):.2f}")
    
    # 拟合SARIMA模型
    model = SARIMAModel(p=1, d=1, q=1, P=1, D=1, Q=1, s=12)
    result = model.fit(y)
    
    print(f"\nSARIMA(1,1,1)(1,1,1)12 拟合结果:")
    print(f"  AR参数: {result['ar_params']}")
    print(f"  季节AR参数: {result['seasonal_ar_params']}")
    print(f"  AIC: {result['aic']:.2f}")
    
    # 预测
    forecast = model.predict(n_periods=12, y_history=y)
    print(f"\n未来12期预测（季节性）:")
    print(f"  前6期: {forecast[:6]}")
    print(f"  后6期: {forecast[6:]}")
