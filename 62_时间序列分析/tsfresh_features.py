# -*- coding: utf-8 -*-

"""

算法实现：时间序列分析 / tsfresh_features



本文件实现 tsfresh_features 相关的算法功能。

"""



import numpy as np

from typing import Dict, List, Optional

from scipy import stats





class FeatureExtractor:

    """时间序列特征提取基类"""

    

    @staticmethod

    def compute_statistics(y: np.ndarray) -> Dict[str, float]:

        """计算基础统计特征"""

        return {

            'mean': np.mean(y),

            'std': np.std(y),

            'var': np.var(y),

            'min': np.min(y),

            'max': np.max(y),

            'median': np.median(y),

            'q25': np.percentile(y, 25),

            'q75': np.percentile(y, 75),

            'iqr': np.percentile(y, 75) - np.percentile(y, 25),

            'skewness': stats.skew(y),

            'kurtosis': stats.kurtosis(y),

        }

    

    @staticmethod

    def compute_trend(y: np.ndarray) -> Dict[str, float]:

        """计算趋势特征"""

        t = np.arange(len(y))

        

        # 线性拟合

        slope, intercept, r_value, p_value, std_err = stats.linregress(t, y)

        

        return {

            'slope': slope,

            'intercept': intercept,

            'r_value': r_value,

            'p_value': p_value,

            'std_err': std_err,

            'abs_slope': abs(slope)

        }

    

    @staticmethod

    def compute_energy(y: np.ndarray) -> Dict[str, float]:

        """计算能量相关特征"""

        n = len(y)

        

        # 时域能量

        energy = np.sum(y ** 2)

        

        # 频域能量

        fft_vals = np.fft.fft(y)

        fft_energy = np.sum(np.abs(fft_vals[:n // 2]) ** 2)

        

        # 主频率能量比例

        fft_magnitude = np.abs(fft_vals[:n // 2])

        total_energy = np.sum(fft_magnitude)

        

        dominant_freq_idx = np.argmax(fft_magnitude[1:]) + 1

        dominant_energy = fft_magnitude[dominant_freq_idx]

        dominant_ratio = dominant_energy / (total_energy + 1e-10)

        

        return {

            'energy': energy,

            'fft_energy': fft_energy,

            'dominant_freq_idx': dominant_freq_idx,

            'dominant_energy_ratio': dominant_ratio

        }

    

    @staticmethod

    def compute_entropy(y: np.ndarray, n_bins: int = 10) -> Dict[str, float]:

        """计算熵特征"""

        # 直方图熵

        hist, _ = np.histogram(y, bins=n_bins)

        hist = hist / (np.sum(hist) + 1e-10)

        hist = hist[hist > 0]

        

        shannon_entropy = -np.sum(hist * np.log2(hist))

        

        # 谱熵

        n = len(y)

        fft_vals = np.abs(np.fft.fft(y)[:n // 2])

        psd = fft_vals / (np.sum(fft_vals) + 1e-10)

        psd = psd[psd > 0]

        

        spectral_entropy = -np.sum(psd * np.log2(psd))

        

        return {

            'shannon_entropy': shannon_entropy,

            'spectral_entropy': spectral_entropy,

            'entropy_ratio': spectral_entropy / (np.log2(n) + 1e-10)

        }

    

    @staticmethod

    def compute_autocorrelation(y: np.ndarray, max_lag: int = 20) -> Dict[str, float]:

        """计算自相关特征"""

        n = len(y)

        

        acf_values = []

        for lag in range(1, max_lag + 1):

            if lag >= n:

                break

            acf = np.corrcoef(y[:-lag], y[lag:])[0, 1]

            acf_values.append(acf if not np.isnan(acf) else 0)

        

        acf_values = np.array(acf_values)

        

        # 找第一个过零的滞后

        zero_crossings = np.where(np.diff(np.signbit(acf_values)))[0]

        first_zero = zero_crossings[0] + 1 if len(zero_crossings) > 0 else max_lag

        

        return {

            'acf_first': acf_values[0] if len(acf_values) > 0 else 0,

            'acf_sum': np.sum(acf_values),

            'acf_max': np.max(acf_values),

            'acf_first_zero_lag': first_zero,

            'acf_positive_count': np.sum(acf_values > 0)

        }

    

    @staticmethod

    def compute_change_features(y: np.ndarray) -> Dict[str, float]:

        """计算变化相关特征"""

        # 一阶差分

        diff = np.diff(y)

        

        # 变化率统计

        mean_change = np.mean(diff)

        std_change = np.std(diff)

        max_increase = np.max(diff)

        max_decrease = np.min(diff)

        

        # 变点数量（差分符号变化）

        sign_changes = np.sum(np.diff(np.signbit(diff)) != 0)

        

        # 绝对变化之和

        total_variation = np.sum(np.abs(diff))

        

        return {

            'mean_change': mean_change,

            'std_change': std_change,

            'max_increase': max_increase,

            'max_decrease': max_decrease,

            'sign_changes': sign_changes,

            'total_variation': total_variation

        }

    

    @staticmethod

    def compute_peaks_features(y: np.ndarray) -> Dict[str, float]:

        """计算峰值特征"""

        n = len(y)

        

        # 找局部极值点

        is_peak = (y[1:-1] > y[:-2]) & (y[1:-1] > y[2:])

        peak_indices = np.where(is_peak)[0] + 1

        

        n_peaks = len(peak_indices)

        peak_heights = y[peak_indices] if n_peaks > 0 else np.array([0])

        

        # 平均峰值间隔

        if n_peaks > 1:

            mean_peak_interval = np.mean(np.diff(peak_indices))

        else:

            mean_peak_interval = n

        

        return {

            'n_peaks': n_peaks,

            'mean_peak_height': np.mean(peak_heights),

            'std_peak_height': np.std(peak_heights) if n_peaks > 1 else 0,

            'mean_peak_interval': mean_peak_interval

        }

    

    @staticmethod

    def compute_quantile_features(y: np.ndarray) -> Dict[str, float]:

        """计算分位数特征"""

        percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]

        quantile_values = np.percentile(y, percentiles)

        

        result = {}

        for p, q in zip(percentiles, quantile_values):

            result[f'q{p}'] = q

        

        # 分位数跨度

        result['q90_q10_ratio'] = quantile_values[-1] / (quantile_values[0] + 1e-10)

        result['median_mean_diff'] = np.median(y) - np.mean(y)

        

        return result

    

    @staticmethod

    def compute_rolling_features(y: np.ndarray, window: int = 10) -> Dict[str, float]:

        """计算滚动统计特征"""

        n = len(y)

        

        # 滚动均值

        rolling_mean = np.convolve(y, np.ones(window) / window, mode='same')

        

        # 滚动标准差

        rolling_std = np.zeros(n)

        for i in range(n):

            start = max(0, i - window // 2)

            end = min(n, i + window // 2)

            rolling_std[i] = np.std(y[start:end])

        

        return {

            'rolling_mean_std': np.std(rolling_mean),

            'rolling_std_mean': np.mean(rolling_std),

            'rolling_std_max': np.max(rolling_std),

            'rolling_std_min': np.min(rolling_std)

        }





class TSFreshFeatureExtractor:

    """

    完整的TSFresh风格特征提取器

    

    提取特征包括：

    - 基础统计特征

    - 趋势特征

    - 能量特征

    - 熵特征

    - 自相关特征

    - 变化特征

    - 峰值特征

    - 分位数特征

    - 滚动特征

    """

    

    def __init__(self, window_size: Optional[int] = None):

        self.window_size = window_size

    

    def extract(self, y: np.ndarray, prefix: str = '') -> Dict[str, float]:

        """

        提取所有特征

        

        参数:

            y: 时间序列

            prefix: 特征名前缀

        

        返回:

            特征字典

        """

        y = np.array(y)

        n = len(y)

        

        if n < 3:

            return {}

        

        features = {}

        

        # 基础统计

        stats_feats = FeatureExtractor.compute_statistics(y)

        features.update({f'{prefix}stat_{k}': v for k, v in stats_feats.items()})

        

        # 趋势

        if n > 2:

            trend_feats = FeatureExtractor.compute_trend(y)

            features.update({f'{prefix}trend_{k}': v for k, v in trend_feats.items()})

        

        # 能量

        if n > 1:

            energy_feats = FeatureExtractor.compute_energy(y)

            features.update({f'{prefix}energy_{k}': v for k, v in energy_feats.items()})

        

        # 熵

        if n > 10:

            entropy_feats = FeatureExtractor.compute_entropy(y)

            features.update({f'{prefix}entropy_{k}': v for k, v in entropy_feats.items()})

        

        # 自相关

        if n > 5:

            autocorr_feats = FeatureExtractor.compute_autocorrelation(y, min(20, n // 2))

            features.update({f'{prefix}autocorr_{k}': v for k, v in autocorr_feats.items()})

        

        # 变化特征

        if n > 1:

            change_feats = FeatureExtractor.compute_change_features(y)

            features.update({f'{prefix}change_{k}': v for k, v in change_feats.items()})

        

        # 峰值特征

        if n > 2:

            peak_feats = FeatureExtractor.compute_peaks_features(y)

            features.update({f'{prefix}peak_{k}': v for k, v in peak_feats.items()})

        

        # 分位数

        if n > 10:

            quantile_feats = FeatureExtractor.compute_quantile_features(y)

            features.update({f'{prefix}quantile_{k}': v for k, v in quantile_feats.items()})

        

        # 滚动特征

        if n > 20:

            rolling_feats = FeatureExtractor.compute_rolling_features(y, window=min(10, n // 4))

            features.update({f'{prefix}rolling_{k}': v for k, v in rolling_feats.items()})

        

        return features

    

    def extract_batch(self, series_list: List[np.ndarray], 

                     prefix: str = '') -> np.ndarray:

        """

        批量提取特征

        

        参数:

            series_list: 时间序列列表

            prefix: 特征名前缀

        

        返回:

            特征矩阵 (n_samples, n_features)

        """

        features_list = []

        

        for y in series_list:

            feats = self.extract(y, prefix)

            features_list.append(feats)

        

        # 转为DataFrame风格矩阵

        if len(features_list) == 0:

            return np.array([])

        

        # 获取所有特征名

        all_keys = set()

        for feats in features_list:

            all_keys.update(feats.keys())

        

        feature_names = sorted(list(all_keys))

        feature_matrix = np.zeros((len(series_list), len(feature_names)))

        

        for i, feats in enumerate(features_list):

            for j, name in enumerate(feature_names):

                feature_matrix[i, j] = feats.get(name, 0)

        

        return feature_matrix





# 测试代码

if __name__ == "__main__":

    print("=" * 50)

    print("TSFresh特征提取测试")

    print("=" * 50)

    

    np.random.seed(42)

    

    # 生成各类测试数据

    n = 200

    

    # 1. 正弦波

    t = np.linspace(0, 4 * np.pi, n)

    sine_wave = np.sin(t) + np.random.randn(n) * 0.1

    

    # 2. 随机游走

    random_walk = np.cumsum(np.random.randn(n))

    

    # 3. 线性趋势

    linear_trend = 0.1 * np.arange(n) + np.random.randn(n) * 0.5

    

    # 4. 尖峰序列

    spike_data = np.zeros(n)

    spike_data[50] = 5

    spike_data[120] = -4

    spike_data[180] = 3

    

    test_series = [sine_wave, random_walk, linear_trend, spike_data]

    series_names = ['正弦波', '随机游走', '线性趋势', '尖峰序列']

    

    print(f"\n测试4类时间序列，每类 {n} 个数据点")

    

    # 特征提取

    extractor = TSFreshFeatureExtractor()

    

    for name, series in zip(series_names, test_series):

        print(f"\n--- {name} ---")

        features = extractor.extract(series)

        

        print(f"提取特征数量: {len(features)}")

        print(f"部分特征值:")

        for i, (k, v) in enumerate(list(features.items())[:5]):

            print(f"  {k}: {v:.4f}")

    

    # 批量提取

    print("\n--- 批量特征提取 ---")

    feature_matrix = extractor.extract_batch(test_series)

    print(f"特征矩阵形状: {feature_matrix.shape}")

    

    # 数据标准化

    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()

    features_scaled = scaler.fit_transform(feature_matrix)

    

    print(f"标准化后特征矩阵形状: {features_scaled.shape}")

    print(f"特征均值（应接近0）: {np.mean(features_scaled, axis=0)[:3]}")

    print(f"特征标准差（应接近1）: {np.std(features_scaled, axis=0)[:3]}")

    

    print("\n" + "=" * 50)

    print("测试完成")

