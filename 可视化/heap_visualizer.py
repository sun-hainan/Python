# -*- coding: utf-8 -*-
"""
算法实现：可视化 / heap_visualizer

本文件实现 heap_visualizer 相关的算法功能。
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


class MaxHeap:
    def __init__(self):
        self.heap = []
        self.steps = []  # 可视化步骤

    def size(self):
        return len(self.heap)

    def parent(self, i):
        return (i - 1) // 2

    def left(self, i):
        return 2 * i + 1

    def right(self, i):
        return 2 * i + 2

    def swap(self, i, j):
        self.heap[i], self.heap[j] = self.heap[j], self.heap[i]
        self.steps.append(('swap', i, j))

    def heapify_down(self, i):
        """从节点 i 向下堆化"""
        smallest = i
        l = self.left(i)
        r = self.right(i)

        if l < self.size() and self.heap[l] > self.heap[smallest]:
            smallest = l
        if r < self.size() and self.heap[r] > self.heap[smallest]:
            smallest = r

        if smallest != i:
            self.swap(i, smallest)
            self.heapify_down(smallest)

    def heapify_up(self, i):
        """从节点 i 向上堆化（插入时用）"""
        while i > 0 and self.heap[self.parent(i)] < self.heap[i]:
            self.swap(i, self.parent(i))
            i = self.parent(i)

    def insert(self, val):
        self.heap.append(val)
        self.steps.append(('insert', len(self.heap) - 1, val))
        self.heapify_up(len(self.heap) - 1)

    def extract_max(self):
        if self.size() == 0:
            return None
        max_val = self.heap[0]
        self.heap[0] = self.heap[-1]
        self.heap.pop()
        if self.size() > 0:
            self.heapify_down(0)
        self.steps.append(('extract', 0, max_val))
        return max_val


def heap_sort(arr):
    """堆排序"""
    heap = MaxHeap()
    for val in arr:
        heap.insert(val)

    result = []
    while heap.size() > 0:
        result.append(heap.extract_max())
    return result


def draw_heap(heap, ax, title=""):
    """绘制堆的树形结构"""
    ax.clear()
    ax.set_xlim(-1, 10)
    ax.set_ylim(-0.5, 5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title, fontsize=12)

    if not heap:
        ax.text(5, 2, "堆为空", ha='center', fontsize=14)
        return

    n = len(heap)
    positions = {}

    # BFS 计算位置
    queue = [(0, 5, 4)]
    level = 0
    level_count = 0
    while queue:
        i, x, y = queue.pop(0)
        if i < n:
            positions[i] = (x, y)
            l = 2 * i + 1
            r = 2 * i + 2
            dx = 2 / (level + 2)
            if l < n:
                queue.append((l, x - dx * (5 - level), y - 1.2))
            if r < n:
                queue.append((r, x + dx * (5 - level), y - 1.2))

    # 绘制边
    for i in range(n):
        l = 2 * i + 1
        r = 2 * i + 2
        if l < n and l in positions:
            ax.plot([positions[i][0], positions[l][0]], [positions[i][1], positions[l][1]], 'gray', linewidth=1.5)
        if r < n and r in positions:
            ax.plot([positions[i][0], positions[r][0]], [positions[i][1], positions[r][1]], 'gray', linewidth=1.5)

    # 绘制节点
    for i, (x, y) in positions.items():
        color = 'lightcoral' if heap[i] == max(heap) else 'lightblue'
        circle = plt.Circle((x, y), 0.35, color=color, ec='navy', linewidth=2)
        ax.add_patch(circle)
        ax.text(x, y, str(heap[i]), ha='center', va='center', fontsize=11, fontweight='bold')

    # 数组表示
    arr_str = ' '.join(str(v) for v in heap)
    ax.text(5, -0.2, f'数组: [{arr_str}]', ha='center', fontsize=10, family='monospace')


def visualize_heap_sort(arr, save_path='heap_sort.png'):
    """可视化堆排序过程"""
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))

    heap = MaxHeap()

    # 阶段1：构建堆
    ax1 = axes[0]
    for val in arr:
        heap.insert(val)
    draw_heap(heap.heap, ax1, '阶段1：最大堆构建完成')

    # 阶段2：堆排序
    ax2 = axes[1]
    sorted_arr = heap_sort(arr.copy())
    draw_heap([], ax2, f'阶段2：排序完成（降序）\n结果: {sorted_arr}')

    # 阶段3：数组对比
    ax3 = axes[2]
    ax3.text(0.5, 0.8, f'原始数组: {arr}', ha='center', fontsize=12, family='monospace')
    ax3.text(0.5, 0.5, f'堆排序结果: {sorted_arr}', ha='center', fontsize=12, family='monospace', color='green')
    ax3.text(0.5, 0.2, '注：最大堆排序得到升序结果', ha='center', fontsize=10, color='gray')
    ax3.axis('off')
    ax3.set_title('排序结果对比', fontsize=12)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"图片已保存: {save_path}")
    plt.show()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 堆排序可视化测试 ===\n")

    arr = [4, 10, 3, 5, 1, 8, 7, 2, 9, 6]
    print(f"原始数组: {arr}")

    # 堆排序
    sorted_arr = heap_sort(arr.copy())
    print(f"排序结果: {sorted_arr}")

    # 可视化
    visualize_heap_sort(arr)
