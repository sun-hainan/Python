# -*- coding: utf-8 -*-
"""
算法实现：可视化 / topological_sort_visualizer

本文件实现 topological_sort_visualizer 相关的算法功能。
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拓扑排序可视化器
使用 matplotlib 动画展示有向无环图(DAG)的拓扑排序过程
支持入度变化标注

使用方法:
    python topological_sort_visualizer.py         # 静态展示
    python topological_sort_visualizer.py --animate  # 动画展示
    python topological_sort_visualizer.py --gif   # 生成 GIF
"""

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from collections import defaultdict, deque

# ============== 全局配置 ==============
# 动画帧间隔（毫秒）
FRAME_INTERVAL = 1000
# 节点颜色
NODE_COLOR_DEFAULT = '#3498db'
NODE_COLOR_PROCESSING = '#f39c12'
NODE_COLOR_DONE = '#2ecc71'
NODE_COLOR_WAITING = '#e74c3c'
# 边颜色
EDGE_COLOR_DEFAULT = '#7f8c8d'
EDGE_COLOR_HIGHLIGHT = '#e74c3c'


# ============== 图结构类 ==============

class DAG:
    """有向无环图类"""
    
    def __init__(self):
        self.graph = defaultdict(list)   # 邻接表
        self.in_degree = defaultdict(int)  # 入度
        self.nodes = set()                # 所有节点
        self.edges = []                   # 边列表
    
    def add_node(self, node):
        """添加节点"""
        self.nodes.add(node)
    
    def add_edge(self, from_node, to_node):
        """添加有向边 from -> to"""
        self.graph[from_node].append(to_node)
        self.edges.append((from_node, to_node))
        self.in_degree[to_node] += 1
        self.nodes.add(from_node)
        self.nodes.add(to_node)
    
    def get_in_degree(self, node):
        """获取节点入度"""
        return self.in_degree.get(node, 0)
    
    def get_out_edges(self, node):
        """获取节点的出边"""
        return [(node, neighbor) for neighbor in self.graph[node]]
    
    def topological_sort(self):
        """
        执行拓扑排序（Kahn算法）
        返回: 排序结果列表，每步状态记录
        """
        history = []
        result = []
        current_in_degree = self.in_degree.copy()
        temp_in_degree = current_in_degree.copy()
        
        # 记录初始状态
        history.append({
            'step': 0,
            'action': 'init',
            'queue': [],
            'result': [],
            'in_degree': temp_in_degree.copy(),
            'message': '初始化入度表，准备拓扑排序'
        })
        
        # 将入度为0的节点加入队列
        zero_degree_nodes = sorted([n for n in self.nodes if temp_in_degree[n] == 0])
        queue = deque(zero_degree_nodes)
        
        history.append({
            'step': 1,
            'action': 'enqueue',
            'queue': list(queue),
            'result': [],
            'in_degree': temp_in_degree.copy(),
            'message': f'入度为0的节点入队: {list(queue)}'
        })
        
        step = 2
        while queue:
            # 取出队首节点
            node = queue.popleft()
            result.append(node)
            
            history.append({
                'step': step,
                'action': 'dequeue',
                'node': node,
                'queue': list(queue),
                'result': result.copy(),
                'in_degree': temp_in_degree.copy(),
                'message': f'取出节点 {node}，加入结果序列'
            })
            step += 1
            
            # 更新相邻节点的入度
            for neighbor in self.graph[node]:
                temp_in_degree[neighbor] -= 1
                
                history.append({
                    'step': step,
                    'action': 'update_degree',
                    'node': node,
                    'neighbor': neighbor,
                    'queue': list(queue),
                    'result': result.copy(),
                    'in_degree': temp_in_degree.copy(),
                    'message': f'节点 {node} 处理完毕，邻居 {neighbor} 入度减1变为 {temp_in_degree[neighbor]}'
                })
                step += 1
                
                # 如果入度变为0，加入队列
                if temp_in_degree[neighbor] == 0:
                    queue.append(neighbor)
                    
                    history.append({
                        'step': step,
                        'action': 'enqueue',
                        'neighbor': neighbor,
                        'queue': list(queue),
                        'result': result.copy(),
                        'in_degree': temp_in_degree.copy(),
                        'message': f'节点 {neighbor} 入度变为0，加入队列'
                    })
                    step += 1
        
        # 检查是否有环
        if len(result) != len(self.nodes):
            history.append({
                'step': step,
                'action': 'cycle',
                'result': result,
                'message': '检测到环，无法完成拓扑排序'
            })
        
        return result, history


# ============== 可视化器类 ==============

