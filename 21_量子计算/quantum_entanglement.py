# -*- coding: utf-8 -*-
"""
算法实现：21_量子计算 / quantum_entanglement

本文件实现 quantum_entanglement 相关的算法功能。
"""

import numpy as np  # 导入NumPy用于数值计算和矩阵运算


# =============================================================================
# 常量定义 - Constants
# =============================================================================

# 描述：全局常量，定义数学中常用的复数虚部单位 i = sqrt(-1)
I_COMPLEX = 1j  # 复数单位，用于构造复数态向量

# 描述：π的近似值，用于Bloch球等几何计算
PI = np.pi  # 圆周率

# 描述：sqrt(2)的预计算值，用于Bell态归一化和CHSH参数
SQRT2 = np.sqrt(2)  # 根号2


# =============================================================================
# Bell态定义 - Bell States Definition
# =============================================================================

def create_bell_states():
    """
    创建四个Bell态（最大纠缠态）的复数向量表示。

    Bell态是两个量子比特的最大纠缠态基矢，包含：
        |Φ+> = (|00> + |11>) / sqrt(2)   -- even parity, antisymmetric
        |Φ-> = (|00> - |11>) / sqrt(2)   -- odd parity, symmetric
        |Ψ+> = (|01> + |10>) / sqrt(2)   -- even parity, symmetric
        |Ψ-> = (|01> - |10>) / sqrt(2)   -- odd parity, antisymmetric

    Returns:
        dict: 键为Bell态名称，值为对应的numpy复数向量（形状 (4, 1)）

    Example:
        bells = create_bell_states()
        print(bells['PHI_PLUS'])  # 打印|Φ+>态向量
    """
    # 归一化系数：确保每个态向量的模为1
    norm_factor = 1.0 / SQRT2  # = 1/sqrt(2)

    # |Φ+> = (|00> + |11>) / sqrt(2)  -- 对称纠缠态，测量结果相同
    phi_plus = norm_factor * np.array([[1], [0], [0], [1]], dtype=complex)

    # |Φ-> = (|00> - |11>) / sqrt(2)  -- 单粒子测量沿z轴时关联减弱
    phi_minus = norm_factor * np.array([[1], [0], [0], [-1]], dtype=complex)

    # |Ψ+> = (|01> + |10>) / sqrt(2)  -- 两个粒子自旋相反时关联
    psi_plus = norm_factor * np.array([[0], [1], [1], [0]], dtype=complex)

    # |Ψ-> = (|01> - |10>) / sqrt(2)  -- 单粒子测量沿x/y轴时关联最强
    psi_minus = norm_factor * np.array([[0], [1], [-1], [0]], dtype=complex)

    # 返回字典，方便按名称索引
    return {
        'PHI_PLUS': phi_plus,    # |Φ+>
        'PHI_MINUS': phi_minus,  # |Φ->
        'PSI_PLUS': psi_plus,    # |Ψ+>
        'PSI_MINUS': psi_minus   # |Ψ->
    }


# =============================================================================
# EPR佯谬与局域隐变量理论 - EPR Paradox & Local Realism
# =============================================================================

def epr_argument():
    """
    阐述EPR佯谬的核心思想。

    EPR佯谬（Einstein-Podolsky-Rosen paradox，1935）：
        如果量子力学是完备的，则"幽灵般的超距作用"必然存在；
        若存在局域隐变量理论，则量子力学是不完备的。

    本函数返回描述EPR论点的字符串，说明：
        1. 关联性：两个粒子测量结果存在强关联
        2. 定域性：信息传递不超过光速
        3. 实在性：测量前粒子具有确定属性

    Returns:
        str: EPR佯谬的简要说明

    Note:
        Bell定理证明了局域隐变量理论无法重现量子预测，
        从而支持量子力学的非局域性（但不可用于超光速通信）。
    """
    epr_text = """
    EPR佯谬（Einstein-Podolsky-Rosen, 1935）
    ==========================================

    核心论点：
    假设 (A) 定域实在论：粒子属性在测量前已确定，且无超光速影响
    假设 (B) 量子力学完备

    若两个粒子相距很远且同时测量：
    - 量子预测：测量结果强关联（如自旋纠缠）
    - EPR论点：若B成立，则A必被违反 → 存在"幽灵般超距作用"

    Bell的贡献（1964）：
    - 构造局域隐变量理论可检验的不等式
    - 实验结果违反Bell不等式 → 定域隐变量理论被排除
    - 证明了量子纠缠的非局域性（但不允许超光速通信）

    结论：纠缠是真实存在的量子资源，非经典关联。
    """
    return epr_text


