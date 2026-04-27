# -*- coding: utf-8 -*-
"""
算法实现：编码理论 / huffman_coding

本文件实现 huffman_coding 相关的算法功能。
"""

import heapq
from typing import List, Tuple, Dict


class HuffmanNode:
    """哈夫曼树节点"""
    def __init__(self, char: str, freq: int):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None
    
    def __lt__(self, other):
        return self.freq < other.freq


def build_huffman_tree(freq_dict: Dict[str, int]) -> HuffmanNode:
    """
    构建哈夫曼树
    
    Args:
        freq_dict: 字符频率字典
    
    Returns:
        哈夫曼树根节点
    """
    # 创建优先队列
    heap = [HuffmanNode(char, freq) for char, freq in freq_dict.items()]
    heapq.heapify(heap)
    
    while len(heap) > 1:
        # 取出两个最小频率的节点
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        
        # 创建父节点
        parent = HuffmanNode(None, left.freq + right.freq)
        parent.left = left
        parent.right = right
        
        heapq.heappush(heap, parent)
    
    return heap[0] if heap else None


def generate_codes(root: HuffmanNode) -> Dict[str, str]:
    """
    生成哈夫曼编码
    
    Args:
        root: 哈夫曼树根节点
    
    Returns:
        字符到编码的映射
    """
    codes = {}
    
    def traverse(node: HuffmanNode, code: str):
        if node is None:
            return
        
        if node.char is not None:
            codes[node.char] = code if code else '0'
            return
        
        traverse(node.left, code + '0')
        traverse(node.right, code + '1')
    
    traverse(root, '')
    return codes


def huffman_encode(text: str) -> Tuple[str, Dict[str, str]]:
    """
    哈夫曼编码
    
    Args:
        text: 输入文本
    
    Returns:
        (编码后的字符串, 编码表)
    """
    # 统计频率
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    
    # 构建哈夫曼树
    root = build_huffman_tree(freq)
    
    # 生成编码表
    codes = generate_codes(root)
    
    # 编码
    encoded = ''.join(codes[char] for char in text)
    
    return encoded, codes


def huffman_decode(encoded: str, codes: Dict[str, str]) -> str:
    """
    哈夫曼解码
    
    Args:
        encoded: 编码字符串
        codes: 编码表
    
    Returns:
        解码后的文本
    """
    # 反转编码表
    reverse_codes = {v: k for k, v in codes.items()}
    
    decoded = []
    current_code = ''
    
    for bit in encoded:
        current_code += bit
        if current_code in reverse_codes:
            decoded.append(reverse_codes[current_code])
            current_code = ''
    
    return ''.join(decoded)


def calculate_compression_ratio(original: str, encoded: str) -> float:
    """计算压缩比"""
    original_bits = len(original) * 8  # 假设ASCII
    encoded_bits = len(encoded)
    return original_bits / encoded_bits if encoded_bits > 0 else 0


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本编码解码
    print("测试1 - 基本功能:")
    text1 = "abracadabra"
    
    encoded1, codes1 = huffman_encode(text1)
    decoded1 = huffman_decode(encoded1, codes1)
    
    print(f"  原文: {text1}")
    print(f"  编码: {encoded1}")
    print(f"  编码表: {codes1}")
    print(f"  解码: {decoded1}")
    print(f"  正确: {text1 == decoded1}")
    
    # 测试2: 压缩效率
    print("\n测试2 - 压缩效率:")
    texts = [
        "abracadabra",
        "this is an example for huffman encoding",
        "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "the quick brown fox jumps over the lazy dog"
    ]
    
    for text in texts:
        encoded, codes = huffman_encode(text)
        ratio = calculate_compression_ratio(text, encoded)
        entropy = sum(-freq/len(text) * (freq/len(text)).bit_length() 
                      for freq in set(text) for _ in range(text.count(freq)))
        
        print(f"  '{text[:30]}...': 压缩比={ratio:.2f}")
    
    # 测试3: 树结构
    print("\n测试3 - 哈夫曼树结构:")
    freq3 = {'a': 45, 'b': 13, 'c': 12, 'd': 16, 'e': 9, 'f': 5}
    tree3 = build_huffman_tree(freq3)
    codes3 = generate_codes(tree3)
    
    print(f"  频率: {freq3}")
    print(f"  编码: {codes3}")
    
    # 验证最优性
    total_bits = sum(freq3[c] * len(codes3[c]) for c in freq3)
    print(f"  总位数: {total_bits}")
    print(f"  平均码长: {total_bits / sum(freq3.values()):.2f}")
    
    # 测试4: 大文本
    print("\n测试4 - 大文本压缩:")
    import random
    
    random.seed(42)
    large_text = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10000))
    
    encoded_large, codes_large = huffman_encode(large_text)
    ratio_large = calculate_compression_ratio(large_text, encoded_large)
    
    print(f"  原文长度: {len(large_text)}")
    print(f"  编码长度: {len(encoded_large)}")
    print(f"  压缩比: {ratio_large:.2f}")
    
    # 验证解码正确性
    decoded_large = huffman_decode(encoded_large, codes_large)
    print(f"  解码正确: {large_text == decoded_large}")
    
    # 测试5: 边界情况
    print("\n测试5 - 边界情况:")
    for text in ["", "a", "aaa", "abcd"]:
        if text:
            encoded, codes = huffman_encode(text)
            decoded = huffman_decode(encoded, codes)
            print(f"  '{text}' -> 编码='{encoded}', 解码='{decoded}', 正确={text==decoded}")
        else:
            print(f"  '' -> 空字符串")
    
    print("\n所有测试完成!")
