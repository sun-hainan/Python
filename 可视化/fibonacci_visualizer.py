# -*- coding: utf-8 -*-

"""

算法实现：可视化 / fibonacci_visualizer



本文件实现 fibonacci_visualizer 相关的算法功能。

"""



import numpy as np

import matplotlib.pyplot as plt

import matplotlib.patches as patches

import matplotlib.animation as animation

from functools import lru_cache

from collections import defaultdict



# 中文字体设置

plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False





class FibonacciTree:

    """

    斐波那契递归树类 - 用于可视化和计算

    """

    

    def __init__(self, n):

        """

        初始化

        

        参数:

            n: 计算 fib(n)

        """

        self.n = n

        self.call_count_naive = 0  # 朴素递归调用次数

        self.call_count_memo = 0    # 记忆化调用次数

        self.call_count_dp = 0      # DP调用次数

        

        # 存储递归树结构

        self.tree_nodes = []  # (node_id, parent_id, value, depth, x, y)

        self.node_counter = [0]

        self.tree_edges = []

        

        # 存储记忆化缓存用于可视化

        self.memo_cache = {}

        self.dp_table = []

    

    def fib_naive(self, n, parent_id=None, depth=0):

        """

        朴素递归（无优化）- 记录所有调用

        

        参数:

            n: 要计算的斐波那契数

            parent_id: 父节点ID

            depth: 当前深度

        

        返回:

            int: fib(n) 的值

        """

        self.call_count_naive += 1

        node_id = self.node_counter[0]

        self.node_counter[0] += 1

        

        # 基准情况

        if n <= 1:

            self.tree_nodes.append({

                'id': node_id,

                'parent': parent_id,

                'value': n,

                'depth': depth,

                'label': f'F({n})'

            })

            if parent_id is not None:

                self.tree_edges.append((parent_id, node_id))

            return n

        

        # 递归计算

        left_id = self.node_counter[0]

        fib_n1 = self.fib_naive(n - 1, node_id, depth + 1)

        

        right_id = self.node_counter[0]

        fib_n2 = self.fib_naive(n - 2, node_id, depth + 1)

        

        # 记录当前节点

        self.tree_nodes.append({

            'id': node_id,

            'parent': parent_id,

            'value': fib_n1 + fib_n2,

            'depth': depth,

            'label': f'F({n})'

        })

        self.tree_edges.append((parent_id, node_id))

        

        return fib_n1 + fib_n2

    

    def fib_memoized(self, n, memo=None):

        """

        记忆化递归（自顶向下DP）

        

        参数:

            n: 要计算的斐波那契数

            memo: 缓存字典

        

        返回:

            int: fib(n) 的值

        """

        if memo is None:

            memo = {}

        

        self.call_count_memo += 1

        

        if n <= 1:

            memo[n] = n

            return n

        

        if n in memo:

            return memo[n]

        

        memo[n] = self.fib_memoized(n - 1, memo) + self.fib_memoized(n - 2, memo)

        return memo[n]

    

    def fib_dp(self, n):

        """

        自底向上动态规划

        

        参数:

            n: 要计算的斐波那契数

        

        返回:

            int: fib(n) 的值

        """

        if n <= 1:

            return n

        

        dp = [0] * (n + 1)

        dp[0] = 0

        dp[1] = 1

        

        for i in range(2, n + 1):

            self.call_count_dp += 1

            dp[i] = dp[i - 1] + dp[i - 2]

        

        self.dp_table = dp

        return dp[n]

    

    def compute(self):

        """执行所有计算"""

        # 朴素递归

        result_naive = self.fib_naive(self.n)

        

        # 记忆化

        result_memo = self.fib_memoized(self.n)

        

        # DP

        result_dp = self.fib_dp(self.n)

        

        return result_naive, result_memo, result_dp





