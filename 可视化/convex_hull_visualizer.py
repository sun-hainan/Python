# -*- coding: utf-8 -*-
"""
算法实现：可视化 / convex_hull_visualizer

本文件实现 convex_hull_visualizer 相关的算法功能。
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.patches import Polygon
from collections import deque

# 设置中文字体（跨平台兼容）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def cross_product(o, a, b):
    """
    计算向量 OA × OB 的叉积（用于判断转向方向）
    
    参数:
        o: 原点坐标 (x, y)
        a: 向量终点A (x, y)
        b: 向量终点B (x, y)
    
    返回:
        float: 叉积结果
            > 0 表示左转（逆时针）
            < 0 表示右转（顺时针）
            = 0 表示共线
    """
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def polar_angle(point, origin):
    """
    计算点相对于原点的极角（用于排序）
    
    参数:
        point: 目标点坐标 (x, y)
        origin: 原点坐标 (x, y)
    
    返回:
        float: 极角（弧度），范围 [0, 2π)
    """
    return np.arctan2(point[1] - origin[1], point[0] - origin[0])


def graham_scan(points):
    """
    Graham Scan 算法核心实现（生成每一步状态用于可视化）
    
    参数:
        points: 平面点集列表，每个元素为 (x, y) 元组
    
    生成器:
        每一步返回当前可视化的完整状态字典
    """
    # 步骤1：找到 y 坐标最小的点作为起始点（若有多个，选择x最小的）
    points = np.array(points)
    min_idx = np.argmin(points[:, 1] * 1000 + points[:, 0])  # 先比较y，再比较x
    base_point = points[min_idx]
    
    yield {
        'step': '找到基准点',
        'base_point': tuple(base_point),
        'points': points,
        'hull': [],
        'sorted_indices': [],
        'current_idx': min_idx,
        'status': '基准点已标记为红色'
    }
    
    # 步骤2：计算所有点的极角并排序（排除基准点自身）
    other_points = np.delete(points, min_idx, axis=0)
    angles = np.array([polar_angle(p, base_point) for p in other_points])
    sorted_indices = np.argsort(angles)
    sorted_points = other_points[sorted_indices]
    
    # 处理共线点：保留距离最远的点
    final_points = [base_point]
    i = 0
    while i < len(sorted_points):
        # 收集相同极角的所有点
        same_angle_points = [sorted_points[i]]
        j = i + 1
        while j < len(sorted_points) and np.isclose(angles[sorted_indices[j]], angles[sorted_indices[i]]):
            same_angle_points.append(sorted_points[j])
            j += 1
        
        # 按距离排序，保留最远的点
        distances = [np.linalg.norm(p - base_point) for p in same_angle_points]
        farthest_idx = np.argmax(distances)
        final_points.append(same_angle_points[farthest_idx])
        
        # 更新已排序列表（保留用于可视化）
        for k, sp in enumerate(same_angle_points):
            yield {
                'step': f'极角排序 (角度={angles[sorted_indices[i+k]]:.2f}°)',
                'base_point': tuple(base_point),
                'points': points,
                'hull': list(final_points[:-1]),
                'sorted_indices': list(sorted_indices[:i+k+1]),
                'current_idx': min_idx,
                'status': f'处理共线点，保留距离最远点'
            }
        
        i = j
    
    # 最终排序后的点（不含基准点）
    all_sorted = np.array(final_points[1:])
    angles_final = np.array([polar_angle(p, base_point) for p in all_sorted])
    sorted_order = np.argsort(angles_final)
    sorted_points = all_sorted[sorted_order]
    
    yield {
        'step': '极角排序完成',
        'base_point': tuple(base_point),
        'points': points,
        'hull': [base_point],
        'sorted_indices': list(sorted_order),
        'current_idx': min_idx,
        'status': f'共 {len(sorted_points)} 个点待处理'
    }
    
    # 步骤3：Graham 扫描构建凸包
    hull = deque([tuple(base_point), tuple(sorted_points[0])])
    
    yield {
        'step': '开始扫描',
        'base_point': tuple(base_point),
        'points': points,
        'hull': list(hull),
        'sorted_indices': list(sorted_order),
        'current_idx': min_idx,
        'processing_idx': 0,
        'status': '初始化凸包队列'
    }
    
    i = 1
    while i < len(sorted_points):
        current_point = tuple(sorted_points[i])
        
        # 弹出不构成左转的点
        while len(hull) > 1:
            p1 = hull[-2]
            p2 = hull[-1]
            cp = cross_product(p1, p2, current_point)
            
            if cp <= 0:  # 右转或共线，弹出最后一个点
                removed_point = hull.pop()
                yield {
                    'step': '弹出不满足条件的点',
                    'base_point': tuple(base_point),
                    'points': points,
                    'hull': list(hull),
                    'sorted_indices': list(sorted_order),
                    'current_idx': min_idx,
                    'processing_idx': i,
                    'removed_point': removed_point,
                    'status': f'弹出点 {removed_point}（右转或共线）'
                }
            else:
                break
        
        # 加入新点
        hull.append(current_point)
        yield {
            'step': '加入新点到凸包',
            'base_point': tuple(base_point),
            'points': points,
            'hull': list(hull),
            'sorted_indices': list(sorted_order),
            'current_idx': min_idx,
            'processing_idx': i,
            'new_point': current_point,
            'status': f'加入点 {current_point} 到凸包'
        }
        
        i += 1
    
    # 完成
    yield {
        'step': '凸包构建完成',
        'base_point': tuple(base_point),
        'points': points,
        'hull': list(hull),
        'sorted_indices': list(sorted_order),
        'current_idx': min_idx,
        'status': f'凸包包含 {len(hull)} 个顶点'
    }


def visualize_graham_scan(points, save_path=None):
    """
    可视化 Graham Scan 算法的主函数
    
    参数:
        points: 平面点集
        save_path: GIF 保存路径（可选）
    """
    # 创建图形
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 初始化绘图数据
    all_points = np.array(points)
    
    def init():
        """初始化画布"""
        ax.clear()
        ax.set_xlim(all_points[:, 0].min() - 2, all_points[:, 0].max() + 2)
        ax.set_ylim(all_points[:, 1].min() - 2, all_points[:, 1].max() + 2)
        ax.set_title('Graham Scan 凸包算法 - 初始化', fontsize=16)
        ax.set_xlabel('X 坐标', fontsize=12)
        ax.set_ylabel('Y 坐标', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
    
    def update(frame):
        """每帧更新画面"""
        ax.clear()
        
        # 设置坐标范围
        ax.set_xlim(all_points[:, 0].min() - 2, all_points[:, 0].max() + 2)
        ax.set_ylim(all_points[:, 1].min() - 2, all_points[:, 1].max() + 2)
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal')
        
        state = frame
        current_points = state['points']
        base_point = state['base_point']
        hull = state['hull']
        status = state['status']
        
        # 绘制所有原始点（灰色小点）
        ax.scatter(current_points[:, 0], current_points[:, 1], 
                   c='gray', s=30, alpha=0.5, label='输入点集')
        
        # 绘制基准点（红色大点）
        ax.scatter(base_point[0], base_point[1], 
                   c='red', s=200, marker='*', zorder=5, label=f'基准点 {base_point}')
        
        # 绘制已处理的排序后的点（按顺序编号）
        if state['sorted_indices']:
            sorted_pts = [tuple(current_points[i]) for i in range(len(current_points)) 
                         if i != list(current_points).index(base_point)]
            for idx, pt in enumerate(sorted_pts[:len(state['sorted_indices'])]):
                ax.annotate(f'{idx+1}', pt, fontsize=8, ha='center', va='bottom', color='blue')
            # 绘制待处理点（蓝色）
            for i, pt in enumerate(current_points):
                if tuple(pt) != base_point and i < len(state['sorted_indices']) + (list(current_points).index(base_point) == -1):
                    pass
        
        # 绘制当前凸包（绿色连线）
        if len(hull) >= 2:
            hull_array = np.array(hull + [hull[0]])  # 闭合多边形
            ax.plot(hull_array[:, 0], hull_array[:, 1], 
                    'g-', linewidth=2, label='当前凸包')
        
        # 绘制凸包顶点（绿色大点）
        for pt in hull:
            ax.scatter(pt[0], pt[1], c='green', s=100, zorder=4)
        
        # 高亮标记被移除的点
        if 'removed_point' in state:
            ax.scatter(state['removed_point'][0], state['removed_point'][1],
                      c='orange', s=150, marker='x', linewidths=3,
                      label=f'移除: {state["removed_point"]}')
        
        # 高亮标记新加入的点
        if 'new_point' in state:
            ax.scatter(state['new_point'][0], state['new_point'][1],
                      c='lime', s=200, marker='^', linewidths=2,
                      edgecolors='black', label=f'新加入: {state["new_point"]}')
        
        # 标题和信息
        ax.set_title(f"Graham Scan - {state['step']}", fontsize=14)
        ax.set_xlabel(f"状态: {status}", fontsize=11)
        ax.legend(loc='upper left', fontsize=9)
        
        return []
    
    # 生成所有帧
    frames = list(graham_scan(points))
    
    # 创建动画
    anim = animation.FuncAnimation(fig, update, frames=frames, 
                                   interval=800, repeat=True)
    
    if save_path:
        anim.save(save_path, writer='pillow', fps=1.5)
        print(f"动画已保存至: {save_path}")
    
    plt.tight_layout()
    plt.show()


def visualize_static(points):
    """
    静态图：展示 Graham Scan 的最终结果
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    all_points = np.array(points)
    
    # ===== 左图：输入点集 =====
    ax1 = axes[0]
    ax1.scatter(all_points[:, 0], all_points[:, 1], 
                c='gray', s=60, alpha=0.7, label='输入点集')
    
    # 标记基准点
    min_idx = np.argmin(all_points[:, 1] * 1000 + all_points[:, 0])
    base_point = all_points[min_idx]
    ax1.scatter(base_point[0], base_point[1], 
                c='red', s=200, marker='*', zorder=5, label=f'基准点 (y最小)')
    
    # 绘制极角射线（从基准点出发）
    for pt in all_points:
        if not np.array_equal(pt, base_point):
            ax1.plot([base_point[0], pt[0]], [base_point[1], pt[1]], 
                    'b--', alpha=0.3, linewidth=0.8)
    
    ax1.set_title('输入点集 + 极角射线', fontsize=14)
    ax1.set_xlabel('X 坐标')
    ax1.set_ylabel('Y 坐标')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_aspect('equal')
    
    # ===== 右图：凸包结果 =====
    ax2 = axes[1]
    ax2.scatter(all_points[:, 0], all_points[:, 1], 
                c='gray', s=60, alpha=0.5, label='输入点集')
    
    # 计算并绘制凸包
    hull_points = list(graham_scan(points))
    final_hull = hull_points[-1]['hull']
    hull_array = np.array(final_hull + [final_hull[0]])
    ax2.plot(hull_array[:, 0], hull_array[:, 1], 
             'g-', linewidth=2.5, label='凸包边界')
    
    # 凸包顶点高亮
    for pt in final_hull:
        color = 'red' if pt == base_point else 'green'
        ax2.scatter(pt[0], pt[1], c=color, s=150, zorder=5)
        ax2.annotate(f'{pt}', pt, fontsize=9, ha='left', va='bottom')
    
    ax2.set_title(f'Graham Scan 结果 ({len(final_hull)} 个顶点)', fontsize=14)
    ax2.set_xlabel('X 坐标')
    ax2.set_ylabel('Y 坐标')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_aspect('equal')
    
    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    # 生成随机测试点（固定种子保证可复现）
    np.random.seed(42)
    
    # 测试用例1：随机散点
    test_points = np.random.rand(20, 2) * 10
    
    print("=" * 60)
    print("凸包构建可视化测试")
    print("=" * 60)
    print(f"测试点数量: {len(test_points)}")
    print(f"测试点坐标:\n{test_points}")
    
    # 运行动态可视化
    print("\n启动动态可视化（关闭窗口继续静态图）...")
    visualize_graham_scan(test_points)
    
    # 运行静态可视化
    print("\n启动静态可视化...")
    visualize_static(test_points)
    
    print("\n测试完成!")
