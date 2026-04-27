# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / model_calibration



本文件实现 model_calibration 相关的算法功能。

"""



import numpy as np





class TemperatureScaling:

    """

    温度缩放



    通过单一参数T调整softmax输出的置信度



    参数:

        temperature: 温度参数T

    """



    def __init__(self, temperature=1.0):

        self.temperature = temperature

        self.fitted = False



    def _softmax(self, logits):

        """计算softmax"""

        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))

        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)



    def fit(self, logits, y_true):

        """

        拟合温度参数



        参数:

            logits: 模型原始输出（未归一化）

            y_true: 真实标签



        返回:

            最优温度T

        """

        # 简化的优化过程

        best_temp = 1.0

        best_nll = float('inf')



        # 网格搜索

        for temp in np.linspace(0.5, 3.0, 50):

            scaled_logits = logits / temp

            probs = self._softmax(scaled_logits)



            # 计算负对数似然

            eps = 1e-10

            nll = -np.mean(np.log(probs[np.arange(len(y_true)), y_true] + eps))



            if nll < best_nll:

                best_nll = nll

                best_temp = temp



        self.temperature = best_temp

        self.fitted = True

        print(f"   最优温度: {best_temp:.4f}")



        return best_temp



    def predict_proba(self, logits):

        """预测概率（带温度缩放）"""

        scaled_logits = logits / self.temperature

        return self._softmax(scaled_logits)



    def predict(self, logits):

        """预测类别"""

        probs = self.predict_proba(logits)

        return np.argmax(probs, axis=1)





class ModelCalibration:

    """

    模型校准工具



    提供ECE计算和多种校准方法

    """



    @staticmethod

    def compute_ece(probs, y_true, n_bins=10):

        """

        计算Expected Calibration Error



        ECE = Σ (|B_m|/n) * |acc(B_m) - conf(B_m)|



        参数:

            probs: 预测概率 (n_samples, n_classes)

            y_true: 真实标签

            n_bins: 分箱数量

        """

        n_samples = len(y_true)

        confidences = np.max(probs, axis=1)

        predictions = np.argmax(probs, axis=1)

        accuracies = (predictions == y_true).astype(float)



        # 分箱

        bin_boundaries = np.linspace(0, 1, n_bins + 1)



        ece = 0.0

        bin_stats = []



        for i in range(n_bins):

            # 找到在当前置信度区间的样本

            bin_mask = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i+1])

            bin_count = np.sum(bin_mask)



            if bin_count > 0:

                # 区间平均置信度和准确率

                avg_confidence = np.mean(confidences[bin_mask])

                avg_accuracy = np.mean(accuracies[bin_mask])



                # 区间权重

                weight = bin_count / n_samples



                # 贡献

                ece += weight * abs(avg_accuracy - avg_confidence)



                bin_stats.append({

                    'bin': i,

                    'range': (bin_boundaries[i], bin_boundaries[i+1]),

                    'count': bin_count,

                    'avg_conf': avg_confidence,

                    'avg_acc': avg_accuracy,

                    'calibration_error': abs(avg_accuracy - avg_confidence)

                })

            else:

                bin_stats.append({

                    'bin': i,

                    'range': (bin_boundaries[i], bin_boundaries[i+1]),

                    'count': 0,

                    'avg_conf': None,

                    'avg_acc': None,

                    'calibration_error': None

                })



        return ece, bin_stats



    @staticmethod

    def reliability_diagram(probs, y_true, n_bins=10):

        """

        生成可靠性图数据



        返回:

            各区间的准确率和置信度

        """

        ece, bin_stats = ModelCalibration.compute_ece(probs, y_true, n_bins)

        return bin_stats, ece





def test_model_calibration():

    """测试模型校准"""

    np.random.seed(42)



    print("=" * 60)

    print("模型校准测试")

    print("=" * 60)



    # 模拟模型输出（过置信或不自信）

    n_samples = 1000

    n_classes = 3



    # 生成logits（模拟未校准的模型输出）

    logits = np.random.randn(n_samples, n_classes)



    # 添加一些信号

    y_true = np.zeros(n_samples, dtype=int)

    for i in range(n_samples):

        y_true[i] = i % n_classes

        logits[i, y_true[i]] += 2.0  # 增加正确类别的logit



    # Softmax

    def softmax(X):

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    probs_before = softmax(logits)



    print("\n1. 原始模型（未校准）:")

    ece_before, _ = ModelCalibration.compute_ece(probs_before, y_true)

    print(f"   ECE: {ece_before:.4f}")



    # 统计平均置信度和准确率

    avg_conf_before = np.mean(np.max(probs_before, axis=1))

    acc_before = np.mean(np.argmax(probs_before, axis=1) == y_true)

    print(f"   平均置信度: {avg_conf_before:.4f}")

    print(f"   准确率: {acc_before:.4f}")

    print(f"   差距: {abs(avg_conf_before - acc_before):.4f}")



    # 温度缩放

    print("\n2. 温度缩放校准:")

    temp_scaling = TemperatureScaling()

    optimal_temp = temp_scaling.fit(logits, y_true)



    probs_after = temp_scaling.predict_proba(logits)



    ece_after, _ = ModelCalibration.compute_ece(probs_after, y_true)

    print(f"   ECE: {ece_after:.4f}")



    avg_conf_after = np.mean(np.max(probs_after, axis=1))

    acc_after = np.mean(np.argmax(probs_after, axis=1) == y_true)

    print(f"   平均置信度: {avg_conf_after:.4f}")

    print(f"   准确率: {acc_after:.4f}")

    print(f"   差距: {abs(avg_conf_after - acc_after):.4f}")



    # 可靠性图数据

    print("\n3. 可靠性图数据:")

    bin_stats, ece = ModelCalibration.reliability_diagram(probs_before, y_true, n_bins=10)

    print("   区间   样本数  置信度  准确率  校准误差")

    print("   " + "-" * 50)

    for stat in bin_stats:

        if stat['count'] > 0:

            print(f"   [{stat['range'][0]:.1f}-{stat['range'][1]:.1f}]  "

                  f"{stat['count']:4d}   "

                  f"{stat['avg_conf']:.3f}   "

                  f"{stat['avg_acc']:.3f}   "

                  f"{stat['calibration_error']:.3f}")



    print("\n4. 校准方法对比:")

    print("   ┌─────────────────────────────────────────────┐")

    print("   │ Temperature Scaling:                       │")

    print("   │   - 单一参数T，简单有效                     │")

    print("   │   - 保持排序，适合深度学习                  │")

    print("   │                                            │")

    print("   │ Platt Scaling:                             │")

    print("   │   - 两个参数（slope, intercept）            │")

    print("   │   - 对logits做线性变换                     │")

    print("   │                                            │")

    print("   │ Isotonic Regression:                       │")

    print("   │   - 非参数方法                             │")

    print("   │   - 分段单调变换                           │")

    print("   └─────────────────────────────────────────────┘")





if __name__ == "__main__":

    test_model_calibration()

