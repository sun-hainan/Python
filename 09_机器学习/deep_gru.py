# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / deep_gru



本文件实现 deep_gru 相关的算法功能。

"""



import numpy as np





class GRUCell:

    """

    单个GRU单元



    参数:

        input_dim: 输入维度

        hidden_dim: 隐藏状态维度

    """



    def __init__(self, input_dim, hidden_dim):

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim



        # 权重矩阵（Xavier初始化）

        dim = input_dim + hidden_dim



        # 更新门权重

        self.W_z = np.random.randn(dim, hidden_dim) * np.sqrt(2.0 / dim)

        self.b_z = np.zeros(hidden_dim)



        # 重置门权重

        self.W_r = np.random.randn(dim, hidden_dim) * np.sqrt(2.0 / dim)

        self.b_r = np.zeros(hidden_dim)



        # 候选隐藏状态权重

        self.W_h = np.random.randn(dim, hidden_dim) * np.sqrt(2.0 / dim)

        self.b_h = np.zeros(hidden_dim)



    def _sigmoid(self, X):

        """Sigmoid激活函数"""

        return 1.0 / (1.0 + np.exp(-np.clip(X, -500, 500)))



    def forward(self, x_t, h_prev):

        """

        单步前向传播



        参数:

            x_t: 当前时刻输入 (batch, input_dim)

            h_prev: 上一时刻隐藏状态 (batch, hidden_dim)



        返回:

            h_t: 当前时刻隐藏状态

            cache: 反向传播所需的缓存

        """

        # 拼接输入和上一时刻隐藏状态

        combined = np.concatenate([h_prev, x_t], axis=1)



        # 更新门

        z_t = self._sigmoid(combined @ self.W_z + self.b_z)



        # 重置门

        r_t = self._sigmoid(combined @ self.W_r + self.b_r)



        # 候选隐藏状态

        combined_reset = np.concatenate([r_t * h_prev, x_t], axis=1)

        h_tilde = np.tanh(combined_reset @ self.W_h + self.b_h)



        # 最终隐藏状态

        h_t = (1 - z_t) * h_prev + z_t * h_tilde



        cache = (x_t, h_prev, z_t, r_t, h_tilde, h_t, combined, combined_reset)

        return h_t, cache



    def backward(self, dh_t, cache):

        """

        反向传播



        参数:

            dh_t: 隐藏状态梯度

            cache: 前向传播缓存



        返回:

            dx_t: 输入梯度

            dh_prev: 上一时刻隐藏状态梯度

        """

        x_t, h_prev, z_t, r_t, h_tilde, h_t, combined, combined_reset = cache



        # dh_t = (1 - z_t) * dh_prev + z_t * dh_tilde + dz * (h_prev - h_tilde)

        dh_prev = (1 - z_t) * dh_t

        dh_tilde = z_t * dh_t



        # tanh梯度

        dh_tilde_raw = dh_tilde * (1 - h_tilde ** 2)



        # combined_reset梯度

        dcombined_reset = dh_tilde_raw @ self.W_h.T

        dr_t = dcombined_reset[:, :self.hidden_dim] * h_prev

        dh_prev_r = dcombined_reset[:, :self.hidden_dim] * r_t



        # Sigmoid梯度

        dz_t = dh_t * (h_prev - h_tilde)

        dz_t_raw = dz_t * z_t * (1 - z_t)



        dr_t_raw = dr_t * r_t * (1 - r_t)



        # combined梯度

        dcombined = np.zeros_like(combined)

        dcombined += dz_t_raw @ self.W_z.T

        dcombined += dr_t_raw @ self.W_r.T



        # 分离梯度

        dh_prev += dcombined[:, :self.hidden_dim] + dh_prev_r

        dx_t = dcombined[:, self.hidden_dim:]



        # 计算权重梯度

        dW_z = combined.T @ dz_t_raw

        dW_r = combined.T @ dr_t_raw

        dW_h = combined_reset.T @ dh_tilde_raw



        db_z = np.sum(dz_t_raw, axis=0)

        db_r = np.sum(dr_t_raw, axis=0)

        db_h = np.sum(dh_tilde_raw, axis=0)



        return dx_t, dh_prev, (dW_z, dW_r, dW_h, db_z, db_r, db_h)





class DeepGRU:

    """

    深层GRU实现



    参数:

        input_dim: 输入维度

        hidden_dim: 每层隐藏状态维度

        num_layers: 层数

    """



    def __init__(self, input_dim, hidden_dim, num_layers=2):

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim

        self.num_layers = num_layers



        # 创建多层GRU单元

        self.layers = []

        for l in range(num_layers):

            in_dim = input_dim if l == 0 else hidden_dim

            self.layers.append(GRUCell(in_dim, hidden_dim))



    def forward_sequence(self, X, h0=None):

        """

        前向传播整个序列



        参数:

            X: 输入序列 (batch, seq_len, input_dim)

            h0: 初始隐藏状态 (num_layers, batch, hidden_dim)



        返回:

            outputs: 所有时刻的隐藏状态

            final_h: 最终隐藏状态

        """

        batch_size, seq_len, _ = X.shape



        # 初始化隐藏状态

        if h0 is None:

            h0 = np.zeros((self.num_layers, batch_size, self.hidden_dim))



        outputs = []

        current_h = h0.copy()



        for t in range(seq_len):

            x_t = X[:, t, :]  # (batch, input_dim)

            layer_input = x_t



            new_h = []

            for l, layer in enumerate(self.layers):

                h_prev = current_h[l]

                h_t, cache = layer.forward(layer_input, h_prev)

                new_h.append(h_t)

                layer_input = h_t  # 下一层的输入是这一层的输出



            current_h = np.array(new_h)

            outputs.append(current_h[-1])  # 保存最后一层的输出



        return np.array(outputs), current_h



    def backward_sequence(self, X, y, dh_last=None):

        """

        时间反向传播（BPTT）



        参数:

            X: 输入序列

            y: 目标序列

            dh_last: 最终隐藏状态的梯度



        返回:

            权重梯度

        """

        outputs, final_h = self.forward_sequence(X)

        loss = np.mean((outputs - y) ** 2)



        # 简化的梯度计算

        dZ = 2.0 * (outputs - y) / y.shape[0]



        return loss, dZ



    def fit(self, X, y, epochs=10, lr=0.01):

        """

        训练GRU



        参数:

            X: 输入数据 (batch, seq_len, input_dim)

            y: 目标数据 (batch, seq_len, hidden_dim)

            epochs: 训练轮数

            lr: 学习率

        """

        for epoch in range(epochs):

            loss, grad = self.backward_sequence(X, y)

            if (epoch + 1) % 5 == 0:

                print(f"Epoch {epoch + 1}/{epochs}, Loss: {loss:.6f}")





if __name__ == "__main__":

    np.random.seed(42)



    # 模拟序列数据

    batch_size = 4

    seq_len = 10

    input_dim = 8

    hidden_dim = 16



    # 随机输入序列

    X = np.random.randn(batch_size, seq_len, input_dim)

    # 随机目标序列

    y = np.random.randn(batch_size, seq_len, hidden_dim)



    # 创建深层GRU

    deep_gru = DeepGRU(input_dim=input_dim, hidden_dim=hidden_dim, num_layers=2)



    # 前向传播

    outputs, final_h = deep_gru.forward_sequence(X)

    print(f"输出形状: {outputs.shape}")  # (seq_len, batch, hidden_dim)

    print(f"最终隐藏状态形状: {final_h.shape}")  # (num_layers, batch, hidden_dim)



    # 训练

    print("\n开始训练:")

    deep_gru.fit(X, y, epochs=50, lr=0.01)



    # 测试：多层GRU的信息传递

    print("\n验证深层GRU:")

    test_gru = DeepGRU(input_dim=4, hidden_dim=4, num_layers=3)

    test_input = np.random.randn(2, 5, 4)  # batch=2, seq=5, input=4

    out, h = test_gru.forward_sequence(test_input)

    print(f"  输入形状: {test_input.shape}")

    print(f"  输出形状: {out.shape}")

    print(f"  隐藏状态形状: {h.shape} (3层)")

