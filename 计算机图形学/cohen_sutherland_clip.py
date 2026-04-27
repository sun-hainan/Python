# -*- coding: utf-8 -*-
"""
算法实现：计算机图形学 / cohen_sutherland_clip

本文件实现 cohen_sutherland_clip 相关的算法功能。
"""

from typing import Tuple, List, Optional


# 区域编码常量（使用4位）
# | 1001 | 1000 | 1010 |   左上 上  右上
# | 0001 | 0000 | 0010 |   左   中   右
# | 0101 | 0100 | 0110 |   左下 下  右下
CODE_LEFT = 1       # 1000
CODE_RIGHT = 2      # 0100
CODE_BOTTOM = 4     # 0010
CODE_TOP = 8        # 0001

# 窗口边界常量
XL = 0  # Left X
XR = 0  # Right X
YB = 0  # Bottom Y
YT = 0  # Top Y


def compute_out_code(x: float, y: float, 
                     x_min: float, y_min: float, 
                     x_max: float, y_max: float) -> int:
    """
    计算点的区域编码
    
    参数:
        x, y: 点的坐标
        x_min, y_min: 窗口左下角
        x_max, y_max: 窗口右上角
    
    返回:
        4位区域编码
    """
    code = 0
    
    if x < x_min:
        code |= CODE_LEFT
    elif x > x_max:
        code |= CODE_RIGHT
    
    if y < y_min:
        code |= CODE_BOTTOM
    elif y > y_max:
        code |= CODE_TOP
    
    return code


def cohen_sutherland_clip(x1: float, y1: float, 
                         x2: float, y2: float,
                         x_min: float, y_min: float,
                         x_max: float, y_max: float) -> Optional[Tuple[float, float, float, float]]:
    """
    Cohen-Sutherland 线段裁剪算法
    
    参数:
        x1, y1: 线段起点
        x2, y2: 线段终点
        x_min, y_min: 窗口左下角
        x_max, y_max: 窗口右上角
    
    返回:
        裁剪后的线段 (x1', y1', x2', y2')，或 None（完全丢弃）
    """
    # 初始编码
    code1 = compute_out_code(x1, y1, x_min, y_min, x_max, y_max)
    code2 = compute_out_code(x2, y2, x_min, y_min, x_max, y_max)
    
    while True:
        # 情况1：两个端点都在窗口内 -> 完全保留
        if code1 == 0 and code2 == 0:
            return x1, y1, x2, y2
        
        # 情况2：两个端点都在同一侧 -> 完全丢弃
        if code1 & code2 != 0:
            return None
        
        # 情况3：需要裁剪 -> 计算交点
        # 选择在窗口外的端点
        code_out = code1 if code1 != 0 else code2
        
        # 计算交点（使用参数方程）
        # 斜率
        if x2 != x1:
            slope = (y2 - y1) / (x2 - x1)
        else:
            slope = float('inf') if y2 != y1 else 0
        
        # 根据编码的位，确定裁剪边并计算交点
        if CODE_LEFT & code_out:
            # 与左边界相交
            x = x_min
            y = y1 + slope * (x - x1)
        elif CODE_RIGHT & code_out:
            # 与右边界相交
            x = x_max
            y = y1 + slope * (x - x1)
        elif CODE_BOTTOM & code_out:
            # 与下边界相交
            y = y_min
            if x2 != x1:
                x = x1 + (y - y1) / slope
            else:
                x = x1
        elif CODE_TOP & code_out:
            # 与上边界相交
            y = y_max
            if x2 != x1:
                x = x1 + (y - y1) / slope
            else:
                x = x1
        else:
            # 不应该到这里
            return None
        
        # 用交点替换在窗口外的端点
        if code_out == code1:
            x1, y1 = x, y
            code1 = compute_out_code(x1, y1, x_min, y_min, x_max, y_max)
        else:
            x2, y2 = x, y
            code2 = compute_out_code(x2, y2, x_min, y_min, x_max, y_max)
    
    return None


def cohen_sutherland_clip_batch(lines: List[Tuple[float, float, float, float]],
                                 x_min: float, y_min: float,
                                 x_max: float, y_max: float) -> List[Tuple[float, float, float, float]]:
    """
    批量裁剪多条线段
    
    参数:
        lines: 线段列表 [(x1,y1,x2,y2), ...]
        x_min, y_min: 窗口左下角
        x_max, y_max: 窗口右上角
    
    返回:
        裁剪后的线段列表
    """
    clipped = []
    for x1, y1, x2, y2 in lines:
        result = cohen_sutherland_clip(x1, y1, x2, y2, x_min, y_min, x_max, y_max)
        if result is not None:
            clipped.append(result)
    return clipped


