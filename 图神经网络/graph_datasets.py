# -*- coding: utf-8 -*-
"""
算法实现：图神经网络 / graph_datasets

本文件实现 graph_datasets 相关的算法功能。
"""

import numpy as np


class GraphDataset:
    """图数据集基类"""
    def __init__(self, num_nodes, node_features, adj, labels=None):
        self.num_nodes = num_nodes
        self.node_features = node_features
        self.adj = adj
        self.labels = labels
        
        self.train_mask = None
        self.val_mask = None
        self.test_mask = None
    
    def split(self, train_ratio=0.6, val_ratio=0.2, test_ratio=0.2, method='random'):
        """
        划分数据集
        
        参数:
            train_ratio: 训练集比例
            val_ratio: 验证集比例
            test_ratio: 测试集比例
            method: 'random' 或 'stratified'
        """
        assert train_ratio + val_ratio + test_ratio == 1.0
        
        n = self.num_nodes
        
        if method == 'random':
            indices = np.arange(n)
            np.random.shuffle(indices)
            
            train_size = int(n * train_ratio)
            val_size = int(n * val_ratio)
            
            self.train_mask = indices[:train_size]
            self.val_mask = indices[train_size:train_size + val_size]
            self.test_mask = indices[train_size + val_size:]
        
        return self
    
    def get_split(self, split_name='train'):
        """获取指定划分"""
        if split_name == 'train':
            mask = self.train_mask
        elif split_name == 'val':
            mask = self.val_mask
        elif split_name == 'test':
            mask = self.test_mask
        else:
            raise ValueError(f"Unknown split: {split_name}")
        
        if mask is None:
            return None
        
        return {
            'features': self.node_features[mask],
            'labels': self.labels[mask] if self.labels is not None else None
        }


class CoraDataset(GraphDataset):
    """
    Cora引文网络数据集（简化版）
    
    节点：学术论文
    边：引用关系
    特征：词袋向量
    标签：论文主题类别
    """
    
    def __init__(self):
        np.random.seed(42)
        
        # 简化版Cora
        self.num_nodes = 2708
        self.num_features = 1433
        self.num_classes = 7
        
        # 模拟生成数据
        # 真实Cora有2708节点，1433维特征
        self.node_features = np.random.randn(self.num_nodes, self.num_features) > 0
        self.node_features = self.node_features.astype(float)
        
        # 模拟邻接矩阵（稀疏连接）
        self.adj = self._generate_cora_graph()
        
        # 模拟标签
        self.labels = np.random.randint(0, self.num_classes, self.num_nodes)
        
        # 划分
        self.split()
    
    def _generate_cora_graph(self):
        """生成类似Cora的图结构"""
        n = self.num_nodes
        adj = np.zeros((n, n))
        
        # 每个节点的类别内连接概率更高
        for i in range(n):
            for j in range(i + 1, n):
                if self.labels[i] == self.labels[j]:
                    # 同类别，高概率连接
                    if np.random.random() < 0.08:
                        adj[i, j] = adj[j, i] = 1
                else:
                    # 不同类别，低概率连接
                    if np.random.random() < 0.005:
                        adj[i, j] = adj[j, i] = 1
        
        # 每个节点至少有一个邻居
        for i in range(n):
            if np.sum(adj[i]) == 0:
                # 随机连接一个同类节点
                same_label = np.where(self.labels == self.labels[i])[0]
                same_label = same_label[same_label != i]
                if len(same_label) > 0:
                    j = np.random.choice(same_label)
                    adj[i, j] = adj[j, i] = 1
        
        return adj


class PubmedDataset(GraphDataset):
    """Pubmed糖尿病文献网络（简化版）"""
    
    def __init__(self):
        np.random.seed(123)
        
        self.num_nodes = 19717
        self.num_features = 500
        self.num_classes = 3
        
        self.node_features = np.random.randn(self.num_nodes, self.num_features) > 0
        self.node_features = self.node_features.astype(float)
        
        self.adj = self._generate_pubmed_graph()
        self.labels = np.random.randint(0, self.num_classes, self.num_nodes)
        
        self.split()


class PPIDataset(GraphDataset):
    """蛋白质相互作用网络（简化版）"""
    
    def __init__(self):
        np.random.seed(456)
        
        self.num_nodes = 56944
        self.num_features = 50
        self.num_classes = 121  # 多标签
        
        self.node_features = np.random.randn(self.num_nodes, self.num_features)
        self.adj = self._generate_ppi_graph()
        
        # 多标签
        self.labels = (np.random.rand(self.num_nodes, self.num_classes) > 0.7).astype(float)
        
        self.split()


class LinkPredictionDataset:
    """
    边预测数据集
    
    用于训练和评估边预测模型
    """
    
    def __init__(self, adj, node_features):
        self.adj = adj
        self.node_features = node_features
        self.num_nodes = adj.shape[0]
        
        self._generate_train_samples()
    
    def _generate_train_samples(self):
        """生成训练样本"""
        n = self.num_nodes
        
        # 正样本：真实存在的边
        positive_edges = []
        for i in range(n):
            for j in range(i + 1, n):
                if self.adj[i, j] > 0:
                    positive_edges.append((i, j))
        
        self.positive_edges = positive_edges
        
        # 负样本：不存在的边
        negative_edges = []
        attempts = 0
        max_attempts = len(positive_edges) * 10
        
        while len(negative_edges) < len(positive_edges) and attempts < max_attempts:
            i, j = np.random.randint(0, n), np.random.randint(0, n)
            if i != j and self.adj[i, j] == 0:
                negative_edges.append((i, j))
            attempts += 1
        
        self.negative_edges = negative_edges
        
        # 组合
        self.edges = positive_edges + negative_edges
        self.labels = [1] * len(positive_edges) + [0] * len(negative_edges)
    
    def get_batch(self, batch_size=32):
        """获取一个批次"""
        indices = np.random.choice(len(self.edges), size=batch_size, replace=False)
        
        batch_edges = [self.edges[i] for i in indices]
        batch_labels = np.array([self.labels[i] for i in indices])
        
        return batch_edges, batch_labels


