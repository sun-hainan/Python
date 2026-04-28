"""
差分隐私深度学习
==========================================

【算法原理】
在深度学习训练过程中保护训练数据隐私。核心思想是在梯度更新时
引入噪声，并限制单个样本对梯度的影响（梯度裁剪），从而实现DP保证。

【时间复杂度】O(epochs × dataset_size × model_params)
【空间复杂度】O(model_params + batch_size × model_params)

【应用场景】
- 差分隐私SGD训练神经网络
- 联邦学习中的隐私保护
- 会员推断攻击防御
- 差分隐私词向量学习

【何时使用】
- 训练数据包含敏感信息
- 需要防止模型泄露训练数据
- 对抗会员推断攻击
"""

import numpy as np
from typing import List, Tuple, Optional
import math


# ========================================
# 第1部分：差分隐私SGD核心
# ========================================

class DPSGD:
    """
    差分隐私随机梯度下降

    【核心思想】
    1. 梯度裁剪：将每个样本的梯度裁剪到L2范数C以内
    2. 噪声注入：在聚合梯度中添加高斯噪声
    3. 隐私账户：跟踪隐私预算消耗（DP-SGD论文）

    【参数】
    - noise_multiplier: 噪声乘数 σ/C，典型值1.0-10.0
    - l2_clip_norm: 裁剪范数C，典型值1.0-4.0
    - secure_seed: 是否使用安全随机数（CSPRNG）
    """

    def __init__(self, noise_multiplier: float = 1.0, l2_clip_norm: float = 1.0):
        # 噪声乘数：噪声标准差 = noise_multiplier × 裁剪范数
        self.noise_multiplier = noise_multiplier
        # 梯度裁剪范数：限制单个样本的梯度L2范数
        self.l2_clip_norm = l2_clip_norm

    def clip_gradients(self, gradients: List[np.ndarray]) -> List[np.ndarray]:
        """
        梯度裁剪：将梯度L2范数裁剪到[0, l2_clip_norm]

        【实现】对于每个参数梯度：
        - 计算其L2范数
        - 如果范数 > C，则缩放梯度使其范数等于C
        """
        clipped = []
        for grad in gradients:
            # 计算L2范数
            l2_norm = np.sqrt(np.sum(grad ** 2))
            # 如果范数超过裁剪阈值，则缩放
            if l2_norm > self.l2_clip_norm:
                scale = self.l2_clip_norm / l2_norm
                clipped.append(grad * scale)
            else:
                clipped.append(grad)
        return clipped

    def add_noise(self, gradients: List[np.ndarray]) -> List[np.ndarray]]:
        """
        添加高斯噪声实现差分隐私

        【原理】对于d维输出和敏感性Δ，添加N(0, σ²Δ²I)的噪声
        满足(ε, δ)-DP，其中σ是噪声乘数
        """
        noisy_grads = []
        for grad in gradients:
            # 计算噪声标准差：σ × 裁剪范数
            noise_std = self.noise_multiplier * self.l2_clip_norm
            # 生成高斯噪声
            noise = np.random.normal(0, noise_std, grad.shape)
            noisy_grads.append(grad + noise)
        return noisy_grads

    def compute_sensitivity(self, batch_size: int) -> float:
        """
        计算敏感性：batch_size个样本的梯度聚合的L2敏感性

        【定义】敏感性 = 裁剪范数 / batch_size
        因为每个样本梯度被裁剪到C，替换一个样本最多改变C/batch_size
        """
        return self.l2_clip_norm / batch_size


