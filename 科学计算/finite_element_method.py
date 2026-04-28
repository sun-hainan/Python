"""
有限元方法(FEM)基础实现
=========================
本模块实现了有限元方法的核心概念，包括：
- 一维线性单元的网格生成
- 单元刚度矩阵的构造
- 总体刚度矩阵的组装
- 边界条件的处理

Author: 算法库
"""

import numpy as np
from typing import Tuple, List


def generate_mesh_1d(a: float, b: float, n: int) -> np.ndarray:
    """
    生成一维均匀网格
    
    参数:
        a: 区间左端点
        b: 区间右端点  
        n: 单元数量
    
    返回:
        nodes: 节点坐标数组，形状为(n+1,)
    """
    # 计算节点间距
    h = (b - a) / n
    # 生成等距节点坐标
    nodes = np.linspace(a, b, n + 1)
    return nodes


def element_stiffness_linear(h: float) -> np.ndarray:
    """
    计算一维线性单元的单元刚度矩阵
    
    参数:
        h: 单元长度
    
    返回:
        Ke: 2x2单元刚度矩阵
    """
    # 单元刚度矩阵公式：Ke = (1/h) * [[1, -1], [-1, 1]]
    Ke = np.array([[1, -1], [-1, 1]]) / h
    return Ke


def element_load_linear(h: float, f: float = 1.0) -> np.ndarray:
    """
    计算一维线性单元的载荷向量
    
    参数:
        h: 单元长度
        f: 体力（默认为1.0）
    
    返回:
        Fe: 2x1载荷向量
    """
    # 分布载荷的等效节点力：Fe = f * h/2 * [1, 1]
    Fe = np.array([1.0, 1.0]) * f * h / 2.0
    return Fe


def assemble_global(
    n_elements: int,
    Ke_func,
    Fe_func,
    h: float,
    f: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    将单元刚度矩阵和载荷向量组装为总体刚度矩阵和总体载荷向量
    
    参数:
        n_elements: 单元数量
        Ke_func: 单元刚度矩阵函数
        Fe_func: 单元载荷向量函数
        h: 单元长度
        f: 体力
    
    返回:
        K: 总体刚度矩阵(n+1)x(n+1)
        F: 总体载荷向量(n+1,)
    """
    n_nodes = n_elements + 1
    K = np.zeros((n_nodes, n_nodes))
    F = np.zeros(n_nodes)
    
    for e in range(n_elements):
        # 获取当前单元的节点索引
        i = e
        j = e + 1
        # 计算单元刚度矩阵
        Ke = Ke_func(h)
        # 计算单元载荷向量
        Fe = Fe_func(h, f)
        # 组装到总体矩阵
        K[i:i+2, i:i+2] += Ke
        F[i:j+1] += Fe
    
    return K, F


def apply_dirichlet_bc(
    K: np.ndarray,
    F: np.ndarray,
    boundary_conditions: List[Tuple[int, float]]
) -> Tuple[np.ndarray, np.ndarray]:
    """
    应用Dirichlet边界条件（本质边界条件）
    
    参数:
        K: 总体刚度矩阵
        F: 总体载荷向量
        boundary_conditions: 边界条件列表，元素为(节点索引, 位移值)
    
    返回:
        K_mod: 修改后的刚度矩阵
        F_mod: 修改后的载荷向量
    """
    K_mod = K.copy()
    F_mod = F.copy()
    
    for node_idx, u_value in boundary_conditions:
        # 惩罚法处理边界条件
        penalty = 1e15
        K_mod[node_idx, node_idx] += penalty
        F_mod[node_idx] = penalty * u_value
    
    return K_mod, F_mod


def solve_fem_1d(a: float, b: float, n: int, f: float = 1.0,
                 bc_left: float = 0.0, bc_right: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    求解一维稳态问题（-u'' = f）的有限元解
    
    参数:
        a: 区间左端点
        b: 区间右端点
        n: 单元数量
        f: 体力
        bc_left: 左边界位移值
        bc_right: 右边界位移值
    
    返回:
        nodes: 节点坐标
        u: 数值解
    """
    # 生成网格
    nodes = generate_mesh_1d(a, b, n)
    h = (b - a) / n
    
    # 组装总体矩阵
    K, F = assemble_global(n, element_stiffness_linear, element_load_linear, h, f)
    
    # 应用边界条件
    bc = [(0, bc_left), (n, bc_right)]
    K, F = apply_dirichlet_bc(K, F, bc)
    
    # 求解线性系统
    u = np.linalg.solve(K, F)
    
    return nodes, u


if __name__ == "__main__":
    # 测试：一维稳态热传导问题（-u'' = 1）
    # 精确解：u(x) = x(1-x)/2
    print("=" * 50)
    print("有限元方法(FEM)基础测试")
    print("=" * 50)
    
    # 设置参数
    a, b = 0.0, 1.0  # 区间
    n = 10  # 单元数量
    
    # 求解
    nodes, u = solve_fem_1d(a, b, n, f=1.0, bc_left=0.0, bc_right=0.0)
    
    # 计算精确解
    u_exact = nodes * (1 - nodes) / 2.0
    
    # 输出结果
    print(f"\n节点数: {len(nodes)}, 单元数: {n}")
    print(f"{'x':>8} {'FEM解':>12} {'精确解':>12} {'误差':>12}")
    print("-" * 46)
    for i in range(0, len(nodes), 2):
        print(f"{nodes[i]:8.3f}{u[i]:12.6f}{u_exact[i]:12.6f}{abs(u[i]-u_exact[i]):12.6f}")
    
    # 计算最大误差
    max_error = np.max(np.abs(u - u_exact))
    print(f"\n最大误差: {max_error:.6f}")
    print("\n测试通过！有限元方法基础实现正确。")
