#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二叉树可视化
使用 matplotlib 动画展示：二叉树绘制和三种遍历过程（中序/前序/后序�?
使用方法：python visualization/tree_visualizer.py
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Arrow
import numpy as np

# ============== 二叉树节�?==============

class TreeNode:
    """二叉树节�?""

    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


# ============== 常量配置 ==============
NODE_RADIUS = 0.25
COLORS = {
    'node_default': '#3498db',
    'node_visited': '#2ecc71',
    'node_current': '#e74c3c',
    'node_in_path': '#f39c12',
    'edge_default': '#7f8c8d',
    'edge_visited': '#2ecc71',
    'text': 'white',
}


# ============== 二叉树可视化�?==============

class BinaryTreeVisualizer:
    """二叉树可视化�?""

    def __init__(self, root):
        self.root = root
        self.positions = {}  # node -> (x, y)
        self.history = []
        self._compute_positions()

    def _compute_positions(self):
        """计算每个节点的位置（分层布局�?""
        if self.root is None:
            return

        def assign(node, depth, left_bound, right_bound):
            if node is None:
                return

            x = (left_bound + right_bound) / 2
            y = -depth
            self.positions[node] = (x, y)

            # 递归分配左右子节�?            if node.left or node.right:
                mid = (left_bound + right_bound) / 2
                if node.left:
                    assign(node.left, depth + 1, left_bound, mid)
                if node.right:
                    assign(node.right, depth + 1, mid, right_bound)

        assign(self.root, 0, 0, 1)

    def draw_state(self, ax, title='', visited=None, current=None, path=None,
                   edge_state=None, message=''):
        """绘制当前状�?""
        ax.clear()
        ax.set_xlim(-0.1, 1.1)
        ax.set_ylim(-self._get_depth() - 0.5, 1)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(title, fontsize=14, fontweight='bold', pad=10)

        if visited is None:
            visited = set()
        if path is None:
            path = []
        if edge_state is None:
            edge_state = {}

        # 绘制�?        def draw_edges(node):
            if node is None:
                return

            x, y = self.positions[node]
            edge_key = id(node)

            if node.left:
                lx, ly = self.positions[node.left]
                edge_id = (id(node), id(node.left))
                color = COLORS['edge_visited'] if edge_id in edge_state else COLORS['edge_default']
                ax.annotate('', xy=(lx, ly), xytext=(x, y),
                           arrowprops=dict(arrowstyle='-', color=color, lw=2))
                draw_edges(node.left)

            if node.right:
                rx, ry = self.positions[node.right]
                edge_id = (id(node), id(node.right))
                color = COLORS['edge_visited'] if edge_id in edge_state else COLORS['edge_default']
                ax.annotate('', xy=(rx, ry), xytext=(x, y),
                           arrowprops=dict(arrowstyle='-', color=color, lw=2))
                draw_edges(node.right)

        draw_edges(self.root)

        # 绘制节点
        for node, (x, y) in self.positions.items():
            if node == current:
                color = COLORS['node_current']
            elif id(node) in path:
                color = COLORS['node_in_path']
            elif node in visited:
                color = COLORS['node_visited']
            else:
                color = COLORS['node_default']

            ax.add_patch(Circle((x, y), NODE_RADIUS, facecolor=color,
                                edgecolor='white', linewidth=2, zorder=2))
            ax.text(x, y, str(node.val), ha='center', va='center',
                   fontsize=11, fontweight='bold', color=COLORS['text'], zorder=3)

        if message:
            ax.text(0.5, -self._get_depth() - 0.3, message,
                   ha='center', va='top', fontsize=11, style='italic', color='#333')

    def _get_depth(self):
        """获取树的深度"""
        def depth(node):
            if node is None:
                return 0
            return 1 + max(depth(node.left), depth(node.right))
        return depth(self.root)


# ============== 遍历可视�?==============

