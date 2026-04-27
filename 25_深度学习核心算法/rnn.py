# -*- coding: utf-8 -*-

"""

算法实现：25_深度学习核心算法 / rnn



本文件实现 rnn 相关的算法功能。

"""



import numpy as np





def sigmoid(x):

    """Sigmoid函数"""

    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))





def tanh(x):

    """Tanh函数"""

    return np.tanh(x)





class SimpleRNN:

    """

    基础RNN

    

    参数:

        input_dim: 输入维度

        hidden_dim: 隐藏层维度

        output_dim: 输出维度

    """

    

    def __init__(self, input_dim, hidden_dim, output_dim):

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim

        self.output_dim = output_dim

        

        # 输入到隐藏层

        self.W_xh = np.random.randn(input_dim, hidden_dim) * 0.01

        # 隐藏层到隐藏层（循环）

        self.W_hh = np.random.randn(hidden_dim, hidden_dim) * 0.01

        # 隐藏层到输出

        self.W_hy = np.random.randn(hidden_dim, output_dim) * 0.01

        

        # 偏置

        self.b_h = np.zeros(hidden_dim)

        self.b_y = np.zeros(output_dim)

    

    def forward(self, x_sequence):

        """

        前馈传播

        

        参数:

            x_sequence: 输入序列 (seq_len, input_dim) 或 (batch, seq_len, input_dim)

        返回:

            outputs: 输出序列

            hidden_states: 隐藏状态序列

        """

        if x_sequence.ndim == 2:

            x_sequence = x_sequence.reshape(1, *x_sequence.shape)

        

        batch_size, seq_len, _ = x_sequence.shape

        

        # 初始化隐藏状态

        h = np.zeros((batch_size, self.hidden_dim))

        hidden_states = []

        outputs = []

        

        for t in range(seq_len):

            x_t = x_sequence[:, t, :]  # (batch, input_dim)

            

            # RNN计算

            h = tanh(x_t @ self.W_xh + h @ self.W_hh + self.b_h)

            

            # 输出

            y_t = h @ self.W_hy + self.b_y

            y_t = sigmoid(y_t)

            

            hidden_states.append(h)

            outputs.append(y_t)

        

        return np.array(outputs), np.array(hidden_states)





class LSTM:

    """

    LSTM（长短期记忆网络）

    

    参数:

        input_dim: 输入维度

        hidden_dim: 隐藏层维度

        output_dim: 输出维度

    """

    

    def __init__(self, input_dim, hidden_dim, output_dim):

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim

        self.output_dim = output_dim

        

        # 遗忘门参数

        self.W_f = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_f = np.zeros(hidden_dim)

        

        # 输入门参数

        self.W_i = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_i = np.zeros(hidden_dim)

        

        # 候选记忆参数

        self.W_c = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_c = np.zeros(hidden_dim)

        

        # 输出门参数

        self.W_o = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_o = np.zeros(hidden_dim)

        

        # 输出参数

        self.W_y = np.random.randn(hidden_dim, output_dim) * 0.01

        self.b_y = np.zeros(output_dim)

    

    def forward(self, x_sequence):

        """

        前馈传播

        

        参数:

            x_sequence: 输入序列 (seq_len, input_dim) 或 (batch, seq_len, input_dim)

        返回:

            outputs: 输出序列

            hidden_states: 隐藏状态

            cell_states: 细胞状态

        """

        if x_sequence.ndim == 2:

            x_sequence = x_sequence.reshape(1, *x_sequence.shape)

        

        batch_size, seq_len, _ = x_sequence.shape

        

        # 初始化

        h = np.zeros((batch_size, self.hidden_dim))

        c = np.zeros((batch_size, self.hidden_dim))

        

        hidden_states = []

        cell_states = []

        outputs = []

        

        for t in range(seq_len):

            x_t = x_sequence[:, t, :]

            

            # 拼接输入和隐藏状态

            h_x = np.concatenate([h, x_t], axis=1)

            

            # 遗忘门

            f = sigmoid(h_x @ self.W_f + self.b_f)

            

            # 输入门

            i = sigmoid(h_x @ self.W_i + self.b_i)

            

            # 候选记忆

            c_tilde = tanh(h_x @ self.W_c + self.b_c)

            

            # 更新细胞状态

            c = f * c + i * c_tilde

            

            # 输出门

            o = sigmoid(h_x @ self.W_o + self.b_o)

            

            # 隐藏状态

            h = o * tanh(c)

            

            # 输出

            y_t = sigmoid(h @ self.W_y + self.b_y)

            

            hidden_states.append(h)

            cell_states.append(c)

            outputs.append(y_t)

        

        return np.array(outputs), np.array(hidden_states), np.array(cell_states)





class GRU:

    """

    GRU（门控循环单元）

    

    参数:

        input_dim: 输入维度

        hidden_dim: 隐藏层维度

        output_dim: 输出维度

    """

    

    def __init__(self, input_dim, hidden_dim, output_dim):

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim

        self.output_dim = output_dim

        

        # 更新门参数

        self.W_z = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_z = np.zeros(hidden_dim)

        

        # 重置门参数

        self.W_r = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_r = np.zeros(hidden_dim)

        

        # 候选隐藏状态参数

        self.W_h = np.random.randn(input_dim + hidden_dim, hidden_dim) * 0.01

        self.b_h = np.zeros(hidden_dim)

        

        # 输出参数

        self.W_y = np.random.randn(hidden_dim, output_dim) * 0.01

        self.b_y = np.zeros(output_dim)

    

    def forward(self, x_sequence):

        """前馈传播"""

        if x_sequence.ndim == 2:

            x_sequence = x_sequence.reshape(1, *x_sequence.shape)

        

        batch_size, seq_len, _ = x_sequence.shape

        

        h = np.zeros((batch_size, self.hidden_dim))

        hidden_states = []

        outputs = []

        

        for t in range(seq_len):

            x_t = x_sequence[:, t, :]

            h_x = np.concatenate([h, x_t], axis=1)

            

            # 更新门

            z = sigmoid(h_x @ self.W_z + self.b_z)

            

            # 重置门

            r = sigmoid(h_x @ self.W_r + self.b_r)

            

            # 候选隐藏状态

            h_x_r = np.concatenate([r * h, x_t], axis=1)

            h_tilde = tanh(h_x_r @ self.W_h + self.b_h)

            

            # 更新隐藏状态

            h = (1 - z) * h + z * h_tilde

            

            # 输出

            y_t = sigmoid(h @ self.W_y + self.b_y)

            

            hidden_states.append(h)

            outputs.append(y_t)

        

        return np.array(outputs), np.array(hidden_states)





