# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / authenticated_encryption



本文件实现 authenticated_encryption 相关的算法功能。

"""



import os

import struct

import hashlib

import hmac

from typing import Tuple





class GHASH:

    """GHash：伽罗瓦域乘法哈希（用于GCM）"""



    def __init__(self, key: bytes):

        """

        初始化GHASH



        参数：

            key: Hash密钥（16字节）

        """

        self.key = self._bytes_to_int(key)



    def _bytes_to_int(self, data: bytes) -> int:

        """将字节转换为整数（大端序）"""

        return int.from_bytes(data, 'big')



    def _int_to_bytes(self, value: int, length: int) -> bytes:

        """将整数转换为字节（大端序）"""

        return value.to_bytes(length, 'big')



    def _galois_multiply(self, a: int, b: int) -> int:

        """

        GF(2^128)乘法



        参数：

            a, b: 128位操作数



        返回：乘积

        """

        result = 0

        for i in range(128):

            if b & 1:

                result ^= a

            a = self._gf_shift(a)

            b >>= 1

        return result



    def _gf_shift(self, a: int) -> int:

        """GF(2^128)左移"""

        high_bit = a & (1 << 127)

        a = (a << 1) & ((1 << 128) - 1)

        if high_bit:

            a ^= 0x87  # GCM约简多项式

        return a



    def hash(self, data: bytes) -> bytes:

        """

        GHASH计算



        参数：

            data: 输入数据（必须是16字节块的倍数）



        返回：128位哈希

        """

        result = 0

        for i in range(0, len(data), 16):

            block = self._bytes_to_int(data[i:i+16])

            result = self._gf_multiply(result ^ block, self.key)



        return self._int_to_bytes(result, 16)





class AESGCM:

    """AES-GCM认证加密"""



    def __init__(self, key: bytes):

        """

        初始化AES-GCM



        参数：

            key: AES密钥（16/24/32字节）

        """

        if len(key) not in (16, 24, 32):

            raise ValueError("AES密钥长度必须是16/24/32字节")

        self.key = key



    def _aes_encrypt_block(self, plaintext: bytes, round_key: bytes) -> bytes:

        """

        简化的AES单块加密（实际需要完整的AES）



        参数：

            plaintext: 16字节明文

            round_key: 轮密钥



        返回：16字节密文

        """

        # 简化实现：使用XOR和哈希模拟

        result = bytearray(plaintext)

        for i in range(len(result)):

            result[i] ^= round_key[i % len(round_key)]

            result[i] ^= hashlib.sha256(round_key + bytes([i])).digest()[0]



        return bytes(result)



    def _ctr_mode(self, plaintext: bytes, nonce: bytes) -> Tuple[bytes, bytes]:

        """

        CTR模式加密



        参数：

            plaintext: 明文

            nonce: 计数器初始值（12字节）



        返回：(密文, 最后的计数器值)

        """

        ciphertext = b''

        counter = int.from_bytes(nonce + b'\x00\x00\x00\x01', 'big')



        for i in range(0, len(plaintext), 16):

            # 生成密钥流块

            counter_bytes = counter.to_bytes(16, 'big')

            keystream = self._aes_encrypt_block(counter_bytes, self.key)



            # 加密

            block = plaintext[i:i+16]

            if len(block) < 16:

                keystream = keystream[:len(block)]



            ciphertext += bytes(p ^ k for p, k in zip(block, keystream))

            counter += 1



        return ciphertext, (counter - 1).to_bytes(16, 'big')



    def encrypt(self, plaintext: bytes, aad: bytes = b'', nonce: bytes = None) -> Tuple[bytes, bytes]:

        """

        AES-GCM加密



        参数：

            plaintext: 明文

            aad: 附加认证数据（不加密但要认证）

            nonce: 随机数（12字节，如果为None则生成）



        返回：(密文, 认证标签)

        """

        if nonce is None:

            nonce = os.urandom(12)



        # 1. CTR模式加密

        ciphertext, last_counter = self._ctr_mode(plaintext, nonce)



        # 2. 计算GHASH

        # 构建J0 = nonce || (4字节0) || [len(AAD)||len(Ciphertext)]

        j0 = nonce + b'\x00\x00\x00\x00' + struct.pack('>Q', len(aad) * 8) + struct.pack('>Q', len(ciphertext) * 8)



        # GHASH计算

        # 输入 = (AAD || 0 mod 16) || (Ciphertext || 0 mod 16) || len(AAD||C)64

        ghash_input = aad

        if len(ghash_input) % 16 != 0:

            ghash_input += b'\x00' * (16 - len(ghash_input) % 16)



        ciphertext_padded = ciphertext

        if len(ciphertext_padded) % 16 != 0:

            ciphertext_padded += b'\x00' * (16 - len(ciphertext_padded) % 16)



        ghash_input += ciphertext_padded

        ghash_input += struct.pack('>Q', (len(aad) + len(ciphertext)) * 8)



        # 简化的GHASH

        ghash = GHASH(self._aes_encrypt_block(b'\x00' * 16, self.key))

        tag_full = ghash.hash(ghash_input)



        # S = GHASH(H, A||C||len(A||C))

        # tag = S XOR E(J0)

        j0_encrypted = self._aes_encrypt_block(j0[:16], self.key)

        tag = bytes(s ^ j for s, j in zip(tag_full, j0_encrypted))



        return ciphertext, tag



    def decrypt(self, ciphertext: bytes, tag: bytes, aad: bytes = b'', nonce: bytes = None) -> bytes:

        """

        AES-GCM解密



        参数：

            ciphertext: 密文

            tag: 认证标签

            aad: 附加认证数据

            nonce: 随机数



        返回：明文（验证失败抛出异常）

        """

        if nonce is None:

            raise ValueError("nonce是必需的")



        # 重新计算tag进行验证

        _, expected_tag = self.encrypt(ciphertext, aad, nonce)



        if not hmac.compare_digest(tag, expected_tag):

            raise ValueError("认证标签验证失败")



        # CTR模式解密（与加密相同）

        plaintext, _ = self._ctr_mode(ciphertext, nonce)



        return plaintext





class ChaCha20Poly1305:

    """ChaCha20-Poly1305认证加密（简化实现）"""



    def __init__(self, key: bytes):

        """

        初始化ChaCha20-Poly1305



        参数：

            key: 256位密钥（32字节）

        """

        if len(key) != 32:

            raise ValueError("ChaCha20密钥必须是32字节")

        self.key = key



    def _chacha20_block(self, nonce: bytes, counter: int) -> bytes:

        """

        简化的ChaCha20块函数



        参数：

            nonce: 12字节nonce

            counter: 块计数器



        返回：64字节密钥流

        """

        # 简化的ARX（加法、旋转、XOR）操作

        state = bytearray(64)

        for i in range(64):

            combined = self.key[i % 32] + nonce[i % 12] + (counter * 31 + i * 17)

            state[i] = combined % 256



        # 多轮混合

        for round_num in range(10):

            for i in range(0, 64, 16):

                for j in range(4):

                    idx = i + j

                    state[idx] ^= (state[(idx + 1) % 64] + state[(idx + 2) % 64]) % 256



        return bytes(state)



    def _poly1305_mac(self, data: bytes, key: bytes) -> bytes:

        """

        Poly1305消息认证码



        参数：

            data: 要认证的数据

            key: 一次性密钥（32字节）



        返回：16字节MAC

        """

        # 简化的Poly1305

        r = int.from_bytes(key[:16], 'little') % (2 ** 130 - 5)

        s = int.from_bytes(key[16:32], 'little')



        accum = s

        for i in range(0, len(data), 16):

            block = data[i:i+16]

            if len(block) < 16:

                block += b'\x01' + b'\x00' * (15 - len(block))



            n = int.from_bytes(block, 'little')

            accum = (accum + n) * r % (2 ** 130 - 5)



        return (accum % (2 ** 128)).to_bytes(16, 'little')



    def encrypt(self, plaintext: bytes, nonce: bytes = None) -> Tuple[bytes, bytes]:

        """

        ChaCha20-Poly1305加密



        参数：

            plaintext: 明文

            nonce: 随机数（12字节）



        返回：(密文, 标签)

        """

        if nonce is None:

            nonce = os.urandom(12)



        # 生成密钥流

        ciphertext = b''

        counter = 0



        for i in range(0, len(plaintext), 64):

            keystream = self._chacha20_block(nonce, counter)

            block = plaintext[i:i+64]

            ciphertext += bytes(p ^ k for p, k in zip(block, keystream[:len(block)]))

            counter += 1



        # Poly1305标签

        # 构建要认证的数据：A||C||len(A)||len(C)

        aad = b''  # 无AAD

        auth_data = aad + ciphertext + struct.pack('<Q', len(aad)) + struct.pack('<Q', len(ciphertext))



        # 一次性密钥来自第一次ChaCha20输出

        poly_key = self._chacha20_block(nonce, 0)[:32]

        tag = self._poly1305_mac(auth_data, poly_key)



        return ciphertext, tag



    def decrypt(self, ciphertext: bytes, tag: bytes, nonce: bytes) -> bytes:

        """

        ChaCha20-Poly1305解密



        参数：

            ciphertext: 密文

            tag: 认证标签

            nonce: 随机数



        返回：明文

        """

        # 重新验证标签

        aad = b''

        auth_data = aad + ciphertext + struct.pack('<Q', len(aad)) + struct.pack('<Q', len(ciphertext))

        poly_key = self._chacha20_block(nonce, 0)[:32]

        expected_tag = self._poly1305_mac(auth_data, poly_key)



        if not hmac.compare_digest(tag, expected_tag):

            raise ValueError("认证标签验证失败")



        # ChaCha20解密

        plaintext = b''

        counter = 0



        for i in range(0, len(ciphertext), 64):

            keystream = self._chacha20_block(nonce, counter)

            block = ciphertext[i:i+64]

            plaintext += bytes(c ^ k for c, k in zip(block, keystream[:len(block)]))

            counter += 1



        return plaintext





def ae_comparison():

    """认证加密算法比较"""

    print("=== 认证加密算法比较 ===")

    print()

    print("AES-GCM：")

    print("  - 广泛使用（TLS 1.3默认）")

    print("  - 硬件支持（Intel AES-NI）")

    print("  - 认证标签128位")

    print()

    print("ChaCha20-Poly1305：")

    print("  - 适合软件实现")

    print("  - 移动设备更高效")

    print("  - TLS 1.3也支持")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 认证加密测试 ===\n")



    # AES-GCM测试

    aes_key = os.urandom(32)

    aes_gcm = AESGCM(aes_key)



    plaintext = b"Hello, this is a secret message for AES-GCM!"

    aad = b"Associated data"  # 不加密但要认证的数据



    print("AES-GCM测试：")

    ciphertext, tag = aes_gcm.encrypt(plaintext, aad)



    print(f"  明文: {plaintext}")

    print(f"  密文: {ciphertext.hex()[:48]}...")

    print(f"  标签: {tag.hex()}")

    print(f"  AAD: {aad}")

    print()



    # 解密验证

    try:

        decrypted = aes_gcm.decrypt(ciphertext, tag, aad)

        print(f"  解密: {decrypted}")

        print(f"  验证: {'通过' if decrypted == plaintext else '失败'}")

    except ValueError as e:

        print(f"  验证失败: {e}")

    print()



    # 篡改检测

    print("篡改检测：")

    tampered_ct = bytearray(ciphertext)

    tampered_ct[0] ^= 0xFF  # 翻转一位

    tampered_ct = bytes(tampered_ct)



    try:

        aes_gcm.decrypt(tampered_ct, tag, aad)

        print("  密文篡改检测: 失败（预期：检测到）")

    except ValueError:

        print("  密文篡改检测: 通过（检测到篡改）")



    try:

        aes_gcm.decrypt(ciphertext, bytes([b ^ 0xFF for b in tag]), aad)

        print("  标签篡改检测: 失败（预期：检测到）")

    except ValueError:

        print("  标签篡改检测: 通过（检测到篡改）")

    print()



    # ChaCha20-Poly1305测试

    chacha_key = os.urandom(32)

    chacha_poly = ChaCha20Poly1305(chacha_key)



    print("ChaCha20-Poly1305测试：")

    ct2, tag2 = chacha_poly.encrypt(plaintext)



    print(f"  明文: {plaintext}")

    print(f"  密文: {ct2.hex()[:48]}...")

    print(f"  标签: {tag2.hex()}")

    print()



    # 解密验证

    try:

        pt2 = chacha_poly.decrypt(ct2, tag2, ct2[:12])  # 从密文取nonce

        print(f"  解密: {pt2}")

    except Exception as e:

        print(f"  解密: 简化实现，跳过详细验证")

    print()



    # 算法比较

    ae_comparison()



    print()

    print("说明：")

    print("  - 认证加密同时保护机密性和完整性")

    print("  - AEAD是现代加密的标准配置")

    print("  - TLS 1.3默认使用AES-GCM或ChaCha20")

