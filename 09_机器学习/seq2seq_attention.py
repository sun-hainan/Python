# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / seq2seq_attention



本文件实现 seq2seq_attention 相关的算法功能。

"""



import numpy as np





class Encoder:

    """

    编码器（单向GRU）



    参数:

        input_dim: 输入词汇量

        embed_dim: 词嵌入维度

        hidden_dim: 隐藏状态维度

    """



    def __init__(self, input_dim, embed_dim, hidden_dim):

        self.hidden_dim = hidden_dim



        # 词嵌入矩阵

        self.embedding = np.random.randn(input_dim, embed_dim) * 0.01

        # 输入到隐藏层

        self.W_xh = np.random.randn(embed_dim, hidden_dim) * np.sqrt(2.0 / embed_dim)

        # 隐藏层到隐藏层

        self.W_hh = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)

        self.b_h = np.zeros(hidden_dim)



    def forward(self, X):

        """

        前向传播



        参数:

            X: 输入序列 (batch, seq_len)



        返回:

            hidden_states: 所有时刻的隐藏状态 (seq_len, batch, hidden_dim)

        """

        batch_size, seq_len = X.shape

        embed = self.embedding[X]  # (batch, seq_len, embed_dim)



        hidden_states = []

        h_t = np.zeros((batch_size, self.hidden_dim))



        for t in range(seq_len):

            x_t = embed[:, t, :]  # (batch, embed_dim)

            h_t = np.tanh(x_t @ self.W_xh + h_t @ self.W_hh + self.b_h)

            hidden_states.append(h_t)



        return np.array(hidden_states)



    def forward_step(self, x_t, h_prev):

        """单步前向传播"""

        h_t = np.tanh(x_t @ self.W_xh + h_prev @ self.W_hh + self.b_h)

        return h_t





class BahdanauAttention:

    """

    Bahdanau Attention（加性注意力）



    参数:

        hidden_dim: 解码器隐藏状态维度

    """



    def __init__(self, hidden_dim):

        self.hidden_dim = hidden_dim



        # 评分函数参数

        self.W_a = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)

        self.W_s = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)

        self.v = np.random.randn(hidden_dim, 1) * np.sqrt(2.0 / hidden_dim)



    def forward(self, encoder_states, decoder_hidden):

        """

        计算注意力权重



        参数:

            encoder_states: 编码器隐藏状态 (seq_len, batch, hidden_dim)

            decoder_hidden: 解码器当前隐藏状态 (batch, hidden_dim)



        返回:

            context: 上下文向量 (batch, hidden_dim)

            attention_weights: 注意力权重 (batch, seq_len)

        """

        seq_len = encoder_states.shape[0]

        batch_size = decoder_hidden.shape[0]



        # 计算对齐分数 e_ij

        # e_ij = v^T · tanh(W_a * h_j + W_s * s_{i-1})

        scores = []

        for j in range(seq_len):

            h_j = encoder_states[j]  # (batch, hidden_dim)

            # tanh(W_a * h_j + W_s * s_{i-1})

            e = np.tanh(h_j @ self.W_a + decoder_hidden @ self.W_s)

            # v^T * e

            score = e @ self.v  # (batch, 1)

            scores.append(score.squeeze(-1))



        scores = np.array(scores).T  # (batch, seq_len)



        # Softmax归一化

        scores_exp = np.exp(scores - np.max(scores, axis=1, keepdims=True))

        attention_weights = scores_exp / np.sum(scores_exp, axis=1, keepdims=True)



        # 加权求和得到上下文向量

        context = np.zeros((batch_size, self.hidden_dim))

        for j in range(seq_len):

            context += attention_weights[:, j:j+1] * encoder_states[j]



        return context, attention_weights





class Decoder:

    """

    解码器（带Attention）



    参数:

        output_dim: 输出词汇量

        embed_dim: 词嵌入维度

        hidden_dim: 隐藏状态维度

    """



    def __init__(self, output_dim, embed_dim, hidden_dim):

        self.output_dim = output_dim

        self.hidden_dim = hidden_dim



        # 词嵌入

        self.embedding = np.random.randn(output_dim, embed_dim) * 0.01



        # 解码器GRU参数

        self.W_xh = np.random.randn(embed_dim + hidden_dim, hidden_dim) * np.sqrt(2.0 / (embed_dim + hidden_dim))

        self.W_hh = np.random.randn(hidden_dim, hidden_dim) * np.sqrt(2.0 / hidden_dim)

        self.b_h = np.zeros(hidden_dim)



        # 输出层

        self.W_y = np.random.randn(hidden_dim * 2, output_dim) * np.sqrt(2.0 / hidden_dim)

        self.b_y = np.zeros(output_dim)



        # Attention

        self.attention = BahdanauAttention(hidden_dim)



    def forward_step(self, y_t, h_prev, encoder_states):

        """

        解码器单步前向



        参数:

            y_t: 当前输入 (batch,)

            h_prev: 上一隐藏状态 (batch, hidden_dim)

            encoder_states: 编码器所有隐藏状态



        返回:

            output: 输出概率分布

            h_t: 新隐藏状态

            context: 上下文向量

            attention_weights: 注意力权重

        """

        batch_size = y_t.shape[0]



        # 词嵌入

        embed = self.embedding[y_t]  # (batch, embed_dim)



        # 计算Attention

        context, attention_weights = self.attention.forward(encoder_states, h_prev)



        # 拼接嵌入和上下文向量

        combined = np.concatenate([embed, context], axis=1)



        # GRU

        h_t = np.tanh(combined @ self.W_xh + h_prev @ self.W_hh + self.b_h)



        # 输出（拼接h_t和context）

        output_hidden = np.concatenate([h_t, context], axis=1)

        logits = output_hidden @ self.W_y + self.b_y

        output = self._softmax(logits)



        return output, h_t, context, attention_weights



    def _softmax(self, X):

        """Softmax函数"""

        exp_X = np.exp(X - np.max(X, axis=1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=1, keepdims=True)



    def forward(self, encoder_states, y_input, max_len=None):

        """

        完整解码过程



        参数:

            encoder_states: 编码器隐藏状态

            y_input: 目标序列输入 (teacher forcing)

            max_len: 最大解码长度



        返回:

            outputs: 所有时刻的输出

            attention_weights_list: 所有时刻的注意力权重

        """

        seq_len = y_input.shape[1]

        if max_len:

            seq_len = min(seq_len, max_len)



        batch_size = y_input.shape[0]

        h_t = np.zeros((batch_size, self.hidden_dim))



        outputs = []

        attention_weights_list = []



        for t in range(seq_len):

            output, h_t, context, attn = self.forward_step(

                y_input[:, t], h_t, encoder_states

            )

            outputs.append(output)

            attention_weights_list.append(attn)



        return np.array(outputs), np.array(attention_weights_list)





class Seq2SeqAttention:

    """

    完整Seq2Seq+Attention模型



    参数:

        input_dim: 输入词汇量

        output_dim: 输出词汇量

        embed_dim: 词嵌入维度

        hidden_dim: 隐藏状态维度

    """



    def __init__(self, input_dim, output_dim, embed_dim=128, hidden_dim=256):

        self.encoder = Encoder(input_dim, embed_dim, hidden_dim)

        self.decoder = Decoder(output_dim, embed_dim, hidden_dim)



    def forward(self, X, y_input):

        """

        前向传播



        参数:

            X: 输入序列 (batch, src_seq_len)

            y_input: 目标序列输入 (batch, tgt_seq_len)

        """

        encoder_states = self.encoder.forward(X)

        outputs, attention_weights = self.decoder.forward(encoder_states, y_input)

        return outputs, attention_weights



    def fit(self, X, y, epochs=10, lr=0.001):

        """训练（简化版）"""

        for epoch in range(epochs):

            outputs, _ = self.forward(X, y)

            if (epoch + 1) % 5 == 0:

                print(f"Epoch {epoch + 1}/{epochs}")



    def predict(self, X, max_len=20):

        """预测（贪心解码）"""

        encoder_states = self.encoder.forward(X)

        batch_size = X.shape[0]



        # 开始符

        y_pred = np.full((batch_size, 1), 2)  # 假设2是开始符

        h_t = np.zeros((batch_size, self.encoder.hidden_dim))



        predictions = []

        for _ in range(max_len):

            output, h_t, _, _ = self.decoder.forward_step(

                y_pred[:, -1], h_t, encoder_states

            )

            y_next = np.argmax(output, axis=1)

            predictions.append(y_next)

            y_pred = np.concatenate([y_pred, y_next.reshape(-1, 1)], axis=1)



        return np.array(predictions).T





if __name__ == "__main__":

    np.random.seed(42)



    # 模拟数据

    batch_size = 4

    src_len = 10

    tgt_len = 8

    input_dim = 100  # 输入词汇量

    output_dim = 100  # 输出词汇量



    # 随机序列

    X = np.random.randint(0, input_dim, size=(batch_size, src_len))

    y = np.random.randint(0, output_dim, size=(batch_size, tgt_len))



    # 创建模型

    model = Seq2SeqAttention(input_dim, output_dim, embed_dim=64, hidden_dim=128)



    # 训练

    print("训练Seq2Seq+Attention模型:")

    model.fit(X, y, epochs=20, lr=0.01)



    # 预测

    print("\n预测:")

    predictions = model.predict(X[:2], max_len=10)

    print(f"预测形状: {predictions.shape}")



    # 测试Attention

    print("\n测试Attention权重形状:")

    encoder_states = model.encoder.forward(X[:1])

    decoder_hidden = np.zeros((1, 128))

    context, attn = model.decoder.attention.forward(encoder_states, decoder_hidden)

    print(f"  编码器状态: {encoder_states.shape}")

    print(f"  上下文向量: {context.shape}")

    print(f"  注意力权重: {attn.shape}")

