# -*- coding: utf-8 -*-
"""
算法实现：14_信息论 / shannon_fano

本文件实现 shannon_fano 相关的算法功能。
"""

from typing import Dict, List, Tuple
from collections import Counter
import math


def shannon_fano_table(symbols: List[str], freqs: List[int]) -> Dict[str, str]:
    """
    构建香农-范诺编码表

    参数：
        symbols: 符号列表
        freqs: 对应频率/概率列表

    返回：字典 {符号: 编码}
    """
    # 按频率降序排序
    pairs = sorted(zip(symbols, freqs), key=lambda x: -x[1])
    symbols_sorted = [p[0] for p in pairs]
    freqs_sorted = [p[1] for p in pairs]

    def build_codes(symbols_list: List[str], freqs_list: List[int], prefix: str) -> Dict[str, str]:
        """递归构建编码"""
        if len(symbols_list) <= 1:
            return {symbols_list[0]: prefix if symbols_list else ""}

        # 计算总概率
        total = sum(freqs_list)

        # 找到最佳分割点，使得两边概率和尽可能相等
        best_split = 0
        min_diff = float('inf')
        cumulative = 0

        for i in range(len(freqs_list) - 1):
            cumulative += freqs_list[i]
            left_prob = cumulative / total
            right_prob = 1 - left_prob
            diff = abs(left_prob - right_prob)

            if diff < min_diff:
                min_diff = diff
                best_split = i + 1

        # 递归构建左右两部分的编码
        codes = {}
        left_symbols = symbols_list[:best_split]
        left_freqs = freqs_list[:best_split]
        right_symbols = symbols_list[best_split:]
        right_freqs = freqs_list[best_split:]

        if left_symbols:
            codes.update(build_codes(left_symbols, left_freqs, prefix + "0"))
        if right_symbols:
            codes.update(build_codes(right_symbols, right_freqs, prefix + "1"))

        return codes

    return build_codes(symbols_sorted, freqs_sorted, "")


def encode(text: str) -> Tuple[Dict[str, str], str]:
    """
    编码文本

    返回：(编码表, 编码后的比特串)
    """
    freq = Counter(text)
    symbols = list(freq.keys())
    freqs = [freq[s] for s in symbols]

    code_table = shannon_fano_table(symbols, freqs)

    # 编码
    encoded = "".join(code_table[c] for c in text)

    return code_table, encoded


def decode(encoded: str, code_table: Dict[str, str]) -> str:
    """解码"""
    # 构建反向映射（编码 -> 符号）
    reverse_table = {v: k for k, v in code_table.items()}

    decoded = []
    code = ""
    for bit in encoded:
        code += bit
        if code in reverse_table:
            decoded.append(reverse_table[code])
            code = ""

    return "".join(decoded)


def calculate_avg_length(code_table: Dict[str, str], freq: Counter) -> float:
    """计算平均码长"""
    total = sum(freq.values())
    avg_len = sum(len(code) * count for code, count in freq.items()) / total
    return avg_len


def calculate_entropy(text: str) -> float:
    """计算香农熵"""
    freq = Counter(text)
    total = len(text)
    entropy = 0
    for count in freq.values():
        p = count / total
        entropy -= p * math.log2(p)
    return entropy


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== 香农-范诺编码测试 ===\n")

    # 测试文本
    text = "AAAA BBB CC D"
    print(f"原文: '{text}'")
    print(f"长度: {len(text)}\n")

    # 编码
    code_table, encoded = encode(text)
    print("编码表:")
    for symbol, code in sorted(code_table.items(), key=lambda x: -ord(x[0])):
        print(f"  '{symbol}': {code}")

    print(f"\n编码结果: {encoded}")
    print(f"编码长度: {len(encoded)} bits")

    # 解码验证
    decoded = decode(encoded, code_table)
    print(f"\n解码结果: '{decoded}'")
    print(f"验证: {'✅ 通过' if decoded == text else '❌ 失败'}")

    # 统计指标
    print(f"\n统计:")
    print(f"  原文bit数: {len(text) * 8}")
    print(f"  编码bit数: {len(encoded)}")
    print(f"  压缩比: {len(text) * 8 / len(encoded):.2f}")
    print(f"  香农熵: {calculate_entropy(text):.4f}")
    print(f"  平均码长: {calculate_avg_length(code_table, Counter(text)):.4f}")

    # 效率
    entropy = calculate_entropy(text)
    avg_len = calculate_avg_length(code_table, Counter(text))
    efficiency = entropy / avg_len * 100
    print(f"  编码效率: {efficiency:.2f}%")
