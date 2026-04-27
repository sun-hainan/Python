# -*- coding: utf-8 -*-
"""
算法实现：15_操作系统与调度 / container_networking

本文件实现 container_networking 相关的算法功能。
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class NetworkMode(Enum):
    """容器网络模式"""
    BRIDGE = "bridge"   # 桥接模式（默认）
    HOST = "host"       # 共享宿主机网络栈
    NONE = "none"       # 无网络（完全隔离）
    CONTAINER = "container"  # 使用其他容器的网络栈


@dataclass
class VethPair:
    """veth pair：虚拟以太网对（一头在容器，一头在host）"""
    container_iface: str  # 容器内接口名（如eth0）
    host_iface: str        # 宿主机端接口名（如veth123abc）
    container_ns: str     # 所属容器ID


@dataclass
class BridgeInfo:
    """网桥信息"""
    name: str
    ip_addr: str
    subnet_mask: str
    ports: list[str] = field(default_factory=list)


class ContainerNetworkNamespace:
    """容器网络命名空间（模拟）"""

    def __init__(self, ns_id: str):
        self.ns_id = ns_id
        self.interfaces: dict[str, dict] = {}  # 接口名 -> 接口信息
        self.routes: list[dict] = []
        self.iptables_rules: list[str] = []


class BridgeNetwork:
    """桥接网络（类似docker0）"""

    def __init__(self, name: str = "docker0", ip: str = "172.17.0.1/16"):
        self.name = name
        self.ip, self.mask = ip.split("/")
        self.interfaces: list[str] = []  # 连接到此网桥的veth端口
        self.veth_pairs: list[VethPair] = []

    def attach_veth(self, veth: VethPair):
        """将veth对接入网桥"""
        self.interfaces.append(veth.host_iface)
        self.veth_pairs.append(veth)

    def get_bridge_info(self) -> BridgeInfo:
        return BridgeInfo(
            name=self.name,
            ip_addr=self.ip,
            subnet_mask=self.mask,
            ports=self.interfaces.copy()
        )


class ContainerNetworkManager:
    """
    容器网络管理器
    支持：bridge/host/none模式
    """

    def __init__(self):
        self.net_ns_map: dict[str, ContainerNetworkNamespace] = {}
        self.bridges: dict[str, BridgeNetwork] = {}
        self.default_bridge = BridgeNetwork()
        self.bridges["bridge"] = self.default_bridge

    def create_network_namespace(self, container_id: str) -> ContainerNetworkNamespace:
        """为容器创建独立网络命名空间"""
        ns = ContainerNetworkNamespace(ns_id=container_id)
        self.net_ns_map[container_id] = ns
        return ns

    def setup_bridge_mode(self, container_id: str) -> dict:
        """
        设置桥接网络模式
        原理：创建veth pair，一端在容器，一端接入docker0网桥
        """
        ns = self.net_ns_map.get(container_id)
        if ns is None:
            ns = self.create_network_namespace(container_id)

        # 创建veth pair
        veth_container = f"eth0"  # 容器内固定名称
        veth_host = f"veth{container_id[:8]}"  # 宿主机端随机名称

        veth = VethPair(
            container_iface=veth_container,
            host_iface=veth_host,
            container_ns=container_id
        )

        # 添加容器内接口
        ns.interfaces[veth_container] = {
            "type": "veth",
            "peer": veth_host,
            "ip": "172.17.0.2/16",  # 模拟分配的IP
            "mtu": 1500
        }

        # 接入网桥
        self.default_bridge.attach_veth(veth)

        return {
            "mode": "bridge",
            "veth_pair": f"{veth_container} <-> {veth_host}",
            "container_ip": "172.17.0.2",
            "gateway": "172.17.0.1",
            "dns": ["8.8.8.8", "8.8.4.4"]
        }

    def setup_host_mode(self, container_id: str) -> dict:
        """
        设置host网络模式
        原理：容器直接使用宿主机的网络栈（无隔离）
        """
        ns = self.net_ns_map.get(container_id)
        if ns is None:
            ns = self.create_network_namespace(container_id)

        # host模式：直接共享宿主机的网络命名空间
        ns.interfaces["lo"] = {"type": "loopback", "ip": "127.0.0.1/8"}
        ns.interfaces["eth0"] = {"type": "physical", "ip": "inherit"}

        return {
            "mode": "host",
            "network_namespace": "shared with host",
            "note": "容器使用宿主机IP和端口，无隔离"
        }

    def setup_none_mode(self, container_id: str) -> dict:
        """
        设置none网络模式
        原理：容器有独立的网络命名空间，但无任何接口（仅loopback）
        """
        ns = self.net_ns_map.get(container_id)
        if ns is None:
            ns = self.create_network_namespace(container_id)

        # 只启用loopback
        ns.interfaces["lo"] = {"type": "loopback", "ip": "127.0.0.1/8"}

        return {
            "mode": "none",
            "interfaces": list(ns.interfaces.keys()),
            "note": "完全隔离，仅本地通信"
        }

    def get_container_network_config(self, container_id: str, mode: str) -> dict:
        """获取容器网络配置"""
        if mode == "bridge":
            return self.setup_bridge_mode(container_id)
        elif mode == "host":
            return self.setup_host_mode(container_id)
        elif mode == "none":
            return self.setup_none_mode(container_id)
        else:
            return {"error": f"Unknown mode: {mode}"}

    def list_networks(self) -> list[BridgeInfo]:
        """列出所有网络"""
        return [bridge.get_bridge_info() for bridge in self.bridges.values()]


if __name__ == "__main__":
    net_mgr = ContainerNetworkManager()

    print("=== 容器网络模式演示 ===")

    # 创建3个容器，分别使用不同网络模式
    containers = [
        ("container-A", "bridge"),
        ("container-B", "bridge"),
        ("container-C", "host"),
        ("container-D", "none"),
    ]

    for cid, mode in containers:
        config = net_mgr.get_container_network_config(cid, mode)
        print(f"\n容器 {cid} ({mode}模式):")
        for k, v in config.items():
            print(f"  {k}: {v}")

    # 桥接网络详情
    print("\n=== 桥接网络详情 ===")
    bridge_info = net_mgr.default_bridge.get_bridge_info()
    print(f"网桥: {bridge_info.name}")
    print(f"IP: {bridge_info.ip_addr}/{bridge_info.subnet_mask}")
    print(f"连接端口: {bridge_info.ports}")

    # 网络连通性说明
    print("\n=== 网络隔离说明 ===")
    print("Bridge模式: 通过veth pair连接docker0，容器间可通信")
    print("  - container-A 和 container-B 可以通过 172.17.0.x 互通")
    print("  - 通过 NAT 访问外网")
    print("\nHost模式: 与宿主机共享网络栈，无隔离")
    print("  - container-C 使用宿主机IP")
    print("  - 端口冲突风险（如宿主机已占用80，容器也用80）")
    print("\nNone模式: 完全隔离，无网络")
    print("  - container-D 只能访问自己（loopback）")
    print("  - 适合安全要求高的计算任务")
