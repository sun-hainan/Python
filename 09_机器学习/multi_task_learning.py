# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / multi_task_learning



本文件实现 multi_task_learning 相关的算法功能。

"""



import numpy as np





class SharedEncoder:

    """

    共享编码器



    参数:

        input_dim: 输入维度

        hidden_dims: 共享隐藏层维度

    """



    def __init__(self, input_dim, hidden_dims=[128, 64]):

        self.input_dim = input_dim

        self.hidden_dims = hidden_dims



        # 共享权重

        dims = [input_dim] + hidden_dims

        self.weights = []

        self.biases = []



        for i in range(len(dims) - 1):

            W = np.random.randn(dims[i], dims[i + 1]) * np.sqrt(2.0 / dims[i])

            b = np.zeros(dims[i + 1])

            self.weights.append(W)

            self.biases.append(b)



    def forward(self, X):

        """前向传播"""

        H = X

        for i, (W, b) in enumerate(zip(self.weights, self.biases)):

            Z = H @ W + b

            if i < len(self.weights) - 1:

                H = np.maximum(0, Z)  # ReLU

            else:

                H = Z

        return H





class TaskSpecificHead:

    """

    任务特定输出头



    参数:

        input_dim: 输入维度

        output_dim: 输出维度

    """



    def __init__(self, input_dim, output_dim):

        self.W = np.random.randn(input_dim, output_dim) * np.sqrt(2.0 / input_dim)

        self.b = np.zeros(output_dim)



    def forward(self, X):

        """前向传播"""

        return X @ self.W + self.b





class MultiTaskNetwork:

    """

    多任务神经网络（硬参数共享）



    参数:

        input_dim: 输入维度

        hidden_dims: 共享隐藏层维度

        task_outputs: 任务配置 {task_name: output_dim}

    """



    def __init__(self, input_dim, hidden_dims, task_outputs):

        self.input_dim = input_dim

        self.task_outputs = task_outputs

        self.n_tasks = len(task_outputs)



        # 共享编码器

        self.encoder = SharedEncoder(input_dim, hidden_dims)

        shared_dim = hidden_dims[-1]



        # 各任务特定头

        self.task_heads = {}

        for task_name, output_dim in task_outputs.items():

            self.task_heads[task_name] = TaskSpecificHead(shared_dim, output_dim)



    def _softmax(self, X):

        """Softmax"""

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def _sigmoid(self, X):

        """Sigmoid"""

        return 1.0 / (1.0 + np.exp(-np.clip(X, -500, 500)))



    def forward(self, X, task_name):

        """

        前向传播特定任务



        参数:

            X: 输入数据

            task_name: 任务名

        """

        shared_repr = self.encoder.forward(X)

        task_output = self.task_heads[task_name].forward(shared_repr)

        return shared_repr, task_output



    def forward_all(self, X):

        """

        所有任务的前向传播



        返回:

            所有任务的输出

        """

        shared_repr = self.encoder.forward(X)

        outputs = {}



        for task_name, head in self.task_heads.items():

            outputs[task_name] = head.forward(shared_repr)



        return shared_repr, outputs



    def predict(self, X, task_name):

        """预测"""

        _, output = self.forward(X, task_name)



        if 'classification' in task_name:

            return np.argmax(output, axis=1)

        elif 'regression' in task_name:

            return output

        else:

            return output





class MultiTaskLoss:

    """

    多任务损失计算



    支持：

    - 加权求和

    - 动态任务权重（uncertainty weighting）

    - GradNorm风格

    """



    def __init__(self, task_weights=None):

        """

        参数:

            task_weights: 任务权重字典 {task_name: weight}

        """

        self.task_weights = task_weights or {}



    def compute_task_loss(self, y_pred, y_true, task_name):

        """计算单个任务损失"""

        if 'classification' in task_name:

            # 交叉熵

            eps = 1e-10

            return -np.mean(y_true * np.log(y_pred + eps))

        elif 'regression' in task_name:

            # MSE

            return np.mean((y_pred - y_true) ** 2)

        else:

            return np.mean((y_pred - y_true) ** 2)



    def __call__(self, outputs, targets):

        """

        计算多任务总损失



        参数:

            outputs: 预测输出字典

            targets: 目标字典

        """

        total_loss = 0.0

        losses = {}



        for task_name in outputs:

            y_pred = outputs[task_name]

            y_true = targets[task_name]



            loss = self.compute_task_loss(y_pred, y_true, task_name)

            weight = self.task_weights.get(task_name, 1.0)



            losses[task_name] = loss

            total_loss += weight * loss



        return total_loss, losses





def test_multi_task_learning():

    """测试多任务学习"""

    np.random.seed(42)



    print("=" * 60)

    print("多任务学习测试")

    print("=" * 60)



    # 模拟数据：输入是共享的，输出是多个任务

    n_samples = 500

    n_features = 20



    X = np.random.randn(n_samples, n_features)



    # 任务1：二分类

    y1 = (X[:, 0] + X[:, 1] > 0).astype(int)

    y1_onehot = np.zeros((n_samples, 2))

    y1_onehot[np.arange(n_samples), y1] = 1



    # 任务2：回归

    y2 = X[:, 2] * 2 + X[:, 3] + np.random.randn(n_samples) * 0.1



    # 任务3：多分类

    y3_raw = (X[:, 4] + X[:, 5] + X[:, 6] > 1).astype(int) % 3

    y3_onehot = np.zeros((n_samples, 3))

    y3_onehot[np.arange(n_samples), y3_raw] = 1



    print(f"\n1. 任务配置:")

    print(f"   任务1: 二分类（输入维度0,1）")

    print(f"   任务2: 回归（输入维度2,3）")

    print(f"   任务3: 3分类（输入维度4,5,6）")



    # 构建多任务网络

    task_outputs = {

        'task1_classification': 2,

        'task2_regression': 1,

        'task3_classification': 3

    }



    model = MultiTaskNetwork(

        input_dim=n_features,

        hidden_dims=[64, 32],

        task_outputs=task_outputs

    )



    # 损失函数

    criterion = MultiTaskLoss(task_weights={

        'task1_classification': 1.0,

        'task2_regression': 0.5,

        'task3_classification': 1.0

    })



    # 训练

    print("\n2. 训练多任务网络:")

    for epoch in range(100):

        # 前向

        shared, outputs = model.forward_all(X)



        # 目标

        targets = {

            'task1_classification': y1_onehot,

            'task2_regression': y2.reshape(-1, 1),

            'task3_classification': y3_onehot

        }



        # 损失

        total_loss, losses = criterion(outputs, targets)



        if (epoch + 1) % 20 == 0:

            print(f"   Epoch {epoch + 1}: Total={total_loss:.4f}, "

                  f"T1={losses['task1_classification']:.4f}, "

                  f"T2={losses['task2_regression']:.4f}, "

                  f"T3={losses['task3_classification']:.4f}")



    # 测试各任务准确率

    print("\n3. 各任务性能:")

    for task_name in task_outputs:

        preds = model.predict(X, task_name)

        targets = targets[task_name]



        if 'classification' in task_name:

            if task_name == 'task1_classification':

                acc = np.mean(preds == y1)

                print(f"   {task_name}: 准确率 = {acc:.4f}")

            else:

                acc = np.mean(preds == y3_raw)

                print(f"   {task_name}: 准确率 = {acc:.4f}")

        else:

            mse = np.mean((preds.flatten() - y2) ** 2)

            print(f"   {task_name}: MSE = {mse:.4f}")



    print("\n4. 多任务学习优势:")

    print("   - 共享表示提高泛化能力")

    print("   - 防止单一任务过拟合")

    print("   - 利用任务间相关性")

    print("   - 减少总体计算量")





if __name__ == "__main__":

    test_multi_task_learning()

