# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / deep_compression



本文件实现 deep_compression 相关的算法功能。

"""



import numpy as np

import torch

import torch.nn as nn

import torch.nn.functional as F

import copy





class DeepCompressor:

    """

    深度压缩器：整合剪枝、量化和霍夫曼编码

    """



    def __init__(self, model, device='cpu'):

        """

        参数:

            model: 待压缩的模型

            device: 计算设备

        """

        self.model = copy.deepcopy(model)

        self.original_model = copy.deepcopy(model)

        self.device = device

        self.pruned_masks = {}

        self.quantized_weights = {}

        self.codebooks = {}

        self.encodings = {}



    def prune(self, sparsity=0.5, method='magnitude'):

        """

        权重剪枝



        参数:

            sparsity: 剪枝比例（设置为0表示保留的比例）

            method: 剪枝方法 ('magnitude', 'random')

        """

        print(f"开始剪枝 (sparsity={sparsity}, method={method})...")



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.cpu().numpy()



            if method == 'magnitude':

                # 幅度剪枝：去除绝对值最小的权重

                threshold = np.percentile(np.abs(weight), sparsity * 100)

                mask = np.abs(weight) > threshold

            else:

                # 随机剪枝

                mask = np.random.rand(*weight.shape) > sparsity



            mask_tensor = torch.from_numpy(mask).float().to(self.device)

            param.data *= mask_tensor



            # 记录mask用于后续恢复

            self.pruned_masks[name] = mask_tensor



        print("剪枝完成")



    def quantize(self, num_bits=8, method='kmeans'):

        """

        权重量化



        参数:

            num_bits: 量化位数

            method: 量化方法 ('kmeans', 'linear')

        """

        print(f"开始量化 (num_bits={num_bits}, method={method})...")



        n_levels = 2 ** num_bits

        self.quantized_weights = {}

        self.codebooks = {}



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.cpu().numpy()

            mask = self.pruned_masks.get(name, torch.ones_like(param)).cpu().numpy()

            weight_masked = weight * mask



            if method == 'kmeans':

                # K-Means量化

                unique_vals = np.unique(weight_masked[mask > 0])

                if len(unique_vals) <= n_levels:

                    # 权重种类数少于量化级别，不需要量化

                    self.quantized_weights[name] = torch.from_numpy(weight).to(self.device)

                    self.codebooks[name] = None

                    continue



                # K-Means聚类

                from sklearn.cluster import KMeans



                kmeans = KMeans(n_clusters=n_levels, random_state=42, n_init=3)

                kmeans.fit(weight_masked.reshape(-1, 1))



                # 用聚类中心替代原始值

                quantized = kmeans.cluster_centers_[kmeans.labels_].reshape(weight.shape)

                quantized = torch.from_numpy(quantized).float().to(self.device)



                self.quantized_weights[name] = quantized

                self.codebooks[name] = {

                    'centers': kmeans.cluster_centers_,

                    'labels': kmeans.labels_

                }



            else:

                # 线性量化

                w_min, w_max = weight_masked.min(), weight_masked.max()

                if w_max == w_min:

                    quantized = torch.zeros_like(param)

                else:

                    # 映射到[0, 2^num_bits-1]再映射回[w_min, w_max]

                    scale = (w_max - w_min) / (n_levels - 1)

                    quantized = torch.round((param - w_min) / scale) * scale + w_min



                self.quantized_weights[name] = quantized

                self.codebooks[name] = {'min': w_min, 'max': w_max, 'scale': scale}



            # 应用量化权重

            param.data.copy_(self.quantized_weights[name])



        print("量化完成")



    def huffman_encode(self):

        """

        霍夫曼编码



        对量化后的权重进行霍夫曼编码以进一步压缩

        """

        print("开始霍夫曼编码...")



        import heapq

        from collections import defaultdict



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.cpu().numpy()



            # 计算频率

            freq = defaultdict(int)

            for val in weight.flatten():

                freq[val] += 1



            # 构建霍夫曼树

            heap = [[wt, [val, ""]] for val, wt in freq.items()]

            heapq.heapify(heap)



            while len(heap) > 1:

                lo, hi = heapq.heappop(heap), heapq.heappop(heap)

                for pair in lo[1:]:

                    pair[1] = '0' + pair[1]

                for pair in hi[1:]:

                    pair[1] = '1' + pair[1]

                heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])



            # 生成编码表

            encoding = {}

            for val, code in heap[0][1:]:

                encoding[val] = code



            self.encodings[name] = {

                'code_table': encoding,

                'frequency': dict(freq)

            }



        print("霍夫曼编码完成")



    def get_compression_ratio(self):

        """

        计算压缩比



        返回:

            ratio: 压缩比

        """

        original_size = sum(p.numel() for p in self.original_model.parameters())

        compressed_size = 0



        for name in self.pruned_masks:

            # 非零权重数量

            mask = self.pruned_masks[name].cpu().numpy()

            nonzero_count = np.sum(mask)



            # 量化后的位数

            if self.codebooks[name] is not None and 'centers' in self.codebooks[name]:

                compressed_size += nonzero_count * 8  # 假设用8位存储聚类中心索引

            else:

                compressed_size += nonzero_count * 32  # 32位浮点数



        if compressed_size == 0:

            compressed_size = original_size * 0.5  # 估计值



        return original_size / compressed_size





class PruningScheduler:

    """

    渐进式剪枝调度器



    逐步增加剪枝率，避免一次性大幅剪枝导致的剧烈性能下降

    """



    def __init__(self, model, initial_sparsity=0.1, final_sparsity=0.7, epochs=100):

        """

        参数:

            initial_sparsity: 初始剪枝率

            final_sparsity: 最终剪枝率

            epochs: 总训练轮数

        """

        self.model = model

        self.initial_sparsity = initial_sparsity

        self.final_sparsity = final_sparsity

        self.epochs = epochs



    def get_sparsity(self, epoch):

        """

        获取当前epoch的剪枝率



        使用余弦退火调度

        """

        if epoch >= self.epochs:

            return self.final_sparsity



        # 余弦退火

        cos_inner = np.pi * epoch / self.epochs

        sparsity = self.final_sparsity + (self.initial_sparsity - self.final_sparsity) * \

                   (1 + np.cos(cos_inner)) / 2



        return sparsity



    def prune_step(self, epoch, method='magnitude'):

        """

        执行一步剪枝



        参数:

            epoch: 当前epoch

            method: 剪枝方法

        """

        sparsity = self.get_sparsity(epoch)



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.cpu().numpy()



            if method == 'magnitude':

                threshold = np.percentile(np.abs(weight), sparsity * 100)

                mask = np.abs(weight) > threshold

            else:

                mask = np.random.rand(*weight.shape) > sparsity



            param.data *= torch.from_numpy(mask).float().to(param.device)





class SparseTraining:

    """

    稀疏训练：从头开始训练稀疏网络

    """



    def __init__(self, model, target_sparsity=0.5, device='cpu'):

        self.model = model

        self.target_sparsity = target_sparsity

        self.device = device



    def apply_mask(self):

        """应用稀疏掩码"""

        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            # 动态计算掩码

            weight = param.data

            threshold = torch.quantile(torch.abs(weight), self.target_sparsity)

            mask = (torch.abs(weight) > threshold).float()

            param.data *= mask



    def train_step(self, images, labels, optimizer):

        """稀疏训练步骤"""

        self.model.train()



        # 应用掩码

        self.apply_mask()



        # 前向传播

        outputs = self.model(images)

        loss = F.cross_entropy(outputs, labels)



        # 反向传播

        optimizer.zero_grad()

        loss.backward()

        optimizer.step()



        return loss.item()





if __name__ == "__main__":

    # 定义简单模型

    class SimpleCNN(nn.Module):

        def __init__(self, num_classes=10):

            super().__init__()

            self.conv1 = nn.Conv2d(1, 32, 3, padding=1)

            self.conv2 = nn.Conv2d(32, 64, 3, padding=1)

            self.fc1 = nn.Linear(64 * 7 * 7, 128)

            self.fc2 = nn.Linear(128, num_classes)



        def forward(self, x):

            x = F.relu(F.max_pool2d(self.conv1(x), 2))

            x = F.relu(F.max_pool2d(self.conv2(x), 2))

            x = x.view(x.size(0), -1)

            x = F.relu(self.fc1(x))

            return self.fc2(x)



    device = torch.device("cpu")



    print("=" * 50)

    print("深度压缩全流程测试")

    print("=" * 50)



    # 创建并压缩模型

    model = SimpleCNN(num_classes=10).to(device)



    # 初始化压缩器

    compressor = DeepCompressor(model, device)



    # 1. 剪枝

    compressor.prune(sparsity=0.7, method='magnitude')



    # 2. 量化

    compressor.quantize(num_bits=8, method='kmeans')



    # 3. 霍夫曼编码

    compressor.huffman_encode()



    # 计算压缩比

    ratio = compressor.get_compression_ratio()

    print(f"\n压缩比: {ratio:.2f}x")



    # 测试压缩后模型

    torch.manual_seed(42)

    test_images = torch.rand(4, 1, 28, 28).to(device)

    test_labels = torch.tensor([0, 1, 2, 3]).to(device)



    with torch.no_grad():

        outputs = compressor.model(test_images)

        preds = torch.argmax(outputs, dim=1)

        print(f"压缩后模型预测: {preds.cpu().numpy()}")



    # 剪枝调度器测试

    print("\n--- 剪枝调度器 ---")

    model2 = SimpleCNN(num_classes=10).to(device)

    scheduler = PruningScheduler(model2, initial_sparsity=0.1, final_sparsity=0.7, epochs=100)



    for epoch in [0, 25, 50, 75, 100]:

        sparsity = scheduler.get_sparsity(epoch)

        print(f"Epoch {epoch}: sparsity={sparsity:.2%}")



    print("\n测试完成！")

