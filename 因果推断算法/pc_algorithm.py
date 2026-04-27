# -*- coding: utf-8 -*-
"""
算法实现：因果推断算法 / pc_algorithm

本文件实现 pc_algorithm 相关的算法功能。
"""

import numpy as np
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
import random


class PCAlgorithm:
    """
    PC算法实现
    
    核心思想：
    - 使用条件独立性检验判断两个变量是否条件独立
    - 条件独立 -> 边断开
    - 最终学习因果骨架和方向
    """
    
    def __init__(self, alpha: float = 0.05, max_cond_set: int = 3):
        """
        初始化
        
        Args:
            alpha: 显著性水平
            max_cond_set: 最大条件集大小
        """
        self.alpha = alpha
        self.max_cond_set = max_cond_set
        
        # 因果图结构
        self.variables: List[str] = []
        self.sepsets: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        self.skeleton: Dict[str, Set[str]] = defaultdict(set)
        self.undirected_edges: Set[Tuple[str, str]] = set()
        self.directed_edges: List[Tuple[str, str]] = []
        
        # 统计
        self.ci_tests = 0
    
    def fit(self, data: Dict[str, np.ndarray]):
        """
        从数据学习因果结构
        
        Args:
            data: {变量名: 数据数组}
        """
        self.variables = list(data.keys())
        self.n = len(data[self.variables[0]])
        
        # 转换为numpy数组
        self.data = np.column_stack([data[v] for v in self.variables])
        self.var_index = {v: i for i, v in enumerate(self.variables)}
        
        # 阶段1：学习骨架
        self._learn_skeleton()
        
        # 阶段2：定向v-结构
        self._orient_v_structures()
        
        # 阶段3：定向剩余边
        self._orient_edges()
    
    def _learn_skeleton(self):
        """学习因果骨架"""
        n_vars = len(self.variables)
        
        # 初始化：完全图
        for i in range(n_vars):
            vi = self.variables[i]
            for j in range(i + 1, n_vars):
                vj = self.variables[j]
                self.skeleton[vi].add(vj)
                self.skeleton[vj].add(vi)
                self.undirected_edges.add((vi, vj))
        
        # 逐步增加条件集大小
        for cond_size in range(self.max_cond_set + 1):
            edges_to_check = list(self.undirected_edges.copy())
            
            for x, y in edges_to_check:
                # 获取x和y的邻居（排除彼此）
                neighbors_x = [v for v in self.skeleton[x] if v != y]
                neighbors_y = [v for v in self.skeleton[y] if v != x]
                
                # 所有可能的条件集
                all_neighbors = list(set(neighbors_x) | set(neighbors_y))
                
                if len(all_neighbors) < cond_size:
                    continue
                
                # 检查所有大小为cond_size的条件集
                for cond_set in self._combinations(all_neighbors, cond_size):
                    self.ci_tests += 1
                    
                    # 条件独立性检验
                    if self._ci_test(x, y, cond_set):
                        # x和y条件独立，断开边
                        self.skeleton[x].discard(y)
                        self.skeleton[y].discard(x)
                        self.undirected_edges.discard((x, y))
                        self.undirected_edges.discard((y, x))
                        
                        # 记录分离集
                        self.sepsets[(x, y)] = set(cond_set)
                        self.sepsets[(y, x)] = set(cond_set)
                        break
    
    def _ci_test(self, x: str, y: str, cond_set: List[str]) -> bool:
        """
        条件独立性检验
        
        使用偏相关或G²检验
        这里使用简化的高斯检验
        
        Returns:
            True表示条件独立（无直接边）
        """
        i, j = self.var_index[x], self.var_index[y]
        
        if len(cond_set) == 0:
            # 简单相关
            corr = np.corrcoef(self.data[:, i], self.data[:, j])[0, 1]
            stat = corr * np.sqrt(self.n - 2) / np.sqrt(1 - corr ** 2)
            p_value = 2 * (1 - self._normal_cdf(abs(stat)))
        else:
            # 偏相关
            k = len(cond_set)
            cond_indices = [self.var_index[v] for v in cond_set]
            
            # 计算偏相关
            corr = self._partial_correlation(i, j, cond_indices)
            
            if abs(corr) < 0.999:
                stat = corr * np.sqrt(self.n - k - 2) / np.sqrt(1 - corr ** 2)
                p_value = 2 * (1 - self._normal_cdf(abs(stat)))
            else:
                p_value = 0.0
        
        # p值大 -> 条件独立 -> 断边
        return p_value > self.alpha
    
    def _partial_correlation(self, i: int, j: int, cond: List[int]) -> float:
        """计算偏相关系数"""
        if len(cond) == 0:
            return np.corrcoef(self.data[:, i], self.data[:, j])[0, 1]
        
        # 使用线性回归的残差计算偏相关
        all_indices = [i, j] + cond
        
        subdata = self.data[:, all_indices]
        
        # 回归
        X = subdata[:, 2:]  # 条件变量
        y_i = subdata[:, 0]  # x
        y_j = subdata[:, 1]  # y
        
        # 残差
        if X.shape[1] > 0:
            beta_i = np.linalg.lstsq(X, y_i, rcond=None)[0]
            resid_i = y_i - X @ beta_i
            
            beta_j = np.linalg.lstsq(X, y_j, rcond=None)[0]
            resid_j = y_j - X @ beta_j
        else:
            resid_i = y_i
            resid_j = y_j
        
        # 偏相关
        return np.corrcoef(resid_i, resid_j)[0, 1]
    
    def _combinations(self, items: List, size: int) -> List[List]:
        """生成组合"""
        if size == 0:
            return [[]]
        
        if len(items) < size:
            return []
        
        result = []
        for i in range(len(items)):
            for combo in self._combinations(items[i+1:], size-1):
                result.append([items[i]] + combo)
        
        return result
    
    def _orient_v_structures(self):
        """
        定向v-结构
        
        模式: x - z - y, x和y不相邻, z不在sep(x,y)中
        则定向为: x -> z <- y
        """
        for z in self.variables:
            neighbors = list(self.skeleton[z])
            
            for i, x in enumerate(neighbors):
                for y in neighbors[i+1:]:
                    # x和y不相邻
                    if y not in self.skeleton[x]:
                        # z不在sep(x,y)中
                        if z not in self.sepsets[(x, y)]:
                            # 定向为v-结构
                            self.directed_edges.append((x, z))
                            self.directed_edges.append((y, z))
    
    def _orient_edges(self):
        """定向剩余边（使用其他规则）"""
        # 迭代定向直到没有变化
        changed = True
        while changed:
            changed = False
            
            for x, y in list(self.undirected_edges):
                if (x, y) not in self.undirected_edges:
                    continue
                
                # 规则：如果是x -> z - y，且x和y不相邻，则定向z -> y
                for z in self.skeleton[y]:
                    if z == x:
                        continue
                    
                    if (x, z) in self.directed_edges and (z, x) not in self.directed_edges:
                        # x -> z
                        if y not in self.skeleton[x]:  # x和y不相邻
                            if (z, y) not in self.directed_edges:
                                self.directed_edges.append((z, y))
                                self.undirected_edges.discard((z, y))
                                self.undirected_edges.discard((y, z))
                                changed = True
    
    def _normal_cdf(self, x: float) -> float:
        """标准正态CDF"""
        import math
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))
    
    def get_skeleton(self) -> Dict[str, List[str]]:
        """获取骨架"""
        return {v: list(self.skeleton[v]) for v in self.variables}
    
    def get_dag(self) -> List[Tuple[str, str]]:
        """获取有向无环图"""
        return self.directed_edges.copy()
    
    def get_undirected_edges(self) -> List[Tuple[str, str]]:
        """获取无向边"""
        return list(self.undirected_edges)


