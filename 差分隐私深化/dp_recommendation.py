"""
推荐系统差分隐私 (Differential Privacy for Recommendation Systems)
================================================================

算法原理:
---------
推荐系统通过分析用户行为数据来预测用户偏好，但这些数据包含敏感的个人信息。
差分隐私为推荐系统提供了严格的隐私保护框架：

1. 协同过滤（Collaborative Filtering）：
   - 基于用户-物品交互矩阵，找到相似用户/物品进行推荐
   - DP通过扰动相似度计算或评分来保护隐私

2. 矩阵分解（Matrix Factorization）：
   - 将高维用户-物品评分矩阵分解为低维用户和物品隐向量
   - DP通过添加噪声到梯度或最终因子来保护用户评分

3. 差分隐私矩阵分解（DP-MF）：
   - 在矩阵分解过程中引入DP噪声
   - 确保攻击者无法通过观察推荐结果推断特定用户的偏好

核心技术：
- 敏感度计算：用户-物品交互矩阵的秩一更新影响
- 噪声注入：在梯度下降或SVD分解过程中添加噪声
- 隐私预算分配：分解到每个迭代或每个用户

时间复杂度: O(k * n * m) 其中k为隐向量维度，n为用户数，m为物品数
空间复杂度: O(k * (n + m)) 存储隐向量矩阵

应用场景:
--------
- 电商推荐：保护用户购买历史和浏览偏好
- 音乐推荐：保护用户听歌记录和收藏
- 新闻推荐：保护用户阅读偏好和兴趣
- 电影推荐：保护用户评分和观看历史
"""

import numpy as np
from numpy.random import Laplace, normal


def build_user_item_matrix(interactions, n_users, n_items, default_score=0):
    """
    构建用户-物品交互矩阵
    
    参数:
        interactions: 交互列表，格式为[(user_id, item_id, score), ...]
        n_users: 用户总数
        n_items: 物品总数
        default_score: 默认评分（表示无交互）
    
    返回:
        matrix: n_users x n_items 的评分矩阵
    """
    # 初始化矩阵，默认评分为0（无交互）
    matrix = np.full((n_users, n_items), default_score, dtype=np.float64)
    
    # 填充实际交互数据
    for user_id, item_id, score in interactions:
        if 0 <= user_id < n_users and 0 <= item_id < n_items:
            matrix[user_id, item_id] = score
    
    return matrix


def pearson_similarity_with_dp(user_ratings, v_user_ratings, epsilon=1.0):
    """
    带差分隐私的Pearson相似度计算
    
    原理：Pearson相似度衡量两个用户偏好的线性相关性，
    通过添加Laplace噪声来保护评分数据
    
    参数:
        user_ratings: 用户A的评分向量
        v_user_ratings: 用户B的评分向量
        epsilon: 隐私预算
    
    返回:
        noisy_similarity: 添加噪声后的Pearson相似度
    """
    # 找出两个用户都有评分的物品
    common_items = (user_ratings > 0) & (v_user_ratings > 0)
    n_common = np.sum(common_items)
    
    if n_common < 2:
        return 0.0  # 共同评分数太少，无法计算相似度
    
    # 提取共同评分
    ratings_a = user_ratings[common_items]
    ratings_b = v_user_ratings[common_items]
    
    # 计算Pearson相关系数
    mean_a = np.mean(ratings_a)
    mean_b = np.mean(ratings_b)
    
    # 计算协方差和标准差
    cov = np.sum((ratings_a - mean_a) * (ratings_b - mean_b))
    std_a = np.sqrt(np.sum((ratings_a - mean_a) ** 2))
    std_b = np.sqrt(np.sum((ratings_b - mean_b) ** 2))
    
    if std_a == 0 or std_b == 0:
        return 0.0
    
    similarity = cov / (std_a * std_b)
    
    # 敏感性分析：移除一条评分最多改变相似度约2/n
    sensitivity = 2.0 / n_common
    
    # 添加Laplace噪声
    noise = Laplace(scale=sensitivity / epsilon)
    noisy_similarity = similarity + noise
    
    # 将相似度限制在[-1, 1]范围内
    return np.clip(noisy_similarity, -1.0, 1.0)