def liang_barsky_clip(x1: float, y1: float, 
                      x2: float, y2: float,
                      x_min: float, y_min: float,
                      x_max: float, y_max: float) -> Optional[Tuple[float, float, float, float]]:
    """
    Liang-Barsky 裁剪算法
    
    参数化线段裁剪，比 Cohen-Sutherland 更高效。
    
    参数:
        x1, y1: 线段起点
        x2, y2: 线段终点
        x_min, y_min: 窗口左下角
        x_max, y_max: 窗口右上角
    
    返回:
        裁剪后的线段，或 None
    """
    # 参数方程: P = P1 + t(P2 - P1), t ∈ [0, 1]
    dx = x2 - x1
    dy = y2 - y1
    
    t0 = 0.0
    t1 = 1.0
    
    # 四个裁剪边界
    p = [-dx, dx, -dy, dy]
    q = [x1 - x_min, x_max - x1, y1 - y_min, y_max - y1]
    
    for i in range(4):
        if p[i] == 0:
            # 线段与边界平行
            if q[i] < 0:
                return None
        else:
            # 计算参数值
            t = q[i] / p[i]
            
            if p[i] < 0:
                # 进入窗口
                t0 = max(t0, t)
            else:
                # 离开窗口
                t1 = min(t1, t)
    
    # 检查是否有效
    if t0 > t1:
        return None
    
    # 计算裁剪后的端点
    x1_clip = x1 + t0 * dx
    y1_clip = y1 + t0 * dy
    x2_clip = x1 + t1 * dx
    y2_clip = y1 + t1 * dy
    
    return x1_clip, y1_clip, x2_clip, y2_clip


if __name__ == "__main__":
    print("=" * 60)
    print("Cohen-Sutherland 裁剪算法测试")
    print("=" * 60)
    
    # 定义裁剪窗口
    x_min, y_min = 2, 2
    x_max, y_max = 8, 8
    
    print(f"\n裁剪窗口: ({x_min},{y_min}) - ({x_max},{y_max})")
    
    # 测试线段
    test_lines = [
        # 完全在窗口内
        (3, 3, 7, 7, "完全在内"),
        # 一端在外
        (1, 3, 5, 7, "左外"),
        (5, 1, 5, 7, "下外"),
        (5, 9, 5, 7, "上外"),
        # 两端在外
        (0, 0, 10, 10, "对角线穿过"),
        (0, 5, 10, 5, "水平穿过"),
        (-2, 3, 12, 3, "水平完全穿过"),
        # 完全在外
        (0, 0, 1, 1, "左上角外"),
        (9, 9, 10, 10, "右下角外"),
        (-2, -2, -1, -1, "完全在左下外"),
    ]
    
    print("\n测试结果:")
    for x1, y1, x2, y2, desc in test_lines:
        result = cohen_sutherland_clip(x1, y1, x2, y2, x_min, y_min, x_max, y_max)
        print(f"  {desc}:")
        print(f"    原线段: ({x1},{y1}) -> ({x2},{y2})")
        if result:
            r1, r2, r3, r4 = result
            print(f"    裁剪后: ({r1:.2f},{r2:.2f}) -> ({r3:.2f},{r4:.2f})")
        else:
            print(f"    裁剪后: 丢弃")
    
    # 批量裁剪测试
    print("\n批量裁剪测试:")
    lines = [
        (0, 0, 10, 10),
        (0, 5, 10, 5),
        (5, 0, 5, 10),
        (1, 1, 2, 2),
        (9, 9, 10, 10),
    ]
    
    clipped = cohen_sutherland_clip_batch(lines, x_min, y_min, x_max, y_max)
    print(f"  输入: {len(lines)} 条线段")
    print(f"  输出: {len(clipped)} 条线段")
    
    # 可视化
    print("\n可视化:")
    print("  窗口范围: y 9 (上) to 1 (下)")
    
    # 创建简化的可视化
    import sys
    width = 13
    height = 11
    
    for y in range(height - 1, -1, -1):
        row = ""
        for x in range(width):
            # 窗口边界
            if x == x_min - 1 and y == y_min - 1:
                row += "+"
            elif x == x_min - 1 or x == x_max + 1:
                if y_min <= y <= y_max:
                    row += "|"
                else:
                    row += " "
            elif y == y_min - 1 or y == y_max + 1:
                if x_min <= x <= x_max:
                    row += "-"
                else:
                    row += " "
            elif x_min <= x <= x_max and y_min <= y <= y_max:
                row += "."
            else:
                row += " "
        print(f"  y={y:2d} {row}")
    
    print(f"       {' ' * (x_min - 1) + 'x' * (x_max - x_min + 1)}")
    print(f"         x={x_min} to {x_max}")
    
    print("\n" + "=" * 60)
    print("复杂度分析:")
    print("=" * 60)
    print("  时间复杂度: O(1) 每个线段")
    print("  空间复杂度: O(1)")
    print("  注意: Cohen-Sutherland 需要多次迭代计算交点")
    print("       Liang-Barsky 只需要一次参数计算，更高效")
