# -*- coding: utf-8 -*-

"""

算法实现：密码学与安全 / timing_cache_attack



本文件实现 timing_cache_attack 相关的算法功能。

"""



import time

import random

import hmac

import hashlib

from typing import Callable, List





class TimingAttack:

    """时序攻击模拟"""



    def __init__(self):

        """初始化时序攻击"""

        self.baseline_time = None



    def measure_time(self, func: Callable, *args, iterations: int = 100) -> float:

        """

        测量函数执行时间



        参数：

            func: 要测量的函数

            iterations: 迭代次数



        返回：平均执行时间（毫秒）

        """

        times = []

        for _ in range(iterations):

            start = time.perf_counter()

            func(*args)

            end = time.perf_counter()

            times.append((end - start) * 1000)



        return sum(times) / len(times)



    def vulnerable_compare(self, secret: bytes, guess: bytes) -> bool:

        """

        有漏洞的比较实现（逐字节比较，遇到错误立即返回）



        参数：

            secret: 秘密值

            guess: 猜测值



        返回：是否相等

        """

        if len(secret) != len(guess):

            return False



        for i in range(len(secret)):

            if secret[i] != guess[i]:

                return False

            # 每个字节比较后sleep（模拟真实漏洞）

            time.sleep(0.001)  # 1ms延迟



        return True



    def secure_compare(self, secret: bytes, guess: bytes) -> bool:

        """

        安全的恒定时间比较



        参数：

            secret: 秘密值

            guess: 猜测值



        返回：是否相等

        """

        if len(secret) != len(guess):

            return False



        result = 0

        for i in range(len(secret)):

            result |= secret[i] ^ guess[i]



        return result == 0



    def attack_byte(self, secret: bytes, position: int) -> int:

        """

        攻击单个字节



        参数：

            secret: 秘密值

            position: 目标位置



        返回：猜测的字节值

        """

        # 测量baseline（错误位置）

        times_for_each_byte = []



        for guess_byte in range(256):

            guess = bytearray(len(secret))

            guess[position] = guess_byte



            # 测量时间

            if self.baseline_time is None:

                # 测量错误字节的平均时间

                wrong_times = []

                for wrong_byte in range(256):

                    if wrong_byte != secret[position]:

                        test_guess = bytearray(secret)

                        test_guess[position] = wrong_byte

                        start = time.perf_counter()

                        self.vulnerable_compare(bytes(secret), bytes(test_guess))

                        end = time.perf_counter()

                        wrong_times.append((end - start) * 1000)

                self.baseline_time = sum(wrong_times) / len(wrong_times)



            # 测量这个猜测的时间

            start = time.perf_counter()

            self.vulnerable_compare(bytes(secret), bytes(guess))

            end = time.perf_counter()

            elapsed = (end - start) * 1000



            times_for_each_byte.append(elapsed)



        # 时间最长的是正确的

        return times_for_each_byte.index(max(times_for_each_byte))



    def attack(self, secret: bytes, max_len: int = None) -> bytes:

        """

        时序攻击完整流程



        参数：

            secret: 秘密值

            max_len: 最大猜测长度



        返回：攻击得到的值

        """

        if max_len is None:

            max_len = len(secret)



        recovered = bytearray()



        for i in range(max_len):

            guessed = self.attack_byte(secret, i)

            recovered.append(guessed)

            print(f"  位置{i}: {guessed} (0x{guessed:02x})")



        return bytes(recovered)





class CacheAttack:

    """Cache侧信道攻击"""



    def __init__(self, cache_line_size: int = 64):

        """

        初始化Cache攻击



        参数：

            cache_line_size: Cache行大小（字节）

        """

        self.cache_line_size = cache_line_size



    def access_memory(self, address: int) -> bool:

        """

        模拟内存访问是否命中Cache



        参数：

            address: 内存地址



        返回：是否Cache命中

        """

        # 简化：地址在Cache窗口内则命中

        cache_window = 1024  # 简化Cache大小

        return (address % cache_window) < 256



    def prime_probe(self, data_access: List[int]) -> List[float]:

        """

        Prime+Probe攻击：测量访问时间



        参数：

            data_access: 数据访问地址列表



        返回：每个数据项的访问时间

        """

        times = []

        for addr in data_access:

            start = time.perf_counter_ns()

            # 模拟Cache访问

            hit = self.access_memory(addr)

            end = time.perf_counter_ns()

            times.append((end - start, hit))



        return times



    def extract_bit(self, secret_key_byte: int, target_bit: int, 

                    access_pattern_0: List[int], access_pattern_1: List[int]) -> int:

        """

        从Cache访问模式提取密钥某位



        参数：

            secret_key_byte: 密钥字节

            target_bit: 目标位

            access_pattern_0: 位为0时的访问模式

            access_pattern_1: 位为1时的访问模式



        返回：猜测的位值

        """

        # 测量实际的访问时间

        if (secret_key_byte >> target_bit) & 1:

            pattern = access_pattern_1

        else:

            pattern = access_pattern_0



        times = self.prime_probe(pattern)

        avg_time = sum(t for t, _ in times) / len(times)



        # 简化判断

        return 1 if avg_time > 100 else 0



    def specter_like_attack(self, array_size: int = 256) -> bytes:

        """

        模拟Spectre类攻击（简化的边界检查绕过）



        参数：

            array_size: 数组大小



        返回：泄露的数据

        """

        # 模拟训练阶段和攻击阶段

        secret_data = bytes([random.randint(0, 255) for _ in range(16)])



        # 正常访问

        def bounds_check(index: int) -> int:

            if index < array_size:

                return secret_data[index]

            return 0



        # 攻击：训练CPU错误预测

        leaked = bytearray()

        for i in range(8):

            # 简化：实际需要CPU的 speculative execution

            leaked.append(secret_data[i])



        return bytes(leaked)





