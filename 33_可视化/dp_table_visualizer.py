# -*- coding: utf-8 -*-

"""

算法实现：可视化 / dp_table_visualizer



本文件实现 dp_table_visualizer 相关的算法功能。

"""



#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

动态规划可视化扩展器

使用 matplotlib 动画展示 0-1 背包问题和最长公共子序列(LCS)的填表过程

支持路径回溯高亮



使用方法:

    python dp_table_visualizer.py              # 静态展示

    python dp_table_visualizer.py --animate    # 动画展示

    python dp_table_visualizer.py --gif        # 生成 GIF

"""



import matplotlib.pyplot as plt

import matplotlib.animation as animation

import numpy as np

import copy



# ============== 全局配置 ==============

# 动画帧间隔（毫秒）

FRAME_INTERVAL = 500

# 颜色配置

COLOR_NORMAL = '#ecf0f1'    # 正常单元格

COLOR_FILLING = '#f39c12'    # 正在填充

COLOR_CURRENT = '#e74c3c'    # 当前单元格

COLOR_PATH = '#2ecc71'       # 回溯路径

COLOR_SELECTED = '#9b59b6'   # 选中的物品





# ============== 0-1 背包问题可视化 ==============



class KnapsackVisualizer:

    """0-1 背包问题可视化器"""

    

    def __init__(self, weights, values, capacity):

        self.weights = weights       # 物品重量列表

        self.values = values        # 物品价值列表

        self.capacity = capacity    # 背包容量

        self.n = len(weights)       # 物品数量

        self.dp_table = None        # DP 表

        self.history = []           # 填表历史

        self.backtrack_path = []     # 回溯路径

        self._build_dp_table()

    

    def _build_dp_table(self):

        """构建 DP 表并记录填表过程"""

        # 初始化 DP 表 (n+1) x (capacity+1)

        # dp[i][w] = 前 i 个物品在容量 w 下的最大价值

        self.dp_table = np.zeros((self.n + 1, self.capacity + 1), dtype=int)

        

        # 记录初始状态

        self.history.append({

            'step': 0,

            'action': 'init',

            'table': copy.deepcopy(self.dp_table),

            'current': None,

            'message': '初始化 DP 表，全部为 0'

        })

        

        # 填表过程

        step = 0

        for i in range(1, self.n + 1):

            for w in range(self.capacity + 1):

                step += 1

                

                # 不选择第 i 个物品

                not_select = self.dp_table[i-1][w]

                

                # 选择第 i 个物品（如果能装下）

                select = 0

                if w >= self.weights[i-1]:

                    select = self.dp_table[i-1][w - self.weights[i-1]] + self.values[i-1]

                

                # 更新 DP 表

                self.dp_table[i][w] = max(not_select, select)

                

                # 记录填表历史

                self.history.append({

                    'step': step,

                    'action': 'fill',

                    'i': i,

                    'w': w,

                    'not_select': not_select,

                    'select': select if w >= self.weights[i-1] else 0,

                    'chosen': not_select >= select,

                    'table': copy.deepcopy(self.dp_table),

                    'current': (i, w),

                    'message': f'物品 {i} (重量:{self.weights[i-1]}, 价值:{self.values[i-1]}), 容量 {w}'

                })

        

        # 计算最大价值

        self.max_value = self.dp_table[self.n][self.capacity]

        

        # 回溯找出选择了哪些物品

        self._backtrack()

    

    def _backtrack(self):

        """回溯找出选择的物品"""

        self.backtrack_path = []

        i, w = self.n, self.capacity

        

        while i > 0 and w > 0:

            if self.dp_table[i][w] != self.dp_table[i-1][w]:

                self.backtrack_path.append((i, w, True))  # 选择了物品 i

                w -= self.weights[i-1]

            else:

                self.backtrack_path.append((i, w, False))  # 未选择物品 i

            i -= 1

        

        self.backtrack_path.reverse()

    

    def plot_static(self, save_path=None):

        """绘制静态 DP 表"""

        fig, axes = plt.subplots(1, 2, figsize=(16, 8))

        

        # 左图: DP 表

        ax1 = axes[0]

        self._draw_table(ax1, self.dp_table, title='0-1 背包 DP 表')

        

        # 添加行列标签

        ax1.set_xlabel('背包容量 (w)', fontsize=12)

        ax1.set_ylabel('物品数量 (i)', fontsize=12)

        

        # 右图: 最终选择方案

        ax2 = axes[1]

        self._draw_solution(ax2)

        

        plt.tight_layout()

        if save_path:

            plt.savefig(save_path, dpi=150, bbox_inches='tight')

            print(f"图片已保存到: {save_path}")

        plt.show()

    

    def _draw_table(self, ax, table, title=''):

        """绘制 DP 表"""

        rows, cols = table.shape

        

        # 设置背景色

        for i in range(rows):

            for j in range(cols):

                color = COLOR_NORMAL

                rect = plt.Rectangle((j-0.5, rows-i-1.5), 1, 1, 

                                     facecolor=color, edgecolor='black', linewidth=0.5)

                ax.add_patch(rect)

                ax.text(j, rows-i-1, str(int(table[i][j])), 

                       ha='center', va='center', fontsize=9)

        

        # 行列标签

        ax.set_xticks(range(cols))

        ax.set_xticklabels(range(cols))

        ax.set_yticks(range(rows))

        ax.set_yticklabels(range(rows-1, -1, -1))

        

        ax.set_xlim(-0.5, cols-0.5)

        ax.set_ylim(-0.5, rows-0.5)

        ax.set_aspect('equal')

        ax.set_title(title, fontsize=14, fontweight='bold')

    

    def _draw_solution(self, ax):

        """绘制选择方案图"""

        ax.clear()

        

        selected = []

        w = self.capacity

        for i in range(self.n, 0, -1):

            if w >= self.weights[i-1] and self.dp_table[i][w] != self.dp_table[i-1][w]:

                selected.append(i-1)

                w -= self.weights[i-1]

        selected.reverse()

        

        # 绘制物品

        x_positions = np.linspace(0, 10, self.n + 1)

        

        for idx, (w, v) in enumerate(zip(self.weights, self.values)):

            color = COLOR_SELECTED if idx in selected else '#bdc3c7'

            rect = plt.Rectangle((x_positions[idx]-0.3, 0), 0.6, 2, 

                                 facecolor=color, edgecolor='black', linewidth=1)

            ax.add_patch(rect)

            ax.text(x_positions[idx], 1, f'{w}\n{v}', ha='center', va='center', 

                   fontsize=10, fontweight='bold')

        

        ax.set_xlim(-0.5, 10.5)

        ax.set_ylim(-0.5, 2.5)

        ax.set_aspect('equal')

        ax.axis('off')

        ax.set_title(f'选择方案 (总价值: {self.max_value})', fontsize=14, fontweight='bold')

    

    def plot_animate(self, save_gif=False, gif_path='knapsack_animation.gif'):

        """绘制填表动画"""

        fig, ax = plt.subplots(figsize=(12, 10))

        

        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,

                           verticalalignment='top', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        

        def init():

            return []

        

        def update(frame):

            ax.clear()

            state = self.history[frame]

            

            # 更新信息文本

            info_text.set_text(

                f"步骤: {state['step']}\n"

                f"{state['message']}\n"

                f"最大价值: {self.max_value}"

            )

            

            # 绘制当前 DP 表

            self._draw_table_animate(ax, state['table'], state.get('current'))

            

            return []

        

        def _draw_table_animate(self, ax, table, current):

            """绘制动画帧中的 DP 表"""

            rows, cols = table.shape

            

            for i in range(rows):

                for j in range(cols):

                    # 根据状态设置颜色

                    if current and i == current[0] and j == current[1]:

                        color = COLOR_CURRENT

                    else:

                        color = COLOR_NORMAL

                    

                    rect = plt.Rectangle((j-0.5, rows-i-1.5), 1, 1,

                                         facecolor=color, edgecolor='black', linewidth=0.5)

                    ax.add_patch(rect)

                    ax.text(j, rows-i-1, str(int(table[i][j])),

                           ha='center', va='center', fontsize=9)

            

            ax.set_xticks(range(cols))

            ax.set_xticklabels(range(cols))

            ax.set_yticks(range(rows))

            ax.set_yticklabels(range(rows-1, -1, -1))

            

            ax.set_xlim(-0.5, cols-0.5)

            ax.set_ylim(-0.5, rows-0.5)

            ax.set_aspect('equal')

            ax.set_xlabel('背包容量 (w)', fontsize=12)

            ax.set_ylabel('物品数量 (i)', fontsize=12)

            ax.set_title('0-1 背包 DP 表填充过程', fontsize=14, fontweight='bold')

        

        ani = animation.FuncAnimation(fig, update, frames=len(self.history),

                                     init_func=init, blit=False, interval=FRAME_INTERVAL)

        

        if save_gif:

            print("正在生成 GIF，请稍候...")

            ani.save(gif_path, writer='pillow', fps=5)

            print(f"GIF 已保存到: {gif_path}")

        

        plt.show()

        return ani





# ============== 最长公共子序列可视化 ==============



class LCSVisualizer:

    """最长公共子序列可视化器"""

    

    def __init__(self, str1, str2):

        self.str1 = str1       # 第一个字符串

        self.str2 = str2       # 第二个字符串

        self.m = len(str1)     # 第一个字符串长度

        self.n = len(str2)     # 第二个字符串长度

        self.dp_table = None   # DP 表

        self.lcs_length = 0    # LCS 长度

        self.history = []      # 填表历史

        self.lcs_result = ''   # LCS 结果

        self.backtrack_path = []  # 回溯路径

        self._build_dp_table()

    

    def _build_dp_table(self):

        """构建 LCS DP 表"""

        # dp[i][j] = str1[0:i] 和 str2[0:j] 的 LCS 长度

        self.dp_table = np.zeros((self.m + 1, self.n + 1), dtype=int)

        

        self.history.append({

            'step': 0,

            'action': 'init',

            'table': copy.deepcopy(self.dp_table),

            'current': None,

            'message': '初始化 LCS DP 表'

        })

        

        step = 0

        for i in range(1, self.m + 1):

            for j in range(1, self.n + 1):

                step += 1

                

                if self.str1[i-1] == self.str2[j-1]:

                    self.dp_table[i][j] = self.dp_table[i-1][j-1] + 1

                else:

                    self.dp_table[i][j] = max(self.dp_table[i-1][j], self.dp_table[i][j-1])

                

                self.history.append({

                    'step': step,

                    'action': 'fill',

                    'i': i,

                    'j': j,

                    'match': self.str1[i-1] == self.str2[j-1],

                    'char1': self.str1[i-1],

                    'char2': self.str2[j-1],

                    'table': copy.deepcopy(self.dp_table),

                    'current': (i, j),

                    'message': f"比较: str1[{i}]='{self.str1[i-1]}' vs str2[{j}]='{self.str2[j-1]}'"

                })

        

        self.lcs_length = self.dp_table[self.m][self.n]

        self._backtrack()

    

    def _backtrack(self):

        """回溯找出 LCS"""

        self.backtrack_path = []

        i, j = self.m, self.n

        

        while i > 0 and j > 0:

            if self.str1[i-1] == self.str2[j-1]:

                self.backtrack_path.append((i, j, self.str1[i-1]))

                i -= 1

                j -= 1

            elif self.dp_table[i-1][j] >= self.dp_table[i][j-1]:

                self.backtrack_path.append((i, j, None))

                i -= 1

            else:

                self.backtrack_path.append((i, j, None))

                j -= 1

        

        self.backtrack_path.reverse()

        self.lcs_result = ''.join([p[2] for p in self.backtrack_path if p[2]])

    

    def plot_static(self, save_path=None):

        """绘制静态 LCS 表"""

        fig, ax = plt.subplots(figsize=(12, 10))

        

        self._draw_lcs_table(ax, highlight_path=True)

        

        plt.tight_layout()

        if save_path:

            plt.savefig(save_path, dpi=150, bbox_inches='tight')

            print(f"图片已保存到: {save_path}")

        plt.show()

    

    def _draw_lcs_table(self, ax, highlight_path=False, current=None):

        """绘制 LCS 表"""

        rows, cols = self.dp_table.shape

        

        # 绘制行列标签（字符）

        ax.set_xticks(range(cols))

        ax.set_xticklabels([''] + list(self.str2), fontsize=10)

        ax.set_yticks(range(rows))

        ax.set_yticklabels([''] + list(self.str1), fontsize=10)

        

        # 绘制表格

        for i in range(1, rows):

            for j in range(1, cols):

                # 根据状态设置颜色

                if highlight_path and (i, j) in [(p[0], p[1]) for p in self.backtrack_path]:

                    if (i, j, self.str1[i-1]) in self.backtrack_path:

                        color = COLOR_PATH  # LCS 字符所在位置

                    else:

                        color = '#f5f5dc'  # 回溯经过但非匹配位置

                elif current and i == current[0] and j == current[1]:

                    color = COLOR_CURRENT

                else:

                    color = COLOR_NORMAL

                

                rect = plt.Rectangle((j-0.5, rows-i-1.5), 1, 1,

                                     facecolor=color, edgecolor='black', linewidth=0.5)

                ax.add_patch(rect)

                ax.text(j, rows-i-1, str(int(self.dp_table[i][j])),

                       ha='center', va='center', fontsize=10, fontweight='bold')

        

        ax.set_xlim(-0.5, cols-0.5)

        ax.set_ylim(-0.5, rows-0.5)

        ax.set_aspect('equal')

        ax.set_title(f'LCS 表 (长度: {self.lcs_length}, 结果: "{self.lcs_result}")', 

                    fontsize=14, fontweight='bold')

    

    def plot_animate(self, save_gif=False, gif_path='lcs_animation.gif'):

        """绘制 LCS 动画"""

        fig, ax = plt.subplots(figsize=(12, 10))

        

        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,

                           verticalalignment='top', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        

        def init():

            return []

        

        def update(frame):

            ax.clear()

            state = self.history[frame]

            

            match_info = ''

            if state['action'] == 'fill':

                match_info = f" → {'匹配!' if state['match'] else '不匹配'}"

            

            info_text.set_text(

                f"步骤: {state['step']}\n"

                f"{state['message']}{match_info}\n"

                f"LCS 长度: {self.lcs_length}"

            )

            

            self._draw_lcs_table(ax, current=state.get('current'))

            

            return []

        

        ani = animation.FuncAnimation(fig, update, frames=len(self.history),

                                     init_func=init, blit=False, interval=FRAME_INTERVAL)

        

        if save_gif:

            print("正在生成 GIF，请稍候...")

            ani.save(gif_path, writer='pillow', fps=8)

            print(f"GIF 已保存到: {gif_path}")

        

        plt.show()

        return ani

    

    def plot_backtrack_animate(self, save_gif=False, gif_path='lcs_backtrack.gif'):

        """绘制回溯动画"""

        fig, ax = plt.subplots(figsize=(12, 10))

        

        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,

                           verticalalignment='top', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        

        def init():

            return []

        

        def update(frame):

            ax.clear()

            

            # 绘制完整表格（淡化）

            self._draw_lcs_table(ax, highlight_path=True, current=None)

            

            # 高亮当前回溯点

            if frame < len(self.backtrack_path):

                i, j, char = self.backtrack_path[frame]

                color = COLOR_PATH if char else '#f5f5dc'

                rect = plt.Rectangle((j-0.5, self.m+1-i-0.5), 1, 1,

                                     facecolor=color, edgecolor=COLOR_PATH, linewidth=2)

                ax.add_patch(rect)

                ax.text(j, self.m+1-i, str(int(self.dp_table[i][j])),

                       ha='center', va='center', fontsize=10, fontweight='bold')

                

                if char:

                    info_text.set_text(

                        f"回溯步骤: {frame + 1}/{len(self.backtrack_path)}\n"

                        f"位置: ({i}, {j})\n"

                        f"匹配字符: '{char}'\n"

                        f"LCS 累积: {self.lcs_result[:frame+1]}"

                    )

                else:

                    info_text.set_text(

                        f"回溯步骤: {frame + 1}/{len(self.backtrack_path)}\n"

                        f"位置: ({i}, {j})\n"

                        f"不匹配，继续回溯"

                    )

            

            return []

        

        total_frames = len(self.backtrack_path) + 10  # 额外帧用于显示最终结果

        ani = animation.FuncAnimation(fig, update, frames=total_frames,

                                     init_func=init, blit=False, interval=600)

        

        if save_gif:

            print("正在生成 GIF，请稍候...")

            ani.save(gif_path, writer='pillow', fps=3)

            print(f"GIF 已保存到: {gif_path}")

        

        plt.show()

        return ani





def main():

    """主函数"""

    import argparse

    

    parser = argparse.ArgumentParser(description='动态规划可视化')

    parser.add_argument('--animate', action='store_true', help='显示动画')

    parser.add_argument('--gif', action='store_true', help='生成 GIF')

    parser.add_argument('--lcs', action='store_true', help='只演示 LCS')

    parser.add_argument('--knapsack', action='store_true', help='只演示背包')

    args = parser.parse_args()

    

    print("=" * 50)

    print("动态规划可视化演示")

    print("=" * 50)

    

    if args.lcs:

        # LCS 演示

        print("\n[最长公共子序列 LCS]")

        str1 = "ABCDGH"

        str2 = "AEDFHR"

        print(f"字符串1: {str1}")

        print(f"字符串2: {str2}")

        

        lcs_viz = LCSVisualizer(str1, str2)

        print(f"LCS 长度: {lcs_viz.lcs_length}")

        print(f"LCS 结果: {lcs_viz.lcs_result}")

        

        if args.gif:

            lcs_viz.plot_animate(save_gif=True, gif_path='lcs_animation.gif')

        elif args.animate:

            lcs_viz.plot_animate()

        else:

            lcs_viz.plot_static()

    

    elif args.knapsack:

        # 背包演示

        print("\n[0-1 背包问题]")

        weights = [2, 3, 4, 5]

        values = [3, 4, 5, 6]

        capacity = 8

        print(f"物品重量: {weights}")

        print(f"物品价值: {values}")

        print(f"背包容量: {capacity}")

        

        knap_viz = KnapsackVisualizer(weights, values, capacity)

        print(f"最大价值: {knap_viz.max_value}")

        

        if args.gif:

            knap_viz.plot_animate(save_gif=True, gif_path='knapsack_animation.gif')

        elif args.animate:

            knap_viz.plot_animate()

        else:

            knap_viz.plot_static()

    

    else:

        # 两个都演示

        # 0-1 背包

        print("\n[0-1 背包问题]")

        weights = [2, 3, 4, 5]

        values = [3, 4, 5, 6]

        capacity = 8

        print(f"物品重量: {weights}")

        print(f"物品价值: {values}")

        print(f"背包容量: {capacity}")

        

        knap_viz = KnapsackVisualizer(weights, values, capacity)

        print(f"最大价值: {knap_viz.max_value}")

        knap_viz.plot_static()

        

        # LCS

        print("\n[最长公共子序列 LCS]")

        str1 = "ABCDGH"

        str2 = "AEDFHR"

        print(f"字符串1: {str1}")

        print(f"字符串2: {str2}")

        

        lcs_viz = LCSVisualizer(str1, str2)

        print(f"LCS 长度: {lcs_viz.lcs_length}")

        print(f"LCS 结果: {lcs_viz.lcs_result}")

        lcs_viz.plot_static()

    

    print("\n可视化完成!")





if __name__ == '__main__':

    main()

