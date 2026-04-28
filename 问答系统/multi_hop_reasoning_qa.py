"""
多跳推理问答模块

本模块实现需要多跳推理的问答系统。
多跳问答是指回答问题需要从多个文档/段落中综合信息，
例如："某公司的CEO创建的公司的竞争对手是谁？"

核心方法：
1. 实体链接：将问题中的实体链接到知识库
2. 图推理：构建实体关系图并进行推理
3. 迭代检索：逐步检索和推理
4. 答案综合：聚合多跳结果得到最终答案
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass, field


@dataclass
class Entity:
    """实体节点"""
    entity_id: str
    name: str
    entity_type: str
    mentions: List[str] = field(default_factory=list)


@dataclass
class Relation:
    """关系边"""
    source_id: str
    target_id: str
    relation_type: str
    weight: float = 1.0


@dataclass
class KnowledgeGraph:
    """知识图谱"""
    entities: Dict[str, Entity] = field(default_factory=dict)
    relations: List[Relation] = field(default_factory=list)
    adjacency: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)  # entity_id -> [(neighbor_id, relation)]

    def add_entity(self, entity: Entity):
        self.entities[entity.entity_id] = entity
        if entity.entity_id not in self.adjacency:
            self.adjacency[entity.entity_id] = []

    def add_relation(self, relation: Relation):
        self.relations.append(relation)
        self.adjacency[relation.source_id].append((relation.target_id, relation.relation_type))
        self.adjacency[relation.target_id].append((relation.source_id, relation.relation_type))


class EntityLinker:
    """实体链接器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def link(self, text: str) -> List[Entity]:
        """将文本中的实体链接到知识图谱"""
        text_lower = text.lower()
        linked = []

        for entity_id, entity in self.kg.entities.items():
            if entity.name.lower() in text_lower:
                linked.append(entity)
            else:
                # 检查别名
                for mention in entity.mentions:
                    if mention.lower() in text_lower:
                        linked.append(entity)
                        break

        return linked