class BranchPredictorAttack:

    """分支预测器攻击（简化的Spectre）"""



    def __init__(self):

        """初始化"""

        self.training_index = 0



    def victim_function(self, x: int, secret: bytes) -> int:

        """

        受害函数（恒定时间实现）



        参数：

            x: 索引

            secret: 秘密数据



        返回：秘密数据[x]

        """

        if x < len(secret):

            return secret[x]

        return 0



    def attack(self, secret: bytes, malicious_index: int) -> int:

        """

        执行攻击



        参数：

            secret: 秘密

            malicious_index: 恶意索引



        返回：泄露的秘密字节

        """

        # 简化：分支预测攻击

        # 实际需要 speculative execution



        # 训练阶段：多次使用合法索引

        for _ in range(100):

            self.victim_function(0, secret)



        # 攻击阶段：使用恶意索引

        # CPU可能仍然使用分支预测执行

        leaked = self.victim_function(malicious_index, secret)



        return leaked





def countermeasure_summary():

    """防御措施总结"""

    print("=== 时序/Cache攻击防御 ===")

    print()

    print("时序攻击防御：")

    print("  1. 恒定时间比较")

    print("  2. 避免分支")

    print("  3. 使用密码学库的安全比较")

    print()

    print("Cache攻击防御：")

    print("  1. 恒定时间访问模式")

    print("  2. 清除敏感Cache行")

    print("  3. 随机化Cache策略")

    print()

    print("微架构攻击防御：")

    print("  1. 禁用高分辨率计时器")

    print("  2. 使用安全编程语言")

    print("  3. 硬件级别隔离")





# ========================== 测试代码 ==========================

if __name__ == "__main__":

    print("=== 时序攻击与Cache攻击测试 ===\n")



    # 时序攻击演示

    print("时序攻击演示：")

    attack = TimingAttack()



    secret = b"SecretPass123"



    print(f"  秘密值: {secret}")

    print(f"  秘密长度: {len(secret)}")

    print()



    # 测量比较时间差异

    print("比较时间测量：")

    correct_guess = bytearray(secret)

    wrong_guess = bytearray(b"XecretPass123")



    correct_start = time.perf_counter()

    attack.vulnerable_compare(bytes(secret), bytes(correct_guess))

    correct_end = time.perf_counter()



    wrong_start = time.perf_counter()

    attack.vulnerable_compare(bytes(secret), bytes(wrong_guess))

    wrong_end = time.perf_counter()



    print(f"  正确猜测耗时: {(correct_end-correct_start)*1000:.2f} ms")

    print(f"  错误猜测耗时: {(wrong_end-wrong_start)*1000:.2f} ms")

    print()



    # 攻击单字节

    print("单字节攻击：")

    byte_position = 0

    guess = attack.attack_byte(secret, byte_position)

    actual = secret[byte_position]

    print(f"  位置0: 猜测={guess} (0x{guess:02x}), 实际={actual} (0x{actual:02x})")

    print()



    # 安全比较演示

    print("安全比较（恒定时间）：")

    secure_times = []

    for _ in range(10):

        start = time.perf_counter()

        attack.secure_compare(bytes(secret), bytes(correct_guess))

        end = time.perf_counter()

        secure_times.append((end - start) * 1000)



    print(f"  正确猜测: {sum(secure_times)/len(secure_times):.4f} ms (稳定)")

    print()



    # Cache攻击演示

    print("Cache侧信道攻击演示：")

    cache_attack = CacheAttack()



    data_access = [i * 64 for i in range(16)]

    times = cache_attack.prime_probe(data_access)



    print(f"  访问16个Cache行")

    hits = sum(1 for _, hit in times if hit)

    print(f"  Cache命中: {hits}/16")

    print()



    # 分支预测攻击

    print("分支预测攻击演示：")

    bp_attack = BranchPredictorAttack()



    secret = b"HiddenKey"

    leaked = bp_attack.attack(secret, 4)



    print(f"  秘密: {secret}")

    print(f"  泄露: {bytes([leaked])}")

    print()



    # 防御措施

    countermeasure_summary()



    print()

    print("说明：")

    print("  - 侧信道攻击绕过了算法的数学安全性")

    print("  - 攻击者通过物理信息推断秘密")

    print("  - 实现层面的防御比算法层面更重要")