def demo_pc_algorithm():
    """演示PC算法"""
    print("=== PC算法演示 ===\n")
    
    np.random.seed(42)
    
    # 生成因果数据: X -> Z <- Y
    n = 1000
    
    X = np.random.randn(n)
    Y = np.random.randn(n)
    Z = 0.5 * X + 0.5 * Y + 0.2 * np.random.randn(n)
    
    data = {'X': X, 'Y': Y, 'Z': Z}
    
    print("数据生成:")
    print("  X: 标准正态")
    print("  Y: 标准正态")
    print("  Z = 0.5*X + 0.5*Y + 噪声")
    print()
    print("真实因果结构: X -> Z <- Y")
    
    # PC算法
    pc = PCAlgorithm(alpha=0.05, max_cond_set=2)
    pc.fit(data)
    
    print(f"\n算法统计:")
    print(f"  条件独立性检验次数: {pc.ci_tests}")
    
    print("\n学习到的骨架:")
    skeleton = pc.get_skeleton()
    for v, neighbors in skeleton.items():
        print(f"  {v}: {neighbors}")
    
    print("\n定向边:")
    for x, y in pc.get_dag():
        print(f"  {x} -> {y}")


def demo_pc_vs_correlation():
    """演示PC算法与相关分析的区别"""
    print("\n=== PC vs 相关分析 ===\n")
    
    print("问题: X和Y都受Z影响，X和Y表面相关")
    print()
    
    print("相关分析结论:")
    print("  - X和Y相关")
    print("  - 可能错误推断X -> Y 或 Y -> X")
    print()
    
    print("PC算法结论:")
    print("  - 控制Z后，X和Y条件独立")
    print("  - 正确识别X <- Z -> Y结构")
    print()
    
    print("关键洞察:")
    print("  - 相关 ≠ 因果")
    print("  - 需要条件独立性检验")


