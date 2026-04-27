# -*- coding: utf-8 -*-
"""
算法实现：多智能体系统 / agent_communication

本文件实现 agent_communication 相关的算法功能。
"""

import numpy as np
from collections import defaultdict, deque
from enum import Enum
import time


class MessageType(Enum):
    """消息类型枚举"""
    REQUEST = "request"
    INFORM = "inform"
    QUERY = "query"
    PROPAGATE = "propagate"
    ACKNOWLEDGE = "ack"
    REJECT = "reject"
    VOTE = "vote"
    COMMIT = "commit"


class Message:
    """通信消息对象"""
    
    def __init__(self, sender_id, receiver_id, msg_type, content, timestamp=None):
        # sender_id: 发送方ID
        # receiver_id: 接收方ID（-1表示广播）
        # msg_type: 消息类型
        # content: 消息内容（字典）
        # timestamp: 时间戳
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.msg_type = msg_type
        self.content = content
        self.timestamp = timestamp if timestamp else time.time()
        self.sequence_number = 0
        self.acknowledged = False
    
    def is_broadcast(self):
        """是否为广播消息"""
        return self.receiver_id == -1
    
    def __repr__(self):
        return f"Msg(from={self.sender_id}, to={self.receiver_id}, " \
               f"type={self.msg_type.value}, seq={self.sequence_number})"


class CommunicationChannel:
    """通信信道：模拟消息传输"""
    
    def __init__(self, reliability=1.0, delay_mean=0.1, delay_std=0.02):
        # reliability: 可靠性（丢包率 = 1 - reliability）
        # delay_mean: 平均延迟（秒）
        # delay_std: 延迟标准差
        self.reliability = reliability
        self.delay_mean = delay_mean
        self.delay_std = delay_std
        self.message_queue = deque()
    
    def send(self, message, destination):
        """
        发送消息到目的地
        返回：是否成功发送
        """
        # 检查是否丢包
        if np.random.random() > self.reliability:
            return False
        
        # 计算延迟
        delay = max(0, np.random.normal(self.delay_mean, self.delay_std))
        
        # 放入队列
        self.message_queue.append({
            'message': message,
            'destination': destination,
            'delivery_time': time.time() + delay
        })
        
        return True
    
    def broadcast(self, message, all_destinations):
        """广播消息到所有目的地"""
        results = []
        for dest in all_destinations:
            results.append(self.send(message, dest))
        return results
    
    def receive(self, agent_id, current_time=None):
        """接收属于指定智能体的消息"""
        if current_time is None:
            current_time = time.time()
        
        delivered = []
        pending = deque()
        
        while self.message_queue:
            item = self.message_queue.popleft()
            if item['delivery_time'] <= current_time:
                msg = item['message']
                if msg.receiver_id == agent_id or msg.is_broadcast():
                    delivered.append(msg)
                else:
                    pending.append(item)
            else:
                pending.append(item)
        
        # 重新放回未送达的消息
        self.message_queue = pending
        
        return delivered


class AgentCommunicationModule:
    """智能体通信模块"""
    
    def __init__(self, agent_id, channel):
        # agent_id: 智能体ID
        # channel: 通信信道
        self.agent_id = agent_id
        self.channel = channel
        self.message_history = []
        self.inbox = deque()
        self.outbox = deque()
        self.sequence_counter = 0
        self.peers = set()
    
    def add_peer(self, peer_id):
        """添加通信对等方"""
        self.peers.add(peer_id)
    
    def remove_peer(self, peer_id):
        """移除通信对等方"""
        self.peers.discard(peer_id)
    
    def send_message(self, receiver_id, msg_type, content):
        """发送消息"""
        msg = Message(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            msg_type=msg_type,
            content=content,
            timestamp=time.time()
        )
        msg.sequence_number = self.sequence_counter
        self.sequence_counter += 1
        
        self.outbox.append(msg)
        success = self.channel.send(msg, receiver_id)
        
        return success, msg
    
    def broadcast_message(self, msg_type, content):
        """广播消息到所有对等方"""
        results = []
        for peer_id in self.peers:
            success, msg = self.send_message(peer_id, msg_type, content)
            results.append((peer_id, success))
        return results
    
    def receive_messages(self, current_time=None):
        """接收所有等待中的消息"""
        messages = self.channel.receive(self.agent_id, current_time)
        
        for msg in messages:
            self.inbox.append(msg)
            self.message_history.append(msg)
        
        return messages
    
    def pop_message(self):
        """从收件箱取出一条消息"""
        if self.inbox:
            return self.inbox.popleft()
        return None
    
    def send_ack(self, original_message):
        """发送确认消息"""
        content = {'ack_for_seq': original_message.sequence_number}
        return self.send_message(original_message.sender_id, 
                                 MessageType.ACKNOWLEDGE, content)


