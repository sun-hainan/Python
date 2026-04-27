# -*- coding: utf-8 -*-
"""
算法实现：GPU并行算法 / gpu_graph_algorithms

本文件实现 gpu_graph_algorithms 相关的算法功能。
"""

import numpy as np
from numba import cuda
import numba


def cpu_page_rank(adjacency_matrix, damping=0.85, max_iter=100, tol=1e-6):
    """
    CPU PageRank（基准）
    
    参数:
        adjacency_matrix: 邻接矩阵
        damping: 阻尼因子
        max_iter: 最大迭代次数
        tol: 收敛阈值
    
    返回:
        pagerank: 页面排名向量
    """
    n = adjacency_matrix.shape[0]
    
    # 计算出度
    out_degree = np.sum(adjacency_matrix, axis=1)
    out_degree[out_degree == 0] = 1  # 避免除零
    
    # 初始化PageRank
    pagerank = np.ones(n) / n
    
    for _ in range(max_iter):
        new_pagerank = np.zeros(n)
        
        for i in range(n):
            # 收集所有指向节点i的节点的贡献
            incoming = np.where(adjacency_matrix[:, i] > 0)[0]
            for j in incoming:
                new_pagerank[i] += pagerank[j] / out_degree[j]
        
        # 加上随机跳转
        new_pagerank = damping * new_pagerank + (1 - damping) / n
        
        # 检查收敛
        if np.sum(np.abs(new_pagerank - pagerank)) < tol:
            break
        
        pagerank = new_pagerank
    
    return pagerank


@cuda.jit
def gpu_page_rank_kernel(pagerank, new_pagerank, adj_row_ptr, adj_col_idx, 
                         out_degree, damping, n):
    """
    GPU PageRank迭代内核
    
    参数:
        pagerank: 当前PageRank值
        new_pagerank: 下一轮PageRank值
        adj_row_ptr: 邻接表行指针
        adj_col_idx: 邻接表列索引
        out_degree: 出度
        damping: 阻尼因子
        n: 节点数
    """
    node = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if node < n:
        total = 0.0
        
        # 遍历所有出边
        for i in range(adj_row_ptr[node], adj_row_ptr[node + 1]):
            neighbor = adj_col_idx[i]
            total += pagerank[neighbor] / out_degree[neighbor]
        
        # 阻尼因子
        new_pagerank[node] = damping * total + (1.0 - damping) / n


def gpu_page_rank(adj_row_ptr, adj_col_idx, out_degree, n, damping=0.85, max_iter=100):
    """
    GPU PageRank封装函数
    
    参数:
        adj_row_ptr: 邻接表行指针
        adj_col_idx: 邻接表列索引
        out_degree: 出度数组
        n: 节点数
        damping: 阻尼因子
        max_iter: 最大迭代次数
    
    返回:
        pagerank: 页面排名向量
    """
    # 初始化
    pagerank = np.ones(n, dtype=np.float32) / n
    new_pagerank = np.zeros(n, dtype=np.float32)
    
    # 传输到GPU
    d_adj_row_ptr = cuda.to_device(adj_row_ptr)
    d_adj_col_idx = cuda.to_device(adj_col_idx)
    d_out_degree = cuda.to_device(out_degree.astype(np.float32))
    d_pagerank = cuda.to_device(pagerank)
    d_new_pagerank = cuda.to_device(new_pagerank)
    
    # 配置
    threads = 256
    blocks = (n + threads - 1) // threads
    
    # 迭代
    for _ in range(max_iter):
        gpu_page_rank_kernel[blocks, threads](
            d_pagerank, d_new_pagerank, 
            d_adj_row_ptr, d_adj_col_idx,
            d_out_degree, damping, n
        )
        
        # 交换引用
        d_pagerank, d_new_pagerank = d_new_pagerank, d_pagerank
    
    return d_pagerank.copy_to_host()


