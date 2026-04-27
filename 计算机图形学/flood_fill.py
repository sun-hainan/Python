# -*- coding: utf-8 -*-

"""

算法实现：计算机图形学 / flood_fill



本文件实现 flood_fill 相关的算法功能。

"""



from typing import List, Tuple, Set, Optional

from collections import deque





Point = Tuple[int, int]

Color = int





def flood_fill_4(image: List[List[Color]], 

                seed_x: int, seed_y: int,

                new_color: Color) -> List[List[Color]]:

    """

    4连通洪水填充

    

    参数:

        image: 图像矩阵

        seed_x, seed_y: 种子点坐标

        new_color: 新的填充颜色

    

    返回:

        填充后的图像

    """

    height = len(image)

    if height == 0:

        return image

    width = len(image[0])

    

    # 获取种子颜色

    target_color = image[seed_y][seed_x]

    

    # 如果颜色相同则无需填充

    if target_color == new_color:

        return image

    

    # 深度优先搜索

    stack = [(seed_x, seed_y)]

    visited: Set[Point] = set()

    

    while stack:

        x, y = stack.pop()

        

        # 检查边界

        if x < 0 or x >= width or y < 0 or y >= height:

            continue

        

        # 检查是否已访问

        if (x, y) in visited:

            continue

        

        # 检查颜色是否匹配

        if image[y][x] != target_color:

            continue

        

        # 填充

        image[y][x] = new_color

        visited.add((x, y))

        

        # 4连通邻居

        stack.append((x + 1, y))

        stack.append((x - 1, y))

        stack.append((x, y + 1))

        stack.append((x, y - 1))

    

    return image





def flood_fill_8(image: List[List[Color]],

                 seed_x: int, seed_y: int,

                 new_color: Color) -> List[List[Color]]:

    """

    8连通洪水填充

    

    参数:

        image: 图像矩阵

        seed_x, seed_y: 种子点坐标

        new_color: 新的填充颜色

    

    返回:

        填充后的图像

    """

    height = len(image)

    if height == 0:

        return image

    width = len(image[0])

    

    target_color = image[seed_y][seed_x]

    

    if target_color == new_color:

        return image

    

    stack = [(seed_x, seed_y)]

    visited: Set[Point] = set()

    

    while stack:

        x, y = stack.pop()

        

        if x < 0 or x >= width or y < 0 or y >= height:

            continue

        

        if (x, y) in visited:

            continue

        

        if image[y][x] != target_color:

            continue

        

        image[y][x] = new_color

        visited.add((x, y))

        

        # 8连通邻居

        for dx in [-1, 0, 1]:

            for dy in [-1, 0, 1]:

                if dx == 0 and dy == 0:

                    continue

                stack.append((x + dx, y + dy))

    

    return image





def flood_fill_bfs(image: List[List[Color]],

                   seed_x: int, seed_y: int,

                   new_color: Color) -> List[List[Color]]:

    """

    洪水填充（BFS 版本，广度优先）

    

    参数:

        image: 图像矩阵

        seed_x, seed_y: 种子点坐标

        new_color: 新的填充颜色

    

    返回:

        填充后的图像

    """

    height = len(image)

    if height == 0:

        return image

    width = len(image[0])

    

    target_color = image[seed_y][seed_x]

    

    if target_color == new_color:

        return image

    

    queue = deque([(seed_x, seed_y)])

    visited: Set[Point] = set()

    

    while queue:

        x, y = queue.popleft()

        

        if x < 0 or x >= width or y < 0 or y >= height:

            continue

        

        if (x, y) in visited:

            continue

        

        if image[y][x] != target_color:

            continue

        

        image[y][x] = new_color

        visited.add((x, y))

        

        # 4连通

        queue.append((x + 1, y))

        queue.append((x - 1, y))

        queue.append((x, y + 1))

        queue.append((x, y - 1))

    

    return image





def flood_fill_scanline(image: List[List[Color]],

                        seed_x: int, seed_y: int,

                        new_color: Color) -> List[List[Color]]:

    """

    扫描线洪水填充（优化大量像素情况）

    

    思路：

    1. 从种子点向左右扫描，填充一整行

    2. 记录这一行的边界

    3. 对于上下相邻的行，从边界处继续扫描

    

    参数:

        image: 图像矩阵

        seed_x, seed_y: 种子点坐标

        new_color: 新的填充颜色

    

    返回:

        填充后的图像

    """

    height = len(image)

    if height == 0:

        return image

    width = len(image[0])

    

    target_color = image[seed_y][seed_x]

    

    if target_color == new_color:

        return image

    

    stack = [(seed_x, seed_y)]

    

    while stack:

        x, y = stack.pop()

        

        # 从种子点向左扩展

        left = x

        while left > 0 and image[y][left - 1] == target_color:

            left -= 1

        

        # 从种子点向右扩展

        right = x

        while right < width - 1 and image[y][right + 1] == target_color:

            right += 1

        

        # 填充这一行

        for i in range(left, right + 1):

            image[y][i] = new_color

        

        # 检查上下两行

        for dy in [-1, 1]:

            new_y = y + dy

            if 0 <= new_y < height:

            if 0 <= new_y < height:

                # 扫描这一行中的可填充区间

                continue

            segment_start = None

            

            for i in range(left, right + 1):

                if image[new_y][i] == target_color:

                    if segment_start is None:

                        segment_start = i

                else:

                    if segment_start is not None:

                        stack.append((segment_start, new_y))

                        segment_start = None

            

            if segment_start is not None:

                stack.append((segment_start, new_y))

    

    return image





