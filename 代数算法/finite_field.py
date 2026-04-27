# -*- coding: utf-8 -*-
"""
算法实现：代数算法 / finite_field

本文件实现 finite_field 相关的算法功能。
"""

class GF256:
    """
    有限域 GF(2^8) 实现
    用于AES加密等密码学算法
    """
    
    IRREDUCIBLE_POLY = 0x11B
    
    @staticmethod
    def add(a: int, b: int) -> int:
        """有限域加法（异或操作）"""
        return a ^ b
    
    @staticmethod
    def multiply(a: int, b: int) -> int:
        """有限域乘法 - 俄罗斯农民乘法"""
        result = 0
        while b > 0:
            if b & 1:
                result ^= a
            a <<= 1
            if a & 0x100:
                a ^= GF256.IRREDUCIBLE_POLY
            b >>= 1
        return result & 0xFF
    
    @staticmethod
    def inverse(a: int) -> int:
        """有限域乘法逆元"""
        if a == 0:
            raise ValueError("零没有逆元")
        t, new_t = 0, 1
        r, new_r = GF256.IRREDUCIBLE_POLY, a
        
        while new_r != 0:
            quotient = r // new_r
            t, new_t = new_t, t ^ GF256.multiply(quotient, new_t)
            r, new_r = new_r, r ^ GF256.multiply(quotient, new_r)
        
        return t & 0xFF

if __name__ == "__main__":
    print("=== GF(2^8) 有限域运算测试 ===")
    
    a, b = 0x57, 0x83
    sum_result = GF256.add(a, b)
    print(f"加法: 0x{a:02X} + 0x{b:02X} = 0x{sum_result:02X}")
    
    prod = GF256.multiply(a, b)
    print(f"乘法: 0x{a:02X} * 0x{b:02X} = 0x{prod:02X} (预期: 0xC1)")
    
    a = 0x57
    inv = GF256.inverse(a)
    prod = GF256.multiply(a, inv)
    print(f"逆元: inv(0x{a:02X}) = 0x{inv:02X}")
    print(f"验证: 0x{a:02X} * 0x{inv:02X} = 0x{prod:02X} (应为0x01)")
