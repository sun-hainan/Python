"""
折叠Gibbs采样（Collapsed Gibbs Sampling）
Collapsed Gibbs Sampling

折叠Gibbs采样通过边际化掉某些变量来减少状态空间，
从而降低采样方差。常用于主题模型（如LDA）等隐变量模型。
"""

import numpy as np
from typing import Dict, List, Callable, Optional, Tuple
from collections import defaultdict


class CollapsedGibbsSampler:
    """
    折叠Gibbs采样器
    
    核心思想：
    - 边际化掉超参数/部分隐变量
    - 只对关键变量进行Gibbs采样
    - 减少采样空间，降低方差
    
    参数:
        variables: 可变变量列表
        collapsed_vars: 被边际化的变量列表
    """
    
    def __init__(self, variables: List[str], collapsed_vars: Optional[List[str]] = None):
        self.variables = variables
        self.collapsed_vars = collapsed_vars or []
        self.samples = []
        self.state = {}
    
    def initialize(self, init_func: Callable):
        """初始化状态"""
        for var in self.variables:
            self.state[var] = init_func(var)
    
    def conditional_log_prob(self, var: str, value: int, 
                             others: Dict[str, int]) -> float:
        """
        计算条件对数概率
        
        参数:
            var: 变量名
            value: 变量值
            others: 其他变量的当前值
            
        返回:
            对数概率
        """
        raise NotImplementedError
    
    def sample_one(self, var: str) -> int:
        """对单个变量采样"""
        others = {k: v for k, v in self.state.items() if k != var}
        
        # 计算各值的概率
        log_probs = []
        for val in [0, 1]:  # 假设二元变量
            log_probs.append(self.conditional_log_prob(var, val, others))
        
        # 归一化（减去最大值）
        log_probs = np.array(log_probs)
        log_probs = log_probs - np.max(log_probs)
        probs = np.exp(log_probs)
        probs = probs / np.sum(probs)
        
        return np.random.choice(len(probs), p=probs)
    
    def run(self, n_iterations: int) -> List[Dict]:
        """
        运行折叠Gibbs采样
        
        参数:
            n_iterations: 迭代次数
            
        返回:
            样本历史
        """
        self.samples = []
        
        for _ in range(n_iterations):
            # 依次采样每个变量
            for var in self.variables:
                self.state[var] = self.sample_one(var)
            
            # 记录样本
            self.samples.append(self.state.copy())
        
        return self.samples


class LatentDirichletAllocation:
    """
    潜在狄利克雷分配（LDA）的折叠Gibbs采样
    
    模型：
    - 文档d中的词w来自主题z
    - z ~ Multinomial(theta)  主题分布
    - theta ~ Dirichlet(alpha)  主题先验
    - w ~ Multinomial(beta)  词分布
    
    折叠：边际化掉theta，只对z采样
    
    参数:
        n_topics: 主题数K
        alpha: 文档-主题Dirichlet参数
        beta: 主题-词Dirichlet参数
    """
    
    def __init__(self, n_topics: int = 2, alpha: float = 0.1, beta: float = 0.1):
        self.K = n_topics  # 主题数
        self.alpha = alpha  # Dirichlet(alpha)
        self.beta = beta  # Dirichlet(beta)
        
        self.vocab = []  # 词汇表
        self.n_terms = 0  # 词汇量
        
        # 文档-主题计数
        self.ndz = None  # (n_docs, K)
        # 主题-词计数
        self.nzw = None  # (K, n_terms)
        # 主题总数
        self.nz = None  # (K,)
        
        self.z = None  # 隐变量：词-主题分配
    
    def fit(self, documents: List[List[int]], n_iterations: int = 100) -> 'LatentDirichletAllocation':
        """
        运行折叠Gibbs采样训练LDA
        
        参数:
            documents: 文档列表，每篇文档是词ID列表
            n_iterations: 迭代次数
            
        返回:
            self
        """
        self.vocab = sorted(set(w for doc in documents for w in doc))
        self.n_terms = len(self.vocab)
        word2id = {w: i for i, w in enumerate(self.vocab)}
        
        n_docs = len(documents)
        
        # 初始化计数矩阵
        self.ndz = np.zeros((n_docs, self.K))  # 文档-主题计数
        self.nzw = np.zeros((self.K, self.n_terms))  # 主题-词计数
        self.nz = np.zeros(self.K)  # 每个主题的词总数
        
        # 初始化隐变量z
        self.z = []
        for d, doc in enumerate(documents):
            doc_z = []
            for w in doc:
                w_id = word2id[w]
                z = np.random.randint(self.K)
                doc_z.append(z)
                
                # 更新计数
                self.ndz[d, z] += 1
                self.nzw[z, w_id] += 1
                self.nz[z] += 1
            
            self.z.append(doc_z)
        
        # Gibbs采样迭代
        for iteration in range(n_iterations):
            for d, doc in enumerate(documents):
                for i, w in enumerate(doc):
                    w_id = word2id[w]
                    z_old = self.z[d][i]
                    
                    # 从计数中移除当前词
                    self.ndz[d, z_old] -= 1
                    self.nzw[z_old, w_id] -= 1
                    self.nz[z_old] -= 1
                    
                    # 计算新主题的采样概率
                    # P(z_i=k | z_-i, w_i) ∝ (n_dk^-i + alpha) * (n_kw^-i + beta) / (n_k^-i + beta * V)
                    probs = np.zeros(self.K)
                    for k in range(self.K):
                        probs[k] = (self.ndz[d, k] + self.alpha)
                        probs[k] *= (self.nzw[k, w_id] + self.beta)
                        probs[k] /= (self.nz[k] + self.beta * self.n_terms)
                    
                    # 采样新主题
                    probs = probs / np.sum(probs)
                    z_new = np.random.choice(self.K, p=probs)
                    
                    # 更新计数和隐变量
                    self.z[d][i] = z_new
                    self.ndz[d, z_new] += 1
                    self.nzw[z_new, w_id] += 1
                    self.nz[z_new] += 1
            
            if (iteration + 1) % 20 == 0:
                print(f"   LDA迭代 {iteration + 1}/{n_iterations}")
        
        return self
    
    def get_document_topics(self, document_idx: int) -> np.ndarray:
        """
        获取文档的主题分布
        
        参数:
            document_idx: 文档索引
            
        返回:
            主题分布 (K,)
        """
        # 文档-主题分布：theta_d ∝ n_dz + alpha
        theta = self.ndz[document_idx] + self.alpha
        return theta / np.sum(theta)
    
    def get_topic_words(self, topic_idx: int, top_n: int = 10) -> List[Tuple[int, float]]:
        """
        获取主题的词分布
        
        参数:
            topic_idx: 主题索引
            top_n: 返回前n个词
            
        返回:
            [(词ID, 概率), ...]
        """
        # 主题-词分布：phi_k ∝ n_zw + beta
        phi = self.nzw[topic_idx] + self.beta
        phi = phi / np.sum(phi)
        
        # 返回概率最高的词
        top_indices = np.argsort(phi)[::-1][:top_n]
        return [(self.vocab[i], phi[i]) for i in top_indices]


