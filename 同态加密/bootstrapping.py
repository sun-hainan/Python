# -*- coding: utf-8 -*-
"""
算法实现：同态加密 / bootstrapping

本文件实现 bootstrapping 相关的算法功能。
"""

import random
import numpy as np
from typing import Tuple


class BootstrappableCipher:
    """可自举的简化密文"""

    def __init__(self, noise_bound: float = 1.0):
        """
        参数：
            noise_bound: 噪声上界
        """
        self.noise_bound = noise_bound
        self.threshold = 10.0  # 需要自举的阈值

    def encrypt(self, message: int, key: int) -> dict:
        """
        加密

        返回：密文和噪声
        """
        noise = random.uniform(0, self.noise_bound)
        ciphertext = message + noise * key

        return {
            'ciphertext': ciphertext,
            'noise': abs(noise),
            'key': key
        }

    def decrypt(self, ct: dict) -> int:
        """
        解密

        返回：明文
        """
        c = ct['ciphertext']
        key = ct['key']

        # 简化：取最近的整数
        return round((c % key) / key)

    def is_noisy(self) -> bool:
        """检查是否需要自举"""
        return self.noise_bound > self.threshold

    def refresh(self, ct: dict, evaluation_key: dict) -> dict:
        """
        自举（刷新密文）

        参数：
            ct: 需要刷新的密文
            evaluation_key: 评估密钥

        返回：刷新后的密文
        """
        # 简化：重加密
        key = ct['key']

        # 解密得到明文
        m = self.decrypt(ct)

        # 用新的密钥重新加密
        new_ct = self.encrypt(m, key)

        # 噪声降低
        new_ct['noise'] = self.noise_bound * 0.1  # 大幅降低

        return new_ct


class BootstrappingScheduler:
    """自举调度器"""

    def __init__(self, threshold: float = 5.0):
        """
        参数：
            threshold: 噪声阈值
        """
        self.threshold = threshold

    def should_bootstrap(self, ciphertext: dict) -> bool:
        """
        检查是否需要自举

        返回：是否需要
        """
        noise = ciphertext.get('noise', 0)
        return noise > self.threshold

    def schedule_bootstrapping(self, ciphertexts: list) -> list:
        """
        调度自举

        返回：需要自举的密文列表
        """
        to_bootstrap = []

        for ct in ciphertexts:
            if self.should_bootstrap(ct):
                to_bootstrap.append(ct)

        return to_bootstrap


def bootstrapping_complexity():
    """自举复杂度"""
    print("=== 自举复杂度 ===")
    print()
    print("问题：")
    print("  - 同态计算后噪声累积")
    print("  - 噪声过大会导致解密失败")
    print("  - 自举可以"重置"噪声")
    print()
    print("成本：")
    print("  - 每次自举需要执行解密电路")
    print("  - O(m³) 或更高")
    print("  - 是FHE的主要性能瓶颈")
    print()
    print("优化：")
    print("  - 批处理密文")
    print("  - 减少解密电路深度")
    print("  - 近似解密")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== Bootstrapping测试 ===\n")

    # 创建可自举的密文系统
    bc = BootstrappableCipher(noise_bound=1.0)

    # 加密消息
    key = 100
    message = 42

    ct = bc.encrypt(message, key)

    print(f"消息: {message}")
    print(f"密文噪声: {ct['noise']:.4f}")
    print()

    # 同态操作（模拟）
    print("执行同态操作...")
    ct['ciphertext'] += random.uniform(0, 0.5) * key
    ct['noise'] += 0.2

    print(f"操作后噪声: {ct['noise']:.4f}")
    print()

    # 检查是否需要自举
    if bc.is_noisy():
        print("需要自举！")
        ct_refreshed = bc.refresh(ct, {'eval_key': key})

        print(f"自举后噪声: {ct_refreshed['noise']:.4f}")

        # 解密验证
        m_decrypted = bc.decrypt(ct_refreshed)
        print(f"解密结果: {m_decrypted}")
        print(f"正确: {'✅' if m_decrypted == message else '❌'}")
    else:
        print("噪声可接受")

    print()
    bootstrapping_complexity()

    print()
    print("说明：")
    print("  - Bootstrapping是FHE的关键技术")
    print("  - 显著增加计算开销")
    print("  - 最新方案（如CKKS）尽量减少自举需求")
