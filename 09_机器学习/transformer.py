# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / transformer



本文件实现 transformer 相关的算法功能。

"""



import numpy as np





class PositionalEncoding:

    """

    位置编码



    参数:

        d_model: 模型维度

        max_len: 最大序列长度

    """



    def __init__(self, d_model, max_len=5000):

        self.d_model = d_model

        self.pe = self._create_encoding(max_len)



    def _create_encoding(self, max_len):

        """创建位置编码矩阵"""

        pe = np.zeros((max_len, self.d_model))



        # 计算位置编码

        position = np.arange(0, max_len).reshape(-1, 1)

        div_term = np.exp(np.arange(0, self.d_model, 2) * (-np.log(10000.0) / self.d_model))



        # 偶数维度用sin

        pe[:, 0::2] = np.sin(position * div_term)

        # 奇数维度用cos

        pe[:, 1::2] = np.cos(position * div_term)



        return pe



    def forward(self, seq_len):

        """获取指定长度的位置编码"""

        return self.pe[:seq_len]





class ScaledDotProductAttention:

    """

    缩放点积注意力



    公式: Attention(Q, K, V) = softmax(QK^T / √d_k) * V

    """



    def __init__(self, d_k):

        self.d_k = d_k



    def forward(self, Q, K, V, mask=None):

        """

        参数:

            Q: 查询 (batch, heads, seq_len, d_k)

            K: 键 (batch, heads, seq_len, d_k)

            V: 值 (batch, heads, seq_len, d_v)

            mask: 掩码 (batch, 1, seq_len, seq_len)



        返回:

            output: 注意力输出

            attention_weights: 注意力权重

        """

        # 计算注意力分数

        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(self.d_k)



        # 应用掩码（可选）

        if mask is not None:

            scores = np.where(mask, -1e9, scores)



        # Softmax

        attention_weights = self._softmax(scores)



        # 加权求和

        output = attention_weights @ V



        return output, attention_weights



    def _softmax(self, X):

        """多维Softmax"""

        exp_X = np.exp(X - np.max(X, axis=-1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=-1, keepdims=True)





class MultiHeadAttention:

    """

    多头注意力



    参数:

        d_model: 模型维度

        n_heads: 注意力头数

    """



    def __init__(self, d_model, n_heads=8):

        assert d_model % n_heads == 0, "d_model必须能被n_heads整除"



        self.d_model = d_model

        self.n_heads = n_heads

        self.d_k = d_model // n_heads

        self.d_v = d_model // n_heads



        # 权重矩阵

        self.W_Q = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)

        self.W_K = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)

        self.W_V = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)

        self.W_O = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)



        self.attention = ScaledDotProductAttention(self.d_k)



    def _split_heads(self, X):

        """分割多头"""

        batch_size, seq_len, d_model = X.shape

        X = X.reshape(batch_size, seq_len, self.n_heads, self.d_k)

        return X.transpose(0, 2, 1, 3)  # (batch, heads, seq_len, d_k)



    def _combine_heads(self, X):

        """合并多头"""

        batch_size, _, seq_len, d_k = X.shape

        X = X.transpose(0, 2, 1, 3)  # (batch, seq_len, heads, d_k)

        return X.reshape(batch_size, seq_len, self.d_model)



    def forward(self, Q, K, V, mask=None):

        """

        前向传播



        参数:

            Q: 查询 (batch, seq_len, d_model)

            K: 键 (batch, seq_len, d_model)

            V: 值 (batch, seq_len, d_model)

            mask: 掩码



        返回:

            output: 多头注意力输出

            attention_weights: 注意力权重

        """

        batch_size = Q.shape[0]



        # 线性变换

        Q = Q @ self.W_Q

        K = K @ self.W_K

        V = V @ self.W_V



        # 分割多头

        Q = self._split_heads(Q)

        K = self._split_heads(K)

        V = self._split_heads(V)



        # 缩放点积注意力

        attn_output, attention_weights = self.attention.forward(Q, K, V, mask)



        # 合并多头

        output = self._combine_heads(attn_output)



        # 最终线性变换

        output = output @ self.W_O



        return output, attention_weights





class FeedForwardNetwork:

    """

    前馈神经网络



    两层全连接：Linear -> ReLU -> Linear

    """



    def __init__(self, d_model, d_ff=2048, dropout=0.1):

        self.d_model = d_model

        self.d_ff = d_ff



        self.W1 = np.random.randn(d_model, d_ff) * np.sqrt(2.0 / d_model)

        self.b1 = np.zeros(d_ff)

        self.W2 = np.random.randn(d_ff, d_model) * np.sqrt(2.0 / d_ff)

        self.b2 = np.zeros(d_model)



    def forward(self, X):

        """前向传播"""

        # 第一层

        Z1 = X @ self.W1 + self.b1

        A1 = np.maximum(0, Z1)  # ReLU



        # 第二层

        Z2 = A1 @ self.W2 + self.b2



        return Z2





class TransformerEncoderLayer:

    """

    Transformer编码器层



    结构: Multi-Head Attention -> Add & Norm -> FFN -> Add & Norm

    """



    def __init__(self, d_model, n_heads=8, d_ff=2048):

        self.attention = MultiHeadAttention(d_model, n_heads)

        self.norm1 = LayerNorm(d_model)

        self.ffn = FeedForwardNetwork(d_model, d_ff)

        self.norm2 = LayerNorm(d_model)



    def forward(self, X, mask=None):

        """前向传播"""

        # Multi-Head Attention + Add & Norm

        attn_output, _ = self.attention.forward(Q=X, K=X, V=X, mask=mask)

        X = self.norm1.forward(X + attn_output)



        # FFN + Add & Norm

        ffn_output = self.ffn.forward(X)

        X = self.norm2.forward(X + ffn_output)



        return X





class TransformerDecoderLayer:

    """

    Transformer解码器层



    结构: Masked MHA -> Add & Norm -> MHA (cross attention) -> Add & Norm -> FFN -> Add & Norm

    """



    def __init__(self, d_model, n_heads=8, d_ff=2048):

        self.masked_attention = MultiHeadAttention(d_model, n_heads)

        self.norm1 = LayerNorm(d_model)



        self.attention = MultiHeadAttention(d_model, n_heads)

        self.norm2 = LayerNorm(d_model)



        self.ffn = FeedForwardNetwork(d_model, d_ff)

        self.norm3 = LayerNorm(d_model)



    def forward(self, X, encoder_output, src_mask=None, tgt_mask=None):

        """前向传播"""

        # Masked Multi-Head Attention (解码器自注意力)

        masked_attn, _ = self.masked_attention.forward(Q=X, K=X, V=X, mask=tgt_mask)

        X = self.norm1.forward(X + masked_attn)



        # Cross Attention (编码器-解码器注意力)

        cross_attn, _ = self.attention.forward(Q=X, K=encoder_output, V=encoder_output, mask=src_mask)

        X = self.norm2.forward(X + cross_attn)



        # FFN

        ffn_output = self.ffn.forward(X)

        X = self.norm3.forward(X + ffn_output)



        return X





class LayerNorm:

    """

    层归一化



    LayerNorm(x) = γ * (x - μ) / √(σ² + ε) + β

    """



    def __init__(self, d_model, eps=1e-6):

        self.gamma = np.ones(d_model)

        self.beta = np.zeros(d_model)

        self.eps = eps



    def forward(self, X):

        """前向传播"""

        mean = np.mean(X, axis=-1, keepdims=True)

        var = np.var(X, axis=-1, keepdims=True)

        X_norm = (X - mean) / np.sqrt(var + self.eps)

        return self.gamma * X_norm + self.beta





if __name__ == "__main__":

    np.random.seed(42)



    # 参数

    batch_size = 2

    seq_len = 10

    d_model = 64

    n_heads = 4



    print("=" * 50)

    print("测试Transformer组件")

    print("=" * 50)



    # 测试位置编码

    print("\n1. 位置编码:")

    pos_encoding = PositionalEncoding(d_model, max_len=100)

    pe = pos_encoding.forward(seq_len)

    print(f"   位置编码形状: {pe.shape}")



    # 测试多头注意力

    print("\n2. 多头注意力:")

    X = np.random.randn(batch_size, seq_len, d_model)

    mha = MultiHeadAttention(d_model, n_heads)

    output, attn_weights = mha.forward(X, X, X)

    print(f"   输入形状: {X.shape}")

    print(f"   输出形状: {output.shape}")

    print(f"   注意力权重形状: {attn_weights.shape}")



    # 测试编码器层

    print("\n3. 编码器层:")

    encoder_layer = TransformerEncoderLayer(d_model, n_heads)

    encoder_output = encoder_layer.forward(X)

    print(f"   编码器输出形状: {encoder_output.shape}")



    # 测试解码器层

    print("\n4. 解码器层:")

    decoder_layer = TransformerDecoderLayer(d_model, n_heads)

    decoder_output = decoder_layer.forward(X, encoder_output)

    print(f"   解码器输出形状: {decoder_output.shape}")



    # 测试完整前向传播

    print("\n5. 完整前向传播示例:")

    src_seq = np.random.randn(batch_size, seq_len, d_model)

    tgt_seq = np.random.randn(batch_size, seq_len // 2, d_model)



    encoder_out = encoder_layer.forward(src_seq)

    decoder_out = decoder_layer.forward(tgt_seq, encoder_out)

    print(f"   源序列编码输出: {encoder_out.shape}")

    print(f"   目标序列解码输出: {decoder_out.shape}")

