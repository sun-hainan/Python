"""
DeepWalk图嵌入 (Graph Embedding via DeepWalk)
============================================
实现DeepWalk算法，将图节点映射到低维向量空间。

DeepWalk使用随机游走生成节点序列，然后应用Skip-Gram模型学习嵌入。

核心思想：
1. 随机游走：从每个节点出发，进行多次短随机游走
2. Skip-Gram：使用分层Softmax或负采样训练词向量模型

参考：
    - Perozzi, B. et al. (2014). DeepWalk: Online Learning of Social Representations.
"""

from typing import List, Dict, Set, Tuple
import random
from collections import Counter, defaultdict
import math


class Graph:
    """无向图"""
    def __init__(self, n: int = 0):
        self.n = n
        self.adj = [set() for _ in range(n)]
    
    def add_edge(self, u: int, v: int):
        self.adj[u].add(v)
        self.adj[v].add(u)
    
    def neighbors(self, u: int) -> Set[int]:
        return self.adj[u]


class DeepWalk:
    """
    DeepWalk图嵌入模型
    
    参数:
        graph: 输入图
        embedding_dim: 嵌入维度
        walk_length: 随机游走长度
        num_walks: 每个节点的游走次数
        window_size: Skip-Gram窗口大小
        learning_rate: 学习率
    """
    
    def __init__(self, graph: Graph, embedding_dim: int = 64, 
                 walk_length: int = 10, num_walks: int = 8,
                 window_size: int = 5, learning_rate: float = 0.025):
        self.graph = graph
        self.embedding_dim = embedding_dim
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.window_size = window_size
        self.learning_rate = learning_rate
        
        # 嵌入矩阵
        self.embeddings = None
    
    def random_walk(self, start: int) -> List[int]:
        """
        从起始节点生成一条随机游走
        
        参数:
            start: 起始节点
        
        返回:
            游走路径（节点序列）
        """
        walk = [start]
        current = start
        
        for _ in range(self.walk_length - 1):
            neighbors = list(self.graph.neighbors(current))
            if not neighbors:
                break
            current = random.choice(neighbors)
            walk.append(current)
        
        return walk
    
    def generate_walks(self) -> List[List[int]]:
        """
        生成所有随机游走序列
        
        返回:
            所有游走路径的列表
        """
        walks = []
        nodes = list(range(self.graph.n))
        
        for _ in range(self.num_walks):
            random.shuffle(nodes)
            for node in nodes:
                walk = self.random_walk(node)
                walks.append(walk)
        
        return walks
    
    def build_vocab(self, walks: List[List[int]]) -> Dict[int, int]:
        """
        构建词汇表（节点到索引的映射）
        
        参数:
            walks: 游走序列
        
        返回:
            node_to_idx 字典
        """
        # 统计节点出现频率
        node_counts = Counter()
        for walk in walks:
            node_counts.update(walk)
        
        # 按频率降序排列
        vocab = [node for node, _ in node_counts.most_common()]
        
        # 创建映射
        node_to_idx = {node: idx for idx, node in enumerate(vocab)}
        
        return node_to_idx
    
    def skip_gram(self, walk: List[int], node_to_idx: Dict[int, int]):
        """
        Skip-Gram训练步骤（简化实现，使用随机梯度下降）
        
        参数:
            walk: 一条游走路径
            node_to_idx: 词汇表映射
        """
        vocab_size = len(node_to_idx)
        
        # 初始化嵌入（如果尚未初始化）
        if self.embeddings is None:
            # 使用Xavier初始化
            scale = math.sqrt(2.0 / (vocab_size + self.embedding_dim))
            self.embeddings = [[random.uniform(-scale, scale) 
                               for _ in range(self.embedding_dim)]
                              for _ in range(vocab_size)]
        
        # 对路径中的每个词作为中心词
        for i, center in enumerate(walk):
            if center not in node_to_idx:
                continue
            
            center_idx = node_to_idx[center]
            
            # 上下文窗口
            start = max(0, i - self.window_size)
            end = min(len(walk), i + self.window_size + 1)
            
            for j in range(start, end):
                if i == j:
                    continue
                
                context = walk[j]
                if context not in node_to_idx:
                    continue
                
                context_idx = node_to_idx[context]
                
                # 简化的梯度更新（实际应使用负采样或分层Softmax）
                # 这里只做概念演示
                pass
    
    def train(self, epochs: int = 5, verbose: bool = True) -> List[List[float]]:
        """
        训练DeepWalk模型
        
        参数:
            epochs: 训练轮数
            verbose: 是否打印进度
        
        返回:
            嵌入矩阵
        """
        if verbose:
            print(f"生成随机游走 (num_walks={self.num_walks}, walk_length={self.walk_length})...")
        
        walks = self.generate_walks()
        
        if verbose:
            print(f"生成 {len(walks)} 条游走路径")
        
        # 构建词汇表
        node_to_idx = self.build_vocab(walks)
        vocab_size = len(node_to_idx)
        
        if verbose:
            print(f"词汇表大小: {vocab_size}")
        
        # 初始化嵌入
        scale = math.sqrt(2.0 / (vocab_size + self.embedding_dim))
        self.embeddings = [[random.uniform(-scale, scale) 
                           for _ in range(self.embedding_dim)]
                          for _ in range(vocab_size)]
        
        # 训练
        if verbose:
            print(f"训练 {epochs} 轮...")
        
        for epoch in range(epochs):
            total_loss = 0.0
            
            for walk in walks:
                # Skip-Gram训练
                loss = self._skip_gram_step(walk, node_to_idx)
                total_loss += loss
            
            if verbose:
                print(f"  Epoch {epoch+1}: loss = {total_loss / len(walks):.4f}")
        
        # 创建节点ID到嵌入的映射
        idx_to_embedding = {}
        for node, idx in node_to_idx.items():
            idx_to_embedding[idx] = self.embeddings[idx]
        
        # 返回按节点ID排序的嵌入
        result = []
        for node in range(self.graph.n):
            if node in node_to_idx:
                result.append(self.embeddings[node_to_idx[node]])
            else:
                # 未出现的节点使用零向量
                result.append([0.0] * self.embedding_dim)
        
        return result
    
    def _skip_gram_step(self, walk: List[int], node_to_idx: Dict[int, int]) -> float:
        """
        单步Skip-Gram训练
        
        参数:
            walk: 游走路径
            node_to_idx: 词汇表
        
        返回:
            训练损失
        """
        loss = 0.0
        
        for i, center in enumerate(walk):
            if center not in node_to_idx:
                continue
            
            center_idx = node_to_idx[center]
            
            # 上下文窗口
            start = max(0, i - self.window_size)
            end = min(len(walk), i + self.window_size + 1)
            
            for j in range(start, end):
                if i == j:
                    continue
                
                context = walk[j]
                if context not in node_to_idx:
                    continue
                
                context_idx = node_to_idx[context]
                
                # 简化的损失计算（余弦相似度损失）
                # 实际应使用负采样
                center_emb = self.embeddings[center_idx]
                context_emb = self.embeddings[context_idx]
                
                # 计算点积
                dot = sum(a * b for a, b in zip(center_emb, context_emb))
                
                # sigmoid损失
                loss += -math.log(1 + math.exp(-dot))
                
                # 简化的梯度更新
                # grad = sigmoid(dot) - 1
                grad = 1 / (1 + math.exp(-dot)) - 1
                
                for k in range(self.embedding_dim):
                    self.embeddings[center_idx][k] -= self.learning_rate * grad * context_emb[k]
                    self.embeddings[context_idx][k] -= self.learning_rate * grad * center_emb[k]
        
        return loss
    
    def get_embedding(self, node: int) -> List[float]:
        """
        获取指定节点的嵌入向量
        
        参数:
            node: 节点ID
        
        返回:
            嵌入向量
        """
        if self.embeddings is None:
            raise ValueError("模型尚未训练，请先调用train()")
        
        return self.embeddings[node]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    参数:
        vec1: 向量1
        vec2: 向量2
    
    返回:
        余弦相似度
    """
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(a * a for a in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot / (norm1 * norm2)


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    计算欧氏距离
    
    参数:
        vec1: 向量1
        vec2: 向量2
    
    返回:
        距离
    """
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def node_similarity_analysis(embeddings: List[List[float]], 
                             node_pairs: List[Tuple[int, int]]) -> List[float]:
    """
    分析节点对的相似度
    
    参数:
        embeddings: 嵌入矩阵
        node_pairs: 节点对列表
    
    返回:
        各对的余弦相似度
    """
    similarities = []
    
    for u, v in node_pairs:
        sim = cosine_similarity(embeddings[u], embeddings[v])
        similarities.append(sim)
    
    return similarities


