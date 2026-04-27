# -*- coding: utf-8 -*-
"""
算法实现：25_�������� / vxlan_tunnel

本文件实现 vxlan_tunnel 相关的算法功能。
"""

import struct
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class EthernetHeader:
    """以太网头部"""
    dst_mac: str
    src_mac: str
    ethertype: int  # 0x0800 for IPv4, 0x86DD for IPv6
    
    def to_bytes(self) -> bytes:
        dst = self._parse_mac(self.dst_mac)
        src = self._parse_mac(self.src_mac)
        return dst + src + struct.pack('!H', self.ethertype)
    
    @staticmethod
    def _parse_mac(mac: str) -> bytes:
        return bytes(int(m, 16) for m in mac.split(':'))


@dataclass
class IPv4Header:
    """IPv4头部"""
    src_ip: str
    dst_ip: str
    protocol: int  # 17 for UDP
    ttl: int = 64
    
    def to_bytes(self) -> bytes:
        src = self._parse_ip(self.src_ip)
        dst = self._parse_ip(self.dst_ip)
        
        version_ihl = (4 << 4) | 5
        DSCP_ECN = 0
        total_length = 20 + 8 + 50  # IP + UDP + inner frame
        identification = 0
        flags_fragment = 0
        checksum = 0
        
        header = struct.pack('!BBHHHBBH4s4s',
            version_ihl, DSCP_ECN, total_length,
            identification, flags_fragment, self.ttl,
            self.protocol, checksum, src, dst
        )
        
        return header
    
    @staticmethod
    def _parse_ip(ip: str) -> bytes:
        return bytes(int(p) for p in ip.split('.'))


@dataclass
class UDPHeader:
    """UDP头部"""
    src_port: int
    dst_port: int
    length: int
    checksum: int = 0
    
    def to_bytes(self) -> bytes:
        return struct.pack('!HHHH', self.src_port, self.dst_port, self.length, self.checksum)


@dataclass 
class VXLANHeader:
    """VXLAN头部（8字节）"""
    vni: int  # 24位VXLAN网络标识
    reserved1: int = 0
    reserved2: int = 0
    reserved3: int = 0
    
    def to_bytes(self) -> bytes:
        # Flags: 8位，只有I(Instance)位需要设置
        flags = 0x08  # I flag = 1
        return struct.pack('!BBH', flags, self.reserved1, self.vni)


