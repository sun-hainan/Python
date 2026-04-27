# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / pairs_trading



本文件实现 pairs_trading 相关的算法功能。

"""



import numpy as np

from scipy import stats

from scipy.optimize import minimize





def find_cointegrated_pairs(prices_df):

    """

    寻找协整的价格对

    使用 Engle-Granger 两步法



    Parameters

    ----------

    prices_df : pd.DataFrame

        价格数据，列为不同资产，行为时间



    Returns

    -------

    list of tuples

        协整对的列表 (asset1, asset2, coint_stat, p_value)

    """

    n_assets = prices_df.shape[1]

    pairs = []

    asset_names = prices_df.columns.tolist()



    for i in range(n_assets):

        for j in range(i+1, n_assets):

            price1 = prices_df.iloc[:, i].values

            price2 = prices_df.iloc[:, j].values



            # Engle-Granger 协整检验

            try:

                # OLS: price1 = α + β * price2 + ε

                X = np.column_stack([np.ones(len(price2)), price2])

                beta = np.linalg.lstsq(X, price1, rcond=None)[0]

                residuals = price1 - (beta[0] + beta[1] * price2)



                # 检验残差的平稳性（ADF 检验）

                adf_result = adf_test(residuals)

                if adf_result['p_value'] < 0.05:

                    pairs.append({

                        'asset1': asset_names[i],

                        'asset2': asset_names[j],

                        'beta': beta[1],

                        'alpha': beta[0],

                        'adf_stat': adf_result['statistic'],

                        'p_value': adf_result['p_value']

                    })

            except:

                pass



    return sorted(pairs, key=lambda x: x['p_value'])





def adf_test(series, max_lag=None):

    """

    Augmented Dickey-Fuller 检验

    H0: 序列存在单位根（非平稳）

    """

    series = np.array(series)

    n = len(series)



    if max_lag is None:

        max_lag = int(np.ceil(12.0 * (n/100.0) ** (1/4)))



    # 差分序列

    y = series[1:]

    x = series[:-1]



    # 加入滞后差分项

    for k in range(1, max_lag + 1):

        y_k = series[k+1:]

        x_k = np.column_stack([series[k:-1]])

        for j in range(1, k):

            x_k = np.column_stack([x_k, series[k-j:-j-1]])



        if len(y_k) > len(x_k):

            break



    if k == max_lag and len(y_k) <= len(x_k):

        return {'statistic': 0, 'p_value': 1.0}



    # OLS

    try:

        X_with_lags = np.column_stack([np.ones(len(x_k)), x_k])

        coef = np.linalg.lstsq(X_with_lags, y_k, rcond=None)[0]

        residuals = y_k - X_with_lags @ coef

        # 简化：使用残差标准差计算

        adf_stat = coef[0] / np.std(residuals) if np.std(residuals) > 0 else 0



        # 临界值（简化）

        p_value = 0.5 if abs(adf_stat) < 2.5 else 0.01 if abs(adf_stat) > 3 else 0.05



        return {'statistic': adf_stat, 'p_value': p_value}

    except:

        return {'statistic': 0, 'p_value': 1.0}





def pairs_trading_strategy(price1, price2, lookback=60, entry_threshold=2.0,

                           exit_threshold=0.5, hedge_ratio=None):

    """

    配对交易策略



    Parameters

    ----------

    lookback : int

        计算均值和标准差的窗口

    entry_threshold : float

        入场阈值（标准差倍数）

    exit_threshold : float

        出场阈值



    Returns

    -------

    dict

        交易信号、持仓、盈亏

    """

    n = len(price1)



    # 计算对冲比率（OLS）

    if hedge_ratio is None:

        hedge_ratio = np.zeros(n)

        for i in range(lookback, n):

            x = price2[i-lookback:i]

            y = price1[i-lookback:i]

            X = np.column_stack([np.ones(lookback), x])

            beta = np.linalg.lstsq(X, y, rcond=None)[0]

            hedge_ratio[i] = beta[1]



    # 计算价差（spread）

    # spread = price1 - hedge_ratio * price2

    spread = price1 - hedge_ratio * price2



    # 计算 z-score

    ma = np.zeros(n)

    std = np.zeros(n)

    z_score = np.zeros(n)



    for i in range(lookback, n):

        window_spread = spread[i-lookback:i]

        ma[i] = np.mean(window_spread)

        std[i] = np.std(window_spread)

        if std[i] > 0:

            z_score[i] = (spread[i] - ma[i]) / std[i]

        else:

            z_score[i] = 0



    # 交易

    position = 0  # 0: 空仓, 1: 多头 spread, -1: 空头 spread

    # 多头 spread = 做多 price1 + 做空 price2 * hedge_ratio

    # 空头 spread = 做空 price1 + 做多 price2 * hedge_ratio



    signals = np.zeros(n)

    pnl = np.zeros(n)

    position_value = np.zeros(n)



    entry_spread = 0



    for i in range(lookback, n):

        z = z_score[i]



        if position == 0:

            if z > entry_threshold:

                # spread 过高，做空 spread

                # 即：做空 price1，做多 price2

                position = -1

                entry_spread = spread[i]

                signals[i] = -1

            elif z < -entry_threshold:

                # spread 过低，做多 spread

                # 即：做多 price1，做空 price2

                position = 1

                entry_spread = spread[i]

                signals[i] = 1

        elif position == 1:

            # 持有多头 spread

            if z > -exit_threshold:

                # 平仓

                pnl[i] = spread[i] - entry_spread

                position = 0

                signals[i] = 0

        else:

            # 持有空头 spread

            if z < exit_threshold:

                # 平仓

                pnl[i] = entry_spread - spread[i]

                position = 0

                signals[i] = 0



        position_value[i] = position



    return {

        'signals': signals,

        'spread': spread,

        'z_score': z_score,

        'hedge_ratio': hedge_ratio,

        'position': position_value,

        'pnl': pnl,

        'cumulative_pnl': np.cumsum(pnl)

    }





def hurst_test(series, max_lag=None):

    """

    Hurst 指数检验

    衡量时间序列的持续性/均值回归特性

    H < 0.5: 均值回归

    H = 0.5: 随机游走

    H > 0.5: 趋势持续

    """

    series = np.array(series)

    n = len(series)



    if max_lag is None:

        max_lag = min(100, n // 2)



    lags = range(2, max_lag)

    rs_values = []



    for lag in lags:

        rs_list = []

        for start in range(0, n - lag, lag):

            subseries = series[start:start+lag]

            mean_sub = np.mean(subseries)

            deviation = subseries - mean_sub

            cumsum_dev = np.cumsum(deviation)

            R = np.max(cumsum_dev) - np.min(cumsum_dev)

            S = np.std(subseries, ddof=1)

            if S > 0:

                rs_list.append(R / S)

        if rs_list:

            rs_values.append(np.mean(rs_list))



    if not rs_values:

        return {'hurst_exponent': 0.5}



    # H = slope of log(R/S) vs log(lag)

    log_lags = np.log(list(lags[:len(rs_values)]))

    log_rs = np.log(rs_values)

    slope, _, _, _, _ = stats.linregress(log_lags, log_rs)



    return {'hurst_exponent': slope}





def half_life_of_mean_reversion(series):

    """

    估计均值回复的半衰期

    使用 Ornstein-Uhlenbeck 过程拟合

    dX = -λX dt + dW

    半衰期 = ln(2) / λ

    """

    series = np.array(series)

    delta_x = np.diff(series)

    x_lag = series[:-1]



    # OLS: ΔX = -λX_{t-1} + ε

    X = x_lag.reshape(-1, 1)

    coef = np.linalg.lstsq(X, delta_x, rcond=None)[0]

    lambda_coef = -coef[0]



    if lambda_coef <= 0:

        return {'half_life': np.inf, 'lambda': lambda_coef}



    half_life = np.log(2) / lambda_coef



    return {'half_life': half_life, 'lambda': lambda_coef}





def kalman_filter_pairs(price1, price2, delta=1e-4):

    """

    使用卡尔曼滤波动态估计对冲比率

    更适合在线交易

    """

    n = len(price1)



    # 状态：hedge_ratio

    # 观测：price1 - alpha = hedge_ratio * price2 + noise



    # 初始化

    theta = np.zeros(n)  # 对冲比率

    P = np.zeros(n)  # 误差协方差

    y = np.zeros(n)  # 观测残差



    # 先验

    theta[0] = 1.0  # 初始对冲比率

    P[0] = 1.0



    R = 0.001  # 观测噪声

    Q = delta  # 状态噪声



    for t in range(1, n):

        # 预测步骤

        theta_pred = theta[t-1]

        P_pred = P[t-1] + Q



        # 观测

        y[t] = price1[t] - theta_pred * price2[t]



        # 更新步骤

        K = P_pred * price2[t] / (price2[t]**2 * P_pred + R)  # 卡尔曼增益

        theta[t] = theta_pred + K * y[t]

        P[t] = (1 - K * price2[t]) * P_pred



    return {

        'hedge_ratio': theta,

        'spread': y,

        'prediction_error': y

    }





if __name__ == "__main__":

    print("=" * 60)

    print("配对交易策略")

    print("=" * 60)



    # 模拟配对价格数据

    np.random.seed(42)

    n = 500

    t = np.arange(n)



    # 生成两个协整资产

    # Y 是基础资产

    Y = 100 + 0.01 * t + np.cumsum(np.random.normal(0, 1, n))



    # X 与 Y 协整：X = alpha + beta * Y + noise

    alpha = 10

    beta = 0.8

    noise = np.random.normal(0, 0.5, n)

    X = alpha + beta * Y + noise



    # 添加一些非平稳成分（测试用）

    X[200:300] += 5  # 价差暂时偏离



    print("\n--- 数据统计 ---")

    print(f"X 均值: {np.mean(X):.2f}, 标准差: {np.std(X):.2f}")

    print(f"Y 均值: {np.mean(Y):.2f}, 标准差: {np.std(Y):.2f}")

    print(f"相关系数: {np.corrcoef(X, Y)[0,1]:.4f}")



    # Hurst 指数

    spread_static = X - np.mean(X - np.mean(X)) - 0.8 * (Y - np.mean(Y))

    # 简化：直接用 X - 0.8*Y

    spread_test = X - 0.8 * Y

    hurst = hurst_test(spread_test)

    print(f"\nHurst 指数: {hurst['hurst_exponent']:.4f}")

    print(f"  (< 0.5 表示均值回归)")



    # 半衰期

    hl = half_life_of_mean_reversion(spread_test[-100:])

    print(f"均值回复半衰期: {hl['half_life']:.2f} 期")



    # 卡尔曼滤波对冲比率

    print("\n--- 卡尔曼滤波对冲比率 ---")

    kf_result = kalman_filter_pairs(X, Y)

    print(f"初始对冲比率: {kf_result['hedge_ratio'][0]:.4f}")

    print(f"最终对冲比率: {kf_result['hedge_ratio'][-1]:.4f}")

    print(f"对冲比率范围: [{np.min(kf_result['hedge_ratio']):.4f}, {np.max(kf_result['hedge_ratio']):.4f}]")



    # 配对交易策略

    print("\n--- 配对交易结果 ---")

    result = pairs_trading_strategy(X, Y, lookback=60, entry_threshold=2.0, exit_threshold=0.5)



    # 计算统计

    total_pnl = np.sum(result['pnl'])

    n_trades = np.sum(result['signals'] != 0)

    n_complete_trades = np.sum((result['signals'][:-1] != 0) & (result['signals'][1:] == 0))



    print(f"总盈亏: {total_pnl:.4f}")

    print(f"信号切换次数: {n_trades}")



    # 收益分布

    pnl_nonzero = result['pnl'][result['pnl'] != 0]

    if len(pnl_nonzero) > 0:

        print(f"平均每笔交易盈亏: {np.mean(pnl_nonzero):.4f}")

        print(f"盈利交易占比: {np.sum(pnl_nonzero > 0) / len(pnl_nonzero):.2%}")

