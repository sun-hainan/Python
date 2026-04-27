# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / http2_framing



本文件实现 http2_framing 相关的算法功能。

"""



import struct





class HTTP2Frame:

    """HTTP/2 帧类"""



    # 帧类型

    TYPE_DATA = 0x0

    TYPE_HEADERS = 0x1

    TYPE_PRIORITY = 0x2

    TYPE_RST_STREAM = 0x3

    TYPE_SETTINGS = 0x4

    TYPE_PING = 0x6

    TYPE_GOAWAY = 0x7

    TYPE_WINDOW_UPDATE = 0x8

    TYPE_CONTINUATION = 0x9



    # 帧类型的字符串表示

    FRAME_TYPE_NAMES = {

        0x0: "DATA",

        0x1: "HEADERS",

        0x2: "PRIORITY",

        0x3: "RST_STREAM",

        0x4: "SETTINGS",

        0x5: "PING",

        0x6: "PING",

        0x7: "GOAWAY",

        0x8: "WINDOW_UPDATE",

        0x9: "CONTINUATION",

    }



    def __init__(self):

        # length: 负载长度（3字节，24位）

        self.length = 0

        # type: 帧类型（1字节）

        self.type = 0

        # flags: 标志位（1字节）

        self.flags = 0

        # reserved: 保留位（1位）

        # stream_identifier: 流标识符（31位）

        self.stream_id = 0

        # payload: 帧负载

        self.payload = b''



    @staticmethod

    def parse(data):

        """

        解析 HTTP/2 帧数据

        

        参数:

            data: 原始帧数据（至少9字节）

        返回:

            frame: HTTP2Frame 对象

        """

        if len(data) < 9:

            return None

        

        frame = HTTP2Frame()

        

        # 前3字节：长度（大端序）

        frame.length = (data[0] << 16) | (data[1] << 8) | data[2]

        

        # 第4字节：类型

        frame.type = data[3]

        

        # 第5字节：标志位

        frame.flags = data[4]

        

        # 第6-9字节：流标识符（高1位为保留位）

        frame.stream_id = struct.unpack('>I', data[5:9])[0] & 0x7FFFFFFF

        

        # 负载

        if len(data) >= 9 + frame.length:

            frame.payload = data[9:9 + frame.length]

        else:

            frame.payload = data[9:]

        

        return frame



    def serialize(self):

        """

        序列化帧为字节数据

        

        返回:

            data: 完整的帧字节数据

        """

        # 9字节头

        header = bytearray(9)

        

        # 长度（3字节）

        header[0] = (self.length >> 16) & 0xFF

        header[1] = (self.length >> 8) & 0xFF

        header[2] = self.length & 0xFF

        

        # 类型

        header[3] = self.type & 0xFF

        

        # 标志位

        header[4] = self.flags & 0xFF

        

        # 流标识符（31位，高位保留位为0）

        struct.pack_into('>I', header, 5, self.stream_id & 0x7FFFFFFF)

        

        return bytes(header) + self.payload



    def __str__(self):

        """返回帧的可读描述"""

        type_name = self.FRAME_TYPE_NAMES.get(self.type, f"0x{self.type:02x}")

        return (f"HTTP2Frame(type={type_name}, length={self.length}, "

                f"flags=0x{self.flags:02x}, stream_id={self.stream_id})")





class HTTP2Parser:

    """HTTP/2 帧解析器"""



    # HPACK 静态表索引范围

    STATIC_TABLE = {

        1: (":authority', ''"),

        2: (":method", "GET"),

        3: (":method", "POST"),

        4: (":path", "/"),

        5: (":path", "/index.html"),

        6: (":scheme", "http"),

        7: (":scheme", "https"),

        8: (":status", "200"),

        9: (":status", "204"),

        10: (":status", "206"),

        11: (":status", "304"),

        12: (":status", "400"),

        13: (":status", "404"),

        14: (":status", "500"),

    }



    def __init__(self):

        # 动态表（表索引从 61 开始）

        self.dynamic_table = []

        self.dynamic_table_size = 0

        self.max_dynamic_table_size = 4096



    def decode_integer(self, data, offset, prefix_bits):

        """

        解码 HPACK 整数

        

        参数:

            data: 数据字节

            offset: 起始偏移

            prefix_bits: 前缀位数

        返回:

            (value, new_offset): 解码后的值和新偏移

        """

        max_prefix = (1 << prefix_bits) - 1

        value = data[offset] & max_prefix

        offset += 1

        

        if value < max_prefix:

            return value, offset

        

        # 扩展编码

        m = 0

        while True:

            b = data[offset]

            offset += 1

            value += (b & 0x7F) << m

            m += 7

            if not (b & 0x80):

                break

        

        return value, offset



    def decode_string(self, data, offset):

        """

        解码 HPACK 字符串

        

        参数:

            data: 数据字节

            offset: 起始偏移

        返回:

            (string, new_offset): 解码后的字符串和新偏移

        """

        if offset >= len(data):

            return "", offset

        

        # 读取 huffman 标志和字符串长度

        first_byte = data[offset]

        huffman = bool(first_byte & 0x80)

        length, offset = self.decode_integer(data, offset, 7)

        

        if offset + length > len(data):

            return "", len(data)

        

        str_data = data[offset:offset+length]

        offset += length

        

        # 简化：不做 Huffman 解码

        if huffman:

            # 实际应该用 Huffman 表解码

            return str_data.decode('utf-8', errors='replace'), offset

        else:

            return str_data.decode('utf-8', errors='replace'), offset



    def decode_header_block(self, block):

        """

        解码完整的头部块

        

        参数:

            block: 头部块数据

        返回:

            headers: 头部字典

        """

        headers = {}

        offset = 0

        

        while offset < len(block):

            first_byte = block[offset]

            offset += 1

            

            # 索引了头部

            if first_byte & 0x40:

                # 索引了静态或动态表

                index, offset = self.decode_integer(block, offset - 1, 6)

                if index == 0:

                    # 索引为0，需要读取名称和值

                    name, offset = self.decode_string(block, offset)

                    value, offset = self.decode_string(block, offset)

                    headers[name] = value

                elif index in self.STATIC_TABLE:

                    name, base_value = self.STATIC_TABLE[index]

                    if offset < len(block) and block[offset] & 0x80:

                        # 有值，直接用基础值

                        offset += 1

                        value = base_value

                    else:

                        value, offset = self.decode_string(block, offset)

                    headers[name] = value

            elif first_byte & 0x20:

                # 动态表大小更新

                index, offset = self.decode_integer(block, offset - 1, 4)

                # 忽略简化

            else:

                # _literal header field without indexing

                name, offset = self.decode_string(block, offset)

                value, offset = self.decode_string(block, offset)

                headers[name] = value

        

        return headers





class HTTP2Connection:

    """HTTP/2 连接状态管理"""



    def __init__(self):

        # 下一可用的流 ID（客户端用奇数，服务端用偶数）

        self.next_stream_id = 1

        # 流表（stream_id -> StreamState）

        self.streams = {}

        # 设置帧

        self.settings = {

            'HEADER_TABLE_SIZE': 4096,

            'ENABLE_PUSH': 1,

            'MAX_CONCURRENT_STREAMS': float('inf'),

            'INITIAL_WINDOW_SIZE': 65535,

            'MAX_FRAME_SIZE': 16384,

        }

        # 认可设置（收到对方的设置确认）

        self.acknowledged_settings = False

        # 流量控制窗口

        self.remote_window = 65535

        self.local_window = 65535



    def create_stream(self):

        """创建新流"""

        stream_id = self.next_stream_id

        self.next_stream_id += 2

        self.streams[stream_id] = {

            'id': stream_id,

            'state': 'open',  # idle, open, half_closed, closed

            'data': b'',

            'headers': {},

        }

        return stream_id



    def process_frame(self, frame):

        """

        处理收到的帧

        

        参数:

            frame: HTTP2Frame 对象

        返回:

            response_frames: 响应帧列表

        """

        responses = []

        

        if frame.type == HTTP2Frame.TYPE_SETTINGS:

            if not (frame.flags & 0x01):  # 不是 ACK

                # 应用设置

                self._apply_settings(frame.payload)

                # 发送设置 ACK

                ack_frame = HTTP2Frame()

                ack_frame.type = HTTP2Frame.TYPE_SETTINGS

                ack_frame.flags = 0x01  # ACK

                ack_frame.stream_id = 0

                responses.append(ack_frame)

        

        elif frame.type == HTTP2Frame.TYPE_HEADERS:

            # 解码头部

            parser = HTTP2Parser()

            headers = parser.decode_header_block(frame.payload)

            self.streams[frame.stream_id]['headers'] = headers

        

        elif frame.type == HTTP2Frame.TYPE_DATA:

            # 接收数据

            if frame.stream_id in self.streams:

                self.streams[frame.stream_id]['data'] += frame.payload

                # 发送窗口更新

                if frame.flags & 0x08:  # END_STREAM

                    pass

        

        return responses



    def _apply_settings(self, payload):

        """应用 SETTINGS 帧中的参数"""

        offset = 0

        while offset < len(payload):

            if offset + 4 > len(payload):

                break

            identifier = struct.unpack('>H', payload[offset:offset+2])[0]

            value = struct.unpack('>I', payload[offset+2:offset+6])[0]

            offset += 6

            

            if identifier == 0x01:

                self.settings['SETTINGS_HEADER_TABLE_SIZE'] = value

            elif identifier == 0x02:

                self.settings['ENABLE_PUSH'] = value

            elif identifier == 0x03:

                self.settings['MAX_CONCURRENT_STREAMS'] = value

            elif identifier == 0x04:

                self.settings['INITIAL_WINDOW_SIZE'] = value

            elif identifier == 0x05:

                self.settings['MAX_FRAME_SIZE'] = value





if __name__ == "__main__":

    # 测试 HTTP/2 帧解析

    print("=== HTTP/2 帧解析测试 ===")

    

    # 构建测试帧

    frame = HTTP2Frame()

    frame.type = HTTP2Frame.TYPE_HEADERS

    frame.flags = 0x04  # END_HEADERS

    frame.stream_id = 1

    frame.payload = b'\x82\x86\x84\x41\x0f\x77\x77\x77\x2e\x65\x78\x61\x6d\x70\x6c\x65\x2e\x63\x6f\x6d'

    

    print(f"原始帧: {frame}")

    

    # 序列化

    data = frame.serialize()

    print(f"序列化后: {len(data)} 字节, {data.hex()}")

    

    # 解析

    parsed = HTTP2Frame.parse(data)

    print(f"解析后: {parsed}")

    print(f"负载长度: {parsed.length}")

    print(f"流ID: {parsed.stream_id}")

    

    # 解析头部

    parser = HTTP2Parser()

    headers = parser.decode_header_block(parsed.payload)

    print(f"解码头部: {headers}")

    

    # 测试连接

    print("\n=== HTTP/2 连接测试 ===")

    conn = HTTP2Connection()

    

    # 创建流

    stream_id = conn.create_stream()

    print(f"创建流: ID={stream_id}")

    

    # 构建并处理 SETTINGS 帧

    settings_frame = HTTP2Frame()

    settings_frame.type = HTTP2Frame.TYPE_SETTINGS

    settings_frame.stream_id = 0

    

    responses = conn.process_frame(settings_frame)

    print(f"处理 SETTINGS，收到响应帧: {len(responses)}")

    for resp in responses:

        print(f"  {resp}")