class VTEP:
    """
    VXLAN隧道端点 (VXLAN Tunnel End Point)
    
    负责：
    - 封装：添加VXLAN头部
    - 解封装：移除VXLAN头部
    - 学习MAC地址
    """
    
    def __init__(self, vtep_id: str, ip: str, vni: int):
        self.vtep_id = vtep_id
        self.ip = ip
        self.vni = vni
        
        # MAC地址表（VM MAC -> 远端VTEP IP）
        self.mac_table: Dict[str, str] = {}
        
        # VNI内的虚拟机MAC
        self.local_macs: List[str] = []
        
        # VNI内的其他VTEP
        self.peer_vteps: Dict[str, str] = {}  # vtep_id -> ip
    
    def add_local_mac(self, mac: str):
        """注册本地MAC"""
        if mac not in self.local_macs:
            self.local_macs.append(mac)
    
    def learn_mac(self, mac: str, remote_vtep_ip: str):
        """
        学习MAC地址
        
        Args:
            mac: 虚拟机MAC
            remote_vtep_ip: 远端VTEP IP
        """
        self.mac_table[mac] = remote_vtep_ip
    
    def lookup_mac(self, mac: str) -> Optional[str]:
        """
        查找MAC对应的VTEP
        
        Args:
            mac: 目标MAC
        
        Returns:
            远端VTEP IP或None
        """
        # 本地直接交付
        if mac in self.local_macs:
            return None  # 本地
        
        # 查找远端
        return self.mac_table.get(mac)
    
    def add_peer(self, vtep_id: str, ip: str):
        """添加对端VTEP"""
        self.peer_vteps[vtep_id] = ip
    
    def encapsulate(self, inner_frame: bytes, dst_mac: str) -> bytes:
        """
        VXLAN封装
        
        Args:
            inner_frame: 原始以太网帧
            dst_mac: 目标MAC
        
        Returns:
            封装后的数据包
        """
        # 构建VXLAN头部
        vxlan_header = VXLANHeader(vni=self.vni).to_bytes()
        
        # UDP头部 (VXLAN使用UDP 4789)
        udp_header = UDPHeader(
            src_port=self._compute_udp_port(dst_mac),
            dst_port=4789,
            length=8 + 8 + len(inner_frame)  # UDP + VXLAN + frame
        ).to_bytes()
        
        # IP头部
        dst_vtep_ip = self.lookup_mac(dst_mac)
        
        if dst_vtep_ip is None:
            # 本地交付，不需要封装
            return inner_frame
        
        ip_header = IPv4Header(
            src_ip=self.ip,
            dst_ip=dst_vtep_ip,
            protocol=17  # UDP
        ).to_bytes()
        
        # 以太网头部（VTEP之间）
        eth_header = EthernetHeader(
            dst_mac='ff:ff:ff:ff:ff:ff',  # 下一跳MAC
            src_mac='00:00:00:00:00:00',  # 简化
            ethertype=0x0800  # IPv4
        ).to_bytes()
        
        return eth_header + ip_header + udp_header + vxlan_header + inner_frame
    
    def decapsulate(self, packet: bytes) -> Tuple[bytes, str]:
        """
        VXLAN解封装
        
        Args:
            packet: 接收到的数据包
        
        Returns:
            (原始帧, 源VTEP IP)
        """
        # 简化解析
        # 跳过外层以太网(14) + IP(20) + UDP(8) + VXLAN(8)
        offset = 14 + 20 + 8 + 8
        
        inner_frame = packet[offset:]
        src_ip = "0.0.0.0"  # 从IP头提取
        
        return inner_frame, src_ip
    
    def _compute_udp_port(self, mac: str) -> int:
        """
        计算UDP源端口（用于ECMP负载均衡）
        
        基于内层帧头的哈希
        """
        # 使用内层MAC计算哈希
        h = hashlib.md5(mac.encode()).digest()
        port = int.from_bytes(h[:2], 'big') & 0xF000  # 保留高4位
        return 32768 + (port >> 12)  # 范围: 32768-40959


class VXLANNetwork:
    """
    VXLAN网络模拟
    
    模拟多个VTEP之间的通信
    """
    
    def __init__(self, vni: int):
        self.vni = vni
        self.vteps: Dict[str, VTEP] = {}
        self.vni_to_vteps: Dict[int, List[VTEP]] = {vni: []}
    
    def add_vtep(self, vtep: VTEP):
        """添加VTEP"""
        self.vteps[vtep.vtep_id] = vtep
        self.vni_to_vteps.setdefault(vtep.vni, []).append(vtep)
        
        # VTEP之间建立对等关系
        for other in self.vteps.values():
            if other.vtep_id != vtep.vtep_id and other.vni == vtep.vni:
                vtep.add_peer(other.vtep_id, other.ip)
                other.add_peer(vtep.vtep_id, vtep.ip)
    
    def send_frame(self, src_vtep_id: str, src_mac: str, dst_mac: str, 
                   payload: bytes) -> bool:
        """
        发送帧
        
        Args:
            src_vtep_id: 源VTEP ID
            src_mac: 源MAC
            dst_mac: 目标MAC
            payload: 数据载荷
        
        Returns:
            是否成功发送
        """
        src_vtep = self.vteps.get(src_vtep_id)
        if not src_vtep:
            return False
        
        # 构建原始以太网帧
        inner_frame = EthernetHeader(
            dst_mac=dst_mac,
            src_mac=src_mac,
            ethertype=0x0800
        ).to_bytes() + payload
        
        # 封装
        encapsulated = src_vtep.encapsulate(inner_frame, dst_mac)
        
        # 查找目标VTEP
        dst_vtep_ip = src_vtep.lookup_mac(dst_mac)
        
        if dst_vtep_ip is None:
            # 本地交付
            print(f"  [本地交付] {src_mac} -> {dst_mac}")
            return True
        
        # 查找目标VTEP
        dst_vtep = None
        for v in self.vteps.values():
            if v.ip == dst_vtep_ip and v.vni == self.vni:
                dst_vtep = v
                break
        
        if dst_vtep:
            # 模拟传输
            self._simulate_transmit(src_vtep, dst_vtep, encapsulated, src_mac)
            return True
        
        return False
    
    def _simulate_transmit(self, src_vtep: VTEP, dst_vtep: VTEP, 
                          packet: bytes, src_mac: str):
        """模拟数据包传输"""
        print(f"  [{src_vtep.vtep_id} -> {dst_vtep.vtep_id}]")
        print(f"    封装: VNI={self.vni}, 长度={len(packet)}")
        
        # 解封装
        inner_frame, _ = dst_vtep.decapsulate(packet)
        
        # 学习MAC
        src_vtep_ip = src_vtep.ip
        dst_vtep.learn_mac(src_mac, src_vtep_ip)
        
        print(f"    解封装: {len(inner_frame)} bytes")