# =============================================================================
# CHSH不等式验证 - CHSH Inequality Verification
# =============================================================================

def chsh_correlator(state_vector, theta_a1=0, theta_a2=PI/4,
                    theta_b1=PI/8, theta_b2=-PI/8):
    """
    计算CHSH不等式的关联函数E(a, b)。

    CHSH不等式（Clauser-Horne-Shimony-Holt, 1969）：
        S = E(a1, b1) + E(a1, b2) + E(a2, b1) - E(a2, b2)
        局域隐变量理论约束：|S| ≤ 2
        量子力学允许：|S| ≤ 2*sqrt(2) ≈ 2.828（Tsirelson界）

    参数：
        state_vector: 两个量子比特的复数态向量（形状 (4,) 或 (4, 1)）
        theta_a1: Alice测量方向a1（弧度，默认0对应Pauli-Z基）
        theta_a2: Alice测量方向a2（弧度，默认π/4）
        theta_b1: Bob测量方向b1（弧度，默认π/8）
        theta_b2: Bob测量方向b2（弧度，默认-π/8）

    返回：
        float: CHSH参数S的值

    示例：
        >>> bells = create_bell_states()
        >>> S = chsh_correlator(bells['PHI_PLUS'].flatten())
        >>> print(f"CHSH S = {S:.4f}")  # 量子纠缠态应接近 2*sqrt(2)
    """
    # 将输入规范化为1维向量
    state = np.asarray(state_vector).flatten()

    # 确保态向量已归一化
    assert np.isclose(np.dot(state.conj(), state), 1.0), "态向量必须归一化"

    # 定义测量算符（用于在指定方向测量自旋）
    def measure_operator(angle):
        """
        创建指定测量方向的自旋算符。

        参数：
            angle: 测量方向与z轴的夹角（弧度）

        返回：
            complex: 4x4测量算符矩阵
        """
        # cos(θ) * σz + sin(θ) * σx，即沿指定方向的Pauli自旋测量
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        # Pauli矩阵：σz = [[1,0],[0,-1]]，σx = [[0,1],[1,0]]
        sigma_z = np.array([[1, 0], [0, -1]], dtype=complex)
        sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)

        # 单粒子测量算符：cos(θ)·σz + sin(θ)·σx
        single = cos_a * sigma_z + sin_a * sigma_x

        # 两粒子测量算符 = A ⊗ B（张量积）
        return np.kron(single, single)

    # 构建四个联合测量算符
    M_a1_b1 = measure_operator(theta_a1) @ measure_operator(theta_b1)
    M_a1_b2 = measure_operator(theta_a1) @ measure_operator(theta_b2)
    M_a2_b1 = measure_operator(theta_a2) @ measure_operator(theta_b1)
    M_a2_b2 = measure_operator(theta_a2) @ measure_operator(theta_b2)

    # 计算关联函数 E(a, b) = <ψ|M(a)⊗M(b)|ψ>
    # 关联函数衡量两个测量结果的相关程度
    E_a1b1 = np.real(np.vdot(state, M_a1_b1 @ state))
    E_a1b2 = np.real(np.vdot(state, M_a1_b2 @ state))
    E_a2b1 = np.real(np.vdot(state, M_a2_b1 @ state))
    E_a2b2 = np.real(np.vdot(state, M_a2_b2 @ state))

    # CHSH参数：经典极限2，量子极限2*sqrt(2)
    S = E_a1b1 + E_a1b2 + E_a2b1 - E_a2b2

    return S


def verify_chsh_inequality(state_vector):
    """
    验证给定量子态是否违反CHSH不等式。

    参数：
        state_vector: 量子态向量

    返回：
        dict: 包含经典边界、量子边界、实际S值及判断结果
    """
    S = chsh_correlator(state_vector.flatten())

    # 经典局域隐变量理论上限
    classical_bound = 2.0

    # 量子Tsirelson界（最大可能违反）
    quantum_bound = 2 * SQRT2

    # 判断是否违反经典边界（纠缠证据）
    is_violated = abs(S) > classical_bound

    return {
        'S': S,
        'classical_bound': classical_bound,
        'quantum_bound': quantum_bound,
        'is_entangled': is_violated,
        'quantum_advantage': abs(S) / classical_bound
    }


# =============================================================================
# 纠缠度量 - Entanglement Measures
# =============================================================================

