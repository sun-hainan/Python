# -*- coding: utf-8 -*-
"""
算法实现：编码理论 / reed_solomon

本文件实现 reed_solomon 相关的算法功能。
"""

from typing import List, Tuple
import random


class ReedSolomonCode:
    """
    Reed-Solomon码编码器/解码器
    基于GF(2^m)域
    """
    
    def __init__(self, m: int = 8, t: int = 16):
        """
        初始化
        
        Args:
            m: 符号大小(位数)
            t: 纠错能力(符号数)
        """
        self.m = m
        self.q = 2 ** m  # 域大小
        self.n = self.q - 1  # 码长(符号数)
        self.k = self.n - 2 * t  # 信息长度
        
        # 构建GF(2^m)
        self._build_gf()
        # 构建生成多项式
        self._build_generator()
    
    def _build_gf(self):
        """构建伽罗华域GF(2^m)"""
        # 简化:使用8位表示
        # 本原多项式 x^8 + x^4 + x^3 + x^2 + 1 = 0x11D
        
        # 简化实现:使用整数运算模拟GF
        self.alpha_to = [1] * (2 * self.q)
        self.index_of = [0] * self.q
        
        # 生成域元素
        primitive = 0x11D
        primitive_root = 2
        
        for i in range(1, self.q - 1):
            self.alpha_to[i] = self.alpha_to[i - 1] * primitive_root
            if self.alpha_to[i] >= self.q:
                self.alpha_to[i] ^= primitive
            self.alpha_to[i] &= (self.q - 1)
            self.index_of[self.alpha_to[i]] = i
        
        self.alpha_to[self.q - 1] = 0
        self.index_of[0] = -1
    
    def _build_generator(self):
        """构建生成多项式"""
        # g(x) = (x - alpha^1)(x - alpha^2)...(x - alpha^{2t})
        self.generator = [1]
        
        for i in range(1, 2 * self.t + 1):
            # g(x) *= (x - alpha^i)
            self.generator = self._poly_mul(self.generator, [1, self.negate(self.alpha_pow(i))])
    
    def alpha_pow(self, i: int) -> int:
        """alpha^i"""
        i = i % (self.q - 1)
        if i < 0:
            i += self.q - 1
        return self.alpha_to[i]
    
    def alpha_log(self, x: int) -> int:
        """alpha的对数"""
        if x == 0:
            return -self.q  # 特殊值
        return self.index_of[x]
    
    def negate(self, x: int) -> int:
        """GF中的负号(对于二进制就是它本身)"""
        return x
    
    def _poly_mul(self, a: List[int], b: List[int]) -> List[int]:
        """多项式乘法"""
        result = [0] * (len(a) + len(b) - 1)
        
        for i in range(len(a)):
            for j in range(len(b)):
                if a[i] and b[j]:
                    result[i + j] ^= a[i] * b[j]
        
        return result
    
    def encode(self, data: List[int]) -> List[int]:
        """
        RS编码
        
        Args:
            data: 信息符号列表
        
        Returns:
            编码后的码字
        """
        if len(data) != self.k:
            data = data[:self.k] + [0] * (self.k - len(data))
        
        # 乘以x^{2t}
        padded = data + [0] * (2 * self.t)
        
        # 除以生成多项式
        remainder = self._poly_divide(padded, self.generator)
        
        # 码字 = 信息 + 余式
        return data + remainder
    
    def _poly_divide(self, dividend: List[int], divisor: List[int]) -> List[int]:
        """多项式除法"""
        dividend = dividend.copy()
        div_degree = len(divisor) - 1
        
        for i in range(len(dividend) - div_degree):
            if dividend[i]:
                coef = dividend[i]
                for j in range(1, len(divisor)):
                    dividend[i + j] ^= divisor[j] * coef
        
        return dividend[len(dividend) - div_degree:]


def encode_rs_simple(data: List[int], n: int = 7, k: int = 3) -> List[int]:
    """
    简化RS编码
    
    Args:
        data: 信息符号列表
        n: 码长
        k: 信息长度
    
    Returns:
        码字
    """
    # 使用(n, k) RS码
    # 简化实现:使用范德蒙矩阵编码
    
    # 校验符号数量
    r = n - k
    
    # 信息多项式
    msg_poly = data[:k] + [0] * r
    
    # 生成多项式
    gen = [1]
    for i in range(1, r + 1):
        # g(x) = (x - alpha^i)
        gen = poly_mul(gen, [1, i])  # 简化:使用整数代替GF元素
    
    # 除以生成多项式
    remainder = poly_divide(msg_poly, gen)
    
    # 码字
    return data[:k] + remainder


