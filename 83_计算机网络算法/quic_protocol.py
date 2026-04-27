# -*- coding: utf-8 -*-

"""

算法实现：计算机网络算法 / quic_protocol



本文件实现 quic_protocol 相关的算法功能。

"""



import struct

import random

import hashlib

import time





class QUICConnection:

    """QUIC 连接类"""



    # QUIC 包类型

    TYPE_INITIAL = 0x0

    TYPE_HANDSHAKE = 0x1

    TYPE_0RTT = 0x2

    TYPE_SHORT = 0x3



    def __init__(self, conn_id_len=8):

        # conn_id_len: 连接 ID 长度（字节）

        self.conn_id_len = conn_id_len

        # dcid: 目标连接 ID

        self.dcid = self._generate_conn_id()

        # scid: 源连接 ID

        self.scid = self._generate_conn_id()

        # scid_len: 源连接 ID 长度

        self.scid_len = conn_id_len

        # dcid_len: 目标连接 ID 长度

        self.dcid_len = conn_id_len

        # packet_number: 当前包序号

        self.packet_number = 0

        # 最大数据包序号

        self.max_packet_number = 2**62 - 1

        # 密钥阶段（0=初始，1=握手，2=0-RTT，3=1-RTT）

        self.key_phase = 0

        # 连接状态

        self.state = "init"

        # 流表（stream_id -> Stream）

        self.streams = {}

        # 下一可用的流 ID（客户端用偶数，服务端用奇数）

        self.next_stream_id = 0

        # 确认延迟（ACK）

        self.ack_delay = 0

        # 初始令牌（用于地址验证）

        self.token = b""

        # 乐观地址认证令牌

        self.opts_token = b""

        # 加密密钥（简化版）

        self.crypto_stream = b""



    def _generate_conn_id(self):

        """生成随机连接 ID"""

        return bytes([random.randint(0, 255) for _ in range(self.conn_id_len)])



    def _parse_header(self, packet):

        """

        解析 QUIC 包头

        

        参数:

            packet: 原始数据包字节

        返回:

            header_info: 解析后的头部信息字典

        """

        if len(packet) < 5:

            return None

        

        # 第一个字节：包类型和标志位

        first_byte = packet[0]

        # 固定位（必须为1）

        if not (first_byte & 0x40):

            return None

        

        # 提取包类型（前2位）

        packet_type = (first_byte & 0x30) >> 4

        

        # 提取连接 ID 长度（DCI 长度，在字节1）

        dcid_len = packet[1] if len(packet) > 1 else 0

        

        header = {

            'type': packet_type,

            'dcid': packet[2:2+dcid_len] if len(packet) > 2+dcid_len else b"",

            'scid_len': 0,

            'scid': b"",

            'pn_len': 1,  # 默认

        }

        

        offset = 2 + dcid_len

        

        # 长包有 SCID

        if packet_type in (self.TYPE_INITIAL, self.TYPE_HANDSHAKE, self.TYPE_0RTT):

            if len(packet) > offset:

                header['scid_len'] = packet[offset]

                offset += 1

                header['scid'] = packet[offset:offset+header['scid_len']]

                offset += header['scid_len']

        

        return header



    def _build_header(self, packet_type, dcid, scid, pn):

        """

        构建 QUIC 包头

        

        参数:

            packet_type: 包类型

            dcid: 目标连接 ID

            scid: 源连接 ID

            pn: 包序号

        返回:

            header_bytes: 包头字节

        """

        first_byte = 0x40  # 固定位

        first_byte |= (packet_type & 0x3) << 4

        

        # 构建包头

        header = bytearray()

        header.append(first_byte)

        header.append(len(dcid))  # DCID 长度

        header.extend(dcid)  # DCID

        

        if packet_type in (self.TYPE_INITIAL, self.TYPE_HANDSHAKE, self.TYPE_0RTT):

            header.append(len(scid))  # SCID 长度

            header.extend(scid)  # SCID

        

        # 包序号（1-4 字节，可变长）

        header.append(pn & 0xFF)

        

        return bytes(header)



    def build_packet(self, packet_type, payload):

        """

        构建完整的 QUIC 数据包

        

        参数:

            packet_type: 包类型

            payload: 负载数据

        返回:

            packet: 完整数据包

        """

        # 包头

        header = self._build_header(

            packet_type,

            self.dcid,

            self.scid,

            self.packet_number

        )

        

        # 简化的负载（无加密）

        packet = header + payload

        

        # 更新包序号

        self.packet_number = (self.packet_number + 1) % (2**62)

        

        return packet



    def parse_packet(self, packet):

        """

        解析收到的 QUIC 数据包

        

        参数:

            packet: 原始数据包

        返回:

            parsed: 解析后的数据包信息

        """

        header = self._parse_header(packet)

        if not header:

            return None

        

        pn_len = header.get('pn_len', 1)

        header_len = 2 + header.get('dcid', b"").__len__() + pn_len

        

        if header['type'] in (self.TYPE_INITIAL, self.TYPE_HANDSHAKE, self.TYPE_0RTT):

            header_len += 1 + header.get('scid_len', 0)

        

        payload = packet[header_len:]

        

        return {

            'header': header,

            'payload': payload,

            'packet_number': 0,  # 简化

        }



    def create_stream(self, bidirectional=True):

        """

        创建新的 QUIC 流

        

        参数:

            bidirectional: 是否为双向流

        返回:

            stream_id: 新建的流 ID

        """

        # 客户端流 ID 为偶数，服务端为奇数

        stream_id = self.next_stream_id

        if stream_id % 2 == 0 and not bidirectional:

            stream_id += 1

        self.next_stream_id += 2

        

        self.streams[stream_id] = {

            'id': stream_id,

            'bidirectional': bidirectional,

            'data': b'',

            'offset': 0,

            'fin': False,

        }

        

        return stream_id



    def send_data(self, stream_id, data, fin=False):

        """

        发送流数据

        

        参数:

            stream_id: 流 ID

            data: 要发送的数据

            fin: 是否结束流

        返回:

            frames: 要发送的帧列表

        """

        if stream_id not in self.streams:

            return []

        

        stream = self.streams[stream_id]

        stream['data'] += data

        stream['offset'] += len(data)

        stream['fin'] = fin

        

        # 构建 STREAM 帧（简化）

        frames = []

        

        # STREAM 帧格式：类型(1) + 流ID(varint) + 偏移(varint) + 数据

        frame_type = 0x08 if stream['fin'] else 0x09

        

        frames.append({

            'type': 'STREAM',

            'stream_id': stream_id,

            'offset': stream['offset'] - len(data),

            'data': data,

            'fin': fin

        })

        

        return frames



    def recv_data(self, stream_id, data, offset, fin):

        """

        接收流数据

        

        参数:

            stream_id: 流 ID

            data: 收到的数据

            offset: 数据偏移

            fin: 是否结束

        """

        if stream_id not in self.streams:

            self.streams[stream_id] = {

                'id': stream_id,

                'bidirectional': True,

                'data': b'',

                'offset': 0,

                'fin': False,

            }

        

        stream = self.streams[stream_id]

        # 按偏移量排序存储（简化实现）

        if offset == len(stream['data']):

            stream['data'] += data

        stream['offset'] = max(stream['offset'], offset + len(data))

        stream['fin'] = fin





