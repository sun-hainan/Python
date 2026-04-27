# -*- coding: utf-8 -*-
"""
算法实现：14_信息论 / lz78_compression

本文件实现 lz78_compression 相关的算法功能。
"""

from typing import Dict, List, Tuple


def lz78_compress(text: str) -> List[Tuple[int, str]]:
    """
    LZ78 压缩

    返回：(字典索引, 字符) 元组列表
    """
    dictionary = {"" : 0}
    next_index = 1
    result = []
    phrase = ""

    for char in text:
        phrase_with_char = phrase + char
        if phrase_with_char in dictionary:
            phrase = phrase_with_char
        else:
            # 输出 phrase 的字典索引（空字符串索引为0）
            index = dictionary.get(phrase, 0)
            result.append((index, char))

            # 添加新短语到字典
            dictionary[phrase_with_char] = next_index
            next_index += 1
            phrase = ""

    # 处理最后一个短语
    if phrase:
        index = dictionary.get(phrase, 0)
        result.append((index, ""))

    return result


def lz78_decompress(compressed: List[Tuple[int, str]]) -> str:
    """
    LZ78 解压

    参数：压缩后的 (索引, 字符) 列表
    返回：原始文本
    """
    dictionary = {0: ""}
    next_index = 1
    result = []

    for index, char in compressed:
        if index == 0:
            phrase = char
        else:
            phrase = dictionary[index] + char

        result.append(phrase)
        dictionary[next_index] = phrase
        next_index += 1

    return "".join(result)


def calculate_compression_ratio(original: str, compressed: List[Tuple[int, str]]) -> float:
    """计算压缩比"""
    original_bits = len(original) * 8
    # 每个输出用 (index_bits + char_bits) 表示
    # 假设用4位表示索引（最多16个字典项），8位表示字符
    index_bits = 4
    char_bits = 8
    compressed_bits = len(compressed) * (index_bits + char_bits)
    return original_bits / compressed_bits


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== LZ78 压缩算法测试 ===\n")

    # 测试文本
    texts = [
        "ABABABAB",
        "AAAAAAAA",
        "HELLO WORLD HELLO",
        "THE RAIN IN SPAIN",
        "0123456789"
    ]

    for text in texts:
        print(f"--- 测试: '{text}' ---")

        # 压缩
        compressed = lz78_compress(text)
        print(f"压缩后: {compressed}")

        # 解压验证
        decompressed = lz78_decompress(compressed)
        print(f"解压结果: '{decompressed}'")
        print(f"验证: {'✅ 通过' if decompressed == text else '❌ 失败'}")

        # 压缩比
        ratio = calculate_compression_ratio(text, compressed)
        print(f"压缩比: {ratio:.2f}")
        print()

    # 详细演示
    print("=== 详细演示 ===")
    text = "ABABABABA"
    print(f"原文: '{text}'")

    compressed = lz78_compress(text)
    print(f"\n压缩过程:")
    dictionary = {"" : 0}
    next_index = 1
    phrase = ""

    print("步骤 | 读入 | 当前短语 | 字典查找 | 输出 | 字典更新")
    print("-" * 60)

    for i, char in enumerate(text):
        phrase_with_char = phrase + char
        if phrase_with_char in dictionary:
            phrase = phrase_with_char
            print(f"{i+1:2d}  |  '{char}'  |  '{phrase}'  |  在字典中  |  -  |  -")
        else:
            index = dictionary.get(phrase, 0)
            print(f"{i+1:2d}  |  '{char}'  |  '{phrase_with_char}'  |  不在字典  |  ({index},'{char}')  |  '{phrase_with_char}'={next_index}")
            dictionary[phrase_with_char] = next_index
            next_index += 1
            phrase = ""

    print(f"\n最终编码: {compressed}")
    print(f"字典大小: {next_index}")

    # 解压
    decompressed = lz78_decompress(compressed)
    print(f"\n解压结果: '{decompressed}'")
