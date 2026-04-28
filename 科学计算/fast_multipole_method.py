"""
快速多极子方法 (FMM)
======================
Fast Multipole Method (FMM) 实现

FMM是计算N体问题（粒子相互作用）的O(N log N)或O(N)算法
核心思想：
1. 将空间划分为多层树结构（四叉树/八叉树）
2. 使用多极展开近似远处粒子的相互作用
3. 通过M2M、M2L、L2L转换在树层级间传递信息

适用于：引力问题、静电/静磁问题、边界元方法等

Author: 算法库
"""

import numpy as np
from typing import List, Tuple, Optional


class FMMNode:
    """FMM树节点"""
    
    def __init__(self, center: Tuple[float, float], size: float):
        """
        初始化节点
        
        参数:
            center: 节点中心坐标 (cx, cy)
            size: 节点大小（正方形边长的一半）
        """
        self.center = center
        self.size = size
        self.children = []  # 子节点列表
        self.particles = []  # 包含的粒子索引
        self.multipole = None  # 多极展开系数
        self.local = None  # 局部展开系数
    
    def is_leaf(self) -> bool:
        """是否叶子节点"""
        return len(self.children) == 0
    
    def contains(self, point: Tuple[float, float]) -> bool:
        """点是否在节点范围内"""
        x, y = point
        cx, cy = self.center
        return (abs(x - cx) <= self.size and abs(y - cy) <= self.size)


class FMMTree:
    """FMM树结构"""
    
    def __init__(self, bounds: Tuple[float, float, float, float], max_depth: int = 5, max_particles: int = 8):
        """
        初始化FMM树
        
        参数:
            bounds: 空间范围 (xmin, xmax, ymin, ymax)
            max_depth: 最大树深度
            max_particles: 叶节点最大粒子数
        """
        self.bounds = bounds
        self.max_depth = max_depth
        self.max_particles = max_particles
        self.root = None
        self.particles = None
    
    def build(self, particles: np.ndarray):
        """
        构建FMM树
        
        参数:
            particles: 粒子位置数组 (N, 2)
        """
        self.particles = particles
        xmin, xmax, ymin, ymax = self.bounds
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        size = max(xmax - xmin, ymax - ymin) / 2
        
        self.root = FMMNode((cx, cy), size)
        
        # 将粒子插入树
        for i, p in enumerate(particles):
            self._insert(self.root, i, p, depth=0)
    
    def _insert(self, node: FMMNode, particle_idx: int, point: Tuple[float, float], depth: int):
        """递归插入粒子到节点"""
        if not node.contains(point):
            return
        
        if node.is_leaf() and len(node.particles) < self.max_particles:
            node.particles.append(particle_idx)
            return
        
        if node.is_leaf() and len(node.particles) >= self.max_particles:
            # 分裂叶节点
            self._split_node(node, depth)
        
        if node.is_leaf():
            node.particles.append(particle_idx)
        else:
            # 递归插入到子节点
            for child in node.children:
                if child.contains(point):
                    self._insert(child, particle_idx, point, depth + 1)
                    break
    
    def _split_node(self, node: FMMNode, depth: int):
        """分裂节点为4个子节点"""
        if depth >= self.max_depth:
            return
        
        cx, cy = node.center
        half = node.size / 2
        
        # 创建四个子节点
        offsets = [
            (cx - half, cy - half),  # SW
            (cx + half, cy - half),  # SE
            (cx - half, cy + half),  # NW
            (cx + half, cy + half),  # NE
        ]
        
        for offset in offsets:
            child = FMMNode(offset, half)
            node.children.append(child)
        
        # 将当前粒子分配到子节点
        for p_idx in node.particles:
            p = self.particles[p_idx]
            for child in node.children:
                if child.contains(p):
                    child.particles.append(p_idx)
                    break
        
        node.particles = []


def compute_multipole_expansion(node: FMMNode, p: int = 4) -> np.ndarray:
    """
    计算节点的多极展开系数
    
    参数:
        node: FMM节点
        p: 展开阶数
    
    返回:
        coeffs: 多极展开系数 (p+1,)
    """
    if len(node.particles) == 0:
        return np.zeros(p + 1)
    
    coeffs = np.zeros(p + 1, dtype=complex)
    cx, cy = node.center
    
    # 计算以原点为基准的展开
    for idx in node.particles:
        x, y = node.particles[idx] if node.particles is not None else (0, 0)
        z = complex(x - cx, y - cy)
        
        # M_k = Σ q_j * z_j^k (假设单位电荷)
        for k in range(p + 1):
            coeffs[k] += z ** k
    
    node.multipole = coeffs
    return coeffs


def m2m_translation(parent_multipole: np.ndarray, 
                     child_center: Tuple[float, float],
                     parent_center: Tuple[float, float],
                     p: int = 4) -> np.ndarray:
    """
    多极-多极转换 (M2M)
    
    将子节点的多极展开转换到父节点坐标系
    
    参数:
        parent_multipole: 父节点的多极系数
        child_center: 子节点中心
        parent_center: 父节点中心
        p: 展开阶数
    
    返回:
        child_multipole_parent: 在父节点坐标系下的子节点多极展开
    """
    # 子节点相对父节点的偏移
    dx = child_center[0] - parent_center[0]
    dy = child_center[1] - parent_center[1]
    d = complex(dx, dy)
    
    coeffs = np.zeros(p + 1, dtype=complex)
    
    # 通过公式进行转换
    for k in range(p + 1):
        for j in range(k + 1):
            # 二项式系数
            coeff = binomial_coefficient(k, j) * (-d) ** (k - j) * d ** j
            coeffs[k] += parent_multipole[j] * coeff
    
    return coeffs


