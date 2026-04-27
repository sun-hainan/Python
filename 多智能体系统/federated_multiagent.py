# -*- coding: utf-8 -*-

"""

算法实现：多智能体系统 / federated_multiagent



本文件实现 federated_multiagent 相关的算法功能。

"""



import numpy as np

from collections import defaultdict





class LocalModel:

    """本地模型：智能体在本地训练的数据"""

    

    def __init__(self, agent_id, model_weights, train_samples, validation_accuracy=0.0):

        # agent_id: 智能体ID

        # model_weights: 模型权重参数

        # train_samples: 本地训练样本数

        # validation_accuracy: 验证准确率

        self.agent_id = agent_id

        self.model_weights = [w.copy() for w in model_weights]

        self.train_samples = train_samples

        self.validation_accuracy = validation_accuracy

        self.local_epochs = 0

    

    def get_weight_norm(self):

        """计算权重范数"""

        total_norm = 0.0

        for w in self.model_weights:

            total_norm += np.sum(w ** 2)

        return np.sqrt(total_norm)





class FederatedServer:

    """联邦学习服务器：协调模型聚合"""

    

    def __init__(self, global_model, aggregation_rule='fedavg'):

        # global_model: 全局模型初始权重

        # aggregation_rule: 聚合规则 ('fedavg', 'fedprox', 'byzantine')

        self.global_weights = [w.copy() for w in global_model]

        self.global_model_version = 0

        self.aggregation_rule = aggregation_rule

        

        # 参与智能体记录

        self.participant_history = []

        

        # FedProx参数

        self.mu = 0.01  # 近端项权重

        

        # 拜占庭检测参数

        self.byzantine_threshold = 0.5

    

    def aggregate_models(self, local_models, selected_agents=None):

        """

        聚合本地模型更新

        local_models: 参与本次聚合的本地模型列表

        selected_agents: 被选中参与的智能体ID列表

        """

        if not local_models:

            return

        

        n_models = len(local_models)

        

        if self.aggregation_rule == 'fedavg':

            # 联邦平均：按样本数加权

            total_samples = sum(m.train_samples for m in local_models)

            aggregated_weights = [np.zeros_like(w) for w in self.global_weights]

            

            for model in local_models:

                weight_factor = model.train_samples / total_samples

                for i, w in enumerate(model.model_weights):

                    aggregated_weights[i] += weight_factor * w

            

            self.global_weights = aggregated_weights

            

        elif self.aggregation_rule == 'fedprox':

            # FedProx：添加近端项

            total_samples = sum(m.train_samples for m in local_models)

            aggregated_weights = [np.zeros_like(w) for w in self.global_weights]

            

            for model in local_models:

                weight_factor = model.train_samples / total_samples

                for i, w in enumerate(model.model_weights):

                    # 近端项修正

                    diff = w - self.global_weights[i]

                    prox_correction = self.mu * diff

                    aggregated_weights[i] += weight_factor * (w - prox_correction)

            

            self.global_weights = aggregated_weights

            

        elif self.aggregation_rule == 'byzantine':

            # 拜占庭容错：使用中位数或修整均值

            aggregated_weights = self._byzantine_aggregate(local_models)

            self.global_weights = aggregated_weights

        

        self.global_model_version += 1

        

        # 记录参与者

        if selected_agents:

            self.participant_history.append(selected_agents.copy())

    

    def _byzantine_aggregate(self, local_models):

        """拜占庭容错聚合"""

        n_weights = len(self.global_weights)

        aggregated = []

        

        for i in range(n_weights):

            # 收集该层所有模型的权重

            layer_weights = [m.model_weights[i] for m in local_models]

            

            # 计算每个权重的范数

            norms = [np.linalg.norm(w) for w in layer_weights]

            median_norm = np.median(norms)

            

            # 过滤异常权重（范数偏离中位数过大的）

            valid_weights = [

                w for w, norm in zip(layer_weights, norms)

                if abs(norm - median_norm) < self.byzantine_threshold * median_norm

            ]

            

            if not valid_weights:

                valid_weights = layer_weights  # 回退到使用所有权重

            

            # 使用中位数聚合

            aggregated.append(np.median(np.array(valid_weights), axis=0))

        

        return aggregated

    

    def add_noise(self, noise_std=0.1):

        """添加高斯噪声实现差分隐私"""

        for i in range(len(self.global_weights)):

            self.global_weights[i] += np.random.randn(*self.global_weights[i].shape) * noise_std

    

    def get_global_model(self):

        """获取全局模型"""

        return [w.copy() for w in self.global_weights]

    

    def select_participants(self, all_agents, participation_rate=0.5, 

                          selection_method='random'):

        """

        选择参与本轮联邦学习的智能体

        selection_method: 'random', 'accuracy', 'availability'

        """

        n_total = len(all_agents)

        n_select = max(1, int(n_total * participation_rate))

        

        if selection_method == 'random':

            indices = np.random.choice(n_total, n_select, replace=False)

        elif selection_method == 'accuracy':

            # 选择准确率最高的

            sorted_idx = np.argsort([a.validation_accuracy for a in all_agents])[::-1]

            indices = sorted_idx[:n_select]

        else:

            indices = np.random.choice(n_total, n_select, replace=False)

        

        return indices.tolist()