if __name__ == "__main__":

    # 测试 QUIC 连接

    conn = QUICConnection(conn_id_len=8)

    

    print("=== QUIC 协议测试 ===")

    print(f"本地连接ID: {conn.dcid.hex()}")

    print(f"远端连接ID: {conn.scid.hex()}")

    

    # 创建流

    stream_id = conn.create_stream(bidirectional=True)

    print(f"\n创建流: ID={stream_id}")

    

    # 发送数据

    data = b"Hello, QUIC!"

    frames = conn.send_data(stream_id, data)

    print(f"发送数据帧: {len(frames)} 帧")

    if frames:

        f = frames[0]

        print(f"  流ID={f['stream_id']}, 数据={f['data']}")

    

    # 构建数据包

    packet = conn.build_packet(QUICConnection.TYPE_SHORT, b"QUIC payload test")

    print(f"\n构建数据包: {len(packet)} 字节")

    print(f"包类型: {packet[0] & 0x30 >> 4}")

    

    # 解析数据包

    parsed = conn.parse_packet(packet)

    if parsed:

        print(f"解析成功: 类型={parsed['header']['type']}")

    

    # 接收数据

    conn.recv_data(stream_id, b"Response", 0, False)

    print(f"\n流数据: {conn.streams[stream_id]['data']}")