def visualize_inorder(root):
    """中序遍历 (�?�?�? 可视�?""
    viz = BinaryTreeVisualizer(root)
    result = []
    visited = set()
    edge_state = {}

    def inorder(node):
        if node is None:
            return

        inorder(node.left)

        edge_state[(id(node), id(node.left))] = True if node.left else None
        edge_state[(id(node), id(node.right))] = True if node.right else None
        visited.add(node)
        result.append({
            'visited': set(visited),
            'current': node,
            'path': list(result),
            'edge_state': dict(edge_state),
            'message': f'访问节点 {node.val} (左子树→根→右子�?'
        })

        inorder(node.right)

    inorder(root)

    # 最终路�?    result.append({
        'visited': set(visited),
        'current': None,
        'path': list(result),
        'edge_state': dict(edge_state),
        'message': f'中序遍历完成: {" �?".join(str(n.val) for n in visited)}'
    })

    return result


def visualize_preorder(root):
    """前序遍历 (�?�?�? 可视�?""
    viz = BinaryTreeVisualizer(root)
    result = []
    visited = set()
    edge_state = {}

    def preorder(node):
        if node is None:
            return

        edge_state[(id(node), id(node.left))] = True if node.left else None
        edge_state[(id(node), id(node.right))] = True if node.right else None
        visited.add(node)
        result.append({
            'visited': set(visited),
            'current': node,
            'path': list(result),
            'edge_state': dict(edge_state),
            'message': f'访问节点 {node.val} (根→左→�?'
        })

        preorder(node.left)
        preorder(node.right)

    preorder(root)

    result.append({
        'visited': set(visited),
        'current': None,
        'path': list(result),
        'edge_state': dict(edge_state),
        'message': f'前序遍历完成: {" �?".join(str(n.val) for n in visited)}'
    })

    return result


def visualize_postorder(root):
    """后序遍历 (�?�?�? 可视�?""
    viz = BinaryTreeVisualizer(root)
    result = []
    visited = set()
    edge_state = {}

    def postorder(node):
        if node is None:
            return

        postorder(node.left)
        postorder(node.right)

        edge_state[(id(node), id(node.left))] = True if node.left else None
        edge_state[(id(node), id(node.right))] = True if node.right else None
        visited.add(node)
        result.append({
            'visited': set(visited),
            'current': node,
            'path': list(result),
            'edge_state': dict(edge_state),
            'message': f'访问节点 {node.val} (左→右→�?'
        })

    postorder(root)

    result.append({
        'visited': set(visited),
        'current': None,
        'path': list(result),
        'edge_state': dict(edge_state),
        'message': f'后序遍历完成: {" �?".join(str(n.val) for n in visited)}'
    })

    return result


def visualize_level_order(root):
    """层序遍历（使用队列）可视�?""
    viz = BinaryTreeVisualizer(root)
    result = []
    visited = set()
    queue = [root] if root else []
    step = 0

    result.append({
        'visited': set(visited),
        'queue': list(queue),
        'current': None,
        'message': f'初始化队�? {[n.val for n in queue]}'
    })

    while queue:
        node = queue.pop(0)
        step += 1

        visited.add(node)
        result.append({
            'visited': set(visited),
            'queue': list(queue),
            'current': node,
            'message': f'出队: {node.val}'
        })

        # 先加左子节点
        if node.left:
            queue.append(node.left)
            result.append({
                'visited': set(visited),
                'queue': list(queue),
                'current': node.left,
                'message': f'左子节点 {node.left.val} 入队'
            })

        # 再加右子节点
        if node.right:
            queue.append(node.right)
            result.append({
                'visited': set(visited),
                'queue': list(queue),
                'current': node.right,
                'message': f'右子节点 {node.right.val} 入队'
            })

    result.append({
        'visited': set(visited),
        'queue': [],
        'current': None,
        'message': f'层序遍历完成: {" �?".join(str(n.val) for n in visited)}'
    })

    return result


# ============== 动画创建函数 ==============

def create_tree_animation(viz, history, title, filename):
    """创建二叉树遍历动�?""
    fig, ax = plt.subplots(figsize=(10, 7))

    def update(frame):
        state = history[frame]
        viz.draw_state(ax, f'{title} (步骤 {frame+1}/{len(history)})',
                      visited=state.get('visited'),
                      current=state.get('current'),
                      path=[s['current'] for s in state.get('path', []) if s.get('current')],
                      edge_state=state.get('edge_state', {}),
                      message=state.get('message', ''))

    ani = animation.FuncAnimation(fig, update, frames=len(history),
                                  interval=800, repeat=False)
    ani.save(filename, writer='pillow', fps=1.25)
    plt.close()
    print(f'  已保�? {filename}')


# ============== 主函�?==============

def build_sample_tree():
    """构建示例二叉�?""
    #       1
    #      / \
    #     2   3
    #    / \   \
    #   4   5   6
    #  /       /
    # 7       8

    n7 = TreeNode(7)
    n4 = TreeNode(4, left=n7)
    n5 = TreeNode(5)
    n8 = TreeNode(8)
    n6 = TreeNode(6, left=n8)
    n2 = TreeNode(2, left=n4, right=n5)
    n3 = TreeNode(3, right=n6)
    root = TreeNode(1, left=n2, right=n3)
    return root


def main():
    print('=' * 50)
    print('二叉树可视化演示')
    print('=' * 50)
    print()

    output_dir = 'D:/openclaw-home/.openclaw/workspace/计算机算�?可视�?'

    root = build_sample_tree()

    # 初始化可视化器（用于获取树结构）
    init_viz = BinaryTreeVisualizer(root)

    # ---- 中序遍历 ----
    print('[1/4] 中序遍历动画生成�?..')
    inorder_history = visualize_inorder(root)
    create_tree_animation(init_viz, inorder_history, '中序遍历 (Inorder: 左→根→�?',
                         output_dir + 'inorder_traversal.gif')

    # ---- 前序遍历 ----
    print('[2/4] 前序遍历动画生成�?..')
    preorder_history = visualize_preorder(root)
    create_tree_animation(init_viz, preorder_history, '前序遍历 (Preorder: 根→左→�?',
                         output_dir + 'preorder_traversal.gif')

    # ---- 后序遍历 ----
    print('[3/4] 后序遍历动画生成�?..')
    postorder_history = visualize_postorder(root)
    create_tree_animation(init_viz, postorder_history, '后序遍历 (Postorder: 左→右→�?',
                         output_dir + 'postorder_traversal.gif')

    # ---- 层序遍历 ----
    print('[4/4] 层序遍历动画生成�?..')
    level_order_history = visualize_level_order(root)
    create_tree_animation(init_viz, level_order_history, '层序遍历 (Level Order: 按层)',
                         output_dir + 'level_order_traversal.gif')

    print()
    print('=' * 50)
    print('所有二叉树遍历动画已生成完毕！')
    print('GIF文件位于: 可视�? 目录�?)
    print('=' * 50)


if __name__ == '__main__':
    main()

