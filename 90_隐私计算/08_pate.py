# -*- coding: utf-8 -*-

"""

算法实现：隐私计算 / 08_pate



本文件实现 08_pate 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional

from dataclasses import dataclass





@dataclass

class TeacherConfig:

    """教师模型配置"""

    teacher_id: int

    data_indices: List[int]  # 教师训练数据的索引

    model_type: str = "linear"  # 模型类型





class PATETeacher:

    """

    PATE教师模型



    每个教师在独立的数据子集上训练

    """



    def __init__(self, config: TeacherConfig):

        """

        初始化教师模型



        Args:

            config: 教师配置

        """

        self.config = config

        self.teacher_id = config.teacher_id

        self.model_params = None

        self.is_trained = False



    def train(

        self,

        data: np.ndarray,

        labels: np.ndarray

    ):

        """

        训练教师模型



        Args:

            data: 训练数据

            labels: 训练标签

        """

        # 获取本教师的数据子集

        train_data = data[self.config.data_indices]

        train_labels = labels[self.config.data_indices]



        # 训练简单线性模型

        n_samples, n_features = train_data.shape

        self.model_params = np.random.randn(n_features) * 0.01

        lr = 0.1



        for _ in range(100):

            predictions = train_data @ self.model_params

            errors = predictions - train_labels

            gradients = (1.0 / n_samples) * (train_data.T @ errors)

            self.model_params = self.model_params - lr * gradients



        self.is_trained = True



    def predict(self, data: np.ndarray) -> np.ndarray:

        """

        预测



        Args:

            data: 输入数据



        Returns:

            预测值

        """

        if not self.is_trained:

            raise ValueError("教师模型尚未训练")



        return data @ self.model_params



    def predict_soft(self, data: np.ndarray) -> np.ndarray:

        """

        软预测(用于PATE)



        返回未归一化的logit分数



        Args:

            data: 输入数据



        Returns:

            logit分数

        """

        return self.predict(data)





class PATEAggregator:

    """

    PATE聚合器



    使用差分隐私聚合教师预测

    """



    def __init__(self, num_teachers: int, epsilon: float):

        """

        初始化聚合器



        Args:

            num_teachers: 教师数量

            epsilon: 差分隐私预算

        """

        self.num_teachers = num_teachers

        self.epsilon = epsilon

        self.noise_scale = 1.0 / epsilon



    def aggregate(

        self,

        teacher_predictions: np.ndarray,

        labels: np.ndarray = None

    ) -> Tuple[np.ndarray, float]:

        """

        聚合教师预测



        Args:

            teacher_predictions: 各教师的预测,shape为(n_teachers, n_samples)

            labels: 真实标签(用于评估,可选)



        Returns:

            (聚合后的预测, 隐私消耗)

        """

        n_teachers, n_samples = teacher_predictions.shape



        # 1. 对每个样本,统计各类的投票数

        # 使用投票机制而非简单平均(更隐私)

        aggregated_logits = np.zeros(n_samples)



        for t in range(n_teachers):

            aggregated_logits += teacher_predictions[t]



        # 2. 添加拉普拉斯噪声实现差分隐私

        # 每个教师的贡献敏感度为1

        noise = np.random.laplace(0, self.noise_scale, n_samples)

        noisy_aggregated = aggregated_logits + noise



        # 3. 转换为预测

        predictions = np.sign(noisy_aggregated)



        # 评估(如果有标签)

        accuracy = 0.0

        if labels is not None:

            accuracy = np.mean(predictions == labels)



        return predictions, accuracy



    def aggregate_confident(

        self,

        teacher_predictions: np.ndarray,

        threshold: float = 0.8

    ) -> Tuple[np.ndarray, List[int], float]:

        """

        置信聚合 - 只在教师共识高时标注



        关键优化: 只有当超过threshold比例的教师意见一致时,

        才使用该标签;否则放弃该样本



        Args:

            teacher_predictions: 教师预测

            threshold: 共识阈值



        Returns:

            (伪标签, 未标注样本索引, 隐私消耗)

        """

        n_teachers, n_samples = teacher_predictions.shape



        # 统计每个样本的多数投票

        votes = np.sign(teacher_predictions)  # 简化为二分类

        vote_sum = np.sum(votes, axis=0)  # 正票-负票



        # 计算共识比例

        consensus_ratio = np.abs(vote_sum) / n_teachers



        # 置信样本

        confident_mask = consensus_ratio >= threshold

        confident_indices = np.where(confident_mask)[0]



        # 伪标签

        pseudo_labels = np.sign(vote_sum)

        pseudo_labels[~confident_mask] = 0  # 未置信的设为0



        # 计算隐私消耗(每个样本一次查询)

        privacy_spent = len(confident_indices) * self.epsilon



        return pseudo_labels, confident_indices.tolist(), privacy_spent



    def aggregate_gnmax(

        self,

        teacher_predictions: np.ndarray,

        num_classes: int = 2

    ) -> Tuple[np.ndarray, float]:

        """

        GNMax聚合 - 用于多分类



        步骤:

        1. 统计每个类别的投票数

        2. 添加噪声到投票计数

        3. 选择噪声后得票最多的类别



        Args:

            teacher_predictions: 教师预测(类别索引)

            num_classes: 类别数



        Returns:

            (聚合后的类别预测, 隐私消耗)

        """

        n_teachers, n_samples = teacher_predictions.shape



        # 统计每个样本的各类得票

        vote_counts = np.zeros((n_samples, num_classes))



        for t in range(n_teachers):

            for s in range(n_samples):

                pred_class = int(teacher_predictions[t, s])

                vote_counts[s, pred_class] += 1



        # 添加拉普拉斯噪声

        noise = np.random.laplace(0, self.noise_scale, vote_counts.shape)

        noisy_counts = vote_counts + noise



        # 选择噪声后得票最多的类

        predictions = np.argmax(noisy_counts, axis=1)



        return predictions, self.epsilon





class PATEStudent:

    """

    PATE学生模型



    使用教师生成的伪标签训练

    """



    def __init__(

        self,

        n_features: int,

        aggregator: PATEAggregator

    ):

        """

        初始化学生模型



        Args:

            n_features: 特征维度

            aggregator: PATE聚合器

        """

        self.n_features = n_features

        self.aggregator = aggregator

        self.model_params = None



    def train(

        self,

        data: np.ndarray,

        pseudo_labels: np.ndarray,

        confident_mask: np.ndarray = None

    ):

        """

        训练学生模型



        Args:

            data: 训练数据

            pseudo_labels: 伪标签

            confident_mask: 置信样本掩码(可选)

        """

        # 过滤置信样本

        if confident_mask is not None:

            data = data[confident_mask]

            pseudo_labels = pseudo_labels[confident_mask]



        # 移除未标注的样本

        valid_mask = pseudo_labels != 0

        data = data[valid_mask]

        labels = pseudo_labels[valid_mask]



        # 训练线性模型

        n_samples, n_features = data.shape

        self.model_params = np.random.randn(n_features) * 0.01

        lr = 0.1



        for _ in range(100):

            predictions = data @ self.model_params

            errors = predictions - labels

            gradients = (1.0 / n_samples) * (data.T @ errors)

            self.model_params = self.model_params - lr * gradients



    def predict(self, data: np.ndarray) -> np.ndarray:

        """

        预测



        Args:

            data: 输入数据



        Returns:

            预测值

        """

        if self.model_params is None:

            raise ValueError("学生模型尚未训练")



        return data @ self.model_params





class PATEFramework:

    """

    完整PATE框架



    整合教师、学生和聚合器

    """



    def __init__(

        self,

        num_teachers: int,

        epsilon: float,

        n_features: int

    ):

        """

        初始化PATE框架



        Args:

            num_teachers: 教师数量

            epsilon: 差分隐私预算

            n_features: 特征维度

        """

        self.num_teachers = num_teachers

        self.epsilon = epsilon

        self.n_features = n_features



        self.aggregator = PATEAggregator(num_teachers, epsilon)

        self.teachers: List[PATETeacher] = []

        self.student: Optional[PATEStudent] = None



        self.privacy_spent = 0.0



    def setup_teachers(

        self,

        data: np.ndarray,

        labels: np.ndarray,

        data_indices: List[List[int]]

    ):

        """

        设置教师模型



        Args:

            data: 全部数据

            labels: 全部标签

            data_indices: 每个教师的数据索引列表

        """

        self.teachers = []



        for i, indices in enumerate(data_indices):

            config = TeacherConfig(

                teacher_id=i,

                data_indices=indices

            )

            teacher = PATETeacher(config)

            teacher.train(data, labels)

            self.teachers.append(teacher)



    def get_teacher_predictions(self, data: np.ndarray) -> np.ndarray:

        """

        获取所有教师的预测



        Args:

            data: 输入数据



        Returns:

            教师预测矩阵

        """

        predictions = []



        for teacher in self.teachers:

            pred = teacher.predict(data)

            predictions.append(pred)



        return np.array(predictions)



    def generate_pseudo_labels(

        self,

        unlabeled_data: np.ndarray,

        use_confident: bool = True,

        threshold: float = 0.8

    ) -> Tuple[np.ndarray, List[int], float]:

        """

        生成伪标签



        Args:

            unlabeled_data: 无标签数据

            use_confident: 是否使用置信聚合

            threshold: 共识阈值



        Returns:

            (伪标签, 置信样本索引, 隐私消耗)

        """

        teacher_preds = self.get_teacher_predictions(unlabeled_data)



        if use_confident:

            pseudo_labels, confident_indices, privacy_spent = \

                self.aggregator.aggregate_confident(teacher_preds, threshold)

        else:

            predictions, accuracy = self.aggregator.aggregate(teacher_preds)

            pseudo_labels = predictions

            confident_indices = list(range(len(predictions)))

            privacy_spent = self.epsilon



        self.privacy_spent += privacy_spent



        return pseudo_labels, confident_indices, privacy_spent



    def train_student(

        self,

        student_data: np.ndarray,

        pseudo_labels: np.ndarray,

        confident_indices: List[int]

    ):

        """

        训练学生模型



        Args:

            student_data: 学生训练数据

            pseudo_labels: 伪标签

            confident_indices: 置信样本索引

        """

        self.student = PATEStudent(self.n_features, self.aggregator)

        self.student.train(

            student_data,

            pseudo_labels,

            np.array(confident_indices)

        )



    def get_total_privacy_spent(self) -> Tuple[float, float]:

        """

        获取总隐私消耗



        Returns:

            (epsilon, delta) 元组

        """

        return (self.privacy_spent, 1e-5)  # 简化delta





def demonstrate_pate():

    """

    演示PATE框架

    """



    print("PATE (Private Aggregation of Teacher Ensembles) 演示")

    print("=" * 60)



    np.random.seed(42)



    # 1. 准备数据

    print("\n1. 数据准备")

    n_samples = 1000

    n_features = 10

    n_teachers = 10



    # 生成数据

    X = np.random.randn(n_samples, n_features)

    true_w = np.random.randn(n_features) * 0.5

    y = np.sign(X @ true_w + np.random.randn(n_samples) * 0.5)



    # 分成有标签和无标签

    labeled_ratio = 0.1

    n_labeled = int(n_samples * labeled_ratio)



    labeled_indices = np.random.choice(n_samples, n_labeled, replace=False)

    unlabeled_indices = np.array([i for i in range(n_samples) if i not in labeled_indices])



    print(f"   总样本数: {n_samples}")

    print(f"   有标签样本: {n_labeled}")

    print(f"   无标签样本: {len(unlabeled_indices)}")



    # 2. 设置教师

    print("\n2. 设置教师模型")



    # 将有标签数据分成k份

    np.random.shuffle(labeled_indices)

    chunk_size = len(labeled_indices) // n_teachers

    teacher_indices = []



    for i in range(n_teachers):

        start = i * chunk_size

        end = (i + 1) * chunk_size if i < n_teachers - 1 else len(labeled_indices)

        indices = labeled_indices[start:end]

        teacher_indices.append(indices)

        print(f"   教师{i}: {len(indices)}个样本")



    # 3. 创建PATE框架

    print("\n3. PATE训练")

    pate = PATEFramework(

        num_teachers=n_teachers,

        epsilon=1.0,

        n_features=n_features

    )



    # 设置教师

    pate.setup_teachers(X, y, teacher_indices)



    # 生成伪标签

    unlabeled_data = X[unlabeled_indices]

    pseudo_labels, confident_indices, privacy_spent = pate.generate_pseudo_labels(

        unlabeled_data,

        use_confident=True,

        threshold=0.8

    )



    print(f"   生成伪标签: {len(pseudo_labels)}")

    print(f"   置信样本: {len(confident_indices)}")

    print(f"   本轮隐私消耗: ε={privacy_spent:.4f}")



    # 4. 训练学生

    print("\n4. 训练学生模型")

    pate.train_student(unlabeled_data, pseudo_labels, confident_indices)



    student = pate.student



    # 评估学生

    student_pred = student.predict(X)

    student_acc = np.mean(np.sign(student_pred) == y)

    print(f"   学生模型准确率: {student_acc:.4f}")



    # 5. 总隐私消耗

    print("\n5. 隐私消耗汇总")

    total_eps, total_delta = pate.get_total_privacy_spent()

    print(f"   总ε消耗: {total_eps:.4f}")

    print(f"   总δ: {total_delta:.2e}")





if __name__ == "__main__":

    demonstrate_pate()



    print("\n" + "=" * 60)

    print("PATE演示完成!")

    print("=" * 60)

