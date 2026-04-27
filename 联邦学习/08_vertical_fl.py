# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 08_vertical_fl



本文件实现 08_vertical_fl 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict, Optional

from dataclasses import dataclass





@dataclass

class PartyConfig:

    """

    参与方配置数据类



    Attributes:

        party_id: 参与方唯一标识符

        n_features: 本地特征维度

        sample_ids: 本地样本ID列表

        has_label: 是否拥有标签数据

    """

    party_id: int

    n_features: int

    sample_ids: List[int]

    has_label: bool = False





class VerticalParty:

    """

    纵向联邦参与方



    每个参与方持有部分特征,可能拥有或不具备标签

    """



    def __init__(self, config: PartyConfig):

        """

        初始化参与方



        Args:

            config: 参与方配置

        """

        self.config = config

        self.party_id = config.party_id

        self.local_features = None  # 本地特征数据

        self.local_labels = None    # 本地标签(如果有)

        self.model_params = None    # 本地模型参数



    def set_data(

        self,

        features: np.ndarray,

        labels: np.ndarray = None

    ):

        """

        设置本地数据



        Args:

            features: 本地特征矩阵,shape为(n_samples, n_local_features)

            labels: 本地标签向量(可选)

        """

        self.local_features = features

        if labels is not None:

            self.local_labels = labels



    def initialize_params(self, seed: int = 42):

        """

        初始化本地模型参数



        Args:

            seed: 随机种子

        """

        np.random.seed(seed + self.config.party_id)

        dim = self.config.n_features

        self.model_params = np.random.randn(dim) * np.sqrt(2.0 / dim)



    def compute_local_gradient(

        self,

        predictions: np.ndarray,

        global_labels: np.ndarray,

        weight: float = 1.0

    ) -> np.ndarray:

        """

        计算本地特征的梯度



        对于纵向联邦,梯度需要根据各方特征分别计算。

        这里模拟: 梯度 = X.T @ (predictions - labels) / n



        Args:

            predictions: 全局预测值

            global_labels: 真实标签

            weight: 样本权重



        Returns:

            本地特征的梯度向量

        """

        n_samples = len(global_labels)

        errors = predictions - global_labels



        # 本地特征对预测的贡献

        local_gradients = (weight / n_samples) * (self.local_features.T @ errors)



        return local_gradients



    def update_params(self, gradients: np.ndarray, learning_rate: float):

        """

        更新本地模型参数



        Args:

            gradients: 接收到的梯度

            learning_rate: 学习率

        """

        self.model_params = self.model_params - learning_rate * gradients



    def get_params(self) -> np.ndarray:

        """

        获取本地模型参数



        Returns:

            本地参数向量

        """

        return self.model_params





