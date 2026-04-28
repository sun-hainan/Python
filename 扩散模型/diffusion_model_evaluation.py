"""
扩散模型评估：FID、IS、Inception Score
Diffusion Model Evaluation: FID, IS, Inception Score

扩散模型的评估指标用于衡量生成图像的质量和多样性。
主要指标包括FID、IS、Precision/Recall等。
"""

import numpy as np
from typing import Callable, Tuple, Optional, List
from scipy import linalg
from collections import defaultdict


class InceptionV3FeatureExtractor:
    """
    简化的Inception V3特征提取器
    
    用于计算IS和提取中间特征
    
    参数:
        dim: 输出特征维度
    """
    
    def __init__(self, dim: int = 2048):
        self.dim = dim
        
        # 简化的网络权重
        self.weights = {
            'conv1': np.random.randn(32, 3, 3, 3) * 0.02,
            'conv2': np.random.randn(64, 32, 3, 3) * 0.02,
            'pool': np.zeros((1, 1)),  # 占位
        }
    
    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        前向传播
        
        参数:
            x: 图像 (B, C, H, W)
            
        返回:
            (logits, features)
        """
        # 简化的特征提取
        # 实际应用中会经过完整的Inception网络
        
        B = len(x)
        
        # 模拟特征
        features = np.random.randn(B, self.dim) * 1.0
        
        # 模拟logits（用于分类）
        logits = np.random.randn(B, 1000)
        
        # softmax得到概率
        probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
        
        return logits, probs


class InceptionScore:
    """
    Inception Score (IS)
    
    IS = exp(E_x[KL(p(y|x) || p(y))])
    
    衡量生成图像的质量和多样性
    越高越好
    
    参数:
        extractor: 特征提取器
        splits: 分组数（通常10）
    """
    
    def __init__(self, extractor: Optional[InceptionV3FeatureExtractor] = None,
                 splits: int = 10):
        self.extractor = extractor or InceptionV3FeatureExtractor()
        self.splits = splits
    
    def compute(self, images: np.ndarray) -> Tuple[float, float]:
        """
        计算IS
        
        参数:
            images: 图像 (N, C, H, W) 或 (N, H, W, C)
            
        返回:
            (mean, std) IS均值和标准差
        """
        # 预处理
        if images.ndim == 4:
            if images.shape[1] == 3:  # (N, C, H, W)
                images = images.transpose(0, 2, 3, 1)  # (N, H, W, C)
        
        # 归一化到[0, 1]
        if images.max() > 1:
            images = images / 255.0
        
        # 获取预测概率
        _, probs = self.extractor.forward(images)
        
        # 计算KL散度
        # p(y|x) vs p(y) = E_x[p(y|x)]
        p_y = np.mean(probs, axis=0)
        
        kl_scores = []
        for i in range(len(probs)):
            p_y_given_x = probs[i]
            kl = p_y_given_x * (np.log(p_y_given_x + 1e-10) - np.log(p_y + 1e-10))
            kl_scores.append(np.sum(kl))
        
        # 分组计算均值和方差
        split_scores = []
        chunk_size = len(kl_scores) // self.splits
        
        for i in range(self.splits):
            start = i * chunk_size
            end = (i + 1) * chunk_size if i < self.splits - 1 else len(kl_scores)
            split_kl = kl_scores[start:end]
            split_scores.append(np.exp(np.mean(split_kl)))
        
        return np.mean(split_scores), np.std(split_scores)


class FID:
    """
    Fréchet Inception Distance (FID)
    
    FID = ||mu_1 - mu_2||^2 + Tr(Sigma_1 + Sigma_2 - 2*sqrt(Sigma_1*Sigma_2))
    
    衡量真实分布和生成分布之间的距离
    越低越好
    
    参数:
        extractor: 特征提取器
    """
    
    def __init__(self, extractor: Optional[InceptionV3FeatureExtractor] = None):
        self.extractor = extractor or InceptionV3FeatureExtractor()
    
    def compute_statistics(self, images: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        计算图像集合的统计量
        
        参数:
            images: 图像
            
        返回:
            (mu, sigma) 均值和协方差
        """
        # 预处理
        if images.ndim == 4:
            if images.shape[1] == 3:
                images = images.transpose(0, 2, 3, 1)
        
        if images.max() > 1:
            images = images / 255.0
        
        # 提取特征
        features, _ = self.extractor.forward(images)
        
        # 计算统计量
        mu = np.mean(features, axis=0)
        sigma = np.cov(features, rowvar=False)
        
        return mu, sigma
    
    def compute(self, real_images: np.ndarray, 
                generated_images: np.ndarray) -> float:
        """
        计算FID
        
        参数:
            real_images: 真实图像
            generated_images: 生成图像
            
        返回:
            FID分数
        """
        # 计算各自的统计量
        mu_real, sigma_real = self.compute_statistics(real_images)
        mu_gen, sigma_gen = self.compute_statistics(generated_images)
        
        # 计算FID
        diff = mu_real - mu_gen
        
        # 协方差矩阵平方根（使用SVD）
        covmean, _ = linalg.sqrtm(sigma_real @ sigma_gen, disp=False)
        
        # 数值稳定性
        if np.iscomplexobj(covmean):
            covmean = covmean.real
        
        fid = np.dot(diff, diff) + np.trace(sigma_real + sigma_gen - 2 * covmean)
        
        return fid


