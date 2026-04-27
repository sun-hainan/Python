# -*- coding: utf-8 -*-
"""
算法实现：可视化 / stock_visualizer

本文件实现 stock_visualizer 相关的算法功能。
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票价格模拟与移动平均线可视化器
使用 matplotlib 展示模拟股价数据和 MA5/MA10/MA20 移动平均线
支持动画回放和 GIF 生成

使用方法:
    python stock_visualizer.py              # 静态展示
    python stock_visualizer.py --animate    # 动画展示
    python stock_visualizer.py --gif        # 生成 GIF
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import random
from datetime import datetime, timedelta

# ============== 全局配置 ==============
# 随机种子，保证实验可复现
RANDOM_SEED = 42
# 初始股价
INIT_PRICE = 100.0
# 模拟天数
NUM_DAYS = 100
# 移动平均参数
MA_PERIODS = [5, 10, 20]
# 动画帧间隔（毫秒）
FRAME_INTERVAL = 100


def set_seed(seed):
    """设置随机种子，保证结果可复现"""
    random.seed(seed)
    np.random.seed(seed)


def simulate_stock_prices(num_days, init_price, volatility=0.02, drift=0.001):
    """
    使用几何布朗运动模拟股票价格
    
    参数:
        num_days: 模拟天数
        init_price: 初始价格
        volatility: 波动率（每天的价格变动标准差比例）
        drift: 漂移率（每天的平均收益率）
    
    返回:
        prices: 价格列表
        dates: 日期列表
    """
    set_seed(RANDOM_SEED)
    prices = [init_price]
    dates = [datetime.now() - timedelta(days=num_days - i) for i in range(num_days)]
    
    for _ in range(num_days - 1):
        # 几何布朗运动公式: P(t+1) = P(t) * exp((drift - 0.5*volatility^2) + volatility * Z)
        # 其中 Z 是标准正态随机变量
        daily_return = drift + volatility * np.random.randn()
        new_price = prices[-1] * np.exp(daily_return)
        prices.append(new_price)
    
    return prices, dates


def calculate_moving_average(prices, period):
    """
    计算移动平均线
    
    参数:
        prices: 价格列表
        period: 移动平均周期
    
    返回:
        ma_values: 移动平均值列表（前面部分为 NaN）
    """
    ma_values = []
    for i in range(len(prices)):
        if i < period - 1:
            ma_values.append(np.nan)  # 不足周期时填充 NaN
        else:
            # 计算最近 period 天的平均值
            ma_values.append(np.mean(prices[i - period + 1:i + 1]))
    return np.array(ma_values)


class StockVisualizer:
    """股票价格可视化器类"""
    
    def __init__(self, prices, dates):
        self.prices = prices
        self.dates = dates
        self.history = []  # 记录每一步状态，用于回放
        self._build_history()
    
    def _build_history(self):
        """构建历史记录，用于动画回放"""
        # 计算每天的移动平均线
        ma_dict = {}
        for period in MA_PERIODS:
            ma_dict[f'ma_{period}'] = calculate_moving_average(self.prices, period)
        
        # 逐步记录每个时间点的状态
        for i in range(len(self.prices)):
            state = {
                'day': i,
                'price': self.prices[i],
                'ma_values': {k: v[i] for k, v in ma_dict.items()},
                'prices_snapshot': self.prices[:i+1],  # 到当前天为止的价格序列
            }
            # 为每个 MA 添加当天的值（如果不足周期则为 None）
            for period in MA_PERIODS:
                if i < period - 1:
                    state[f'ma_{period}_snapshot'] = [np.nan] * (i + 1)
                else:
                    state[f'ma_{period}_snapshot'] = [np.nan if j < period - 1 else ma_dict[f'ma_{period}'][j] 
                                                       for j in range(i + 1)]
            self.history.append(state)
    
    def plot_static(self, save_path=None):
        """
        绘制静态图表
        
        参数:
            save_path: 可选，图片保存路径
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 绘制价格线
        ax.plot(range(len(self.prices)), self.prices, 
                label='股价', color='#2c3e50', linewidth=1.5, alpha=0.8)
        
        # 绘制移动平均线
        colors = {'ma_5': '#e74c3c', 'ma_10': '#3498db', 'ma_20': '#2ecc71'}
        for period in MA_PERIODS:
            ma_values = calculate_moving_average(self.prices, period)
            ax.plot(range(len(self.prices)), ma_values, 
                    label=f'MA{period}', color=colors[f'ma_{period}'], 
                    linewidth=1.2, linestyle='--')
        
        # 设置图表样式
        ax.set_xlabel('天数', fontsize=12)
        ax.set_ylabel('价格 (元)', fontsize=12)
        ax.set_title('股票价格与移动平均线', fontsize=16, fontweight='bold')
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 添加注释
        ax.annotate(f'最终价格: {self.prices[-1]:.2f}', 
                    xy=(len(self.prices)-1, self.prices[-1]),
                    xytext=(len(self.prices)-20, self.prices[-1]+5),
                    arrowprops=dict(arrowstyle='->', color='gray'),
                    fontsize=10)
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图片已保存到: {save_path}")
        plt.show()
    
    def plot_animate(self, save_gif=False, gif_path='stock_animation.gif'):
        """
        绘制动画
        
        参数:
            save_gif: 是否保存为 GIF
            gif_path: GIF 保存路径
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # 初始化线条
        price_line, = ax.plot([], [], label='股价', color='#2c3e50', linewidth=1.5)
        ma_lines = {}
        for period in MA_PERIODS:
            color = {'ma_5': '#e74c3c', 'ma_10': '#3498db', 'ma_20': '#2ecc71'}[f'ma_{period}']
            (line,) = ax.plot([], [], label=f'MA{period}', color=color, 
                              linewidth=1.2, linestyle='--')
            ma_lines[f'ma_{period}'] = line
        
        # 设置轴范围
        ax.set_xlim(0, len(self.prices))
        price_min, price_max = min(self.prices), max(self.prices)
        ax.set_ylim(price_min * 0.9, price_max * 1.1)
        
        ax.set_xlabel('天数', fontsize=12)
        ax.set_ylabel('价格 (元)', fontsize=12)
        ax.set_title('股票价格与移动平均线 - 动画回放', fontsize=16, fontweight='bold')
        ax.legend(loc='upper left', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        # 信息文本
        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes, 
                           verticalalignment='top', fontsize=11,
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        def init():
            """初始化函数"""
            price_line.set_data([], [])
            for period in MA_PERIODS:
                ma_lines[f'ma_{period}'].set_data([], [])
            info_text.set_text('')
            return [price_line] + list(ma_lines.values()) + [info_text]
        
        def update(frame):
            """更新每一帧"""
            state = self.history[frame]
            x = range(state['day'] + 1)
            
            # 更新价格线
            price_line.set_data(x, state['prices_snapshot'])
            
            # 更新各移动平均线
            for period in MA_PERIODS:
                ma_key = f'ma_{period}_snapshot'
                ma_data = state[ma_key]
                ma_lines[f'ma_{period}'].set_data(x, ma_data)
            
            # 更新信息文本
            info_text.set_text(
                f"第 {state['day']} 天\n"
                f"价格: {state['price']:.2f}\n"
                f"MA5: {state['ma_values']['ma_5']:.2f if not np.isnan(state['ma_values']['ma_5']) else 'N/A'}\n"
                f"MA10: {state['ma_values']['ma_10']:.2f if not np.isnan(state['ma_values']['ma_10']) else 'N/A'}\n"
                f"MA20: {state['ma_values']['ma_20']:.2f if not np.isnan(state['ma_values']['ma_20']) else 'N/A'}"
            )
            
            return [price_line] + list(ma_lines.values()) + [info_text]
        
        ani = animation.FuncAnimation(fig, update, frames=len(self.history),
                                      init_func=init, blit=True, interval=FRAME_INTERVAL)
        
        if save_gif:
            print("正在生成 GIF，请稍候...")
            ani.save(gif_path, writer='pillow', fps=10)
            print(f"GIF 已保存到: {gif_path}")
        
        plt.show()
        return ani


def main():
    """主函数：演示股票价格可视化"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票价格与移动平均线可视化')
    parser.add_argument('--animate', action='store_true', help='显示动画')
    parser.add_argument('--gif', action='store_true', help='生成 GIF')
    parser.add_argument('--days', type=int, default=NUM_DAYS, help='模拟天数')
    args = parser.parse_args()
    
    print("=" * 50)
    print("股票价格模拟与移动平均线可视化")
    print("=" * 50)
    
    # 生成模拟数据
    prices, dates = simulate_stock_prices(args.days, INIT_PRICE)
    
    print(f"\n数据统计:")
    print(f"  模拟天数: {args.days}")
    print(f"  初始价格: {INIT_PRICE:.2f}")
    print(f"  最终价格: {prices[-1]:.2f}")
    print(f"  最高价格: {max(prices):.2f}")
    print(f"  最低价格: {min(prices):.2f}")
    print(f"  价格波动: {(max(prices) - min(prices)) / min(prices) * 100:.1f}%")
    
    # 创建可视化器
    visualizer = StockVisualizer(prices, dates)
    
    if args.gif:
        visualizer.plot_animate(save_gif=True)
    elif args.animate:
        visualizer.plot_animate()
    else:
        visualizer.plot_static()
    
    print("\n可视化完成!")


if __name__ == '__main__':
    main()