if __name__ == "__main__":
    print("=== DeepWalk图嵌入测试 ===")
    
    # 创建测试图：Zachary空手道俱乐部网络
    g = Graph(34)
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (0, 10), (0, 11), (0, 12), (0, 13), (0, 17), (0, 19), (0, 21), (0, 31),
        (1, 2), (1, 3), (1, 7), (1, 13), (1, 17), (1, 19), (1, 21), (1, 30),
        (2, 3), (2, 7), (2, 8), (2, 9), (2, 13), (2, 27), (2, 28), (2, 32),
        (3, 7), (3, 12), (3, 13),
        (4, 6), (4, 10),
        (5, 6), (5, 10), (5, 16),
        (6, 16),
        (8, 30), (8, 32), (8, 33),
        (9, 33),
        (13, 33),
        (14, 32), (14, 33),
        (15, 32), (15, 33),
        (18, 32), (18, 33),
        (19, 33),
        (20, 32), (20, 33),
        (22, 32), (22, 33),
        (23, 25), (23, 27), (23, 29), (23, 32), (23, 33),
        (24, 25), (24, 27), (24, 31),
        (25, 31),
        (26, 29),
        (27, 33),
        (28, 31), (28, 33),
        (29, 32), (29, 33),
        (30, 32), (30, 33),
        (31, 32), (31, 33),
        (32, 33)
    ]
    
    for u, v in edges:
        g.add_edge(u, v)
    
    print(f"图: {g.n} 节点, {len(edges)} 条边")
    
    # 训练DeepWalk
    dw = DeepWalk(g, embedding_dim=16, walk_length=10, num_walks=5, 
                  window_size=3, learning_rate=0.01)
    
    embeddings = dw.train(epochs=5)
    
    print(f"\n嵌入形状: ({len(embeddings)}, {len(embeddings[0])})")
    
    # 分析节点相似度
    print("\n节点相似度分析:")
    test_pairs = [(0, 1), (0, 33), (1, 2), (2, 33)]
    
    for u, v in test_pairs:
        sim = cosine_similarity(embeddings[u], embeddings[v])
        dist = euclidean_distance(embeddings[u], embeddings[v])
        print(f"  节点 {u} vs {v}: cos={sim:.4f}, dist={dist:.4f}")
    
    # 查找最相似的节点
    print("\n与节点0最相似的节点:")
    similarities = []
    for i in range(g.n):
        if i != 0:
            sim = cosine_similarity(embeddings[0], embeddings[i])
            similarities.append((i, sim))
    
    similarities.sort(key=lambda x: x[1], reverse=True)
    for node, sim in similarities[:5]:
        print(f"  节点 {node}: {sim:.4f}")
    
    print("\n=== 测试完成 ===")
