# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / radar_imaging



本文件实现 radar_imaging 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Optional

from dataclasses import dataclass





@dataclass

class RadarTarget:

    """雷达目标"""

    range_m: float    # 距离（米）

    azimuth_rad: float  # 方位角（弧度）

    rcs_db: float = 0  # 雷达散射截面（dBsm）





class CompressiveRadar:

    """

    压缩感知雷达成像系统

    使用随机采样减少脉冲数

    """



    def __init__(self, range_resolution_m: float, max_range_m: float,

                 azimuth_range: float):

        self.range_res = range_resolution_m

        self.max_range = max_range_m

        self.azimuth_range = azimuth_range



        # 计算网格

        self.n_range = int(max_range_m / range_resolution_m)

        self.n_azimuth = 360  # 方位角分辨率



    def create_sparse_scene(self, targets: list[RadarTarget]) -> np.ndarray:

        """

        创建稀疏场景（真实场景）

        返回：图像矩阵（range × azimuth）

        """

        scene = np.zeros((self.n_range, self.n_azimuth))



        for target in targets:

            # 计算网格索引

            range_idx = int(target.range_m / self.range_res)

            azimuth_idx = int((target.azimuth_rad + np.pi) / (2 * np.pi) * self.n_azimuth) % self.n_azimuth



            if 0 <= range_idx < self.n_range:

                # RCS转换为线性值

                rcs_linear = 10 ** (target.rcs_db / 10)

                scene[range_idx, azimuth_idx] += rcs_linear



        return scene



    def forward_model(self, scene: np.ndarray,

                      pulse_angles: np.ndarray) -> np.ndarray:

        """

        雷达前向模型

        模拟稀疏采样下的回波采集



        y = A * x + noise

        其中A是测量矩阵，x是场景向量，y是回波信号

        """

        n_range, n_azimuth = scene.shape

        n_pulses = len(pulse_angles)



        # 向量化场景

        x = scene.flatten()



        # 构建测量矩阵

        # 简化模型：回波 = 场景在某角度的投影

        A = np.zeros((n_pulses, n_range * n_azimuth))



        for i, angle in enumerate(pulse_angles):

            for r in range(n_range):

                for a in range(n_azimuth):

                    # 简化的雷达方程

                    # 回波强度与目标距离和RCS成正比

                    path_loss = 1.0 / (r + 1) ** 2

                    # 方位角匹配

                    angle_diff = abs(a / n_azimuth * 2 * np.pi - angle)

                    azimuth_gain = np.exp(-angle_diff ** 2 / (2 * 0.1 ** 2))



                    idx = r * n_azimuth + a

                    A[i, idx] = path_loss * azimuth_gain



        # 测量

        y = A @ x



        return y, A



    def cs_reconstruction(self, y: np.ndarray, A: np.ndarray,

                         scene_shape: tuple,

                         s: int = 10,

                         method: str = "omp") -> np.ndarray:

        """

        压缩感知重建雷达图像



        方法：OMP（贪婪）或 IRLS（非凸）

        """

        if method == "omp":

            x_recovered = self._omp_recover(A, y, s)

        elif method == "irls":

            x_recovered = self._irls_recover(A, y, max_iter=50)

        else:

            raise ValueError(f"Unknown method: {method}")



        # 恢复为图像

        scene_recovered = x_recovered.reshape(scene_shape)



        # 后处理：阈值化

        scene_recovered = np.maximum(scene_recovered, 0)



        return scene_recovered



    def _omp_recover(self, A: np.ndarray, y: np.ndarray, s: int) -> np.ndarray:

        """OMP稀疏恢复"""

        n = A.shape[1]

        x = np.zeros(n)

        support = []

        residual = y.copy()



        for _ in range(s):

            c = A.T @ residual

            best_idx = np.argmax(np.abs(c))

            if best_idx in support:

                break

            support.append(best_idx)



            A_support = A[:, support]

            x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)



            residual = y - A_support @ x_support



        x[support] = x_support

        return x



    def _irls_recover(self, A: np.ndarray, y: np.ndarray, max_iter: int = 50) -> np.ndarray:

        """IRLS恢复（非凸ℓ0.5）"""

        n = A.shape[1]

        x = np.zeros(n)

        delta = 1e-6

        p = 0.5



        for _ in range(max_iter):

            # 权重

            weights = 1.0 / (np.abs(x) + delta) ** (1 - p)

            W = np.diag(weights)



            # 加权最小二乘

            WA = W @ A

            Wy = W @ y

            x_new, _, _, _ = np.linalg.lstsq(WA, Wy, rcond=None)



            if np.linalg.norm(x_new - x) < 1e-6:

                x = x_new

                break



            x = x_new



        return x



    def matched_filter(self, y: np.ndarray, A: np.ndarray) -> np.ndarray:

        """

        匹配滤波器（传统方法对比）

        """

        x_mf = A.T @ y

        return x_mf





