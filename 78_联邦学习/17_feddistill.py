# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 17_feddistill



本文件实现 17_feddistill 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict

from scipy.special import softmax





class FederatedDistillationServer:

    """联邦蒸馏服务器"""



    def __init__(self, n_classes: int):

        """

        初始化服务器



        Args:

            n_classes: 类别数量

        """

        self.n_classes = n_classes

        self.global_logits = np.zeros(n_classes)  # 全局平均logits

        self.client_logits_history = []  # 客户端logits历史



    def aggregate_logits(

        self,

        client_logits: List[np.ndarray],

        client_weights: List[float]

    ) -> np.ndarray:

        """

        聚合客户端logits



        Args:

            client_logits: 客户端logits列表

            client_weights: 客户端权重



        Returns:

            聚合后的logits

        """

        total_weight = sum(client_weights)

        normalized_weights = [w / total_weight for w in client_weights]



        aggregated = np.zeros(self.n_classes)

        for logits, weight in zip(client_logits, normalized_weights):

            aggregated += weight * logits



        return aggregated



    def compute_distillation_loss(

        self,

        local_logits: np.ndarray,

        global_logits: np.ndarray,

        temperature: float = 2.0

    ) -> float:

        """

        计算蒸馏损失



        L_distill = KL(softmax(logits/T) || softmax(global_logits/T))



        Args:

            local_logits: 本地模型logits

            global_logits: 全局模型logits

            temperature: 温度参数



        Returns:

            蒸馏损失

        """

        # 软化logits

        local_soft = softmax(local_logits / temperature)

        global_soft = softmax(global_logits / temperature)



        # KL散度

        kl_div = np.sum(local_soft * np.log(local_soft / (global_soft + 1e-10) + 1e-10))



        return kl_div





class FederatedDistillationClient:

    """联邦蒸馏客户端"""



    def __init__(self, client_id: int, train_data: np.ndarray, train_labels: np.ndarray, n_classes: int):

        """初始化客户端"""

        self.client_id = client_id

        self.train_data = train_data

        self.train_labels = train_labels

        self.n_classes = n_classes

        self.model_params = None

        self.local_logits = None



    def initialize_model(self, dim: int, seed: int = 42):

        """初始化模型"""

        np.random.seed(seed + self.client_id)

        self.model_params = np.random.randn(dim, n_classes) * 0.01



    def local_train(

        self,

        global_logits: np.ndarray,

        local_epochs: int,

        learning_rate: float,

        temperature: float = 2.0,

        alpha: float = 0.5

    ) -> Tuple[np.ndarray, float]:

        """

        本地训练(带蒸馏损失)



        损失 = alpha * 任务损失 + (1-alpha) * 蒸馏损失



        Args:

            global_logits: 全局logits(知识)

            local_epochs: 本地训练轮数

            learning_rate: 学习率

            temperature: 温度参数

            alpha: 任务损失权重



        Returns:

            (更新后的模型参数, 本地logits)

        """

        n_samples = len(self.train_labels)

        dim = self.model_params.shape[0]



        for _ in range(local_epochs):

            # 前向传播

            logits = self.train_data @ self.model_params



            # 任务损失(交叉熵)

            log_probs = logits - np.log(np.sum(np.exp(logits), axis=1, keepdims=True) + 1e-10)

            task_loss = -np.mean(log_probs[np.arange(n_samples), self.train_labels.astype(int)])



            # 蒸馏损失

            distill_loss = self._compute_distillation_loss(logits, global_logits, temperature)



            # 总损失

            loss = alpha * task_loss + (1 - alpha) * distill_loss



            # 梯度(简化)

            gradients = (1.0 / n_samples) * self.train_data.T @ (logits - self.train_labels[:, np.newaxis])

            self.model_params = self.model_params - learning_rate * gradients



        # 计算最终logits

        final_logits = self.train_data @ self.model_params

        self.local_logits = np.mean(final_logits, axis=0)  # 平均logits



        return self.model_params, self.local_logits



    def _compute_distillation_loss(

        self,

        local_logits: np.ndarray,

        global_logits: np.ndarray,

        temperature: float

    ) -> float:

        """计算蒸馏损失"""

        # 简化的蒸馏损失

        local_soft = np.mean(softmax(local_logits / temperature, axis=1), axis=0)

        global_soft = softmax(global_logits / temperature)



        kl_div = np.sum(local_soft * np.log(local_soft / (global_soft + 1e-10) + 1e-10))



        return kl_div





def run_federated_distillation(

    n_clients: int,

    model_dim: int,

    n_classes: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    temperature: float = 2.0,

    alpha: float = 0.5,

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """运行联邦蒸馏"""

    np.random.seed(seed)



    # 生成数据

    w_true = np.random.randn(model_dim, n_classes) * 0.5



    client_data_list = []

    client_weights = []



    for i in range(n_clients):

        X = np.random.randn(data_per_client, model_dim)

        y = np.random.randint(0, n_classes, data_per_client)

        client_data_list.append((X, y))

        client_weights.append(float(data_per_client))



    X_test = np.random.randn(test_size, model_dim)

    y_test = np.random.randint(0, n_classes, test_size)



    # 初始化服务器

    server = FederatedDistillationServer(n_classes)

    global_logits = np.zeros(n_classes)



    # 初始化客户端

    clients = []

    for i, (data, labels) in enumerate(client_data_list):

        client = FederatedDistillationClient(i, data, labels, n_classes)

        client.initialize_model(model_dim)

        clients.append(client)



    history = {"rounds": [], "test_accuracy": []}



    print(f"联邦蒸馏: T={temperature}, alpha={alpha}")



    for round_idx in range(n_rounds):

        client_logits = []



        # 本地训练

        for client in clients:

            _, logits = client.local_train(

                global_logits, local_epochs, learning_rate, temperature, alpha

            )

            client_logits.append(logits)



        # 聚合logits

        global_logits = server.aggregate_logits(client_logits, client_weights)



        # 评估(用第一个客户端的模型)

        test_logits = X_test @ clients[0].model_params

        test_preds = np.argmax(test_logits, axis=1)

        accuracy = np.mean(test_preds == y_test)



        history["rounds"].append(round_idx + 1)

        history["test_accuracy"].append(accuracy)



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | 准确率: {accuracy:.4f}")



    return {"history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("联邦学习 - FedDistill 联邦蒸馏演示")

    print("=" * 60)



    result = run_federated_distillation(

        n_clients=5,

        model_dim=20,

        n_classes=5,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        temperature=2.0,

        alpha=0.5,

        data_per_client=200,

        test_size=500,

        seed=42

    )



    print("\n" + "=" * 60)

    print(f"最终准确率: {result['history']['test_accuracy'][-1]:.4f}")

    print("=" * 60)