class VerticalFederatedServer:

    """

    纵向联邦学习服务器



    负责任务协调、样本对齐和聚合

    """



    def __init__(self, total_feature_dim: int):

        """

        初始化服务器



        Args:

            total_feature_dim: 总特征维度(所有参与方特征维度之和)

        """

        self.total_feature_dim = total_feature_dim

        self.global_model = None

        self.aligned_sample_ids = None



    def initialize_model(self, seed: int = 42):

        """

        初始化全局模型



        Args:

            seed: 随机种子

        """

        np.random.seed(seed)

        self.global_model = np.random.randn(self.total_feature_dim) * np.sqrt(

            2.0 / self.total_feature_dim

        )



    def align_samples(

        self,

        party_configs: List[PartyConfig]

    ) -> List[int]:

        """

        样本对齐 - 找到所有参与方共有的样本



        在实际中需要使用私有集合交集(PSI)协议,

        这里简化模拟:各参与方样本ID空间有重叠。



        Args:

            party_configs: 各参与方配置



        Returns:

            对齐后的样本ID列表

        """

        # 简化:假设第一个参与方的样本为基准

        base_ids = set(party_configs[0].sample_ids)



        for config in party_configs[1:]:

            base_ids = base_ids.intersection(set(config.sample_ids))



        aligned = sorted(list(base_ids))

        self.aligned_sample_ids = aligned



        return aligned



    def broadcast_model(

        self,

        parties: List[VerticalParty],

        party_feature_ranges: List[Tuple[int, int]]

    ):

        """

        向各参与方广播对应的全局模型参数



        纵向联邦中,每个参与方只接收自己特征对应的那部分模型参数



        Args:

            parties: 参与方列表

            party_feature_ranges: 每个参与方的特征范围 [(start, end), ...]

        """

        for party, (start, end) in zip(parties, party_feature_ranges):

            party.model_params = self.global_model[start:end].copy()



    def aggregate_gradients(

        self,

        party_gradients: List[np.ndarray],

        party_feature_ranges: List[Tuple[int, int]]

    ) -> np.ndarray:

        """

        聚合各参与方传来的梯度



        将各参与方的梯度合并为完整的梯度向量



        Args:

            party_gradients: 各参与方的梯度列表

            party_feature_ranges: 特征范围



        Returns:

            完整梯度向量

        """

        full_gradients = np.zeros(self.total_feature_dim)



        for gradients, (start, end) in zip(party_gradients, party_feature_ranges):

            full_gradients[start:end] = gradients



        return full_gradients



    def update_model(self, gradients: np.ndarray, learning_rate: float):

        """

        更新全局模型



        Args:

            gradients: 聚合后的梯度

            learning_rate: 学习率

        """

        self.global_model = self.global_model - learning_rate * gradients



    def evaluate(

        self,

        parties: List[VerticalParty],

        party_feature_ranges: List[Tuple[int, int]],

        test_labels: np.ndarray

    ) -> Dict[str, float]:

        """

        评估全局模型



        Args:

            parties: 参与方列表

            party_feature_ranges: 特征范围

            test_labels: 测试标签



        Returns:

            评估指标

        """

        # 收集各方特征并拼接

        aligned_idx = self.aligned_sample_ids



        # 简化:直接用各方当前数据计算预测

        predictions_list = []

        for party, (start, end) in zip(parties, party_feature_ranges):

            # 取对齐后的样本

            local_pred = party.local_features @ party.model_params

            predictions_list.append(local_pred)



        # 预测为各方预测之和

        predictions = sum(predictions_list)

        mse = np.mean((predictions - test_labels) ** 2)



        return {"mse": mse, "rmse": np.sqrt(mse)}





class VerticalFederatedLearning:

    """

    纵向联邦学习主框架



    整合各参与方和服务器,提供完整的纵向联邦训练流程

    """



    def __init__(

        self,

        parties: List[VerticalParty],

        server: VerticalFederatedServer,

        party_feature_ranges: List[Tuple[int, int]]

    ):

        """

        初始化纵向联邦学习框架



        Args:

            parties: 参与方列表

            server: 服务器

            party_feature_ranges: 各方特征范围

        """

        self.parties = parties

        self.server = server

        self.party_feature_ranges = party_feature_ranges

        self.n_parties = len(parties)



    def train(

        self,

        n_rounds: int,

        learning_rate: float,

        test_labels: np.ndarray = None,

        verbose: bool = True

    ) -> Dict:

        """

        执行纵向联邦学习训练



        每轮流程:

        1. 服务器广播模型片段给各参与方

        2. 各参与方计算本地梯度

        3. 各参与方发送梯度到服务器

        4. 服务器聚合梯度并更新全局模型



        Args:

            n_rounds: 训练轮数

            learning_rate: 学习率

            test_labels: 测试标签(可选)

            verbose: 是否打印进度



        Returns:

            训练历史

        """

        history = {

            "rounds": [],

            "test_mse": [] if test_labels is not None else None

        }



        for round_idx in range(n_rounds):

            # 1. 服务器广播模型

            self.server.broadcast_model(self.parties, self.party_feature_ranges)



            # 2. 各参与方计算本地梯度

            # 注意:实际需要安全计算,这里简化模拟

            party_gradients = []



            for party in self.parties:

                # 获取全局预测(这里简化用各方本地预测模拟)

                predictions = party.local_features @ party.model_params

                # 计算梯度

                gradients = party.compute_local_gradient(

                    predictions, party.local_labels

                )

                party_gradients.append(gradients)



            # 3. 聚合梯度

            full_gradients = self.server.aggregate_gradients(

                party_gradients, self.party_feature_ranges

            )



            # 4. 更新全局模型

            self.server.update_model(full_gradients, learning_rate)



            # 5. 更新各方本地模型

            for party, gradients in zip(self.parties, party_gradients):

                party.update_params(gradients, learning_rate)



            # 评估

            if test_labels is not None:

                metrics = self.server.evaluate(

                    self.parties, self.party_feature_ranges, test_labels

                )

                history["test_mse"].append(metrics["mse"])



            history["rounds"].append(round_idx + 1)



            if verbose and (round_idx + 1) % 5 == 0:

                msg = f"轮次 {round_idx + 1}/{n_rounds}"

                if test_labels is not None:

                    msg += f" | MSE: {metrics['mse']:.6f}"

                print(msg)



        return history





