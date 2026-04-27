# -*- coding: utf-8 -*-
"""
算法实现：区块链算法 / signature_verification

本文件实现 signature_verification 相关的算法功能。
"""

import hashlib
import hmac
from typing import Tuple, Optional

class ECPoint:
    """椭圆曲线上的点（简化实现）"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
    
    def __add__(self, other):
        if self.x == other.x and self.y == other.y:
            # 倍点
            lam = (3 * self.x * self.x) * pow(2 * self.y, -1, 2**256 - 2**32 - 977)
        else:
            lam = (other.y - self.y) * pow(other.x - self.x, -1, 2**256 - 2**32 - 977)
        
        x3 = (lam * lam - self.x - other.x) % (2**256 - 2**32 - 977)
        y3 = (lam * (self.x - x3) - self.y) % (2**256 - 2**32 - 977)
        return ECPoint(x3, y3)
    
    def __mul__(self, scalar: int):
        result = ECPoint(0, 0)  # 无穷远点
        base = self
        
        while scalar:
            if scalar & 1:
                result = result + base
            base = base + base
            scalar >>= 1
        
        return result

class SignatureVerifier:
    """
    椭圆曲线签名验证
    
    基于secp256k1曲线（比特币使用的曲线）
    """
    
    # 椭圆曲线参数 (secp256k1)
    P = 2**256 - 2**32 - 977  # 素数模
    G = ECPoint(0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
                0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)  # 生成元
    N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141  # 阶
    
    def __init__(self):
        self.curve_order = self.N
    
    def hash_message(self, message: str) -> int:
        """对消息进行哈希"""
        h = hashlib.sha256(message.encode()).digest()
        return int.from_bytes(h, 'big') % self.curve_order
    
    def sign(self, message: str, private_key: int) -> Tuple[int, int]:
        """
        签名（简化实现）
        
        Args:
            message: 消息
            private_key: 私钥
        
        Returns:
            (r, s) 签名
        """
        # 计算消息哈希
        e = self.hash_message(message)
        
        # 生成随机数k
        k = int(hashlib.sha256((str(private_key) + str(e)).encode()).hexdigest(), 16) % self.curve_order
        if k == 0:
            k = 1
        
        # 计算R点
        R = self.G * k
        r = R.x % self.curve_order
        
        if r == 0:
            raise ValueError("签名失败: r=0")
        
        # 计算s
        s = pow(k, -1, self.curve_order) * (e + r * private_key) % self.curve_order
        
        if s == 0:
            raise ValueError("签名失败: s=0")
        
        return (r, s)
    
    def verify(self, message: str, signature: Tuple[int, int], public_key_point: ECPoint) -> bool:
        """
        验证签名
        
        Args:
            message: 消息
            signature: (r, s)
            public_key_point: 公钥点
        
        Returns:
            是否验证通过
        """
        r, s = signature
        
        # 检查r, s范围
        if r < 1 or r >= self.curve_order:
            return False
        if s < 1 or s >= self.curve_order:
            return False
        
        # 计算e = hash(message)
        e = self.hash_message(message)
        
        # 计算w = s^(-1) mod N
        w = pow(s, -1, self.curve_order)
        
        # 计算u1 = e * w mod N, u2 = r * w mod N
        u1 = (e * w) % self.curve_order
        u2 = (r * w) % self.curve_order
        
        # 计算P = u1 * G + u2 * public_key
        P = (self.G * u1) + (public_key_point * u2)
        
        # 验证: r == P.x mod N
        return r == P.x % self.curve_order

def generate_keypair():
    """生成密钥对"""
    # 简化实现：使用随机数
    import secrets
    private_key = int(secrets.token_hex(32), 16) % SignatureVerifier.curve_order
    if private_key < 1:
        private_key = 1
    
    public_key_point = SignatureVerifier.G * private_key
    
    return private_key, public_key_point

if __name__ == "__main__":
    print("=== 椭圆曲线签名验证测试 ===")
    
    verifier = SignatureVerifier()
    
    # 生成密钥对
    private_key, public_key = generate_keypair()
    print(f"私钥: {private_key}")
    print(f"公钥: ({public_key.x}, {public_key.y})")
    
    # 签名
    message = "Hello, Blockchain!"
    r, s = verifier.sign(message, private_key)
    print(f"\n签名:")
    print(f"  r: {r}")
    print(f"  s: {s}")
    
    # 验证
    is_valid = verifier.verify(message, (r, s), public_key)
    print(f"\n验证结果: {'通过' if is_valid else '失败'}")
    
    # 篡改消息测试
    print("\n=== 篡改消息测试 ===")
    tampered_message = "Hello, Blockchain??"
    is_valid_tampered = verifier.verify(tampered_message, (r, s), public_key)
    print(f"篡改消息验证: {'通过' if is_valid_tampered else '失败'} (应为失败)")
    
    # 篡改签名测试
    print("\n=== 篡改签名测试 ===")
    tampered_sig = (r, (s + 1) % SignatureVerifier.curve_order)
    is_valid_sig = verifier.verify(message, tampered_sig, public_key)
    print(f"篡改签名验证: {'通过' if is_valid_sig else '失败'} (应为失败)")
    
    # 使用错误的公钥测试
    print("\n=== 错误公钥测试 ===")
    _, wrong_public_key = generate_keypair()
    is_valid_wrong = verifier.verify(message, (r, s), wrong_public_key)
    print(f"错误公钥验证: {'通过' if is_valid_wrong else '失败'} (应为失败)")
    
    # 多次签名测试
    print("\n=== 批量签名测试 ===")
    messages = ["消息1", "消息2", "消息3", "消息4", "消息5"]
    for msg in messages:
        r, s = verifier.sign(msg, private_key)
        is_valid = verifier.verify(msg, (r, s), public_key)
        print(f"  '{msg}': {'通过' if is_valid else '失败'}")