def compute_density_matrix(state_vector):
    """
    计算纯态的密度矩阵表示。

    密度矩阵ρ = |ψ><ψ|，用于描述量子态的统计性质。

    参数：
        state_vector: 归一化的复数态向量

    返回：
        complex: 密度矩阵（形状 n×n）
    """
    # 将向量重塑为列向量
    psi = np.asarray(state_vector).reshape(-1, 1)

    # 密度矩阵 ρ = |ψ⟩⟨ψ|
    rho = psi @ psi.conj().T

    return rho


def partial_transpose(rho, subsystem=1):
    """
    计算二粒子密度矩阵的偏转置（Partial Transpose）。

    偏转置是判断纠缠的重要工具（PPT判据）：
        若ρ^{T_A}的特征值全部非负，则态可分（无纠缠）；
        若存在负特征值，则态必纠缠。

    参数：
        rho: 二粒子密度矩阵（形状 4×4）
        subsystem: 转置哪个子系统（0=A, 1=B，默认1转置B）

    返回：
        complex: 偏转置后的密度矩阵
    """
    # 获取维度（假设为2×2两粒子系统）
    d = int(np.sqrt(rho.shape[0]))  # 每个子系统的维度

    if subsystem == 0:
        # 转置第一个子系统（A的转置）
        # reshape为(d, d, d, d)后交换第0和2个指标，再展平
        rho_pt = rho.reshape(d, d, d, d).transpose(2, 1, 0, 3).reshape(4, 4)
    else:
        # 转置第二个子系统（B的转置）
        rho_pt = rho.reshape(d, d, d, d).transpose(0, 2, 1, 3).reshape(4, 4)

    return rho_pt


def ppt_criterion(state_vector):
    """
    使用PPT（Positive Partial Transpose）判据判断纠缠。

    参数：
        state_vector: 量子态向量

    返回：
        dict: 包含偏转置特征值和判断结果
    """
    rho = compute_density_matrix(state_vector)  # 计算密度矩阵
    rho_pt = partial_transpose(rho, subsystem=1)  # 对B子系统偏转置

    # 计算特征值（数值稳定性）
    eigenvalues = np.linalg.eigvalsh(rho_pt.real)

    # 判断：所有特征值非负 → 可分态；存在负特征值 → 纠缠态
    is_entangled = np.any(eigenvalues < -1e-10)

    return {
        'eigenvalues': eigenvalues,
        'min_eigenvalue': np.min(eigenvalues),
        'is_entangled': is_entangled,
        'ppt_passed': not is_entangled
    }


def concurrence(state_vector):
    """
    计算两 qubit 纯态的 concurrence（并发度）。

    Concurrence 是衡量纠缠程度的另一种度量：
        C = 0          → 无纠缠（可分态）
        C = 1          → 最大纠缠态
        0 < C < 1      → 部分纠缠

    计算公式：C = |<ψ|σy⊗σy|ψ*>|，其中σy是Pauli-Y矩阵。

    参数：
        state_vector: 两 qubit 纯态向量

    返回：
        float: concurrence值，范围[0, 1]
    """
    # 将向量转为列向量形式
    psi = np.asarray(state_vector).reshape(-1, 1)

    # Pauli-Y矩阵：σy = [[0,-i],[i,0]]
    sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)

    # 计算 ⟨ψ|σy⊗σy|ψ*⟩
    sigma_y_y = np.kron(sigma_y, sigma_y)  # 张量积 σy ⊗ σy

    # 态的复共轭
    psi_star = np.conj(psi)

    # 计算复数内积
    overlap = np.vdot(psi, sigma_y_y @ psi_star)

    # concurrence = |⟨ψ|σy⊗σy|ψ*⟩|
    C = np.abs(overlap)

    return C


