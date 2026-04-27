# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / hough_transform

本文件实现 hough_transform 相关的算法功能。
"""

import numpy as np
import math


class HoughLines:
    """
    霍夫直线变换

    检测图像中的直线。
    """

    def __init__(self, rho_resolution=1, theta_resolution=1):
        """
        初始化霍夫变换

        参数:
            rho_resolution: ρ 分辨率（像素）
            theta_resolution: θ 分辨率（度）
        """
        self.rho_resolution = rho_resolution
        self.theta_resolution = theta_resolution
        self.threshold = 50  # 投票阈值
        self.accumulator = None

    def transform(self, binary_image):
        """
        霍夫变换

        参数:
            binary_image: 二值边缘图像
        返回:
            lines: 检测到的线 [(ρ, θ), ...]
        """
        image = np.array(binary_image, dtype=bool)
        h, w = image.shape

        # 参数空间大小
        max_rho = int(math.sqrt(h**2 + w**2))
        n_rho = int(max_rho / self.rho_resolution)
        n_theta = int(180 / self.theta_resolution)

        # 累加器
        self.accumulator = np.zeros((n_rho, n_theta))

        # 投票
        y_indices, x_indices = np.where(image)

        for y, x in zip(y_indices, x_indices):
            for theta_idx in range(n_theta):
                theta = math.radians(theta_idx * self.theta_resolution)
                rho = int(x * math.cos(theta) + y * math.sin(theta))
                rho_idx = int(rho / self.rho_resolution)

                if 0 <= rho_idx < n_rho:
                    self.accumulator[rho_idx, theta_idx] += 1

        # 峰值检测
        lines = []
        threshold = self.threshold

        for rho_idx in range(n_rho):
            for theta_idx in range(n_theta):
                if self.accumulator[rho_idx, theta_idx] >= threshold:
                    rho = rho_idx * self.rho_resolution
                    theta = math.radians(theta_idx * self.theta_resolution)
                    lines.append((rho, theta, self.accumulator[rho_idx, theta_idx]))

        # 按投票数排序
        lines.sort(key=lambda x: x[2], reverse=True)

        return lines

    def draw_lines(self, image, lines, color=255):
        """
        在图像上绘制直线

        参数:
            image: 背景图像
            lines: 直线列表
            color: 绘制颜色
        返回:
            result: 绘制后的图像
        """
        result = image.copy()
        h, w = image.shape[:2]

        for rho, theta, votes in lines:
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)

            x0 = cos_t * rho
            y0 = sin_t * rho

            # 延长线到图像边界
            x1 = int(x0 + 1000 * (-sin_t))
            y1 = int(y0 + 1000 * cos_t)
            x2 = int(x0 - 1000 * (-sin_t))
            y2 = int(y0 - 1000 * cos_t)

            # 简化的绘制（仅绘制中心点附近）
            result[int(y0), int(x0)] = color

        return result


class HoughCircles:
    """
    霍夫圆变换

    检测图像中的圆。

    参数方程：
    x = a + r·cos(θ)
    y = b + r·sin(θ)

    累加器是 3D：a, b, r
    """

    def __init__(self, min_radius=10, max_radius=100, threshold=50):
        """
        初始化霍夫圆变换

        参数:
            min_radius: 最小半径
            max_radius: 最大半径
            threshold: 投票阈值
        """
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.threshold = threshold
        self.accumulator = None

    def transform(self, binary_image):
        """
        霍夫圆变换

        参数:
            binary_image: 二值边缘图像
        返回:
            circles: 检测到的圆 [(a, b, r), ...]
        """
        image = np.array(binary_image, dtype=bool)
        h, w = image.shape

        # 累加器大小
        n_a = w
        n_b = h
        n_r = self.max_radius - self.min_radius + 1

        # 3D 累加器
        self.accumulator = np.zeros((n_a, n_b, n_r))

        # 投票（简化：只对边缘点投票）
        y_indices, x_indices = np.where(image)

        for y, x in zip(y_indices, x_indices):
            for r in range(self.min_radius, self.max_radius + 1):
                # 遍历圆上的点
                for theta_idx in range(0, 360, 10):
                    theta = math.radians(theta_idx)
                    a = int(x - r * math.cos(theta))
                    b = int(y - r * math.sin(theta))

                    if 0 <= a < n_a and 0 <= b < n_b:
                        self.accumulator[a, b, r - self.min_radius] += 1

        # 峰值检测
        circles = []
        threshold = self.threshold

        for a in range(n_a):
            for b in range(n_b):
                for r_idx in range(n_r):
                    if self.accumulator[a, b, r_idx] >= threshold:
                        r = r_idx + self.min_radius
                        circles.append((a, b, r, self.accumulator[a, b, r_idx]))

        # 排序
        circles.sort(key=lambda x: x[3], reverse=True)

        return circles


class HoughTransformGeneral:
    """
    通用霍夫变换

    用于检测任意形状。
    """

    def __init__(self, template, threshold=0.8):
        """
        初始化通用霍夫变换

        参数:
            template: 模板点集
            threshold: 匹配阈值
        """
        self.template = np.array(template)
        self.threshold = threshold
        self.accumulator = None

    def transform(self, edge_image):
        """
        通用霍夫变换

        参数:
            edge_image: 边缘图像
        返回:
            peaks: 检测到的位置
        """
        image = np.array(edge_image, dtype=bool)
        h, w = image.shape

        # 模板边界
        t_min = np.min(self.template, axis=0)
        t_max = np.max(self.template, axis=0)

        # 累加器大小
        accumulator_h = h + int(t_max[0] - t_min[0]) + 1
        accumulator_w = w + int(t_max[1] - t_min[1]) + 1

        self.accumulator = np.zeros((accumulator_h, accumulator_w))

        # 获取边缘点
        y_indices, x_indices = np.where(image)

        # 对每个模板点投票
        for ty, tx in self.template:
            for y, x in zip(y_indices, x_indices):
                # 计算位置
                py = int(y - ty)
                px = int(x - tx)

                if 0 <= py < accumulator_h and 0 <= px < accumulator_w:
                    self.accumulator[py, px] += 1

        # 找峰值
        max_votes = np.max(self.accumulator)
        threshold_votes = int(max_votes * self.threshold)

        peaks = np.where(self.accumulator >= threshold_votes)
        peaks = list(zip(peaks[0], peaks[1], self.accumulator[peaks]))

        peaks.sort(key=lambda x: x[2], reverse=True)

        return peaks


def simple_edge_detection(image, threshold=100):
    """
    简单的边缘检测（梯度）

    参数:
        image: 灰度图像
        threshold: 边缘阈值
    返回:
        edges: 二值边缘图像
    """
    image = np.array(image, dtype=float)

    # Sobel 算子
    sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]])
    sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]])

    h, w = image.shape
    edges = np.zeros_like(image)

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            gx = 0
            gy = 0
            for ky in range(-1, 2):
                for kx in range(-1, 2):
                    gx += image[y + ky, x + kx] * sobel_x[ky + 1, kx + 1]
                    gy += image[y + ky, x + kx] * sobel_y[ky + 1, kx + 1]

            magnitude = math.sqrt(gx**2 + gy**2)
            if magnitude >= threshold:
                edges[y, x] = 255

    return edges


def probabilistic_hough_line(image, threshold=50, line_length=30, line_gap=5):
    """
    概率霍夫变换（简化）

    更高效的直线检测。

    参数:
        image: 二值图像
        threshold: 投票阈值
        line_length: 最小线段长度
        line_gap: 最大间隙
    返回:
        lines: 线段列表
    """
    hough = HoughLines()
    lines = hough.transform(image)

    # 简化为返回完整线
    return [(rho, theta) for rho, theta, votes in lines[:10] if votes >= threshold]


if __name__ == "__main__":
    print("=== Hough 变换测试 ===")

    # 创建测试图像
    print("\n1. 创建测试图像")
    image = np.zeros((100, 100), dtype=np.uint8)

    # 绘制对角线（模拟）
    for i in range(50):
        image[2*i, i] = 255
        image[2*i + 1, i] = 255

    # 添加一些噪声点
    for _ in range(20):
        y, x = np.random.randint(0, 100, 2)
        image[y, x] = 255

    print(f"边缘点数: {np.sum(image > 0)}")

    # 霍夫直线变换
    print("\n2. 霍夫直线变换")
    hough = HoughLines(rho_resolution=1, theta_resolution=1)
    lines = hough.transform(image > 0)
    print(f"检测到 {len(lines)} 条直线")
    for i, (rho, theta, votes) in enumerate(lines[:5]):
        print(f"  线 {i+1}: ρ={rho:.1f}, θ={math.degrees(theta):.1f}°, 票数={votes}")

    # 霍夫圆变换
    print("\n3. 霍夫圆变换")
    circle_image = np.zeros((100, 100), dtype=np.uint8)
    cx, cy, r = 50, 50, 20
    for theta in np.linspace(0, 2*np.pi, 100):
        x = int(cx + r * math.cos(theta))
        y = int(cy + r * math.sin(theta))
        if 0 <= x < 100 and 0 <= y < 100:
            circle_image[y, x] = 255

    hough_circles = HoughCircles(min_radius=15, max_radius=25, threshold=10)
    circles = hough_circles.transform(circle_image > 0)
    print(f"检测到 {len(circles)} 个圆")
    for i, (a, b, r, votes) in enumerate(circles[:3]):
        print(f"  圆 {i+1}: 中心=({a}, {b}), r={r}, 票数={votes}")

    # 通用霍夫变换
    print("\n4. 通用霍夫变换")
    # 定义 L 形模板
    template = np.array([[0, 0], [0, 1], [0, 2], [1, 2], [2, 2]])
    general_hough = HoughTransformGeneral(template, threshold=0.6)

    # 创建 L 形图像
    l_image = np.zeros((50, 50), dtype=np.uint8)
    for y in range(10, 20):
        l_image[y, 10] = 255
    for x in range(10, 20):
        l_image[19, x] = 255

    peaks = general_hough.transform(l_image > 0)
    print(f"检测到 {len(peaks)} 个匹配位置")

    # 绘制结果
    print("\n5. 绘制结果（统计）")
    if hough.accumulator is not None:
        print(f"霍夫累加器形状: {hough.accumulator.shape}")
        print(f"累加器最大值: {np.max(hough.accumulator)}")

    # 概率霍夫变换
    print("\n6. 概率霍夫变换")
    prob_lines = probabilistic_hough_line(image > 0, threshold=20)
    print(f"概率霍夫检测到 {len(prob_lines)} 条线段")

    print("\nHough 变换测试完成!")
