# -*- coding: utf-8 -*-
"""
算法实现：密码学与安全 / iot_security_auth

本文件实现 iot_security_auth 相关的算法功能。
"""

import hashlib
import hmac
import os
from typing import Tuple, Optional


class IoTIdentityBasedAuth:
    """基于身份的IoT认证协议"""

    def __init__(self, security_param: int = 256):
        """
        初始化认证系统

        参数：
            security_param: 安全参数（位）
        """
        self.k = security_param
        self.master_secret = os.urandom(32)  # 主密钥
        self.device_keys = {}  # 设备私钥存储

    def _hash_to_point(self, identity: str) -> int:
        """
        身份字符串映射到曲线点（简化实现）

        参数：
            identity: 设备身份标识

        返回：曲线点坐标
        """
        # 简化：使用哈希模拟
        h = hashlib.sha256((identity + "salt").encode()).digest()
        return int.from_bytes(h, 'big') % (2**256)

    def generate_device_private_key(self, device_id: str) -> bytes:
        """
        为设备生成私钥

        参数：
            device_id: 设备唯一标识

        返回：设备私钥
        """
        # 简化：私钥 = Hash(主密钥 || 设备ID)
        h = hashlib.sha256(self.master_secret + device_id.encode()).digest()
        self.device_keys[device_id] = h
        return h

    def device_challenge_response(self, device_id: str, challenge: bytes) -> Tuple[bytes, bytes]:
        """
        设备生成挑战响应

        参数：
            device_id: 设备标识
            challenge: 网关发送的挑战

        返回：(响应, 时间戳)
        """
        if device_id not in self.device_keys:
            self.generate_device_private_key(device_id)

        private_key = self.device_keys[device_id]

        # 简化签名：HMAC(device_id, challenge)
        response = hmac.new(private_key, challenge, hashlib.sha256).digest()

        return response

    def gateway_verify(self, device_id: str, challenge: bytes, response: bytes) -> bool:
        """
        网关验证设备响应

        参数：
            device_id: 设备标识
            challenge: 原始挑战
            response: 设备响应

        返回：验证是否通过
        """
        if device_id not in self.device_keys:
            return False

        private_key = self.device_keys[device_id]
        expected = hmac.new(private_key, challenge, hashlib.sha256).digest()

        return hmac.compare_digest(response, expected)

    def mutual_authentication(self, device_id: str) -> Tuple[bytes, bytes, bool]:
        """
        设备与网关双向认证

        参数：
            device_id: 设备标识

        返回：(挑战, 响应, 验证结果)
        """
        # 1. 网关生成挑战
        challenge = os.urandom(32)

        # 2. 设备响应
        response = self.device_challenge_response(device_id, challenge)

        # 3. 网关验证
        verified = self.gateway_verify(device_id, challenge, response)

        return challenge, response, verified

    def session_key_derivation(self, device_id: str, shared_secret: bytes) -> bytes:
        """
        推导会话密钥

        参数：
            device_id: 设备标识
            shared_secret: 共享秘密

        返回：会话密钥
        """
        # 简化：使用HKDF类似的结构
        info = b"session_key_" + device_id.encode()
        return hashlib.sha256(shared_secret + info).digest()


def iot_security_threats():
    """IoT安全威胁"""
    print("=== IoT安全威胁 ===")
    print()
    print("1. 物理攻击")
    print("   - 设备被物理获取")
    print("   - 提取存储的密钥")
    print()
    print("2. 侧信道攻击")
    print("   - 功耗分析")
    print("   - 时序分析")
    print()
    print("3. 重放攻击")
    print("   - 捕获并重放旧消息")
    print()
    print("4. 中间人攻击")
    print("   - 拦截通信")
    print("   - 伪造身份")


# ========================== 测试代码 ==========================
if __name__ == "__main__":
    print("=== IoT身份认证测试 ===\n")

    # 创建认证系统
    auth = IoTIdentityBasedAuth()

    # 注册设备
    device_id = "sensor_001"
    device_key = auth.generate_device_private_key(device_id)

    print(f"设备ID: {device_id}")
    print(f"设备私钥: {device_key.hex()}")
    print()

    # 双向认证
    challenge, response, verified = auth.mutual_authentication(device_id)

    print(f"挑战: {challenge.hex()}")
    print(f"响应: {response.hex()}")
    print(f"验证结果: {'通过' if verified else '失败'}")
    print()

    # 会话密钥推导
    session_key = auth.session_key_derivation(device_id, response)

    print(f"会话密钥: {session_key.hex()}")
    print()

    # 安全威胁
    iot_security_threats()

    print()
    print("说明：")
    print("  - 基于身份的密码学简化证书管理")
    print("  - 适合大规模IoT部署")
    print("  - 实际系统需更强的数学基础")