@cuda.jit
def gpu_bfs_kernel(adj_row_ptr, adj_col_idx, distances, queue, queue_size, n):
    """
    GPU BFS（广度优先搜索）内核
    
    使用类似GPU链式顺序的并行BFS
    
    参数:
        adj_row_ptr: 邻接表行指针
        adj_col_idx: 邻接表列索引
        distances: 距离数组（-1表示未访问）
        queue: 当前层的节点队列
        queue_size: 当前队列大小
        n: 节点数
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < queue_size:
        node = queue[global_idx]
        dist = distances[node] + 1
        
        # 遍历该节点的所有邻居
        for i in range(adj_row_ptr[node], adj_row_ptr[node + 1]):
            neighbor = adj_col_idx[i]
            
            # 如果邻居未访问，则标记距离
            if distances[neighbor] == -1:
                distances[neighbor] = dist
                # 注意：这里不加入队列，而是在下一层处理


def gpu_bfs(adj_row_ptr, adj_col_idx, start_node, n):
    """
    GPU BFS封装函数
    
    参数:
        adj_row_ptr: 邻接表行指针
        adj_col_idx: 邻接表列索引
        start_node: 起始节点
        n: 节点数
    
    返回:
        distances: 每个节点到起始节点的距离
    """
    # 初始化距离数组
    distances = np.full(n, -1, dtype=np.int32)
    distances[start_node] = 0
    
    # 当前层队列
    current_queue = np.array([start_node], dtype=np.int32)
    
    threads = 256
    
    while len(current_queue) > 0:
        blocks = (len(current_queue) + threads - 1) // threads
        
        d_adj_row_ptr = cuda.to_device(adj_row_ptr)
        d_adj_col_idx = cuda.to_device(adj_col_idx)
        d_distances = cuda.to_device(distances)
        d_queue = cuda.to_device(current_queue)
        
        gpu_bfs_kernel[blocks, threads](
            d_adj_row_ptr, d_adj_col_idx,
            d_distances, d_queue, len(current_queue), n
        )
        
        distances = d_distances.copy_to_host()
        
        # 收集新访问的节点
        current_queue = np.where(distances >= 0)[0]
        # 去重：只保留新加入的（距离等于当前层+1的）
        # 简化处理：重新计算
        break  # 单轮演示
    
    return distances


@cuda.jit
def gpu_triangle_count_kernel(adj_row_ptr, adj_col_idx, n, counter):
    """
    GPU三角形计数内核
    
    原理：对于无向图，三角形 = 节点对之间的共同邻居 / 2
    
    参数:
        adj_row_ptr: 邻接表行指针
        adj_col_idx: 邻接表列索引
        n: 节点数
        counter: 三角形计数器（原子操作）
    """
    global_idx = cuda.blockIdx.x * cuda.blockDim.x + cuda.threadIdx.x
    
    if global_idx < n:
        u = global_idx
        
        # 遍历u的所有邻居对
        for i in range(adj_row_ptr[u], adj_row_ptr[u + 1]):
            v = adj_col_idx[i]
            
            if v > u:  # 避免重复计数
                # 找u和v的共同邻居
                for j in range(adj_row_ptr[u], adj_row_ptr[u + 1]):
                    w = adj_col_idx[j]
                    
                    if w > v:  # 确保每个三角形只计数一次
                        # 检查v是否在u的邻居中
                        # 检查w是否在u的邻居中
                        # 简化：检查w是否在v的邻居中
                        for k in range(adj_row_ptr[v], adj_row_ptr[v + 1]):
                            if adj_col_idx[k] == w:
                                cuda.atomic.add(counter, 0, 1)
                                break


def gpu_triangle_count(adj_row_ptr, adj_col_idx, n):
    """
    GPU三角形计数封装函数
    
    参数:
        adj_row_ptr: 邻接表行指针
        adj_col_idx: 邻接表列索引
        n: 节点数
    
    返回:
        count: 三角形数量
    """
    counter = np.zeros(1, dtype=np.int32)
    
    d_adj_row_ptr = cuda.to_device(adj_row_ptr)
    d_adj_col_idx = cuda.to_device(adj_col_idx)
    d_counter = cuda.to_device(counter)
    
    threads = 256
    blocks = (n + threads - 1) // threads
    
    gpu_triangle_count_kernel[blocks, threads](
        d_adj_row_ptr, d_adj_col_idx, n, d_counter
    )
    
    result = d_counter.copy_to_host()
    return result[0]


def create_graph_csr(num_nodes, edge_prob):
    """
    创建随机图并返回CSR格式
    
    参数:
        num_nodes: 节点数
        edge_prob: 边概率
    
    返回:
        adj_row_ptr, adj_col_idx, out_degree
    """
    # 创建随机邻接矩阵
    adj_matrix = np.random.rand(num_nodes, num_nodes) < edge_prob
    np.fill_diagonal(adj_matrix, False)  # 无自环
    
    # 确保无向（对称）
    adj_matrix = adj_matrix | adj_matrix.T
    adj_matrix = adj_matrix.astype(np.float32)
    
    # 转换为CSR格式
    n = num_nodes
    adj_row_ptr = np.zeros(n + 1, dtype=np.int32)
    row_counts = np.sum(adj_matrix, axis=1).astype(np.int32)
    adj_row_ptr[1:] = np.cumsum(row_counts)
    
    adj_col_idx = np.argwhere(adj_matrix > 0)[:, 1].astype(np.int32)
    out_degree = row_counts.astype(np.float32)
    
    return adj_row_ptr, adj_col_idx, out_degree


def run_demo():
    """运行图算法演示"""
    print("=" * 60)
    print("GPU图算法 - PageRank/BFS/三角形计数演示")
    print("=" * 60)
    
    n = 100
    edge_prob = 0.1
    
    print(f"\n图规模: {n}节点, 边概率{edge_prob*100:.0f}%")
    
    # 创建图
    adj_row_ptr, adj_col_idx, out_degree = create_graph_csr(n, edge_prob)
    print(f"  总边数: {len(adj_col_idx)}")
    
    # PageRank演示
    print("\n[演示1] PageRank算法:")
    cpu_pr = cpu_page_rank(
        np.zeros((n, n)),  # 简化，不使用
        damping=0.85
    )
    
    # 使用CSR格式计算PageRank
    gpu_pr = gpu_page_rank(adj_row_ptr, adj_col_idx, out_degree, n)
    print(f"  Top 5节点: {np.argsort(gpu_pr)[-5:][::-1]}")
    print(f"  对应PageRank值: {gpu_pr[np.argsort(gpu_pr)[-5:][::-1]]}")
    print(f"  PageRank和: {np.sum(gpu_pr):.4f} (应为1.0)")
    
    # BFS演示
    print("\n[演示2] BFS（广度优先搜索）:")
    start = 0
    distances = gpu_bfs(adj_row_ptr, adj_col_idx, start, n)
    visited = np.sum(distances >= 0)
    print(f"  起始节点: {start}")
    print(f"  访问节点数: {visited}/{n}")
    print(f"  最远距离: {np.max(distances)}")
    
    # 三角形计数演示
    print("\n[演示3] 三角形计数:")
    triangle_count = gpu_triangle_count(adj_row_ptr, adj_col_idx, n)
    print(f"  三角形数量: {triangle_count}")
    
    print("\n" + "=" * 60)
    print("GPU图算法核心概念:")
    print("  1. PageRank: 迭代计算节点重要性")
    print("  2. BFS: 按层遍历，需要处理数据依赖")
    print("  3. 三角形计数: 寻找共同邻居")
    print("  4. 挑战: 图的不规则结构，负载均衡难")
    print("  5. 优化: CSR格式，原子操作，共享内存")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