class DPAdam:
    """
    差分隐私Adam优化器

    【原理】在标准Adam更新规则上叠加梯度噪声
    - m_t = β₁·m_{t-1} + (1-β₁)·g_t         （ momentum ）
    - v_t = β₂·v_{t-1} + (1-β₂)·g_t²       （ adaptive lr ）
    - g_t_noise = g_t + N(0, σ²C²)          （ 加噪梯度 ）
    - θ_t = θ_{t-1} - α·m_t/(√v_t + ε)    （ 参数更新 ）
    """

    def __init__(self, lr: float = 0.001, noise_multiplier: float = 1.0,
                 l2_clip_norm: float = 1.0, beta1: float = 0.9, beta2: float = 0.999):
        self.lr = lr
        self.dp_sgd = DPSGD(noise_multiplier, l2_clip_norm)
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = 1e-8
        # 一阶矩估计（momentum）
        self.m = None
        # 二阶矩估计（adaptive lr）
        self.v = None
        self.t = 0

    def update(self, params: np.ndarray, gradients: np.ndarray) -> np.ndarray:
        """
        执行一步DP-Adam更新

        【步骤】
        1. 裁剪梯度
        2. 添加噪声
        3. 更新一阶/二阶矩估计
        4. 偏差校正
        5. 更新参数
        """
        self.t += 1

        # 第1步：裁剪梯度
        clipped_grad = gradients
        grad_norm = np.linalg.norm(clipped_grad)
        if grad_norm > self.dp_sgd.l2_clip_norm:
            clipped_grad = clipped_grad * (self.dp_sgd.l2_clip_norm / grad_norm)

        # 第2步：添加高斯噪声
        noise_std = self.dp_sgd.noise_multiplier * self.dp_sgd.l2_clip_norm
        noisy_grad = clipped_grad + np.random.normal(0, noise_std, gradients.shape)

        # 第3步：初始化/更新动量
        if self.m is None:
            self.m = np.zeros_like(gradients)
        self.m = self.beta1 * self.m + (1 - self.beta1) * noisy_grad

        # 第4步：初始化/更新二阶矩
        if self.v is None:
            self.v = np.zeros_like(gradients)
        self.v = self.beta2 * self.v + (1 - self.beta2) * (noisy_grad ** 2)

        # 第5步：偏差校正
        m_hat = self.m / (1 - self.beta1 ** self.t)
        v_hat = self.v / (1 - self.beta2 ** self.t)

        # 第6步：参数更新
        params = params - self.lr * m_hat / (np.sqrt(v_hat) + self.epsilon)
        return params


# ========================================
# 第2部分：隐私预算计算
# ========================================

def compute_privacy_budget(epochs: int, batch_size: int, noise_multiplier: float,
                          delta: float = 1e-5) -> float:
    """
    计算DP-SGD的隐私预算ε（使用 RDP + 顺序组合）

    【算法】基于随机梯度下降的隐私分析
    - 每个样本的梯度敏感度 = C / batch_size
    - 使用Rényi差分隐私（RDP）分析

    【返回】隐私预算ε
    """
    # RDP的μ参数（相当于σ²的函数）
    # 对于高斯机制：μ = (0.5 * C²) / (noise_multiplier * C)² = 1/(2*noise_multiplier²)
    # 但实际分析需要考虑组合
    sensitivity = 1.0 / batch_size
    mu = sensitivity ** 2 / (2 * noise_multiplier ** 2)

    # 样本数（假设整个数据集是一个epoch）
    samples_per_epoch = 1.0 / sensitivity

    # 总迭代次数
    total_steps = epochs * samples_per_epoch / batch_size

    # RDP → (ε, δ)-DP 转换
    # 使用现有bounds: RDP(μ) 转换为 (ε,δ)-DP
    # 简化近似：ε ≈ sqrt(2*mu*log(1/delta)) * sqrt(total_steps)
    epsilon = math.sqrt(2 * mu * math.log(1.25 / delta)) * math.sqrt(total_steps)

    return epsilon


def compute_rdp_accountant(steps: int, noise_multiplier: float,
                          sample_rate: float, orders: List[float]) -> List[float]:
    """
    Rényi差分隐私（RDP）账户

    【原理】RDP提供更紧的隐私界限，通过Rényi散度度量

    【参数】
    - steps: 总训练步数
    - noise_multiplier: σ/C
    - sample_rate: 批次大小/数据集大小
    - orders: Rényi阶数（通常取[1.1, 1.2, ..., 10]）
    """
    rdp = []
    for alpha in orders:
        # 每个样本的RDP
        # RDP for Gaussian mechanism: α/(2*σ²) for α≥2
        # 结合采样率：乘以sample_rate
        if alpha >= 2:
            rdp_alpha = (alpha * sample_rate) / (2 * noise_multiplier ** 2)
        else:
            # α接近1时的处理
            rdp_alpha = sample_rate * 1.0 / (noise_multiplier ** 2)
        # 组合（加法）
        rdp.append(rdp_alpha * steps)
    return rdp


# ========================================
# 第3部分：成员推断防御
# ========================================

