# -*- coding: utf-8 -*-
"""
算法实现：18_信号与图像 / image_warp

本文件实现 image_warp 相关的算法功能。
"""

import numpy as np
import math


class AffineTransform:
    """
    2D 仿射变换

    变换矩阵：
    [x']   [a b] [x]   [e]
    [y'] = [c d] [y] + [f]
    """

    def __init__(self):
        self.matrix = np.eye(3)

    @staticmethod
    def translation(tx, ty):
        """平移矩阵"""
        T = np.eye(3)
        T[0, 2] = tx
        T[1, 2] = ty
        return T

    @staticmethod
    def rotation(angle):
        """旋转矩阵（弧度）"""
        c, s = math.cos(angle), math.sin(angle)
        R = np.eye(3)
        R[0, 0] = c; R[0, 1] = -s
        R[1, 0] = s; R[1, 1] = c
        return R

    @staticmethod
    def scaling(sx, sy):
        """缩放矩阵"""
        S = np.eye(3)
        S[0, 0] = sx
        S[1, 1] = sy
        return S

    @staticmethod
    def shear(shx, shy):
        """剪切矩阵"""
        H = np.eye(3)
        H[0, 1] = shx
        H[1, 0] = shy
        return H

    @staticmethod
    def from_points(src_points, dst_points):
        """
        从对应点对计算变换矩阵

        参数:
            src_points: 源点 (3, 2)
            dst_points: 目标点 (3, 2)
        返回:
            matrix: 2x3 变换矩阵
        """
        A = []
        B = []
        for (x, y), (u, v) in zip(src_points, dst_points):
            A.append([x, y, 1, 0, 0, 0])
            A.append([0, 0, 0, x, y, 1])
            B.append(u)
            B.append(v)

        A = np.array(A)
        B = np.array(B)

        try:
            h = np.linalg.lstsq(A, B, rcond=None)[0]
            M = np.array([[h[0], h[1], h[2]],
                          [h[3], h[4], h[5]]])
        except:
            M = np.eye(2, 3)

        return M

    def transform_point(self, x, y):
        """变换单个点"""
        pt = np.array([x, y, 1])
        new_pt = self.matrix @ pt
        return new_pt[0] / new_pt[2], new_pt[1] / new_pt[2]


class PerspectiveTransform:
    """
    透视变换（单应性变换 Homography）

    8 个自由度，需要 4 个点对确定。
    """

    def __init__(self):
        self.matrix = np.eye(3)

    @staticmethod
    def from_points(src_points, dst_points):
        """
        从 4 个对应点计算透视变换矩阵

        参数:
            src_points: 源点 [(x,y), ...]
            dst_points: 目标点 [(u,v), ...]
        返回:
            H: 3x3 变换矩阵
        """
        A = []
        for (x, y), (u, v) in zip(src_points, dst_points):
            A.append([-x, -y, -1, 0, 0, 0, u*x, u*y, u])
            A.append([0, 0, 0, -x, -y, -1, v*x, v*y, v])

        A = np.array(A)
        _, _, V = np.linalg.svd(A)
        H = V[-1].reshape(3, 3)
        H = H / H[2, 2]  # 归一化

        return H

    def transform_point(self, x, y):
        """变换点"""
        pt = np.array([x, y, 1])
        new_pt = self.matrix @ pt
        return new_pt[0] / new_pt[2], new_pt[1] / new_pt[2]


def warp_affine(image, M, output_shape=None):
    """
    仿射变换

    参数:
        image: 输入图像
        M: 2x3 变换矩阵
        output_shape: 输出形状
    返回:
        warped: 变形后图像
    """
    h, w = image.shape[:2]
    if output_shape is None:
        output_shape = (h, w)

    out_h, out_w = output_shape
    warped = np.zeros_like(image)

    M_inv = np.linalg.inv(np.vstack([M, [0, 0, 1]]))

    for y in range(out_h):
        for x in range(out_w):
            src_pt = M_inv @ np.array([x, y, 1])
            sx, sy = src_pt[0] / src_pt[2], src_pt[1] / src_pt[2]

            if 0 <= sx < w - 1 and 0 <= sy < h - 1:
                # 双线性插值
                x0, y0 = int(sx), int(sy)
                fx, fy = sx - x0, sy - y0

                p00 = image[y0, x0]
                p01 = image[y0, min(x0 + 1, w - 1)]
                p10 = image[min(y0 + 1, h - 1), x0]
                p11 = image[min(y0 + 1, h - 1), min(x0 + 1, w - 1)]

                warped[y, x] = (1 - fx) * (1 - fy) * p00 + \
                               fx * (1 - fy) * p01 + \
                               (1 - fx) * fy * p10 + \
                               fx * fy * p11

    return warped


