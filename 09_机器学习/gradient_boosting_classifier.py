# -*- coding: utf-8 -*-
"""
算法实现：09_机器学习 / gradient_boosting_classifier

本文件实现 gradient_boosting_classifier 相关的算法功能。
"""

gradient_boosting_classifier.py
"""

import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import accuracy_score


class GradientBoostingClassifier:
    """梯度提升分类器"""

    def __init__(self, n_estimators: int = 100, learning_rate: float = 0.1):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.models: list[tuple[DecisionTreeRegressor, float]] = []

    def fit(self, features: np.ndarray, target: np.ndarray) -> None:
        """训练模型"""
        for _ in range(self.n_estimators):
            # 计算伪残差
            residuals = -self.gradient(target, self.predict(features))
            # 用决策树拟合残差
            model = DecisionTreeRegressor(max_depth=1)
            model.fit(features, residuals)
            # 加上学习率更新模型
            self.models.append((model, self.learning_rate))

    def predict(self, features: np.ndarray) -> np.ndarray:
        """预测"""
        predictions = np.zeros(features.shape[0])
        for model, learning_rate in self.models:
            predictions += learning_rate * model.predict(features)
        return np.sign(predictions)

    def gradient(self, target: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """计算梯度"""
        return -target / (1 + np.exp(target * y_pred))


if __name__ == "__main__":
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    clf = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2f}")
