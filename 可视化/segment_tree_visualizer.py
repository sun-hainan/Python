# -*- coding: utf-8 -*-
"""
算法实现：可视化 / segment_tree_visualizer

本文件实现 segment_tree_visualizer 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class SegmentTree:
    """
    线段树类 - 支持区间查询和单点更新
    
    属性:
        data: 原始数据数组
        tree: 线段树数组（存储区间和）
        n: 数据长度
    """
    
    def __init__(self, data):
        """
        初始化线段树
        
        参数:
            data: 输入数组
        """
        self.data = np.array(data)
        self.n = len(data)
        # 线段树大小约为 4n（足够容纳所有节点）
        self.tree = np.zeros(4 * self.n)
        self._build(1, 0, self.n - 1)
    
    def _build(self, node, start, end):
        """
        递归构建线段树
        
        参数:
            node: 当前节点编号
            start: 当前区间起始索引
            end: 当前区间结束索引
        """
        if start == end:
            # 叶子节点：存储原始数据
            self.tree[node] = self.data[start]
        else:
            mid = (start + end) // 2
            left_child = 2 * node
            right_child = 2 * node + 1
            
            # 递归构建左右子树
            self._build(left_child, start, mid)
            self._build(right_child, mid + 1, end)
            
            # 父节点 = 左子 + 右子
            self.tree[node] = self.tree[left_child] + self.tree[right_child]
    
    def query(self, query_start, query_end):
        """
        区间查询 - 返回 [query_start, query_end] 的和
        
        参数:
            query_start: 查询区间起始
            query_end: 查询区间结束
        
        返回:
            int/float: 区间和
        """
        return self._query_helper(1, 0, self.n - 1, query_start, query_end)
    
    def _query_helper(self, node, start, end, query_start, query_end):
        """
        区间查询递归辅助函数
        
        返回:
            (sum, visited_nodes): 查询和与访问过的节点路径
        """
        if query_start <= start and end <= query_end:
            # 完全覆盖：返回当前节点值
            return self.tree[node], [(node, start, end, 'cover')]
        elif end < query_start or start > query_end:
            # 完全不相交：返回0
            return 0, [(node, start, end, 'no_overlap')]
        else:
            # 部分相交：递归查询左右子树
            mid = (start + end) // 2
            left_sum, left_nodes = self._query_helper(2 * node, start, mid, query_start, query_end)
            right_sum, right_nodes = self._query_helper(2 * node + 1, mid + 1, end, query_start, query_end)
            all_nodes = [(node, start, end, 'partial')] + left_nodes + right_nodes
            return left_sum + right_sum, all_nodes
    
    def update(self, index, value):
        """
        单点更新：将 data[index] 修改为 value
        
        参数:
            index: 要更新的索引
            value: 新的值
        """
        self._update_helper(1, 0, self.n - 1, index, value)
        self.data[index] = value
    
    def _update_helper(self, node, start, end, index, value):
        """
        单点更新递归辅助函数
        
        返回:
            visited_nodes: 更新过程中访问的节点路径
        """
        if start == end:
            # 找到目标节点
            self.tree[node] = value
            return [(node, start, end, 'found')]
        else:
            mid = (start + end) // 2
            if index <= mid:
                result = self._update_helper(2 * node, start, mid, index, value)
            else:
                result = self._update_helper(2 * node + 1, mid + 1, end, index, value)
            # 回溯时更新父节点
            self.tree[node] = self.tree[2 * node] + self.tree[2 * node + 1]
            return [(node, start, end, 'update')] + result


def draw_tree_structure(tree, n, ax, highlight_nodes=None, query_range=None):
    """
    绘制线段树的树形结构
    
    参数:
        tree: 线段树数组
        n: 数据长度
        ax: matplotlib 子图
        highlight_nodes: 要高亮的节点列表
        query_range: 查询区间元组 (start, end)
    """
    ax.clear()
    ax.set_xlim(-0.5, 2.0)
    ax.set_ylim(-0.5, 5.5)
    ax.set_aspect('equal')
    ax.axis('off')
    
    if highlight_nodes is None:
        highlight_nodes = set()
    
    def draw_node(node, x, y, start, end, dx):
        """
        递归绘制节点
        
        参数:
            node: 节点编号
            x, y: 节点坐标
            start, end: 节点代表的区间
            dx: x方向偏移（控制树的宽度）
        """
        # 确定节点颜色
        if query_range and query_range[0] <= start and end <= query_range[1]:
            color = '#90EE90'  # 浅绿色 - 完全覆盖
        elif query_range and (end < query_range[0] or start > query_range[1]):
            color = '#FFB6C1'  # 浅红色 - 不相交
        elif node in highlight_nodes:
            color = '#FFD700'  # 金色 - 访问过的节点
        else:
            color = '#87CEEB'  # 天蓝色 - 普通节点
        
        # 绘制节点方框
        rect = patches.FancyBboxPatch((x - 0.25, y - 0.2), 0.5, 0.4,
                                       boxstyle="round,pad=0.02",
                                       facecolor=color, edgecolor='black', linewidth=1.5)
        ax.add_patch(rect)
        
        # 绘制节点值和区间
        value = int(tree[node]) if tree[node] == int(tree[node]) else f'{tree[node]:.1f}'
        ax.text(x, y, f'{value}\n[{start},{end}]', ha='center', va='center', fontsize=7)
        
        # 绘制连接线
        if node * 2 < len(tree) and tree[node * 2] != 0:
            # 左子节点
            ax.plot([x, x - dx], [y - 0.2, y - 0.8], 'k-', linewidth=1)
            draw_node(node * 2, x - dx, y - 0.8, start, (start + end) // 2, dx / 2)
        
        if node * 2 + 1 < len(tree) and tree[node * 2 + 1] != 0:
            # 右子节点
            ax.plot([x, x + dx], [y - 0.2, y - 0.8], 'k-', linewidth=1)
            draw_node(node * 2 + 1, x + dx, y - 0.8, (start + end) // 2 + 1, end, dx / 2)
    
    # 根节点位置
    draw_node(1, 1.0, 5.0, 0, n - 1, 0.5)


def visualize_segment_tree(data, query_range=None, update_index=None, update_value=None):
    """
    可视化线段树的主函数
    
    参数:
        data: 原始数组
        query_range: 要查询的区间 (start, end)
        update_index: 要更新的索引
        update_value: 更新后的值
    """
    # 创建线段树
    seg_tree = SegmentTree(data)
    n = len(data)
    
    # 创建图形窗口
    fig = plt.figure(figsize=(16, 12))
    
    # 上半部分：树形结构
    ax_tree = plt.subplot2grid((3, 2), (0, 0), colspan=2, rowspan=2)
    
    # 下半部分左侧：原始数组
    ax_data = plt.subplot2grid((3, 2), (2, 0))
    
    # 下半部分右侧：操作信息
    ax_info = plt.subplot2grid((3, 2), (2, 1))
    ax_info.axis('off')
    
    frames = []
    
    # ===== 生成动画帧 =====
    
    # 第1帧：初始状态
    frames.append({
        'tree': seg_tree.tree.copy(),
        'n': n,
        'highlight': set(),
        'info': f'原始数组: {list(data)}\n线段树已构建完成',
        'data': data,
        'query': None,
        'update': None
    })
    
    # 如果有查询操作
    if query_range:
        _, visited = seg_tree._query_helper(1, 0, n - 1, query_range[0], query_range[1])
        
        # 为每个访问的节点生成帧
        for node, start, end, status in visited:
            highlight_set = {n[0] for n in visited[:visited.index((node, start, end, status))+1]}
            info = f'访问节点 {node}: 区间 [{start}, {end}]\n状态: '
            if status == 'cover':
                info += '✓ 完全覆盖，返回节点值'
            elif status == 'no_overlap':
                info += '✗ 不相交，返回0'
            else:
                info += '○ 部分相交，继续递归'
            
            frames.append({
                'tree': seg_tree.tree.copy(),
                'n': n,
                'highlight': highlight_set,
                'info': info,
                'data': data,
                'query': query_range,
                'update': None
            })
        
        # 查询结果帧
        result = seg_tree.query(query_range[0], query_range[1])
        frames.append({
            'tree': seg_tree.tree.copy(),
            'n': n,
            'highlight': set(),
            'info': f'查询区间 [{query_range[0]}, {query_range[1]}] = {result}\n（所有访问节点已标记为黄色）',
            'data': data,
            'query': query_range,
            'update': None
        })
    
    # 如果有更新操作
    if update_index is not None:
        visited = seg_tree._update_helper(1, 0, n - 1, update_index, update_value)
        
        # 记录更新前的值
        old_value = data[update_index]
        
        for node, start, end, status in visited:
            info = f'更新索引 {update_index}: {old_value} → {update_value}\n'
            info += f'访问节点 {node}: 区间 [{start}, {end}]'
            
            frames.append({
                'tree': seg_tree.tree.copy(),
                'n': n,
                'highlight': {n[0] for n in visited[:visited.index((node, start, end, status))+1]},
                'info': info,
                'data': data,
                'query': query_range,
                'update': (update_index, update_value)
            })
        
        frames.append({
            'tree': seg_tree.tree.copy(),
            'n': n,
            'highlight': set(),
            'info': f'更新完成!\ndata[{update_index}] = {update_value}\n线段树已同步更新',
            'data': data.copy(),
            'query': query_range,
            'update': (update_index, update_value)
        })
    
    def init():
        """初始化"""
        ax_tree.clear()
        ax_data.clear()
        ax_info.clear()
        return []
    
    def update(frame):
        """每帧更新"""
        # 更新树形结构
        ax_tree.clear()
        ax_tree.set_title('线段树结构', fontsize=14, fontweight='bold')
        draw_tree_structure(frame['tree'], frame['n'], ax_tree, 
                           frame['highlight'], frame.get('query'))
        
        # 更新数组视图
        ax_data.clear()
        bars = ax_data.bar(range(frame['n']), frame['data'], color='lightblue', edgecolor='black')
        
        # 高亮查询区间
        if frame.get('query'):
            for i in range(frame['query'][0], frame['query'][1] + 1):
                bars[i].set_color('#90EE90')
                bars[i].set_edgecolor('green')
        
        # 高亮更新位置
        if frame.get('update'):
            bars[frame['update'][0]].set_color('orange')
            bars[frame['update'][0]].set_edgecolor('red')
        
        ax_data.set_title(f'数组数据: {list(frame["data"])}', fontsize=11)
        ax_data.set_xlabel('索引')
        ax_data.set_ylabel('值')
        ax_data.set_xticks(range(frame['n']))
        
        # 更新信息面板
        ax_info.clear()
        ax_info.axis('off')
        ax_info.text(0.1, 0.5, frame['info'], fontsize=11, va='center',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        return []
    
    # 创建并运行动画
    anim = animation.FuncAnimation(fig, update, frames=frames, 
                                   init_func=init, interval=1200, repeat=True)
    
    plt.tight_layout()
    plt.show()


def visualize_static_tree(data):
    """
    绘制静态的线段树结构图（带完整注解）
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    seg_tree = SegmentTree(data)
    n = len(data)
    
    # ===== 左图：树形结构 =====
    ax1 = axes[0]
    ax1.set_xlim(-0.5, 2.0)
    ax1.set_ylim(-0.5, 5.5)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('线段树结构图', fontsize=14, fontweight='bold')
    
    def draw_node_static(node, x, y, start, end, dx):
        """递归绘制节点（静态版）"""
        # 节点颜色
        color = '#87CEEB'
        rect = patches.FancyBboxPatch((x - 0.25, y - 0.2), 0.5, 0.4,
                                       boxstyle="round,pad=0.02",
                                       facecolor=color, edgecolor='black', linewidth=1.5)
        ax1.add_patch(rect)
        
        value = int(seg_tree.tree[node]) if seg_tree.tree[node] == int(seg_tree.tree[node]) else f'{seg_tree.tree[node]:.1f}'
        ax1.text(x, y, f'{value}\n[{start},{end}]', ha='center', va='center', fontsize=7)
        
        if node * 2 < len(seg_tree.tree) and seg_tree.tree[node * 2] != 0:
            ax1.plot([x, x - dx], [y - 0.2, y - 0.8], 'k-', linewidth=1)
            draw_node_static(node * 2, x - dx, y - 0.8, start, (start + end) // 2, dx / 2)
        
        if node * 2 + 1 < len(seg_tree.tree) and seg_tree.tree[node * 2 + 1] != 0:
            ax1.plot([x, x + dx], [y - 0.2, y - 0.8], 'k-', linewidth=1)
            draw_node_static(node * 2 + 1, x + dx, y - 0.8, (start + end) // 2 + 1, end, dx / 2)
    
    draw_node_static(1, 1.0, 5.0, 0, n - 1, 0.5)
    
    # ===== 右图：数组对比 =====
    ax2 = axes[1]
    
    # 原始数组
    bars1 = ax2.bar(np.arange(n) - 0.2, data, 0.35, label='原始数据', color='lightblue', edgecolor='black')
    
    # 叶子节点值（对应原始数据）
    leaf_values = [seg_tree.tree[i] for i in range(1, 2*n)]
    leaf_nodes = [i for i in range(1, 2*n) if seg_tree.tree[i] != 0 and i >= n]
    ax2.bar(np.arange(len(leaf_nodes)) + 0.2, 
            [seg_tree.tree[i] for i in leaf_nodes], 0.35, 
            label='叶子节点', color='lightgreen', edgecolor='black')
    
    ax2.set_title('数组与叶子节点对比', fontsize=14)
    ax2.set_xlabel('索引')
    ax2.set_ylabel('值')
    ax2.legend()
    ax2.set_xticks(range(max(n, len(leaf_nodes))))
    
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # 测试数据
    test_data = [1, 3, 5, 7, 9, 11, 13, 15]
    
    print("=" * 60)
    print("线段树可视化测试")
    print("=" * 60)
    print(f"原始数组: {test_data}")
    print(f"数组长度: {len(test_data)}")
    
    # 构建线段树
    seg_tree = SegmentTree(test_data)
    print(f"\n线段树数组: {seg_tree.tree[:len(seg_tree.tree)//2 + 2]}")
    
    # 测试查询
    q_start, q_end = 1, 5
    result = seg_tree.query(q_start, q_end)
    print(f"\n区间查询 [{q_start}, {q_end}] = {result}")
    print(f"（验证: {sum(test_data[q_start:q_end+1])}）")
    
    # 测试更新
    idx, val = 3, 100
    seg_tree.update(idx, val)
    print(f"\n单点更新: data[{idx}] = {val}")
    print(f"更新后查询 [{q_start}, {q_end}] = {seg_tree.query(q_start, q_end)}")
    
    # 可视化
    print("\n" + "=" * 60)
    print("启动动态可视化...")
    print("=" * 60)
    
    # 重新构建树用于可视化
    test_data = [1, 3, 5, 7, 9, 11, 13, 15]
    seg_tree_viz = SegmentTree(test_data)
    
    visualize_segment_tree(
        data=test_data,
        query_range=(1, 5),  # 查询区间 [1, 5]
        update_index=3,       # 更新索引 3
        update_value=100      # 更新为 100
    )
    
    # 静态图
    print("\n启动静态结构图...")
    visualize_static_tree(test_data)
    
    print("\n测试完成!")