def warp_perspective(image, H, output_shape=None):
    """
    透视变换

    参数:
        image: 输入图像
        H: 3x3 透视变换矩阵
        output_shape: 输出形状
    返回:
        warped: 变形后图像
    """
    h, w = image.shape[:2]
    if output_shape is None:
        output_shape = (h, w)

    out_h, out_w = output_shape
    warped = np.zeros_like(image)

    H_inv = np.linalg.inv(H)

    for y in range(out_h):
        for x in range(out_w):
            src_pt = H_inv @ np.array([x, y, 1])
            sx, sy = src_pt[0] / src_pt[2], src_pt[1] / src_pt[2]

            if 0 <= sx < w - 1 and 0 <= sy < h - 1:
                x0, y0 = int(sx), int(sy)
                fx, fy = sx - x0, sy - y0

                p00 = image[y0, x0]
                p01 = image[y0, min(x0 + 1, w - 1)]
                p10 = image[min(y0 + 1, h - 1), x0]
                p11 = image[min(y0 + 1, h - 1), min(x0 + 1, w - 1)]

                warped[y, x] = (1 - fx) * (1 - fy) * p00 + \
                               fx * (1 - fy) * p01 + \
                               (1 - fx) * fy * p10 + \
                               fx * fy * p11

    return warped


def barrel_distortion(image, k=0.1):
    """
    桶形畸变

    参数:
        image: 输入图像
        k: 畸变系数
    返回:
        distorted: 畸变后图像
    """
    h, w = image.shape[:2]
    cx, cy = w / 2, h / 2

    distorted = np.zeros_like(image)
    max_r = math.sqrt(cx**2 + cy**2)

    for y in range(h):
        for x in range(w):
            # 归一化坐标
            nx = (x - cx) / cx
            ny = (y - cy) / cy
            r = math.sqrt(nx**2 + ny**2)

            # 畸变
            factor = 1 + k * r**2
            dx = nx * factor
            dy = ny * factor

            # 反变换到原图
            sx = int(dx * cx + cx)
            sy = int(dy * cy + cy)

            if 0 <= sx < w and 0 <= sy < h:
                distorted[y, x] = image[sy, sx]

    return distorted


def elastic_deformation(image, alpha=10, sigma=3):
    """
    弹性变形

    参数:
        image: 输入图像
        alpha: 变形幅度
        sigma: 高斯核标准差
    返回:
        deformed: 变形后图像
    """
    from scipy.ndimage import gaussian_filter

    h, w = image.shape[:2]

    # 随机位移场
    dx = np.random.randn(h, w) * alpha
    dy = np.random.randn(h, w) * alpha

    # 平滑位移
    dx = gaussian_filter(dx, sigma)
    dy = gaussian_filter(dy, sigma)

    deformed = np.zeros_like(image)

    for y in range(h):
        for x in range(w):
            sx = int(x + dx[y, x])
            sy = int(y + dy[y, x])

            if 0 <= sx < w and 0 <= sy < h:
                deformed[y, x] = image[sy, sx]

    return deformed


if __name__ == "__main__":
    print("=== 图像变形测试 ===")

    # 创建测试图像
    print("\n1. 创建测试图像")
    image = np.zeros((100, 100))
    image[20:80, 20:80] = 200
    image[40:60, 40:60] = 100
    print(f"图像尺寸: {image.shape}")

    # 仿射变换
    print("\n2. 仿射变换")
    T = AffineTransform.translation(10, 5)
    R = AffineTransform.rotation(math.radians(15))
    S = AffineTransform.scaling(0.8, 0.8)

    combined = S @ R @ T
    print(f"变换矩阵:\n{combined}")

    # 应用仿射变换
    warped = warp_affine(image, combined[:2])
    print(f"变形后非零像素: {np.sum(warped > 0)}")

    # 透视变换
    print("\n3. 透视变换")
    src_points = [(0, 0), (100, 0), (100, 100), (0, 100)]
    dst_points = [(10, 5), (95, 0), (100, 95), (5, 100)]

    H = PerspectiveTransform.from_points(src_points, dst_points)
    print(f"透视变换矩阵:\n{H}")

    warped_persp = warp_perspective(image, H)
    print(f"透视变形后非零像素: {np.sum(warped_persp > 0)}")

    # 桶形畸变
    print("\n4. 桶形畸变")
    distorted = barrel_distortion(image, k=0.05)
    print(f"畸变后中心像素值: {distorted[50, 50]:.1f}")

    # 弹性变形
    print("\n5. 弹性变形")
    deformed = elastic_deformation(image, alpha=5, sigma=2)
    print(f"变形后非零像素: {np.sum(deformed > 0)}")

    # 点变换验证
    print("\n6. 点变换验证")
    pt = (50, 50)
    transformed = AffineTransform().transform_point(pt[0], pt[1], combined)
    print(f"点 {pt} 变换后: ({transformed[0]:.2f}, {transformed[1]:.2f})")

    print("\n图像变形测试完成!")