class ConsensusProtocol:
    """共识协议：实现多智能体间的状态一致性"""
    
    def __init__(self, n_agents, threshold=None):
        # n_agents: 智能体数量
        # threshold: 通过阈值（默认>n/2）
        self.n_agents = n_agents
        self.threshold = threshold if threshold else n_agents // 2 + 1
        
        # 投票记录
        self.votes = defaultdict(list)
        self.proposals = {}
        self.committed_values = {}
    
    def propose(self, proposer_id, value):
        """提议一个新值"""
        proposal_id = f"{proposer_id}_{len(self.proposals)}"
        self.proposals[proposal_id] = {
            'value': value,
            'proposer': proposer_id,
            'votes': []
        }
        return proposal_id
    
    def vote(self, agent_id, proposal_id):
        """对提议投票"""
        if proposal_id in self.proposals:
            self.proposals[proposal_id]['votes'].append(agent_id)
            return True
        return False
    
    def check_commit(self, proposal_id):
        """检查是否可以提交"""
        if proposal_id not in self.proposals:
            return False
        
        vote_count = len(self.proposals[proposal_id]['votes'])
        return vote_count >= self.threshold
    
    def commit(self, proposal_id):
        """提交值"""
        if self.check_commit(proposal_id):
            value = self.proposals[proposal_id]['value']
            self.committed_values[proposal_id] = value
            return value
        return None


class ByzantineConsensus:
    """拜占庭共识协议（简化版）"""
    
    def __init__(self, n_agents, max_byzantine=1):
        # n_agents: 智能体数量
        # max_byzantine: 最大容忍的拜占庭节点数
        self.n_agents = n_agents
        self.max_byzantine = max_byzantine
        self.required_votes = n_agents - max_byzantine  # 需要至少这么多票
        
        self.values = {}  # agent_id -> value
        self.pre_prepare_votes = defaultdict(list)
        self.prepare_votes = defaultdict(list)
        self.commit_votes = defaultdict(list)
    
    def pre_prepare(self, agent_id, instance_id, value):
        """预准备阶段"""
        key = f"{instance_id}_{agent_id}"
        self.values[agent_id] = value
        self.pre_prepare_votes[key].append(agent_id)
        return len(self.pre_prepare_votes[key]) >= self.required_votes
    
    def prepare(self, agent_id, instance_id, value):
        """准备阶段"""
        key = f"{instance_id}_{value}"
        self.prepare_votes[key].append(agent_id)
        return len(self.prepare_votes[key]) >= self.required_votes
    
    def commit(self, instance_id, value):
        """提交阶段"""
        key = f"{instance_id}_{value}"
        self.commit_votes[key].append(value)
        return len(self.commit_votes[key]) >= self.required_votes
    
    def is_consensus_reached(self, instance_id):
        """检查是否达成共识"""
        # 检查是否有足够的提交
        max_votes = 0
        consensus_value = None
        
        for (inst, val), votes in self.commit_votes.items():
            if inst == instance_id and len(votes) > max_votes:
                max_votes = len(votes)
                consensus_value = val
        
        return max_votes >= self.required_votes, consensus_value


class KMeansClustering:
    """基于通信的K-means聚类（分布式聚类算法）"""
    
    def __init__(self, k, max_iterations=10):
        self.k = k
        self.max_iterations = max_iterations
        self.centers = []
        self.cluster_assignments = {}
    
    def initialize_centers(self, data_points):
        """随机初始化聚类中心"""
        indices = np.random.choice(len(data_points), self.k, replace=False)
        self.centers = [data_points[i].copy() for i in indices]
    
    def compute_distances(self, point, centers):
        """计算点到各中心的距离"""
        return [np.linalg.norm(point - c) for c in centers]
    
    def assign_to_cluster(self, point):
        """分配点到最近的聚类"""
        distances = self.compute_distances(point, self.centers)
        return np.argmin(distances)
    
    def update_centers(self, clusters, data_points):
        """更新聚类中心"""
        for i in range(self.k):
            cluster_points = [data_points[j] for j in clusters.get(i, [])]
            if cluster_points:
                self.centers[i] = np.mean(cluster_points, axis=0)


