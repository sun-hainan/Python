# -*- coding: utf-8 -*-
"""
算法实现：08_位运算 / crc_checksum

本文件实现 crc_checksum 相关的算法功能。
"""

class CRC32:
    """CRC-32校验器，使用标准以太网多项式 0xEDB88320"""

    # 标准CRC-32多项式（反转形式）
    POLYNOMIAL = 0xEDB88320

    def __init__(self):
        # 预计算256项查找表
        self.table = self._build_table()

    def _build_table(self) -> list[int]:
        """预计算CRC32查表（抗漏洞攻击的固定实现）"""
        table = [0] * 256
        for i in range(256):
            crc = i
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ self.POLYNOMIAL
                else:
                    crc >>= 1
            table[i] = crc
        return table

    def update(self, data: bytes) -> int:
        """计算data的CRC-32值（无初始化寄存器）"""
        crc = 0xFFFFFFFF  # 初始寄存器值
        for byte in data:
            idx = (crc ^ byte) & 0xFF
            crc = (crc >> 8) ^ self.table[idx]
        return crc ^ 0xFFFFFFFF  # 最终翻转

    def checksum(self, data: bytes) -> int:
        """计算并返回16进制字符串"""
        return self.update(data)

    def verify(self, data: bytes, expected: int) -> bool:
        """校验数据完整性"""
        return self.update(data) == expected


def crc32_naive(data: bytes) -> int:
    """朴素实现（不预计算表）供学习"""
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF


if __name__ == "__main__":
    import binascii

    crc = CRC32()

    # 标准测试向量
    test_cases = [
        (b"", 0x00000000),
        (b"\x00", 0xD4EF1155),
        (b"123456789", 0x9BE3E7A3),
        (b"Hello, World!", 0xA384F08E),
    ]

    print("=== CRC-32 测试向量验证 ===")
    for data, expected in test_cases:
        result = crc.update(data)
        status = "✓" if result == expected else "✗"
        print(f"{status} CRC32({data!r}) = 0x{result:08X} (期望 0x{expected:08X})")

    # 朴素实现对比
    print("\n=== 朴素实现对比 ===")
    data = b"123456789"
    fast = crc.update(data)
    slow = crc32_naive(data)
    print(f"快速查表: 0x{fast:08X}")
    print(f"朴素实现: 0x{slow:08X}")
    print(f"一致: {fast == slow}")

    # 文件校验模拟
    print("\n=== 数据校验模拟 ===")
    payload = b"JSON payload with sensitive data"
    chk = crc.checksum(payload)
    print(f"数据: {payload}")
    print(f"CRC32: 0x{chk:08X}")
    print(f"传输后校验: {crc.verify(payload, chk)}")
    print(f"篡改后校验: {crc.verify(payload + b"\x00", chk)}")