def get_filled_pixels(image: List[List[Color]],

                      seed_x: int, seed_y: int) -> Set[Point]:

    """

    获取填充区域的像素集合（不修改原图）

    

    参数:

        image: 图像矩阵

        seed_x, seed_y: 种子点坐标

    

    返回:

        填充区域像素集合

    """

    height = len(image)

    if height == 0:

        return set()

    width = len(image[0])

    

    target_color = image[seed_y][seed_x]

    filled: Set[Point] = set()

    

    queue = deque([(seed_x, seed_y)])

    

    while queue:

        x, y = queue.popleft()

        

        if x < 0 or x >= width or y < 0 or y >= height:

            continue

        

        if (x, y) in filled:

            continue

        

        if image[y][x] != target_color:

            continue

        

        filled.add((x, y))

        

        queue.append((x + 1, y))

        queue.append((x - 1, y))

        queue.append((x, y + 1))

        queue.append((x, y - 1))

    

    return filled





if __name__ == "__main__":

    print("=" * 60)

    print("洪水填充算法测试")

    print("=" * 60)

    

    # 创建测试图像

    def create_test_image():

        return [

            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],

            [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],

            [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],

            [0, 1, 1, 0, 0, 0, 1, 1, 1, 0],

            [0, 1, 1, 0, 0, 0, 1, 1, 1, 0],

            [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],

            [0, 1, 1, 1, 1, 1, 1, 1, 1, 0],

            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],

        ]

    

    # 测试1：基本填充

    print("\n测试1 - 基本填充（从中心）:")

    image = create_test_image()

    print("  填充前:")

    for y, row in enumerate(image):

        print(f"    y={y}: {''.join(str(v) for v in row)}")

    

    image = flood_fill_bfs(image, 4, 4, 2)

    

    print("\n  填充后 (种子点4,4):")

    for y, row in enumerate(image):

        print(f"    y={y}: {''.join(str(v) for v in row)}")

    

    # 测试2：边界填充

    print("\n测试2 - 边界填充:")

    image = create_test_image()

    image = flood_fill_bfs(image, 0, 0, 3)  # 从边界开始

    

    print("  从(0,0)开始填充颜色3:")

    for y, row in enumerate(image):

        print(f"    y={y}: {''.join(str(v) for v in row)}")

    

    # 测试3：带"岛屿"的情况

    print("\n测试3 - 填充一个环状区域:")

    

    def create_ring_image():

        return [

            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],

            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],

            [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1],

            [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],

            [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1],

            [1, 0, 1, 0, 1, 2, 1, 0, 1, 0, 1],

            [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1],

            [1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],

            [1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1],

            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],

            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],

        ]

    

    image = create_ring_image()

    print("  填充前 (2是中心岛屿):")

    for y, row in enumerate(image):

        print(f"    y={y}: {''.join(str(v) for v in row)}")

    

    image = flood_fill_bfs(image, 1, 1, 3)  # 填充外环

    

    print("\n  填充后 (种子点1,1):")

    for y, row in enumerate(image):

        print(f"    y={y}: {''.join(str(v) for v in row)}")

    

    # 测试4：获取填充像素集合

    print("\n测试4 - 获取填充像素集合:")

    image = create_test_image()

    filled = get_filled_pixels(image, 4, 4)

    print(f"  种子点(4,4)的填充区域包含 {len(filled)} 个像素")

    print(f"  是否包含中心点(4,4): {(4,4) in filled}")

    print(f"  是否包含角落点(0,0): {(0,0) in filled}")

    

    print("\n" + "=" * 60)

    print("复杂度分析:")

    print("=" * 60)

    print("  时间复杂度: O(w × h)")

    print("    w = 图像宽度")

    print("    h = 图像高度")

    print("  空间复杂度: O(w × h) 访问记录")

    print("  优化版本:")

    print("    - 扫描线填充减少栈深度")

    print("    - BFS 保证最短路径")

    print("    - 边界限制避免溢出")