def demo_vxlan_encapsulation():
    """演示VXLAN封装"""
    print("=== VXLAN封装演示 ===\n")
    
    # 创建VTEP
    vtep1 = VTEP("vtep1", "10.0.1.1", vni=1000)
    vtep2 = VTEP("vtep2", "10.0.2.1", vni=1000)
    
    # 添加MAC
    vtep1.add_local_mac("00:11:22:33:44:55")
    vtep2.add_local_mac("00:aa:bb:cc:dd:ee")
    
    # 建立对等
    vtep1.add_peer("vtep2", "10.0.2.1")
    vtep2.add_peer("vtep1", "10.0.1.1")
    
    # 学习MAC
    vtep1.learn_mac("00:aa:bb:cc:dd:ee", "10.0.2.1")
    vtep2.learn_mac("00:11:22:33:44:55", "10.0.1.1")
    
    # 封装
    payload = b"Hello VXLAN!"
    inner_frame = EthernetHeader(
        dst_mac="00:aa:bb:cc:dd:ee",
        src_mac="00:11:22:33:44:55",
        ethertype=0x0800
    ).to_bytes() + payload
    
    print("原始帧:")
    print(f"  DST MAC: 00:aa:bb:cc:dd:ee")
    print(f"  SRC MAC: 00:11:22:33:44:55")
    print(f"  载荷: {payload}")
    print()
    
    encapsulated = vtep1.encapsulate(inner_frame, "00:aa:bb:cc:dd:ee")
    
    print("封装后:")
    print(f"  外层以太网: dst=ff:ff:ff:ff:ff:ff")
    print(f"  外层IP: 10.0.1.1 -> 10.0.2.1")
    print(f"  UDP: src=??? -> 4789 (VXLAN)")
    print(f"  VXLAN头: VNI=1000")
    print(f"  总长度: {len(encapsulated)} bytes")
    print()
    
    # 解封装
    inner, src_ip = vtep2.decapsulate(encapsulated)
    print("解封装:")
    print(f"  提取的载荷: {inner[14:]}")
    print(f"  源VTEP: {src_ip}")


