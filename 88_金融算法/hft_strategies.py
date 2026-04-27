# -*- coding: utf-8 -*-

"""

算法实现：金融算法 / hft_strategies



本文件实现 hft_strategies 相关的算法功能。

"""



import numpy as np

from collections import deque





def mean_reversion_prices(prices, window=20, entry_threshold=2.0, exit_threshold=0.5):

    """

    均值回归策略

    核心思想：当价格偏离移动平均超过阈值时建仓，回归时平仓



    Parameters

    ----------

    prices : list/np.ndarray

        价格序列

    window : int

        计算移动平均的窗口

    entry_threshold : float

        入场阈值（标准差倍数）

    exit_threshold : float

        出场阈值（标准差倍数）



    Returns

    -------

    dict

        交易信号和盈亏

    """

    prices = np.array(prices)

    n = len(prices)



    # 计算滚动均值和标准差

    ma = np.zeros(n)

    std = np.zeros(n)

    z_score = np.zeros(n)



    for i in range(window, n):

        window_prices = prices[i-window:i]

        ma[i] = np.mean(window_prices)

        std[i] = np.std(window_prices)

        if std[i] > 0:

            z_score[i] = (prices[i] - ma[i]) / std[i]

        else:

            z_score[i] = 0



    # 生成交易信号

    position = 0  # 0: 空仓, 1: 多头, -1: 空头

    signals = np.zeros(n)

    trades = []



    for i in range(window, n):

        if position == 0:

            # 无持仓

            if z_score[i] > entry_threshold:

                # 价格过高，做空

                position = -1

                signals[i] = -1

                trades.append({'idx': i, 'action': 'SHORT', 'price': prices[i], 'z': z_score[i]})

            elif z_score[i] < -entry_threshold:

                # 价格过低，做多

                position = 1

                signals[i] = 1

                trades.append({'idx': i, 'action': 'LONG', 'price': prices[i], 'z': z_score[i]})

        elif position == 1:

            # 多头持仓

            if z_score[i] > -exit_threshold:

                # 价格回归，平多

                position = 0

                signals[i] = 0

                trades.append({'idx': i, 'action': 'SELL', 'price': prices[i], 'z': z_score[i], 'pnl': prices[i] - trades[-1]['price']})

        else:

            # 空头持仓

            if z_score[i] < exit_threshold:

                # 价格回归，平空

                position = 0

                signals[i] = 0

                trades.append({'idx': i, 'action': 'COVER', 'price': prices[i], 'z': z_score[i], 'pnl': trades[-1]['price'] - prices[i]})



    return {

        'signals': signals,

        'z_scores': z_score,

        'ma': ma,

        'trades': trades

    }





def market_maker_simulator(mid_prices, spread=0.01, inventory_limit=100, seed=42):

    """

    简单做市商模拟

    策略：

    - 在买一和卖一同时挂单

    - 根据库存风险调整报价

    - 库存超过限制时减少单边持仓



    Parameters

    ----------

    mid_prices : list/np.ndarray

        中间价序列

    spread : float

        买卖价差（绝对值或比例）

    inventory_limit : int

        最大库存

    """

    np.random.seed(seed)

    prices = np.array(mid_prices)

    n = len(prices)



    # 做市商状态

    inventory = 0  # 正数表示多头，负数表示空头

    cash = 0  # 累计现金

    realized_pnl = 0



    # 订单簿记录

    bids = []  # 买单队列

    asks = []  # 卖单队列



    trade_log = []



    for i in range(n):

        price = prices[i]



        # 生成报价（以中间价为中心）

        bid_price = price - spread / 2

        ask_price = price + spread / 2



        # 库存调整：库存越多，报价越不利

        # 库存为正（多头）时，降低 bid 报价（不愿意买更多）

        # 库存为负（空头）时，提高 ask 报价（不愿意卖更多）

        inventory_penalty = 0.001 * inventory

        bid_price_adjusted = bid_price - inventory_penalty

        ask_price_adjusted = ask_price - inventory_penalty



        # 模拟成交（简化的 Poisson 过程）

        # 买单成交概率

        prob_bid = 0.3 * (1 - abs(inventory) / inventory_limit)

        # 卖单成交概率

        prob_ask = 0.3 * (1 - abs(inventory) / inventory_limit)



        bid_filled = np.random.random() < prob_bid

        ask_filled = np.random.random() < prob_ask



        # 处理成交

        if bid_filled and inventory < inventory_limit:

            # 买方吃单，做市商卖出（增加空头库存）

            cash -= bid_price_adjusted

            inventory -= 1

            trade_log.append({'idx': i, 'side': 'BID_FILLED', 'price': bid_price_adjusted})



        if ask_filled and inventory > -inventory_limit:

            # 卖方吃单，做市商买入（增加多头库存）

            cash += ask_price_adjusted

            inventory += 1

            trade_log.append({'idx': i, 'side': 'ASK_FILLED', 'price': ask_price_adjusted})



    # 平仓（最后价格）

    final_price = prices[-1]

    if inventory > 0:

        cash += inventory * final_price  # 卖出多头

        unrealized_pnl = inventory * (final_price - np.mean([t['price'] for t in trade_log if t['side'] == 'ASK_FILLED']))

    elif inventory < 0:

        cash += inventory * final_price  # 买入空头平仓

        unrealized_pnl = -inventory * (np.mean([t['price'] for t in trade_log if t['side'] == 'BID_FILLED']) - final_price)

    else:

        unrealized_pnl = 0



    total_pnl = cash + unrealized_pnl



    return {

        'cash': cash,

        'inventory': inventory,

        'unrealized_pnl': unrealized_pnl,

        'total_pnl': total_pnl,

        'n_trades': len(trade_log),

        'trade_log': trade_log

    }





