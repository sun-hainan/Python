# -*- coding: utf-8 -*-

"""

算法实现：联邦学习 / 09_fl_communication_compression



本文件实现 09_fl_communication_compression 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict





class TopkSparsification:

    """

    Top-k稀疏化压缩器



    原理:只保留绝对值最大的k个元素,其余置零



    优点:简单高效,压缩比可控

    缺点:可能丢失重要信息,需要调整k值

    """



    def __init__(self, sparsity_ratio: float = 0.01):

        """

        初始化Top-k稀疏化器



        Args:

            sparsity_ratio: 稀疏度比例,即保留元素比例

        """

        self.sparsity_ratio = sparsity_ratio

        self.name = f"Top-{int(sparsity_ratio * 100)}%"



    def compress(self, gradient: np.ndarray) -> Tuple[np.ndarray, Dict]:

        """

        稀疏化压缩



        Args:

            gradient: 原始梯度向量



        Returns:

            (压缩后的梯度, 元数据)

            元数据包含:

            - indices: 保留元素的索引

            - original_norm: 原始梯度的L2范数

            - compressed_norm: 压缩后梯度的L2范数

        """

        n_elements = len(gradient)

        k = max(1, int(n_elements * self.sparsity_ratio))



        original_norm = np.linalg.norm(gradient)



        # 找出绝对值最大的k个索引

        abs_gradient = np.abs(gradient)

        topk_indices = np.argsort(abs_gradient)[-k:]



        # 创建稀疏向量

        compressed = np.zeros_like(gradient)

        compressed[topk_indices] = gradient[topk_indices]



        compressed_norm = np.linalg.norm(compressed)



        metadata = {

            "indices": topk_indices,

            "k": k,

            "original_norm": original_norm,

            "compressed_norm": compressed_norm,

            "compression_ratio": 1.0 - k / n_elements

        }



        return compressed, metadata



    def decompress(self, compressed: np.ndarray, metadata: Dict) -> np.ndarray:

        """

        解压缩(稀疏化不需要特殊解压,直接返回)



        Args:

            compressed: 压缩后的梯度

            metadata: 元数据



        Returns:

            原始梯度

        """

        return compressed





class SketchCompressor:

    """

    Sketch压缩器 - Count Sketch实现



    Sketch将高维向量映射到低维计数器,

    用于估计梯度的频域信息。



    原理:

    - 使用多个哈希函数将元素映射到sketch行

    - 每行维护计数的符号版本

    - 通过中位数或均值恢复估计



    用途:检测梯度中的主导元素,识别重要更新

    """



    def __init__(self, sketch_dim: int = 100, n_hashes: int = 4):

        """

        初始化Sketch压缩器



        Args:

            sketch_dim: Sketch维度(行数)

            n_hashes: 哈希函数数量

        """

        self.sketch_dim = sketch_dim

        self.n_hashes = n_hashes

        self.name = f"Sketch({sketch_dim}x{n_hashes})"



        # 模拟哈希函数(实际需要密码学哈希)

        np.random.seed(42)

        self.hash_seeds = np.random.randint(0, 2**31, size=n_hashes)



    def _hash_function(self, index: int, seed: int) -> int:

        """

        模拟哈希函数



        Args:

            index: 元素索引

            seed: 随机种子



        Returns:

            哈希值(目标bucket索引)

        """

        # 简化的哈希:使用线性同余生成

        return (index * 1103515245 + seed) % self.sketch_dim



    def _sign_function(self, index: int, seed: int) -> int:

        """

        模拟符号函数



        Args:

            index: 元素索引

            seed: 随机种子



        Returns:

            +1或-1

        """

        return 1 if ((index * 12345 + seed) % 2 == 0) else -1



    def compress(self, gradient: np.ndarray) -> Tuple[np.ndarray, Dict]:

        """

        Sketch压缩



        Args:

            gradient: 原始梯度



        Returns:

            (sketch矩阵, 元数据)

        """

        n = len(gradient)

        original_norm = np.linalg.norm(gradient)



        # 初始化sketch矩阵: (n_hashes, sketch_dim)

        sketch = np.zeros((self.n_hashes, self.sketch_dim))



        # 填充sketch

        for h in range(self.n_hashes):

            for i in range(n):

                bucket = self._hash_function(i, self.hash_seeds[h])

                sign = self._sign_function(i, self.hash_seeds[h])

                sketch[h, bucket] += sign * gradient[i]



        metadata = {

            "n_hashes": self.n_hashes,

            "sketch_dim": self.sketch_dim,

            "original_norm": original_norm

        }



        return sketch, metadata



    def decompress(self, sketch: np.ndarray, metadata: Dict) -> np.ndarray:

        """

        从Sketch恢复梯度估计



        使用简单的反哈希过程(实际更复杂)



        Args:

            sketch: Sketch矩阵

            metadata: 元数据



        Returns:

            恢复的梯度估计

        """

        n = metadata.get("n", len(self._recover_vector_length(sketch)))

        recovered = np.zeros(n)



        # 简化的恢复:对每个sketch行进行反投影

        for h in range(self.n_hashes):

            for i in range(n):

                bucket = self._hash_function(i, self.hash_seeds[h])

                sign = self._sign_function(i, self.hash_seeds[h])

                recovered[i] += sign * sketch[h, bucket] / self.n_hashes



        return recovered



    def _recover_vector_length(self, sketch: np.ndarray) -> int:

        """从sketch推断原始向量长度"""

        return self.sketch_dim * 10  # 简化估计





class DitheringCompressor:

    """

    抖动量化(Dithering)压缩器



    原理:在量化前添加随机抖动,减少量化误差



    步骤:

    1. 在梯度上添加均匀分布的噪声

    2. 将实数值映射到有限的量化级别

    3. 接收端通过期望还原近似值



    优点:无偏估计,理论保证

    """



    def __init__(self, n_levels: int = 16):

        """

        初始化抖动量化器



        Args:

            n_levels: 量化级别数

        """

        self.n_levels = n_levels

        self.name = f"Dithering({n_levels})"



    def compress(self, gradient: np.ndarray) -> Tuple[np.ndarray, Dict]:

        """

        抖动量化压缩



        Args:

            gradient: 原始梯度



        Returns:

            (量化后的梯度, 元数据)

        """

        # 计算梯度范围

        max_val = np.max(np.abs(gradient))

        if max_val < 1e-10:

            return gradient.copy(), {"zero": True}



        # 归一化到[0, 1]

        normalized = gradient / max_val



        # 生成抖动

        dither = np.random.uniform(-0.5, 0.5, gradient.shape)



        # 添加抖动并量化

        noisy = normalized + dither / self.n_levels

        quantized = np.round(noisy * self.n_levels) / self.n_levels



        # 反归一化

        compressed = quantized * max_val



        metadata = {

            "max_val": max_val,

            "n_levels": self.n_levels,

            "original_norm": np.linalg.norm(gradient),

            "quantized_norm": np.linalg.norm(compressed)

        }



        return compressed, metadata



    def decompress(self, compressed: np.ndarray, metadata: Dict) -> np.ndarray:

        """解压缩"""

        return compressed





class ErrorFeedbackCompressor:

    """

    误差反馈压缩器



    原理:累积压缩带来的误差,在下一轮补偿



    e_t = x_t - compress(x_t)  # 累积误差

    x_{t+1} = compress(x_t + e_t)  # 将误差加回



    这使得压缩是无偏的(long-term)

    """



    def __init__(self, base_compressor):

        """

        初始化误差反馈压缩器



        Args:

            base_compressor: 基础压缩器(TopkSparsification等)

        """

        self.compressor = base_compressor

        self.error = None

        self.name = f"EF-{base_compressor.name}"



    def compress(

        self,

        gradient: np.ndarray,

        accumulate_error: bool = True

    ) -> Tuple[np.ndarray, Dict]:

        """

        带误差反馈的压缩



        Args:

            gradient: 原始梯度

            accumulate_error: 是否累积误差



        Returns:

            (压缩后的梯度, 元数据)

        """

        # 如果有累积误差,将其加回当前梯度

        if self.error is not None and accumulate_error:

            gradient = gradient + self.error



        # 执行压缩

        compressed, metadata = self.compressor.compress(gradient)



        # 计算新的误差

        self.error = gradient - compressed

        metadata["error_norm"] = np.linalg.norm(self.error)



        return compressed, metadata



    def decompress(self, compressed: np.ndarray, metadata: Dict) -> np.ndarray:

        """解压缩"""

        return compressed





def compressed_federated_round(

    global_params: np.ndarray,

    client_data_list: List[Tuple[np.ndarray, np.ndarray]],

    client_weights: List[float],

    local_epochs: int,

    learning_rate: float,

    compressor,

    error_feedback: bool = False

) -> np.ndarray:

    """

    压缩联邦学习一轮



    Args:

        global_params: 当前全局模型参数

        client_data_list: 各客户端数据

        client_weights: 各客户端权重

        local_epochs: 本地训练轮数

        learning_rate: 学习率

        compressor: 压缩器实例

        error_feedback: 是否使用误差反馈



    Returns:

        聚合后的全局模型参数

    """

    n_clients = len(client_data_list)



    # 本地训练

    client_updates = []

    for data, labels in client_data_list:

        local_params = global_params.copy()

        n_samples = len(labels)



        for _ in range(local_epochs):

            predictions = data @ local_params

            errors = predictions - labels

            gradients = (1.0 / n_samples) * (data.T @ errors)

            local_params = local_params - learning_rate * gradients



        update = local_params - global_params

        client_updates.append(update)



    # 压缩并聚合

    total_weight = sum(client_weights)

    normalized_weights = [w / total_weight for w in client_weights]



    aggregated = np.zeros_like(global_params)



    for update, weight in zip(client_updates, normalized_weights):

        # 压缩

        if error_feedback:

            compressed, meta = compressor.compress(update, accumulate_error=True)

        else:

            compressed, meta = compressor.compress(update)



        aggregated += weight * compressed



    return global_params + aggregated





def run_compressed_fl(

    n_clients: int,

    model_dim: int,

    n_rounds: int,

    local_epochs: int,

    learning_rate: float,

    compressor_type: str = "topk",

    error_feedback: bool = False,

    data_per_client: int = 100,

    test_size: int = 500,

    seed: int = 42

) -> Dict:

    """

    运行压缩联邦学习



    Args:

        n_clients: 客户端数量

        model_dim: 模型参数维度

        n_rounds: 联邦通信轮数

        local_epochs: 每轮本地训练epoch数

        learning_rate: 学习率

        compressor_type: 压缩器类型,"topk","sketch","dithering"

        error_feedback: 是否使用误差反馈

        data_per_client: 每客户端数据量

        test_size: 测试集大小

        seed: 随机种子



    Returns:

        训练结果字典

    """

    np.random.seed(seed)



    w_true = np.random.randn(model_dim) * 0.5



    client_data_list = []

    client_weights = []



    for i in range(n_clients):

        noise_scale = 0.1 + 0.2 * (i / n_clients)

        X = np.random.randn(data_per_client, model_dim)

        y = X @ w_true + np.random.randn(data_per_client) * noise_scale

        client_data_list.append((X, y))

        client_weights.append(float(data_per_client))



    X_test = np.random.randn(test_size, model_dim)

    y_test = X_test @ w_true + np.random.randn(test_size) * 0.1



    global_params = np.random.randn(model_dim) * np.sqrt(2.0 / model_dim)



    # 创建压缩器

    if compressor_type == "topk":

        compressor = TopkSparsification(sparsity_ratio=0.1)

        if error_feedback:

            compressor = ErrorFeedbackCompressor(compressor)

    elif compressor_type == "sketch":

        compressor = SketchCompressor(sketch_dim=50, n_hashes=4)

    else:

        compressor = DitheringCompressor(n_levels=16)



    history = {"rounds": [], "test_mse": []}



    print(f"压缩FL: {compressor.name}, 误差反馈={error_feedback}")



    for round_idx in range(n_rounds):

        global_params = compressed_federated_round(

            global_params, client_data_list, client_weights,

            local_epochs, learning_rate, compressor, error_feedback

        )



        predictions = X_test @ global_params

        mse = np.mean((predictions - y_test) ** 2)



        history["rounds"].append(round_idx + 1)

        history["test_mse"].append(mse)



        if (round_idx + 1) % 5 == 0 or round_idx == 0:

            print(f"轮次 {round_idx + 1}/{n_rounds} | MSE: {mse:.6f}")



    return {"final_params": global_params, "history": history}





if __name__ == "__main__":

    print("=" * 60)

    print("联邦学习 - 通信压缩演示 (Top-k, Sketch, Dithering)")

    print("=" * 60)



    # 测试Top-k压缩

    print("\n--- Top-k 稀疏化 (10%) ---")

    result = run_compressed_fl(

        n_clients=5,

        model_dim=50,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        compressor_type="topk",

        error_feedback=False,

        data_per_client=200,

        test_size=500,

        seed=42

    )

    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")



    # 测试带误差反馈的Top-k

    print("\n--- Top-k + 误差反馈 ---")

    result = run_compressed_fl(

        n_clients=5,

        model_dim=50,

        n_rounds=20,

        local_epochs=5,

        learning_rate=0.1,

        compressor_type="topk",

        error_feedback=True,

        data_per_client=200,

        test_size=500,

        seed=42

    )

    print(f"最终MSE: {result['history']['test_mse'][-1]:.6f}")



    print("\n" + "=" * 60)

    print("训练完成!")

    print("=" * 60)