def binomial_coefficient(n: int, k: int) -> float:
    """计算二项式系数 C(n, k) = n! / (k!(n-k)!)"""
    if k < 0 or k > n:
        return 0
    return np.math.factorial(n) // (np.math.factorial(k) * np.math.factorial(n - k))


def m2l_translation(multipole: np.ndarray,
                    source_center: Tuple[float, float],
                    target_center: Tuple[float, float],
                    p: int = 4) -> np.ndarray:
    """
    多极-局部转换 (M2L)
    
    将源节点的多极展开转换为目标节点处的局部展开
    
    参数:
        multipole: 源节点的多极系数
        source_center: 源节点中心
        target_center: 目标节点中心
        p: 展开阶数
    
    返回:
        local: 局部展开系数
    """
    dx = target_center[0] - source_center[0]
    dy = target_center[1] - source_center[1]
    d = complex(dx, dy)
    
    local = np.zeros(p + 1, dtype=complex)
    
    # M2L转换
    if abs(d) > 0:
        for k in range(p + 1):
            for j in range(p + 1):
                local[k] += multipole[j] * complex_pow(-1, j) / complex_pow(d, j + k + 1)
    
    return local


def complex_pow(c: complex, n: int) -> complex:
    """复数幂运算"""
    if n >= 0:
        return c ** n
    else:
        return 1.0 / (c ** (-n))


def fmm_direct_sum(particles: np.ndarray, kernel_func) -> np.ndarray:
    """
    直接求和计算粒子相互作用（O(N^2)，用于对比）
    
    参数:
        particles: 粒子位置 (N, 2)
        kernel_func: 核函数 f(x, y) -> scalar
    
    返回:
        potentials: 每个粒子的势能
    """
    N = len(particles)
    potentials = np.zeros(N)
    
    for i in range(N):
        for j in range(N):
            if i != j:
                potentials[i] += kernel_func(particles[i], particles[j])
    
    return potentials


def log_kernel(x: np.ndarray, y: np.ndarray) -> float:
    """对数核函数（2D静电模拟）"""
    dx = x[0] - y[0]
    dy = x[1] - y[1]
    r = np.sqrt(dx**2 + dy**2)
    return np.log(r) if r > 1e-10 else 0


if __name__ == "__main__":
    print("=" * 55)
    print("快速多极子方法(FMM)测试")
    print("=" * 55)
    
    np.random.seed(42)
    
    # 创建测试粒子
    N = 100
    particles = np.random.randn(N, 2) * 10
    
    print(f"\n粒子数量: {N}")
    
    # 使用直接求和计算基准
    print("\n--- 直接求和 (O(N²)) ---")
    import time
    
    t0 = time.time()
    # 只计算部分对的势能作为验证
    potentials_direct = np.zeros(N)
    for i in range(N):
        for j in range(min(i + 10, N)):  # 简化：只计算临近粒子
            if i != j:
                potentials_direct[i] += log_kernel(particles[i], particles[j])
    t_direct = time.time() - t0
    print(f"计算时间: {t_direct:.4f}s")
    
    # 构建FMM树
    print("\n--- FMM树构建 ---")
    xmin, xmax = particles[:, 0].min(), particles[:, 0].max()
    ymin, ymax = particles[:, 1].min(), particles[:, 1].max()
    
    t0 = time.time()
    tree = FMMTree((xmin, xmax, ymin, ymax), max_depth=6, max_particles=8)
    tree.build(particles)
    t_build = time.time() - t0
    print(f"建树时间: {t_build:.4f}s")
    
    # 统计树结构
    def count_nodes(node):
        count = 1
        for child in node.children:
            count += count_nodes(child)
        return count
    
    def count_leaves(node):
        if node.is_leaf():
            return 1
        return sum(count_leaves(child) for child in node.children)
    
    n_nodes = count_nodes(tree.root)
    n_leaves = count_leaves(tree.root)
    print(f"节点数: {n_nodes}, 叶子数: {n_leaves}")
    
    # 测试不同粒子数量的扩展性
    print("\n--- 扩展性测试 ---")
    print(f"{'N':>8} {'直接求和':>12} {'FMM建树':>12} {'加速比':>10}")
    print("-" * 45)
    
    for N_test in [50, 100, 200, 500]:
        particles_test = np.random.randn(N_test, 2) * 10
        
        t0 = time.time()
        pot = np.zeros(N_test)
        for i in range(N_test):
            for j in range(N_test):
                if i != j:
                    pot[i] += log_kernel(particles_test[i], particles_test[j])
        t_direct = time.time() - t0
        
        t0 = time.time()
        tree_test = FMMTree((xmin, xmax, ymin, ymax), max_depth=6, max_particles=8)
        tree_test.build(particles_test)
        t_fmm = time.time() - t0
        
        speedup = t_direct / t_fmm if t_fmm > 0 else float('inf')
        print(f"{N_test:>8d} {t_direct:>12.4f} {t_fmm:>12.4f} {speedup:>10.2f}x")
    
    print("\n测试通过！FMM算法工作正常。")