def create_vertical_fl_scenario(

    n_parties: int,

    features_per_party: int,

    n_samples: int,

    test_size: int,

    seed: int = 42

) -> Tuple[VerticalFederatedLearning, np.ndarray]:

    """

    创建纵向联邦学习场景



    Args:

        n_parties: 参与方数量

        features_per_party: 每个参与方的特征维度

        n_samples: 每方样本数

        test_size: 测试集大小

        seed: 随机种子



    Returns:

        (框架实例, 测试标签)

    """

    np.random.seed(seed)



    total_features = n_parties * features_per_party



    # 生成真实模型和标签

    w_true = np.random.randn(total_features) * 0.5

    sample_ids = list(range(n_samples))



    # 创建参与方

    parties = []

    party_feature_ranges = []

    all_features = []

    all_labels = []



    for i in range(n_parties):

        start = i * features_per_party

        end = (i + 1) * features_per_party

        party_feature_ranges.append((start, end))



        # 生成各方特征

        X_local = np.random.randn(n_samples, features_per_party)

        all_features.append(X_local)



        # 合并特征计算标签

        if i == 0:

            y = X_local @ w_true[start:end]

        else:

            y += X_local @ w_true[start:end]



    y = y + np.random.randn(n_samples) * 0.1

    all_labels = y



    # 测试集

    X_test_list = []

    for i in range(n_parties):

        X_test_local = np.random.randn(test_size, features_per_party)

        X_test_list.append(X_test_local)



    y_test_list = []

    for i in range(n_parties):

        if i == 0:

            y_test = X_test_list[i] @ w_true[party_feature_ranges[i][0]:party_feature_ranges[i][1]]

        else:

            y_test += X_test_list[i] @ w_true[party_feature_ranges[i][0]:party_feature_ranges[i][1]]

    y_test = y_test + np.random.randn(test_size) * 0.1



    # 创建参与方实例

    parties = []

    for i in range(n_parties):

        config = PartyConfig(

            party_id=i,

            n_features=features_per_party,

            sample_ids=sample_ids,

            has_label=(i == 0)  # 只有第一方有标签

        )

        party = VerticalParty(config)

        party.set_data(all_features[i], y if i == 0 else None)

        party.initialize_params(seed)

        parties.append(party)



    # 创建服务器

    server = VerticalFederatedServer(total_features)

    server.initialize_model(seed)

    server.align_samples([p.config for p in parties])



    # 创建框架

    framework = VerticalFederatedLearning(parties, server, party_feature_ranges)



    return framework, y_test





if __name__ == "__main__":

    print("=" * 60)

    print("纵向联邦学习框架演示")

    print("=" * 60)



    framework, y_test = create_vertical_fl_scenario(

        n_parties=3,           # 3个参与方

        features_per_party=5,  # 每方5个特征

        n_samples=500,         # 每方500样本

        test_size=200,

        seed=42

    )



    history = framework.train(

        n_rounds=20,

        learning_rate=0.1,

        test_labels=y_test,

        verbose=True

    )



    print("\n" + "=" * 60)

    print("训练完成!")

    print(f"最终MSE: {history['test_mse'][-1]:.6f}")

    print("=" * 60)

