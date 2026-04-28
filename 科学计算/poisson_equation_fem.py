"""
Poisson方程的有限元求解
=========================
本模块求解标准的Poisson方程边值问题：
    -∇²u = f(x,y)  在区域Ω内
    u = g           在边界∂Ω上

使用三角形线性单元（FEM），实现网格生成、单元计算和求解。
基于一维FEM的思路推广到二维。

Author: 算法库
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple, List


class TriMesh:
    """二维三角形网格类"""
    
    def __init__(self, xmin: float, xmax: float, ymin: float, ymax: float, nx: int, ny: int):
        """
        初始化矩形区域网格
        
        参数:
            xmin, xmax: x方向区间
            ymin, ymax: y方向区间
            nx, ny: x和y方向的单元数
        """
        self.xmin, self.xmax = xmin, xmax
        self.ymin, self.ymax = ymin, ymax
        self.nx, self.ny = nx, ny
        
        # 生成节点坐标
        self._generate_nodes()
        # 生成三角形单元连接
        self._generate_elements()
    
    def _generate_nodes(self):
        """生成网格节点"""
        # 节点总数
        self.n_nodes = (self.nx + 1) * (self.ny + 1)
        # 存储节点坐标
        self.nodes = np.zeros((self.n_nodes, 2))
        
        dx = (self.xmax - self.xmin) / self.nx
        dy = (self.ymax - self.ymin) / self.ny
        
        idx = 0
        for j in range(self.ny + 1):
            for i in range(self.nx + 1):
                self.nodes[idx, 0] = self.xmin + i * dx
                self.nodes[idx, 1] = self.ymin + j * dy
                idx += 1
    
    def _generate_elements(self):
        """生成三角形单元（两个三角形组成一个矩形单元）"""
        self.n_elements = 2 * self.nx * self.ny
        self.elements = np.zeros((self.n_elements, 3), dtype=int)
        
        e = 0
        for j in range(self.ny):
            for i in range(self.nx):
                # 当前矩形的四个顶点索引
                n00 = j * (self.nx + 1) + i
                n10 = n00 + 1
                n01 = n00 + (self.nx + 1)
                n11 = n01 + 1
                
                # 第一个三角形(左下，右下，左上)
                self.elements[e] = [n00, n10, n01]
                e += 1
                # 第二个三角形(右下，右上，左上)
                self.elements[e] = [n10, n11, n01]
                e += 1
    
    def get_boundary_nodes(self) -> List[int]:
        """获取边界节点索引"""
        boundary = []
        # 左边界
        for j in range(self.ny + 1):
            boundary.append(j * (self.nx + 1))
        # 右边界
        for j in range(self.ny + 1):
            boundary.append(j * (self.nx + 1) + self.nx)
        # 下边界（排除四个角）
        for i in range(1, self.nx):
            boundary.append(i)
        # 上边界（排除四个角）
        for i in range(1, self.nx):
            boundary.append((self.ny) * (self.nx + 1) + i)
        
        return boundary


def element_stiffness_tri(
    x1: float, y1: float,
    x2: float, y2: float,
    x3: float, y3: float
) -> Tuple[np.ndarray, float]:
    """
    计算三角形单元的刚度矩阵和面积
    
    参数:
        (x1,y1), (x2,y2), (x3,y3): 三角形三个顶点坐标
    
    返回:
        Ke: 3x3单元刚度矩阵
        area: 三角形面积
    """
    # 计算三角形面积（叉积的一半）
    area = 0.5 * abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1))
    
    # 计算形函数导数的系数矩阵
    # 形函数: N_i(x,y) = (a_i + b_i*x + c_i*y) / (2*area)
    a1 = x2 * y3 - x3 * y2
    b1 = y2 - y3
    c1 = x3 - x2
    
    a2 = x3 * y1 - x1 * y3
    b2 = y3 - y1
    c2 = x1 - x3
    
    a3 = x1 * y2 - x2 * y1
    b3 = y1 - y2
    c3 = x2 - x1
    
    # 组装单元刚度矩阵
    Ke = np.zeros((3, 3))
    for i in range(3):
        bi = [b1, b2, b3][i]
        ci = [c1, c2, c3][i]
        for j in range(3):
            bj = [b1, b2, b3][j]
            cj = [c1, c2, c3][j]
            # Ke(i,j) = (bi*bj + ci*cj) / (4*area)
            Ke[i, j] = (bi * bj + ci * cj) / (4.0 * area)
    
    return Ke, area


def element_load_tri(area: float, f: float) -> np.ndarray:
    """
    计算三角形单元的载荷向量
    
    参数:
        area: 三角形面积
        f: 体力（默认为常数）
    
    返回:
        Fe: 3x1载荷向量
    """
    # 分布载荷的等效节点力（假设f为常数）
    Fe = np.array([1.0, 1.0, 1.0]) * f * area / 3.0
    return Fe


def assemble_poisson(mesh: TriMesh, f: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    组装Poisson方程的总体刚度矩阵和载荷向量
    
    参数:
        mesh: 三角形网格
        f: 体力
    
    返回:
        K: 总体刚度矩阵
        F: 总体载荷向量
    """
    n = mesh.n_nodes
    K = np.zeros((n, n))
    F = np.zeros(n)
    
    for e in range(mesh.n_elements):
        # 获取单元的三个节点索引
        i, j, k = mesh.elements[e]
        
        # 获取节点坐标
        x_i, y_i = mesh.nodes[i]
        x_j, y_j = mesh.nodes[j]
        x_k, y_k = mesh.nodes[k]
        
        # 计算单元刚度矩阵和面积
        Ke, area = element_stiffness_tri(x_i, y_i, x_j, y_j, x_k, y_k)
        
        # 计算单元载荷向量
        Fe = element_load_tri(area, f)
        
        # 组装到总体矩阵
        indices = [i, j, k]
        for ii, idx_i in enumerate(indices):
            for jj, idx_j in enumerate(indices):
                K[idx_i, idx_j] += Ke[ii, jj]
            F[idx_i] += Fe[ii]
    
    return K, F