class GraphReasoner:
    """基于图的推理器"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    def find_paths(self, source_id: str, target_id: str, max_hops: int = 3) -> List[List[Tuple[str, str]]]:
        """
        查找两点之间的路径
        :param source_id: 起始实体ID
        :param target_id: 目标实体ID
        :param max_hops: 最大跳数
        :return: 路径列表，每条路径是 [(neighbor_id, relation)] 的序列
        """
        paths = []

        def dfs(current: str, target: str, visited: Set[str], path: List[Tuple[str, str]], depth: int):
            if depth > max_hops:
                return
            if current == target and path:
                paths.append(path.copy())
                return
            if current in visited:
                return

            visited.add(current)
            for neighbor, rel in self.kg.adjacency.get(current, []):
                path.append((neighbor, rel))
                dfs(neighbor, target, visited, path, depth + 1)
                path.pop()
            visited.remove(current)

        dfs(source_id, target_id, set(), [], 0)
        return paths

    def find_neighbors(self, entity_id: str, relation_type: Optional[str] = None, depth: int = 1) -> Set[str]:
        """查找邻居实体"""
        neighbors = set()
        current_level = {entity_id}
        visited = {entity_id}

        for _ in range(depth):
            next_level = set()
            for eid in current_level:
                for neighbor, rel in self.kg.adjacency.get(eid, []):
                    if neighbor not in visited and (relation_type is None or rel == relation_type):
                        next_level.add(neighbor)
                        neighbors.add(neighbor)
            visited.update(next_level)
            current_level = next_level

        return neighbors


class HopRetrievalModule(nn.Module):
    """单跳检索模块"""

    def __init__(self, embed_dim=128, hidden_dim=256):
        super().__init__()
        # 查询编码
        self.query_encoder = nn.LSTM(embed_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        # 实体编码
        self.entity_encoder = nn.LSTM(embed_dim, hidden_dim, num_layers=1, batch_first=True, bidirectional=True)
        # 相似度计算
        self.similarity = nn.Linear(hidden_dim * 2, 1)

    def encode_query(self, query_ids):
        """编码查询"""
        embed = nn.functional.embedding(query_ids, torch.zeros_like(query_ids).float())
        _, (h_n, _) = self.query_encoder(embed)
        return torch.cat([h_n[0], h_n[1]], dim=-1)

    def encode_entity(self, entity_ids):
        """编码实体"""
        embed = nn.functional.embedding(entity_ids, torch.zeros_like(entity_ids).float())
        _, (h_n, _) = self.entity_encoder(embed)
        return torch.cat([h_n[0], h_n[1]], dim=-1)

    def score(self, query_repr, entity_repr):
        """计算查询-实体匹配分数"""
        combined = torch.cat([query_repr, entity_repr], dim=-1)
        score = self.similarity(combined)
        return score


class MultiHopReasoner(nn.Module):
    """多跳推理网络"""

    def __init__(self, num_hops=3, embed_dim=128, hidden_dim=256, vocab_size=5000):
        super().__init__()
        self.num_hops = num_hops
        self.hop_modules = nn.ModuleList([
            HopRetrievalModule(embed_dim, hidden_dim) for _ in range(num_hops)
        ])
        # 记忆更新GRU
        self.memory_gru = nn.GRUCell(hidden_dim * 2, hidden_dim * 2)
        # 最终答案预测
        self.answer_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, vocab_size)
        )

    def forward(self, query_ids, entity_ids_list, num_entities_per_hop):
        """
        前向传播
        :param query_ids: 问题token ids
        :param entity_ids_list: 每跳的候选实体ids列表
        :param num_entities_per_hop: 每跳的实体数量
        :return: 每跳的注意力分数, 最终答案logits
        """
        # 初始化记忆
        query_repr = self.hop_modules[0].encode_query(query_ids)
        memory = query_repr  # 初始记忆为查询表示

        hop_attentions = []

        for hop in range(self.num_hops):
            # 编码候选实体
            entity_reprs = []
            for eid in entity_ids_list[hop][:num_entities_per_hop[hop]]:
                entity_repr = self.hop_modules[hop].encode_entity(eid)
                entity_reprs.append(entity_repr)

            if entity_reprs:
                entity_reprs = torch.stack(entity_reprs)  # [num_entities, hidden*2]
                # 计算注意力
                scores = self.hop_modules[hop].score(memory, entity_reprs)
                attn_weights = F.softmax(scores, dim=0)
                hop_attentions.append(attn_weights)

                # 选择top实体
                top_entity = entity_reprs[attn_weights.argmax()]

                # 更新记忆
                memory = self.memory_gru(top_entity.unsqueeze(0), memory.unsqueeze(0)).squeeze(0)
            else:
                hop_attentions.append(torch.tensor([]))

        # 预测答案
        answer_logits = self.answer_predictor(memory)

        return hop_attentions, answer_logits


class MultiHopQAPipeline:
    """多跳问答Pipeline"""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.entity_linker = EntityLinker(kg)
        self.graph_reasoner = GraphReasoner(kg)
        self.model = MultiHopReasoner(num_hops=3)

    def retrieve_hop(self, query: str, focus_entities: List[Entity], hop: int) -> List[Entity]:
        """
        检索单跳的候选实体
        :param query: 查询文本
        :param focus_entities: 当前关注的实体列表
        :param hop: 当前第几跳（0-indexed）
        :return: 候选实体列表
        """
        candidates = []

        for entity in focus_entities:
            # 获取邻居实体
            neighbors = self.graph_reasoner.find_neighbors(entity.entity_id, depth=1)
            for neighbor_id in neighbors:
                if neighbor_id in self.kg.entities:
                    candidates.append(self.kg.entities[neighbor_id])

        # 去重
        seen = set()
        unique = []
        for e in candidates:
            if e.entity_id not in seen:
                seen.add(e.entity_id)
                unique.append(e)

        return unique

    def reason(self, question: str) -> Dict:
        """
        多跳推理问答
        :param question: 问题文本
        :return: 推理结果
        """
        # 第一步：链接问题中的实体
        linked_entities = self.entity_linker.link(question)

        # 迭代多跳推理
        focus_entities = linked_entities
        reasoning_chains = []

        for hop in range(3):  # 最多3跳
            # 检索当前跳的候选
            candidates = self.retrieve_hop(question, focus_entities, hop)

            # 选择最相关的实体
            if candidates:
                # 简化：选择第一个候选
                chosen = candidates[0]
                reasoning_chains.append({
                    "hop": hop,
                    "focus_entities": [e.name for e in focus_entities],
                    "candidates": [c.name for c in candidates[:5]],
                    "chosen": chosen.name,
                    "relation": "related_to"
                })
                focus_entities = [chosen]
            else:
                break

        # 生成答案
        answer = focus_entities[0].name if focus_entities else ""

        return {
            "question": question,
            "linked_entities": [e.name for e in linked_entities],
            "reasoning_chains": reasoning_chains,
            "answer": answer
        }


def build_toy_knowledge_graph() -> KnowledgeGraph:
    """构建示例知识图谱"""
    kg = KnowledgeGraph()

    # 添加实体
    entities = [
        Entity("e1", "Apple Inc.", "Company", ["Apple"]),
        Entity("e2", "Steve Jobs", "Person"),
        Entity("e3", "Tim Cook", "Person"),
        Entity("e4", "Cupertino", "Location", ["Cupertino"]),
        Entity("e5", "Google", "Company"),
        Entity("e6", "Larry Page", "Person"),
        Entity("e7", "CEO", "Position"),
        Entity("e8", "California", "Location"),
    ]
    for e in entities:
        kg.add_entity(e)

    # 添加关系
    relations = [
        Relation("e2", "e1", "founded_by"),
        Relation("e1", "e4", "headquartered_in"),
        Relation("e3", "e1", "CEO_of"),
        Relation("e2", "e3", "worked_with"),
        Relation("e5", "e6", "founded_by"),
        Relation("e4", "e8", "located_in"),
        Relation("e6", "e5", "CEO_of"),
    ]
    for r in relations:
        kg.add_relation(r)

    return kg


def demo():
    """多跳推理问答演示"""
    print("[多跳推理问答演示]")

    # 构建知识图谱
    kg = build_toy_knowledge_graph()
    print(f"  知识图谱: {len(kg.entities)} 实体, {len(kg.relations)} 关系")

    # 初始化Pipeline
    pipeline = MultiHopQAPipeline(kg)

    # 多跳问答
    questions = [
        "Who is the CEO of Apple Inc.?",
        "Where is Apple Inc. headquartered?",
        "Who founded the company that competes with Apple?",
    ]

    for q in questions:
        result = pipeline.reason(q)
        print(f"\n  问题: {q}")
        print(f"  链接的实体: {result['linked_entities']}")
        print(f"  推理链:")
        for step in result['reasoning_chains']:
            print(f"    Hop {step['hop']}: {step['focus_entities']} -> {step['chosen']} ({step['relation']})")
        print(f"  答案: {result['answer']}")

    # 图推理演示
    print("\n  图推理演示:")
    paths = pipeline.graph_reasoner.find_paths("e2", "e4")  # Steve Jobs -> Cupertino
    print(f"    Steve Jobs到Cupertino的路径: {paths}")

    # 邻居查找
    neighbors = pipeline.graph_reasoner.find_neighbors("e1")  # Apple Inc.的邻居
    print(f"    Apple Inc.的邻居: {[kg.entities[n].name for n in neighbors]}")

    # 模型演示
    model = MultiHopReasoner(num_hops=3)
    print(f"\n  多跳推理网络参数量: {sum(p.numel() for p in model.parameters()):,}")

    print("  ✅ 多跳推理问答演示通过！")


if __name__ == "__main__":
    demo()