class TopoSortVisualizer:
    """拓扑排序可视化器类"""
    
    def __init__(self, dag):
        self.dag = dag
        self.history = []
        self.result = []
        self.node_positions = {}
        self._layout_nodes()
    
    def _layout_nodes(self):
        """为节点分配布局位置"""
        # 使用分层布局
        # 找出入度为0的节点作为第一层
        nodes = list(self.dag.nodes)
        n = len(nodes)
        
        # 按拓扑排序层级布局
        # 这里使用简单的圆形布局
        angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
        for i, node in enumerate(sorted(nodes)):
            x = 5 * np.cos(angles[i])
            y = 5 * np.sin(angles[i])
            self.node_positions[node] = (x, y)
    
    def plot_static(self, topo_order=None, save_path=None):
        """绘制静态图"""
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 绘制边
        for edge in self.dag.edges:
            x1, y1 = self.node_positions[edge[0]]
            x2, y2 = self.node_positions[edge[1]]
            
            # 计算箭头终点（指向节点边缘）
            dx = x2 - x1
            dy = y2 - y1
            dist = np.sqrt(dx**2 + dy**2)
            # 箭头缩短到节点边缘
            shrink = 1.0
            ax.annotate('', xy=(x2 - dx/dist*shrink, y2 - dy/dist*shrink),
                       xytext=(x1 + dx/dist*0.5, y1 + dy/dist*0.5),
                       arrowprops=dict(arrowstyle='->', color=EDGE_COLOR_DEFAULT,
                                     lw=2, connectionstyle='arc3,rad=0'))
        
        # 绘制节点
        for node in self.dag.nodes:
            x, y = self.node_positions[node]
            
            # 根据拓扑排序结果设置颜色
            if topo_order and node in topo_order:
                idx = topo_order.index(node)
                color = plt.cm.viridis(idx / max(len(topo_order) - 1, 1))
            else:
                color = NODE_COLOR_DEFAULT
            
            circle = plt.Circle((x, y), 1.2, fill=True, 
                              facecolor=color, edgecolor='black', linewidth=2)
            ax.add_patch(circle)
            ax.text(x, y, str(node), ha='center', va='center',
                   fontsize=14, fontweight='bold', color='white')
            
            # 显示入度
            in_deg = self.dag.get_in_degree(node)
            ax.text(x, y - 1.8, f'in={in_deg}', ha='center', va='top',
                   fontsize=10, color='gray')
        
        # 添加图例
        if topo_order:
            ax.text(0.02, 0.98, f'拓扑排序结果:\n{" → ".join(str(n) for n in topo_order)}',
                   transform=ax.transAxes, fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        ax.set_xlim(-8, 8)
        ax.set_ylim(-8, 8)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('有向无环图 (DAG) 与拓扑排序', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"图片已保存到: {save_path}")
        plt.show()
    
    def plot_animate(self, history, save_gif=False, gif_path='toposort_animation.gif'):
        """绘制拓扑排序动画"""
        fig, ax = plt.subplots(figsize=(12, 10))
        
        info_text = ax.text(0.02, 0.98, '', transform=ax.transAxes,
                           verticalalignment='top', fontsize=11,
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        def init():
            return []
        
        def update(frame):
            ax.clear()
            state = history[frame]
            
            # 更新信息文本
            info_text.set_text(
                f"步骤 {state['step']}: {state['action']}\n"
                f"{state['message']}\n"
                f"队列: {state['queue']}\n"
                f"结果: {state['result']}"
            )
            
            # 绘制边
            for edge in self.dag.edges:
                x1, y1 = self.node_positions[edge[0]]
                x2, y2 = self.node_positions[edge[1]]
                
                # 如果是当前处理的节点相关的边，高亮
                highlight = False
                if state['action'] in ['dequeue', 'update_degree']:
                    if edge[0] == state.get('node') or edge[1] == state.get('neighbor'):
                        highlight = True
                
                color = EDGE_COLOR_HIGHLIGHT if highlight else EDGE_COLOR_DEFAULT
                
                dx = x2 - x1
                dy = y2 - y1
                dist = np.sqrt(dx**2 + dy**2) if dist > 0 else 1
                ax.annotate('', xy=(x2 - dx/dist*1.2, y2 - dy/dist*1.2),
                           xytext=(x1 + dx/dist*0.5, y1 + dy/dist*0.5),
                           arrowprops=dict(arrowstyle='->', color=color,
                                         lw=2 if highlight else 1.5))
            
            # 绘制节点
            for node in self.dag.nodes:
                x, y = self.node_positions[node]
                
                # 根据状态设置节点颜色
                if node in state['result']:
                    color = NODE_COLOR_DONE
                elif node in state['queue']:
                    color = NODE_COLOR_PROCESSING
                elif state['action'] == 'enqueue' and node == state.get('neighbor'):
                    color = NODE_COLOR_PROCESSING
                elif state['action'] == 'cycle':
                    color = NODE_COLOR_WAITING
                else:
                    color = NODE_COLOR_DEFAULT
                
                circle = plt.Circle((x, y), 1.2, fill=True,
                                   facecolor=color, edgecolor='black', linewidth=2)
                ax.add_patch(circle)
                ax.text(x, y, str(node), ha='center', va='center',
                       fontsize=14, fontweight='bold', color='white')
                
                # 显示入度
                in_deg = state['in_degree'].get(node, self.dag.get_in_degree(node))
                color_in = 'red' if in_deg > 0 else 'green'
                ax.text(x, y - 1.8, f'in={in_deg}', ha='center', va='top',
                       fontsize=10, color=color_in)
            
            ax.set_xlim(-8, 8)
            ax.set_ylim(-8, 8)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title('拓扑排序过程', fontsize=16, fontweight='bold')
            
            return []
        
        ani = animation.FuncAnimation(fig, update, frames=len(history),
                                     init_func=init, blit=False, interval=FRAME_INTERVAL)
        
        if save_gif:
            print("正在生成 GIF，请稍候...")
            ani.save(gif_path, writer='pillow', fps=2)
            print(f"GIF 已保存到: {gif_path}")
        
        plt.show()
        return ani


def create_sample_dag():
    """创建示例 DAG"""
    dag = DAG()
    
    # 添加边：表示课程依赖关系
    # 例如：课程 A 是课程 B 的先修课，则添加边 A -> B
    edges = [
        ('A', 'C'),  # A 是 C 的先修
        ('B', 'C'),  # B 是 C 的先修
        ('B', 'D'),  # B 是 D 的先修
        ('C', 'E'),  # C 是 E 的先修
        ('D', 'E'),  # D 是 E 的先修
        ('E', 'F'),  # E 是 F 的先修
    ]
    
    for from_node, to_node in edges:
        dag.add_edge(from_node, to_node)
    
    return dag


def create_dag2():
    """创建另一个示例 DAG（更复杂的依赖图）"""
    dag = DAG()
    
    edges = [
        (0, 1), (0, 2), (0, 3),
        (1, 4), (2, 4), (2, 5),
        (3, 5), (4, 6), (5, 6), (5, 7),
        (6, 8), (7, 8)
    ]
    
    for from_node, to_node in edges:
        dag.add_edge(from_node, to_node)
    
    return dag


def demo_basic():
    """基础演示"""
    print("=" * 50)
    print("拓扑排序可视化 - 基础示例")
    print("=" * 50)
    
    dag = create_sample_dag()
    
    print(f"节点: {sorted(dag.nodes)}")
    print(f"边: {dag.edges}")
    print("\n各节点入度:")
    for node in sorted(dag.nodes):
        print(f"  {node}: {dag.get_in_degree(node)}")
    
    # 执行拓扑排序
    topo_order, history = dag.topological_sort()
    
    print(f"\n拓扑排序结果: {' → '.join(topo_order)}")
    print(f"排序步骤数: {len(history)}")
    
    # 可视化
    visualizer = TopoSortVisualizer(dag)
    visualizer.plot_static(topo_order)


def demo_animate():
    """动画演示"""
    print("=" * 50)
    print("拓扑排序可视化 - 动画演示")
    print("=" * 50)
    
    dag = create_sample_dag()
    topo_order, history = dag.topological_sort()
    
    visualizer = TopoSortVisualizer(dag)
    visualizer.plot_animate(history)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='拓扑排序可视化')
    parser.add_argument('--animate', action='store_true', help='显示动画')
    parser.add_argument('--gif', action='store_true', help='生成 GIF')
    parser.add_argument('--dag', type=int, default=1, choices=[1, 2],
                       help='选择 DAG 示例 (1 或 2)')
    args = parser.parse_args()
    
    if args.gif:
        if args.dag == 1:
            dag = create_sample_dag()
        else:
            dag = create_dag2()
        
        topo_order, history = dag.topological_sort()
        visualizer = TopoSortVisualizer(dag)
        
        if args.dag == 1:
            gif_path = 'toposort_animation.gif'
        else:
            gif_path = 'toposort_dag2_animation.gif'
        
        visualizer.plot_animate(history, save_gif=True, gif_path=gif_path)
    
    elif args.animate:
        demo_animate()
    
    else:
        # 静态展示
        demo_basic()


if __name__ == '__main__':
    main()
