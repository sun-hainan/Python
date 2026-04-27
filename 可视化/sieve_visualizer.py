# -*- coding: utf-8 -*-
"""
算法实现：可视化 / sieve_visualizer

本文件实现 sieve_visualizer 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Rectangle

# 中文字体设置
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def sieve_of_eratosthenes(n):
    """
    埃拉托斯特尼筛法 - 生成每一步状态用于可视化
    
    参数:
        n: 筛选范围上限 [2, n]
    
    生成器:
        每一步返回当前筛选状态
    """
    # 初始化：假设所有数都是质数（True表示质数）
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False  # 0和1不是质数
    
    primes = []  # 已找到的质数列表
    eliminated = []  # 本轮被标记的合数
    
    yield {
        'step': '初始化',
        'is_prime': is_prime.copy(),
        'primes': [],
        'current_prime': None,
        'eliminated': [],
        'status': f'假设所有数 [2-{n}] 都是质数'
    }
    
    # 从2开始筛选
    for i in range(2, n + 1):
        if is_prime[i]:
            # i 是质数
            primes.append(i)
            
            yield {
                'step': f'发现新质数: {i}',
                'is_prime': is_prime.copy(),
                'primes': primes.copy(),
                'current_prime': i,
                'eliminated': [],
                'status': f'{i} 是质数！标记它的倍数'
            }
            
            # 标记 i 的倍数为合数（从 i*i 开始，因为更小的倍数已被之前标记）
            if i * i <= n:
                eliminated = []
                for j in range(i * i, n + 1, i):
                    if is_prime[j]:
                        is_prime[j] = False
                        eliminated.append(j)
                    
                    # 每标记一个数就yield一次（用于动画）
                    if j == i * i:
                        yield {
                            'step': f'从 {i}²={i*i} 开始标记',
                            'is_prime': is_prime.copy(),
                            'primes': primes.copy(),
                            'current_prime': i,
                            'eliminated': eliminated.copy(),
                            'marking': j,
                            'status': f'标记 {j} 为合数'
                        }
                    else:
                        yield {
                            'step': f'标记倍数为合数',
                            'is_prime': is_prime.copy(),
                            'primes': primes.copy(),
                            'current_prime': i,
                            'eliminated': eliminated.copy(),
                            'marking': j,
                            'status': f'标记 {j} 为合数'
                        }
    
    yield {
        'step': '筛选完成',
        'is_prime': is_prime.copy(),
        'primes': primes.copy(),
        'current_prime': None,
        'eliminated': [],
        'status': f'共找到 {len(primes)} 个质数: {primes}'
    }


def visualize_sieve(n, save_path=None):
    """
    可视化埃拉托斯特尼筛法
    
    参数:
        n: 筛选范围上限
        save_path: GIF 保存路径（可选）
    """
    # 创建图形
    fig = plt.figure(figsize=(16, 10))
    
    # 上方：数字网格
    ax_grid = plt.subplot2grid((3, 1), (0, 0), rowspan=2)
    
    # 下方：信息面板
    ax_info = plt.subplot2grid((3, 1), (2, 0))
    ax_info.axis('off')
    
    def get_color_scheme(state, idx):
        """
        根据状态确定每个数的颜色
        
        参数:
            state: 当前筛选状态
            idx: 数字索引
        
        返回:
            tuple: (facecolor, edgecolor, alpha)
        """
        is_prime = state['is_prime'][idx]
        current_prime = state.get('current_prime')
        eliminated = state.get('eliminated', [])
        marking = state.get('marking')
        
        if idx == current_prime:
            return '#FF6347', 'darkred', 1.0  # 当前质数 - 红色
        elif marking == idx:
            return '#FF4500', 'orange', 1.0  # 正在标记 - 橙红色
        elif idx in eliminated:
            return '#FFB6C1', 'lightpink', 0.7  # 刚被标记的合数 - 粉色
        elif is_prime:
            return '#90EE90', 'green', 0.9  # 质数 - 浅绿色
        else:
            return '#D3D3D3', 'gray', 0.5  # 合数 - 灰色
    
    def update(frame):
        """每帧更新"""
        ax_grid.clear()
        ax_grid.set_title(f'埃拉托斯特尼筛法 - 筛选范围: 2 到 {n}', fontsize=14, fontweight='bold')
        ax_grid.set_xlim(-0.5, min(n+1, 20) + 0.5)
        ax_grid.set_ylim(-0.5, (n // min(n, 20)) + 1)
        ax_grid.axis('off')
        
        state = frame
        
        # 绘制数字方格
        cols = min(n + 1, 20)
        rows = (n // cols) + 1
        
        for i in range(2, n + 1):
            row = (i - 2) // cols
            col = (i - 2) % cols
            
            facecolor, edgecolor, alpha = get_color_scheme(state, i)
            
            # 绘制方格
            rect = Rectangle((col - 0.4, -row - 0.4), 0.8, 0.8,
                             facecolor=facecolor, edgecolor=edgecolor,
                             linewidth=2, alpha=alpha)
            ax_grid.add_patch(rect)
            
            # 绘制数字
            fontcolor = 'black' if state['is_prime'][i] else '#666666'
            ax_grid.text(col, -row, str(i), ha='center', va='center',
                        fontsize=11, fontweight='bold', color=fontcolor)
            
            # 标记质数（在数字下方标注P）
            if state['is_prime'][i]:
                ax_grid.text(col, -row - 0.25, '✓', ha='center', va='top',
                           fontsize=8, color='green')
        
        # 更新信息面板
        ax_info.clear()
        ax_info.axis('off')
        
        info_text = f"步骤: {state['step']}\n"
        info_text += f"{state['status']}\n\n"
        info_text += f"已找到质数 ({len(state['primes'])}): {state['primes']}"
        
        ax_info.text(0.5, 0.5, info_text, ha='center', va='center',
                    fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 添加图例
        legend_elements = [
            patches.Patch(facecolor='#90EE90', edgecolor='green', label='质数'),
            patches.Patch(facecolor='#FF6347', edgecolor='darkred', label='当前质数'),
            patches.Patch(facecolor='#FFB6C1', edgecolor='lightpink', label='被标记的合数'),
            patches.Patch(facecolor='#D3D3D3', edgecolor='gray', label='已知合数'),
        ]
        ax_grid.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        return []
    
    # 生成所有帧
    frames = list(sieve_of_eratosthenes(n))
    
    # 创建动画
    anim = animation.FuncAnimation(fig, update, frames=frames,
                                   interval=600, repeat=True)
    
    if save_path:
        anim.save(save_path, writer='pillow', fps=2)
        print(f"动画已保存至: {save_path}")
    
    plt.tight_layout()
    plt.show()


def visualize_sieve_static(n):
    """
    静态可视化埃拉托斯特尼筛法的最终结果
    """
    # 计算质数
    is_prime = [True] * (n + 1)
    is_prime[0] = is_prime[1] = False
    
    primes = []
    for i in range(2, n + 1):
        if is_prime[i]:
            primes.append(i)
            if i * i <= n:
                for j in range(i * i, n + 1, i):
                    is_prime[j] = False
    
    # 创建图形
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # ===== 左图：质数分布 =====
    ax1 = axes[0]
    
    # 创建颜色数组
    colors = ['#90EE90' if is_prime[i] else '#D3D3D3' for i in range(2, n + 1)]
    
    # 绘制柱状图
    bars = ax1.bar(range(2, n + 1), [1] * (n - 1), color=colors, edgecolor='black', linewidth=0.5)
    
    # 在质数柱上标注
    for i, bar in enumerate(bars):
        if is_prime[i + 2]:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(i + 2), ha='center', va='bottom', fontsize=7, rotation=45)
    
    ax1.set_title(f'质数分布 (2-{n})', fontsize=13)
    ax1.set_xlabel('数字')
    ax1.set_ylabel('')
    ax1.set_yticks([])
    ax1.set_ylim(0, 1.5)
    
    # 添加图例
    legend_elements = [
        patches.Patch(facecolor='#90EE90', edgecolor='black', label=f'质数 ({len(primes)}个)'),
        patches.Patch(facecolor='#D3D3D3', edgecolor='black', label=f'合数 ({n-1-len(primes)}个)'),
    ]
    ax1.legend(handles=legend_elements, loc='upper right')
    
    # ===== 右图：质数数量统计 =====
    ax2 = axes[1]
    
    # 计算累计质数数量
    cumulative_primes = []
    count = 0
    for i in range(2, n + 1):
        if is_prime[i]:
            count += 1
        cumulative_primes.append(count)
    
    ax2.plot(range(2, n + 1), cumulative_primes, 'b-', linewidth=2, label='累计质数数量')
    
    # 理论曲线 n / ln(n)（素数定理）
    x = np.arange(2, n + 1)
    theoretical = x / np.log(x)
    ax2.plot(x, theoretical, 'r--', linewidth=1.5, label='素数定理: n/ln(n)')
    
    ax2.set_title('质数计数 vs 素数定理', fontsize=13)
    ax2.set_xlabel('n')
    ax2.set_ylabel('质数数量 π(n)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


def visualize_sieve_explained(n):
    """
    带详细解释的筛法可视化
    """
    fig = plt.figure(figsize=(16, 12))
    
    # 创建子图布局
    gs = fig.add_gridspec(4, 3, hspace=0.4, wspace=0.3)
    
    # ===== 主图：数字网格 =====
    ax_main = fig.add_subplot(gs[0:3, :])
    
    # ===== 信息面板 =====
    ax_info = fig.add_subplot(gs[3, :])
    ax_info.axis('off')
    
    cols = min(n + 1, 20)
    
    def update(frame_idx):
        """更新画面"""
        ax_main.clear()
        ax_info.clear()
        ax_info.axis('off')
        
        # 获取当前状态
        for idx, state in enumerate(sieve_of_eratosthenes(n)):
            if idx == frame_idx:
                current_state = state
                break
        
        # 绘制网格
        ax_main.set_xlim(-0.5, cols - 0.5)
        ax_main.set_ylim(-((n - 1) // cols + 1) - 0.5, 0.5)
        ax_main.axis('off')
        ax_main.set_title(f'埃拉托斯特尼筛法 n={n} - {current_state["step"]}',
                          fontsize=14, fontweight='bold')
        
        for i in range(2, n + 1):
            row = (i - 2) // cols
            col = (i - 2) % cols
            
            # 确定颜色
            if i == current_state.get('current_prime'):
                facecolor, edgecolor = '#FF6347', 'darkred'
            elif i == current_state.get('marking'):
                facecolor, edgecolor = '#FF4500', 'orange'
            elif i in current_state.get('eliminated', []):
                facecolor, edgecolor = '#FFB6C1', 'lightpink'
            elif current_state['is_prime'][i]:
                facecolor, edgecolor = '#90EE90', 'green'
            else:
                facecolor, edgecolor = '#D3D3D3', 'gray'
            
            rect = Rectangle((col - 0.4, -row - 0.4), 0.8, 0.8,
                            facecolor=facecolor, edgecolor=edgecolor, linewidth=1.5)
            ax_main.add_patch(rect)
            ax_main.text(col, -row, str(i), ha='center', va='center', fontsize=10)
        
        # 信息面板
        info = f"{current_state['status']}\n\n质数列表: {current_state['primes']}"
        ax_info.text(0.5, 0.5, info, ha='center', va='center', fontsize=11,
                    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        return []
    
    # 生成帧
    frames = list(sieve_of_eratosthenes(n))
    
    anim = animation.FuncAnimation(fig, update, frames=len(frames),
                                   interval=500, repeat=True)
    
    plt.show()


if __name__ == '__main__':
    # 测试参数
    test_n = 50
    
    print("=" * 60)
    print("埃拉托斯特尼筛法可视化测试")
    print("=" * 60)
    print(f"筛选范围: 2 到 {test_n}")
    
    # 计算并验证
    is_prime = [True] * (test_n + 1)
    is_prime[0] = is_prime[1] = False
    
    primes_found = []
    for i in range(2, test_n + 1):
        if is_prime[i]:
            primes_found.append(i)
            if i * i <= test_n:
                for j in range(i * i, test_n + 1, i):
                    is_prime[j] = False
    
    print(f"找到 {len(primes_found)} 个质数:")
    print(primes_found)
    
    # 启动动态可视化
    print("\n启动动态可视化...")
    visualize_sieve(test_n)
    
    # 静态可视化
    print("\n启动静态可视化...")
    visualize_sieve_static(test_n)
    
    # 带解释的版本
    print("\n启动带详细解释的版本...")
    visualize_sieve_explained(30)
    
    print("\n测试完成!")
