# -*- coding: utf-8 -*-

"""

算法实现：在线算法 / online_feature_selection



本文件实现 online_feature_selection 相关的算法功能。

"""



import numpy as np

import random





class OnlineFeatureSelector:

    """

    在线特征选择器基类

    """



    def __init__(self, n_features, budget=None):

        """

        初始化

        

        参数:

            n_features: 特征总数

            budget: 选择特征的数量上限

        """

        self.n_features = n_features

        self.budget = budget or n_features

        self.selected_features = set()

        # 特征统计

        self.feature_scores = {}

        self.feature_counts = {}



    def select(self, X, y=None):

        """

        选择特征（返回特征索引列表）

        

        参数:

            X: 数据

            y: 标签

        返回:

            selected: 选中的特征索引

        """

        raise NotImplementedError



    def partial_fit(self, X, y=None):

        """增量更新"""

        raise NotImplementedError



    def get_selected_features(self):

        """获取已选中的特征"""

        return sorted(self.selected_features)





class StochasticGreedySelector(OnlineFeatureSelector):

    """

    随机贪婪特征选择

    

    每次随机选择一个候选特征，评估其贡献，

    如果贡献大于当前最差的被选中特征，则替换

    """



    def __init__(self, n_features, budget=None, epsilon=0.1):

        """

        初始化

        

        参数:

            n_features: 特征总数

            budget: 选择特征数

            epsilon: 探索概率

        """

        super().__init__(n_features, budget)

        self.epsilon = epsilon

        self.feature_contributions = {}

        self.total_evaluated = 0



    def _evaluate_feature(self, X, y, feature_idx):

        """

        评估单个特征的贡献

        

        参数:

            X: 数据

            y: 标签

            feature_idx: 特征索引

        返回:

            score: 贡献分数

        """

        # 简化：使用与标签的相关性

        if y is None:

            return 0

        

        x = X[:, feature_idx] if X.ndim > 1 else X

        correlation = np.abs(np.corrcoef(x, y)[0, 1])

        return correlation if not np.isnan(correlation) else 0



    def partial_fit(self, X, y=None):

        """

        部分拟合

        

        参数:

            X: 数据 (n_samples, n_features) 或 (n_samples,)

            y: 标签

        """

        self.total_evaluated += 1

        

        X = np.asarray(X)

        if X.ndim == 1:

            X = X.reshape(-1, 1)

        

        n_samples, n_feat = X.shape

        

        # 以 epsilon 概率随机探索

        if random.random() < self.epsilon:

            # 随机选择特征

            candidate = random.randint(0, n_feat - 1)

            score = self._evaluate_feature(X, y, candidate)

            self.feature_scores[candidate] = score

        else:

            # 选择贡献最大的特征

            best_score = -1

            best_feature = 0

            for i in range(n_feat):

                score = self._evaluate_feature(X, y, i)

                if score > best_score:

                    best_score = score

                    best_feature = i

            self.feature_scores[best_feature] = best_score

        

        # 更新已选特征

        self._update_selected()



    def _update_selected(self):

        """更新选中的特征"""

        # 按分数排序

        sorted_features = sorted(

            self.feature_scores.items(),

            key=lambda x: x[1],

            reverse=True

        )

        

        # 取前 budget 个

        self.selected_features = set(

            f for f, s in sorted_features[:self.budget]

        )





