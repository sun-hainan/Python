# -*- coding: utf-8 -*-

"""

算法实现：模型压缩完整版 / huffman_coding



本文件实现 huffman_coding 相关的算法功能。

"""



import numpy as np

import heapq

from collections import defaultdict

import torch

import torch.nn as nn





class HuffmanNode:

    """霍夫曼树节点"""



    def __init__(self, value, frequency):

        self.value = value

        self.frequency = frequency

        self.left = None

        self.right = None



    def __lt__(self, other):

        return self.frequency < other.frequency





class HuffmanCoder:

    """

    霍夫曼编码器

    """



    def __init__(self):

        self.code_table = {}

        self.reverse_code_table = {}



    def build_tree(self, frequency_dict):

        """

        构建霍夫曼树



        参数:

            frequency_dict: {value: frequency}

        """

        # 创建叶子节点堆

        heap = []

        for value, freq in frequency_dict.items():

            node = HuffmanNode(value, freq)

            heapq.heappush(heap, node)



        # 构建树

        while len(heap) > 1:

            node1 = heapq.heappop(heap)

            node2 = heapq.heappop(heap)



            merged = HuffmanNode(None, node1.frequency + node2.frequency)

            merged.left = node1

            merged.right = node2



            heapq.heappush(heap, merged)



        return heap[0] if heap else None



    def generate_codes(self, node, code=""):

        """

        递归生成编码表



        参数:

            node: 霍夫曼树根节点

            code: 当前编码

        """

        if node is None:

            return



        if node.value is not None:

            self.code_table[node.value] = code

            self.reverse_code_table[code] = node.value

            return



        self.generate_codes(node.left, code + "0")

        self.generate_codes(node.right, code + "1")



    def fit(self, data):

        """

        拟合数据，构建编码表



        参数:

            data: 数据数组

        """

        # 统计频率

        frequency = defaultdict(int)

        for val in data.flatten():

            frequency[val] += 1



        # 构建树

        root = self.build_tree(frequency)



        # 生成编码

        self.generate_codes(root)



        return self.code_table



    def encode(self, data):

        """

        编码数据



        返回:

            encoded: 位字符串

            padding_info: 填充信息

        """

        encoded_bits = []



        for val in data.flatten():

            if val in self.code_table:

                encoded_bits.append(self.code_table[val])

            else:

                # 值不在码表中（应该不会发生）

                encoded_bits.append("1")  # 标记为新值



        # 转换为位字符串

        bit_string = "".join(encoded_bits)



        # 填充到字节边界

        padding = (8 - len(bit_string) % 8) % 8

        bit_string += "0" * padding



        return bit_string, padding



    def decode(self, bit_string, original_shape, padding=0):

        """

        解码数据



        参数:

            bit_string: 位字符串

            original_shape: 原始形状

            padding: 填充位数

        """

        # 移除填充

        if padding > 0:

            bit_string = bit_string[:-padding]



        decoded = []

        current_code = ""



        for bit in bit_string:

            current_code += bit



            if current_code in self.reverse_code_table:

                decoded.append(self.reverse_code_table[current_code])

                current_code = ""



        return np.array(decoded).reshape(original_shape)





class ModelCompressor:

    """

    模型压缩器：整合霍夫曼编码

    """



    def __init__(self, model):

        self.model = model

        self.encoders = {}

        self.metadata = {}



    def compress_weights(self):

        """

        压缩模型权重



        返回:

            compressed_data: 压缩后的数据字典

        """

        compressed = {}



        for name, param in self.model.named_parameters():

            if 'weight' not in name:

                continue



            weight = param.data.cpu().numpy()



            # 创建霍夫曼编码器

            coder = HuffmanCoder()

            code_table = coder.fit(weight)



            # 编码

            bit_string, padding = coder.encode(weight)



            # 存储

            compressed[name] = {

                'bit_string': bit_string,

                'padding': padding,

                'shape': weight.shape,

                'code_table': code_table

            }



            self.encoders[name] = coder



            # 计算压缩率

            original_bits = weight.size * 32  # 假设float32

            compressed_bits = len(bit_string)

            ratio = original_bits / compressed_bits



            self.metadata[name] = {

                'original_size': original_bits,

                'compressed_size': compressed_bits,

                'ratio': ratio

            }



        return compressed



    def decompress_weights(self, compressed_data):

        """

        解压权重



        参数:

            compressed_data: 压缩数据



        返回:

            decompressed: 解压后的权重字典

        """

        decompressed = {}



        for name, data in compressed_data.items():

            coder = self.encoders[name]



            weight = coder.decode(

                data['bit_string'],

                data['shape'],

                data['padding']

            )



            decompressed[name] = torch.from_numpy(weight)



        return decompressed



    def compute_compression_ratio(self):

        """

        计算总压缩比

        """

        total_original = 0

        total_compressed = 0



        for name, meta in self.metadata.items():

            total_original += meta['original_size']

            total_compressed += meta['compressed_size']



        return total_original / total_compressed if total_compressed > 0 else 1.0



    def apply_compressed_weights(self, compressed_data):

        """

        应用压缩后的权重到模型

        """

        decompressed = self.decompress_weights(compressed_data)



        with torch.no_grad():

            for name, weight in decompressed.items():

                for n, param in self.model.named_parameters():

                    if n == name:

                        param.copy_(weight)





