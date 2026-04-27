# -*- coding: utf-8 -*-

"""

算法实现：数据库内核 / index_compression



本文件实现 index_compression 相关的算法功能。

"""



from typing import List, Tuple, Optional

import struct



class VarintEncoder:

    """

    Varint（Variable-length Integer）编码

    使用1-9字节表示整数，值越小字节数越少

    适用于数据库索引和Google Protocol Buffers

    """

    

    @staticmethod

    def encode(value: int) -> bytes:

        """

        将整数编码为Varint字节序列

        规则：

        - 值 0-127 用1字节表示（最高位0）

        - 值 128-16383 用2字节表示

        - 值 16384-2097151 用3字节表示

        - ...以此类推

        """

        if value < 0:

            raise ValueError("Varint only supports non-negative integers")

        

        result = bytearray()

        

        while value >= 0x80:

            # 取出低7位，最高位设为1（表示后面还有字节）

            result.append((value & 0x7F) | 0x80)

            value >>= 7

        

        # 最后一个字节，最高位为0

        result.append(value & 0x7F)

        

        return bytes(result)

    

    @staticmethod

    def decode(data: bytes, offset: int = 0) -> Tuple[int, int]:

        """

        解码Varint

        返回: (解码的值, 消耗的字节数)

        """

        result = 0

        shift = 0

        bytes_consumed = 0

        

        while True:

            if offset + bytes_consumed >= len(data):

                raise ValueError("Truncated Varint")

            

            byte = data[offset + bytes_consumed]

            bytes_consumed += 1

            

            result |= (byte & 0x7F) << shift

            

            if (byte & 0x80) == 0:

                # 最高位为0，编码结束

                break

            

            shift += 7

        

        return result, bytes_consumed

    

    @staticmethod

    def encode_list(values: List[int]) -> bytes:

        """批量编码整数列表"""

        return b''.join(VarintEncoder.encode(v) for v in values)

    

    @staticmethod

    def decode_list(data: bytes) -> List[int]:

        """批量解码"""

        result = []

        offset = 0

        

        while offset < len(data):

            value, consumed = VarintEncoder.decode(data, offset)

            result.append(value)

            offset += consumed

        

        return result





class FrameOfReference:

    """

    FOR（Frame of Reference）编码

    将值减去基准值（frame），然后用Varint存储

    适用于值域紧凑的列（如年龄、日期）

    """

    

    def __init__(self, block_size: int = 128):

        self.block_size = block_size  # 每个块的元组数

    

    def encode_block(self, values: List[int]) -> Tuple[bytes, int]:

        """

        编码一个块

        返回: (编码字节, 基准值)

        """

        if not values:

            return b'', 0

        

        # 计算基准值（最小值）

        base_value = min(values)

        

        # 计算差值

        deltas = [v - base_value for v in values]

        

        # 用Varint编码差值列表

        encoded_deltas = VarintEncoder.encode_list(deltas)

        

        return encoded_deltas, base_value

    

    def decode_block(self, encoded_data: bytes, base_value: int, count: int) -> List[int]:

        """

        解码一个块

        """

        deltas = VarintEncoder.decode_list(encoded_data)

        

        if len(deltas) != count:

            raise ValueError(f"Expected {count} values, got {len(deltas)}")

        

        return [base_value + d for d in deltas]

    

    def encode(self, values: List[int]) -> Tuple[List[bytes], List[int]]:

        """

        分块编码

        返回: (编码块列表, 基准值列表)

        """

        encoded_blocks = []

        base_values = []

        

        for i in range(0, len(values), self.block_size):

            block = values[i:i + self.block_size]

            encoded, base = self.encode_block(block)

            encoded_blocks.append(encoded)

            base_values.append(base)

        

        return encoded_blocks, base_values

    

    def decode(self, encoded_blocks: List[bytes], 

               base_values: List[int]) -> List[int]:

        """分块解码"""

        result = []

        

        for encoded, base in zip(encoded_blocks, base_values):

            block_values = self.decode_block(encoded, base, self.block_size)

            result.extend(block_values)

        

        return result





