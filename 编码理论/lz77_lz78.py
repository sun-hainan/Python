# -*- coding: utf-8 -*-
"""
算法实现：编码理论 / lz77_lz78

本文件实现 lz77_lz78 相关的算法功能。
"""

from typing import List, Tuple, Optional


def lz77_compress(text: str, window_size: int = 1000) -> List[Tuple[int, int, str]]:
    """
    LZ77压缩算法
    
    Args:
        text: 输入文本
        window_size: 窗口大小
    
    Returns:
        压缩后的三元组列表 [(offset, length, next_char), ...]
    """
    result = []
    i = 0
    
    while i < len(text):
        # 在窗口中搜索最长匹配
        best_offset = 0
        best_length = 0
        
        start = max(0, i - window_size)
        
        for j in range(start, i):
            # 计算从j开始能匹配多长
            length = 0
            while i + length < len(text) and text[j + length] == text[i + length]:
                length += 1
                if length > best_length:
                    best_length = length
                    best_offset = i - j
        
        # 添加三元组
        if best_length > 0:
            next_char = text[i + best_length] if i + best_length < len(text) else ''
            result.append((best_offset, best_length, next_char))
            i += best_length + 1
        else:
            result.append((0, 0, text[i]))
            i += 1
    
    return result


def lz77_decompress(compressed: List[Tuple[int, int, str]]) -> str:
    """
    LZ77解压
    
    Args:
        compressed: 压缩后的三元组列表
    
    Returns:
        解压后的文本
    """
    result = []
    
    for offset, length, char in compressed:
        if length > 0:
            # 回溯复制
            start = len(result) - offset
            for i in range(length):
                result.append(result[start + i])
        
        if char:
            result.append(char)
    
    return ''.join(result)


def lz78_compress(text: str) -> List[Tuple[int, str]]:
    """
    LZ78压缩算法
    
    Args:
        text: 输入文本
    
    Returns:
        压缩后的对列表 [(dict_index, next_char), ...]
    """
    dictionary = {'': 0}
    next_index = 1
    result = []
    
    i = 0
    while i < len(text):
        # 找最长的已字典条目
        longest_match = ''
        match_index = 0
        
        for j in range(i, len(text)):
            prefix = text[i:j + 1]
            
            if prefix in dictionary:
                longest_match = prefix
                match_index = dictionary[prefix]
            else:
                break
        
        if longest_match:
            # 使用字典条目
            next_char = text[i + len(longest_match)] if i + len(longest_match) < len(text) else ''
            result.append((match_index, next_char))
            
            # 添加新条目
            new_phrase = longest_match + (next_char if next_char else '')
            if new_phrase not in dictionary:
                dictionary[new_phrase] = next_index
                next_index += 1
            
            i += len(longest_match) + (1 if next_char else 0)
        else:
            # 单字符
            result.append((0, text[i]))
            if text[i] not in dictionary:
                dictionary[text[i]] = next_index
                next_index += 1
            i += 1
    
    return result


def lz78_decompress(compressed: List[Tuple[int, str]]) -> str:
    """
    LZ78解压
    
    Args:
        compressed: 压缩后的对列表
    
    Returns:
        解压后的文本
    """
    dictionary = {0: ''}
    next_index = 1
    result = []
    
    for index, char in compressed:
        phrase = dictionary[index] + char
        result.append(phrase)
        dictionary[next_index] = phrase
        next_index += 1
    
    return ''.join(result)


# 测试代码
if __name__ == "__main__":
    # 测试1: LZ77基本功能
    print("测试1 - LZ77压缩:")
    text1 = "abracadabracadabra"
    
    compressed1 = lz77_compress(text1, window_size=10)
    decompressed1 = lz77_decompress(compressed1)
    
    print(f"  原文: {text1}")
    print(f"  压缩: {compressed1}")
    print(f"  解压: {decompressed1}")
    print(f"  正确: {text1 == decompressed1}")
    
    # 测试2: LZ78基本功能
    print("\n测试2 - LZ78压缩:")
    text2 = "ababababababababa"
    
    compressed2 = lz78_compress(text2)
    decompressed2 = lz78_decompress(compressed2)
    
    print(f"  原文: {text2}")
    print(f"  压缩: {compressed2}")
    print(f"  解压: {decompressed2}")
    print(f"  正确: {text2 == decompressed2}")
    
    # 测试3: 压缩比
    print("\n测试3 - 压缩效率:")
    texts = [
        "aaaaaaabbbbbbbbcccccc",
        "abcdefghijklmnopqrstuvwxyz",
        "abababababababababababababab",
        "the quick brown fox jumps over the lazy dog"
    ]
    
    for text in texts:
        lz77_comp = lz77_compress(text)
        lz78_comp = lz78_compress(text)
        
        lz77_size = len(lz77_comp) * 3  # 每个三元组3个值
        lz78_size = len(lz78_comp) * 2  # 每个对2个值
        
        print(f"  '{text[:20]}...':")
        print(f"    原文: {len(text)}字节")
        print(f"    LZ77: {lz77_size}字节")
        print(f"    LZ78: {lz78_size}字节")
    
    # 测试4: 实际应用
    print("\n测试4 - 实际文本:")
    text4 = """
    Python is a programming language that lets you work quickly 
    and integrate systems more effectively. Python is a popular 
    programming language. It was created by Guido van Rossum, 
    and released in 1991.
    """
    
    lz77_comp = lz77_compress(text4)
    lz78_comp = lz78_compress(text4)
    
    print(f"  原文长度: {len(text4)}")
    print(f"  LZ77压缩后: {len(lz77_comp)}个条目")
    print(f"  LZ78压缩后: {len(lz78_comp)}个条目")
    
    # 验证解压
    dec77 = lz77_decompress(lz77_comp)
    dec78 = lz78_decompress(lz78_comp)
    
    print(f"  LZ77解压正确: {text4 == dec77}")
    print(f"  LZ78解压正确: {text4 == dec78}")
    
    # 测试5: 重复模式
    print("\n测试5 - 重复模式:")
    pattern = "abc" * 100
    comp = lz77_compress(pattern)
    
    print(f"  'abc'重复100次:")
    print(f"  压缩后条目数: {len(comp)}")
    print(f"  压缩比: {len(pattern) / (len(comp) * 3):.1f}x")
    
    print("\n所有测试完成!")