class FederatedAgent:

    """联邦学习智能体"""

    

    def __init__(self, agent_id, local_data_size, model_structure):

        # agent_id: 智能体ID

        # local_data_size: 本地数据大小

        # model_structure: 模型结构维度

        self.agent_id = agent_id

        self.local_data_size = local_data_size

        

        # 初始化本地模型

        self.local_model = self._init_model(model_structure)

        self.validation_accuracy = np.random.uniform(0.6, 0.9)

        

        # 本地训练历史

        self.training_history = []

    

    def _init_model(self, structure):

        """初始化模型权重"""

        weights = []

        for i in range(len(structure) - 1):

            w = np.random.randn(structure[i], structure[i+1]) * 0.1

            b = np.random.randn(structure[i+1]) * 0.1

            weights.append(w)

            weights.append(b)

        return weights

    

    def receive_global_model(self, global_weights):

        """接收全局模型更新本地模型"""

        self.local_model = [w.copy() for w in global_weights]

    

    def local_train(self, epochs=5, learning_rate=0.01):

        """

        本地训练（模拟）

        实际应用中这里执行真正的模型训练

        """

        for epoch in range(epochs):

            # 模拟梯度下降

            for i in range(len(self.local_model)):

                grad = np.random.randn(*self.local_model[i].shape) * 0.01

                self.local_model[i] -= learning_rate * grad

        

        self.training_history.append({

            'epochs': epochs,

            'loss': np.random.uniform(0.1, 0.5)

        })

        

        # 模拟训练后准确率提升

        self.validation_accuracy = min(0.99, self.validation_accuracy + 0.02)

        

        return LocalModel(

            agent_id=self.agent_id,

            model_weights=self.local_model,

            train_samples=self.local_data_size,

            validation_accuracy=self.validation_accuracy

        )

    

    def compute_gradient_difference(self, global_weights):

        """计算本地模型与全局模型的差异（用于FedProx）"""

        diff = 0.0

        for local_w, global_w in zip(self.local_model, global_weights):

            diff += np.sum((local_w - global_w) ** 2)

        return np.sqrt(diff)





