# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / federated_learning



本文件实现 federated_learning 相关的算法功能。

"""



import numpy as np





class FederatedClient:

    """

    联邦学习客户端



    参数:

        client_id: 客户端ID

        X, y: 本地数据

    """



    def __init__(self, client_id, X, y):

        self.client_id = client_id

        self.X = X

        self.y = y

        self.n_samples = len(y)



    def get_model_update(self, global_model, epochs=5, lr=0.01):

        """

        本地训练并返回模型更新



        参数:

            global_model: 全局模型

            epochs: 本地训练轮数

            lr: 学习率



        返回:

            delta_weights: 权重更新量

            n_samples: 参与训练的样本数

        """

        # 记录训练前参数

        old_weights = {k: v.copy() for k, v in global_model.get_weights().items()}



        # 本地训练

        for epoch in range(epochs):

            # 随机采样

            indices = np.random.choice(self.n_samples, min(16, self.n_samples), replace=False)

            batch_X = self.X[indices]

            batch_y = self.y[indices]



            # 前向（简化）

            y_pred = global_model.forward(batch_X)



            # 简化的参数更新

            global_model.local_update(lr=lr)



        # 计算更新量

        delta_weights = {}

        for k in old_weights:

            delta_weights[k] = global_model.get_weights()[k] - old_weights[k]



        return delta_weights, self.n_samples



    def fit(self, global_model, epochs=5, lr=0.01):

        """本地训练（更新全局模型）"""

        for epoch in range(epochs):

            indices = np.random.choice(self.n_samples, min(16, self.n_samples), replace=False)

            batch_X = self.X[indices]

            batch_y = self.y[indices]



            y_pred = global_model.forward(batch_X)

            global_model.local_update(lr=lr)





class SimpleNN:

    """简单神经网络"""



    def __init__(self, layer_dims):

        self.weights = {}

        self.biases = {}



        for i in range(len(layer_dims) - 1):

            fan_in = layer_dims[i]

            fan_out = layer_dims[i + 1]

            self.weights[f'W{i}'] = np.random.randn(fan_in, fan_out) * np.sqrt(2.0 / fan_in)

            self.biases[f'b{i}'] = np.zeros(fan_out)



    def get_weights(self):

        return {**self.weights, **self.biases}



    def forward(self, X):

        H = X

        for i, (W, b) in enumerate(zip(self.weights.values(), self.biases.values())):

            Z = H @ W + b

            if i < len(self.weights) - 1:

                H = np.maximum(0, Z)

            else:

                H = self._softmax(Z)

        return H



    def _softmax(self, X):

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def local_update(self, lr=0.01):

        """简化的本地更新"""

        for name in self.weights:

            self.weights[name] -= lr * 0.001

        for name in self.biases:

            self.biases[name] -= lr * 0.001



    def set_weights(self, weights):

        for k, v in weights.items():

            if k.startswith('W'):

                self.weights[k] = v

            elif k.startswith('b'):

                self.biases[k] = v





class FederatedServer:

    """

    联邦学习服务器



    参数:

        model: 全局模型

        clients: 客户端列表

    """



    def __init__(self, model, clients):

        self.model = model

        self.clients = clients

        self.total_samples = sum(c.n_samples for c in clients)



    def federated_averaging(self, updates, client_weights):

        """

        FedAvg聚合



        参数:

            updates: 客户端更新列表

            client_weights: 客户端权重（样本数）



        返回:

            聚合后的更新

        """

        aggregated = {}



        for key in updates[0].keys():

            # 加权平均

            weighted_sum = np.zeros_like(updates[0][key])

            for update, weight in zip(updates, client_weights):

                weighted_sum += update[key] * weight



            aggregated[key] = weighted_sum / sum(client_weights)



        return aggregated



    def broadcast(self, weights):

        """向所有客户端广播模型"""

        for client in self.clients:

            client.model.set_weights(weights)



    def run_round(self, epochs=5, lr=0.01, frac_clients=1.0):

        """

        运行一轮联邦学习



        参数:

            epochs: 本地训练轮数

            lr: 学习率

            frac_clients: 参与客户端比例



        返回:

            聚合后的全局模型权重

        """

        # 随机选择客户端

        n_clients = max(1, int(len(self.clients) * frac_clients))

        selected_clients = np.random.choice(self.clients, n_clients, replace=False)



        # 客户端本地训练

        updates = []

        weights = []



        for client in selected_clients:

            delta, n = client.get_model_update(self.model, epochs=epochs, lr=lr)

            updates.append(delta)

            weights.append(n)



        # 聚合更新

        aggregated = self.federated_averaging(updates, weights)



        # 更新全局模型

        current_weights = self.model.get_weights()

        for k in current_weights:

            current_weights[k] += aggregated[k]

        self.model.set_weights(current_weights)



        return self.model.get_weights()



    def fit(self, n_rounds=10, epochs_per_round=5, lr=0.01):

        """

        联邦学习训练



        参数:

            n_rounds: 通信轮数

            epochs_per_round: 每轮本地训练轮数

            lr: 学习率

        """

        for round_num in range(n_rounds):

            # 执行一轮

            self.run_round(epochs=epochs_per_round, lr=lr)



            # 评估全局模型

            if (round_num + 1) % 5 == 0:

                # 汇总所有客户端数据评估

                all_X = np.vstack([c.X for c in self.clients])

                all_y = np.vstack([c.y for c in self.clients])



                y_pred = self.model.forward(all_X)

                acc = np.mean(np.argmax(y_pred, axis=1) == np.argmax(all_y, axis=1))

                print(f"   Round {round_num + 1}, Global Acc: {acc:.4f}")





def test_federated_learning():

    """测试联邦学习"""

    np.random.seed(42)



    print("=" * 60)

    print("联邦学习测试")

    print("=" * 60)



    # 模拟数据：3个客户端，数据分布不同

    n_clients = 3

    n_samples = 100

    n_features = 20

    n_classes = 2



    clients = []



    for i in range(n_clients):

        # 每个客户端有自己的数据分布

        X_i = np.random.randn(n_samples, n_features) + i

        y_i = np.zeros((n_samples, n_classes))

        labels = (np.sum(X_i[:, :3], axis=1) > 0).astype(int)

        y_i[np.arange(n_samples), labels] = 1



        client = FederatedClient(client_id=i, X=X_i, y=y_i)

        clients.append(client)



    print(f"\n1. 联邦学习配置:")

    print(f"   客户端数: {n_clients}")

    print(f"   每客户端样本数: {n_samples}")

    print(f"   通信轮数: 20")



    # 初始化全局模型

    global_model = SimpleNN([n_features, 32, 16, n_classes])



    # 创建服务器

    server = FederatedServer(model=global_model, clients=clients)



    # 联邦学习

    print("\n2. 联邦学习训练:")

    server.fit(n_rounds=20, epochs_per_round=5, lr=0.01)



    # 最终评估

    print("\n3. 最终性能:")

    all_X = np.vstack([c.X for c in clients])

    all_y = np.vstack([c.y for c in clients])



    y_pred = global_model.forward(all_X)

    acc = np.mean(np.argmax(y_pred, axis=1) == np.argmax(all_y, axis=1))

    print(f"   全局模型准确率: {acc:.4f}")



    # 各客户端性能

    print("\n4. 各客户端准确率:")

    for client in clients:

        y_pred = global_model.forward(client.X)

        acc = np.mean(np.argmax(y_pred, axis=1) == np.argmax(client.y, axis=1))

        print(f"   Client {client.client_id}: {acc:.4f}")



    print("\n5. 联邦学习关键点:")

    print("   - 数据不出本地，保护隐私")

    print("   - 客户端本地训练，减少通信")

    print("   - FedAvg加权聚合")

    print("   - 适合移动端/边缘设备场景")





if __name__ == "__main__":

    test_federated_learning()