class OrderBookSimulator:

    """

    订单簿模拟器

    用于分析订单簿微观结构和价格发现

    """



    def __init__(self, tick_size=0.01, depth=10):

        self.tick_size = tick_size

        self.depth = depth

        self.bids = {}  # 价格 -> 数量

        self.asks = {}  # 价格 -> 数量



    def add_order(self, side, price, quantity):

        """添加订单"""

        if side == 'BID':

            self.bids[price] = self.bids.get(price, 0) + quantity

        else:

            self.asks[price] = self.asks.get(price, 0) + quantity



    def remove_order(self, side, price, quantity):

        """移除订单（部分成交或取消）"""

        if side == 'BID':

            if price in self.bids:

                self.bids[price] = max(0, self.bids[price] - quantity)

                if self.bids[price] == 0:

                    del self.bids[price]

        else:

            if price in self.asks:

                self.asks[price] = max(0, self.asks[price] - quantity)

                if self.asks[price] == 0:

                    del self.asks[price]



    def best_bid(self):

        """最佳买价"""

        if not self.bids:

            return None

        return max(self.bids.keys())



    def best_ask(self):

        """最佳卖价"""

        if not self.asks:

            return None

        return min(self.asks.keys())



    def spread(self):

        """买卖价差"""

        bid = self.best_bid()

        ask = self.best_ask()

        if bid is None or ask is None:

            return None

        return ask - bid



    def mid_price(self):

        """中间价"""

        bid = self.best_bid()

        ask = self.best_ask()

        if bid is None or ask is None:

            return None

        return (bid + ask) / 2



    def depth_imbalance(self, levels=5):

        """订单簿深度失衡

        衡量买方压力 vs 卖方压力

        > 0 表示买方压力，< 0 表示卖方压力

        """

        bid_vol = 0

        ask_vol = 0



        sorted_bids = sorted(self.bids.keys(), reverse=True)[:levels]

        sorted_asks = sorted(self.asks.keys())[:levels]



        for p in sorted_bids:

            bid_vol += self.bids[p]

        for p in sorted_asks:

            ask_vol += self.asks[p]



        if bid_vol + ask_vol == 0:

            return 0

        return (bid_vol - ask_vol) / (bid_vol + ask_vol)



    def vwap(self, side, levels=5):

        """成交量加权平均价"""

        if side == 'BID':

            sorted_prices = sorted(self.bids.keys(), reverse=True)[:levels]

            total_vol = sum(self.bids[p] for p in sorted_prices)

            if total_vol == 0:

                return None

            return sum(p * self.bids[p] for p in sorted_prices) / total_vol

        else:

            sorted_prices = sorted(self.asks.keys())[:levels]

            total_vol = sum(self.asks[p] for p in sorted_prices)

            if total_vol == 0:

                return None

            return sum(p * self.asks[p] for p in sorted_prices) / total_vol





