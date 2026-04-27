# -*- coding: utf-8 -*-

"""

算法实现：可视化 / union_find_visualizer



本文件实现 union_find_visualizer 相关的算法功能。

"""



import matplotlib.pyplot as plt

import matplotlib.patches as mpatches

import numpy as np





class UnionFind:

    def __init__(self, n):

        self.parent = list(range(n))

        self.rank = [0] * n

        self.steps = []  # 操作历史



    def find(self, x):

        """路径压缩查找"""

        if self.parent[x] != x:

            original = self.parent[x]

            self.parent[x] = self.find(self.parent[x])

            self.steps.append(('find_compress', x, original, self.parent[x]))

        return self.parent[x]



    def union(self, x, y):

        """按秩合并"""

        px, py = self.find(x), self.find(y)

        if px == py:

            self.steps.append(('union_same', x, y, px))

            return px



        if self.rank[px] < self.rank[py]:

            px, py = py, px



        old_parent_py = self.parent[py]

        self.parent[py] = px

        self.steps.append(('union', x, y, px, py, old_parent_py))



        if self.rank[px] == self.rank[py]:

            self.rank[px] += 1



        return px



    def connected(self, x, y):

        return self.find(x) == self.find(y)



    def get_groups(self):

        """返回所有连通分量"""

        groups = {}

        for i in range(len(self.parent)):

            root = self.find(i)

            if root not in groups:

                groups[root] = []

            groups[root].append(i)

        return groups





def draw_uf_state(uf, ax, title=""):

    """绘制并查集状态"""

    ax.clear()

    ax.set_xlim(-1, 10)

    ax.set_ylim(-0.5, 5)

    ax.set_aspect('equal')

    ax.axis('off')

    ax.set_title(title, fontsize=12)



    n = len(uf.parent)

    groups = uf.get_groups()



    # 每个连通分量一排

    group_list = list(groups.values())

    for gi, group in enumerate(group_list):

        y = 3 - gi * 1.2

        # 绘制节点

        for i, node in enumerate(group):

            x = 2 + i * 1.5

            parent = uf.parent[node]

            is_root = (node == uf.find(node))

            color = 'lightgreen' if is_root else 'lightblue'

            circle = plt.Circle((x, y), 0.35, color=color, ec='navy', linewidth=2)

            ax.add_patch(circle)

            ax.text(x, y, str(node), ha='center', va='center', fontsize=11, fontweight='bold')

            # 指向父节点的箭头（如果不是根）

            if parent != node:

                parent_idx = group.index(parent) if parent in group else -1

                if parent_idx >= 0:

                    px = 2 + parent_idx * 1.5

                    ax.annotate('', xy=(px, y + 0.35), xytext=(x, y + 0.35),

                               arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))

            # rank 标注

            ax.text(x + 0.4, y - 0.4, f'r={uf.rank[node]}', fontsize=8, color='gray')



    # 显示连通分量数

    ax.text(0, 4.5, f'连通分量数: {len(groups)}', fontsize=10)





def visualize_union_find(n, operations, save_path='union_find.png'):

    """可视化并查集操作过程"""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    fig.suptitle('并查集（Union-Find）可视化 - 路径压缩 + 按秩合并', fontsize=14)



    uf = UnionFind(n)



    # 初始状态

    draw_uf_state(uf, axes[0, 0], '初始状态（每个节点独立）')



    # 执行操作

    for i, (op, x, y) in enumerate(operations):

        uf.union(x, y)

        if i < 2:  # 显示前几个状态

            ax_idx = (i // 2 + 1, i % 2) if i < 3 else (2, 0)

            draw_uf_state(uf, axes[ax_idx[0], ax_idx[1]],

                         f'操作 {i+1}: union({x}, {y})')



    # 最终状态

    draw_uf_state(uf, axes[1, 1], f'最终状态（共{len(uf.get_groups())}个连通分量）')



    # 操作历史

    history_text = "操作历史:\n" + "\n".join([

        f"  {i+1}. {op}: {x}-{y} -> 根={root if 'root' in locals() else 'N/A'}"

        for i, (op, *rest) in enumerate(uf.steps[:10])

    ])

    axes[1, 0].text(0, 0.9, history_text, fontsize=9, family='monospace',

                    transform=axes[1, 0].transAxes, verticalalignment='top')

    axes[1, 0].axis('off')

    axes[1, 0].set_title('操作记录', fontsize=12)



    plt.tight_layout()

    plt.savefig(save_path, dpi=150, bbox_inches='tight')

    print(f"图片已保存: {save_path}")

    plt.show()





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 并查集可视化测试 ===\n")



    n = 6

    print(f"元素数量: {n}")



    # 执行合并操作

    operations = [

        ('union', 0, 1),

        ('union', 2, 3),

        ('union', 4, 5),

        ('union', 0, 2),  # 合并 {0,1} 和 {2,3}

        ('union', 0, 4),  # 合并 {0,1,2,3} 和 {4,5}

    ]



    print("操作序列:")

    for op, x, y in operations:

        print(f"  union({x}, {y})")



    print()

    visualize_union_find(n, operations)



    # 额外测试连通性

    uf = UnionFind(6)

    for x, y in [(0,1), (2,3), (4,5), (0,2), (0,4)]:

        uf.union(x, y)



    print("连通性检查:")

    test_pairs = [(0, 5), (1, 4), (2, 5)]

    for a, b in test_pairs:

        print(f"  connected({a}, {b}): {uf.connected(a, b)}")

