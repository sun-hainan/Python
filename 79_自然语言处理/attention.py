# -*- coding: utf-8 -*-

"""

算法实现：自然语言处理 / attention



本文件实现 attention 相关的算法功能。

"""



import numpy as np





class ScaledDotProductAttention:

    """缩放点积注意力机制"""



    def __init__(self, scale=True):

        """

        scale: 是否使用缩放因子 1/sqrt(d_k)

        """

        self.scale = scale



    def forward(self, Q, K, V, mask=None):

        """

        Q: Query 矩阵 (n_q, d_k)

        K: Key 矩阵 (n_k, d_k)

        V: Value 矩阵 (n_v, d_v)，通常 n_k == n_v

        mask: 遮罩矩阵 (n_q, n_k)，True=需要遮罩



        返回: (output, attention_weights)

        output: (n_q, d_v)

        attention_weights: (n_q, n_k)

        """

        d_k = Q.shape[-1]



        # 1. 计算 QK^T / sqrt(d_k)

        scores = Q @ K.T  # (n_q, n_k)

        if self.scale:

            scores = scores / np.sqrt(d_k)



        # 2. 应用遮罩（将遮罩位置设为 -inf）

        if mask is not None:

            scores = np.where(mask, -1e9, scores)



        # 3. Softmax

        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))

        attention_weights = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)  # (n_q, n_k)



        # 4. 加权求和

        output = attention_weights @ V  # (n_q, d_v)



        return output, attention_weights



    def multi_head(self, Q, K, V, num_heads=8):

        """

        多头注意力

        将 Q, K, V 划分为 num_heads 个头，分别计算注意力后拼接

        """

        d_model = Q.shape[-1]

        d_k = d_model // num_heads



        # 分割成多个头（简化：直接分割通道维度）

        # 实际实现会先用线性投影，这里简化为按通道均分

        outputs = []

        attn_weights = []

        chunk_size = d_k

        for i in range(num_heads):

            start = i * chunk_size

            end = start + chunk_size

            Q_i = Q[:, start:end]

            K_i = K[:, start:end]

            V_i = V[:, start:end]

            out_i, attn_i = self.forward(Q_i, K_i, V_i)

            outputs.append(out_i)

            attn_weights.append(attn_i)



        # 拼接多个头

        output_concat = np.concatenate(outputs, axis=-1)  # (n_q, d_model)

        return output_concat, np.stack(attn_weights, axis=0)  # (num_heads, n_q, n_k)





class PositionalEncoding:

    """位置编码：为序列中的每个位置添加位置信息"""



    def __init__(self, d_model, max_len=5000):

        self.d_model = d_model

        # 预计算位置编码

        pe = np.zeros((max_len, d_model))

        position = np.arange(0, max_len).reshape(-1, 1)

        div_term = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))

        pe[:, 0::2] = np.sin(position * div_term)

        pe[:, 1::2] = np.cos(position * div_term)

        self.pe = pe



    def encode(self, seq_len):

        """获取序列长度对应的位置编码"""

        return self.pe[:seq_len]





class SelfAttentionLayer:

    """简化的 Self-Attention 层"""



    def __init__(self, d_model, num_heads=8):

        self.d_model = d_model

        self.num_heads = num_heads

        self.d_k = d_model // num_heads



        # 简化的线性投影（用 Xavier 初始化）

        scale = np.sqrt(2.0 / (d_model + d_model))

        self.W_Q = np.random.randn(d_model, d_model) * scale

        self.W_K = np.random.randn(d_model, d_model) * scale

        self.W_V = np.random.randn(d_model, d_model) * scale

        self.W_O = np.random.randn(d_model, d_model) * scale



        self.attention = ScaledDotProductAttention(scale=True)



    def forward(self, X, mask=None):

        """

        X: 输入序列 (batch_size, seq_len, d_model)

        返回: (output, attention_weights)

        """

        batch_size, seq_len, d_model = X.shape



        # 线性投影

        Q = X @ self.W_Q  # (batch, seq_len, d_model)

        K = X @ self.W_K

        V = X @ self.W_V



        # Reshape 为多头格式 (batch * num_heads, seq_len, d_k)

        Q = Q.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)

        K = K.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)

        V = V.reshape(batch_size, seq_len, self.num_heads, self.d_k).transpose(0, 2, 1, 3)



        Q = Q.reshape(-1, seq_len, self.d_k)

        K = K.reshape(-1, seq_len, self.d_k)

        V = V.reshape(-1, seq_len, self.d_k)



        # 计算注意力

        attn_out, attn_weights = self.attention.forward(Q, K, V, mask)



        # Reshape 回 (batch, num_heads, seq_len, d_k)

        seq_len_out = attn_out.shape[1]

        d_k_out = attn_out.shape[-1]

        attn_out = attn_out.reshape(batch_size, self.num_heads, seq_len_out, d_k_out)

        # 合并多头 -> (batch, seq_len, d_model)

        attn_out = attn_out.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, d_model)



        # 输出投影

        output = attn_out @ self.W_O



        return output, attn_weights





def demo():

    """Attention 机制演示"""

    print("=== Scaled Dot-Product Attention ===")



    # 模拟 Q, K, V

    np.random.seed(42)

    batch_size = 1

    seq_len = 5

    d_model = 8

    num_heads = 2



    X = np.random.randn(batch_size, seq_len, d_model)



    # Self-Attention 层

    layer = SelfAttentionLayer(d_model=d_model, num_heads=num_heads)

    output, attn_weights = layer.forward(X)



    print(f"输入 X 形状: {X.shape} -> 输出形状: {output.shape}")

    print(f"注意力权重形状: {attn_weights.shape}")

    print(f"\n注意力权重矩阵（多头）:")

    for h in range(attn_weights.shape[0]):

        print(f"  Head {h}:\n{attn_weights[h][0].round(3)}")



    # 位置编码

    print("\n=== 位置编码 ===")

    pe = PositionalEncoding(d_model=8)

    pos_enc = pe.encode(seq_len=6)

    print(f"位置编码形状: {pos_enc.shape}")

    print(f"位置 0: {pos_enc[0].round(4)}")

    print(f"位置 5: {pos_enc[5].round(4)}")



    # 演示 Encoder-Decoder Attention（Query 来自 decoder，Key/Value 来自 encoder）

    print("\n=== Encoder-Decoder Attention ===")

    enc_output = np.random.randn(batch_size, 6, d_model)  # encoder 输出

    dec_input = np.random.randn(batch_size, 4, d_model)  # decoder 输入



    attn = ScaledDotProductAttention()

    # decoder 的 Q 来自 dec_input，K/V 来自 enc_output

    Q_dec = dec_input @ layer.W_Q

    K_enc = enc_output @ layer.W_K

    V_enc = enc_output @ layer.W_V



    cross_out, cross_attn = attn.forward(Q_dec[0], K_enc[0], V_enc[0])

    print(f"Cross Attention 输出形状: {cross_out.shape}")

    print(f"Cross Attention 权重形状: {cross_attn.shape}")





if __name__ == "__main__":

    demo()