class BanditFeatureSelector(OnlineFeatureSelector):

    """

    基于多臂老虎机的特征选择

    

    将每个特征视为一个臂，使用 UCB 策略选择

    """



    def __init__(self, n_features, budget=None, alpha=1.0):

        """

        初始化

        

        参数:

            n_features: 特征总数

            budget: 选择特征数

            alpha: UCB 参数

        """

        super().__init__(n_features, budget)

        self.alpha = alpha

        # 每个特征的奖励估计

        self.rewards = {i: 0.0 for i in range(n_features)}

        # 每个特征被选择的次数

        self.counts = {i: 0 for i in range(n_features)}

        # 总选择次数

        self.total_selections = 0



    def _ucb_score(self, feature_idx):

        """

        计算 UCB 分数

        

        参数:

            feature_idx: 特征索引

        返回:

            score: UCB 分数

        """

        if self.counts[feature_idx] == 0:

            return float('inf')  # 未选择的特征优先

        

        avg_reward = self.rewards[feature_idx] / self.counts[feature_idx]

        exploration_bonus = self.alpha * np.sqrt(

            np.log(self.total_selections) / self.counts[feature_idx]

        )

        return avg_reward + exploration_bonus



    def select(self, X, y=None):

        """

        选择特征

        

        参数:

            X: 数据

            y: 标签

        返回:

            selected: 选中的特征索引

        """

        if y is None:

            return list(range(min(self.budget, self.n_features)))

        

        X = np.asarray(X)

        if X.ndim == 1:

            X = X.reshape(-1, 1)

        

        # 更新奖励

        self.total_selections += 1

        

        # 计算每个特征的 UCB 分数

        ucb_scores = {i: self._ucb_score(i) for i in range(X.shape[1])}

        

        # 选择分数最高的特征

        sorted_features = sorted(ucb_scores.items(), key=lambda x: x[1], reverse=True)

        self.selected_features = set(f for f, _ in sorted_features[:self.budget])

        

        return sorted(self.selected_features)



    def partial_fit(self, X, y=None):

        """

        部分拟合（带奖励更新）

        

        参数:

            X: 数据

            y: 标签

        """

        if y is None:

            return

        

        # 选择特征

        selected = self.select(X, y)

        

        # 评估奖励（简化：与标签的相关性）

        for feature_idx in selected:

            x = X[:, feature_idx] if X.ndim > 1 else X

            correlation = np.abs(np.corrcoef(x, y)[0, 1])

            reward = correlation if not np.isnan(correlation) else 0

            

            # 更新奖励估计

            n = self.counts[feature_idx]

            self.rewards[feature_idx] = (self.rewards[feature_idx] * n + reward) / (n + 1)

            self.counts[feature_idx] += 1





class GradientBasedFeatureSelection(OnlineFeatureSelector):

    """

    基于梯度的在线特征选择

    

    使用随机梯度下降来评估特征重要性

    """



    def __init__(self, n_features, budget=None, learning_rate=0.01):

        """

        初始化

        

        参数:

            n_features: 特征数

            budget: 选择数

            learning_rate: 学习率

        """

        super().__init__(n_features, budget)

        self.learning_rate = learning_rate

        # 特征权重

        self.weights = np.zeros(n_features)

        # 特征重要性（累积梯度）

        self.importance = np.zeros(n_features)



    def partial_fit(self, X, y=None):

        """

        部分拟合

        

        参数:

            X: 数据

            y: 标签

        """

        X = np.asarray(X)

        if X.ndim == 1:

            X = X.reshape(-1, 1)

        

        if y is None:

            return

        

        # 简化的梯度计算

        # 预测误差

        y_pred = X @ self.weights[:X.shape[1]]

        error = y - y_pred

        

        # 梯度

        gradient = -X.T @ error / len(y)

        

        # 更新权重

        self.weights[:X.shape[1]] -= self.learning_rate * gradient

        

        # 更新重要性（梯度的 L1 范数）

        self.importance[:X.shape[1]] += np.abs(gradient)

        

        # 更新选中的特征

        self._update_selected()



    def _update_selected(self):

        """根据重要性更新选中的特征"""

        # 选择重要性最高的特征

        sorted_indices = np.argsort(self.importance)[::-1]

        self.selected_features = set(sorted_indices[:self.budget])



    def get_feature_importance(self):

        """获取特征重要性"""

        return dict(enumerate(self.importance))





class SlidingWindowFeatureSelector(OnlineFeatureSelector):

    """

    滑动窗口特征选择

    

    在滑动窗口内评估特征重要性

    """



    def __init__(self, n_features, budget=None, window_size=1000):

        """

        初始化

        

        参数:

            n_features: 特征数

            budget: 选择数

            window_size: 滑动窗口大小

        """

        super().__init__(n_features, budget)

        self.window_size = window_size

        # 滑动窗口

        self.X_window = []

        self.y_window = []

        # 分数

        self.scores = np.zeros(n_features)



    def partial_fit(self, X, y=None):

        """

        部分拟合

        

        参数:

            X: 数据

            y: 标签

        """

        X = np.asarray(X)

        if X.ndim == 1:

            X = X.reshape(1, -1)

        

        # 添加到窗口

        self.X_window.append(X)

        self.y_window.append(y)

        

        # 保持窗口大小

        while len(self.X_window) > self.window_size:

            self.X_window.pop(0)

            self.y_window.pop(0)

        

        # 重新计算分数

        self._compute_scores()



    def _compute_scores(self):

        """计算特征分数"""

        if not self.X_window:

            return

        

        X = np.vstack(self.X_window)

        y = np.array(self.y_window)

        

        if len(y) < 2:

            return

        

        # 计算每个特征与标签的相关性

        for i in range(X.shape[1]):

            correlation = np.abs(np.corrcoef(X[:, i], y)[0, 1])

            self.scores[i] = correlation if not np.isnan(correlation) else 0

        

        # 更新选中的特征

        sorted_indices = np.argsort(self.scores)[::-1]

        self.selected_features = set(sorted_indices[:self.budget])





