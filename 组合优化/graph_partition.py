# -*- coding: utf-8 -*-
"""
算法实现：组合优化 / graph_partition

本文件实现 graph_partition 相关的算法功能。
"""

from typing import List, Tuple, Optional
import random


class GraphPartitioner:
    """
    图划分求解器
    将图划分为k个大致相等的的部分,同时最小化切割边
    """
    
    def __init__(self, num_vertices: int, edges: List[Tuple[int, int]]):
        """
        初始化
        
        Args:
            num_vertices: 顶点数
            edges: 边列表
        """
        self.n = num_vertices
        self.edges = edges
        
        # 构建邻接表
        self.adj: List[List[int]] = [[] for _ in range(num_vertices)]
        for u, v in edges:
            self.adj[u].append(v)
            self.adj[v].append(u)
    
    def partition_greedy(self, k: int) -> List[int]:
        """
        贪心图划分
        
        Args:
            k: 分区数
        
        Returns:
            每个顶点所属的分区
        """
        # 初始化:每个顶点分配到最小负载的分区
        partition = [-1] * self.n
        loads = [0] * k
        
        # 简单策略:轮询分配
        for v in range(self.n):
            # 找到负载最小的分区
            min_partition = min(range(k), key=lambda i: loads[i])
            partition[v] = min_partition
            loads[min_partition] += 1
        
        return partition
    
    def partition_kl(self, k: int, iterations: int = 10) -> List[int]:
        """
        Kernighan-Lin风格的多路划分
        简化版:只支持2路,然后递归
        
        Args:
            k: 分区数
            iterations: 迭代次数
        
        Returns:
            每个顶点所属的分区
        """
        if k == 2:
            return self._kl_bipartition(iterations)
        
        # 递归划分
        # 先做k/2划分
        half = k // 2
        first_half = self._greedy_initial_partition(half)
        
        # 计算每个分区的大小
        sizes = [0] * half
        for p in first_half:
            sizes[p] += 1
        
        # 迭代改进
        for _ in range(iterations):
            improved = False
            
            # 尝试移动顶点到更小的分区
            for v in range(self.n):
                current = first_half[v]
                if sizes[current] > (self.n // (2 * half)):
                    # 找更好的分区
                    for neighbor in self.adj[v]:
                        target = first_half[neighbor]
                        if sizes[target] < sizes[current]:
                            first_half[v] = target
                            sizes[current] -= 1
                            sizes[target] += 1
                            improved = True
                            break
            
            if not improved:
                break
        
        return first_half
    
    def _kl_bipartition(self, iterations: int) -> List[int]:
        """
        Kernighan-Lin二路划分
        
        Args:
            iterations: 迭代次数
        
        Returns:
            划分结果(0或1)
        """
        n = self.n
        
        # 初始划分
        partition = [0] * n
        for i in range(n // 2):
            partition[i] = 1
        random.shuffle(partition)
        
        for _ in range(iterations):
            # 计算初始增益
            gains = []
            for v in range(n):
                gain = self._vertex_gain(v, partition)
                gains.append((gain, v))
            
            # 按增益排序
            gains.sort(reverse=True)
            
            # 贪心选择交换
            best_partition = partition.copy()
            best_cut = self._count_cut_edges(partition)
            
            current_partition = partition.copy()
            current_cut = best_cut
            
            for gain, v in gains[:n//4]:  # 只考虑前25%
                # 尝试交换
                current_partition[v] = 1 - current_partition[v]
                new_cut = self._count_cut_edges(current_partition)
                
                if new_cut < current_cut:
                    current_cut = new_cut
                    best_partition = current_partition.copy()
                    best_cut = new_cut
            
            partition = best_partition
            
            if best_cut == 0:
                break
        
        return partition
    
    def _vertex_gain(self, v: int, partition: List[int]) -> int:
        """计算将顶点v移动到另一分区能减少的切割边数"""
        p = partition[v]
        gain = 0
        for neighbor in self.adj[v]:
            if partition[neighbor] != p:
                gain += 1
            else:
                gain -= 1
        return gain
    
    def _count_cut_edges(self, partition: List[int]) -> int:
        """统计切割边数"""
        cut = 0
        for u, v in self.edges:
            if partition[u] != partition[v]:
                cut += 1
        return cut
    
    def _greedy_initial_partition(self, k: int) -> List[int]:
        """贪心初始划分"""
        partition = [-1] * self.n
        loads = [0] * k
        
        # 按度数排序
        vertices = list(range(self.n))
        vertices.sort(key=lambda v: len(self.adj[v]), reverse=True)
        
        for v in vertices:
            # 分配到邻居最少的分区
            min_partition = min(range(k), key=lambda i: loads[i])
            partition[v] = min_partition
            loads[min_partition] += 1
        
        return partition
    
    def partition_spectral(self, k: int) -> List[int]:
        """
        谱划分(简化版)
        使用特征向量来指导划分
        
        Args:
            k: 分区数
        
        Returns:
            划分结果
        """
        # 简化:只支持2路
        if k != 2:
            return self.partition_kl(k)
        
        # 构建邻接矩阵
        import numpy as np
        
        A = np.zeros((self.n, self.n))
        for u, v in self.edges:
            A[u][v] = 1
            A[v][u] = 1
        
        # 度矩阵
        D = np.diag([len(self.adj[i]) for i in range(self.n)])
        
        # 拉普拉斯矩阵 L = D - A
        L = D - A
        
        # 计算最小的特征值对应的特征向量
        eigenvalues, eigenvectors = np.linalg.eig(L)
        
        # 找第二小的特征值(最小的非零)
        idx = np.argsort(eigenvalues)
        second_smallest = eigenvectors[:, idx[1]]
        
        # 按特征向量分量符号划分
        partition = [0 if x >= 0 else 1 for x in second_smallest]
        
        # 如果划分不平衡,调整
        count0 = sum(partition)
        count1 = self.n - count0
        
        if abs(count0 - count1) > self.n // 4:
            # 按值排序后取中间的分界点
            sorted_vertices = sorted(range(self.n), key=lambda i: second_smallest[i])
            mid = self.n // 2
            partition = [0] * self.n
            for i in sorted_vertices[:mid]:
                partition[i] = 1
        
        return partition


def partition_graph(num_vertices: int, edges: List[Tuple[int, int]], 
                   k: int, method: str = 'kl') -> List[int]:
    """
    图划分便捷函数
    
    Args:
        num_vertices: 顶点数
        edges: 边列表
        k: 分区数
        method: 'greedy', 'kl'
    
    Returns:
        每个顶点的分区编号
    """
    solver = GraphPartitioner(num_vertices, edges)
    
    if method == 'greedy':
        return solver.partition_greedy(k)
    else:
        return solver.partition_kl(k)


# 测试代码
if __name__ == "__main__":
    import random
    random.seed(42)
    
    # 测试1: 简单图
    print("测试1 - 简单图(6顶点):")
    edges1 = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 5)]
    
    solver1 = GraphPartitioner(6, edges1)
    
    for method in ['greedy', 'kl']:
        if method == 'kl':
            part = solver1.partition_kl(2)
        else:
            part = solver1.partition_greedy(2)
        
        cut = solver1._count_cut_edges(part)
        print(f"  {method}: 划分={part}, 切割边数={cut}")
    
    # 测试2: 网格图
    print("\n测试2 - 网格图(4x4):")
    n = 4
    edges2 = []
    
    for i in range(n):
        for j in range(n):
            idx = i * n + j
            if i < n - 1:
                edges2.append((idx, idx + n))  # 上下
            if j < n - 1:
                edges2.append((idx, idx + 1))  # 左右
    
    solver2 = GraphPartitioner(n * n, edges2)
    
    for k in [2, 4]:
        part = solver2.partition_kl(k)
        cut = solver2._count_cut_edges(part)
        
        # 统计每个分区的大小
        sizes = [0] * k
        for p in part:
            sizes[p] += 1
        
        print(f"  k={k}: 大小={sizes}, 切割边数={cut}")
    
    # 测试3: 随机图
    print("\n测试3 - 随机图(20顶点):")
    n = 20
    edges3 = []
    
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() > 0.5:
                edges3.append((i, j))
    
    solver3 = GraphPartitioner(n, edges3)
    
    for method in ['greedy', 'kl']:
        if method == 'kl':
            part = solver3.partition_kl(2)
        else:
            part = solver3.partition_greedy(2)
        
        cut = solver3._count_cut_edges(part)
        count0 = sum(part)
        count1 = n - count0
        print(f"  {method}: 大小=[{count0},{count1}], 切割边数={cut}")
    
    # 测试4: 大规模图
    print("\n测试4 - 较大图(100顶点):")
    n = 100
    edges4 = []
    
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() > 0.9:
                edges4.append((i, j))
    
    solver4 = GraphPartitioner(n, edges4)
    
    part = solver4.partition_kl(4)
    cut = solver4._count_cut_edges(part)
    
    sizes = [0] * 4
    for p in part:
        sizes[p] += 1
    
    print(f"  k=4: 大小={sizes}, 切割边数={cut}")
    
    print("\n所有测试完成!")