class MembershipInferenceDefense:
    """
    成员推断攻击防御

    【攻击原理】攻击者训练一个影子模型，预测某样本是否在训练集中
    - 如果模型对该样本的loss很小，说明可能是成员

    【防御方法】
    1. 差分隐私：降低模型对训练数据的记忆
    2. 正则化：early stopping, L2正则
    3. 预测熵阈值：在高熵预测上拒绝推断
    """

    def __init__(self, privacy_budget: float = 8.0, use_dp: bool = True):
        self.privacy_budget = privacy_budget
        self.use_dp = use_dp
        # 预测熵阈值：高于此值认为不可推断
        self.entropy_threshold = 2.0

    def compute_prediction_entropy(self, probabilities: np.ndarray) -> float:
        """
        计算预测熵

        H = -∑ p_i · log(p_i)
        高熵 = 低置信度 = 难以判断是否成员
        """
        entropy = 0.0
        for p in probabilities:
            if 0 < p < 1:
                entropy -= p * math.log(p)
        return entropy

    def defend_prediction(self, model, x: np.ndarray, threshold: float = None) -> dict:
        """
        对预测结果进行防御处理

        【策略】
        1. 如果使用DP，输出天然带噪声保护
        2. 对高熵预测添加随机扰动
        """
        threshold = threshold or self.entropy_threshold

        # 正常预测
        logits = model.predict_logits(x)
        probs = self._softmax(logits)
        entropy = self.compute_prediction_entropy(probs)

        # 如果熵很高（不确定性大），则拒绝明确回答
        if entropy > threshold:
            return {
                "prediction": None,
                "confidence": None,
                "entropy": entropy,
                "defended": True,
                "reason": "high_entropy_obfuscated"
            }

        return {
            "prediction": np.argmax(probs),
            "confidence": np.max(probs),
            "entropy": entropy,
            "defended": False,
            "reason": "normal"
        }

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Softmax函数"""
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)


# ========================================
# 第4部分：差分隐私词向量
# ========================================

class DPWord2Vec:
    """
    差分隐私Word2Vec

    【原理】在词向量训练中注入噪声，保护原始语料

    【方法】
    1. 目标函数扰动：在词共现统计量上加噪声
    2. 梯度扰动：训练时对梯度加噪声
    3. 输入扰动：对输入词向量加噪声

    【隐私保护】
    - 对词共现矩阵添加拉普拉斯噪声
    - 通过指数机制选择词向量维度
    """

    def __init__(self, vocab_size: int, embedding_dim: int,
                 epsilon: float = 1.0, noise_multiplier: float = 1.0):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        # 隐私预算
        self.epsilon = epsilon
        # 噪声乘数
        self.noise_multiplier = noise_multiplier
        # 词向量矩阵
        self.W = None
        # 上下文向量矩阵（Skip-gram使用）
        self.C = None

    def fit(self, sentences: List[List[int]], epochs: int = 5,
            window_size: int = 5, learning_rate: float = 0.025):
        """
        训练差分隐私词向量

        【步骤】
        1. 构建词共现矩阵
        2. 添加噪声到共现计数
        3. 使用SVD降维获得词向量
        """
        # 构建原始共现矩阵
        cooccur = self._build_cooccurrence_matrix(sentences, window_size)

        # 添加拉普拉斯噪声实现DP
        noisy_cooccur = self._add_laplace_noise(cooccur)

        # SVD分解得到词向量
        self.W = self._svd_embedding(noisy_cooccur, self.embedding_dim)

        return self.W

    def _build_cooccurrence_matrix(self, sentences: List[List[int]],
                                   window_size: int) -> np.ndarray:
        """
        构建词共现矩阵

        【定义】C_ij = 词i在词j上下文中出现的次数
        """
        cooccur = np.zeros((self.vocab_size, self.vocab_size))
        for sentence in sentences:
            for i, center_word in enumerate(sentence):
                # 窗口边界
                start = max(0, i - window_size)
                end = min(len(sentence), i + window_size + 1)
                for j in range(start, end):
                    if i != j:
                        context_word = sentence[j]
                        # 共现次数（距离衰减）
                        distance = abs(i - j)
                        cooccur[center_word][context_word] += 1.0 / distance
        return cooccur

    def _add_laplace_noise(self, cooccur: np.ndarray) -> np.ndarray:
        """
        添加拉普拉斯噪声

        【原理】拉普拉斯机制用于计数查询：
        对于计数查询f，输出 f(x) + Lap(Δf/ε)
        敏感性Δ = 1（替换一个词最多改变共现1次）
        """
        # 拉普拉斯噪声参数 b = 1/ε
        b = 1.0 / self.epsilon
        noise = np.random.laplace(0, b, cooccur.shape)
        # 确保非负（负共现无意义）
        return np.maximum(cooccur + noise, 0)

    def _svd_embedding(self, matrix: np.ndarray, dim: int) -> np.ndarray:
        """
        使用SVD分解获得词向量

        【原理】对共现矩阵做截断SVD：
        M ≈ U·Σ·V^T ≈ (U·Σ^{1/2}) · (Σ^{1/2}·V^T})
        """
        # SVD分解
        U, S, Vt = np.linalg.svd(matrix, full_matrices=False)
        # 取前dim个奇异值开方的结果作为词向量
        embedding = U[:, :dim] * np.sqrt(S[:dim])
        return embedding

    def most_similar(self, word: int, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        查找最相似的词
        """
        if self.W is None:
            raise ValueError("模型未训练")

        # 计算余弦相似度
        word_vec = self.W[word]
        similarities = np.dot(self.W, word_vec) / (
            np.linalg.norm(self.W, axis=1) * np.linalg.norm(word_vec) + 1e-9
        )
        # 排序（排除自身）
        indices = np.argsort(similarities)[::-1]
        results = [(i, similarities[i]) for i in indices if i != word][:top_k]
        return results


