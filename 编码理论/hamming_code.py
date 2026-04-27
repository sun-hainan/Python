# -*- coding: utf-8 -*-
"""
算法实现：编码理论 / hamming_code

本文件实现 hamming_code 相关的算法功能。
"""

from typing import Tuple, List, Optional


class HammingCode:
    """
    汉明码编码器/解码器
    支持(7,4)汉明码和任意2^r-1,2^r-r-1汉明码
    """
    
    def __init__(self, r: int = 3):
        """
        初始化
        
        Args:
            r: 校验位数量,n=2^r-1,k=n-r
        """
        self.r = r
        self.n = 2 ** r - 1
        self.k = self.n - r
        
        # 生成矩阵和校验矩阵
        self._build_matrices()
    
    def _build_matrices(self):
        """构建生成矩阵和校验矩阵"""
        # 对于(7,4)汉明码,校验位在位置0,1,2(2的幂次)
        # 信息位在位置3,4,5,6
        
        # 简化:使用标准汉明码格式
        # 生成矩阵G = [I_k | P]
        # 校验矩阵H = [P^T | I_r]
        
        k = self.k
        r = self.r
        
        # 单位矩阵
        self.G = [[0] * self.n for _ in range(k)]
        self.H = [[0] * self.n for _ in range(r)]
        
        # 构建P矩阵(根据位置映射)
        # 位置i的信息位映射到位置p[i]的校验位
        info_to_code = []
        for i in range(self.n):
            if (i + 1) & i != 0:  # 不是2的幂次
                info_to_code.append(i)
        
        # 构建生成矩阵
        for row in range(k):
            info_pos = row
            code_pos = info_to_code[row]
            self.G[row][code_pos] = 1
        
        # 构建校验矩阵(简化版本)
        # H的每一行对应一个校验位
        for row in range(r):
            parity_pos = (1 << row) - 1  # 2^r - 1 -> 实际位置偏移
            if parity_pos < self.n:
                self.H[row][parity_pos] = 1
        
        # 填充H的其他部分
        for col in range(self.n):
            if col not in [(1 << i) - 1 for i in range(r)]:
                # 非校验位位置
                for row in range(r):
                    bit_pos = (1 << row) - 1
                    if bit_pos < self.n and col != bit_pos:
                        # 计算校验关系
                        val = 1 if ((col + 1) >> (row + 1)) & 1 else 0
                        if bit_pos < self.n:
                            self.H[row][col] = val
    
    def encode(self, data: List[int]) -> List[int]:
        """
        编码信息位
        
        Args:
            data: k位信息序列
        
        Returns:
            n位编码序列
        """
        if len(data) != self.k:
            raise ValueError(f"需要{self.k}位数据,得到{len(data)}位")
        
        # 编码:c = data * G
        code = [0] * self.n
        
        for i in range(self.k):
            if data[i] == 1:
                for j in range(self.n):
                    code[j] ^= self.G[i][j]
        
        return code
    
    def decode(self, received: List[int]) -> Tuple[List[int], int]:
        """
        解码并纠错
        
        Args:
            received: 接收到的n位序列
        
        Returns:
            (解码后的信息位, 纠错状态: 0=无错, 正数=错误位置, -1=不可纠错)
        """
        if len(received) != self.n:
            raise ValueError(f"需要{self.n}位,得到{len(received)}位")
        
        # 计算 syndromes = received * H^T
        syndrome = [0] * self.r
        for row in range(self.r):
            for j in range(self.n):
                syndrome[row] ^= (received[j] & self.H[row][j])
        
        # 检查是否有错误
        error_pos = -1
        for i in range(self.r):
            if syndrome[i]:
                error_pos = sum(syndrome[i] << i for i in range(self.r))
                break
        
        if error_pos == 0 or error_pos == -1:
            # 无错误或不可检测
            pass
        else:
            # 纠错
            error_pos -= 1  # 转换为0索引
            if 0 <= error_pos < self.n:
                received[error_pos] ^= 1
        
        # 提取信息位
        info_to_code = []
        for i in range(self.n):
            if (i + 1) & i != 0:  # 不是2的幂次
                info_to_code.append(i)
        
        decoded = [received[pos] for pos in info_to_code[:self.k]]
        
        return decoded, error_pos if error_pos > 0 else 0
    
    def encode_simple(self, data: int) -> int:
        """
        简单编码(4位->7位)
        
        Args:
            data: 4位整数
        
        Returns:
            7位编码整数
        """
        # 提取位
        b0 = (data >> 0) & 1
        b1 = (data >> 1) & 1
        b2 = (data >> 2) & 1
        b3 = (data >> 3) & 1
        
        # 计算校验位
        p1 = b0 ^ b2 ^ b3  # 位置0
        p2 = b0 ^ b1 ^ b3  # 位置1
        p4 = b1 ^ b2 ^ b3  # 位置2
        
        # 组成7位码字
        # 位置: 0 1 2 3 4 5 6
        # 位:   p1 p2 b0 p4 b1 b2 b3
        code = 0
        code |= (p1 << 0)
        code |= (p2 << 1)
        code |= (b0 << 2)
        code |= (p4 << 3)
        code |= (b1 << 4)
        code |= (b2 << 5)
        code |= (b3 << 6)
        
        return code
    
    def decode_simple(self, code: int) -> Tuple[int, int]:
        """
        简单解码(7位->4位)
        
        Args:
            code: 7位码字整数
        
        Returns:
            (解码后的4位数据, 错误位置,0表示无错)
        """
        # 提取位
        bits = [(code >> i) & 1 for i in range(7)]
        p1, p2, b0, p4, b1, b2, b3 = bits
        
        # 计算校验
        s1 = p1 ^ b0 ^ b2 ^ b3
        s2 = p2 ^ b0 ^ b1 ^ b3
        s4 = p4 ^ b1 ^ b2 ^ b3
        
        # 错误位置(1-7)
        error_pos = s1 * 1 + s2 * 2 + s4 * 4
        
        if error_pos > 0:
            # 翻转错误位
            bit_idx = error_pos - 1
            bits[bit_idx] ^= 1
            p1, p2, b0, p4, b1, b2, b3 = bits
        
        # 重组数据
        data = (b3 << 3) | (b2 << 2) | (b1 << 1) | b0
        
        return data, error_pos