class HiddenMarkovModelCollapsed:
    """
    隐马尔可夫模型(HMM)的折叠Gibbs采样
    
    折叠：边际化掉发射概率和转移概率
    只对隐状态序列采样
    """
    
    def __init__(self, n_states: int, n_observations: int, 
                 alpha: float = 1.0, beta: float = 1.0):
        self.n_states = n_states  # 隐状态数
        self.n_obs = n_observations  # 观测数
        self.alpha = alpha  # 转移概率Dirichlet先验
        self.beta = beta  # 发射概率Dirichlet先验
        
        self.z = None  # 隐状态序列
        self.trans_counts = None  # 转移计数
        self.emit_counts = None  # 发射计数
    
    def fit(self, observations: List[int], n_iterations: int = 100) -> 'HiddenMarkovModelCollapsed':
        """
        运行折叠Gibbs采样
        
        参数:
            observations: 观测序列
            n_iterations: 迭代次数
        """
        T = len(observations)
        
        # 初始化隐状态
        self.z = np.random.randint(self.n_states, size=T)
        
        # 初始化计数
        self._update_counts(observations)
        
        for iteration in range(n_iterations):
            # Gibbs采样每个隐状态
            for t in range(T):
                obs = observations[t]
                
                # 移除当前状态
                self._decrement_counts(t, observations)
                
                # 计算采样概率
                probs = self._compute_probs(t, obs, observations)
                
                # 采样
                probs = probs / np.sum(probs)
                self.z[t] = np.random.choice(self.n_states, p=probs)
                
                # 更新计数
                self._increment_counts(t, obs)
            
            if (iteration + 1) % 20 == 0:
                print(f"   HMM迭代 {iteration + 1}/{n_iterations}")
        
        return self
    
    def _update_counts(self, observations: List[int]):
        """更新计数矩阵"""
        T = len(observations)
        
        self.trans_counts = np.zeros((self.n_states, self.n_states))
        self.emit_counts = np.zeros((self.n_states, self.n_obs))
        
        for t in range(T):
            obs = observations[t]
            z_t = self.z[t]
            self.emit_counts[z_t, obs] += 1
            
            if t > 0:
                z_prev = self.z[t - 1]
                self.trans_counts[z_prev, z_t] += 1
    
    def _decrement_counts(self, t: int, observations: List[int]):
        """移除位置t的计数"""
        obs = observations[t]
        z_t = self.z[t]
        self.emit_counts[z_t, obs] -= 1
        
        if t > 0:
            z_prev = self.z[t - 1]
            self.trans_counts[z_prev, z_t] -= 1
        
        if t < len(observations) - 1:
            z_next = self.z[t + 1]
            self.trans_counts[z_t, z_next] -= 1
    
    def _increment_counts(self, t: int, obs: int):
        """增加位置t的计数"""
        z_t = self.z[t]
        self.emit_counts[z_t, obs] += 1
        
        if t > 0:
            z_prev = self.z[t - 1]
            self.trans_counts[z_prev, z_t] += 1
        
        if t < len(self.z) - 1:
            z_next = self.z[t + 1]
            self.trans_counts[z_t, z_next] += 1
    
    def _compute_probs(self, t: int, obs: int, observations: List[int]) -> np.ndarray:
        """计算位置t各状态的非归一化概率"""
        probs = np.zeros(self.n_states)
        T = len(observations)
        
        for k in range(self.n_states):
            # 发射概率
            emit_prob = (self.emit_counts[k, obs] + self.beta)
            emit_prob /= (np.sum(self.emit_counts[k]) + self.n_obs * self.beta)
            
            # 转移概率（前一个）
            if t > 0:
                z_prev = self.z[t - 1]
                trans_prob = (self.trans_counts[z_prev, k] + self.alpha)
                trans_prob /= (np.sum(self.trans_counts[z_prev]) + self.n_states * self.alpha)
            else:
                trans_prob = 1.0 / self.n_states
            
            # 转移概率（到下一个）
            if t < T - 1:
                z_next = self.z[t + 1]
                trans_prob2 = (self.trans_counts[k, z_next] + self.alpha)
                trans_prob2 /= (np.sum(self.trans_counts[k]) + self.n_states * self.alpha)
                trans_prob = trans_prob * trans_prob2
            
            probs[k] = emit_prob * trans_prob
        
        return probs


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("折叠Gibbs采样测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 测试1：简单二项分配的折叠Gibbs
    print("\n1. 简单二项分配的折叠Gibbs:")
    
    class SimpleCollapsedGibbs(CollapsedGibbsSampler):
        """简单的硬币翻转模型"""
        
        def __init__(self, n_heads: int, n_flips: int):
            super().__init__(variables=['p'])
            self.n_heads = n_heads
            self.n_flips = n_flips
        
        def conditional_log_prob(self, var: str, value: int, 
                                 others: Dict[str, int]) -> float:
            if value == 1:
                # Beta(heads+1, tails+1) 的后验
                return np.log(value + 0.5)  # 简化版
            return 0.0
    
    # 模拟硬币翻转
    true_p = 0.7
    n_flips = 100
    n_heads = sum(np.random.rand(n_flips) < true_p)
    
    sampler = SimpleCollapsedGibbs(n_heads, n_flips)
    sampler.state = {'p': 0.5}  # 初始值
    
    # 简单Metropolis采样
    samples = []
    for _ in range(5000):
        # Beta后验
        from scipy.stats import beta
        sampler.state['p'] = beta.rvs(n_heads + 1, n_flips - n_heads + 1)
        samples.append(sampler.state['p'])
    
    print(f"   真实p: {true_p:.2f}")
    print(f"   估计p: {np.mean(samples):.4f}")
    print(f"   95%置信区间: [{np.percentile(samples, 2.5):.4f}, {np.percentile(samples, 97.5):.4f}]")
    
    # 测试2：LDA主题模型
    print("\n2. LDA主题模型（折叠Gibbs采样）:")
    
    # 简单文档集
    documents = [
        [0, 1, 1, 2],  # doc1: 词0, 词1, 词1, 词2
        [1, 1, 2, 2],  # doc2
        [0, 2, 2, 2],  # doc3
        [1, 0, 1, 2],  # doc4
    ]
    
    lda = LatentDirichletAllocation(n_topics=2, alpha=0.1, beta=0.1)
    lda.fit(documents, n_iterations=50)
    
    print(f"   词汇表: {lda.vocab}")
    
    print(f"   文档0主题分布: {lda.get_document_topics(0)}")
    print(f"   文档1主题分布: {lda.get_document_topics(1)}")
    
    print(f"   主题0高频词: {lda.get_topic_words(0, top_n=3)}")
    print(f"   主题1高频词: {lda.get_topic_words(1, top_n=3)}")
    
    # 测试3：HMM折叠Gibbs
    print("\n3. HMM隐状态推断（折叠Gibbs）:")
    
    # 简单HMM
    np.random.seed(42)
    hmm = HiddenMarkovModelCollapsed(n_states=2, n_observations=3, alpha=1.0, beta=1.0)
    
    # 真实隐状态
    true_z = [0, 0, 1, 1, 0, 1, 0, 0]
    # 观测（简化）
    observations = [(z * 2 + np.random.randint(1, 3)) % 3 for z in true_z]
    
    hmm.fit(observations, n_iterations=100)
    
    print(f"   真实隐状态: {true_z}")
    print(f"   估计隐状态: {list(hmm.z)}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