class PrecisionRecall:
    """
    Precision和Recall for 生成模型
    
    衡量生成质量和覆盖度
    
    参数:
        k: 近邻数量
    """
    
    def __init__(self, k: int = 5):
        self.k = k
    
    def compute(self, real_features: np.ndarray,
                generated_features: np.ndarray) -> Tuple[float, float]:
        """
        计算Precision和Recall
        
        参数:
            real_features: 真实图像特征
            generated_features: 生成图像特征
            
        返回:
            (precision, recall)
        """
        # 计算最近邻
        from sklearn.neighbors import NearestNeighbors
        
        # 真实样本的最近邻（用于Recall）
        nn_real = NearestNeighbors(n_neighbors=self.k + 1)
        nn_real.fit(real_features)
        
        # 生成样本的最近邻（用于Precision）
        nn_gen = NearestNeighbors(n_neighbors=self.k + 1)
        nn_gen.fit(generated_features)
        
        # Recall: 生成样本有多少在真实样本附近
        distances_gen, _ = nn_real.kneighbors(generated_features)
        recall = np.mean(distances_gen[:, self.k] < 0.5)  # 阈值
        
        # Precision: 真实样本有多少在生成样本附近
        distances_real, _ = nn_gen.kneighbors(real_features)
        precision = np.mean(distances_real[:, self.k] < 0.5)
        
        return precision, recall


class GenerationMetrics:
    """
    综合生成指标计算器
    
    参数:
        extractor: 特征提取器
    """
    
    def __init__(self, extractor: Optional[InceptionV3FeatureExtractor] = None):
        self.extractor = extractor or InceptionV3FeatureExtractor()
        self.is_calculator = InceptionScore(extractor)
        self.fid_calculator = FID(extractor)
        self.pr_calculator = PrecisionRecall()
    
    def compute_all(self, real_images: np.ndarray,
                   generated_images: np.ndarray) -> dict:
        """
        计算所有指标
        
        参数:
            real_images: 真实图像
            generated_images: 生成图像
            
        返回:
            指标字典
        """
        # 提取特征
        _, real_probs = self.extractor.forward(real_images)
        _, gen_probs = self.extractor.forward(generated_images)
        
        # IS (生成图像)
        is_mean, is_std = self.is_calculator.compute(generated_images)
        
        # FID
        fid = self.fid_calculator.compute(real_images, generated_images)
        
        # Precision/Recall
        real_features, _ = self.extractor.forward(real_images)
        gen_features, _ = self.extractor.forward(generated_images)
        precision, recall = self.pr_calculator.compute(real_features, gen_features)
        
        return {
            'IS_mean': is_mean,
            'IS_std': is_std,
            'FID': fid,
            'Precision': precision,
            'Recall': recall,
        }


