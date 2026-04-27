# -*- coding: utf-8 -*-
"""
算法实现：编码理论 / arithmetic_coding

本文件实现 arithmetic_coding 相关的算法功能。
"""

from typing import List, Tuple, Optional
import math


class ArithmeticEncoder:
    """
    自适应算术编码器
    """
    
    def __init__(self, precision: int = 32):
        """
        初始化
        
        Args:
            precision: 精度位数
        """
        self.precision = precision
        self.low = 0
        self.high = (1 << precision) - 1
        self.scale = self.high + 1
        
        # 频率统计
        self.freq = {}
        self.total = 0
    
    def update_model(self, symbol: int):
        """更新频率模型"""
        self.freq[symbol] = self.freq.get(symbol, 0) + 1
        self.total += 1
    
    def get_range(self, symbol: int) -> Tuple[int, int]:
        """
        获取符号的概率区间
        
        Returns:
            (low, high) 相对于total
        """
        low = 0
        for sym, count in sorted(self.freq.items()):
            if sym == symbol:
                return (low, low + count)
            low += count
        
        # 新符号
        return (self.total, self.total + 1)
    
    def encode(self, data: List[int]) -> int:
        """
        算术编码
        
        Args:
            data: 要编码的符号序列
        
        Returns:
            编码后的整数
        """
        self.low = 0
        self.high = (1 << self.precision) - 1
        self.scale = self.high + 1
        
        self.freq = {}
        self.total = 0
        
        pending_bits = 0
        
        for symbol in data:
            # 更新模型
            self.update_model(symbol)
            
            # 获取范围
            symbol_low, symbol_high = self.get_range(symbol)
            
            # 更新区间
            range_size = self.high - self.low + 1
            symbol_range = symbol_high - symbol_low
            
            self.high = self.low + (range_size * symbol_high // self.total) - 1
            self.low = self.low + (range_size * symbol_low // self.total)
            
            # 输出确定位
            while True:
                mid = (self.low + self.high) // 2
                low_mid = self.low
                high_mid = mid
                
                if high_mid < self.low:
                    self.low = self.low
                    self.high = self.high
                    break
                elif low_mid > self.high:
                    self.low = self.low
                    self.high = self.high
                    break
                else:
                    break
        
        # 返回中点
        return (self.low + self.high) // 2


class ArithmeticDecoder:
    """
    算术解码器
    """
    
    def __init__(self, precision: int = 32):
        self.precision = precision
        self.freq = {}
        self.total = 0
    
    def update_model(self, symbol: int):
        """更新频率模型"""
        self.freq[symbol] = self.freq.get(symbol, 0) + 1
        self.total += 1
    
    def get_symbol(self, value: int, total: int) -> Tuple[int, int, int]:
        """根据值找到对应的符号"""
        cumulative = 0
        for sym, count in sorted(self.freq.items()):
            if cumulative + count > value:
                return (sym, cumulative, cumulative + count)
            cumulative += count
        
        # 新符号
        return (cumulative, cumulative, cumulative + 1)
    
    def decode(self, code: int, length: int, scale: int) -> List[int]:
        """
        算术解码
        
        Args:
            code: 编码值
            length: 要解码的符号数
            scale: 缩放因子
        
        Returns:
            解码的符号序列
        """
        self.freq = {}
        self.total = 0
        
        result = []
        low = 0
        high = scale - 1
        
        for _ in range(length):
            # 找符号
            range_size = high - low + 1
            value = (code - low) // (range_size // (self.total + 1)) if self.total > 0 else 0
            
            # 获取符号
            symbol, sym_low, sym_high = self.get_symbol(value, self.total + 1)
            result.append(symbol)
            
            # 更新区间
            high = low + (range_size * sym_high // (self.total + 1)) - 1
            low = low + (range_size * sym_low // (self.total + 1))
            
            # 更新模型
            self.update_model(symbol)
        
        return result


def encode_arithmetic(data: List[int]) -> Tuple[int, int]:
    """
    算术编码便捷函数
    
    Args:
        data: 要编码的数据
    
    Returns:
        (编码值, scale)
    """
    encoder = ArithmeticEncoder()
    code = encoder.encode(data)
    return code, encoder.scale


def decode_arithmetic(code: int, length: int, scale: int) -> List[int]:
    """
    算术解码便捷函数
    
    Args:
        code: 编码值
        length: 数据长度
        scale: 缩放因子
    
    Returns:
        解码数据
    """
    decoder = ArithmeticDecoder()
    return decoder.decode(code, length, scale)


# 简单实现
def simple_encode(data: List[int]) -> float:
    """
    简化算术编码
    使用概率区间
    """
    if not data:
        return 0.0
    
    # 统计频率
    freq = {}
    for x in data:
        freq[x] = freq.get(x, 0) + 1
    
    # 按频率排序
    symbols = sorted(freq.keys())
    n = len(data)
    
    low = 0.0
    high = 1.0
    
    for symbol in data:
        # 计算符号的概率范围
        symbol_low = 0.0
        for sym in symbols:
            if sym == symbol:
                break
            symbol_low += freq[sym] / n
        
        symbol_high = symbol_low + freq[symbol] / n
        
        # 缩小区间
        range_size = high - low
        high = low + range_size * symbol_high
        low = low + range_size * symbol_low
        
        # 更新频率
        freq[symbol] -= 1
        if freq[symbol] == 0:
            del freq[symbol]
        n -= 1
    
    # 返回区间中点
    return (low + high) / 2


def simple_decode(code: float, length: int, alphabet: List[int]) -> List[int]:
    """
    简化算术解码
    """
    if length == 0:
        return []
    
    # 初始频率(假设均匀)
    freq = {x: 1 for x in alphabet}
    n = len(alphabet)
    
    result = []
    low = 0.0
    high = 1.0
    
    for _ in range(length):
        # 计算当前值在哪个区间
        range_size = high - low
        value = (code - low) / range_size
        
        # 找到符号
        cumulative = 0.0
        for symbol in sorted(alphabet):
            prob = freq[symbol] / n
            if value < cumulative + prob:
                result.append(symbol)
                
                # 缩小区间
                symbol_low = cumulative
                symbol_high = cumulative + prob
                
                high = low + range_size * symbol_high
                low = low + range_size * symbol_low
                
                # 更新频率
                freq[symbol] -= 1
                if freq[symbol] == 0:
                    del freq[symbol]
                n -= 1
                break
            
            cumulative += prob
    
    return result


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本功能
    print("测试1 - 简化算术编码:")
    data1 = [1, 2, 1, 2, 3, 1]
    code1 = simple_encode(data1)
    print(f"  数据: {data1}")
    print(f"  编码: {code1:.6f}")
    
    # 解码
    alphabet1 = [1, 2, 3]
    decoded1 = simple_decode(code1, len(data1), alphabet1)
    print(f"  解码: {decoded1}")
    print(f"  正确: {data1 == decoded1}")
    
    # 测试2: 二进制数据
    print("\n测试2 - 二进制数据:")
    import random
    random.seed(42)
    
    data2 = [random.randint(0, 1) for _ in range(20)]
    code2 = simple_encode(data2)
    print(f"  数据: {data2}")
    print(f"  编码: {code2:.6f}")
    
    decoded2 = simple_decode(code2, len(data2), [0, 1])
    print(f"  解码: {decoded2}")
    print(f"  正确: {data2 == decoded2}")
    
    # 测试3: 文本数据
    print("\n测试3 - 文本数据:")
    text = "abracadabra"
    data3 = [ord(c) for c in text]
    alphabet3 = list(set(text))
    
    code3 = simple_encode(data3)
    print(f"  文本: {text}")
    print(f"  编码长度: {code3.bit_length()} bits")
    
    decoded3 = simple_decode(code3, len(data3), alphabet3)
    decoded_text = ''.join(chr(c) for c in decoded3)
    print(f"  解码: {decoded_text}")
    print(f"  正确: {decoded_text == text}")
    
    # 测试4: 压缩效率
    print("\n测试4 - 压缩效率:")
    import sys
    
    for text in ["aaaaa", "abcde", "ababab"]:
        data = [ord(c) for c in text]
        alphabet = list(set(text))
        
        code = simple_encode(data)
        
        original_bits = len(data) * 8  # 假设8位字符
        encoded_bits = code.bit_length()
        
        print(f"  '{text}': 原始{original_bits}bits -> 编码{encoded_bits}bits")
    
    # 测试5: 完整编码器测试
    print("\n测试5 - 完整编码器:")
    data5 = [1, 0, 1, 1, 0, 0, 1]
    code5, scale5 = encode_arithmetic(data5)
    print(f"  数据: {data5}")
    print(f"  编码: {code5}")
    
    decoded5 = decode_arithmetic(code5, len(data5), scale5)
    print(f"  解码: {decoded5}")
    print(f"  正确: {data5 == decoded5}")
    
    print("\n所有测试完成!")
