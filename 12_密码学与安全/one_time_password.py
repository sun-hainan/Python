# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / one_time_password



本文件实现 one_time_password 相关的算法功能。

"""



import hmac

import hashlib

import time

import struct

from typing import Tuple





class HOTPGenerator:

    """基于计数器的HOTP"""



    def __init__(self, secret: bytes, digits: int = 6):

        """

        初始化HOTP



        参数：

            secret: 共享密钥

            digits: 验证码位数（通常6或8）

        """

        self.secret = secret

        self.digits = digits

        self.counter = 0



    def _truncate(self, hmac_result: bytes) -> int:

        """

        动态截断算法



        参数：

            hmac_result: HMAC-SHA1结果（20字节）



        返回：6位十进制OTP

        """

        # 取最后一个字节的低4位作为偏移

        offset = hmac_result[-1] & 0x0F



        # 从偏移位置取4字节

        truncated = struct.unpack('>I', hmac_result[offset:offset+4])[0]



        # 取低31位（避免符号位问题）

        truncated = truncated & 0x7FFFFFFF



        # 取模得到指定位数的OTP

        otp = truncated % (10 ** self.digits)



        return otp



    def generate(self, counter: int = None) -> str:

        """

        生成HOTP



        参数：

            counter: 计数器（如果为None，使用内部计数器）



        返回：OTP字符串

        """

        if counter is None:

            counter = self.counter



        # 将计数器转换为8字节大端序

        counter_bytes = struct.pack('>Q', counter)



        # 计算HMAC-SHA1

        hmac_result = hmac.new(self.secret, counter_bytes, hashlib.sha1).digest()



        # 截断得到OTP

        otp_value = self._truncate(hmac_result)



        # 补齐前导0

        return str(otp_value).zfill(self.digits)



    def verify(self, otp: str, counter: int = None, window: int = 1) -> Tuple[bool, int]:

        """

        验证HOTP



        参数：

            otp: 待验证的OTP

            counter: 当前计数器

            window: 允许的前后窗口大小



        返回：(是否有效, 匹配的计数器)

        """

        if counter is None:

            counter = self.counter



        # 在窗口范围内查找匹配

        for c in range(counter, counter + window + 1):

            if self.generate(c) == otp:

                return True, c



        return False, counter



    def increment_counter(self):

        """递增计数器"""

        self.counter += 1





class TOTPGenerator:

    """基于时间的TOTP"""



    def __init__(self, secret: bytes, digits: int = 6, period: int = 30):

        """

        初始化TOTP



        参数：

            secret: 共享密钥

            digits: 验证码位数

            period: 时间步长（秒）

        """

        self.secret = secret

        self.digits = digits

        self.period = period

        self.epoch = 0  # 起始时间（Unix epoch）



    def _get_time_counter(self, timestamp: float = None) -> int:

        """

        获取时间计数器



        参数：

            timestamp: Unix时间戳（如果为None，使用当前时间）



        返回：时间计数器

        """

        if timestamp is None:

            timestamp = time.time()



        return int((timestamp - self.epoch) // self.period)



    def generate(self, timestamp: float = None) -> str:

        """

        生成TOTP



        参数：

            timestamp: Unix时间戳



        返回：OTP字符串

        """

        counter = self._get_time_counter(timestamp)

        counter_bytes = struct.pack('>Q', counter)



        hmac_result = hmac.new(self.secret, counter_bytes, hashlib.sha1).digest()



        # 动态截断

        offset = hmac_result[-1] & 0x0F

        truncated = struct.unpack('>I', hmac_result[offset:offset+4])[0]

        truncated = truncated & 0x7FFFFFFF



        otp_value = truncated % (10 ** self.digits)



        return str(otp_value).zfill(self.digits)



    def verify(self, otp: str, timestamp: float = None, window: int = 1) -> bool:

        """

        验证TOTP



        参数：

            otp: 待验证的OTP

            timestamp: Unix时间戳

            window: 允许的时间偏移（步长数）



        返回：验证结果

        """

        current_counter = self._get_time_counter(timestamp)



        # 允许前后window个时间步长

        for offset in range(-window, window + 1):

            if self.generate(timestamp + offset * self.period) == otp:

                return True



        return False



    def remaining_seconds(self, timestamp: float = None) -> int:

        """

        计算当前OTP剩余有效时间



        参数：

            timestamp: Unix时间戳



        返回：剩余秒数

        """

        if timestamp is None:

            timestamp = time.time()



        elapsed = int((timestamp - self.epoch) % self.period)

        return self.period - elapsed





def totp_vs_hotp():

    """TOTP vs HOTP"""

    print("=== TOTP vs HOTP ===")

    print()

    print("TOTP（基于时间）：")

    print("  - 每30秒生成新密码")

    print("  - 不需要服务器同步计数器")

    print("  - 客户端和服务器时间必须同步")

    print("  - 例子：Google Authenticator")

    print()

    print("HOTP（基于计数器）：")

    print("  - 每次验证后计数器递增")

    print("  - 允许一定窗口内的验证失败")

    print("  - 服务器和客户端需要同步计数器")

    print("  - 例子：银行U盾")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 一次性密码(OTP)测试 ===\n")



    # 共享密钥

    secret = b'base32secretkey123456789'



    # TOTP测试

    totp = TOTPGenerator(secret, digits=6, period=30)



    print("TOTP测试：")

    current_otp = totp.generate()

    print(f"  当前OTP: {current_otp}")

    print(f"  剩余有效时间: {totp.remaining_seconds()} 秒")

    print(f"  验证: {'通过' if totp.verify(current_otp) else '失败'}")

    print()



    # 时间偏移测试

    past_otp = totp.generate(time.time() - 60)  # 1分钟前

    print(f"1分钟前OTP: {past_otp}")

    print(f"当前时间验证旧OTP: {'通过' if totp.verify(past_otp) else '失败'}")

    print()



    # HOTP测试

    hotp = HOTPGenerator(secret, digits=6)



    print("HOTP测试：")

    for i in range(5):

        otp = hotp.generate(i)

        print(f"  计数器{i}: {otp}")



    # 模拟验证流程

    print()

    print("验证流程模拟：")

    current_counter = 2

    valid_otp = hotp.generate(current_counter)

    print(f"  当前计数器: {current_counter}")

    print(f"  生成OTP: {valid_otp}")



    # 正确验证

    valid, matched = hotp.verify(valid_otp, current_counter)

    print(f"  验证结果: {'通过' if valid else '失败'} (匹配计数器: {matched})")



    # 窗口测试

    print()

    print("窗口测试（窗口=2）：")

    for c in [current_counter - 2, current_counter - 1, current_counter + 1, current_counter + 2]:

        if c != current_counter:

            otp = hotp.generate(c)

            valid, _ = hotp.verify(otp, current_counter, window=2)

            print(f"  计数器{c}的OTP在当前验证: {'通过' if valid else '失败'}")

    print()



    # 比较

    totp_vs_hotp()



    print()

    print("说明：")

    print("  - OTP提供动态密码")

    print("  - 即使密码泄露也无法重用")

    print("  - 广泛用于双因素认证")