def encode_hamming_74(data: int) -> int:
    """
    (7,4)汉明码编码
    
    Args:
        data: 4位数据(0-15)
    
    Returns:
        7位码字
    """
    ham = HammingCode(3)
    return ham.encode_simple(data)


def decode_hamming_74(code: int) -> Tuple[int, int]:
    """
    (7,4)汉明码解码
    
    Args:
        code: 7位码字
    
    Returns:
        (解码后的4位数据, 错误位置)
    """
    ham = HammingCode(3)
    return ham.decode_simple(code)


# 测试代码
if __name__ == "__main__":
    # 测试1: 基本编码解码
    print("测试1 - 基本编码解码:")
    for data in range(16):
        code = encode_hamming_74(data)
        decoded, error = decode_hamming_74(code)
        print(f"  数据{data:04b} -> 码字{code:07b} -> 解码{data:04b}, 错误={error}")
    
    # 测试2: 错误检测和纠正
    print("\n测试2 - 单比特错误:")
    code = encode_hamming_74(0b1010)
    print(f"  原始码字: {code:07b}")
    
    # 引入单比特错误
    for i in range(7):
        corrupted = code ^ (1 << i)
        decoded, error = decode_hamming_74(corrupted)
        print(f"  第{i}位翻转: {corrupted:07b} -> {decoded:04b}, 错误位置={error}")
    
    # 测试3: 多比特错误
    print("\n测试3 - 双比特错误:")
    code = encode_hamming_74(0b1100)
    corrupted = code ^ 0b0000101  # 翻转两位
    decoded, error = decode_hamming_74(corrupted)
    print(f"  原始: {code:07b}")
    print(f"  损坏: {corrupted:07b}")
    print(f"  解码: {decoded:04b}, 错误={error} (注意:双比特错误可能无法正确解码)")
    
    # 测试4: 汉明距离
    print("\n测试4 - 汉明距离验证:")
    codes = [encode_hamming_74(d) for d in range(16)]
    
    min_dist = float('inf')
    for i in range(16):
        for j in range(i + 1, 16):
            dist = bin(codes[i] ^ codes[j]).count('1')
            min_dist = min(min_dist, dist)
    
    print(f"  最小汉明距离: {min_dist} (应为3)")
    
    # 测试5: 批量测试
    print("\n测试5 - 批量测试(随机错误):")
    import random
    random.seed(42)
    
    correct = 0
    total = 1000
    
    for _ in range(total):
        data = random.randint(0, 15)
        code = encode_hamming_74(data)
        
        # 随机单比特翻转
        if random.random() > 0.5:
            error_pos = random.randint(0, 6)
            code ^= (1 << error_pos)
        
        decoded, _ = decode_hamming_74(code)
        
        if decoded == data:
            correct += 1
    
    print(f"  正确率: {correct}/{total} = {correct/total:.2%}")
    
    print("\n所有测试完成!")
