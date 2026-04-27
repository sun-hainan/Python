# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / bert_gpt_simplified



本文件实现 bert_gpt_simplified 相关的算法功能。

"""



import numpy as np





class TokenEmbedding:

    """

    词嵌入层



    参数:

        vocab_size: 词汇表大小

        d_model: 嵌入维度

    """



    def __init__(self, vocab_size, d_model):

        self.embedding = np.random.randn(vocab_size, d_model) * 0.02



    def forward(self, token_ids):

        """前向传播"""

        return self.embedding[token_ids]





class PositionalEmbedding:

    """

    位置嵌入



    参数:

        max_len: 最大序列长度

        d_model: 模型维度

    """



    def __init__(self, max_len, d_model):

        self.pe = self._create_encoding(max_len, d_model)



    def _create_encoding(self, max_len, d_model):

        """创建位置编码"""

        pe = np.zeros((max_len, d_model))

        position = np.arange(0, max_len).reshape(-1, 1)

        div_term = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))



        pe[:, 0::2] = np.sin(position * div_term)

        pe[:, 1::2] = np.cos(position * div_term)

        return pe



    def forward(self, seq_len):

        """获取位置编码"""

        return self.pe[:seq_len]





class SimplifiedBERT:

    """

    简化版BERT



    核心组件:

    1. 词嵌入 + 位置嵌入

    2. 多层Transformer编码器

    3. [CLS] token的输出作为句子表示

    4. MLM head（预测被掩码的token）



    参数:

        vocab_size: 词汇表大小

        d_model: 模型维度

        n_heads: 注意力头数

        n_layers: 编码器层数

        d_ff: 前馈网络维度

    """



    def __init__(self, vocab_size, d_model=256, n_heads=4, n_layers=4, d_ff=1024):

        self.vocab_size = vocab_size

        self.d_model = d_model

        self.n_heads = n_heads

        self.n_layers = n_layers



        # 嵌入层

        self.token_embed = TokenEmbedding(vocab_size, d_model)

        self.pos_embed = PositionalEmbedding(512, d_model)

        self.embed_dropout = 0.1



        # 编码器层

        self.encoder_layers = []

        for _ in range(n_layers):

            self.encoder_layers.append({

                'attention': self._create_attention_layer(),

                'ffn': self._create_ffn_layer(),

                'norm1': self._create_norm_layer(),

                'norm2': self._create_norm_layer()

            })



        # 输出层

        self.mlm_head = np.random.randn(d_model, vocab_size) * np.sqrt(2.0 / d_model)

        self.mlm_bias = np.zeros(vocab_size)



    def _create_attention_layer(self):

        """创建注意力层"""

        d_k = self.d_model // self.n_heads

        return {

            'W_Q': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'W_K': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'W_V': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'W_O': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'd_k': d_k,

            'n_heads': self.n_heads

        }



    def _create_ffn_layer(self):

        """创建FFN层"""

        return {

            'W1': np.random.randn(self.d_model, self.d_ff) * np.sqrt(2.0 / self.d_model),

            'b1': np.zeros(self.d_ff),

            'W2': np.random.randn(self.d_ff, self.d_model) * np.sqrt(2.0 / self.d_ff),

            'b2': np.zeros(self.d_model)

        }



    def _create_norm_layer(self):

        """创建LayerNorm"""

        return {

            'gamma': np.ones(self.d_model),

            'beta': np.zeros(self.d_model),

            'eps': 1e-6

        }



    def _multi_head_attention(self, Q, K, V, attention_params):

        """多头注意力"""

        W_Q = attention_params['W_Q']

        W_K = attention_params['W_K']

        W_V = attention_params['W_V']

        W_O = attention_params['W_O']

        d_k = attention_params['d_k']

        n_heads = attention_params['n_heads']



        batch_size, seq_len, d_model = Q.shape



        # 线性变换

        Q = Q @ W_Q

        K = K @ W_K

        V = V @ W_V



        # 分割多头

        Q = Q.reshape(batch_size, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

        K = K.reshape(batch_size, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

        V = V.reshape(batch_size, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)



        # 缩放点积注意力

        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_k)

        attn_weights = self._softmax(scores)

        attn_output = attn_weights @ V



        # 合并多头

        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, d_model)

        output = attn_output @ W_O



        return output, attn_weights



    def _layer_norm(self, X, norm_params):

        """层归一化"""

        mean = np.mean(X, axis=-1, keepdims=True)

        var = np.var(X, axis=-1, keepdims=True)

        X_norm = (X - mean) / np.sqrt(var + norm_params['eps'])

        return norm_params['gamma'] * X_norm + norm_params['beta']



    def _feed_forward(self, X, ffn_params):

        """前馈网络"""

        Z1 = X @ ffn_params['W1'] + ffn_params['b1']

        A1 = np.maximum(0, Z1)  # ReLU

        Z2 = A1 @ ffn_params['W2'] + ffn_params['b2']

        return Z2



    def _softmax(self, X):

        """Softmax"""

        exp_X = np.exp(X - np.max(X, axis=-1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=-1, keepdims=True)



    def forward(self, token_ids):

        """

        前向传播



        参数:

            token_ids: 输入token ID (batch, seq_len)



        返回:

            output: MLM输出 logits

            hidden_states: 所有层的隐藏状态

        """

        batch_size, seq_len = token_ids.shape



        # 词嵌入 + 位置嵌入

        token_emb = self.token_embed.forward(token_ids)

        pos_emb = self.pos_embed.forward(seq_len)

        X = token_emb + pos_emb



        # 编码器层

        hidden_states = [X]

        for layer in self.encoder_layers:

            # Multi-Head Attention + Add & Norm

            attn_out, _ = self._multi_head_attention(X, X, X, layer['attention'])

            X = self._layer_norm(X + attn_out, layer['norm1'])



            # FFN + Add & Norm

            ffn_out = self._feed_forward(X, layer['ffn'])

            X = self._layer_norm(X + ffn_out, layer['norm2'])



            hidden_states.append(X)



        # [CLS] token输出（序列表示）

        cls_output = X[:, 0]  # (batch, d_model)



        # MLM Head

        logits = X @ self.mlm_head + self.mlm_bias  # (batch, seq_len, vocab_size)



        return logits, cls_output, hidden_states



    def mlm_loss(self, token_ids, masked_positions, masked_labels):

        """

        计算MLM损失



        参数:

            token_ids: 原始token序列

            masked_positions: 被掩码的位置

            masked_labels: 被掩码位置的真实token

        """

        logits, _, _ = self.forward(token_ids)



        # 只取被掩码位置的预测

        masked_logits = logits[0, masked_positions]  # 简化：只取第一个样本



        # Cross-entropy损失

        loss = -np.mean(masked_labels * np.log(self._softmax(masked_logits) + 1e-10))

        return loss





class SimplifiedGPT:

    """

    简化版GPT



    与BERT的区别:

    - 使用因果掩码（单向注意力）

    - 解码器结构（不是编码器-解码器）

    - 语言建模任务（预测下一个token）

    """



    def __init__(self, vocab_size, d_model=256, n_heads=4, n_layers=4, d_ff=1024):

        self.vocab_size = vocab_size

        self.d_model = d_model

        self.n_heads = n_heads

        self.n_layers = n_layers



        # 嵌入层

        self.token_embed = TokenEmbedding(vocab_size, d_model)

        self.pos_embed = PositionalEmbedding(512, d_model)



        # 解码器层（带因果掩码）

        self.decoder_layers = []

        for _ in range(n_layers):

            self.decoder_layers.append({

                'attention': self._create_attention_layer(),

                'cross_attention': self._create_attention_layer(),

                'ffn': self._create_ffn_layer(),

                'norm1': self._create_norm_layer(),

                'norm2': self._create_norm_layer(),

                'norm3': self._create_norm_layer()

            })



        # LM Head

        self.lm_head = np.random.randn(d_model, vocab_size) * np.sqrt(2.0 / d_model)



    def _create_attention_layer(self):

        """创建注意力层"""

        d_k = self.d_model // self.n_heads

        return {

            'W_Q': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'W_K': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'W_V': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'W_O': np.random.randn(self.d_model, self.d_model) * np.sqrt(2.0 / self.d_model),

            'd_k': d_k,

            'n_heads': self.n_heads

        }



    def _create_ffn_layer(self):

        """创建FFN层"""

        return {

            'W1': np.random.randn(self.d_model, d_ff) * np.sqrt(2.0 / self.d_model),

            'b1': np.zeros(d_ff),

            'W2': np.random.randn(d_ff, self.d_model) * np.sqrt(2.0 / self.d_ff),

            'b2': np.zeros(self.d_model)

        }



    def _create_norm_layer(self):

        """创建LayerNorm"""

        return {

            'gamma': np.ones(self.d_model),

            'beta': np.zeros(self.d_model),

            'eps': 1e-6

        }



    def _causal_mask(self, seq_len):

        """创建因果掩码（未来不能看到过去）"""

        mask = np.triu(np.ones((seq_len, seq_len)), k=1).astype(bool)

        return mask



    def forward(self, token_ids):

        """

        前向传播



        参数:

            token_ids: 输入token ID (batch, seq_len)

        """

        batch_size, seq_len = token_ids.shape



        # 嵌入

        token_emb = self.token_embed.forward(token_ids)

        pos_emb = self.pos_embed.forward(seq_len)

        X = token_emb + pos_emb



        # 因果掩码

        causal_mask = self._causal_mask(seq_len)



        # 解码器层

        for layer in self.decoder_layers:

            # Masked Self-Attention

            attn_out, _ = self._masked_attention(X, layer['attention'], causal_mask)

            X = self._layer_norm(X + attn_out, layer['norm1'])



            # FFN

            ffn_out = self._feed_forward(X, layer['ffn'])

            X = self._layer_norm(X + ffn_out, layer['norm3'])



        # LM Head

        logits = X @ self.lm_head



        return logits



    def _masked_attention(self, Q, K, V, attention_params, mask):

        """带掩码的注意力"""

        # 简化为双向注意力（实际GPT需要单向）

        return self._multi_head_attention(Q, K, V, attention_params)



    def _multi_head_attention(self, Q, K, V, attention_params):

        """多头注意力"""

        W_Q = attention_params['W_Q']

        W_K = attention_params['W_K']

        W_V = attention_params['W_V']

        W_O = attention_params['W_O']

        d_k = attention_params['d_k']

        n_heads = attention_params['n_heads']



        batch_size, seq_len, d_model = Q.shape



        Q = Q @ W_Q

        K = K @ W_K

        V = V @ W_V



        Q = Q.reshape(batch_size, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

        K = K.reshape(batch_size, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)

        V = V.reshape(batch_size, seq_len, n_heads, d_k).transpose(0, 2, 1, 3)



        scores = Q @ K.transpose(0, 1, 3, 2) / np.sqrt(d_k)

        attn_weights = self._softmax(scores)

        attn_output = attn_weights @ V



        attn_output = attn_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, d_model)

        output = attn_output @ W_O



        return output, attn_weights



    def _layer_norm(self, X, norm_params):

        """层归一化"""

        mean = np.mean(X, axis=-1, keepdims=True)

        var = np.var(X, axis=-1, keepdims=True)

        X_norm = (X - mean) / np.sqrt(var + norm_params['eps'])

        return norm_params['gamma'] * X_norm + norm_params['beta']



    def _feed_forward(self, X, ffn_params):

        """前馈网络"""

        Z1 = X @ ffn_params['W1'] + ffn_params['b1']

        A1 = np.maximum(0, Z1)

        Z2 = A1 @ ffn_params['W2'] + ffn_params['b2']

        return Z2



    def _softmax(self, X):

        """Softmax"""

        exp_X = np.exp(X - np.max(X, axis=-1, keepdims=True))

        return exp_X / np.sum(exp_X, axis=-1, keepdims=True)





# 全局变量供SimplifiedGPT使用

d_ff = 1024





if __name__ == "__main__":

    np.random.seed(42)



    vocab_size = 1000

    seq_len = 20



    print("=" * 50)

    print("测试简化版BERT")

    print("=" * 50)



    # 测试BERT

    bert = SimplifiedBERT(vocab_size, d_model=128, n_heads=4, n_layers=2)



    # 模拟输入

    token_ids = np.random.randint(0, vocab_size, size=(2, seq_len))

    masked_positions = np.array([3, 7, 11])

    masked_labels = np.zeros((len(masked_positions), vocab_size))

    for i, pos in enumerate(masked_positions):

        masked_labels[i, token_ids[0, pos]] = 1.0



    # 前向传播

    logits, cls_output, hidden_states = bert.forward(token_ids)

    print(f"\n输入形状: {token_ids.shape}")

    print(f"MLM输出形状: {logits.shape}")

    print(f"[CLS]输出形状: {cls_output.shape}")

    print(f"隐藏状态数量: {len(hidden_states)}")



    # MLM损失

    loss = bert.mlm_loss(token_ids, masked_positions, masked_labels)

    print(f"MLM损失: {loss:.4f}")



    print("\n" + "=" * 50)

    print("测试简化版GPT")

    print("=" * 50)



    # 测试GPT

    gpt = SimplifiedGPT(vocab_size, d_model=128, n_heads=4, n_layers=2)

    gpt_logits = gpt.forward(token_ids)

    print(f"\nGPT输出形状: {gpt_logits.shape}")



    # 语言建模损失

    # 预测下一个token

    lm_logits = gpt_logits[:, :-1]  # (batch, seq_len-1, vocab_size)

    next_tokens = token_ids[:, 1:]  # (batch, seq_len-1)

    lm_loss = -np.mean(np.take_along_axis(

        gpt._softmax(lm_logits),

        next_tokens.reshape(2, -1, 1),

        axis=2

    ).squeeze(-1))

    print(f"语言建模损失: {lm_loss:.4f}")