class AdaptiveHuffmanCoder:

    """

    自适应霍夫曼编码



    边编码边更新频率表

    """



    def __init__(self):

        self.frequency = defaultdict(int)

        self.coder = HuffmanCoder()

        self.code_table = {}



    def update_frequencies(self, data):

        """更新频率统计"""

        for val in np.unique(data):

            self.frequency[val] += 1



    def encode_stream(self, data):

        """流式编码"""

        encoded = []



        for val in data.flatten():

            # 更新频率

            self.frequency[val] += 1



            # 定期重新构建码表

            if sum(self.frequency.values()) % 1000 == 0:

                self.coder.fit(list(self.frequency.keys()))

                self.code_table = self.coder.code_table



            # 编码

            if val in self.code_table:

                encoded.append(self.code_table[val])

            else:

                encoded.append("0")  # 备用



        return "".join(encoded)



    def decode_stream(self, bit_string, shape):

        """流式解码"""

        decoded = []

        current_code = ""



        for bit in bit_string:

            current_code += bit



            if current_code in self.coder.reverse_code_table:

                decoded.append(self.coder.reverse_code_table[current_code])

                current_code = ""



        return np.array(decoded).reshape(shape)





if __name__ == "__main__":

    import torch.nn as nn

    import torch.nn.functional as F



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



    print("=" * 50)

    print("霍夫曼编码测试")

    print("=" * 50)



    # 简单的霍夫曼编码测试

    print("\n--- 基础霍夫曼编码 ---")



    test_data = np.array([1.0, 2.0, 3.0, 1.0, 2.0, 1.0, 4.0, 1.0, 2.0, 1.0])

    print(f"测试数据: {test_data}")



    coder = HuffmanCoder()

    code_table = coder.fit(test_data)



    print(f"编码表:")

    for val, code in sorted(code_table.items(), key=lambda x: x[1]):

        print(f"  {val}: {code}")



    bit_string, padding = coder.encode(test_data)

    print(f"编码后长度: {len(bit_string)} bits, 填充: {padding}")

    print(f"原始大小: {len(test_data) * 32} bits")

    print(f"压缩比: {len(test_data) * 32 / len(bit_string):.2f}x")



    # 解码验证

    decoded = coder.decode(bit_string, test_data.shape, padding)

    print(f"解码验证: {decoded}")

    print(f"解码正确: {np.allclose(test_data, decoded)}")



    # 模型压缩测试

    print("\n--- 模型压缩 ---")

    model = SimpleCNN(num_classes=10)



    compressor = ModelCompressor(model)

    compressed_data = compressor.compress_weights()



    print("各层压缩统计:")

    for name, meta in compressor.metadata.items():

        print(f"  {name}: 原始={meta['original_size']}bits, "

              f"压缩={meta['compressed_size']}bits, "

              f"比={meta['ratio']:.2f}x")



    total_ratio = compressor.compute_compression_ratio()

    print(f"\n总压缩比: {total_ratio:.2f}x")



    # 验证解压

    print("\n--- 验证解压 ---")

    decompressed = compressor.decompress_weights(compressed_data)



    with torch.no_grad():

        for name, param in model.named_parameters():

            if name in decompressed:

                original = param.data.cpu().numpy()

                restored = decompressed[name].numpy()

                max_error = np.abs(original - restored).max()

                print(f"  {name}: 最大误差={max_error:.2e}")



    print("\n测试完成！")