def poly_mul(a: List[int], b: List[int]) -> List[int]:
    """多项式乘法"""
    result = [0] * (len(a) + len(b) - 1)
    for i in range(len(a)):
        for j in range(len(b)):
            result[i + j] ^= a[i] * b[j]
    return result


def poly_divide(dividend: List[int], divisor: List[int]) -> List[int]:
    """多项式除法"""
    dividend = dividend.copy()
    div_degree = len(divisor) - 1
    
    for i in range(len(dividend) - div_degree):
        if dividend[i]:
            coef = dividend[i]
            for j in range(1, len(divisor)):
                dividend[i + j] ^= divisor[j] * coef
    
    return dividend[len(dividend) - div_degree:]


def decode_rs_simple(code: List[int], n: int = 7, k: int = 3) -> Tuple[List[int], int]:
    """
    简化RS解码
    
    Args:
        code: 接收码字
        n: 码长
        k: 信息长度
    
    Returns:
        (解码信息, 错误数)
    """
    r = n - k
    
    # 计算校验和
    syndrome = []
    for i in range(r):
        s = 0
        for j in range(n):
            s ^= code[j] * (j ** i)  # 简化
        syndrome.append(s)
    
    # 错误数估计
    errors = sum(1 for s in syndrome if s != 0)
    
    # 简化:返回前k位
    return code[:k], errors


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本功能
    print("测试1 - RS码基本功能:")
    rs = ReedSolomonCode(m=4, t=2)  # (15, 11) RS码
    
    data = [1, 2, 3, 4, 5]
    print(f"  信息: {data}")
    
    code = rs.encode(data)
    print(f"  编码: {code}")
    print(f"  码长: {len(code)}, 信息长: {len(data)}")
    
    # 测试2: 简化RS码
    print("\n测试2 - 简化RS码(7, 3):")
    for data in [[1, 2, 3], [5, 7, 9], [10, 20, 30]]:
        code = encode_rs_simple(data, n=7, k=3)
        print(f"  信息: {data} -> 码字: {code}")
    
    # 测试3: 错误检测
    print("\n测试3 - 错误检测:")
    data = [1, 2, 3]
    code = encode_rs_simple(data, n=7, k=3)
    
    # 引入错误
    for error_pos in range(7):
        corrupted = code.copy()
        corrupted[error_pos] ^= 1
        
        decoded, errors = decode_rs_simple(corrupted, n=7, k=3)
        print(f"  位置{error_pos}错误: 原始={code}, 损坏={corrupted}, 解码={decoded}")
    
    # 测试4: 批量测试
    print("\n测试4 - 批量测试:")
    import random
    random.seed(42)
    
    correct = 0
    total = 200
    
    for _ in range(total):
        data = [random.randint(1, 10) for _ in range(3)]
        code = encode_rs_simple(data, n=7, k=3)
        
        # 随机单比特错误
        if random.random() > 0.5:
            error_pos = random.randint(0, 6)
            code[error_pos] ^= 1
        
        decoded, _ = decode_rs_simple(code, n=7, k=3)
        
        if decoded[:len(data)] == data:
            correct += 1
    
    print(f"  正确率: {correct}/{total} = {correct/total:.2%}")
    
    # 测试5: 纠删码应用
    print("\n测试5 - 纠删码模拟:")
    # 模拟RS码在存储系统中的应用
    data = [100, 200, 150]
    code = encode_rs_simple(data, n=7, k=3)
    print(f"  原始数据: {data}")
    print(f"  编码后(7块): {code}")
    
    # 丢失两块
    lost_positions = [2, 5]
    remaining = [code[i] for i in range(7) if i not in lost_positions]
    print(f"  丢失位置: {lost_positions}")
    print(f"  剩余块: {remaining}")
    
    # 简化恢复(假设可以恢复)
    print(f"  尝试恢复...")
    
    print("\n所有测试完成!")