def entanglement_entropy(state_vector):
    """
    计算冯·诺依曼纠缠熵（von Neumann entanglement entropy）。

    纠缠熵衡量系统与子系统之间的纠缠程度：
        S = -Tr(ρ_A log ρ_A) = -Tr(ρ_B log ρ_B)

    其中ρ_A = Tr_B(|ψ⟩⟨ψ|)是约化密度矩阵。

    参数：
        state_vector: 复合系统的纯态向量

    返回：
        float: 纠缠熵（ebits，即多少个最大纠缠对）
    """
    # 计算密度矩阵
    rho = compute_density_matrix(state_vector)

    # 对第二个子系统（A）求偏迹，得到约化密度矩阵
    # ρ_A = Tr_B(ρ) = sum_{i}<i_B| ρ |i_B>
    d = 2  # 单个qubit维度
    rho_a = np.zeros((d, d), dtype=complex)

    for i in range(d):
        # 投影到|i_B⟩上并求迹
        bra_i = np.zeros((1, d))
        bra_i[0, i] = 1.0
        ket_i = bra_i.T

        # <i| ρ |i> 对i求和
        proj_i = np.kron(np.eye(d), bra_i) @ rho @ np.kron(np.eye(d), ket_i)
        rho_a += proj_i

    # 计算冯·诺依曼熵 S = -Tr(ρ log ρ)
    # 对约化密度矩阵对角化
    eigenvalues = np.linalg.eigvalsh(rho_a.real)

    # 过滤掉为零的特征值（避免log(0)）
    eigenvalues = eigenvalues[eigenvalues > 1e-12]

    # 计算熵：S = -sum(λ log λ)
    entropy = -np.sum(eigenvalues * np.log2(eigenvalues))

    return entropy


# =============================================================================
# 主程序测试 - Main Test
# =============================================================================

if __name__ == '__main__':
    # 打印模块信息
    print("=" * 60)
    print("量子纠缠基础模块测试")
    print("=" * 60)

    # 1. 测试Bell态创建
    print("\n[1] Bell态创建测试")
    print("-" * 40)
    bells = create_bell_states()
    for name, vec in bells.items():
        print(f"  {name}: shape={vec.shape}, norm={np.linalg.norm(vec):.4f}")

    # 2. 测试EPR佯谬说明
    print("\n[2] EPR佯谬说明")
    print("-" * 40)
    print(epr_argument())

    # 3. 测试CHSH不等式
    print("\n[3] CHSH不等式验证")
    print("-" * 40)
    for name, vec in bells.items():
        result = verify_chsh_inequality(vec.flatten())
        status = "✅ 违反（纠缠）" if result['is_entangled'] else "❌ 未违反"
        print(f"  {name}: S={result['S']:.4f}, 量子优势={result['quantum_advantage']:.2f}x {status}")

    # 4. 测试PPT判据
    print("\n[4] PPT判据（偏转置）")
    print("-" * 40)
    test_states = {
        'PHI_PLUS': bells['PHI_PLUS'],
        'PHI_MINUS': bells['PHI_MINUS'],
        'PRODUCT_00': np.array([[1], [0], [0], [0]])  # 可分态 |00>
    }
    for name, vec in test_states.items():
        result = ppt_criterion(vec.flatten())
        print(f"  {name}: min_eigenvalue={result['min_eigenvalue']:.4f}, 纠缠={result['is_entangled']}")

    # 5. 测试纠缠度量
    print("\n[5] 纠缠度量")
    print("-" * 40)
    for name, vec in bells.items():
        c = concurrence(vec.flatten())
        s = entanglement_entropy(vec.flatten())
        print(f"  {name}: concurrence={c:.4f}, 纠缠熵={s:.4f} ebits")

    # 6. 物理演示：单粒子测量无关联
    print("\n[6] 局域隐变量模拟（对比）")
    print("-" * 40)
    print("  假设每个粒子有确定的自旋方向（局域实在论）")
    print("  计算10000次随机测量下的CHSH参数...")

    # 局域隐变量模拟：每个粒子有固定角度
    np.random.seed(42)
    S_samples = []
    for _ in range(10000):
        # 每个粒子随机选择隐藏角度
        lambda_a = np.random.uniform(0, 2 * PI)
        lambda_b = np.random.uniform(0, 2 * PI)

        # 局域决策规则（模拟经典关联）
        def local_result(angle, hidden):
            return 1 if np.cos(angle - hidden) > 0 else -1

        # 测量四个设置
        r_a1 = local_result(0, lambda_a)
        r_a2 = local_result(PI / 4, lambda_a)
        r_b1 = local_result(PI / 8, lambda_b)
        r_b2 = local_result(-PI / 8, lambda_b)

        # 关联函数
        E = r_a1 * r_b1
        S_samples.append(E)

    classical_S = np.mean(S_samples) * 4  # CHSH参数
    print(f"  局域隐变量模型 S = {classical_S:.4f} (经典边界: 2.0)")
    print(f"  量子纠缠态 |Φ+> S = {verify_chsh_inequality(bells['PHI_PLUS'].flatten())['S']:.4f} (量子界: {2*SQRT2:.4f})")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
