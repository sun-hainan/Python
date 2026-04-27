# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / arq_fec



本文件实现 arq_fec 相关的算法功能。

"""



import random

import math





class StopAndWaitARQ:

    """

    停止等待 ARQ 协议

    

    发送方发送一个帧，等待确认（ACK）后再发送下一个。

    如果超时未收到 ACK，则重传。

    """



    def __init__(self, frame_size=1460, timeout=1.0, max_retries=3):

        """

        初始化协议

        

        参数:

            frame_size: 帧大小（字节）

            timeout: 超时时间（秒）

            max_retries: 最大重传次数

        """

        self.frame_size = frame_size

        self.timeout = timeout

        self.max_retries = max_retries

        # 序列号

        self.frame_seq = 0

        # 已确认的帧序列号

        self.acked_seq = 0

        # 统计数据

        self.packets_sent = 0

        self.packets_acked = 0

        self.retransmissions = 0



    def send_frame(self, data):

        """

        发送一帧

        

        参数:

            data: 要发送的数据

        返回:

            (frame, seq): 帧和序列号

        """

        frame = {

            'seq': self.frame_seq,

            'data': data[:self.frame_size],

            'timestamp': 0  # 简化：实际应该是时间戳

        }

        self.packets_sent += 1

        return frame, self.frame_seq



    def receive_ack(self, ack_seq):

        """

        处理 ACK

        

        参数:

            ack_seq: 确认的序列号

        返回:

            success: 是否成功确认

        """

        if ack_seq == self.frame_seq:

            # 收到正确的 ACK

            self.acked_seq = self.frame_seq

            self.frame_seq = 1 - self.frame_seq  # 切换序列号

            self.packets_acked += 1

            return True

        return False



    def timeout_occurred(self):

        """超时处理"""

        self.retransmissions += 1

        return self.retransmissions <= self.max_retries



    def reset(self):

        """重置连接"""

        self.frame_seq = 0

        self.acked_seq = 0

        self.retransmissions = 0



    def get_stats(self):

        """获取统计信息"""

        return {

            'sent': self.packets_sent,

            'acked': self.packets_acked,

            'retransmissions': self.retransmissions,

            'success_rate': self.packets_acked / self.packets_sent if self.packets_sent > 0 else 0

        }





class GoBackNARQ:

    """

    回退 N 帧 ARQ 协议

    

    发送方可以连续发送 N 帧，接收方按序接收。

    如果某帧出错，该帧之后的所有帧都会被丢弃并重传。

    """



    def __init__(self, window_size=4, frame_size=1460, timeout=1.0):

        """

        初始化协议

        

        参数:

            window_size: 窗口大小 N

            frame_size: 帧大小

            timeout: 超时时间

        """

        self.window_size = window_size

        self.frame_size = frame_size

        self.timeout = timeout

        # 序列号范围（0 到 2^k - 1）

        self.seq_range = 8  # 使用 3 位序列号

        # 发送窗口

        self.send_base = 0  # 窗口起始

        self.next_seq = 0   # 下一个可用序列号

        # 已发送但未确认的帧

        self.unacked_frames = {}

        # 统计数据

        self.packets_sent = 0

        self.retransmissions = 0



    def can_send(self):

        """检查是否可以发送新帧"""

        return (self.next_seq - self.send_base) % self.seq_range < self.window_size



    def send_frame(self, data):

        """

        发送帧（如果窗口允许）

        

        参数:

            data: 数据

        返回:

            frame: 帧或 None

        """

        if not self.can_send():

            return None

        

        frame = {

            'seq': self.next_seq,

            'data': data[:self.frame_size]

        }

        

        self.unacked_frames[self.next_seq] = frame

        self.next_seq = (self.next_seq + 1) % self.seq_range

        self.packets_sent += 1

        

        return frame



    def receive_ack(self, ack_seq):

        """

        处理 ACK

        

        参数:

            ack_seq: 确认序列号

        返回:

            acked_count: 确认的帧数

        """

        acked_count = 0

        # 确认所有 seq < ack_seq 的帧

        while self.send_base != ack_seq:

            if self.send_base in self.unacked_frames:

                del self.unacked_frames[self.send_base]

                acked_count += 1

            self.send_base = (self.send_base + 1) % self.seq_range

        

        return acked_count



    def receive_nack(self, nack_seq):

        """

        处理 NACK（否定确认）

        

        参数:

            nack_seq: 出错帧的序列号

        返回:

            retransmit_from: 需要重传的起始序列号

        """

        # 回退到 NACK 指示的帧

        self.retransmissions += 1

        self.next_seq = nack_seq

        return nack_seq



    def check_timeout(self):

        """超时处理：回退到 send_base"""

        self.retransmissions += 1

        self.next_seq = self.send_base

        return self.send_base



    def get_unacked_count(self):

        """获取未确认帧数"""

        return len(self.unacked_frames)





class SelectiveRepeatARQ:

    """

    选择性重传 ARQ 协议

    

    接收方可以接受乱序的帧，只重传出错的帧。

    更复杂但效率更高。

    """



    def __init__(self, window_size=4, frame_size=1460):

        """

        初始化协议

        

        参数:

            window_size: 窗口大小

            frame_size: 帧大小

        """

        self.window_size = window_size

        self.frame_size = frame_size

        self.seq_range = 8

        # 发送窗口

        self.send_base = 0

        self.next_seq = 0

        # 接收窗口

        self.recv_base = 0

        # 接收缓冲区

        self.recv_buffer = {}

        # 已发送但未确认的帧

        self.unacked_frames = {}

        # 统计数据

        self.packets_sent = 0

        self.retransmissions = 0



    def send_frame(self, data):

        """发送帧"""

        if (self.next_seq - self.send_base) % self.seq_range >= self.window_size:

            return None

        

        frame = {

            'seq': self.next_seq,

            'data': data[:self.frame_size]

        }

        self.unacked_frames[self.next_seq] = frame

        self.next_seq = (self.next_seq + 1) % self.seq_range

        self.packets_sent += 1

        return frame



    def receive_frame(self, frame):

        """

        接收帧

        

        参数:

            frame: 收到的帧

        返回:

            action: 'accept', 'reject', 'duplicate'

        """

        seq = frame['seq']

        

        # 检查是否在接收窗口内

        if (seq - self.recv_base) % self.seq_range < self.window_size:

            if seq == self.recv_base:

                # 接受的帧

                self.recv_buffer[seq] = frame

                # 交付按序的帧

                while self.recv_base in self.recv_buffer:

                    del self.recv_buffer[self.recv_base]

                    self.recv_base = (self.recv_base + 1) % self.seq_range

                return 'accept'

            else:

                # 在窗口内但不是当前期望的帧

                self.recv_buffer[seq] = frame

                return 'accept'

        elif (seq - self.recv_base + self.seq_range) % self.seq_range >= self.window_size:

            return 'reject'  # 在窗口外

        else:

            return 'duplicate'  # 已接收过的帧



    def receive_ack(self, ack_seq):

        """处理 ACK"""

        if ack_seq in self.unacked_frames:

            del self.unacked_frames[ack_seq]

            # 移动发送窗口

            while self.send_base in self.unacked_frames:

                self.send_base = (self.send_base + 1) % self.seq_range





class ReedSolomonCodec:

    """

    Reed-Solomon 前向纠错编码

    

    RS 码是一种常用的纠错码，可以在不知道错误位置的情况下

    纠正最多 t 个错误符号。

    

    符号在 GF(2^m) 有限域上运算。

    """



    def __init__(self, m=8, t=8):

        """

        初始化编码器

        

        参数:

            m: 有限域阶数（通常为 8）

            t: 纠错能力（能纠正 t 个符号错误）

        """

        self.m = m

        self.t = t

        # 码字长度：2^m - 1

        self.n = 2**m - 1

        # 消息长度：n - 2*t

        self.k = self.n - 2 * t

        # 生成多项式

        self.gen_poly = self._compute_generator_poly()



    def _compute_generator_poly(self):

        """计算生成多项式"""

        # 简化的生成多项式

        # 实际需要复杂的有限域运算

        return [1] * (2 * self.t + 1)



    def encode(self, data):

        """

        编码数据

        

        参数:

            data: 原始数据（字节列表）

        返回:

            encoded: 编码后的数据（含纠错码）

        """

        # 简化的编码：添加奇偶校验

        # 实际 RS 编码使用复杂的矩阵乘法

        if len(data) > self.k:

            data = data[:self.k]

        

        # 添加 2t 个纠错符号

        parity = self._compute_parity(data)

        return list(data) + parity



    def _compute_parity(self, data):

        """计算奇偶校验符号"""

        # 简化的奇偶校验

        parity = []

        for i in range(2 * self.t):

            p = 0

            for j, d in enumerate(data):

                p ^= (d << (i * j)) & 0xFF

            parity.append(p & 0xFF)

        return parity



    def decode(self, received):

        """

        解码数据（并尝试纠错）

        

        参数:

            received: 接收到的数据

        返回:

            (corrected, errors): 纠错后的数据和错误数

        """

        # 简化实现：假设没有错误

        errors = 0

        return received[:self.k], errors



    def correct(self, data, error_positions, error_values):

        """

        纠正指定位置的错误

        

        参数:

            data: 数据

            error_positions: 错误位置列表

            error_values: 错误值列表

        返回:

            corrected: 纠错后的数据

        """

        corrected = list(data)

        for pos, val in zip(error_positions, error_values):

            if 0 <= pos < len(corrected):

                corrected[pos] ^= val

        return corrected





class HammingCodec:

    """

    Hamming(7,4) 纠错码

    

    每个 4 位数据块编码为 7 位码字，可以纠正任意单比特错误。

    

    编码规则：

    位置：1  2  3  4  5  6  7

    角色：P1 P2 D3 P4 D5 D6 D7

    其中 D 是数据位，P 是奇偶校验位

    """



    def __init__(self):

        """初始化 Hamming(7,4) 编码器"""

        # 奇偶校验位位置（1-indexed）

        self.parity_positions = [1, 2, 4]

        # 数据位位置

        self.data_positions = [3, 5, 6, 7]



    def encode(self, data_nibble):

        """

        编码一个半字节（4 位数据）

        

        参数:

            data_nibble: 4 位数据（0-15）

        返回:

            codeword: 7 位码字

        """

        if data_nibble < 0 or data_nibble > 15:

            raise ValueError("数据必须是 0-15 之间的 4 位值")

        

        # 将数据转换为 4 位

        bits = [(data_nibble >> i) & 1 for i in range(4)]

        

        # 构建 7 位码字（初始为 0）

        codeword = [0] * 7

        

        # 填入数据位

        data_idx = 0

        for pos in range(7):

            if (pos + 1) not in self.parity_positions:

                codeword[pos] = bits[data_idx]

                data_idx += 1

        

        # 计算奇偶校验位

        # P1: 检查位置 1,3,5,7

        p1 = codeword[0] ^ codeword[2] ^ codeword[4] ^ codeword[6]

        # P2: 检查位置 2,3,6,7

        p2 = codeword[1] ^ codeword[2] ^ codeword[5] ^ codeword[6]

        # P4: 检查位置 4,5,6,7

        p4 = codeword[3] ^ codeword[4] ^ codeword[5] ^ codeword[6]

        

        codeword[0] = p1

        codeword[1] = p2

        codeword[3] = p4

        

        return codeword



    def decode(self, codeword):

        """

        解码并纠错

        

        参数:

            codeword: 7 位码字

        返回:

            (data, corrected, error_pos): 数据位、是否被纠正、错误位置

        """

        if len(codeword) != 7:

            raise ValueError("码字必须是 7 位")

        

        # 计算 syndromes

        # S1: 检查位置 1,3,5,7

        s1 = codeword[0] ^ codeword[2] ^ codeword[4] ^ codeword[6]

        # S2: 检查位置 2,3,6,7

        s2 = codeword[1] ^ codeword[2] ^ codeword[5] ^ codeword[6]

        # S4: 检查位置 4,5,6,7

        s4 = codeword[3] ^ codeword[4] ^ codeword[5] ^ codeword[6]

        

        error_pos = s1 * 1 + s2 * 2 + s4 * 4

        

        corrected_codeword = list(codeword)

        was_corrected = False

        

        if error_pos > 0:

            # 有错误，纠正

            idx = error_pos - 1

            if 0 <= idx < 7:

                corrected_codeword[idx] ^= 1

                was_corrected = True

        

        # 提取数据位

        data_bits = []

        for pos in self.data_positions:

            data_bits.append(corrected_codeword[pos - 1])

        

        # 转换为数值

        data = 0

        for i, bit in enumerate(data_bits):

            data |= (bit << i)

        

        return data, was_corrected, error_pos





if __name__ == "__main__":

    # 测试 ARQ 协议

    print("=== ARQ 协议测试 ===\n")



    # 停止等待 ARQ

    print("--- 停止等待 ARQ ---")

    saw = StopAndWaitARQ()

    frame, seq = saw.send_frame(b"Test data")

    print(f"  发送帧: seq={seq}, data={frame['data']}")

    saw.receive_ack(0)  # 确认

    stats = saw.get_stats()

    print(f"  统计: 发送={stats['sent']}, 确认={stats['acked']}, 重传={stats['retransmissions']}")



    # Go-Back-N

    print("\n--- 回退 N 帧 ARQ ---")

    gbn = GoBackNARQ(window_size=4)

    

    print("  发送 6 个帧:")

    frames = []

    for i in range(6):

        frame = gbn.send_frame(f"Data_{i}".encode())

        if frame:

            frames.append(frame)

            print(f"    帧 {frame['seq']}: sent")

    

    print(f"  未确认帧数: {gbn.get_unacked_count()}")

    

    # 模拟 ACK

    gbn.receive_ack(2)

    print(f"  ACK(2) 后，未确认帧数: {gbn.get_unacked_count()}")



    # 选择性重传

    print("\n--- 选择性重传 ARQ ---")

    sr = SelectiveRepeatARQ(window_size=4)

    

    for i in range(5):

        frame = sr.send_frame(f"Data_{i}".encode())

        if frame:

            print(f"  发送帧 {frame['seq']}")

    

    # 接收帧（模拟乱序）

    import random

    seqs = [0, 2, 1, 3, 4]  # 乱序到达

    for seq in seqs:

        fake_frame = {'seq': seq, 'data': f'Data_{seq}'.encode()}

        action = sr.receive_frame(fake_frame)

        print(f"  接收帧 {seq}: {action}")



    # 测试 FEC

    print("\n=== FEC 前向纠错测试 ===\n")



    # Hamming(7,4)

    print("--- Hamming(7,4) 编码 ---")

    hamming = HammingCodec()

    

    test_values = [0b1010, 0b1100, 0b1111]

    for val in test_values:

        codeword = hamming.encode(val)

        print(f"  数据 {val:#04b} -> 码字 {''.join(str(b) for b in codeword)}")

        

        # 模拟错误

        error_pos = random.randint(0, 6)

        corrupted = list(codeword)

        corrupted[error_pos] ^= 1

        decoded, corrected, err_pos = hamming.decode(corrupted)

        print(f"    错误位置 {error_pos} -> 纠正位置 {err_pos}, 解码 {decoded:#04b}, 正确={decoded == val}")



    # Reed-Solomon（简化测试）

    print("\n--- Reed-Solomon 编码 ---")

    rs = ReedSolomonCodec(m=8, t=4)

    print(f"  码字长度: {rs.n}, 消息长度: {rs.k}")

    

    data = [0x41, 0x42, 0x43, 0x44, 0x45]  # "ABCDE"

    encoded = rs.encode(data)

    print(f"  原始数据: {[hex(b) for b in data]}")

    print(f"  编码后: {[hex(b) for b in encoded]}")

    

    decoded, errors = rs.decode(encoded)

    print(f"  解码: {[hex(b) for b in decoded]}, 错误数: {errors}")

