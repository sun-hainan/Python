# -*- coding: utf-8 -*-

"""

算法实现：可视化 / bst_visualizer



本文件实现 bst_visualizer 相关的算法功能。

"""



#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

二叉搜索树(BST)与AVL树可视化器

使用 matplotlib 动画展示 BST 的插入、搜索、删除操作

支持 AVL 树旋转操作的可视化



使用方法:

    python bst_visualizer.py              # 静态展示示例树

    python bst_visualizer.py --animate    # 动画演示操作

    python bst_visualizer.py --avl        # AVL 树演示

"""



import matplotlib.pyplot as plt

import matplotlib.animation as animation

import numpy as np



# ============== 节点定义 ==============



class BSTNode:

    """二叉搜索树节点类"""

    

    def __init__(self, key, x=0, y=0):

        self.key = key          # 节点值（key）

        self.left = None       # 左子节点

        self.right = None      # 右子节点

        self.x = x             # 绘图 x 坐标

        self.y = y             # 绘图 y 坐标

        self.parent = None     # 父节点引用

        self.height = 1        # AVL 树用：节点高度

        self.balance = 0       # AVL 树用：平衡因子

    

    def __repr__(self):

        return f"BSTNode({self.key})"





class AVLNode(BSTNode):

    """AVL 树节点（继承自 BSTNode）"""

    

    def __init__(self, key, x=0, y=0):

        super().__init__(key, x, y)

        self.height = 1        # 节点高度

        self.balance = 0       # 平衡因子 = 左子树高度 - 右子树高度





# ============== BST 类 ==============



class BST:

    """二叉搜索树类"""

    

    def __init__(self):

        self.root = None

        self.history = []       # 操作历史记录

        self.node_positions = {}  # 节点绘图位置

    

    def insert(self, key):

        """插入节点"""

        self.history.append({

            'action': 'insert',

            'key': key,

            'tree_state': self._copy_tree(),

            'highlight': None,

            'path': []

        })

        

        if self.root is None:

            self.root = BSTNode(key)

            self._update_positions()

            return

        

        self._insert_recursive(self.root, key, [])

    

    def _insert_recursive(self, node, key, path):

        """递归插入"""

        path = path + [node.key]

        

        if key < node.key:

            if node.left is None:

                node.left = BSTNode(key)

                node.left.parent = node

                self.history.append({

                    'action': 'insert_complete',

                    'key': key,

                    'tree_state': self._copy_tree(),

                    'highlight': key,

                    'path': path

                })

                self._update_positions()

            else:

                self._insert_recursive(node.left, key, path)

        else:

            if node.right is None:

                node.right = BSTNode(key)

                node.right.parent = node

                self.history.append({

                    'action': 'insert_complete',

                    'key': key,

                    'tree_state': self._copy_tree(),

                    'highlight': key,

                    'path': path

                })

                self._update_positions()

            else:

                self._insert_recursive(node.right, key, path)

    

    def search(self, key):

        """搜索节点，返回是否找到及路径"""

        path = []

        node = self.root

        

        while node is not None:

            path.append(node.key)

            if key == node.key:

                return True, path

            elif key < node.key:

                node = node.left

            else:

                node = node.right

        

        return False, path

    

    def delete(self, key):

        """删除节点"""

        self.history.append({

            'action': 'delete_start',

            'key': key,

            'tree_state': self._copy_tree(),

            'highlight': key,

            'path': []

        })

        

        self.root = self._delete_recursive(self.root, key)

        self._update_positions()

    

    def _delete_recursive(self, node, key):

        """递归删除"""

        if node is None:

            return None

        

        if key < node.key:

            node.left = self._delete_recursive(node.left, key)

        elif key > node.key:

            node.right = self._delete_recursive(node.right, key)

        else:

            # 找到目标节点

            if node.left is None:

                return node.right

            elif node.right is None:

                return node.left

            else:

                # 有两个子节点，找到后继

                successor = self._find_min(node.right)

                node.key = successor.key

                node.right = self._delete_recursive(node.right, successor.key)

        

        return node

    

    def _find_min(self, node):

        """找到子树最小节点"""

        while node.left is not None:

            node = node.left

        return node

    

    def _copy_tree(self):

        """复制树结构（用于历史记录）"""

        return self._copy_node_recursive(self.root)

    

    def _copy_node_recursive(self, node):

        """递归复制节点"""

        if node is None:

            return None

        new_node = BSTNode(node.key)

        new_node.left = self._copy_node_recursive(node.left)

        new_node.right = self._copy_node_recursive(node.right)

        return new_node

    

    def _update_positions(self):

        """更新节点的绘图位置"""

        self.node_positions = {}

        if self.root:

            self._assign_positions(self.root, 0, 1, 0, 100)

    

    def _assign_positions(self, node, depth, index, left_bound, right_bound):

        """递归分配节点位置"""

        if node is None:

            return

        

        # x 坐标取中间位置

        x = (left_bound + right_bound) / 2

        node.x = x

        node.y = depth

        

        self.node_positions[node.key] = (x, depth)

        

        # 递归分配子节点

        if node.left:

            self._assign_positions(node.left, depth + 1, index * 2, left_bound, x)

        if node.right:

            self._assign_positions(node.right, depth + 1, index * 2 + 1, x, right_bound)





# ============== AVL 树类 ==============



class AVLTree:

    """AVL 平衡二叉搜索树类"""

    

    def __init__(self):

        self.root = None

        self.history = []       # 操作历史记录

        self.node_positions = {}

    

    def insert(self, key):

        """插入节点并维护平衡"""

        self.history.append({

            'action': 'insert',

            'key': key,

            'tree_state': self._copy_tree(),

            'rotation': None,

            'highlight': None

        })

        

        self.root = self._insert_recursive(self.root, key)

        self._update_positions()

    

    def _insert_recursive(self, node, key):

        """递归插入并维护平衡"""

        # 标准 BST 插入

        if node is None:

            return AVLNode(key)

        

        if key < node.key:

            node.left = self._insert_recursive(node.left, key)

        elif key > node.key:

            node.right = self._insert_recursive(node.right, key)

        else:

            return node  # 不允许重复值

        

        # 更新高度

        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))

        

        # 计算平衡因子

        node.balance = self._get_height(node.left) - self._get_height(node.right)

        

        # 检查平衡并旋转

        return self._rebalance(node)

    

    def _get_height(self, node):

        """获取节点高度"""

        if node is None:

            return 0

        return node.height

    

    def _rebalance(self, node):

        """重平衡操作"""

        # 左-左 情况：右旋

        if node.balance > 1 and node.left and node.left.balance >= 0:

            self.history.append({

                'action': 'rotation',

                'key': node.key,

                'rotation_type': 'right',

                'tree_state': self._copy_tree()

            })

            return self._right_rotate(node)

        

        # 右-右 情况：左旋

        if node.balance < -1 and node.right and node.right.balance <= 0:

            self.history.append({

                'action': 'rotation',

                'key': node.key,

                'rotation_type': 'left',

                'tree_state': self._copy_tree()

            })

            return self._left_rotate(node)

        

        # 左-右 情况：先左旋后右旋

        if node.balance > 1 and node.left and node.left.balance < 0:

            node.left = self._left_rotate(node.left)

            self.history.append({

                'action': 'rotation',

                'key': node.key,

                'rotation_type': 'right',

                'tree_state': self._copy_tree()

            })

            return self._right_rotate(node)

        

        # 右-左 情况：先右旋后左旋

        if node.balance < -1 and node.right and node.right.balance > 0:

            node.right = self._right_rotate(node.right)

            self.history.append({

                'action': 'rotation',

                'key': node.key,

                'rotation_type': 'left',

                'tree_state': self._copy_tree()

            })

            return self._left_rotate(node)

        

        return node

    

    def _right_rotate(self, y):

        """右旋操作"""

        x = y.left

        T2 = x.right

        

        # 执行旋转

        x.right = y

        y.left = T2

        

        # 更新高度

        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))

        

        return x

    

    def _left_rotate(self, x):

        """左旋操作"""

        y = x.right

        T2 = y.left

        

        # 执行旋转

        y.left = x

        x.right = T2

        

        # 更新高度

        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))

        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        

        return y

    

    def _update_positions(self):

        """更新节点绘图位置"""

        self.node_positions = {}

        if self.root:

            self._assign_positions(self.root, 0, 1, -50, 50)

    

    def _assign_positions(self, node, depth, index, left_bound, right_bound):

        """递归分配节点位置"""

        if node is None:

            return

        

        x = (left_bound + right_bound) / 2

        node.x = x

        node.y = depth

        self.node_positions[node.key] = (x, depth)

        

        if node.left:

            self._assign_positions(node.left, depth + 1, index * 2, left_bound, x)

        if node.right:

            self._assign_positions(node.right, depth + 1, index * 2 + 1, x, right_bound)

    

    def _copy_tree(self):

        """复制树结构"""

        return self._copy_node_recursive(self.root)

    

    def _copy_node_recursive(self, node):

        """递归复制节点"""

        if node is None:

            return None

        new_node = AVLNode(node.key)

        new_node.left = self._copy_node_recursive(node.left)

        new_node.right = self._copy_node_recursive(node.right)

        new_node.height = node.height

        new_node.balance = node.balance

        return new_node

    

    def get_edges(self):

        """获取树的边列表"""

        edges = []

        self._collect_edges(self.root, edges)

        return edges

    

    def _collect_edges(self, node, edges):

        """收集所有边"""

        if node is None:

            return

        if node.left:

            edges.append((node.key, node.left.key))

            self._collect_edges(node.left, edges)

        if node.right:

            edges.append((node.key, node.right.key))

            self._collect_edges(node.right, edges)





# ============== 可视化器类 ==============



class BSTVisualizer:

    """BST/AVL 可视化器类"""

    

    def __init__(self, tree):

        self.tree = tree

    

    def plot_static(self, title="BST 可视化", save_path=None):

        """绘制静态树图"""

        fig, ax = plt.subplots(figsize=(14, 8))

        

        # 获取边和节点

        edges = self._get_edges()

        positions = self.tree.node_positions

        

        # 绘制边

        for edge in edges:

            x1, y1 = positions[edge[0]]

            x2, y2 = positions[edge[1]]

            ax.plot([x1, x2], [y1, y2], 'b-', linewidth=1.5, alpha=0.6)

        

        # 绘制节点

        for key, (x, y) in positions.items():

            circle = plt.Circle((x, y), 2, fill=True, color='#3498db', zorder=2)

            ax.add_patch(circle)

            ax.text(x, y, str(key), ha='center', va='center', 

                   fontsize=12, fontweight='bold', color='white', zorder=3)

        

        ax.set_xlim(-60, 60)

        ax.set_ylim(-1, 12)

        ax.set_aspect('equal')

        ax.axis('off')

        ax.set_title(title, fontsize=16, fontweight='bold')

        

        plt.tight_layout()

        if save_path:

            plt.savefig(save_path, dpi=150, bbox_inches='tight')

        plt.show()

    

    def plot_animate(self, save_gif=False, gif_path='bst_animation.gif'):

        """绘制动画"""

        history = self.tree.history

        

        fig, ax = plt.subplots(figsize=(14, 8))

        ax.set_xlim(-60, 60)

        ax.set_ylim(-1, 12)

        ax.set_aspect('equal')

        ax.axis('off')

        

        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,

                           verticalalignment='top', fontsize=11,

                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        

        def init():

            return []

        

        def update(frame):

            ax.clear()

            ax.set_xlim(-60, 60)

            ax.set_ylim(-1, 12)

            ax.set_aspect('equal')

            ax.axis('off')

            

            state = history[frame]

            info_text.set_text(

                f"操作: {state['action']}\n"

                f"key: {state.get('key', 'N/A')}\n"

                f"树状态: {len(state['tree_state']) if state['tree_state'] else 0} 个节点"

            )

            

            # 绘制当前树

            self._draw_tree(ax, state['tree_state'])

            

            # 高亮显示路径

            if 'highlight' in state and state['highlight']:

                self._highlight_node(ax, state['highlight'])

            

            return []

        

        ani = animation.FuncAnimation(fig, update, frames=len(history),

                                     init_func=init, blit=False, interval=800)

        

        if save_gif:

            print("正在生成 GIF，请稍候...")

            ani.save(gif_path, writer='pillow', fps=2)

            print(f"GIF 已保存到: {gif_path}")

        

        plt.show()

        return ani

    

    def _get_edges(self):

        """获取树的所有边"""

        edges = []

        self._collect_edges(self.tree.root, edges)

        return edges

    

    def _collect_edges(self, node, edges):

        """递归收集边"""

        if node is None:

            return

        if node.left:

            edges.append((node.key, node.left.key))

            self._collect_edges(node.left, edges)

        if node.right:

            edges.append((node.key, node.right.key))

            self._collect_edges(node.right, edges)

    

    def _draw_tree(self, ax, node, positions=None):

        """递归绘制树"""

        if node is None:

            return

        

        if positions is None:

            positions = self.tree.node_positions

        

        # 绘制边

        if node.left:

            x1, y1 = positions.get(node.key, (0, 0))

            x2, y2 = positions.get(node.left.key, (0, 0))

            ax.plot([x1, x2], [y1, y2], 'b-', linewidth=1.5, alpha=0.6)

            self._draw_tree(ax, node.left, positions)

        

        if node.right:

            x1, y1 = positions.get(node.key, (0, 0))

            x2, y2 = positions.get(node.right.key, (0, 0))

            ax.plot([x1, x2], [y1, y2], 'b-', linewidth=1.5, alpha=0.6)

            self._draw_tree(ax, node.right, positions)

        

        # 绘制节点

        x, y = positions.get(node.key, (0, 0))

        circle = plt.Circle((x, y), 2, fill=True, color='#3498db', zorder=2)

        ax.add_patch(circle)

        ax.text(x, y, str(node.key), ha='center', va='center',

               fontsize=12, fontweight='bold', color='white', zorder=3)

    

    def _highlight_node(self, ax, key):

        """高亮显示指定节点"""

        if key in self.tree.node_positions:

            x, y = self.tree.node_positions[key]

            circle = plt.Circle((x, y), 2.5, fill=False, 

                               edgecolor='#e74c3c', linewidth=3, zorder=4)

            ax.add_patch(circle)





def demo_bst():

    """演示 BST 操作"""

    print("=" * 50)

    print("二叉搜索树(BST)可视化演示")

    print("=" * 50)

    

    bst = BST()

    

    # 插入操作演示

    keys = [50, 30, 70, 20, 40, 60, 80, 15, 25, 35, 45]

    print(f"\n插入序列: {keys}")

    

    for key in keys:

        bst.insert(key)

        print(f"  插入 {key} 完成")

    

    print(f"\n树结构（节点数: {len(bst.node_positions)}）")

    

    # 搜索演示

    search_keys = [40, 55, 80]

    print("\n搜索操作:")

    for key in search_keys:

        found, path = bst.search(key)

        result = "找到" if found else "未找到"

        print(f"  搜索 {key}: {result}, 路径: {path}")

    

    # 可视化

    visualizer = BSTVisualizer(bst)

    visualizer.plot_static(title="BST 完整树结构")





def demo_avl():

    """演示 AVL 树旋转"""

    print("\n" + "=" * 50)

    print("AVL 树旋转操作演示")

    print("=" * 50)

    

    avl = AVLTree()

    

    # 依次插入会导致不平衡的节点

    # 例如: 10, 20, 30 会导致 LL 失衡，需要右旋

    insert_sequence = [10, 20, 30]

    print(f"\n插入序列: {insert_sequence}")

    print("预期: 10 插入 → 20 插入后右旋 → 30 插入")

    

    for key in insert_sequence:

        avl.insert(key)

        print(f"  插入 {key}")

    

    # 演示 RR 失衡（左旋）

    avl2 = AVLTree()

    rr_sequence = [30, 20, 10]

    print(f"\n右右(RR)失衡演示: 插入 {rr_sequence}")

    

    for key in rr_sequence:

        avl2.insert(key)

    

    visualizer2 = BSTVisualizer(avl2)

    visualizer2.plot_static(title="AVL 树 RR 失衡（左旋后）")





def main():

    """主函数"""

    import argparse

    

    parser = argparse.ArgumentParser(description='BST/AVL 树可视化')

    parser.add_argument('--animate', action='store_true', help='显示动画')

    parser.add_argument('--gif', action='store_true', help='生成 GIF')

    parser.add_argument('--avl', action='store_true', help='演示 AVL 树')

    args = parser.parse_args()

    

    if args.animate or args.gif:

        if args.avl:

            avl = AVLTree()

            for key in [10, 20, 30, 50, 15, 25]:

                avl.insert(key)

            visualizer = BSTVisualizer(avl)

            visualizer.plot_animate(save_gif=args.gif)

        else:

            bst = BST()

            for key in [50, 30, 70, 20, 40]:

                bst.insert(key)

            visualizer = BSTVisualizer(bst)

            visualizer.plot_animate(save_gif=args.gif)

    elif args.avl:

        demo_avl()

    else:

        demo_bst()

        demo_avl()





if __name__ == '__main__':

    main()

