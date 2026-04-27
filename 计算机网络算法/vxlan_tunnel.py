# -*- coding: utf-8 -*-
"""
算法实现：计算机网络算法 / vxlan_tunnel

本文件实现 vxlan_tunnel 相关的算法功能。
"""

import struct
import random


class VXLANHeader:
    """VXLAN 头部"""

    def __init__(self, vni=0, vni_valid=True, instance_id=0):
        """
        初始化 VXLAN 头
        
        参数:
            vni: VXLAN Network Identifier（24位）
            vni_valid: VNI 是否有效
            instance_id: 保留字段
        """
        self.vni = vni
        self.vni_valid = vni_valid
        self.instance_id = instance_id

    def to_bytes(self):
        """序列化为 8 字节"""
        flags = 0x08 if self.vni_valid else 0x00  # I 标志位
        header = struct.pack('!III',
            (flags << 24) | (self.instance_id << 8),
            0,  # 保留
            self.vni
        )
        return header

    @staticmethod
    def parse(data):
        """从字节解析"""
        if len(data) < 8:
            return None
        words = struct.unpack('!III', data[:8])
        flags = (words[0] >> 24) & 0xFF
        vni_valid = bool(flags & 0x08)
        vni = words[2] & 0xFFFFFF
        return VXLANHeader(vni, vni_valid)


class VXLANTunnel:
    """VXLAN 隧道"""

    def __init__(self, tunnel_id, local_ip, remote_ip, vni):
        """
        初始化 VXLAN 隧道
        
        参数:
            tunnel_id: 隧道 ID
            local_ip: 本地 IP
            remote_ip: 远端 IP
            vni: VXLAN 网络 ID
        """
        self.tunnel_id = tunnel_id
        self.local_ip = local_ip
        self.remote_ip = remote_ip
        self.vni = vni
        self.active = True
        self.packets_encapped = 0
        self.packets_decapped = 0

    def encapsulate(self, inner_packet, dst_mac, src_mac, ethertype):
        """
        封装数据包（添加 VXLAN 头和外层头）
        
        参数:
            inner_packet: 原始以太网帧
            dst_mac: 目标 MAC
            src_mac: 源 MAC
            ethertype: 以太网类型
        返回:
            packet: 封装后的 UDP/IP 包
        """
        # 构建内层以太网头
        inner_eth = dst_mac + src_mac + struct.pack('!H', ethertype) + inner_packet
        
        # 构建 VXLAN 头
        vxlan_header = VXLANHeader(self.vni).to_bytes()
        
        # 构建外层 UDP 头（源端口使用 hash，VXLAN 端口 4789）
        src_port = random.randint(49152, 65535)
        dst_port = 4789
        udp_header = struct.pack('!HHHH', src_port, dst_port, 8 + len(inner_eth) + 8, 0)
        
        # 构建外层 IP 头
        ip_header = self._build_ip_header(src_port, dst_port)
        
        # 组装
        self.packets_encapped += 1
        return ip_header + udp_header + vxlan_header + inner_eth

    def _build_ip_header(self, src_port, dst_port):
        """构建简化的 IP 头"""
        src_ip = self.local_ip
        dst_ip = self.remote_ip
        # 简化版本
        ver_ihl = 0x45
        tos = 0
        total_len = 20 + 8 + 8 + 1500  # IP + UDP + VXLAN + Ethernet
        ident = random.randint(0, 65535)
        flags_frag = 0x4000  # Don't Fragment
        ttl = 64
        proto = 17  # UDP
        
        src_int = self._ip_to_int(src_ip)
        dst_int = self._ip_to_int(dst_ip)
        
        header = struct.pack('!BBHHHBBHII', ver_ihl, tos, total_len, ident,
                           flags_frag, ttl, proto, 0, src_int, dst_int)
        return header

    @staticmethod
    def _ip_to_int(ip):
        parts = ip.split('.')
        return (int(parts[0]) << 24) | (int(parts[1]) << 16) | (int(parts[2]) << 8) | int(parts[3])

    def decapsulate(self, packet):
        """解封装数据包"""
        if len(packet) < 42:  # IP + UDP + VXLAN + minimum eth
            return None
        
        # 跳过 IP 和 UDP 头
        ip_header_len = 20
        udp_header_len = 8
        offset = ip_header_len + udp_header_len
        
        # 解析 VXLAN 头
        vxlan_header = VXLANHeader.parse(packet[offset:])
        if not vxlan_header or not vxlan_header.vni_valid:
            return None
        
        # 获取内层以太网帧
        inner_start = offset + 8
        if len(packet) < inner_start + 14:
            return None
        
        self.packets_decapped += 1
        return {
            'vni': vxlan_header.vni,
            'payload': packet[inner_start:]
        }


if __name__ == "__main__":
    print("=== VXLAN 测试 ===")
    tunnel = VXLANTunnel(
        tunnel_id=1,
        local_ip="10.0.0.1",
        remote_ip="10.0.0.2",
        vni=100
    )
    
    # 模拟以太网帧
    dst_mac = b'\x00\x11\x22\x33\x44\x55'
    src_mac = b'\x66\x77\x88\x99\xaa\xbb'
    ethertype = 0x0800
    payload = b'Hello VXLAN!'
    
    # 封装
    encapped = tunnel.encapsulate(payload, dst_mac, src_mac, ethertype)
    print(f"封装后: {len(encapped)} 字节")
    print(f"  外层 IP: {tunnel.local_ip} -> {tunnel.remote_ip}")
    print(f"  VNI: {tunnel.vni}")
    
    # 解封装
    result = tunnel.decapsulate(encapped)
    if result:
        print(f"\n解封装成功:")
        print(f"  VNI: {result['vni']}")
        print(f"  负载: {result['payload'][14:].decode()}")
    
    print(f"\n统计: 封装={tunnel.packets_encapped}, 解封装={tunnel.packets_decapped}")