# ========================================
# 测试代码
# ========================================

if __name__ == "__main__":
    print("=" * 50)
    print("差分隐私深度学习 - 测试")
    print("=" * 50)

    # 测试1：DP-SGD梯度裁剪与噪声
    print("\n【测试1】DP-SGD 梯度处理")
    dpsgd = DPSGD(noise_multiplier=1.0, l2_clip_norm=1.0)

    # 模拟batch梯度
    fake_grads = [np.random.randn(10, 10) for _ in range(3)]
    print(f"原始梯度L2范数: {[np.linalg.norm(g) for g in fake_grads]}")

    clipped = dpsgd.clip_gradients(fake_grads)
    print(f"裁剪后L2范数: {[np.linalg.norm(g) for g in clipped]}")

    noisy = dpsgd.add_noise(clipped)
    print(f"加噪后L2范数: {[np.linalg.norm(g) for g in noisy]}")

    # 测试2：DP-Adam更新
    print("\n【测试2】DP-Adam 更新")
    dpAdam = DPAdam(lr=0.001, noise_multiplier=1.0, l2_clip_norm=1.0)
    params = np.random.randn(10)
    grads = np.random.randn(10)
    new_params = dpAdam.update(params, grads)
    print(f"参数更新: {params[:3]} -> {new_params[:3]}")

    # 测试3：隐私预算计算
    print("\n【测试3】隐私预算计算")
    eps = compute_privacy_budget(
        epochs=10,
        batch_size=256,
        noise_multiplier=1.0,
        delta=1e-5
    )
    print(f"10个epoch后的隐私预算ε ≈ {eps:.2f}")
    print(f"建议：ε < 8 通常可接受，ε < 2 更严格")

    # 测试4：成员推断防御
    print("\n【测试4】成员推断防御")

    class MockModel:
        def predict_logits(self, x):
            return np.array([2.0, -1.0, 0.5])

    defense = MembershipInferenceDefense(privacy_budget=8.0)
    model = MockModel()
    result = defense.defend_prediction(model, np.array([1.0]))
    print(f"防御结果: {result}")

    # 测试5：差分隐私Word2Vec
    print("\n【测试5】DP-Word2Vec")
    np.random.seed(42)
    dp2v = DPWord2Vec(vocab_size=100, embedding_dim=10, epsilon=1.0)
    sentences = [[np.random.randint(0, 100) for _ in range(20)] for _ in range(50)]
    embedding = dp2v.fit(sentences, epochs=3)
    print(f"词向量形状: {embedding.shape}")
    print(f"词向量样例(词0): {embedding[0][:5]}")

    print("\n" + "=" * 50)
    print("所有测试完成！")
    print("=" * 50)