def demo_vxlan_network():
    """演示VXLAN网络"""
    print("\n=== VXLAN网络演示 ===\n")
    
    # 创建VXLAN网络
    vxlan = VXLANNetwork(vni=1000)
    
    # 添加VTEP
    vteps = [
        VTEP("vtep-east", "10.0.1.1", vni=1000),
        VTEP("vtep-west", "10.0.2.1", vni=1000),
        VTEP("vtep-europe", "10.0.3.1", vni=1000),
    ]
    
    for v in vteps:
        vxlan.add_vtep(v)
        v.add_local_mac(f"00:11:22:33:44:{v.vtep_id[-1]}{v.vtep_id[-1]}")
    
    print("VXLAN网络:")
    print(f"  VNI: 1000")
    print(f"  VTEP数量: {len(vteps)}")
    for v in vteps:
        print(f"    - {v.vtep_id}: {v.ip}, MACs={v.local_macs}")
    print()
    
    # 跨VTEP通信
    print("跨VTEP通信:")
    vxlan.send_frame("vtep-east", "00:11:22:33:44:ee", "00:11:22:33:44:ww", b"ping")
    
    print()
    print("MAC学习:")
    for v in vteps:
        print(f"  {v.vtep_id}: {v.mac_table}")


def demo_vni_isolation():
    """演示VNI隔离"""
    print("\n=== VNI隔离演示 ===\n")
    
    # 创建多个VNI
    vni1 = VXLANNetwork(vni=1000)
    vni2 = VXLANNetwork(vni=2000)
    
    # VNI 1000
    vtep1 = VTEP("vtep1", "10.0.1.1", vni=1000)
    vtep2 = VTEP("vtep2", "10.0.2.1", vni=1000)
    
    # VNI 2000
    vtep3 = VTEP("vtep3", "10.0.3.1", vni=2000)
    vtep4 = VTEP("vtep4", "10.0.4.1", vni=2000)
    
    vni1.add_vtep(vtep1)
    vni1.add_vtep(vtep2)
    vni2.add_vtep(vtep3)
    vni2.add_vtep(vtep4)
    
    print("VNI隔离:")
    print("  VNI 1000: vtep1, vtep2")
    print("  VNI 2000: vtep3, vtep4")
    print()
    print("vtep1 无法直接与 vtep3 通信（不同VNI）")
    
    # VNI内部通信
    vtep1.add_peer("vtep2", "10.0.2.1")
    vtep2.add_peer("vtep1", "10.0.1.1")
    vtep1.learn_mac("00:aa:bb:cc:dd:ee", "10.0.2.1")
    
    print()
    print("VNI 1000内部通信:")
    inner = EthernetHeader("00:aa:bb:cc:dd:ee", "00:11:22:33:44:55", 0x0800).to_bytes()
    encapsulated = vtep1.encapsulate(inner, "00:aa:bb:cc:dd:ee")
    print(f"  封装成功: {len(encapsulated)} bytes")


def demo_benefits():
    """演示VXLAN优势"""
    print("\n=== VXLAN优势 ===\n")
    
    print("1. 可扩展性:")
    print("   - VLAN: 12位 = 4094 个网络")
    print("   - VXLAN: 24位 = 16M 个网络")
    
    print("\n2. 多租户:")
    print("   - 传统VLAN需要4094个VLAN全局唯一")
    print("   - VXLAN每个租户可独立使用相同的VNI")
    
    print("\n3. 灵活部署:")
    print("   - 跨三层网络扩展二层")
    print("   - 支持虚拟机迁移")
    
    print("\n4. 负载均衡:")
    print("   - UDP源端口基于内层帧头哈希")
    print("   - 支持ECMP")


if __name__ == "__main__":
    print("=" * 60)
    print("VXLAN隧道技术实现")
    print("=" * 60)
    
    demo_vxlan_encapsulation()
    demo_vxlan_network()
    demo_vni_isolation()
    demo_benefits()
    
    print("\n" + "=" * 60)
    print("VXLAN vs VLAN:")
    print("=" * 60)
    print("""
| 特性      | VLAN        | VXLAN       |
|-----------|-------------|-------------|
| 标识位数   | 12位        | 24位        |
| 网络数量   | 4094        | 16M         |
| 网络类型   | 二层        | 二层over三层|
| 封装      | 无          | UDP/IP      |
| 组播支持   | 原生        | 需要overlay |
| 硬件需求   | VLAN交换机  | VTEP支持    |
""")
