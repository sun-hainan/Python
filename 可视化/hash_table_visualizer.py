# -*- coding: utf-8 -*-
"""
算法实现：可视化 / hash_table_visualizer

本文件实现 hash_table_visualizer 相关的算法功能。
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np


class HashTableChain:
    """链地址法哈希表"""

    def __init__(self, size=10):
        self.size = size
        self.table = [[] for _ in range(size)]
        self.history = []  # 操作历史

    def hash(self, key):
        return key % self.size

    def insert(self, key):
        idx = self.hash(key)
        if key not in self.table[idx]:
            self.table[idx].append(key)
            self.history.append(('insert', idx, key, True))
        else:
            self.history.append(('insert', idx, key, False))
        return idx

    def search(self, key):
        idx = self.hash(key)
        found = key in self.table[idx]
        self.history.append(('search', idx, key, found))
        return found

    def visualize(self, save_path='hash_table_chain.png'):
        """可视化链地址法哈希表"""
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.set_xlim(-1, self.size + 1)
        ax.set_ylim(-1, 12)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('哈希表（链地址法）可视化\n每次插入/查找操作都被记录', fontsize=14)

        # 绘制桶（数组槽）
        for i in range(self.size):
            x = i
            rect = FancyBboxPatch((x - 0.4, 6), 0.8, 1.5,
                                   boxstyle="round,pad=0.05",
                                   facecolor='lightblue', edgecolor='navy', linewidth=2)
            ax.add_patch(rect)
            ax.text(x, 6.75, f'{i}', ha='center', va='center', fontsize=12, fontweight='bold')

            # 绘制链表
            chain = self.table[i]
            if chain:
                # 垂直线
                ax.plot([x, x], [5.5, 4.5], 'b-', linewidth=2)
                # 节点
                for j, key in enumerate(chain):
                    y = 4.5 - j * 1.2
                    if j == 0:
                        circle = plt.Circle((x, y), 0.4, color='orange', ec='darkorange', linewidth=2)
                        ax.add_patch(circle)
                        ax.text(x, y, str(key), ha='center', va='center', fontsize=10, fontweight='bold')
                        if len(chain) > 1:
                            ax.annotate('', xy=(x, y - 0.6), xytext=(x, y - 0.4),
                                       arrowprops=dict(arrowstyle='->', color='gray'))
                    else:
                        circle = plt.Circle((x, y), 0.4, color='orange', ec='darkorange', linewidth=2)
                        ax.add_patch(circle)
                        ax.text(x, y, str(key), ha='center', va='center', fontsize=10, fontweight='bold')
                        if j < len(chain) - 1:
                            ax.annotate('', xy=(x, y - 0.6), xytext=(x, y - 0.4),
                                       arrowprops=dict(arrowstyle='->', color='gray'))

        # 绘制历史记录
        ax.text(0, -0.5, '操作历史:', fontsize=11, fontweight='bold')
        history_text = '\n'.join([f"  {h[0]}: 键={h[2]}, 桶={h[1]}, {'成功' if h[3] else ('已存在' if h[0]=='insert' else '失败')}"
                                  for h in self.history[-5:]])
        ax.text(0, -1.2, history_text, fontsize=9, family='monospace', va='top')

        # 图例
        ax.text(self.size - 3, 11, '图例:', fontsize=10, fontweight='bold')
        ax.add_patch(FancyBboxPatch((self.size - 3, 10), 0.6, 0.6, boxstyle="round", facecolor='lightblue', edgecolor='navy'))
        ax.text(self.size - 2, 10.3, '= 哈希桶（数组索引）', fontsize=9)
        ax.add_patch(plt.Circle((self.size - 2.5, 9.2), 0.3, color='orange', ec='darkorange'))
        ax.text(self.size - 2, 9.2, '= 键值节点', fontsize=9, va='center')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
        plt.show()


class HashTableOpen:
    """开放地址法哈希表（线性探测）"""

    def __init__(self, size=10):
        self.size = size
        self.table = [None] * size
        self.history = []

    def hash(self, key):
        return key % self.size

    def insert(self, key):
        idx = self.hash(key)
        original_idx = idx
        attempts = 0
        while self.table[idx] is not None:
            if self.table[idx] == key:
                self.history.append(('insert', key, original_idx, idx, attempts, False, '已存在'))
                return idx
            idx = (idx + 1) % self.size
            attempts += 1
            if idx == original_idx:
                break

        if self.table[idx] is None:
            self.table[idx] = key
            self.history.append(('insert', key, original_idx, idx, attempts, True, '插入成功'))
        return idx

    def search(self, key):
        idx = self.hash(key)
        original_idx = idx
        attempts = 0
        while self.table[idx] is not None:
            if self.table[idx] == key:
                self.history.append(('search', key, original_idx, idx, attempts, True, '找到'))
                return True
            idx = (idx + 1) % self.size
            attempts += 1
            if idx == original_idx:
                break
        self.history.append(('search', key, original_idx, idx, attempts, False, '未找到'))
        return False

    def visualize(self, save_path='hash_table_open.png'):
        """可视化开放地址法哈希表"""
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.set_xlim(-1, self.size + 1)
        ax.set_ylim(-1, 10)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('哈希表（开放地址法-线性探测）可视化', fontsize=14)

        # 绘制桶
        for i in range(self.size):
            x = i
            if self.table[i] is not None:
                color = 'lightgreen'
            else:
                color = 'white'
            rect = FancyBboxPatch((x - 0.4, 2), 0.8, 1.2,
                                   boxstyle="round,pad=0.05",
                                   facecolor=color, edgecolor='navy', linewidth=2)
            ax.add_patch(rect)
            ax.text(x, 2.6, str(i), ha='center', va='center', fontsize=9, color='gray')
            if self.table[i] is not None:
                ax.text(x, 2.3, str(self.table[i]), ha='center', va='center',
                       fontsize=12, fontweight='bold')
            else:
                ax.text(x, 2.3, '-', ha='center', va='center', fontsize=10, color='lightgray')

        # 绘制探测路径（最后一条历史）
        if self.history:
            last = self.history[-1]
            ax.text(0, 6, f'最后操作: {last}', fontsize=10, family='monospace')
            if last[0] == 'insert' and last[5]:
                # 绘制探测箭头
                start_idx = last[2]
                end_idx = last[3]
                if start_idx != end_idx:
                    ax.annotate(f'探测路径\n{start_idx}→{end_idx}', xy=(end_idx, 2.6),
                              xytext=(start_idx + 2, 5),
                              arrowprops=dict(arrowstyle='->', color='red'),
                              fontsize=9, color='red')

        # 历史记录
        ax.text(0, -0.5, '操作历史:', fontsize=11, fontweight='bold')
        history_text = '\n'.join([f"  {h[0]}: 键={h[1]}, 初始={h[2]}, 最终={h[3]}, 探测次数={h[4]}, {h[6]}"
                                  for h in self.history[-5:]])
        ax.text(0, -1.5, history_text, fontsize=9, family='monospace', va='top')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"图片已保存: {save_path}")
        plt.show()


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 哈希表可视化测试 ===\n")

    # 测试链地址法
    print("--- 链地址法 ---")
    ht_chain = HashTableChain(size=7)
    for key in [15, 22, 8, 33, 5, 18, 12]:
        ht_chain.insert(key)
    print(f"插入后: {ht_chain.table}")
    print(f"查找 18: {ht_chain.search(18)}")
    print(f"查找 99: {ht_chain.search(99)}")
    ht_chain.visualize('hash_table_chain.png')

    print()

    # 测试开放地址法
    print("--- 开放地址法（线性探测）---")
    ht_open = HashTableOpen(size=7)
    for key in [15, 22, 8, 33, 5, 18, 12]:
        ht_open.insert(key)
    print(f"插入后: {ht_open.table}")
    print(f"查找 18: {ht_open.search(18)}")
    print(f"查找 99: {ht_open.search(99)}")
    ht_open.visualize('hash_table_open.png')
