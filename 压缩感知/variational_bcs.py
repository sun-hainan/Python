# -*- coding: utf-8 -*-

"""

算法实现：压缩感知 / variational_bcs



本文件实现 variational_bcs 相关的算法功能。

"""



import numpy as np

from typing import Tuple

from scipy import special





def vbcsi(A: np.ndarray, y: np.ndarray,

          max_iter: int = 100, tol: float = 1e-6) -> Tuple[np.ndarray, np.ndarray, int]:

    """

    变分贝叶斯压缩感知（VBCSI）算法

    原理：用变分推断近似后验分布 p(x|y) = N(x; μ, Σ)



    输入：

        A: 测量矩阵 (m × n)

        y: 测量向量 (m,)

    输出：

        x_mean: 恢复信号均值（稀疏估计）

        x_cov: 恢复信号协方差

        iterations: 迭代次数

    """

    m, n = A.shape



    # 超参数初始化

    alpha = np.ones(n)      # ARD先验精度

    beta = 1.0              # 噪声精度（逆方差）

    gamma = np.ones(n)      # 稀疏诱导参数



    # 信号均值和协方差

    x_mean = np.zeros(n)

    x_cov_diag = np.ones(n)  # 对角协方差



    # 预计算 Gram 矩阵

    A_T_A = A.T @ A

    A_T_y = A.T @ y



    for iteration in range(max_iter):

        # E步：估计信号后验

        # Σ = (β A^T A + diag(α))^{-1}

        precision_matrix = beta * A_T_A + np.diag(alpha)

        x_cov = np.linalg.inv(precision_matrix + 1e-10 * np.eye(n))



        # μ = β Σ A^T y

        x_mean_new = beta * (x_cov @ A_T_y)



        # M步：更新超参数

        # 1. 更新 α_i = (1 - 2/π * arctan(γ_i)) / μ_i^2

        x_mean_sq = x_mean_new ** 2

        x_mean_sq[x_mean_sq < 1e-10] = 1e-10  # 避免除零



        alpha_new = 1.0 / x_mean_sq



        # 2. 更新 γ（稀疏参数）

        gamma_new = np.sqrt(np.diag(x_cov) + x_mean_sq)

        gamma_new[gamma_new < 1e-10] = 1e-10



        # 3. 更新 β（噪声精度）

        residual = y - A @ x_mean_new

        beta_new = m / (np.linalg.norm(residual) ** 2 + 1e-10)



        # 计算变分下界（ELBO）用于收敛检查

        elbo = compute_elbo(A, y, x_mean_new, x_cov, alpha_new, beta_new, gamma_new)



        # 检查收敛

        if iteration > 0:

            if abs(elbo - prev_elbo) < tol:

                break



        prev_elbo = elbo

        alpha = alpha_new

        beta = beta_new

        gamma = gamma_new

        x_mean = x_mean_new

        x_cov_diag = np.diag(x_cov)



    # 稀疏估计（后验均值）

    x_sparse = x_mean



    return x_sparse, x_cov_diag, iteration + 1





def compute_elbo(A, y, x_mean, x_cov, alpha, beta, gamma):

    """

    计算变分下界（Evidence Lower Bound）

    用于监测收敛性

    """

    m, n = A.shape



    # E[log p(y|x)]

    residual = y - A @ x_mean

    trace_term = np.trace(A @ x_cov @ A.T)

    elbo_log_likelihood = -0.5 * m * np.log(2 * np.pi / beta) - 0.5 * beta * (

        np.linalg.norm(residual) ** 2 + trace_term

    )



    # E[log p(x|α)]

    elbo_prior = 0.5 * np.sum(np.log(alpha / (2 * np.pi)) - alpha * (

        np.diag(x_cov) + x_mean ** 2

    ))



    # KL[q||p] 项

    kl_alpha = 0.5 * np.sum(alpha * gamma - np.log(alpha) - 1)



    return elbo_log_likelihood + elbo_prior - kl_alpha