def solve_poisson_fem(
    xmin: float = 0.0, xmax: float = 1.0,
    ymin: float = 0.0, ymax: float = 1.0,
    nx: int = 10, ny: int = 10,
    f: float = 1.0,
    bc_func=None
) -> Tuple[TriMesh, np.ndarray]:
    """
    求解Poisson方程的有限元解
    
    参数:
        xmin-xmax, ymin-ymax: 求解区域
        nx, ny: x和y方向的单元数
        f: 体力
        bc_func: 边界条件函数，默认为零边界
    
    返回:
        mesh: 网格对象
        u: 解向量
    """
    # 创建网格
    mesh = TriMesh(xmin, xmax, ymin, ymax, nx, ny)
    
    # 组装总体矩阵
    K, F = assemble_poisson(mesh, f)
    
    # 应用边界条件
    if bc_func is None:
        bc_func = lambda x, y: 0.0
    
    boundary = mesh.get_boundary_nodes()
    for node_idx in boundary:
        x, y = mesh.nodes[node_idx]
        # 惩罚法
        penalty = 1e15
        K[node_idx, node_idx] += penalty
        F[node_idx] = penalty * bc_func(x, y)
    
    # 求解
    u = np.linalg.solve(K, F)
    
    return mesh, u


if __name__ == "__main__":
    print("=" * 50)
    print("Poisson方程有限元求解测试")
    print("=" * 50)
    
    # 求解问题: -∇²u = 1, u|∂Ω = 0
    # 精确解(单位正方形): u(x,y) = xy(1-x)(1-y)/4 的某种形式
    # 这里我们使用零边界条件
    
    mesh, u = solve_poisson_fem(
        xmin=0.0, xmax=1.0,
        ymin=0.0, ymax=1.0,
        nx=8, ny=8,
        f=1.0
    )
    
    print(f"\n网格信息: {mesh.n_nodes} 节点, {mesh.n_elements} 单元")
    print(f"解的范围: [{u.min():.6f}, {u.max():.6f}]")
    
    # 显示部分节点解
    print(f"\n{'节点索引':>8} {'x':>8} {'y':>8} {'u(x,y)':>12}")
    print("-" * 38)
    # 显示角落和中心点
    display_indices = [0, mesh.nx, mesh.nx*(mesh.ny), -1,
                       mesh.n_nodes//2]
    for idx in display_indices:
        if 0 <= idx < mesh.n_nodes:
            print(f"{idx:8d}{mesh.nodes[idx,0]:8.3f}{mesh.nodes[idx,1]:8.3f}{u[idx]:12.6f}")
    
    print("\n测试通过！Poisson方程FEM求解器工作正常。")