class BidirectionalRNN:

    """

    双向RNN

    

    参数:

        rnn_type: RNN类型 ('rnn', 'lstm', 'gru')

        input_dim: 输入维度

        hidden_dim: 隐藏层维度

        output_dim: 输出维度

    """

    

    def __init__(self, rnn_type, input_dim, hidden_dim, output_dim):

        self.rnn_type = rnn_type

        self.input_dim = input_dim

        self.hidden_dim = hidden_dim

        

        # 正向RNN

        if rnn_type == 'rnn':

            self.forward_rnn = SimpleRNN(input_dim, hidden_dim, output_dim)

        elif rnn_type == 'lstm':

            self.forward_rnn = LSTM(input_dim, hidden_dim, output_dim)

        elif rnn_type == 'gru':

            self.forward_rnn = GRU(input_dim, hidden_dim, output_dim)

        

        # 反向RNN

        if rnn_type == 'rnn':

            self.backward_rnn = SimpleRNN(input_dim, hidden_dim, output_dim)

        elif rnn_type == 'lstm':

            self.backward_rnn = LSTM(input_dim, hidden_dim, output_dim)

        elif rnn_type == 'gru':

            self.backward_rnn = GRU(input_dim, hidden_dim, output_dim)

    

    def forward(self, x_sequence):

        """前馈传播"""

        # 正向

        outputs_fwd, hidden_fwd, *rest_fwd = self.forward_rnn.forward(x_sequence)

        

        # 反向（反转输入）

        x_reversed = x_sequence[:, ::-1, :]

        outputs_bwd, hidden_bwd, *rest_bwd = self.backward_rnn.forward(x_reversed)

        hidden_bwd = hidden_bwd[::-1]  # 翻转回来

        

        # 拼接双向隐藏状态

        hidden_combined = np.concatenate([hidden_fwd, hidden_bwd], axis=-1)

        

        return outputs_fwd, hidden_combined





if __name__ == "__main__":

    np.random.seed(42)

    

    print("=" * 55)

    print("循环神经网络（RNN）测试")

    print("=" * 55)

    

    # 参数

    input_dim = 10

    hidden_dim = 16

    output_dim = 5

    seq_len = 8

    batch_size = 4

    

    # 创建输入序列

    x = np.random.randn(batch_size, seq_len, input_dim)

    

    print(f"输入序列形状: {x.shape}")

    

    # 测试基础RNN

    print("\n--- 基础RNN ---")

    rnn = SimpleRNN(input_dim, hidden_dim, output_dim)

    outputs, hidden_states = rnn.forward(x)

    

    print(f"输出形状: {outputs.shape}")

    print(f"隐藏状态形状: {hidden_states.shape}")

    print(f"最终隐藏状态: {hidden_states[:, -1, :].shape}")

    

    # 测试LSTM

    print("\n--- LSTM ---")

    lstm = LSTM(input_dim, hidden_dim, output_dim)

    outputs_lstm, hidden_lstm, cell_lstm = lstm.forward(x)

    

    print(f"输出形状: {outputs_lstm.shape}")

    print(f"隐藏状态形状: {hidden_lstm.shape}")

    print(f"细胞状态形状: {cell_lstm.shape}")

    

    # 测试GRU

    print("\n--- GRU ---")

    gru = GRU(input_dim, hidden_dim, output_dim)

    outputs_gru, hidden_gru = gru.forward(x)

    

    print(f"输出形状: {outputs_gru.shape}")

    print(f"隐藏状态形状: {hidden_gru.shape}")

    

    # 测试双向RNN

    print("\n--- 双向RNN ---")

    bi_rnn = BidirectionalRNN('lstm', input_dim, hidden_dim, output_dim)

    outputs_bi, hidden_bi = bi_rnn.forward(x)

    

    print(f"输出形状: {outputs_bi.shape}")

    print(f"双向隐藏状态形状: {hidden_bi.shape}")

    print(f"拼接后维度: {hidden_bi.shape[-1]} (应该是 hidden_dim * 2)")

    

    # 不同序列长度的测试

    print("\n--- 不同序列长度 ---")

    for seq_len in [5, 10, 20, 50]:

        x_test = np.random.randn(2, seq_len, input_dim)

        outputs_test, _ = rnn.forward(x_test)

        print(f"  seq_len={seq_len:2d}: 输出形状={outputs_test.shape}")

    

    # 梯度流分析（简化）

    print("\n--- 梯度流分析 ---")

    print("LSTM的门控机制有助于解决梯度消失问题")

    

    # 打印各门的维度

    print(f"LSTM遗忘门参数形状: {lstm.W_f.shape}")

    print(f"LSTM输入门参数形状: {lstm.W_i.shape}")

    print(f"LSTM输出门参数形状: {lstm.W_o.shape}")

    

    print("\n循环神经网络测试完成！")