class GraphClassificationDataset:
    """
    图分类数据集
    
    包含多个图，每个图有标签
    """
    
    def __init__(self, num_graphs=100, avg_nodes=20, max_nodes=50):
        np.random.seed(789)
        
        self.num_graphs = num_graphs
        self.graphs = []
        
        for _ in range(num_graphs):
            n = np.random.randint(avg_nodes // 2, max_nodes)
            
            # 随机特征
            features = np.random.randn(n, 8)
            
            # 随机邻接矩阵
            density = np.random.uniform(0.1, 0.4)
            adj = (np.random.rand(n, n) < density).astype(float)
            adj = (adj + adj.T) / 2
            np.fill_diagonal(adj, 0)
            
            # 标签（随机）
            label = np.random.randint(0, 2)
            
            self.graphs.append({
                'num_nodes': n,
                'features': features,
                'adj': adj,
                'label': label
            })
    
    def __len__(self):
        return self.num_graphs
    
    def __getitem__(self, idx):
        return self.graphs[idx]


def collate_fn_graphs(batch):
    """将一批图整理成批次"""
    # 简化实现
    return batch


def create_data_loader(dataset, batch_size=32, shuffle=True):
    """创建数据加载器"""
    indices = np.arange(len(dataset))
    
    if shuffle:
        np.random.shuffle(indices)
    
    loaders = []
    for i in range(0, len(indices), batch_size):
        batch_indices = indices[i:i + batch_size]
        batch = [dataset[idx] for idx in batch_indices]
        loaders.append(batch)
    
    return loaders


if __name__ == "__main__":
    print("=" * 55)
    print("图数据集和加载器测试")
    print("=" * 55)
    
    # 测试Cora
    print("\n--- Cora数据集 ---")
    cora = CoraDataset()
    print(f"节点数: {cora.num_nodes}")
    print(f"特征维度: {cora.num_features}")
    print(f"类别数: {cora.num_classes}")
    print(f"边数: {int(np.sum(cora.adj) / 2)}")
    print(f"训练集大小: {len(cora.train_mask)}")
    print(f"验证集大小: {len(cora.val_mask)}")
    print(f"测试集大小: {len(cora.test_mask)}")
    
    # 类别分布
    print("\n类别分布:")
    for c in range(cora.num_classes):
        count = np.sum(cora.labels == c)
        print(f"  类别{c}: {count}节点 ({count/cora.num_nodes:.1%})")
    
    # 测试Pubmed
    print("\n--- Pubmed数据集 ---")
    pubmed = PubmedDataset()
    print(f"节点数: {pubmed.num_nodes}")
    print(f"特征维度: {pubmed.num_features}")
    print(f"边数: {int(np.sum(pubmed.adj) / 2)}")
    
    # 测试PPI
    print("\n--- PPI数据集 ---")
    ppi = PPI Dataset()
    print(f"节点数: {ppi.num_nodes}")
    print(f"特征维度: {ppi.num_features}")
    print(f"标签维度: {ppi.labels.shape}")
    print(f"平均每节点标签数: {ppi.labels.sum(axis=1).mean():.2f}")
    
    # 测试边预测数据集
    print("\n--- 边预测数据集 ---")
    adj = np.zeros((20, 20))
    for i in range(19):
        adj[i, i+1] = adj[i+1, i] = 1
    
    features = np.random.randn(20, 8)
    
    lp_dataset = LinkPredictionDataset(adj, features)
    print(f"正样本数: {len(lp_dataset.positive_edges)}")
    print(f"负样本数: {len(lp_dataset.negative_edges)}")
    print(f"总样本数: {len(lp_dataset.edges)}")
    
    # 获取批次
    batch_edges, batch_labels = lp_dataset.get_batch(8)
    print(f"批次边数: {len(batch_edges)}")
    print(f"批次标签: {batch_labels}")
    
    # 测试图分类数据集
    print("\n--- 图分类数据集 ---")
    gc_dataset = GraphClassificationDataset(num_graphs=50)
    print(f"图数量: {len(gc_dataset)}")
    
    # 创建数据加载器
    loader = create_data_loader(gc_dataset, batch_size=8)
    print(f"批次数: {len(loader)}")
    
    # 查看第一批
    first_batch = loader[0]
    print(f"第一批图数: {len(first_batch)}")
    print(f"第一批图节点范围: {[g['num_nodes'] for g in first_batch]}")
    
    # 图统计
    print("\n--- 图统计 ---")
    all_nodes = [g['num_nodes'] for g in gc_dataset.graphs]
    all_edges = [int(np.sum(g['adj']) / 2) for g in gc_dataset.graphs]
    
    print(f"平均节点数: {np.mean(all_nodes):.1f}")
    print(f"节点数范围: [{min(all_nodes)}, {max(all_nodes)}]")
    print(f"平均边数: {np.mean(all_edges):.1f}")
    print(f"边数范围: [{min(all_edges)}, {max(all_edges)}]")
    
    print("\n图数据集和加载器测试完成！")