def draw_fib_tree(tree_nodes, tree_edges, ax, highlight_ids=None, visited_ids=None, 

                  memo_nodes=None, title="斐波那契递归树"):

    """

    绘制斐波那契递归树

    

    参数:

        tree_nodes: 节点列表

        tree_edges: 边列表

        ax: matplotlib 子图

        highlight_ids: 高亮节点ID集合

        visited_ids: 已访问节点ID集合

        memo_nodes: 已在缓存中的节点

        title: 图表标题

    """

    ax.clear()

    ax.set_title(title, fontsize=14, fontweight='bold')

    ax.set_aspect('equal')

    ax.axis('off')

    

    if not tree_nodes:

        return

    

    # 计算树的布局

    max_depth = max(n['depth'] for n in tree_nodes)

    

    # 按深度和ID排序，计算x坐标

    depth_groups = defaultdict(list)

    for node in tree_nodes:

        depth_groups[node['depth']].append(node)

    

    for depth, nodes in depth_groups.items():

        nodes.sort(key=lambda x: x['id'])

        n_nodes = len(nodes)

        for i, node in enumerate(nodes):

            # x坐标：按顺序均匀分布

            node['x'] = (i + 1) / (n_nodes + 1)

            # y坐标：深度越深，y越小

            node['y'] = 1 - depth / (max_depth + 1)

    

    # 绘制边

    for parent_id, child_id in tree_edges:

        parent = next((n for n in tree_nodes if n['id'] == parent_id), None)

        child = next((n for n in tree_nodes if n['id'] == child_id), None)

        if parent and child:

            ax.annotate('', xy=(child['x'], child['y']), xytext=(parent['x'], parent['y']),

                       arrowprops=dict(arrowstyle='->', color='gray', lw=0.8))

    

    # 绘制节点

    for node in tree_nodes:

        x, y = node['x'], node['y']

        

        # 确定颜色

        if highlight_ids and node['id'] in highlight_ids:

            color = '#FF6347'  # 红色 - 当前处理

            edge_color = 'darkred'

        elif visited_ids and node['id'] in visited_ids:

            color = '#90EE90'  # 浅绿色 - 已计算

            edge_color = 'green'

        elif memo_nodes and node.get('value') in memo_nodes:

            color = '#87CEEB'  # 天蓝色 - 在缓存中

            edge_color = 'blue'

        else:

            color = '#FFD700'  # 金色 - 默认

            edge_color = 'black'

        

        # 绘制节点圆

        circle = plt.Circle((x, y), 0.025, color=color, ec=edge_color, lw=1.5)

        ax.add_patch(circle)

        

        # 绘制标签

        label = node['label']

        ax.text(x, y + 0.04, label, ha='center', va='bottom', fontsize=6)





