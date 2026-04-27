# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / morphological_ops

本文件实现 morphological_ops 相关的算法功能。
"""

import numpy as np
from collections import deque


class StructuringElement:
    """
    结构元素

    定义形态学操作的邻域形状。
    """

    @staticmethod
    def square(size):
        """
        方形结构元素

        参数:
            size: 边长（奇数）
        返回:
            se: 结构元素掩码
        """
        return np.ones((size, size), dtype=bool)

    @staticmethod
    def disk(radius):
        """
        圆形结构元素

        参数:
            radius: 半径
        返回:
            se: 圆形掩码
        """
        size = 2 * radius + 1
        y, x = np.ogrid[:size, :size]
        center = radius
        se = ((x - center)**2 + (y - center)**2) <= radius**2
        return se

    @staticmethod
    def cross(size):
        """
        十字形结构元素

        参数:
            size: 大小（奇数）
        返回:
            se: 十字形掩码
        """
        se = np.zeros((size, size), dtype=bool)
        center = size // 2
        se[center, :] = True
        se[:, center] = True
        return se


def erosion(image, se):
    """
    腐蚀操作

    输出像素 = 1 当且仅当 SE 覆盖的所有像素都为 1

    参数:
        image: 二值图像
        se: 结构元素
    返回:
        output: 腐蚀后图像
    """
    image = np.array(image, dtype=bool)
    se_center = np.array(se.shape) // 2

    h, w = image.shape
    sh, sw = se.shape
    output = np.zeros_like(image)

    for y in range(sh // 2, h - sh // 2):
        for x in range(sw // 2, w - sw // 2):
            # 检查 SE 覆盖的所有像素
            region = image[y - se_center[0]:y + se_center[0] + 1,
                        x - se_center[1]:x + se_center[1] + 1]
            if np.all(region[se]):
                output[y, x] = True

    return output


def dilation(image, se):
    """
    膨胀操作

    输出像素 = 1 当 SE 覆盖的像素中至少有一个为 1

    参数:
        image: 二值图像
        se: 结构元素
    返回:
        output: 膨胀后图像
    """
    image = np.array(image, dtype=bool)
    se_center = np.array(se.shape) // 2

    h, w = image.shape
    sh, sw = se.shape
    output = np.zeros_like(image)

    for y in range(sh // 2, h - sh // 2):
        for x in range(sw // 2, w - sw // 2):
            if image[y, x]:
                # 标记 SE 覆盖的位置
                for sy in range(-se_center[0], se_center[0] + 1):
                    for sx in range(-se_center[1], se_center[1] + 1):
                        if se[sy + se_center[0], sx + se_center[1]]:
                            ny, nx = y + sy, x + sx
                            if 0 <= ny < h and 0 <= nx < w:
                                output[ny, nx] = True

    return output


def opening(image, se):
    """
    开运算

    先腐蚀后膨胀，去除小的亮点。

    参数:
        image: 输入图像
        se: 结构元素
    返回:
        output: 开运算结果
    """
    return dilation(erosion(image, se), se)


def closing(image, se):
    """
    闭运算

    先膨胀后腐蚀，填充小的暗点。

   参数:
        image: 输入图像
        se: 结构元素
    返回:
        output: 闭运算结果
    """
    return erosion(dilation(image, se), se)


def boundary(image, se=None):
    """
    提取边界

    边界 = 图像 - 腐蚀后图像

    参数:
        image: 二值图像
        se: 结构元素
    返回:
        boundary: 边界
    """
    if se is None:
        se = StructuringElement.square(3)
    eroded = erosion(image, se)
    return image.astype(bool) ^ eroded.astype(bool)


def region_filling(binary_image, seed_point):
    """
    区域填充（洪水填充算法）

    参数:
        binary_image: 二值图像
        seed_point: 种子点 (y, x)
    返回:
        filled: 填充后图像
    """
    h, w = binary_image.shape
    filled = np.zeros_like(binary_image)
    queue = deque([seed_point])

    while queue:
        y, x = queue.popleft()

        if not (0 <= y < h and 0 <= x < w):
            continue

        if filled[y, x] or not binary_image[y, x]:
            continue

        filled[y, x] = True

        # 4-邻域
        queue.append((y + 1, x))
        queue.append((y - 1, x))
        queue.append((y, x + 1))
        queue.append((y, x - 1))

    return filled


def morphological_gradient(image, se=None):
    """
    形态学梯度

    梯度 = 膨胀 - 腐蚀

    参数:
        image: 输入图像
        se: 结构元素
    返回:
        gradient: 梯度图像
    """
    if se is None:
        se = StructuringElement.square(3)

    dilated = dilation(image, se)
    eroded = erosion(image, se)

    return dilated.astype(float) - eroded.astype(float)


def top_hat(image, se=None):
    """
    顶帽变换

    提取小的亮细节。

    参数:
        image: 输入图像
        se: 结构元素
    返回:
        top_hat: 顶帽变换结果
    """
    if se is None:
        se = StructuringElement.square(5)
    return image.astype(float) - opening(image, se).astype(float)


def black_hat(image, se=None):
    """
    黑帽变换

    提取小的暗细节。

    参数:
        image: 输入图像
        se: 结构元素
    返回:
        black_hat: 黑帽变换结果
    """
    if se is None:
        se = StructuringElement.square(5)
    return closing(image, se).astype(float) - image.astype(float)


def skeletonize(image, se=None):
    """
    骨架提取

    提取对象的中心骨架。

    参数:
        image: 二值图像
        se: 结构元素
    返回:
        skeleton: 骨架
    """
    if se is None:
        # 使用简单的形态学方法
        se = StructuringElement.square(3)

    skeleton = np.zeros_like(image)
    temp = image.copy()

    while True:
        # 开运算
        opened = opening(temp, se)
        # 边界
        boundary = temp.astype(bool) ^ opened.astype(bool)
        skeleton |= boundary
        temp = erosion(opened, se)

        if not np.any(temp):
            break

    return skeleton


def hit_or_miss(image, kernel1, kernel2=None):
    """
    击中击不中变换

    形状匹配。

    参数:
        image: 输入图像
        kernel1: 目标形状核
        kernel2: 背景形状核（可选）
    返回:
        result: 匹配位置
    """
    if kernel2 is None:
        kernel2 = ~kernel1

    result = np.zeros_like(image)

    h, w = image.shape
    kh1, kw1 = kernel1.shape
    center = np.array(kernel1.shape) // 2

    for y in range(center[0], h - center[0]):
        for x in range(center[1], w - center[1]):
            # 检查 kernel1 覆盖
            region = image[y - center[0]:y + center[0] + 1,
                          x - center[1]:x + center[1] + 1]

            match1 = np.all(region[kernel1] == 1) if np.any(kernel1) else True
            match2 = np.all(region[kernel2] == 0) if np.any(kernel2) else True

            if match1 and match2:
                result[y, x] = 1

    return result


class MorphologicalFilter:
    """
    形态学滤波器

    提供完整的形态学操作接口。
    """

    def __init__(self, se_type='square', se_size=3):
        """
        初始化

        参数:
            se_type: 结构元素类型
            se_size: 结构元素大小
        """
        if se_type == 'square':
            self.se = StructuringElement.square(se_size)
        elif se_type == 'disk':
            self.se = StructuringElement.disk(se_size // 2)
        elif se_type == 'cross':
            self.se = StructuringElement.cross(se_size)
        else:
            self.se = StructuringElement.square(se_size)

    def erode(self, image):
        return erosion(image, self.se)

    def dilate(self, image):
        return dilation(image, self.se)

    def open(self, image):
        return opening(image, self.se)

    def close(self, image):
        return closing(image, self.se)

    def gradient(self, image):
        return morphological_gradient(image, self.se)

    def tophat(self, image):
        return top_hat(image, self.se)

    def blackhat(self, image):
        return black_hat(image, self.se)


if __name__ == "__main__":
    print("=== 形态学操作测试 ===")

    # 创建测试图像
    print("\n1. 创建测试图像")
    image = np.zeros((50, 50), dtype=bool)
    image[10:20, 10:20] = True  # 方形
    image[30:40, 30:40] = True  # 另一个方形
    image[35, 35] = True  # 孤立点
    print(f"图像形状: {image.shape}")
    print(f"白色像素数: {np.sum(image)}")

    # 创建结构元素
    se_sq = StructuringElement.square(3)
    se_disk = StructuringElement.disk(3)
    se_cross = StructuringElement.cross(3)

    print(f"\n方形 SE 形状: {se_sq.shape}")
    print(f"圆形 SE 形状: {se_disk.shape}")
    print(f"十字形 SE 形状: {se_cross.shape}")

    # 腐蚀
    print("\n2. 腐蚀操作")
    eroded = erosion(image, se_sq)
    print(f"腐蚀后白色像素: {np.sum(eroded)}")

    # 膨胀
    print("\n3. 膨胀操作")
    dilated = dilation(image, se_sq)
    print(f"膨胀后白色像素: {np.sum(dilated)}")

    # 开运算
    print("\n4. 开运算")
    opened = opening(image, se_sq)
    print(f"开运算后白色像素: {np.sum(opened)}")

    # 闭运算
    print("\n5. 闭运算")
    closed = closing(image, se_sq)
    print(f"闭运算后白色像素: {np.sum(closed)}")

    # 边界提取
    print("\n6. 边界提取")
    boundary_img = boundary(image, se_sq)
    print(f"边界像素数: {np.sum(boundary_img)}")

    # 形态学梯度
    print("\n7. 形态学梯度")
    grad = morphological_gradient(image.astype(float), se_sq)
    print(f"梯度范围: [{np.min(grad):.2f}, {np.max(grad):.2f}]")

    # 顶帽和黑帽
    print("\n8. 顶帽和黑帽变换")
    tophat = top_hat(image.astype(float), se_sq)
    blackhat = black_hat(image.astype(float), se_sq)
    print(f"顶帽变换范围: [{np.min(tophat):.2f}, {np.max(tophat):.2f}]")
    print(f"黑帽变换范围: [{np.min(blackhat):.2f}, {np.max(blackhat):.2f}]")

    # 骨架提取
    print("\n9. 骨架提取")
    skeleton = skeletonize(image, se_sq)
    print(f"骨架像素数: {np.sum(skeleton)}")

    # 区域填充
    print("\n10. 区域填充")
    # 创建带孔的图像
    hollow = np.zeros((50, 50), dtype=bool)
    hollow[20:30, 20:30] = True
    hollow[23:27, 23:27] = False  # 孔
    filled = region_filling(hollow, (25, 25))
    print(f"填充前白色像素: {np.sum(hollow)}")
    print(f"填充后白色像素: {np.sum(filled)}")

    # 形态学滤波器
    print("\n11. MorphologicalFilter 类")
    mf = MorphologicalFilter(se_type='disk', se_size=5)
    filtered = mf.close(image)
    print(f"形态学滤波后白色像素: {np.sum(filtered)}")

    print("\n形态学操作测试完成!")
