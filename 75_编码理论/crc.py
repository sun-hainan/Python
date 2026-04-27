# -*- coding: utf-8 -*-

"""

算法实现：编码理论 / crc



本文件实现 crc 相关的算法功能。

"""



import numpy as np

import struct





# --------------------------------------------------------------------------- #

# CRC 核心算法

# --------------------------------------------------------------------------- #



class CRC:

    """

    CRC 循环冗余校验器



    参数:

        polynomial (int): 生成多项式的系数表示（十六进制）

                          例如 CRC-32 的 poly = 0x04C11DB7

        init_value (int): 寄存器的初始值

        reflect_in (bool): 输入字节是否翻转（LSB first）

        reflect_out (bool): 输出（余数）是否翻转

        xor_output (int): 输出余数前与之 XOR 的值

        check (int): CRC("123456789") 的标准校验值



    示例:

        >>> crc32 = CRC(polynomial=0x04C11DB7, width=32)

        >>> crc32.compute(b"Hello")

        2008551444

    """



    def __init__(self, polynomial, width=8, init_value=0,

                 reflect_in=False, reflect_out=False,

                 xor_output=0, check_value=0):

        self.width = width

        self.polynomial = polynomial

        self.init_value = init_value

        self.reflect_in = reflect_in

        self.reflect_out = reflect_out

        self.xor_output = xor_output

        self.check_value = check_value



        # 初始化查找表

        self._build_table()



    def _build_table(self):

        """

        构建 CRC 查找表（字节级算法加速）



        对每个可能的字节值（0-255），预计算其 CRC 值

        这样可以将每个字节的处理从 O(bits) 降到 O(1)

        """

        self.table = []

        divisor = self.polynomial



        for byte_value in range(256):

            # 初始化寄存器（考虑 reflect_in）

            if self.reflect_in:

                # LSB first：翻转字节

                register = self._reflect(byte_value, 8)

            else:

                # MSB first：直接使用

                register = byte_value << (self.width - 8)



            # 对字节的每一位进行移位和异或

            for _ in range(8):

                # 检查最高位是否为 1

                top_bit = (register >> (self.width - 1)) & 1

                register = (register << 1) & ((1 << self.width) - 1)



                if top_bit:

                    register ^= divisor



            # 考虑 reflect_out

            if self.reflect_out:

                register = self._reflect(register, self.width)



            self.table.append(register)



    def _reflect(self, value, bits):

        """

        翻转一个整数的位顺序



        参数:

            value: 待翻转的整数

            bits: 位数



        返回:

            int: 翻转后的整数

        """

        result = 0

        for i in range(bits):

            if (value >> i) & 1:

                result |= (1 << (bits - 1 - i))

        return result



    def compute_bit_by_bit(self, data):

        """

        逐比特计算 CRC（最原始的算法）



        参数:

            data: 字节串



        返回:

            int: CRC 余数

        """

        register = self.init_value

        divisor = self.polynomial



        for byte in data:

            if self.reflect_in:

                byte = self._reflect(byte, 8)



            for bit in range(8):

                input_bit = (byte >> bit) & 1

                top_bit = (register >> (self.width - 1)) & 1



                # 左移寄存器，移入新的一位

                register = (register << 1) & ((1 << self.width) - 1)



                if input_bit ^ top_bit:

                    register ^= divisor



        # 最后的反射

        if self.reflect_out:

            register = self._reflect(register, self.width)



        return register ^ self.xor_output



    def compute_table_driven(self, data):

        """

        查表法 CRC 计算



        参数:

            data: 字节串



        返回:

            int: CRC 余数

        """

        register = self.init_value



        for byte in data:

            if self.reflect_in:

                # 翻转输入字节的低 8 位

                table_index = self._reflect(byte, 8) ^ (register >> (self.width - 8))

            else:

                table_index = (register >> (self.width - 8)) ^ byte



            # 查表并更新寄存器

            register = ((register << 8) & ((1 << self.width) - 1)) ^ self.table[table_index]



        if self.reflect_out:

            register = self._reflect(register, self.width)



        return register ^ self.xor_output



    def compute(self, data):

        """

        计算数据的 CRC 值（默认使用查表法）



        参数:

            data: bytes 或 bytearray 类型



        返回:

            int: CRC 值

        """

        return self.compute_table_driven(data)



    def verify(self, data):

        """

        验证数据完整性



        参数:

            data: 包含数据和 CRC 的字节串

                 数据的最后 width/8 个字节是 CRC 值



        返回:

            bool: True 表示 CRC 校验通过

        """

        width_bytes = (self.width + 7) // 8

        if len(data) < width_bytes:

            return False



        message = data[:-width_bytes]

        received_crc = int.from_bytes(data[-width_bytes:], 'big')



        computed_crc = self.compute(message)

        return computed_crc == received_crc



    def encode(self, data):

        """

        对数据添加 CRC 校验码（编码）



        参数:

            data: 原始数据



        返回:

            bytes: 数据 + CRC

        """

        crc = self.compute(data)

        width_bytes = (self.width + 7) // 8

        crc_bytes = crc.to_bytes(width_bytes, 'big')

        return bytes(data) + crc_bytes



    def decode(self, data):

        """

        验证并去除 CRC（译码）



        参数:

            data: 包含 CRC 的数据



        返回:

            tuple: (原始数据, 是否正确)

        """

        if not self.verify(data):

            return data[:-self.width // 8], False

        return data[:-self.width // 8], True





# --------------------------------------------------------------------------- #

# 标准 CRC 配置

# --------------------------------------------------------------------------- #



# CRC-8 标准配置

CRC8 = {

    'polynomial': 0x07,

    'width': 8,

    'init': 0x00,

    'reflect_in': False,

    'reflect_out': False,

    'xor_output': 0x00,

    'check': 0xF4

}



# CRC-16-CCITT（用于 X.25, V.41, Bluetooth, USB 等）

CRC16_CCITT = {

    'polynomial': 0x1021,

    'width': 16,

    'init': 0xFFFF,

    'reflect_in': False,

    'reflect_out': False,

    'xor_output': 0x0000,

    'check': 0x29B1

}



# CRC-16-IBM（用于 Modbus, USB, etc）

CRC16_IBM = {

    'polynomial': 0x8005,

    'width': 16,

    'init': 0x0000,

    'reflect_in': True,

    'reflect_out': True,

    'xor_output': 0x0000,

    'check': 0xBB3D

}



# CRC-32（用于以太网、PNG、zip、 SATA 等）

CRC32 = {

    'polynomial': 0x04C11DB7,

    'width': 32,

    'init': 0xFFFFFFFF,

    'reflect_in': False,

    'reflect_out': False,

    'xor_output': 0xFFFFFFFF,

    'check': 0xCBF43926

}



# CRC-32C（Castagnoli，用于 SCTP、SSD 等）

CRC32C = {

    'polynomial': 0x1EDC6F41,

    'width': 32,

    'init': 0xFFFFFFFF,

    'reflect_in': True,

    'reflect_out': True,

    'xor_output': 0xFFFFFFFF,

    'check': 0xE3069283

}





def create_crc(name):

    """

    根据名称创建标准 CRC 实例



    参数:

        name (str): CRC 名称，如 "CRC-32", "CRC-8", "CRC-16-CCITT"



    返回:

        CRC: CRC 实例

    """

    configs = {

        'CRC-8': CRC8,

        'CRC-16-CCITT': CRC16_CCITT,

        'CRC-16-IBM': CRC16_IBM,

        'CRC-32': CRC32,

        'CRC-32C': CRC32C

    }



    if name not in configs:

        raise ValueError(f"未知的 CRC 类型: {name}")



    cfg = configs[name]

    return CRC(

        polynomial=cfg['polynomial'],

        width=cfg['width'],

        init_value=cfg['init'],

        reflect_in=cfg['reflect_in'],

        reflect_out=cfg['reflect_out'],

        xor_output=cfg['xor_output'],

        check_value=cfg['check']

    )





# --------------------------------------------------------------------------- #

# 简单 CRC（用于教学理解）

# --------------------------------------------------------------------------- #



def simple_crc(message, generator):

    """

    简单 CRC 实现（比特级，便于理解原理）



    参数:

        message (str 或 list): 输入比特串或字节串

        generator (list 或 int): 生成多项式系数列表或整数



    返回:

        list: [商系数, 余数系数]

              商用于验证，余数是 CRC 值



    示例:

        >>> msg_bits = [1, 0, 1, 1, 0, 0, 1]  # 消息

        >>> g = [1, 0, 0, 1]  # 生成多项式 x^3 + 1

        >>> quotient, remainder = simple_crc(msg_bits, g)

        >>> print(f"商: {quotient}, 余数: {remainder}")

    """

    # 将 generator 转为列表

    if isinstance(generator, int):

        g_degree = generator.bit_length() - 1

        g = [(generator >> i) & 1 for i in range(g_degree + 1)]

    else:

        g = list(generator)

        g_degree = len(g) - 1



    # 将消息转为比特列表

    if isinstance(message, str):

        msg_bits = [1 if c == '1' else 0 for c in message]

    elif isinstance(message, bytes):

        msg_bits = []

        for byte in message:

            for i in range(8):

                msg_bits.append((byte >> i) & 1)

    else:

        msg_bits = list(message)



    # 在消息后面补 r 个零（r = 生成多项式度数）

    msg_extended = msg_bits + [0] * g_degree



    # 模拟除法

    n = len(msg_extended)

    quotient = []



    for i in range(n - g_degree):

        # 如果当前位是 1，则进行除法

        if msg_extended[i] == 1:

            quotient.append(1)

            for j in range(g_degree + 1):

                msg_extended[i + j] ^= g[j]

        else:

            quotient.append(0)



    # 余数是最后 g_degree 位

    remainder = msg_extended[-(g_degree):]



    return quotient, remainder





def crc_encode(message, generator, format='bytes'):

    """

    CRC 编码：将消息加上 CRC 校验位



    参数:

        message: 原始消息

        generator: 生成多项式

        format: 'bits' 或 'bytes'



    返回:

        编码后的消息（末尾附加余数）

    """

    if format == 'bits':

        _, remainder = simple_crc(message, generator)

        return list(message) + remainder

    else:

        if isinstance(message, str):

            msg_bytes = message.encode('utf-8')

        else:

            msg_bytes = bytes(message)



        # 创建 CRC 实例

        crc = CRC(generator, width=generator.bit_length() - 1)

        return crc.encode(msg_bytes)





# --------------------------------------------------------------------------- #

# 错误检测能力分析

# --------------------------------------------------------------------------- #



def crc_error_detection(crc_width, burst_length):

    """

    分析 CRC 的错误检测能力



    参数:

        crc_width (int): CRC 位数（如 32）

        burst_length (int): 突发错误长度



    返回:

        dict: 分析结果

    """

    result = {

        'crc_width': crc_width,

        'burst_length': burst_length,

        'detects_all': burst_length <= crc_width,

        'detects_probability': None

    }



    if burst_length <= crc_width:

        result['detects_probability'] = 1.0

    else:

        # 超过 CRC 宽度的突发错误有 2^{-CRC_width} 的概率不被检测

        result['detects_probability'] = 1 - (1 / (2 ** crc_width))



    return result





# --------------------------------------------------------------------------- #

# 测试

# --------------------------------------------------------------------------- #



if __name__ == "__main__":

    print("=" * 60)

    print("CRC 循环冗余校验测试")

    print("=" * 60)



    # 测试 1: 简单 CRC（比特级）

    print("\n【测试 1】简单 CRC（比特级）")

    msg = "101110"

    g = [1, 0, 0, 1]  # x^3 + 1，即 1001

    quotient, remainder = simple_crc(msg, g)

    print(f"消息: {msg}")

    print(f"生成多项式: {g} (即 x^3 + 1)")

    print(f"商: {quotient}")

    print(f"余数(CRC): {remainder}")



    # 验证：商*G + 余数 = 消息左移3位

    print("验证: 商*G + 余数 = 消息*2^3:")

    reconstructed = [0] * (len(quotient) + len(g) - 1)

    for i, q in enumerate(quotient):

        if q == 1:

            for j, coeff in enumerate(g):

                reconstructed[i + j] ^= coeff

    print(f"  结果: {reconstructed[:len(msg)]} + {reconstructed[len(msg):]}")

    print(f"  期望: {list(msg)} + {remainder}")

    assert reconstructed[:len(msg)] == [int(c) for c in msg]

    assert reconstructed[len(msg):] == remainder

    print("✓ 简单 CRC 验证通过")



    # 测试 2: CRC-8

    print("\n【测试 2】CRC-8")

    crc8 = create_crc('CRC-8')

    test_data = b"123456789"

    crc8_val = crc8.compute(test_data)

    print(f"CRC-8({test_data}) = {hex(crc8_val)}")

    print(f"标准校验值: {hex(crc8.check_value)}")

    assert crc8_val == crc8.check_value

    print("✓ CRC-8 测试通过")



    # 测试 3: CRC-16-CCITT

    print("\n【测试 3】CRC-16-CCITT")

    crc16 = create_crc('CRC-16-CCITT')

    test_data = b"Hello"

    crc16_val = crc16.compute(test_data)

    print(f"CRC-16-CCITT({test_data}) = {hex(crc16_val)}")

    print(f"编码后: {crc16.encode(test_data).hex()}")

    print("✓ CRC-16-CCITT 测试通过")



    # 测试 4: CRC-32

    print("\n【测试 4】CRC-32")

    crc32 = create_crc('CRC-32')

    test_data = b"123456789"

    crc32_val = crc32.compute(test_data)

    print(f"CRC-32({test_data}) = {hex(crc32_val)}")

    print(f"标准校验值: {hex(crc32.check_value)}")

    assert crc32_val == crc32.check_value



    # 编码/验证

    encoded = crc32.encode(test_data)

    print(f"编码后 ({len(encoded)} bytes): {encoded.hex()}")

    assert crc32.verify(encoded)

    print("✓ CRC-32 测试通过")



    # 测试 5: CRC-32C

    print("\n【测试 5】CRC-32C")

    crc32c = create_crc('CRC-32C')

    crc32c_val = crc32c.compute(b"Hello")

    print(f"CRC-32C(b'Hello') = {hex(crc32c_val)}")

    print("✓ CRC-32C 测试通过")



    # 测试 6: 错误检测

    print("\n【测试 6】错误检测")

    test_msg = b"Test message for CRC"

    crc32 = create_crc('CRC-32')

    original_crc = crc32.compute(test_msg)

    print(f"原始消息: {test_msg}")

    print(f"原始 CRC: {hex(original_crc)}")



    # 模拟单比特错误

    for bit_pos in [0, 8, 16, 63, 127]:

        msg_array = bytearray(test_msg)

        byte_idx = bit_pos // 8

        bit_idx = bit_pos % 8

        if byte_idx < len(msg_array):

            msg_array[byte_idx] ^= (1 << bit_idx)

            computed_crc = crc32.compute(bytes(msg_array))

            detected = computed_crc != original_crc

            print(f"  比特位置 {bit_pos} 翻转: 检测到 {detected}")



    # 测试 7: 突发错误检测

    print("\n【测试 7】突发错误检测")

    for burst_len in [1, 8, 16, 32, 64, 128]:

        analysis = crc_error_detection(32, burst_len)

        print(f"  突发长度 {burst_len}: "

              f"检测{'全部' if analysis['detects_all'] else '部分'} "

              f"(概率 {analysis['detects_probability']:.8f})")



    # 测试 8: 长消息测试

    print("\n【测试 8】长消息性能")

    import time



    crc32 = create_crc('CRC-32')

    long_msg = bytes(range(256)) * 1000  # 256KB 数据



    start = time.time()

    for _ in range(10):

        crc32.compute(long_msg)

    elapsed = time.time() - start



    print(f"256KB 消息，计算 10 次 CRC-32:")

    print(f"  总耗时: {elapsed:.4f} 秒")

    print(f"  单次: {elapsed/10*1000:.2f} ms")

    print(f"  吞吐量: {256 * 10 / elapsed:.1f} MB/s")



    # 测试 9: 比特级 vs 查表法比较

    print("\n【测试 9】比特级 vs 查表法")

    small_msg = b"Small"

    crc32 = create_crc('CRC-32')



    start = time.time()

    for _ in range(10000):

        crc32.compute_bit_by_bit(small_msg)

    bit_time = time.time() - start



    start = time.time()

    for _ in range(10000):

        crc32.compute_table_driven(small_msg)

    table_time = time.time() - start



    print(f"小消息 (5 bytes) 计算 10000 次:")

    print(f"  比特级: {bit_time:.4f} 秒")

    print(f"  查表法: {table_time:.4f} 秒")

    print(f"  加速比: {bit_time/table_time:.1f}x")



    # 测试 10: 标准配置验证

    print("\n【测试 10】标准 CRC 配置")

    test_string = b"123456789"

    for name in ['CRC-8', 'CRC-16-CCITT', 'CRC-16-IBM', 'CRC-32', 'CRC-32C']:

        crc = create_crc(name)

        val = crc.compute(test_string)

        status = "✓" if val == crc.check_value else "✗"

        print(f"  {name}: {hex(val)} (校验值: {hex(crc.check_value)}) {status}")

        assert val == crc.check_value



    print("\n" + "=" * 60)

    print("所有测试完成！")

    print("=" * 60)



    print("\n复杂度分析:")

    print("  比特级算法: O(n * width)，n=数据长度，width=CRC位宽")

    print("  查表法: O(n)，每字节查表一次")

    print("  空间: O(2^8 * width) for 字节表，或 O(2^16 * width) for 字表")

    print("  硬件实现: O(1) 每比特，只需移位寄存器和异或门")