def collaborative_filtering_dp(user_item_matrix, target_user, k_neighbors=10, epsilon=1.0):
    """
    差分隐私协同过滤推荐
    
    原理：找到与目标用户最相似的k个用户，利用他们的评分预测目标用户的未知评分
    相似度计算中引入DP噪声保护用户隐私
    
    参数:
        user_item_matrix: 用户-物品评分矩阵
        target_user: 目标用户索引
        k_neighbors: 近邻数量
        epsilon: 隐私预算
    
    返回:
        predictions: 对目标用户所有物品的预测评分
    """
    n_users, n_items = user_item_matrix.shape
    
    # 获取目标用户的评分
    target_ratings = user_item_matrix[target_user]
    
    # 计算目标用户与所有其他用户的相似度
    similarities = []
    for other_user in range(n_users):
        if other_user == target_user:
            continue
        other_ratings = user_item_matrix[other_user]
        sim = pearson_similarity_with_dp(target_ratings, other_ratings, epsilon)
        similarities.append((other_user, sim))
    
    # 按相似度排序，取前k个近邻
    similarities.sort(key=lambda x: abs(x[1]), reverse=True)
    k_neighbors = min(k_neighbors, len(similarities))
    top_neighbors = similarities[:k_neighbors]
    
    # 加权平均计算预测评分
    predictions = np.zeros(n_items)
    for item_id in range(n_items):
        if target_ratings[item_id] > 0:
            # 目标用户已评分的物品保持原评分
            predictions[item_id] = target_ratings[item_id]
        else:
            # 预测未评分物品
            weighted_sum = 0.0
            sim_sum = 0.0
            for neighbor_id, sim in top_neighbors:
                neighbor_rating = user_item_matrix[neighbor_id, item_id]
                if neighbor_rating > 0:
                    weighted_sum += sim * neighbor_rating
                    sim_sum += abs(sim)
            
            if sim_sum > 0:
                predictions[item_id] = weighted_sum / sim_sum
    
    return predictions


def matrix_factorization_sgd(R, n_factors=10, learning_rate=0.01, 
                             regularization=0.1, n_epochs=50, epsilon=1.0):
    """
    差分隐私矩阵分解 - 使用随机梯度下降
    
    原理：将用户-物品评分矩阵R分解为用户矩阵U和物品矩阵V的乘积
    通过 SGD 优化，过程中引入DP噪声保护梯度
    
    参数:
        R: 评分矩阵 (n_users x n_items)
        n_factors: 隐向量维度
        learning_rate: 学习率
        regularization: L2正则化系数
        n_epochs: 迭代轮数
        epsilon: 隐私预算
    
    返回:
        U: 用户隐向量矩阵 (n_users x n_factors)
        V: 物品隐向量矩阵 (n_items x n_factors)
    """
    n_users, n_items = R.shape
    
    # 初始化隐向量矩阵（使用小的随机值）
    np.random.seed(42)
    U = np.random.randn(n_users, n_factors) * 0.1
    V = np.random.randn(n_items, n_factors) * 0.1
    
    # 获取有评分的位置
    rated_positions = np.where(R > 0)
    n_ratings = len(rated_positions[0])
    
    # 计算梯度敏感性：单条评分的最大影响
    sensitivity = 2 * learning_rate * np.sqrt(n_factors)
    
    # 分摊隐私预算到每个epoch
    epsilon_per_epoch = epsilon / n_epochs
    
    for epoch in range(n_epochs):
        # 随机打乱评分顺序
        indices = np.random.permutation(n_ratings)
        
        for idx in indices:
            u_idx = rated_positions[0][idx]  # 用户索引
            i_idx = rated_positions[1][idx]  # 物品索引
            r_ui = R[u_idx, i_idx]  # 真实评分
            
            # 计算预测评分
            pred = np.dot(U[u_idx], V[i_idx])
            error = r_ui - pred
            
            # 计算梯度
            grad_u = error * V[i_idx] - regularization * U[u_idx]
            grad_v = error * U[u_idx] - regularization * V[i_idx]
            
            # 添加差分隐私噪声到梯度
            noise_scale = sensitivity / epsilon_per_epoch
            noisy_grad_u = grad_u + normal(0, noise_scale, size=n_factors)
            noisy_grad_v = grad_v + normal(0, noise_scale, size=n_factors)
            
            # 更新隐向量
            U[u_idx] += learning_rate * noisy_grad_u
            V[i_idx] += learning_rate * noisy_grad_v
    
    return U, V


def predict_dp_matrix_factorization(U, V):
    """
    使用矩阵分解结果预测评分
    
    参数:
        U: 用户隐向量矩阵
        V: 物品隐向量矩阵
    
    返回:
        predictions: 预测评分矩阵
    """
    return np.dot(U, V.T)


