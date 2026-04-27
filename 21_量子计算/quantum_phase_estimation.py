# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_phase_estimation

本文件实现 quantum_phase_estimation 相关的算法功能。
"""

# =============================================================================
# 验证：使用T gate验证（φ=1/4）
# =============================================================================

def verify_t_gate():
    """
    使用T门验证QPE算法。
    T|1⟩ = e^{iπ/4}|1⟩ = e^{2πi·(1/8)}|1⟩
    所以 φ = 1/8 = 0.125
    """
    print("=" * 60)
    print("验证：QPE估计T门的相位")
    print("=" * 60)

    # T门的矩阵表示
    T = np.array([[1, 0], [0, np.exp(1j * PI / 4)]], dtype=complex)

    # 特征向量|1⟩（对应特征值 e^{iπ/4}）
    eigenstate = np.array([0, 1], dtype=complex)

    # 设置精度
    n_precision_bits = 8  # 精度 1/256

    estimated_phase = quantum_phase_estimation(T, eigenstate, n_precision_bits)

    true_phase = 1 / 8
    error = abs(estimated_phase - true_phase)

    print(f"[验证] 真实相位: {true_phase:.6f}")
    print(f"[验证] 估计相位: {estimated_phase:.6f}")
    print(f"[验证] 绝对误差: {error:.6f} (精度目标: ±{1/2**n_precision_bits:.6f})")
    print(f"[验证] {'✓ 通过' if error < 1/2**n_precision_bits else '✗ 未通过'}精度检验")


if __name__ == '__main__':
    verify_t_gate()
