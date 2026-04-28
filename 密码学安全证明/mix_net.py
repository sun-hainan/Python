"""
混合网络 (Mix Net)
==========================================

【原理】
通过一系列中间节点（mixers）打乱消息顺序和关联，防止流量分析。
用于匿名通信、投票系统等。

【时间复杂度】O(n) 混合
【应用场景】
- 洋葱路由（Tor）
- 匿名邮件
- 电子投票
"""

import random
import hashlib


class MixNode:
    """
    Mix节点

    【操作】
    - 接收一批消息
    - 打乱顺序
    - 重新加密/转发
    """

    def __init__(self, node_id: int):
        self.node_id = node_id
        self.inbox = []
        self.outbox = []

    def receive(self, message: dict):
        """接收消息"""
        self.inbox.append(message)

    def mix(self, threshold: int = 10):
        """
        混合操作

        【步骤】
        1. 收集threshold个消息
        2. 打乱顺序
        3. 重新加密
        4. 转发
        """
        if len(self.inbox) < threshold:
            return []

        messages = self.inbox[:threshold]
        self.inbox = self.inbox[threshold:]

        # 打乱
        random.shuffle(messages)

        # 重新加密并添加层
        for msg in messages:
            msg["layers"].append(self.node_id)

        self.outbox.extend(messages)
        return messages


class MixNet:
    """
    混合网络

    【拓扑】
    Alice -> Mix1 -> Mix2 -> Mix3 -> Bob
    """

    def __init__(self, num_mixes: int = 3):
        self.mixes = [MixNode(i) for i in range(num_mixes)]

    def send(self, message: str, dest: int) -> dict:
        """发送消息"""
        msg = {
            "content": message,
            "destination": dest,
            "layers": []
        }

        # 经过每个mix
        current = msg
        for mix in self.mixes:
            mix.receive(current)
            out = mix.mix(threshold=1)
            if out:
                current = out[0]

        return msg

    def receive_at(self, message: dict, dest: int) -> str:
        """在目标节点接收消息"""
        if message["destination"] == dest:
            return message["content"]
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("Mix Net - 测试")
    print("=" * 50)

    print("\n【测试】混合网络")
    mixnet = MixNet(num_mixes=3)

    # 发送多条消息
    for i in range(5):
        msg = mixnet.send(f"Message {i}", dest=i % 3)
        print(f"  发送消息{i}: layers={len(msg['layers'])}")

    print(f"  Mix0 outbox: {len(mixnet.mixes[0].outbox)}")
    print(f"  Mix1 outbox: {len(mixnet.mixes[1].outbox)}")
    print(f"  Mix2 outbox: {len(mixnet.mixes[2].outbox)}")

    print("\n" + "=" * 50)
