# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / http2_framing

本文件实现 http2_framing 相关的算法功能。
"""

import struct
from enum import IntEnum
from dataclasses import dataclass
from typing import List, Dict, Optional


class HTTP2FrameType(IntEnum):
    """HTTP/2帧类型"""
    DATA = 0x00
    HEADERS = 0x01
    PRIORITY = 0x02
    RST_STREAM = 0x03
    SETTINGS = 0x04
    PUSH_PROMISE = 0x05
    PING = 0x06
    GOAWAY = 0x07
    WINDOW_UPDATE = 0x08
    CONTINUATION = 0x09


class HTTP2Flag(IntEnum):
    """HTTP/2帧标志位"""
    # DATA帧 flags
    DATA_END_STREAM = 0x01
    DATA_PADDED = 0x08
    
    # HEADERS帧 flags
    HEADERS_END_STREAM = 0x01
    HEADERS_END_HEADERS = 0x04
    HEADERS_PADDED = 0x08
    HEADERS_PRIORITY = 0x20
    
    # SETTINGS帧 flags
    SETTINGS_ACK = 0x01
    
    # PING帧 flags
    PING_ACK = 0x01


class HTTP2Setting(IntEnum):
    """HTTP/2 SETTINGS参数"""
    SETTINGS_HEADER_TABLE_SIZE = 0x01
    SETTINGS_ENABLE_PUSH = 0x02
    SETTINGS_MAX_CONCURRENT_STREAMS = 0x03
    SETTINGS_INITIAL_WINDOW_SIZE = 0x04
    SETTINGS_MAX_FRAME_SIZE = 0x05
    SETTINGS_MAX_HEADER_LIST_SIZE = 0x06


@dataclass
class HTTP2Frame:
    """HTTP/2帧结构"""
    length: int  # 载荷长度（3字节，24位）
    type: HTTP2FrameType  # 帧类型
    flags: int  # 标志位
    stream_id: int  # 流ID（31位）
    payload: bytes  # 载荷数据
    
    def to_bytes(self) -> bytes:
        """
        将帧序列化为字节流
        
        Returns:
            序列化后的字节
        """
        # Length: 3字节大端序
        header = struct.pack("!I", self.length)[1:]
        
        # Type: 1字节
        header += bytes([self.type])
        
        # Flags: 1字节
        header += bytes([self.flags])
        
        # Stream ID: 4字节（最高位为0）
        header += struct.pack("!I", self.stream_id & 0x7FFFFFFF)
        
        return header + self.payload
    
    @classmethod
    def parse(cls, data: bytes, offset: int = 0) -> tuple:
        """
        解析帧数据
        
        Args:
            data: 原始数据
            offset: 解析起始位置
        
        Returns:
            (frame, bytes_consumed)
        """
        if len(data) < 9:
            return None, 0
        
        # 解析帧头
        length = struct.unpack("!I", b'\x00' + data[offset:offset+3])[0]
        frame_type = HTTP2FrameType(data[offset + 3])
        flags = data[offset + 4]
        stream_id = struct.unpack("!I", data[offset+5:offset+9])[0] & 0x7FFFFFFF
        
        # 检查数据完整性
        if len(data) < offset + 9 + length:
            return None, 0
        
        payload = data[offset+9:offset+9+length]
        frame = cls(length, frame_type, flags, stream_id, payload)
        return frame, 9 + length


class HTTP2HPACK:
    """
    HPACK：HTTP/2头部压缩
    
    使用动态表和静态表进行整数解码和字符串字面量编码
    """
    
    # 静态表（部分）
    STATIC_TABLE = {
        (":authority",): 1,
        (":method", "GET"): 2,
        (":method", "POST"): 3,
        (":path", "/"): 4,
        (":path", "/index.html"): 5,
        (":scheme", "http"): 6,
        (":scheme", "https"): 7,
        (":status", "200"): 8,
        (":status", "204"): 9,
        (":status", "206"): 10,
        (":status", "304"): 11,
        (":status", "400"): 12,
        (":status", "404"): 13,
        (":status", "500"): 14,
        ("accept-charset",): 15,
        ("content-encoding", "gzip"): 16,
        ("content-type", "application/json"): 17,
    }
    
    def __init__(self):
        self.dynamic_table = []  # 动态表 [(name, value), ...]
        self.max_table_size = 4096  # 最大表大小
        self.current_size = 0
    
    def decode_integer(self, data: bytes, offset: int, prefix_bits: int) -> tuple:
        """
        解码整数（前缀编码）
        
        Args:
            data: 数据
            offset: 起始偏移
            prefix_bits: 前缀位数
        
        Returns:
            (value, bytes_consumed)
        """
        prefix_mask = (1 << prefix_bits) - 1
        value = data[offset] & prefix_mask
        offset += 1
        
        if value < (1 << prefix_bits) - 1:
            return value, 1
        
        m = 0
        while True:
            b = data[offset]
            value += (b & 0x7F) << (7 * m)
            offset += 1
            m += 1
            
            if not (b & 0x80):
                break
            
            if offset >= len(data):
                return None, 0
        
        return value, offset - (offset - m * 7 - 1)
    
    def encode_integer(self, value: int, prefix_bits: int) -> bytes:
        """
        编码整数
        
        Args:
            value: 要编码的值
            prefix_bits: 前缀位数
        
        Returns:
            编码后的字节
        """
        prefix_max = (1 << prefix_bits) - 1
        
        if value < prefix_max:
            return bytes([value])
        
        result = bytes([prefix_max])
        value -= prefix_max
        
        while value >= 128:
            result += bytes([(value & 0x7F) | 0x80])
            value >>= 7
        
        result += bytes([value])
        return result
    
    def decode_string(self, data: bytes, offset: int) -> tuple:
        """
        解码字符串字面量
        
        Args:
            data: 数据
            offset: 起始偏移
        
        Returns:
            (string_value, bytes_consumed)
        """
        # 读取字符串长度
        length, consumed = self.decode_integer(data, offset, 7)
        offset += consumed
        
        # 检查Huffman编码
        huffman_flag = data[offset - 1] & 0x80
        
        if huffman_flag:
            # Huffman解码（简化）
            raw_data = data[offset:offset+length]
            # 简化：假设未压缩
            string_val = raw_data.decode('utf-8')
        else:
            string_val = data[offset:offset+length].decode('utf-8')
        
        return string_val, consumed + length
    
    def decode_header_block(self, block: bytes) -> Dict[str, str]:
        """
        解码头部块
        
        Args:
            block: 编码的头部数据
        
        Returns:
            头部字典
        """
        headers = {}
        offset = 0
        
        while offset < len(block):
            # 读取索引
            first_byte = block[offset]
            
            if first_byte & 0x80:
                # 索引头部
                index, consumed = self.decode_integer(block, offset, 7)
                offset += consumed
                
                if index == 0:
                    # 猎鹰索引=0，需要引用动态表
                    name_len, consumed = self.decode_integer(block, offset, 7)
                    offset += consumed
                    name = block[offset:offset+name_len].decode('utf-8')
                    offset += name_len
                    
                    value_len, consumed = self.decode_integer(block, offset, 7)
                    offset += consumed
                    value = block[offset:offset+value_len].decode('utf-8')
                    offset += value_len
                    
                    headers[name] = value
                else:
                    # 查找静态/动态表
                    if index < len(self.STATIC_TABLE):
                        headers["<indexed>"] = str(index)
            
            elif first_byte & 0x40:
                # 字面量带索引
                index, consumed = self.decode_integer(block, offset, 6)
                offset += consumed
                
                # 后续解码字面量
                name_len, consumed = self.decode_integer(block, offset, 7)
                offset += consumed
                name = block[offset:offset+name_len].decode('utf-8')
                offset += name_len
                
                value_len, consumed = self.decode_integer(block, offset, 7)
                offset += consumed
                value = block[offset:offset+value_len].decode('utf-8')
                offset += value_len
                
                headers[name] = value
            
            else:
                # 其他情况
                offset += 1
        
        return headers


def parse_http2_frames(data: bytes) -> List[HTTP2Frame]:
    """
    解析HTTP/2数据流中的所有帧
    
    Args:
        data: 原始字节数据
    
    Returns:
        帧列表
    """
    frames = []
    offset = 0
    
    while offset < len(data):
        frame, consumed = HTTP2Frame.parse(data, offset)
        if frame is None:
            break
        frames.append(frame)
        offset += consumed
    
    return frames


def build_headers_frame(stream_id: int, headers: Dict[str, str], 
                        end_stream: bool = False, end_headers: bool = True) -> HTTP2Frame:
    """
    构建HEADERS帧
    
    Args:
        stream_id: 流ID
        headers: 头部字典
        end_stream: 是否结束流
        end_headers: 是否结束头部块
    
    Returns:
        HEADERS帧
    """
    hpack = HTTP2HPACK()
    
    # 编码头部
    encoded = b""
    for name, value in headers.items():
        encoded += hpack.encode_integer(62, 6)  # 字面量带新增名称
        encoded += hpack.encode_integer(len(name), 7)
        encoded += name.encode('utf-8')
        encoded += hpack.encode_integer(len(value), 7)
        encoded += value.encode('utf-8')
    
    flags = 0
    if end_stream:
        flags |= HTTP2Flag.HEADERS_END_STREAM
    if end_headers:
        flags |= HTTP2Flag.HEADERS_END_HEADERS
    
    return HTTP2Frame(len(encoded), HTTP2FrameType.HEADERS, flags, stream_id, encoded)


def build_data_frame(stream_id: int, data: bytes, 
                      end_stream: bool = True, padded: bool = False) -> HTTP2Frame:
    """
    构建DATA帧
    
    Args:
        stream_id: 流ID
        data: 数据载荷
        end_stream: 是否结束流
        padded: 是否添加填充
    
    Returns:
        DATA帧
    """
    flags = 0
    payload = data
    
    if padded:
        flags |= HTTP2Flag.DATA_PADDED
        pad_len = 10  # 简化：固定填充长度
        payload = bytes([pad_len]) + data + bytes(pad_len)
    
    if end_stream:
        flags |= HTTP2Flag.DATA_END_STREAM
    
    return HTTP2Frame(len(payload), HTTP2FrameType.DATA, flags, stream_id, payload)


def build_settings_frame(settings: Dict[int, int], ack: bool = False) -> HTTP2Frame:
    """
    构建SETTINGS帧
    
    Args:
        settings: 设置参数字典
        ack: 是否为ACK帧
    
    Returns:
        SETTINGS帧
    """
    payload = b""
    
    if ack:
        flags = HTTP2Flag.SETTINGS_ACK
    else:
        flags = 0
        for setting_id, value in settings.items():
            payload += struct.pack("!HI", setting_id, value)
    
    return HTTP2Frame(len(payload), HTTP2FrameType.SETTINGS, flags, 0, payload)


def build_window_update_frame(stream_id: int, increment: int) -> HTTP2Frame:
    """
    构建WINDOW_UPDATE帧
    
    Args:
        stream_id: 流ID（0表示连接级）
        increment: 窗口增量
    
    Returns:
        WINDOW_UPDATE帧
    """
    payload = struct.pack("!I", increment & 0x7FFFFFFF)
    return HTTP2Frame(len(payload), HTTP2FrameType.WINDOW_UPDATE, 0, stream_id, payload)


def demo_frame_structure():
    """
    演示HTTP/2帧结构
    """
    print("=== HTTP/2 帧结构演示 ===\n")
    
    # 构造HEADERS帧
    headers = {
        ":method": "GET",
        ":path": "/",
        ":scheme": "https",
        "host": "example.com",
    }
    
    frame = build_headers_frame(stream_id=1, headers=headers)
    data = frame.to_bytes()
    
    print("1. HEADERS帧结构:")
    print(f"   帧长度: {frame.length} bytes")
    print(f"   帧类型: {frame.type.name} (0x{frame.type:02x})")
    print(f"   标志位: 0x{frame.flags:02x}")
    print(f"   流ID: {frame.stream_id}")
    print(f"   总帧大小: {len(data)} bytes")
    
    # 解析验证
    parsed, _ = HTTP2Frame.parse(data)
    print(f"\n2. 帧解析验证:")
    print(f"   解析成功: {parsed.type == frame.type}")
    print(f"   流ID匹配: {parsed.stream_id == frame.stream_id}")
    
    # 构造DATA帧
    data_payload = b"Hello, HTTP/2!"
    data_frame = build_data_frame(stream_id=1, data=data_payload)
    print(f"\n3. DATA帧:")
    print(f"   数据: {data_payload}")
    print(f"   帧大小: {len(data_frame.to_bytes())} bytes")
    
    # 构造SETTINGS帧
    settings = {
        HTTP2Setting.SETTINGS_MAX_CONCURRENT_STREAMS: 100,
        HTTP2Setting.SETTINGS_INITIAL_WINDOW_SIZE: 6291456,  # 6MB
    }
    settings_frame = build_settings_frame(settings)
    print(f"\n4. SETTINGS帧:")
    print(f"   设置项数: {len(settings)}")
    for sid, val in settings.items():
        print(f"     {sid.name}: {val}")
    
    # 构造WINDOW_UPDATE帧
    wu_frame = build_window_update_frame(stream_id=1, increment=65535)
    print(f"\n5. WINDOW_UPDATE帧:")
    print(f"   流ID: {wu_frame.stream_id}")
    print(f"   增量: {65535}")


def demo_multiplexing():
    """
    演示HTTP/2流多路复用
    """
    print("\n=== HTTP/2 流多路复用演示 ===\n")
    
    # 模拟两个并发流
    frames = []
    
    # 流1: GET请求
    frames.append(build_headers_frame(1, {":method": "GET", ":path": "/", ":scheme": "https"}, end_stream=True))
    frames.append(build_data_frame(1, b"Stream 1 response data", end_stream=True))
    
    # 流2: POST请求
    frames.append(build_headers_frame(3, {":method": "POST", ":path": "/submit", ":scheme": "https"}, end_stream=False))
    frames.append(build_data_frame(3, b"POST data here", end_stream=True))
    
    # 交织发送（模拟多路复用）
    interleaved = b""
    for frame in frames:
        interleaved += frame.to_bytes()
    
    print(f"总帧数: {len(frames)}")
    print(f"总字节数: {len(interleaved)}")
    
    # 解析验证
    parsed_frames = parse_http2_frames(interleaved)
    print(f"\n解析得到帧数: {len(parsed_frames)}")
    
    stream_ids = [f.stream_id for f in parsed_frames]
    print(f"流ID序列: {stream_ids}")


def demo_hpack():
    """
    演示HPACK压缩
    """
    print("\n=== HPACK 压缩演示 ===\n")
    
    hpack = HTTP2HPACK()
    
    headers = {
        ":method": "GET",
        ":path": "/index.html",
        ":scheme": "https",
        ":authority": "example.com",
        "user-agent": "HTTP/2 Client",
        "accept": "*/*",
    }
    
    # 编码头部
    encoded = b""
    for name, value in headers.items():
        encoded += hpack.encode_integer(62, 6)  # 字面量带新增
        encoded += hpack.encode_integer(len(name), 7)
        encoded += name.encode('utf-8')
        encoded += hpack.encode_integer(len(value), 7)
        encoded += value.encode('utf-8')
    
    print(f"原始头部数: {len(headers)}")
    print(f"原始大小估算: ~{sum(len(k)+len(v) for k,v in headers.items()) + len(headers)*2} bytes")
    print(f"HPACK编码后: {len(encoded)} bytes")
    print(f"压缩率: {len(encoded)/(sum(len(k)+len(v) for k,v in headers.items())):.2f}")


if __name__ == "__main__":
    print("=" * 60)
    print("HTTP/2 帧解析与构造")
    print("=" * 60)
    
    # 帧结构演示
    demo_frame_structure()
    
    # 多路复用演示
    demo_multiplexing()
    
    # HPACK压缩演示
    demo_hpack()
    
    # 总结
    print("\n" + "=" * 60)
    print("HTTP/2 帧类型总结:")
    print("=" * 60)
    print("""
| 帧类型       | 类型值 | 用途                           |
|-------------|-------|--------------------------------|
| DATA        | 0x00  | 传输应用数据                    |
| HEADERS     | 0x01  | 传输头部信息                    |
| PRIORITY    | 0x02  | 指定/更改流优先级                |
| RST_STREAM  | 0x03  | 取消流                          |
| SETTINGS    | 0x04  | 连接级参数协商                  |
| PUSH_PROMISE| 0x05  | 服务器推送                      |
| PING        | 0x06  | 测量往返时间                    |
| GOAWAY      | 0x07  | 优雅关闭连接                   |
| WINDOW_UPDATE| 0x08 | 流量控制窗口更新                |
| CONTINUATION| 0x09  | 延续HEADERS块                  |

关键特性:
- 二进制分帧：所有数据分解为二进制帧
- 流多路复用：多个流共享一个TCP连接
- 头部压缩：使用HPACK减少头部开销
- 流控制：WINDOW_UPDATE实现流量控制
""")