def visualize_fibonacci(n):

    """

    可视化斐波那契数列计算过程

    

    参数:

        n: 计算 fib(n)

    """

    if n > 10:

        print(f"警告: n={n} 较大，递归树可能有 {2**(n+1)-1} 个节点，可能较慢")

        print("建议 n <= 10 以获得最佳可视化效果")

    

    # 创建斐波那契树

    fib_tree = FibonacciTree(n)

    result_naive, result_memo, result_dp = fib_tree.compute()

    

    print("=" * 60)

    print(f"斐波那契数列计算结果 (n={n})")

    print("=" * 60)

    print(f"朴素递归结果: {result_naive}")

    print(f"记忆化结果:   {result_memo}")

    print(f"DP结果:       {result_dp}")

    print(f"\n调用次数对比:")

    print(f"  朴素递归: {fib_tree.call_count_naive} 次")

    print(f"  记忆化:   {fib_tree.call_count_memo} 次")

    print(f"  DP:       {fib_tree.call_count_dp} 次")

    print(f"  （理论上朴素为 O(2^n)，记忆化/DP 为 O(n)）")

    

    # ===== 创建图形 =====

    fig = plt.figure(figsize=(18, 10))

    

    # 左上：递归树

    ax_tree = plt.subplot2grid((2, 3), (0, 0), colspan=2)

    

    # 右上：复杂度对比

    ax_complexity = plt.subplot2grid((2, 3), (0, 2))

    

    # 下排：调用次数柱状图 + DP表格

    ax_bar = plt.subplot2grid((2, 3), (1, 0))

    ax_dp_table = plt.subplot2grid((2, 3), (1, 1))

    ax_memo = plt.subplot2grid((2, 3), (1, 2))

    

    # ===== 绘制递归树 =====

    draw_fib_tree(fib_tree.tree_nodes, fib_tree.tree_edges, ax_tree,

                  title=f'斐波那契递归树 F({n})\n(节点数: {len(fib_tree.tree_nodes)})')

    

    # ===== 绘制复杂度对比图 =====

    ns = np.arange(1, 15)

    naive_complexity = 2 ** ns  # 指数级

    dp_complexity = ns * 5     # 线性（乘以5以便可视化）

    

    ax_complexity.clear()

    ax_complexity.plot(ns, naive_complexity, 'r-', label='朴素递归 O(2^n)', linewidth=2)

    ax_complexity.plot(ns, dp_complexity, 'g-', label='动态规划 O(n)', linewidth=2)

    ax_complexity.set_yscale('log')

    ax_complexity.set_title('时间复杂度对比', fontsize=12)

    ax_complexity.set_xlabel('n')

    ax_complexity.set_ylabel('操作次数 (对数)')

    ax_complexity.legend()

    ax_complexity.grid(True, alpha=0.3)

    

    # ===== 绘制调用次数柱状图 =====

    ax_bar.clear()

    methods = ['朴素递归', '记忆化', '动态规划']

    counts = [fib_tree.call_count_naive, fib_tree.call_count_memo, fib_tree.call_count_dp]

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    

    bars = ax_bar.bar(methods, counts, color=colors, edgecolor='black')

    ax_bar.set_title('调用次数对比', fontsize=12)

    ax_bar.set_ylabel('调用次数')

    

    # 在柱状图上添加数值标签

    for bar, count in zip(bars, counts):

        ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height(),

                   f'{count}', ha='center', va='bottom', fontsize=10)

    

    # ===== 绘制DP表格 =====

    ax_dp_table.clear()

    ax_dp_table.axis('off')

    ax_dp_table.set_title('自底向上 DP 表', fontsize=12)

    

    dp_data = fib_tree.dp_table

    if dp_data:

        table_data = [[i, dp_data[i]] for i in range(len(dp_data))]

        table = ax_dp_table.table(cellText=table_data[:min(12, len(dp_data))],

                                   colLabels=['索引 i', 'fib(i)'],

                                   cellLoc='center', loc='center')

        table.auto_set_font_size(False)

        table.set_fontsize(10)

        table.scale(1, 1.5)

    

    # ===== 绘制记忆化信息 =====

    ax_memo.clear()

    ax_memo.axis('off')

    ax_memo.set_title('记忆化缓存内容', fontsize=12)

    

    memo_text = "自顶向下缓存:\n\n"

    for k, v in sorted(fib_tree.memo_cache.items()):

        memo_text += f"  F({k}) = {v}\n"

    memo_text += f"\n总缓存项数: {len(fib_tree.memo_cache)}"

    

    ax_memo.text(0.1, 0.5, memo_text, fontsize=10, va='center',

                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    

    plt.tight_layout()

    plt.show()

    

    # ===== 动画版本（n较小时） =====

    if n <= 7:

        print(f"\n为 n={n} 生成动画...")

        visualize_fibonacci_animation(n)





def visualize_fibonacci_animation(n):

    """

    斐波那契递归的动画可视化（n较小）

    """

    # 创建斐波那契树

    fib_tree = FibonacciTree(n)

    

    # 重新计算以获取树结构

    result = fib_tree.fib_naive(n)

    

    fig, ax = plt.subplots(figsize=(14, 10))

    

    # 生成动画帧

    frames = []

    

    # 按深度分组处理

    depth_groups = defaultdict(list)

    for node in fib_tree.tree_nodes:

        depth_groups[node['depth']].append(node['id'])

    

    # 帧1：初始状态

    frames.append({

        'highlight': set(),

        'visited': set(),

        'title': f'斐波那契递归树 - 初始状态'

    })

    

    # 逐深度高亮

    for depth in range(max(d for n in fib_tree.tree_nodes for d in [n['depth']]) + 1):

        nodes_at_depth = [n for n in fib_tree.tree_nodes if n['depth'] == depth]

        highlight = {n['id'] for n in nodes_at_depth}

        visited = {n['id'] for n in fib_tree.tree_nodes if n['depth'] <= depth}

        

        frames.append({

            'highlight': highlight,

            'visited': visited,

            'title': f'计算深度 {depth} 的节点'

        })

    

    # 最后显示完整结果

    frames.append({

        'highlight': set(),

        'visited': {n['id'] for n in fib_tree.tree_nodes},

        'title': f'计算完成: F({n}) = {result}'

    })

    

    def init():

        ax.clear()

        ax.set_aspect('equal')

        ax.axis('off')

        return []

    

    def update(frame):

        draw_fib_tree(fib_tree.tree_nodes, fib_tree.tree_edges, ax,

                      highlight_ids=frame['highlight'],

                      visited_ids=frame['visited'],

                      title=frame['title'])

        return []

    

    anim = animation.FuncAnimation(fig, update, frames=frames,

                                   init_func=init, interval=1000, repeat=True)

    

    plt.tight_layout()

    plt.show()





def visualize_time_complexity():

    """

    可视化斐波那契不同实现的时间复杂度对比

    """

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    

    # ===== 左图：不同n的调用次数 =====

    ax1 = axes[0]

    

    ns = range(1, 15)

    naive_counts = []

    memo_counts = []

    dp_counts = []

    

    for n in ns:

        ft = FibonacciTree(n)

        ft.compute()

        naive_counts.append(ft.call_count_naive)

        memo_counts.append(ft.call_count_memo)

        dp_counts.append(ft.call_count_dp)

    

    ax1.plot(ns, naive_counts, 'ro-', label='朴素递归', linewidth=2, markersize=6)

    ax1.plot(ns, memo_counts, 'g^-', label='记忆化递归', linewidth=2, markersize=6)

    ax1.plot(ns, dp_counts, 'bs-', label='自底向上DP', linewidth=2, markersize=6)

    

    ax1.set_title('斐波那契算法调用次数 vs n', fontsize=13)

    ax1.set_xlabel('n')

    ax1.set_ylabel('函数调用次数')

    ax1.legend()

    ax1.grid(True, alpha=0.3)

    ax1.set_yscale('log')

    

    # ===== 右图：理论复杂度对比 =====

    ax2 = axes[1]

    

    ns = np.linspace(0.1, 10, 100)

    naive_complexity = 2 ** ns

    dp_complexity = ns * 10

    

    ax2.plot(ns, naive_complexity, 'r-', label='朴素: O(2^n)', linewidth=2)

    ax2.plot(ns, dp_complexity, 'g-', label='DP: O(n)', linewidth=2)

    ax2.set_yscale('log')

    ax2.set_title('时间复杂度对比（理论）', fontsize=13)

    ax2.set_xlabel('n')

    ax2.set_ylabel('操作数量（对数）')

    ax2.legend()

    ax2.grid(True, alpha=0.3)

    ax2.set_ylim(1, 1e10)

    

    plt.tight_layout()

    plt.show()





if __name__ == '__main__':

    import sys

    

    print("=" * 60)

    print("斐波那契可视化测试")

    print("=" * 60)

    

    # 测试基本功能

    test_n = 6

    

    print(f"\n测试计算 fib({test_n}):")

    ft = FibonacciTree(test_n)

    ft.compute()

    

    print(f"  朴素递归: {ft.call_count_naive} 次调用")

    print(f"  记忆化:   {ft.call_count_memo} 次调用")

    print(f"  DP:       {ft.call_count_dp} 次调用")

    

    # 启动可视化

    print(f"\n启动可视化（n={test_n}）...")

    visualize_fibonacci(test_n)

    

    # 复杂度对比图

    print("\n启动时间复杂度对比图...")

    visualize_time_complexity()

    

    print("\n测试完成!")

