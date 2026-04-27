# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / total_variation



本文件实现 total_variation 相关的算法功能。

"""



import numpy as np

from typing import Tuple, Callable

from scipy import ndimage





class TotalVariation:

    """

    全变分类

    TV(x) = ||∇x||₁ = Σ |∇x_i|



    梯度算子 ∇：计算空间梯度（离散差分）

    """



    @staticmethod

    def gradient_2d(image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """

        计算2D图像的梯度

        ∇x[i,j] = x[i+1,j] - x[i,j]  (x方向)

        ∇y[i,j] = x[i,j+1] - x[i,j]  (y方向)

        """

        # x方向梯度（右邻居 - 当前）

        grad_x = np.zeros_like(image)

        grad_x[:-1, :] = image[1:, :] - image[:-1, :]



        # y方向梯度（下邻居 - 当前）

        grad_y = np.zeros_like(image)

        grad_y[:, :-1] = image[:, 1:] - image[:, :-1]



        return grad_x, grad_y



    @staticmethod

    def gradient_1d(x: np.ndarray) -> np.ndarray:

        """计算1D信号的梯度"""

        grad = np.zeros_like(x)

        grad[:-1] = x[1:] - x[:-1]

        return grad



    @staticmethod

    def tv_norm(image: np.ndarray) -> float:

        """计算TV范数：||∇x||₁"""

        grad_x, grad_y = TotalVariation.gradient_2d(image)

        return np.sum(np.abs(grad_x)) + np.sum(np.abs(grad_y))



    @staticmethod

    def anisotropic_tv(image: np.ndarray) -> float:

        """

        各向异性TV（L1范数，梯度方向独立惩罚）

        TV_aniso(x) = Σ |∇x_i| + |∇y_i|

        """

        grad_x, grad_y = TotalVariation.gradient_2d(image)

        return np.sum(np.abs(grad_x)) + np.sum(np.abs(grad_y))



    @staticmethod

    def isotropic_tv(image: np.ndarray) -> float:

        """

        各向同性TV（欧几里得范数，梯度幅度惩罚）

        TV_iso(x) = Σ sqrt(∇x_i² + ∇y_i²)

        """

        grad_x, grad_y = TotalVariation.gradient_2d(image)

        return np.sum(np.sqrt(grad_x ** 2 + grad_y ** 2))





class TVRecovery:

    """

    全变分最小化恢复

    min 0.5 ||Ax - y||² + λ ||∇x||₁

    """



    def __init__(self, A: np.ndarray, y: np.ndarray):

        self.A = A

        self.y = y

        self.m, self.n = A.shape



    def forward_gradient(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:

        """前向梯度（用于TV项的梯度）"""

        return TotalVariation.gradient_2d(x.reshape(self._guess_shape()))



    def _guess_shape(self) -> tuple:

        """猜测图像形状"""

        h = int(np.sqrt(self.n))

        return (h, self.n // h)





class PrimalDualTV:

    """

    原对偶算法求解TV正则化问题

    min_x 0.5||Ax - y||² + λ||∇x||₁



    使用Chambolle-Pock算法

    """



    def __init__(self, A: np.ndarray, y: np.ndarray,

                 lambda_tv: float = 0.1,

                 max_iter: int = 500,

                 tau: float = 0.02,

                 sigma: float = 0.02,

                 theta: float = 1.0):

        self.A = A

        self.y = y

        self.lambda_tv = lambda_tv

        self.max_iter = max_iter

        self.tau = tau      # 原步长

        self.sigma = sigma  # 对偶步长

        self.theta = theta  # 外推参数



    def solve(self, x0: np.ndarray = None) -> Tuple[np.ndarray, list[float]]:

        """

        求解TV正则化问题



        输出：

            x: 恢复信号

            objective_history: 目标函数值历史

        """

        m, n = self.A.shape



        # 初始化

        if x0 is None:

            x = np.zeros(n)

        else:

            x = x0.copy()



        # 对偶变量（梯度域）

        p_x = np.zeros(n)

        p_y = np.zeros(n)



        # 辅助变量

        x_bar = x.copy()



        objective_history = []



        ATA = self.A.T @ self.A

        ATy = self.A.T @ self.y



        for iteration in range(self.max_iter):

            # 1. 对偶更新（梯度下降）

            # ∇E(x_bar)的近似：使用前一个x

            grad_E = ATA @ x - ATy



            # TV项的梯度

            grad_x, grad_y = TotalVariation.gradient_2d(x_bar.reshape(int(np.sqrt(n)), -1))

            grad_x = grad_x.flatten()

            grad_y = grad_y.flatten()



            p_x_new = p_x + self.sigma * (grad_x + grad_E / self.lambda_tv)

            p_y_new = p_y + self.sigma * grad_y



            # 投影（约束 |p| ≤ 1）

            p_norm = np.sqrt(p_x_new ** 2 + p_y_new ** 2)

            p_norm = np.maximum(p_norm, 1e-10)

            p_x = p_x_new / p_norm

            p_y = p_y_new / p_norm



            # 2. 原变量更新

            # x_new = x - tau * (A^T(Ax - y) + λ * div(p))

            div_p_x = np.zeros_like(p_x)

            div_p_y = np.zeros_like(p_y)



            # 简化的散度计算（边界处理）

            p_x_shaped = p_x.reshape(int(np.sqrt(n)), -1)

            p_y_shaped = p_y.reshape(int(np.sqrt(n)), -1)



            div_p_x[1:] = p_x_shaped[:-1, :]

            div_p_y[:, 1:] = p_y_shaped[:, :-1]



            div_p = (div_p_x + div_p_y).flatten()



            x_new = x - self.tau * (ATA @ x - ATy + self.lambda_tv * div_p)



            # 3. 外推

            x_bar = x_new + self.theta * (x_new - x)



            x = x_new



            # 计算目标函数值

            if iteration % 10 == 0:

                residual = self.A @ x - self.y

                data_fidelity = 0.5 * np.sum(residual ** 2)

                tv = TotalVariation.tv_norm(x.reshape(int(np.sqrt(n)), -1))

                objective = data_fidelity + self.lambda_tv * tv

                objective_history.append(objective)



        return x, objective_history





class SplitBregmanTV:

    """

    分裂Bregman方法求解TV问题

    min ||u||₁ s.t. ||Ax - y||² ≤ ε



    通过Bregman迭代将约束转化为惩罚项

    """



    def __init__(self, A: np.ndarray, y: np.ndarray,

                 mu: float = 1.0,

                 lambda_tv: float = 0.1,

                 max_iter: int = 100):

        self.A = A

        self.y = y

        self.mu = mu

        self.lambda_tv = lambda_tv

        self.max_iter = max_iter



    def shrink(self, x: np.ndarray, kappa: float) -> np.ndarray:

        """软阈值（shrink operator）"""

        return np.sign(x) * np.maximum(np.abs(x) - kappa, 0)



    def solve(self, x0: np.ndarray = None) -> Tuple[np.ndarray, list[float]]:

        """分裂Bregman迭代"""

        m, n = self.A.shape



        if x0 is None:

            x = np.zeros(n)

        else:

            x = x0.copy()



        # Bregman变量

        b = np.zeros(n)



        # 辅助变量

        d = np.zeros(n)  # 用于TV项



        objective_history = []



        for iteration in range(self.max_iter):

            # 1. x-子问题（最小二乘）

            # argmin_x ||Ax - y||² + μ/2 ||x - d + b||²

            # 解：A^T A + μ I 的系统

            H = self.A.T @ self.A + self.mu * np.eye(n)

            rhs = self.A.T @ self.y + self.mu * (d - b)

            x = np.linalg.solve(H, rhs)



            # 2. d-子问题（TV shrinkage）

            # argmin_d λ||d||₁ + μ/2 ||x - d + b||²

            grad_x, grad_y = TotalVariation.gradient_2d(x.reshape(int(np.sqrt(n)), -1))



            # TV范数的梯度（简化处理）

            d_temp = (x - b).flatten()  # 简化的d更新



            # 软阈值

            d = self.shrink(d_temp, self.lambda_tv / self.mu)



            # 3. b-更新（Bregman迭代）

            b = b + x - d



            # 目标值

            if iteration % 10 == 0:

                residual = self.A @ x - self.y

                obj = 0.5 * np.sum(residual ** 2) + self.lambda_tv * np.sum(np.abs(d))

                objective_history.append(obj)



        return x, objective_history





def test_tv_recovery():

    """测试TV图像恢复"""

    np.random.seed(42)



    print("=== 全变分（TV）最小化测试 ===")



    # 创建测试图像（分段平滑）

    print("\n--- 创建测试图像 ---")

    n = 64

    image_true = np.zeros((n, n))



    # 添加几个矩形区域（分段常数）

    image_true[10:25, 10:30] = 100

    image_true[30:50, 25:45] = 150

    image_true[15:35, 40:55] = 80



    print(f"图像尺寸: {image_true.shape}")

    print(f"TV范数: {TotalVariation.tv_norm(image_true):.2f}")



    # 测量矩阵（随机采样）

    m = 400  # 测量数

    A = np.random.randn(m, n * n) / np.sqrt(m)



    # 测量（添加噪声）

    y = A @ image_true.flatten() + 0.01 * np.random.randn(m)



    print(f"测量数: {m} / {n*n} (压缩比: {n*n/m:.1f}x)")



    # TV恢复（Primal-Dual）

    print("\n--- Primal-Dual TV恢复 ---")

    pd_solver = PrimalDualTV(A, y, lambda_tv=5.0, max_iter=200)

    image_pd, obj_pd = pd_solver.solve()



    err_pd = np.linalg.norm(image_pd - image_true.flatten()) / np.linalg.norm(image_true.flatten())

    print(f"Primal-Dual恢复误差: {err_pd:.4f}")

    print(f"目标函数收敛: {obj_pd[-1]:.2f}")



    # TV恢复（Split Bregman）

    print("\n--- Split Bregman TV恢复 ---")

    sb_solver = SplitBregmanTV(A, y, mu=1.0, lambda_tv=5.0, max_iter=100)

    image_sb, obj_sb = sb_solver.solve()



    err_sb = np.linalg.norm(image_sb - image_true.flatten()) / np.linalg.norm(image_true.flatten())

    print(f"Split Bregman恢复误差: {err_sb:.4f}")



    # 各向同性vs各向异性TV

    print("\n--- TV类型对比 ---")

    print(f"各向同性TV (image_true): {TotalVariation.isotropic_tv(image_true):.2f}")

    print(f"各向异性TV (image_true): {TotalVariation.anisotropic_tv(image_true):.2f}")



    # 误差对比（与简单的L2最小化对比）

    print("\n--- 与无TV约束的L2恢复对比 ---")

    x_l2 = np.linalg.lstsq(A, y, rcond=None)[0]

    err_l2 = np.linalg.norm(x_l2 - image_true.flatten()) / np.linalg.norm(image_true.flatten())

    print(f"纯L2恢复误差: {err_l2:.4f}")

    print(f"TV恢复误差: {err_pd:.4f}")

    print(f"TV改善: {(err_l2 - err_pd) / err_l2 * 100:.1f}%")



    # TV梯度可视化

    print("\n--- 梯度场分析 ---")

    grad_x, grad_y = TotalVariation.gradient_2d(image_true)

    active_grad_x = np.sum(np.abs(grad_x) > 1e-6)

    active_grad_y = np.sum(np.abs(grad_y) > 1e-6)

    print(f"梯度非零数: x方向={active_grad_x}, y方向={active_grad_y}")

    print(f"梯度稀疏度: {(active_grad_x + active_grad_y) / (n*n*2) * 100:.1f}%")





if __name__ == "__main__":

    test_tv_recovery()