if __name__ == "__main__":

    print("=== 在线特征选择测试 ===\n")



    # 生成测试数据

    np.random.seed(42)

    n_samples = 500

    n_features = 20

    

    # 生成数据（只有部分特征有用）

    X = np.random.randn(n_samples, n_features)

    # 只有前 5 个特征与标签相关

    y = X[:, 0] * 2 + X[:, 2] * 1.5 + X[:, 4] * 1 + 0.5 * np.random.randn(n_samples)



    # 随机贪婪选择

    print("--- 随机贪婪选择 ---")

    selector1 = StochasticGreedySelector(n_features, budget=5, epsilon=0.1)

    

    for i in range(0, n_samples, 10):

        selector1.partial_fit(X[i:i+10], y[i:i+10])

    

    print(f"  选中的特征: {selector1.get_selected_features()}")

    print(f"  特征分数: {[(f, f'{selector1.feature_scores.get(f, 0):.3f}') for f in selector1.get_selected_features()]}")



    # 多臂老虎机选择

    print("\n--- 多臂老虎机选择 ---")

    selector2 = BanditFeatureSelector(n_features, budget=5, alpha=1.0)

    

    for i in range(n_samples):

        selector2.partial_fit(X[i:i+1], y[i])

    

    print(f"  选中的特征: {selector2.get_selected_features()}")

    print(f"  奖励估计: {[(f, f'{selector2.rewards[f]:.3f}') for f in selector2.get_selected_features()]}")



    # 基于梯度的选择

    print("\n--- 基于梯度的选择 ---")

    selector3 = GradientBasedFeatureSelection(n_features, budget=5, learning_rate=0.01)

    

    for i in range(0, n_samples, 10):

        selector3.partial_fit(X[i:i+10], y[i:i+10])

    

    print(f"  选中的特征: {selector3.get_selected_features()}")

    importance = selector3.get_feature_importance()

    top_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:5]

    print(f"  最重要的特征: {top_features}")



    # 滑动窗口选择

    print("\n--- 滑动窗口选择 ---")

    selector4 = SlidingWindowFeatureSelector(n_features, budget=5, window_size=100)

    

    for i in range(n_samples):

        selector4.partial_fit(X[i:i+1], y[i])

    

    print(f"  选中的特征: {selector4.get_selected_features()}")



    # 比较结果

    print("\n--- 算法比较 ---")

    true_important = {0, 2, 4}

    

    print(f"  真实重要特征: {sorted(true_important)}")

    print(f"  随机贪婪: {sorted(selector1.get_selected_features())} - "

          f"准确率 {len(selector1.get_selected_features() & true_important)}/{len(true_important)}")

    print(f"  老虎机: {sorted(selector2.get_selected_features())} - "

          f"准确率 {len(selector2.get_selected_features() & true_important)}/{len(true_important)}")

    print(f"  梯度: {sorted(selector3.get_selected_features())} - "

          f"准确率 {len(selector3.get_selected_features() & true_important)}/{len(true_important)}")

    print(f"  滑动窗口: {sorted(selector4.get_selected_features())} - "

          f"准确率 {len(selector4.get_selected_features() & true_important)}/{len(true_important)}")



    # 性能测试

    print("\n--- 性能测试 ---")

    import time

    

    n = 10000

    large_X = np.random.randn(n, 100)

    large_y = large_X[:, :10] @ np.ones(10) + 0.1 * np.random.randn(n)

    

    start = time.time()

    selector = StochasticGreedySelector(100, budget=10)

    for i in range(0, n, 10):

        selector.partial_fit(large_X[i:i+10], large_y[i:i+10])

    elapsed = time.time() - start

    print(f"  随机贪婪 {n} 样本: {elapsed:.2f}s")

    

    start = time.time()

    selector = SlidingWindowFeatureSelector(100, budget=10, window_size=500)

    for i in range(n):

        selector.partial_fit(large_X[i:i+1], large_y[i])

    elapsed = time.time() - start

    print(f"  滑动窗口 {n} 样本: {elapsed:.2f}s")

