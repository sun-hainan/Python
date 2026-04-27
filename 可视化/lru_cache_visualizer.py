# -*- coding: utf-8 -*-
"""
算法实现：可视化 / lru_cache_visualizer

本文件实现 lru_cache_visualizer 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
from collections import OrderedDict

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class LRUCache:
    """
    LRU缓存类 - 模拟最近最少使用缓存
    
    属性:
        capacity: 缓存容量
        cache: OrderedDict 实现的有序字典
        hit_count: 命中次数
        miss_count: 未命中次数
    """
    
    def __init__(self, capacity):
        """
        初始化LRU缓存
        
        参数:
            capacity: 缓存容量（最大存储条目数）
        """
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
    
    def get(self, key):
        """
        获取缓存值（同时更新访问顺序）
        
        参数:
            key: 缓存键
        
        返回:
            (value, is_hit): 值和是否命中
        """
        if key in self.cache:
            # 命中：移动到末尾（最近使用）
            self.cache.move_to_end(key)
            self.hit_count += 1
            return self.cache[key], True
        else:
            # 未命中
            self.miss_count += 1
            return -1, False
    
    def put(self, key, value):
        """
        放入缓存
        
        参数:
            key: 缓存键
            value: 缓存值
        
        返回:
            evicted_key: 被淘汰的键（如果有）
        """
        evicted_key = None
        
        if key in self.cache:
            # 已存在：更新值并移到末尾
            self.cache.move_to_end(key)
            self.cache[key] = value
        else:
            # 新键值对
            if len(self.cache) >= self.capacity:
                # 缓存已满：淘汰最久未使用的（OrderedDict开头）
                evicted_key = next(iter(self.cache))
                del self.cache[evicted_key]
            
            self.cache[key] = value
        
        return evicted_key
    
    def get_state(self):
        """
        获取当前缓存状态
        
        返回:
            dict: 包含缓存内容的字典
        """
        return {
            'items': list(self.cache.items()),
            'capacity': self.capacity,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count
        }


def simulate_lru_operations(capacity, operations):
    """
    模拟LRU缓存操作序列，生成可视化状态
    
    参数:
        capacity: 缓存容量
        operations: 操作序列，每个元素为 ('get', key) 或 ('put', key, value)
    
    生成器:
        每一步返回缓存状态
    """
    cache = LRUCache(capacity)
    
    yield {
        'step': '初始化',
        'cache_state': cache.get_state(),
        'operation': None,
        'result': None,
        'status': f'创建容量为 {capacity} 的LRU缓存'
    }
    
    for op in operations:
        if op[0] == 'put':
            key, value = op[1], op[2]
            evicted = cache.put(key, value)
            
            if evicted:
                status = f'PUT key={key}, value={value} | 淘汰: key={evicted}'
            else:
                status = f'PUT key={key}, value={value}'
            
            yield {
                'step': 'PUT 操作',
                'cache_state': cache.get_state(),
                'operation': ('put', key, value),
                'result': evicted,
                'status': status
            }
        
        elif op[0] == 'get':
            key = op[1]
            value, is_hit = cache.get(key)
            
            status = f'GET key={key} -> {"命中!" if is_hit else "未命中"}'
            if is_hit:
                status += f' (value={value})'
            
            yield {
                'step': 'GET 操作',
                'cache_state': cache.get_state(),
                'operation': ('get', key),
                'result': (value, is_hit),
                'status': status
            }


def draw_cache_diagram(cache_state, ax, highlight_key=None, hit_marker=None, miss_marker=None):
    """
    绘制LRU缓存结构的示意图
    
    参数:
        cache_state: 缓存状态字典
        ax: matplotlib 子图
        highlight_key: 高亮显示的键
        hit_marker: 命中标记 ('HIT' 或 'MISS')
        miss_marker: 未命中标记
    """
    ax.clear()
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('LRU 缓存结构', fontsize=14, fontweight='bold')
    
    capacity = cache_state['capacity']
    items = cache_state['items']
    
    # 绘制说明文字
    ax.text(6, 9.5, f'容量: {capacity} | 命中: {cache_state["hit_count"]} | 未命中: {cache_state["miss_count"]}',
           ha='center', va='top', fontsize=11)
    
    # 绘制缓存框
    cache_box = patches.FancyBboxPatch((2, 1), 8, 7.5,
                                        boxstyle="round,pad=0.1",
                                        facecolor='#F5F5F5', edgecolor='black', linewidth=2)
    ax.add_patch(cache_box)
    
    # 绘制标题
    ax.text(6, 8.2, 'LRU Cache', ha='center', va='center', fontsize=12, fontweight='bold')
    
    # 绘制分隔线（左边：使用顺序，右边：缓存块）
    ax.plot([6, 6], [1.5, 7.5], 'k--', linewidth=1, alpha=0.5)
    ax.text(4, 8, '访问顺序\n(左→右)', ha='center', va='center', fontsize=8, color='gray')
    ax.text(8, 8, '缓存块', ha='center', va='center', fontsize=8, color='gray')
    
    # 绘制"最近使用"和"最久未使用"标签
    ax.annotate('', xy=(1.5, 7), xytext=(1.5, 2),
               arrowprops=dict(arrowstyle='<->', color='green', lw=1.5))
    ax.text(1.2, 4.5, 'LRU方向', ha='right', va='center', fontsize=8, color='green', rotation=90)
    ax.text(1.5, 7.2, '最近\n使用', ha='center', va='bottom', fontsize=7, color='green')
    ax.text(1.5, 1.8, '最久\n未用', ha='center', va='top', fontsize=7, color='red')
    
    # 绘制缓存块
    block_height = 1.0
    block_width = 2.5
    start_x = 6.25
    start_y = 6.5
    
    # 空闲块
    free_slots = capacity - len(items)
    for i in range(free_slots):
        y = start_y - i * (block_height + 0.2)
        rect = patches.FancyBboxPatch((start_x, y - block_height/2), block_width, block_height,
                                       boxstyle="round,pad=0.05",
                                       facecolor='#E8E8E8', edgecolor='gray', linewidth=1, linestyle='--')
        ax.add_patch(rect)
        ax.text(start_x + block_width/2, y, '空', ha='center', va='center', fontsize=10, color='gray')
    
    # 占用块（从最近使用到最久未用）
    for i, (key, value) in enumerate(items):
        y = start_y - (i + free_slots) * (block_height + 0.2)
        
        # 确定颜色
        if highlight_key == key:
            facecolor = '#FFD700'  # 金色高亮
            edgecolor = 'orange'
            linewidth = 3
        else:
            facecolor = '#87CEEB'  # 天蓝色
            edgecolor = 'blue'
            linewidth = 1.5
        
        rect = patches.FancyBboxPatch((start_x, y - block_height/2), block_width, block_height,
                                       boxstyle="round,pad=0.05",
                                       facecolor=facecolor, edgecolor=edgecolor, linewidth=linewidth)
        ax.add_patch(rect)
        
        # 绘制键值对
        ax.text(start_x + block_width/2, y, f'key={key}\nval={value}',
               ha='center', va='center', fontsize=9, fontweight='bold')
    
    # 绘制命中/未命中标记
    if hit_marker:
        ax.text(6, 0.5, '✓ 命中 HIT', ha='center', va='bottom',
               fontsize=16, fontweight='bold', color='green',
               bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    
    if miss_marker:
        ax.text(6, 0.5, '✗ 未命中 MISS', ha='center', va='bottom',
               fontsize=16, fontweight='bold', color='red',
               bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8))


def visualize_lru_cache(capacity, operations, save_path=None):
    """
    可视化LRU缓存操作
    
    参数:
        capacity: 缓存容量
        operations: 操作序列
        save_path: GIF保存路径（可选）
    """
    # 生成所有状态
    states = list(simulate_lru_operations(capacity, operations))
    
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 添加操作历史面板
    ax_history = plt.axes([0.1, 0.02, 0.8, 0.08])
    ax_history.axis('off')
    
    def init():
        """初始化"""
        return []
    
    def update(frame_idx):
        """每帧更新"""
        state = states[frame_idx]
        cache_state = state['cache_state']
        
        # 获取高亮键
        highlight_key = None
        hit_marker = None
        miss_marker = None
        
        if state['operation']:
            op = state['operation']
            if op[0] == 'put':
                highlight_key = op[1]
            elif op[0] == 'get':
                result = state['result']
                if result[1]:  # is_hit
                    hit_marker = True
                else:
                    miss_marker = True
        
        # 绘制缓存图
        draw_cache_diagram(cache_state, ax, highlight_key, hit_marker, miss_marker)
        
        # 更新状态信息
        ax.clear()
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 10)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title('LRU 缓存结构', fontsize=14, fontweight='bold')
        
        # 重新绘制缓存（复用上面的逻辑片段）
        draw_cache_diagram(cache_state, ax, highlight_key, hit_marker, miss_marker)
        
        # 标题区
        ax.text(6, 9.5, f'容量: {capacity} | 命中: {cache_state["hit_count"]} | 未命中: {cache_state["miss_count"]}',
               ha='center', va='top', fontsize=11)
        
        # 操作历史
        ax_history.clear()
        ax_history.axis('off')
        history_text = f"操作历史: "
        for st in states[:frame_idx+1]:
            if st['operation']:
                op = st['operation']
                if op[0] == 'put':
                    history_text += f"[PUT {op[1]}={op[2]}] "
                else:
                    history_text += f"[GET {op[1]}] "
        ax_history.text(0.5, 0.5, history_text, ha='center', va='center', fontsize=9,
                        wrap=True, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        return []
    
    # 创建动画
    anim = animation.FuncAnimation(fig, update, frames=len(states),
                                   init_func=init, interval=1000, repeat=True)
    
    if save_path:
        anim.save(save_path, writer='pillow', fps=1.5)
        print(f"动画已保存至: {save_path}")
    
    plt.tight_layout()
    plt.show()


def visualize_lru_static(capacity, operations):
    """
    静态可视化LRU缓存操作流程
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    cache = LRUCache(capacity)
    
    for idx, (ax, op) in enumerate(zip(axes, operations)):
        ax.set_xlim(0, 12)
        ax.set_ylim(0, 10)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'步骤 {idx+1}', fontsize=11)
        
        if op[0] == 'put':
            key, value = op[1], op[2]
            evicted = cache.put(key, value)
            
            # 绘制缓存状态
            items = cache.cache.items()
            for i, (k, v) in enumerate(items):
                y = 7 - i * 1.2
                color = 'gold' if k == key else '#87CEEB'
                rect = patches.FancyBboxPatch((4, y - 0.4), 4, 0.8,
                                               boxstyle="round,pad=0.05",
                                               facecolor=color, edgecolor='blue', linewidth=1.5)
                ax.add_patch(rect)
                ax.text(6, y, f'key={k}, val={v}', ha='center', va='center', fontsize=9)
            
            # 操作信息
            info = f'PUT key={key}, val={value}'
            if evicted:
                info += f'\n淘汰: key={evicted}'
            ax.text(6, 2, info, ha='center', va='center', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor='lightyellow'))
        
        elif op[0] == 'get':
            key = op[1]
            value, is_hit = cache.get(key)
            
            # 高亮命中的键
            items = cache.cache.items()
            for i, (k, v) in enumerate(items):
                y = 7 - i * 1.2
                color = '#90EE90' if k == key else '#87CEEB'
                rect = patches.FancyBboxPatch((4, y - 0.4), 4, 0.8,
                                               boxstyle="round,pad=0.05",
                                               facecolor=color, edgecolor='blue', linewidth=1.5)
                ax.add_patch(rect)
                ax.text(6, y, f'key={k}, val={v}', ha='center', va='center', fontsize=9)
            
            # 命中/未命中标记
            marker_color = 'lightgreen' if is_hit else 'lightcoral'
            marker_text = f'HIT (value={value})' if is_hit else 'MISS'
            ax.text(6, 2, f'GET key={key}\n{marker_text}', ha='center', va='center', fontsize=9,
                   bbox=dict(boxstyle='round', facecolor=marker_color))
    
    # 添加统计信息
    state = cache.get_state()
    fig.suptitle(f'LRU缓存操作演示 (容量={capacity}) | 命中: {state["hit_count"]} | 未命中: {state["miss_count"]}',
                fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # 测试参数
    cache_capacity = 3
    
    # 操作序列: [('put', key, value), ('get', key), ...]
    test_operations = [
        ('put', 1, 100),   # PUT: 添加 key=1, value=100
        ('put', 2, 200),   # PUT: 添加 key=2, value=200
        ('put', 3, 300),   # PUT: 添加 key=3, value=300
        ('get', 1),        # GET: 命中 key=1，移到末尾
        ('put', 4, 400),   # PUT: 缓存满，淘汰 key=2（最久未用）
        ('get', 2),        # GET: 未命中 key=2（已被淘汰）
        ('get', 3),        # GET: 命中 key=3
        ('put', 5, 500),   # PUT: 缓存满，淘汰 key=1
    ]
    
    print("=" * 60)
    print("LRU缓存可视化测试")
    print("=" * 60)
    print(f"缓存容量: {cache_capacity}")
    print(f"\n操作序列:")
    for idx, op in enumerate(test_operations):
        if op[0] == 'put':
            print(f"  {idx+1}. PUT  key={op[1]}, value={op[2]}")
        else:
            print(f"  {idx+1}. GET  key={op[1]}")
    
    # 启动动态可视化
    print("\n启动动态可视化...")
    visualize_lru_cache(cache_capacity, test_operations)
    
    # 静态可视化
    print("\n启动静态可视化...")
    visualize_lru_static(cache_capacity, test_operations)
    
    print("\n测试完成!")