def demo_ci_test():
    """演示条件独立性检验"""
    print("\n=== 条件独立性检验 ===\n")
    
    print("偏相关计算:")
    print("  ρ(X,Y|Z) = (ρ(X,Y) - ρ(X,Z)*ρ(Y,Z)) / sqrt((1-ρ²(X,Z))(1-ρ²(Y,Z)))")
    print()
    
    print("检验步骤:")
    print("  1. 计算偏相关")
    print("  2. 计算检验统计量")
    print("  3. 与阈值比较")


def demo_v_structure():
    """演示v-结构定向"""
    print("\n=== v-结构定向 ===\n")
    
    print("v-结构模式:")
    print("    X")
    print("   /")
    print("  Z")
    print("   \\")
    print("    Y")
    print()
    
    print("判断条件:")
    print("  1. X和Y不相邻")
    print("  2. Z是X和Y的公共邻居")
    print("  3. Z不在sep(X,Y)中")
    print()
    
    print("定向结果: X -> Z <- Y")


if __name__ == "__main__":
    print("=" * 60)
    print("PC算法 - 因果发现")
    print("=" * 60)
    
    # PC算法演示
    demo_pc_algorithm()
    
    # PC vs 相关
    demo_pc_vs_correlation()
    
    # 条件独立性检验
    demo_ci_test()
    
    # v-结构
    demo_v_structure()
    
    print("\n" + "=" * 60)
    print("PC算法核心原理:")
    print("=" * 60)
    print("""
1. 因果骨架学习:
   - 从完全图开始
   - 逐步移除条件独立的边
   - 使用条件独立性检验(CI test)

2. v-结构定向:
   - X - Z - Y, X和Y不相邻
   - Z不在sep(X,Y)中
   - 则定向为X -> Z <- Y

3. 剩余边定向:
   - 使用其他定向规则
   - 避免创建v-结构或环路
   - 最终得到DAG

4. 局限性:
   - 需要马尔可夫等价假设
   - 对隐藏confounder敏感
   - 条件独立性检验功效有限

5. 改进算法:
   - FCI (面对隐藏变量)
   - PC-stable (更稳定)
   - 贪婪等价搜索 (GES)
""")