class ImageQualityAssessment:
    """
    图像质量评估（无参考）
    
    参数:
        method: 评估方法
    """
    
    @staticmethod
    defbrisque(features: np.ndarray) -> float:
        """
        BRISQUE (Blind/Referenceless Image Spatial Quality Evaluator)
        
        简化的实现
        
        参数:
            features: 图像特征
            
        返回:
            质量分数（越低越好）
        """
        # 简化的质量评估
        # 实际应用中需要复杂的特征提取和回归
        
        # 使用方差作为粗略指标
        variance = np.var(features)
        
        return 100.0 / (1.0 + variance)
    
    @staticmethod
    def sharpness(image: np.ndarray) -> float:
        """
        图像锐度（拉普拉斯方差）
        
        参数:
            image: 图像
            
        返回:
            锐度分数
        """
        # 简化的拉普拉斯算子
        if image.ndim == 3 and image.shape[2] == 3:
            # RGB图像，转灰度
            gray = 0.299 * image[:,:,0] + 0.587 * image[:,:,1] + 0.114 * image[:,:,2]
        else:
            gray = image
        
        # 拉普拉斯核
        laplacian = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])
        
        # 简化的卷积
        from scipy.ndimage import convolve
        lap_img = convolve(gray, laplacian, mode='reflect')
        
        return np.var(lap_img)


# ============================================================
# 测试代码
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("扩散模型评估测试")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 模拟图像
    n_real = 100
    n_gen = 100
    
    real_images = np.random.randint(0, 256, (n_real, 3, 64, 64), dtype=np.uint8)
    gen_images = np.random.randint(0, 256, (n_gen, 3, 64, 64), dtype=np.uint8)
    
    # 测试1：Inception Score
    print("\n1. Inception Score:")
    
    extractor = InceptionV3FeatureExtractor()
    is_calc = InceptionScore(extractor, splits=10)
    
    is_mean, is_std = is_calc.compute(gen_images)
    
    print(f"   IS = {is_mean:.4f} ± {is_std:.4f}")
    
    # 测试2：FID
    print("\n2. Fréchet Inception Distance:")
    
    fid_calc = FID(extractor)
    
    fid = fid_calc.compute(real_images, gen_images)
    
    print(f"   FID = {fid:.4f}")
    
    # 测试3：Precision和Recall
    print("\n3. Precision and Recall:")
    
    pr_calc = PrecisionRecall(k=5)
    
    real_features = extractor.forward(real_images)[1]
    gen_features = extractor.forward(gen_images)[1]
    
    precision, recall = pr_calc.compute(real_features, gen_features)
    
    print(f"   Precision = {precision:.4f}")
    print(f"   Recall = {recall:.4f}")
    
    # 测试4：综合指标
    print("\n4. 综合生成指标:")
    
    metrics = GenerationMetrics(extractor)
    results = metrics.compute_all(real_images, gen_images)
    
    for name, value in results.items():
        print(f"   {name}: {value:.4f}")
    
    # 测试5：图像质量评估
    print("\n5. 图像质量评估:")
    
    # 模拟一些图像
    sharp_image = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    blur_image = sharp_image.copy()
    
    # 添加模糊
    for _ in range(5):
        blur_image = blur_image[:, 1:] * 0.5 + blur_image[:, :-1] * 0.5
        blur_image = blur_image[1:, :] * 0.5 + blur_image[:-1, :] * 0.5
        blur_image = blur_image.astype(np.uint8)
    
    sharp_score = ImageQualityAssessment.sharpness(sharp_image)
    blur_score = ImageQualityAssessment.sharpness(blur_image.astype(np.float32))
    
    print(f"   清晰图像锐度: {sharp_score:.4f}")
    print(f"   模糊图像锐度: {blur_score:.4f}")
    
    # 测试6：统计量计算
    print("\n6. 特征统计量:")
    
    mu, sigma = fid_calc.compute_statistics(real_images)
    
    print(f"   均值向量维度: {mu.shape}")
    print(f"   协方差矩阵维度: {sigma.shape}")
    print(f"   均值范数: {np.linalg.norm(mu):.4f}")
    print(f"   协方差迹: {np.trace(sigma):.4f}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