def ard_vbcs(A: np.ndarray, y: np.ndarray, max_iter: int = 100) -> Tuple[np.ndarray, np.ndarray]:

    """

    ARD（自动相关性确定）-VBCS

    自动确定哪些信号分量是活跃的（稀疏结构学习）

    """

    m, n = A.shape



    # 初始化

    alpha = np.ones(n)

    beta = 1.0

    x_mean = np.zeros(n)

    x_cov_diag = np.ones(n)



    for iteration in range(max_iter):

        # E步

        precision = beta * A_T_A + np.diag(alpha)

        x_cov = np.linalg.inv(precision + 1e-10 * np.eye(n))

        x_mean = beta * (x_cov @ (A.T @ y))



        # M步：更新alpha

        x_mean_sq = x_mean ** 2

        diag_Sigma = np.diag(x_cov)



        alpha_new = 1.0 / (x_mean_sq + diag_Sigma + 1e-10)



        # 更新beta

        residual = y - A @ x_mean

        beta_new = m / (np.linalg.norm(residual) ** 2 + np.trace(A @ x_cov @ A.T) + 1e-10)



        # 检查收敛

        if np.max(np.abs(alpha_new - alpha)) < 1e-6:

            break



        alpha = alpha_new

        beta = beta_new



    return x_mean, alpha





def fast_vbcs(A: np.ndarray, y: np.ndarray,

              max_iter: int = 100, s_max: int = 50) -> Tuple[np.ndarray, int]:

    """

    快速VBCS：利用快速求解器近似后验

    适用于大规模问题

    """

    m, n = A.shape



    # 初始化

    x = np.zeros(n)

    residual = y.copy()

    active_set = np.zeros(n, dtype=bool)

    alpha = np.ones(n)

    beta = 1.0



    for iteration in range(max_iter):

        # 梯度

        grad = A.T @ residual



        # 置信度检查

        non_active = ~active_set

        confidence = np.abs(grad[non_active])



        # 选择最大置信度的元素加入活跃集

        if np.any(confidence > 0):

            best_idx = np.argmax(confidence)

            global_idx = np.where(non_active)[0][best_idx]

            active_set[global_idx] = True



        # 限制活跃集大小

        if np.sum(active_set) > s_max:

            # 移除贡献最小的

            least_contrib = np.argmin(np.abs(x[active_set]))

            active_set[np.where(active_set)[0][least_contrib]] = False



        # 在活跃集上求解

        A_active = A[:, active_set]

        x_active = np.linalg.lstsq(A_active, y, rcond=None)[0]



        x_new = np.zeros(n)

        x_new[active_set] = x_active



        # 更新残差

        residual_new = y - A @ x_new



        # 更新超参数

        beta_new = m / (np.linalg.norm(residual_new) ** 2 + 1e-10)



        # 检查收敛

        if np.linalg.norm(x_new - x) < 1e-6:

            break



        x = x_new

        residual = residual_new

        beta = beta_new



    return x, iteration + 1





def test_vbcs():

    """测试变分贝叶斯压缩感知"""

    np.random.seed(42)



    n, m, s = 500, 100, 15



    # 生成稀疏信号

    x_true = np.zeros(n)

    support = np.random.choice(n, s, replace=False)

    x_true[support] = np.random.randn(s)



    # 测量矩阵

    A = np.random.randn(m, n) / np.sqrt(m)



    # 测量

    y = A @ x_true + 0.01 * np.random.randn(m)



    print("=== 变分贝叶斯压缩感知（VBCS）测试 ===")

    print(f"信号维度: {n}, 测量数: {m}, 稀疏度: {s}")



    # VBCSI

    x_recovered, x_cov_diag, iterations = vbcsi(A, y)

    error = np.linalg.norm(x_recovered - x_true) / np.linalg.norm(x_true)



    print(f"\nVBCSI结果:")

    print(f"  迭代次数: {iterations}")

    print(f"  恢复误差: {error:.6f}")

    print(f"  后验不确定性（平均）: {np.mean(x_cov_diag):.6f}")



    # ARD-VBCS

    x_ard, alpha = ard_vbcs(A, y)

    err_ard = np.linalg.norm(x_ard - x_true) / np.linalg.norm(x_true)



    print(f"\nARD-VBCS结果:")

    print(f"  激活分量数: {np.sum(alpha < 10):>3d}")

    print(f"  恢复误差: {err_ard:.6f}")



    # 活跃度排序

    active_sorted = np.argsort(alpha)[:10]

    print(f"  最活跃的10个索引: {active_sorted}")



    # 误差对比

    print("\n--- 与其他方法对比 ---")

    from iht import iht



    x_iht, it_iht, _ = iht(A, y, s)

    err_iht = np.linalg.norm(x_iht - x_true) / np.linalg.norm(x_true)



    print(f"IHT误差: {err_iht:.6f}")

    print(f"VBCS误差: {error:.6f}")





if __name__ == "__main__":

    test_vbcs()