def item_based_dp_recommend(user_item_matrix, target_item, k_neighbors=10, epsilon=1.0):
    """
    物品相似度差分隐私推荐
    
    原理：基于物品的协同过滤，找到与目标物品最相似的k个物品，
    推荐与用户已喜爱物品相似的其他物品
    
    参数:
        user_item_matrix: 用户-物品矩阵
        target_item: 目标物品索引
        k_neighbors: 近邻数量
        epsilon: 隐私预算
    
    返回:
        similar_items: 相似物品列表及相似度分数
    """
    n_users, n_items = user_item_matrix.shape
    
    # 获取目标物品的评分向量
    target_ratings = user_item_matrix[:, target_item]
    
    # 计算目标物品与所有其他物品的相似度
    similarities = []
    for item_id in range(n_items):
        if item_id == target_item:
            continue
        item_ratings = user_item_matrix[:, item_id]
        
        # 使用DP Pearson相似度
        sim = pearson_similarity_with_dp(target_ratings, item_ratings, epsilon)
        similarities.append((item_id, sim))
    
    # 排序并返回前k个
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:k_neighbors]


# ============== 测试代码 ==============
if __name__ == "__main__":
    print("=" * 60)
    print("推荐系统差分隐私 - 测试演示")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 创建模拟用户-物品评分数据
    n_users = 20  # 用户数量
    n_items = 30  # 物品数量
    n_ratings = 150  # 评分数
    
    # 生成随机评分交互
    interactions = []
    for _ in range(n_ratings):
        user_id = np.random.randint(0, n_users)
        item_id = np.random.randint(0, n_items)
        score = np.random.randint(1, 6)  # 1-5分评分
        interactions.append((user_id, item_id, score))
    
    # 构建评分矩阵
    R = build_user_item_matrix(interactions, n_users, n_items)
    
    print(f"\n用户-物品评分矩阵: {R.shape}")
    print(f"总评分数: {n_ratings}")
    print(f"稀疏度: {1 - n_ratings / (n_users * n_items):.2%}")
    
    # 测试1：Pearson相似度（差分隐私版本）
    print("\n" + "-" * 40)
    print("测试1: 差分隐私Pearson相似度")
    print("-" * 40)
    
    user_0_ratings = R[0]
    user_1_ratings = R[1]
    
    # 有噪声的相似度
    noisy_sim = pearson_similarity_with_dp(user_0_ratings, user_1_ratings, epsilon=1.0)
    print(f"用户0与用户1的相似度（带DP噪声）: {noisy_sim:.4f}")
    
    # 不同epsilon值的对比
    for eps in [0.1, 0.5, 1.0, 2.0]:
        sim = pearson_similarity_with_dp(user_0_ratings, user_1_ratings, epsilon=eps)
        print(f"  epsilon={eps}: similarity={sim:.4f}")
    
    # 测试2：协同过滤推荐
    print("\n" + "-" * 40)
    print("测试2: 差分隐私协同过滤")
    print("-" * 40)
    
    target_user = 5
    predictions = collaborative_filtering_dp(R, target_user, k_neighbors=5, epsilon=1.0)
    
    # 显示推荐结果（评分为0的物品）
    unrated_items = np.where(R[target_user] == 0)[0]
    top_recommendations = unrated_items[np.argsort(predictions[unrated_items])[-5:]][::-1]
    
    print(f"用户{target_user}的Top 5推荐物品: {top_recommendations}")
    print(f"推荐物品的预测评分: {predictions[top_recommendations]}")
    
    # 测试3：矩阵分解
    print("\n" + "-" * 40)
    print("测试3: 差分隐私矩阵分解 (DP-MF)")
    print("-" * 40)
    
    U, V = matrix_factorization_sgd(
        R, n_factors=5, learning_rate=0.01, 
        regularization=0.1, n_epochs=20, epsilon=1.0
    )
    
    print(f"用户隐向量矩阵形状: {U.shape}")
    print(f"物品隐向量矩阵形状: {V.shape}")
    
    # 预测评分
    predicted_R = predict_dp_matrix_factorization(U, V)
    print(f"预测评分矩阵形状: {predicted_R.shape}")
    
    # 计算重构误差
    mask = R > 0
    rmse = np.sqrt(np.mean((R[mask] - predicted_R[mask]) ** 2))
    print(f"重构误差 (RMSE): {rmse:.4f}")
    
    # 测试4：基于物品的推荐
    print("\n" + "-" * 40)
    print("测试4: 基于物品的差分隐私推荐")
    print("-" * 40)
    
    target_item = 10
    similar_items = item_based_dp_recommend(R, target_item, k_neighbors=5, epsilon=1.0)
    
    print(f"与物品{target_item}最相似的5个物品:")
    for item_id, sim in similar_items:
        print(f"  物品{item_id}: 相似度={sim:.4f}")
    
    print("\n" + "=" * 60)
    print("所有测试完成")
    print("=" * 60)