class FederatedMultiAgentLearning:

    """联邦多智能体学习主类"""

    

    def __init__(self, n_agents, model_structure, aggregation_rule='fedavg'):

        # n_agents: 智能体数量

        # model_structure: 模型结构 [input_dim, hidden1, ..., output_dim]

        # aggregation_rule: 聚合规则

        self.n_agents = n_agents

        self.model_structure = model_structure

        

        # 初始化全局模型

        init_weights = []

        for i in range(len(model_structure) - 1):

            w = np.random.randn(model_structure[i], model_structure[i+1]) * 0.1

            b = np.random.randn(model_structure[i+1]) * 0.1

            init_weights.append(w)

            init_weights.append(b)

        

        # 创建服务器

        self.server = FederatedServer(init_weights, aggregation_rule)

        

        # 创建智能体

        data_sizes = np.random.randint(100, 1000, n_agents)

        self.agents = [

            FederatedAgent(i, data_sizes[i], model_structure)

            for i in range(n_agents)

        ]

        

        # 通信轮次

        self.current_round = 0

    

    def run_round(self, participation_rate=0.7, local_epochs=5):

        """

        执行一轮联邦学习

        participation_rate: 参与率

        local_epochs: 本地训练轮数

        """

        self.current_round += 1

        print(f"\n===== 联邦学习第{self.current_round}轮 =====")

        

        # 选择参与者

        selected_ids = self.server.select_participants(

            self.agents, participation_rate, 'random'

        )

        print(f"  选中 {len(selected_ids)} 个智能体参与: {selected_ids}")

        

        # 获取全局模型

        global_weights = self.server.get_global_model()

        

        # 本地训练

        local_models = []

        for agent_id in selected_ids:

            agent = self.agents[agent_id]

            agent.receive_global_model(global_weights)

            local_model = agent.local_train(epochs=local_epochs)

            local_models.append(local_model)

            print(f"  智能体{agent_id}: 数据量={agent.local_data_size}, "

                  f"准确率={local_model.validation_accuracy:.4f}")

        

        # 聚合

        self.server.aggregate_models(local_models, selected_ids)

        print(f"  全局模型已更新，版本={self.server.global_model_version}")

        

        # 计算平均准确率

        avg_accuracy = np.mean([a.validation_accuracy for a in self.agents])

        print(f"  智能体平均准确率: {avg_accuracy:.4f}")

        

        return self.server.get_global_model()

    

    def run_training(self, n_rounds=10, participation_rate=0.7, local_epochs=5):

        """运行多轮联邦学习训练"""

        print("=" * 50)

        print("联邦多智能体学习训练")

        print("=" * 50)

        

        for round_num in range(n_rounds):

            self.run_round(participation_rate, local_epochs)

        

        print("\n训练完成!")

        print(f"  总轮数: {self.current_round}")

        print(f"  最终平均准确率: {np.mean([a.validation_accuracy for a in self.agents]):.4f}")

    

    def add_differential_privacy(self, noise_std=0.1):

        """为全局模型添加差分隐私噪声"""

        self.server.add_noise(noise_std)

    

    def get_convergence_status(self):

        """获取收敛状态"""

        accuracies = [a.validation_accuracy for a in self.agents]

        return {

            'mean': np.mean(accuracies),

            'std': np.std(accuracies),

            'min': np.min(accuracies),

            'max': np.max(accuracies)

        }





if __name__ == "__main__":

    # 测试联邦多智能体学习

    print("=" * 50)

    print("联邦多智能体学习测试")

    print("=" * 50)

    

    # 模型结构 [输入, 隐藏层, 输出]

    model_structure = [10, 64, 32, 5]

    n_agents = 5

    

    # 创建联邦学习系统

    fmal = FederatedMultiAgentLearning(

        n_agents=n_agents,

        model_structure=model_structure,

        aggregation_rule='fedavg'

    )

    

    print(f"\n智能体数量: {n_agents}")

    print(f"模型结构: {model_structure}")

    

    # 运行联邦学习

    fmal.run_training(n_rounds=5, participation_rate=0.8, local_epochs=3)

    

    # 检查收敛状态

    status = fmal.get_convergence_status()

    print(f"\n收敛状态: 均值={status['mean']:.4f}, 标准差={status['std']:.4f}")

    print(f"  范围: [{status['min']:.4f}, {status['max']:.4f}]")

    

    # 测试拜占庭容错

    print("\n--- 拜占庭容错联邦学习测试 ---")

    fmal_byzantine = FederatedMultiAgentLearning(

        n_agents=n_agents,

        model_structure=model_structure,

        aggregation_rule='byzantine'

    )

    fmal_byzantine.run_training(n_rounds=3, participation_rate=0.6, local_epochs=2)

    

    print("\n✓ 联邦多智能体学习测试完成")

