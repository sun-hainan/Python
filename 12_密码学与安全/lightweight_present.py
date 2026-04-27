# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / lightweight_present



本文件实现 lightweight_present 相关的算法功能。

"""



import binascii

from typing import Tuple





class PRESENTCipher:

    """PRESENT轻量级块密码"""



    # S盒（4位输入4位输出）

    S_BOX = [

        0xC, 0x5, 0x6, 0xB, 0x9, 0x0, 0xA, 0xD,

        0x3, 0xE, 0xF, 0x8, 0x4, 0x7, 0x1, 0x2

    ]



    # P置换层（位重排）

    P_LAYER = [

        0, 16, 32, 48, 1, 17, 33, 49, 2, 18, 34, 50, 3, 19, 35, 51,

        4, 20, 36, 52, 5, 21, 37, 53, 6, 22, 38, 54, 7, 23, 39, 55,

        8, 24, 40, 56, 9, 25, 41, 57, 10, 26, 42, 58, 11, 27, 43, 59,

        12, 28, 44, 60, 13, 29, 45, 61, 14, 30, 46, 62, 15, 31, 47, 63

    ]



    # 轮常量（每个round的常量不同）

    ROUND_CONSTANTS = [0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F]



    def __init__(self, key: bytes, key_len: int = 80):

        """

        初始化PRESENT加密器



        参数：

            key: 密钥字节（10字节=80位，或16字节=128位）

            key_len: 密钥长度（80或128）

        """

        if len(key) not in (10, 16):

            raise ValueError("密钥长度必须是80位(10字节)或128位(16字节)")

        self.key = key

        self.key_len = key_len



    def _apply_sbox(self, nibble: int) -> int:

        """

        应用S盒替换



        参数：

            nibble: 4位输入



        返回：S盒输出

        """

        return self.S_BOX[nibble & 0xF]



    def _apply_p_layer(self, state: int) -> int:

        """

        应用P置换层



        参数：

            state: 64位状态



        返回：置换后的状态

        """

        new_state = 0

        for i in range(64):

            if state & (1 << i):

                new_state |= 1 << self.P_LAYER[i]

        return new_state



    def _key_schedule_round(self, round_key: int, round_num: int) -> int:

        """

        一轮密钥调度



        参数：

            round_key: 当前轮密钥

            round_num: 轮数（0-31）



        返回：下一轮密钥

        """

        # 左旋63位

        round_key = ((round_key << 61) | (round_key >> 3)) & 0xFFFFFFFFFFFFFFFFFFFF



        # 高4位通过S盒

        high_nibble = (round_key >> 76) & 0xF

        round_key = (round_key & 0x0FFFFFFFFFFFFFFFFFFF) | (self._apply_sbox(high_nibble) << 76)



        # 异或轮常量

        round_key ^= (round_num + 1) << 15



        return round_key



    def _extract_round_key(self, key: int, round_num: int) -> int:

        """

        提取指定轮的轮密钥



        参数：

            key: 主密钥

            round_num: 轮数



        返回：64位轮密钥

        """

        return (key >> (round_num * 4)) & 0xFFFFFFFFFFFFFFFF



    def encrypt_block(self, plaintext: int) -> int:

        """

        加密单个64位块



        参数：

            plaintext: 64位明文



        返回：64位密文

        """

        key = int.from_bytes(self.key[:10], 'big') if self.key_len == 80 else int.from_bytes(self.key, 'big')

        state = plaintext



        for round_num in range(31):

            # 轮密钥加

            round_key = self._extract_round_key(key, round_num)

            state ^= round_key



            # S盒替换（16个4位并行操作）

            new_state = 0

            for i in range(16):

                nibble = (state >> (i * 4)) & 0xF

                new_state |= self._apply_sbox(nibble) << (i * 4)

            state = new_state



            # P置换

            if round_num < 30:  # 最后一轮后不做P置换

                state = self._apply_p_layer(state)



            # 更新轮密钥

            key = self._key_schedule_round(key, round_num)



        # 最后一轮密钥加

        state ^= self._extract_round_key(key, 31)



        return state



    def encrypt(self, data: bytes) -> bytes:

        """

        加密数据（ECB模式）



        参数：

            data: 明文字节



        返回：密文字节

        """

        # PKCS7填充

        pad_len = 8 - (len(data) % 8)

        data += bytes([pad_len] * pad_len)



        ciphertext = b''

        for i in range(0, len(data), 8):

            block = int.from_bytes(data[i:i+8], 'big')

            ciphertext += self.encrypt_block(block).to_bytes(8, 'big')



        return ciphertext



    def decrypt(self, data: bytes) -> bytes:

        """

        解密数据（ECB模式）



        参数：

            data: 密文字节



        返回：明文字节

        """

        # 注意：完整PRESENT解密需要逆S盒和逆P置换

        # 此处简化处理

        plaintext = b''

        for i in range(0, len(data), 8):

            plaintext += b'\x00' * 8  # 简化占位



        # 去除PKCS7填充

        if plaintext:

            pad_len = plaintext[-1]

            plaintext = plaintext[:-pad_len]



        return plaintext





def present_characteristics():

    """PRESENT算法特性"""

    print("=== PRESENT算法特性 ===")

    print()

    print("设计目标：")

    print("  - 硬件门数约1000 GE")

    print("  - 适合RFID、传感器")

    print()

    print("安全性：")

    print("  - 80位密钥：31轮攻击")

    print("  - 128位密钥：更强")

    print()

    print("应用场景：")

    print("  - IoT设备加密")

    print("  - 车联网安全")

    print("  - 医疗设备")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== PRESENT轻量级密码测试 ===\n")



    # 测试向量（80位密钥）

    key = b'\x00' * 10  # 全0密钥

    cipher = PRESENTCipher(key, 80)



    # 加密测试

    plaintext = b'HelloPT!'

    ciphertext = cipher.encrypt(plaintext)



    print(f"明文: {plaintext}")

    print(f"密文: {ciphertext.hex()}")

    print()



    # 显示算法特性

    present_characteristics()



    print()

    print("说明：")

    print("  - PRESENT是超轻量级块密码")

    print("  - 硬件实现极简")

    print("  - 适用于受限IoT设备")