def trend_following(prices, short_window=5, long_window=20):

    """

    趋势跟随策略

    短期均线穿越长期均线时交易

    """

    prices = np.array(prices)

    n = len(prices)



    ma_short = np.zeros(n)

    ma_long = np.zeros(n)



    for i in range(n):

        if i >= short_window:

            ma_short[i] = np.mean(prices[i-short_window:i])

        if i >= long_window:

            ma_long[i] = np.mean(prices[i-long_window:i])



    # 信号

    signals = np.zeros(n)

    position = 0



    for i in range(long_window, n):

        if position == 0:

            if ma_short[i] > ma_long[i] and ma_short[i-1] <= ma_long[i-1]:

                position = 1

                signals[i] = 1

            elif ma_short[i] < ma_long[i] and ma_short[i-1] >= ma_long[i-1]:

                position = -1

                signals[i] = -1

        elif position == 1:

            if ma_short[i] < ma_long[i] and ma_short[i-1] >= ma_long[i-1]:

                position = 0

                signals[i] = 0

        else:

            if ma_short[i] > ma_long[i] and ma_short[i-1] <= ma_long[i-1]:

                position = 0

                signals[i] = 0



    return {

        'signals': signals,

        'ma_short': ma_short,

        'ma_long': ma_long

    }





def momentum_score(prices, lookback=20):

    """

    动量因子：过去 lookback 期的收益

    常用于 Alpha 因子构建

    """

    prices = np.array(prices)

    momentum = np.zeros(len(prices))

    momentum[lookback:] = (prices[lookback:] - prices[:-lookback]) / prices[:-lookback]

    return momentum





if __name__ == "__main__":

    print("=" * 60)

    print("高频交易算法示例")

    print("=" * 60)



    # 生成模拟价格数据（带均值回归和趋势）

    np.random.seed(42)

    n = 1000

    prices = np.zeros(n)

    prices[0] = 100



    # 模拟价格路径

    for i in range(1, n):

        # 随机游走 + 均值回复

        shock = np.random.normal(0, 0.5)

        mean_reversion = 0.1 * (100 - prices[i-1])  # 向 100 均值回归

        prices[i] = prices[i-1] + mean_reversion + shock



    # 均值回归策略

    print("\n--- 均值回归策略 ---")

    mr_result = mean_reversion_prices(prices, window=30, entry_threshold=1.5, exit_threshold=0.5)

    n_trades = len([t for t in mr_result['trades'] if 'pnl' in t])

    if n_trades > 0:

        pnls = [t['pnl'] for t in mr_result['trades'] if 'pnl' in t]

        print(f"交易次数: {n_trades}")

        print(f"盈利交易: {sum(1 for p in pnls if p > 0)}")

        print(f"总盈亏: {sum(pnls):.4f}")

        print(f"胜率: {sum(1 for p in pnls if p > 0)/len(pnls):.2%}")



    # 做市商策略

    print("\n--- 做市商策略 ---")

    mm_result = market_maker_simulator(prices, spread=0.5, inventory_limit=50)

    print(f"现金损益: {mm_result['cash']:.4f}")

    print(f"库存: {mm_result['inventory']}")

    print(f"未实现损益: {mm_result['unrealized_pnl']:.4f}")

    print(f"总损益: {mm_result['total_pnl']:.4f}")

    print(f"交易次数: {mm_result['n_trades']}")



    # 订单簿模拟

    print("\n--- 订单簿分析 ---")

    ob = OrderBookSimulator(tick_size=0.1)



    # 添加一些订单

    for p in np.arange(99.5, 100.5, 0.1):

        ob.add_order('BID', p, np.random.randint(1, 10))

        ob.add_order('ASK', p + 0.1, np.random.randint(1, 10))



    print(f"最佳买价: {ob.best_bid():.2f}")

    print(f"最佳卖价: {ob.best_ask():.2f}")

    print(f"买卖价差: {ob.spread():.2f}")

    print(f"中间价: {ob.mid_price():.2f}")

    print(f"深度失衡 (5档): {ob.depth_imbalance(5):.4f}")



    # 趋势跟随

    print("\n--- 趋势跟随策略 ---")

    tf_result = trend_following(prices, short_window=10, long_window=50)

    long_signals = np.sum(tf_result['signals'] == 1)

    short_signals = np.sum(tf_result['signals'] == -1)

    print(f"做多信号次数: {long_signals}")

    print(f"做空信号次数: {short_signals}")