class PForDelta:

    """

    PForDelta（Patched Frame of Reference Delta）编码

    改进的FOR编码，对异常值（超出当前块表示范围的）进行补丁处理

    适用于高基数列，如主键、ID

    """

    

    def __init__(self, bits_per_value: int = 8, exception_threshold: int = 2):

        self.bits_per_value = bits_per_value  # 每个值的固定位数

        self.exception_threshold = exception_threshold  # 异常阈值

        self.exception_list: List[Tuple[int, int]] = []  # (位置, 值)

    

    def _calculate_exceptions(self, deltas: List[int], bit_num: int) -> Tuple[List[int], List[Tuple[int, int]]]:

        """

        计算需要例外处理的差值

        返回: (修正后的差值列表, 例外列表)

        """

        max_normal = (1 << bit_num) - 1  # 能表示的最大正常值

        

        exceptions = []

        corrected = []

        

        for i, delta in enumerate(deltas):

            if delta > max_normal:

                exceptions.append((i, delta))

                corrected.append(0)  # 用0占位

            else:

                corrected.append(delta)

        

        return corrected, exceptions

    

    def encode(self, values: List[int]) -> bytes:

        """

        PForDelta编码

        """

        if len(values) == 0:

            return b''

        

        # 计算差值

        deltas = [values[0]]

        for i in range(1, len(values)):

            # 使用前值作为参考

            deltas.append(values[i] - values[i - 1])

        

        # 找到合适的bit数（使至少90%的值能够正常编码）

        bit_num = 1

        max_attempts = 16

        

        for attempt in range(max_attempts):

            max_normal = (1 << bit_num) - 1

            exception_count = sum(1 for d in deltas if d > max_normal)

            

            if exception_count <= len(deltas) * 0.1 or bit_num >= 32:

                break

            

            bit_num += 1

        

        # 编码

        exception_count = 0

        

        result = bytearray()

        

        # 存储bit数（1字节）

        result.append(bit_num)

        

        # 首先标记例外位置，用一个bitmap

        bitmap_size = (len(deltas) + 7) // 8

        bitmap = bytearray(bitmap_size)

        

        max_normal = (1 << bit_num) - 1

        exceptions = []

        corrected_deltas = []

        

        for i, d in enumerate(deltas):

            if d > max_normal:

                bitmap[i // 8] |= (1 << (i % 8))

                exceptions.append((i, d))

                corrected_deltas.append(0)

            else:

                corrected_deltas.append(d)

        

        result.extend(bitmap)

        

        # 编码修正后的差值

        bit_offset = 0

        current_byte = 0

        

        for delta in corrected_deltas:

            for bit in range(bit_num):

                if delta & (1 << bit):

                    current_byte |= (1 << (bit_offset % 8))

                bit_offset += 1

                if bit_offset % 8 == 0:

                    result.append(current_byte)

                    current_byte = 0

        

        if bit_offset % 8 != 0:

            result.append(current_byte)

        

        # 存储例外数量和例外值

        result.extend(len(exceptions).to_bytes(4, 'little'))

        

        for pos, value in exceptions:

            result.extend(pos.to_bytes(4, 'little'))

            result.extend(value.to_bytes(8, 'little'))

        

        return bytes(result)

    

    def decode(self, data: bytes) -> List[int]:

        """

        PForDelta解码

        """

        if len(data) == 0:

            return []

        

        pos = 0

        

        # 读取bit数

        bit_num = data[pos]

        pos += 1

        

        # 读取bitmap

        bitmap_size = (0 + 7) // 8  # 简化，假设一个块最多1024个值

        if pos + bitmap_size >= len(data):

            return []

        

        bitmap = data[pos:pos + bitmap_size]

        pos += bitmap_size

        

        # 读取压缩的差值

        values = []

        bit_offset = 0

        

        while pos < len(data):

            delta = 0

            for bit in range(bit_num):

                byte_idx = (bit_offset // 8) + pos

                bit_idx = bit_offset % 8

                

                if byte_idx < len(data):

                    if data[byte_idx] & (1 << bit_idx):

                        delta |= (1 << bit)

                

                bit_offset += 1

            

            # 检查是否是例外

            byte_idx_in_bitmap = len(values) // 8

            bit_idx_in_byte = len(values) % 8

            

            is_exception = False

            if byte_idx_in_bitmap < len(bitmap):

                if bitmap[byte_idx_in_bitmap] & (1 << bit_idx_in_byte):

                    is_exception = True

            

            if is_exception:

                # 读取例外值

                if pos + 12 <= len(data):

                    exception_pos = int.from_bytes(data[pos:pos+4], 'little')

                    exception_val = int.from_bytes(data[pos+4:pos+12], 'little')

                    pos += 12

                    values.append(exception_val)

            else:

                values.append(delta)

        

        # 还原原始值（前值累加）

        result = [values[0]] if values else []

        for i in range(1, len(values)):

            result.append(result[-1] + values[i])

        

        return result





if __name__ == "__main__":

    print("=" * 60)

    print("索引压缩算法演示")

    print("=" * 60)

    

    # Varint测试

    print("\n--- Varint 编码 ---")

    test_values = [0, 127, 128, 16383, 16384, 2097151, 2097152, 1000000]

    

    for val in test_values:

        encoded = VarintEncoder.encode(val)

        decoded, _ = VarintEncoder.decode(encoded)

        print(f"  {val:>10} -> {encoded.hex():>20} -> {decoded}")

    

    # 批量编码

    batch = [1, 127, 128, 1000, 16383, 16384]

    encoded_batch = VarintEncoder.encode_list(batch)

    decoded_batch = VarintEncoder.decode_list(encoded_batch)

    print(f"\n  批量编解码: {batch} -> {encoded_batch.hex()} -> {decoded_batch}")

    

    # Frame of Reference测试

    print("\n--- Frame of Reference 编码 ---")

    for_set = [150, 155, 160, 158, 152, 145, 162, 158, 151, 149]

    

    encoder = FrameOfReference(block_size=5)

    encoded_blocks, base_values = encoder.encode(for_set)

    

    print(f"  原始值: {for_set}")

    print(f"  基准值: {base_values}")

    print(f"  压缩后字节数: {sum(len(b) for b in encoded_blocks)}")

    

    decoded = encoder.decode(encoded_blocks, base_values)

    print(f"  解码结果: {decoded}")

    print(f"  压缩比: {len(for_set) * 8} bit vs {sum(len(b) * 8 for b in encoded_blocks)} bit")

    

    # PForDelta测试

    print("\n--- PForDelta 编码 ---")

    pfor = PForDelta(bits_per_value=8)

    

    test_data = [100, 102, 105, 108, 200, 203, 205, 208, 101, 103]

    encoded_pfor = pfor.encode(test_data)

    

    print(f"  原始数据: {test_data}")

    print(f"  压缩后: {encoded_pfor.hex()}")

    print(f"  压缩后大小: {len(encoded_pfor)} bytes")

    print(f"  原始大小: {len(test_data)} bytes (假设8字节/值)")

    

    decoded_pfor = pfor.decode(encoded_pfor)

    print(f"  解码结果: {decoded_pfor}")

    print(f"  解码正确: {decoded_pfor == test_data}")

