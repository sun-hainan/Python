# -*- coding: utf-8 -*-

"""

算法实现：25_其他工具 / graham_scan



本文件实现 graham_scan 相关的算法功能。

"""



from __future__ import annotations



from collections import deque

from enum import Enum

from math import atan2, degrees

from sys import maxsize





# 方向枚举（左转、直线、右转）

class Direction(Enum):

    left = 1

    straight = 2

    right = 3



    def __repr__(self):

        return f"{self.__class__.__name__}.{self.name}"





def angle_comparer(point: tuple[int, int], minx: int, miny: int) -> float:

    """

    计算从 (minx, miny) 到 point 的极角（度数）。

    

    Args:

        point: 目标点 (x, y)

        minx: 起点 x 坐标

        miny: 起点 y 坐标

    

    Returns:

        极角（度数，逆时针为正）

    

    示例:

        >>> angle_comparer((1,1), 0, 0)

        45.0

    """

    x, y = point

    return degrees(atan2(y - miny, x - minx))





def check_direction(

    starting: tuple[int, int], via: tuple[int, int], target: tuple[int, int]

) -> Direction:

    """

    判断从 starting 经 via 到 target 的转向。

    

    使用 via 相对于 starting 的角度和 target 相对于 starting 的角度比较。

    

    Args:

        starting: 起点

        via: 中间点

        target: 目标点

    

    Returns:

        Direction.left: 左转（逆时针）

        Direction.straight: 直线

        Direction.right: 右转（顺时针）

    

    示例:

        >>> check_direction((0,0), (5,5), (10,0))

        Direction.right

    """

    x0, y0 = starting

    x1, y1 = via

    x2, y2 = target

    # 计算 via 相对于 starting 的极角

    via_angle = degrees(atan2(y1 - y0, x1 - x0))

    via_angle %= 360

    # 计算 target 相对于 starting 的极角

    target_angle = degrees(atan2(y2 - y0, x2 - x0))

    target_angle %= 360

    

    if target_angle > via_angle:

        return Direction.left

    elif target_angle == via_angle:

        return Direction.straight

    else:

        return Direction.right





def graham_scan(points: list[tuple[int, int]]) -> list[tuple[int, int]]:

    """

    Graham 扫描算法计算凸包。

    

    Args:

        points: 平面上的唯一点列表 [(x, y), ...]

    

    Returns:

        凸包顶点列表（逆时针顺序）

    

    Raises:

        ValueError: 点数不足

    

    示例:

        >>> graham_scan([(9, 6), (3, 1), (0, 0), (5, 5), (5, 2), (7, 0), (3, 3), (1, 4)])

        [(0, 0), (7, 0), (9, 6), (5, 5), (1, 4)]

    """

    if len(points) <= 2:

        raise ValueError("graham_scan: argument must contain more than 3 points.")

    if len(points) == 3:

        return points

    

    # 找到纵坐标最低的点（若有多个，横坐标最小）

    minidx = 0

    miny, minx = maxsize, maxsize

    for i, point in enumerate(points):

        x = point[0]

        y = point[1]

        if y < miny:

            miny = y

            minx = x

            minidx = i

        if y == miny and x < minx:

            minx = x

            minidx = i



    # 移除最低点用于排序

    points.pop(minidx)



    # 按极角排序

    sorted_points = sorted(points, key=lambda point: angle_comparer(point, minx, miny))

    # 将最低点加入排序序列开头

    sorted_points.insert(0, (minx, miny))



    # 使用栈维护凸包

    stack: deque[tuple[int, int]] = deque()

    stack.append(sorted_points[0])

    stack.append(sorted_points[1])

    stack.append(sorted_points[2])

    # 前三个点一定是左转（因为按极角排序）

    current_direction = Direction.left



    for i in range(3, len(sorted_points)):

        while True:

            starting = stack[-2]

            via = stack[-1]

            target = sorted_points[i]

            next_direction = check_direction(starting, via, target)



            if next_direction == Direction.left:

                current_direction = Direction.left

                break

            if next_direction == Direction.straight:

                if current_direction == Direction.left:

                    # 保持方向为 left

                    break

                elif current_direction == Direction.right:

                    # 直线朝右时，移除中间点

                    stack.pop()

            if next_direction == Direction.right:

                stack.pop()

        stack.append(sorted_points[i])

    

    return list(stack)





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    # 测试用例

    test_points = [(9, 6), (3, 1), (0, 0), (5, 5), (5, 2), (7, 0), (3, 3), (1, 4)]

    hull = graham_scan(test_points)

    print("凸包顶点:", hull)