class MultiAgentCommunicationSimulator:
    """多智能体通信模拟器"""
    
    def __init__(self, n_agents, channel_reliability=0.95):
        # n_agents: 智能体数量
        # channel_reliability: 信道可靠性
        self.n_agents = n_agents
        
        # 创建通信信道
        self.channel = CommunicationChannel(reliability=channel_reliability)
        
        # 创建智能体通信模块
        self.agents = {
            i: AgentCommunicationModule(i, self.channel)
            for i in range(n_agents)
        }
        
        # 设置对等连接（全连通）
        for i in range(n_agents):
            for j in range(n_agents):
                if i != j:
                    self.agents[i].add_peer(j)
        
        # 共识协议
        self.consensus = ConsensusProtocol(n_agents)
    
    def step(self):
        """单步模拟"""
        # 所有智能体接收消息
        for agent in self.agents.values():
            agent.receive_messages()
    
    def simulate_message_passing(self, n_steps=10):
        """模拟多步消息传递"""
        print("\n===== 多智能体通信模拟 =====")
        
        for step in range(n_steps):
            # 智能体0广播心跳
            if step % 3 == 0:
                msg_type = MessageType.INFORM
                content = {'heartbeat': step, 'agent_id': 0}
                results = self.agents[0].broadcast_message(msg_type, content)
                print(f"  Step {step}: Agent 0 广播 heartbeat, "
                      f"成功={sum(1 for _, s in results if s)}/{len(results)}")
            
            # 更新
            self.step()
            
            # 随机智能体发送查询
            if step % 5 == 2:
                query_agent = np.random.randint(1, self.n_agents)
                target = 0
                content = {'query': 'status'}
                success, _ = self.agents[query_agent].send_message(
                    target, MessageType.QUERY, content)
                if success:
                    print(f"  Step {step}: Agent {query_agent} -> Agent {target} 查询")
        
        return len(self.agents[0].message_history)
    
    def test_consensus(self, n_rounds=5):
        """测试共识协议"""
        print("\n--- 共识协议测试 ---")
        
        for round_num in range(n_rounds):
            # 随机选择提议者
            proposer = np.random.randint(0, self.n_agents)
            value = f"value_{round_num}_{np.random.randint(1000)}"
            
            proposal_id = self.consensus.propose(proposer, value)
            
            # 所有智能体投票
            for voter in range(self.n_agents):
                self.consensus.vote(voter, proposal_id)
            
            # 检查提交
            committed = self.consensus.commit(proposal_id)
            if committed:
                print(f"  Round {round_num}: 值 '{committed}' 已提交")
            else:
                print(f"  Round {round_num}: 未达到阈值")


if __name__ == "__main__":
    # 测试多智能体通信协议
    print("=" * 50)
    print("多智能体通信协议测试")
    print("=" * 50)
    
    # 创建模拟器
    simulator = MultiAgentCommunicationSimulator(n_agents=5, channel_reliability=0.9)
    
    print(f"\n智能体数量: {simulator.n_agents}")
    print(f"通信信道可靠性: {simulator.channel.reliability}")
    
    # 模拟消息传递
    history_len = simulator.simulate_message_passing(n_steps=10)
    
    # 测试共识
    simulator.test_consensus(n_rounds=3)
    
    # 测试拜占庭共识
    print("\n--- 拜占庭共识测试 ---")
    byzantine = ByzantineConsensus(n_agents=5, max_byzantine=1)
    
    for instance in range(3):
        # 模拟提议
        for agent_id in range(4):  # 4个正常节点
            byzantine.pre_prepare(agent_id, instance, f"value_{instance}")
            byzantine.prepare(agent_id, instance, f"value_{instance}")
        
        reached, value = byzantine.is_consensus_reached(instance)
        print(f"  Instance {instance}: 共识{'达成' if reached else '未达成'}, 值={value}")
    
    print("\n✓ 多智能体通信协议测试完成")
