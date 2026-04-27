# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / smote_oversampling



本文件实现 smote_oversampling 相关的算法功能。

"""



import numpy as np





class SMOTE:

    """

    SMOTE过采样



    参数:

        k_neighbors: 近邻数量

        sampling_strategy: 重采样策略

        random_state: 随机种子

    """



    def __init__(self, k_neighbors=5, sampling_strategy='auto', random_state=42):

        self.k_neighbors = k_neighbors

        self.sampling_strategy = sampling_strategy

        self.random_state = random_state

        self.synthetic_samples = None



    def _knn(self, X, k):

        """

        计算每个样本的k个最近邻



        返回:

            neighbors: (n_samples, k) 最近邻索引

        """

        n_samples = X.shape[0]

        neighbors = np.zeros((n_samples, k), dtype=int)



        for i in range(n_samples):

            # 计算到其他样本的距离

            distances = np.linalg.norm(X - X[i], axis=1)

            distances[i] = np.inf  # 排除自身



            # 取k个最近邻

            nearest_indices = np.argsort(distances)[:k]

            neighbors[i] = nearest_indices



        return neighbors



    def _synthetic_sample(self, sample, neighbor):

        """在样本和邻居之间插值生成新样本"""

        alpha = np.random.random()

        synthetic = sample + alpha * (neighbor - sample)

        return synthetic



    def fit_resample(self, X, y):

        """

        过采样



        参数:

            X: 特征数据 (n_samples, n_features)

            y: 标签 (n_samples,)



        返回:

            X_resampled: 过采样后的特征

            y_resampled: 过采样后的标签

        """

        np.random.seed(self.random_state)



        classes, counts = np.unique(y, return_counts=True)

        n_classes = len(classes)



        # 找出多数类和少数类

        max_count = max(counts)

        min_count = min(counts)



        # 确定少数类

        minority_classes = classes[counts < max_count]



        # 计算需要生成的数量

        n_to_generate = max_count - min_count



        # 对每个少数类进行过采样

        synthetic_X = []

        synthetic_y = []



        for cls in minority_classes:

            # 获取少数类样本

            cls_mask = y == cls

            X_minority = X[cls_mask]



            # 找到k个最近邻

            neighbors = self._knn(X_minority, min(self.k_neighbors, len(X_minority) - 1))



            # 生成合成样本

            n_generated = 0

            attempts = 0

            max_attempts = n_to_generate * 10



            while n_generated < n_to_generate and attempts < max_attempts:

                # 随机选择一个样本

                idx = np.random.randint(0, len(X_minority))

                # 随机选择一个邻居

                neighbor_idx = np.random.choice(neighbors[idx])

                # 生成合成样本

                synthetic = self._synthetic_sample(X_minority[idx], X_minority[neighbor_idx])

                synthetic_X.append(synthetic)

                synthetic_y.append(cls)

                n_generated += 1

                attempts += 1



            print(f"   类别 {cls}: 生成 {n_generated} 个合成样本")



        # 合并原始数据和合成数据

        X_resampled = np.vstack([X] + synthetic_X)

        y_resampled = np.concatenate([y] + synthetic_y)



        self.synthetic_samples = np.array(synthetic_X)



        return X_resampled, y_resampled





class BorderlineSMOTE:

    """

    Borderline-SMOTE



    只对边界附近的少数类样本进行过采样

    """



    def __init__(self, k_neighbors=5, random_state=42):

        self.k_neighbors = k_neighbors

        self.random_state = random_state



    def fit_resample(self, X, y):

        """边界SMOTE过采样"""

        np.random.seed(self.random_state)



        classes, counts = np.unique(y, return_counts=True)

        majority_class = classes[np.argmax(counts)]

        minority_class = classes[np.argmin(counts)]



        # 获取少数类和多数类样本

        X_minority = X[y == minority_class]

        X_majority = X[y == majority_class]



        # 对每个少数类样本，统计有多少多数类邻居

        k = min(self.k_neighbors, len(X_majority) - 1)



        # 计算每个少数类样本的多数类邻居数

        danger_mask = []

        for x in X_minority:

            # 到多数类样本的距离

            distances = np.linalg.norm(X_majority - x, axis=1)

            k_nearest = np.argsort(distances)[:k]

            n_majority_neighbors = np.sum(y[y == majority_class][k_nearest] == majority_class)



            # 危险样本：在边界附近（多数类邻居数在k/2到k之间）

            is_danger = n_majority_neighbors >= k / 2 and n_majority_neighbors < k

            danger_mask.append(is_danger)



        danger_mask = np.array(danger_mask)

        print(f"   Borderline-SMOTE: 找到 {np.sum(danger_mask)} 个边界样本")



        # 只对边界样本进行SMOTE

        X_danger = X_minority[danger_mask]



        if len(X_danger) > 0:

            # 找到这些样本的邻居

            neighbors = []

            for x in X_danger:

                distances = np.linalg.norm(X_minority - x, axis=1)

                knn_idx = np.argsort(distances)[1:k+1]

                neighbors.append(knn_idx)



            # 生成合成样本

            synthetic_X = []

            for i, x in enumerate(X_danger):

                # 随机选择一个少数类邻居

                nn_idx = np.random.choice(neighbors[i])

                alpha = np.random.random()

                synthetic = x + alpha * (X_minority[nn_idx] - x)

                synthetic_X.append(synthetic)



            # 合并

            X_resampled = np.vstack([X] + synthetic_X)

            y_resampled = np.concatenate([y] + [minority_class] * len(synthetic_X))

        else:

            X_resampled = X

            y_resampled = y



        return X_resampled, y_resampled





def test_smote():

    """测试SMOTE"""

    np.random.seed(42)



    print("=" * 60)

    print("SMOTE过采样测试")

    print("=" * 60)



    # 创建不平衡数据

    n_samples = 200

    n_features = 2



    # 类别0: 150个样本

    X0 = np.random.randn(150, 2) * 0.5

    X0[:, 0] += 2  # 中心偏移



    # 类别1: 50个样本（少数类）

    X1 = np.random.randn(50, 2) * 0.3

    X1[:, 0] -= 2



    # 合并

    X = np.vstack([X0, X1])

    y = np.array([0] * 150 + [1] * 50)



    print(f"\n1. 原始数据:")

    print(f"   类别0: {np.sum(y==0)}")

    print(f"   类别1: {np.sum(y==1)}")

    print(f"   不平衡比例: {np.sum(y==0)/np.sum(y==1):.1f}:1")



    # SMOTE过采样

    print("\n2. SMOTE过采样:")

    smote = SMOTE(k_neighbors=5)

    X_resampled, y_resampled = smote.fit_resample(X, y)



    print(f"\n3. 过采样后数据:")

    print(f"   类别0: {np.sum(y_resampled==0)}")

    print(f"   类别1: {np.sum(y_resampled==1)}")



    # Borderline-SMOTE

    print("\n4. Borderline-SMOTE:")

    bsmote = BorderlineSMOTE(k_neighbors=5)

    X_bsmote, y_bsmote = bsmote.fit_resample(X, y)



    print(f"   类别0: {np.sum(y_bsmote==0)}")

    print(f"   类别1: {np.sum(y_bsmote==1)}")



    # 验证合成样本位置

    print("\n5. 合成样本验证:")

    if smote.synthetic_samples is not None:

        print(f"   合成样本数: {len(smote.synthetic_samples)}")

        print(f"   合成样本特征维度: {smote.synthetic_samples.shape[1]}")



        # 检查合成样本是否在少数类区域内

        mean_minority = np.mean(X[y==1], axis=0)

        mean_synthetic = np.mean(smote.synthetic_samples, axis=0)

        print(f"   少数类中心: {mean_minority}")

        print(f"   合成样本中心: {mean_synthetic}")



    print("\n6. SMOTE原理:")

    print("   ┌─────────────────────────────────────────────┐")

    print("   │ 对少数类样本:                               │")

    print("   │ 1. 找到k个最近邻                           │")

    print("   │ 2. 随机选一个邻居                          │")

    print("   │ 3. 插值: x_new = x + α*(x_nn - x)           │")

    print("   │                                            │")

    print("   │ Borderline-SMOTE:                          │")

    print("   │ 只对边界样本进行过采样                     │")

    print("   └─────────────────────────────────────────────┘")





if __name__ == "__main__":

    test_smote()