class ISARImaging:

    """

    逆合成孔径雷达（ISAR）成像

    利用目标旋转获得方位分辨率

    """



    def __init__(self, n_range: int = 64, n_doppler: int = 64):

        self.n_range = n_range

        self.n_doppler = n_doppler



    def create_sparse_targets(self, targets: list[RadarTarget]) -> np.ndarray:

        """创建ISAR图像"""

        image = np.zeros((self.n_range, self.n_doppler))



        for target in targets:

            # ISAR图像：距离-多普勒

            r_idx = int(target.range_m / 10) % self.n_range

            # 多普勒与方位角相关

            d_idx = int((target.azimuth_rad + np.pi) / (2 * np.pi) * self.n_doppler) % self.n_doppler



            rcs = 10 ** (target.rcs_db / 10)

            image[r_idx, d_idx] += rcs



        return image



    def cs_isar_reconstruct(self, y: np.ndarray, n_pulses: int,

                            s: int = 20) -> np.ndarray:

        """CS重建ISAR图像"""

        # 构造测量矩阵

        A = np.random.randn(n_pulses, self.n_range * self.n_doppler) / np.sqrt(n_pulses)



        # OMP恢复

        x = np.zeros(self.n_range * self.n_doppler)

        support = []

        residual = y.copy()



        for _ in range(s):

            c = A.T @ residual

            best_idx = np.argmax(np.abs(c))

            if best_idx in support:

                break

            support.append(best_idx)



            A_support = A[:, support]

            x_support, _, _, _ = np.linalg.lstsq(A_support, y, rcond=None)



            residual = y - A_support @ x_support



        x[support] = x_support

        return x.reshape(self.n_range, self.n_doppler)





def test_radar_imaging():

    """测试压缩感知雷达成像"""

    np.random.seed(42)



    print("=== 压缩感知雷达成像测试 ===")



    # 创建雷达系统

    radar = CompressiveRadar(

        range_resolution_m=1.0,

        max_range_m=100.0,

        azimuth_range=np.pi

    )



    # 创建稀疏目标场景

    targets = [

        RadarTarget(range_m=30.0, azimuth_rad=0.3, rcs_db=10),

        RadarTarget(range_m=45.0, azimuth_rad=-0.5, rcs_db=15),

        RadarTarget(range_m=60.0, azimuth_rad=0.8, rcs_db=8),

        RadarTarget(range_m=75.0, azimuth_rad=-0.2, rcs_db=12),

    ]



    scene_true = radar.create_sparse_scene(targets)

    print(f"真实场景: {targets.__len__()} 个目标")



    # 稀疏采样角度

    n_pulses_total = 180

    n_pulses_cs = 30  # 压缩到30个脉冲



    pulse_angles_full = np.linspace(-np.pi/2, np.pi/2, n_pulses_total)

    pulse_angles_cs = np.random.choice(pulse_angles_full, n_pulses_cs, replace=False)



    print(f"全采样脉冲数: {n_pulses_total}")

    print(f"压缩采样脉冲数: {n_pulses_cs} (压缩比: {n_pulses_total/n_pulses_cs:.1f}x)")



    # 获取测量

    y_full, A_full = radar.forward_model(scene_true, pulse_angles_full)

    y_cs, A_cs = radar.forward_model(scene_true, pulse_angles_cs)



    # CS重建

    print("\n--- CS重建 ---")

    scene_cs = radar.cs_reconstruction(y_cs, A_cs, scene_true.shape, s=4, method="omp")



    # 匹配滤波器对比

    scene_mf = radar.matched_filter(y_cs, A_cs).reshape(scene_true.shape)



    # 计算误差

    err_cs = np.linalg.norm(scene_cs - scene_true) / np.linalg.norm(scene_true)

    err_mf = np.linalg.norm(scene_mf - scene_true) / np.linalg.norm(scene_true)



    print(f"CS重建误差: {err_cs:.4f}")

    print(f"匹配滤波器误差: {err_mf:.4f}")



    # ISAR测试

    print("\n--- ISAR成像测试 ---")

    isar = ISARImaging(n_range=64, n_doppler=64)



    isar_targets = [

        RadarTarget(range_m=20, azimuth_rad=0.0, rcs_db=10),

        RadarTarget(range_m=35, azimuth_rad=0.5, rcs_db=12),

    ]



    isar_image = isar.create_sparse_targets(isar_targets)

    print(f"ISAR场景: {isar_targets.__len__()} 个目标")



    # CS重建ISAR

    y_isar = isar.A if hasattr(isar, 'A') else np.random.randn(20, 64*64) / np.sqrt(20)

    # 简化：使用随机测量

    y_isar_meas = isar.A.dot(isar_image.flatten()) if hasattr(isar, 'A') else np.random.randn(20)



    # 简化的重建测试

    A_test = np.random.randn(20, 64*64) / np.sqrt(20)

    y_test = A_test @ isar_image.flatten()

    isar_rec = isar.cs_isar_reconstruct(y_test, n_pulses=20, s=5)



    print(f"ISAR重建完成")





if __name__ == "__main__":

    test_radar_imaging()

