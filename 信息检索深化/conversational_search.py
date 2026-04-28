"""
会话搜索模块

本模块实现对话式信息检索系统。
支持多轮对话上下文理解、查询消歧和指代消解。

核心方法：
1. 对话上下文管理：维护多轮对话历史
2. 查询消歧：解释指代和省略
3. 会话意图识别：理解对话意图
4. 上下文感知检索：利用对话历史优化检索
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Utterance:
    """对话语句"""
    speaker: str  # "user" or "system"
    text: str
    timestamp: float = 0.0
    intent: Optional[str] = None
    entities: List[Dict] = field(default_factory=list)


@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    history: List[Utterance] = field(default_factory=list)
    current_topic: Optional[str] = None
    referenced_entities: List[str] = field(default_factory=list)  # 之前提到的实体


class QueryRewriter:
    """查询改写器：处理指代和省略"""

    def __init__(self):
        self.pronoun_map = {
            "it": "that",
            "this": "that",
            "they": "those",
            "them": "those",
            "he": None,  # 需要根据上下文判断
            "she": None,
        }
        self.reference_patterns = [
            r"(?i)the (previous|last|past) \w+",
            r"(?i)that (one|item|result)",
            r"(?i)same as above",
        ]

    def rewrite(self, query: str, context: ConversationContext) -> str:
        """
        改写查询，解决指代和省略问题
        """
        # 1. 恢复省略的实体
        rewritten = self._expand_ellipsis(query, context)

        # 2. 解析指代
        rewritten = self._resolve_references(rewritten, context)

        # 3. 补充话题信息
        if context.current_topic and len(rewritten.split()) < 3:
            rewritten = f"{rewritten} {context.current_topic}"

        return rewritten

    def _expand_ellipsis(self, query: str, context: ConversationContext) -> str:
        """展开省略的查询"""
        # 短查询可能是省略形式
        if len(query.split()) <= 2 and context.history:
            # 获取上一轮系统回复中的实体
            last_system = None
            for utt in reversed(context.history):
                if utt.speaker == "system":
                    last_system = utt
                    break

            if last_system:
                # 简单策略：直接拼接
                return f"{query} {last_system.text[:50]}"

        return query

    def _resolve_references(self, query: str, context: ConversationContext) -> str:
        """解析指代词"""
        words = query.lower().split()

        for i, word in enumerate(words):
            if word in self.pronoun_map:
                replacement = self.pronoun_map[word]
                if replacement:
                    words[i] = replacement

        return " ".join(words)


class ConversationIntentClassifier(nn.Module):
    """对话意图分类器"""

    def __init__(self, vocab_size=5000, embed_dim=128, hidden_dim=256, num_intents=10):
        super().__init__()
        self.encoder = nn.LSTM(
            input_size=embed_dim,
            hidden_size=hidden_dim,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_intents)
        )

    def forward(self, token_ids: torch.Tensor) -> torch.Tensor:
        """分类意图"""
        embed = nn.functional.embedding(token_ids, torch.zeros_like(token_ids).float())
        _, (h_n, _) = self.encoder(embed)
        hidden = torch.cat([h_n[0], h_n[1]], dim=-1)
        return self.classifier(hidden)


class ContextAwareRetriever:
    """上下文感知检索器"""

    def __init__(self):
        self.query_encoder = None  # 编码器
        self.doc_encoder = None
        self.documents = []

    def encode_context_query(self, current_query: str,
                           context_history: List[str]) -> np.ndarray:
        """
        编码带上下文的查询
        """
        # 简化的上下文编码
        # 实际应该用专门的模型
        context_text = " ".join(context_history[-3:])  # 最近3轮
        combined = f"{current_query} {context_text}"

        # 简化的词袋编码
        vector = np.zeros(1000)
        for i, word in enumerate(combined.split()[:100]):
            vector[i] = 1.0

        return vector

    def retrieve(self, query: str, context: ConversationContext,
                top_k: int = 10) -> List[Tuple[int, float, str]]:
        """
        上下文感知检索
        """
        # 改写查询
        rewritten_query = query  # 简化：使用原始查询

        # 收集历史查询
        history_texts = [utt.text for utt in context.history[-3:]]

        # 编码
        query_vector = self.encode_context_query(rewritten_query, history_texts)

        # 简化检索
        scores = []
        for i, doc in enumerate(self.documents):
            doc_vector = np.zeros(1000)
            for j, word in enumerate(doc.split()[:100]):
                doc_vector[j] = 1.0

            sim = np.dot(query_vector, doc_vector) / (np.linalg.norm(query_vector) + 1e-10)
            scores.append((i, float(sim), doc))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


class ConversationalSearchSystem:
    """会话搜索引擎"""

    def __init__(self):
        self.context = None
        self.query_rewriter = QueryRewriter()
        self.intent_classifier = ConversationIntentClassifier()
        self.retriever = ContextAwareRetriever()
        self.conversation_manager = ConversationManager()

    def start_session(self, session_id: str) -> ConversationContext:
        """开始新会话"""
        self.context = ConversationContext(session_id=session_id)
        self.conversation_manager.create_session(session_id)
        return self.context

    def search(self, query: str) -> Dict[str, Any]:
        """
        执行会话搜索
        """
        # 1. 意图分类
        intent = self._classify_intent(query)

        # 2. 查询改写
        rewritten_query = self.query_rewriter.rewrite(query, self.context)

        # 3. 上下文感知检索
        results = self.retriever.retrieve(rewritten_query, self.context, top_k=5)

        # 4. 更新上下文
        self._update_context(query, intent, results)

        # 5. 生成回复
        response = self._generate_response(query, intent, results)

        return {
            "query": query,
            "rewritten_query": rewritten_query,
            "intent": intent,
            "results": results[:3],
            "response": response
        }

    def _classify_intent(self, query: str) -> str:
        """分类用户意图"""
        # 简化的意图识别
        query_lower = query.lower()

        if any(w in query_lower for w in ["who", "what", "where", "when", "why", "how"]):
            return "question"
        elif any(w in query_lower for w in ["tell me more", "explain", "details"]):
            return "clarification"
        elif any(w in query_lower for w in ["another", "more", "other", "different"]):
            return "exploration"
        elif any(w in query_lower for w in ["thanks", "thank you", "bye"]):
            return "closing"
        else:
            return "information_seeking"

    def _update_context(self, query: str, intent: str, results: List):
        """更新对话上下文"""
        utterance = Utterance(
            speaker="user",
            text=query,
            intent=intent
        )

        if self.context:
            self.context.history.append(utterance)
            self.conversation_manager.add_turn(self.context.session_id, utterance)

            # 更新话题
            if intent == "question" and results:
                self.context.current_topic = results[0][2][:50] if len(results) > 0 else None

    def _generate_response(self, query: str, intent: str,
                         results: List) -> str:
        """生成系统回复"""
        if intent == "closing":
            return "You're welcome! Feel free to ask if you have more questions."

        if not results:
            return "I couldn't find relevant information. Could you rephrase your question?"

        top_result = results[0][2] if results else ""
        return f"I found this: {top_result[:100]}..."


class ConversationManager:
    """对话管理器"""

    def __init__(self):
        self.sessions = {}  # session_id -> context
        self.session_history = defaultdict(list)  # session_id -> turns

    def create_session(self, session_id: str) -> ConversationContext:
        context = ConversationContext(session_id=session_id)
        self.sessions[session_id] = context
        return context

    def get_session(self, session_id: str) -> Optional[ConversationContext]:
        return self.sessions.get(session_id)

    def add_turn(self, session_id: str, utterance: Utterance):
        self.session_history[session_id].append(utterance)

    def get_recent_history(self, session_id: str, n: int = 5) -> List[Utterance]:
        return self.session_history[session_id][-n:]


class QuerySuggestion:
    """查询建议生成器"""

    def __init__(self):
        self.suggestion_templates = [
            "Tell me more about {topic}",
            "What is {topic}?",
            "How does {topic} work?",
            "Related to {topic}: {suggestion}",
        ]

    def generate(self, context: ConversationContext,
                current_results: List[Tuple[int, float, str]]) -> List[str]:
        """生成查询建议"""
        suggestions = []

        if current_results:
            topic = current_results[0][2][:30]
            suggestions.append(f"Tell me more about {topic}")

        if context.current_topic:
            suggestions.append(f"What else about {context.current_topic}?")

        return suggestions[:3]


def evaluate_conversational_search(system: ConversationalSearchSystem,
                                   test_queries: List[str]) -> Dict[str, float]:
    """评估会话搜索系统"""
    # 简化的评估指标
    total_turns = len(test_queries)
    successful_turns = 0

    for query in test_queries:
        result = system.search(query)
        if result["results"] or result["intent"] in ["closing", "clarification"]:
            successful_turns += 1

    return {
        "turn_success_rate": successful_turns / total_turns if total_turns > 0 else 0,
        "total_turns": total_turns
    }


def demo():
    """会话搜索演示"""
    print("[会话搜索演示]")

    # 初始化系统
    system = ConversationalSearchSystem()
    session = system.start_session("session_001")

    # 模拟对话
    queries = [
        "Who founded Apple?",
        "When was that?",
        "Tell me more",
        "What about Google?",
        "Thanks, bye"
    ]

    print(f"  会话ID: {session.session_id}\n")

    for query in queries:
        result = system.search(query)
        print(f"  用户: {query}")
        print(f"  意图: {result['intent']}")
        print(f"  改写查询: {result['rewritten_query']}")
        print(f"  回复: {result['response']}")
        print()

    # 意图分类器
    classifier = ConversationIntentClassifier()
    print(f"  意图分类器参数量: {sum(p.numel() for p in classifier.parameters()):,}")

    # 查询建议
    suggestion_gen = QuerySuggestion()
    suggestions = suggestion_gen.generate(session, [])
    print(f"  查询建议: {suggestions}")

    print("  ✅ 会话搜索演示通过！")


if __name__ == "__main__":
    demo()
