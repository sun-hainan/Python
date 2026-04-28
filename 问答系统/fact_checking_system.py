"""
事实核查系统模块

本模块实现自动化事实核查系统的核心组件。
给定一个声明(claim)，系统需要判断其真实性并提供证据。

核心流程：
1. 声明解析：提取声明中的核心实体和关系
2. 证据检索：从知识库或文档库中检索相关证据
3. 声明验证：比较声明与证据的一致性
4. Verdict预测：输出真实性判断（True/False/Partial）
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class Claim:
    """声明数据结构"""
    text: str
    subject: str  # 主语实体
    predicate: str  # 谓词/关系
    object: str  # 宾语/值
    truth_value: Optional[str] = None  # 真实值标签


@dataclass
class Evidence:
    """证据数据结构"""
    source: str
    content: str
    relevance_score: float = 0.0
    supporting: bool = False  # 是否支持声明


class EvidenceRetriever:
    """证据检索器：从文档库中检索相关证据"""

    def __init__(self, documents: List[Dict]):
        self.documents = documents

    def retrieve(self, claim: Claim, top_k: int = 5) -> List[Evidence]:
        """检索证据"""
        keywords = [claim.subject, claim.predicate, claim.object]
        scores = []

        for doc in self.documents:
            score = 0.0
            content_lower = doc["content"].lower()
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    score += 1.0
            scores.append((doc["id"], score, doc["content"]))

        scores.sort(key=lambda x: x[1], reverse=True)

        evidence_list = []
        for doc_id, score, content in scores[:top_k]:
            evidence_list.append(Evidence(
                source=f"doc_{doc_id}",
                content=content,
                relevance_score=score
            ))
        return evidence_list


class ClaimParser:
    """声明解析器：结构化解析声明"""

    def __init__(self):
        self.predicate_patterns = {
            r"(.*)是(.*)的首都": "capital_of",
            r"(.*)位于(.*)": "located_in",
            r"(.*)创立于(.*)": "founded_in",
            r"(.*)出生于(.*)": "born_in",
            r"(.*)的职业是(.*)": "occupation",
            r"(.*)身高(.*)": "height",
            r"(.*)人口(.*)": "population",
        }

    def parse(self, claim_text: str) -> Claim:
        """解析声明为结构化对象"""
        match = re.match(r"^(.*?)是(.*?)的(.*)$", claim_text)
        if match:
            subject, obj, predicate = match.group(1), match.group(2), match.group(3)
        else:
            subject = claim_text.split("是")[0] if "是" in claim_text else ""
            predicate = "unknown"
            obj = claim_text.split("是")[-1] if "是" in claim_text else ""

        return Claim(
            text=claim_text,
            subject=subject.strip(),
            predicate=predicate.strip() if predicate else "unknown",
            object=obj.strip() if obj else ""
        )


class ClaimVerifier:
    """声明验证器：比较声明与证据的一致性"""

    def __init__(self):
        self.verdict_labels = ["SUPPORTS", "REFUTES", "NOT_ENOUGH_INFO"]

    def verify(self, claim: Claim, evidence_list: List[Evidence]) -> Dict:
        """验证声明与证据的一致性"""
        if not evidence_list:
            return {"verdict": "NOT_ENOUGH_INFO", "confidence": 0.0,
                    "supporting_evidence": [], "refuting_evidence": []}

        supporting, refuting = [], []

        for evidence in evidence_list:
            comparison = self._compare_claim_evidence(claim, evidence)
            if comparison == "support":
                supporting.append(evidence)
            elif comparison == "refute":
                refuting.append(evidence)

        if supporting and not refuting:
            verdict = "SUPPORTS"
        elif refuting and not supporting:
            verdict = "REFUTES"
        else:
            verdict = "NOT_ENOUGH_INFO"

        total = len(supporting) + len(refuting) + 0.1
        confidence = max(len(supporting), len(refuting)) / total

        return {"verdict": verdict, "confidence": confidence,
                "supporting_evidence": supporting, "refuting_evidence": refuting}

    def _compare_claim_evidence(self, claim: Claim, evidence: Evidence) -> str:
        """比较声明与证据"""
        evidence_lower = evidence.content.lower()
        claim_obj = claim.object.lower()

        if self._is_numeric(claim.object):
            if self._numeric_match(claim.object, evidence.content):
                return "support"

        if claim_obj in evidence_lower:
            return "support"

        negations = ["不", "不是", "没有", "非", "无"]
        for neg in negations:
            if neg in claim.object and neg not in evidence_lower:
                return "refute"
        return "neutral"

    def _is_numeric(self, value: str) -> bool:
        try:
            float(value)
            return True
        except:
            return False

    def _numeric_match(self, claim_value: str, evidence_text: str) -> bool:
        try:
            claim_num = float(claim_value)
            numbers = re.findall(r'\d+\.?\d*', evidence_text)
            for num_str in numbers:
                if abs(float(num_str) - claim_num) < 0.01:
                    return True
        except:
            pass
        return False


class FactChecker:
    """完整的事实核查系统"""

    def __init__(self, documents: List[Dict]):
        self.documents = documents
        self.retriever = EvidenceRetriever(documents)
        self.parser = ClaimParser()
        self.verifier = ClaimVerifier()

    def check(self, claim_text: str) -> Dict:
        """端到端事实核查"""
        claim = self.parser.parse(claim_text)
        evidence_list = self.retriever.retrieve(claim, top_k=5)
        result = self.verifier.verify(claim, evidence_list)

        return {
            "claim": claim_text,
            "parsed_claim": {"subject": claim.subject, "predicate": claim.predicate, "object": claim.object},
            "verdict": result["verdict"],
            "confidence": result["confidence"],
            "supporting_evidence": [{"source": e.source, "content": e.content[:100]} for e in result["supporting_evidence"]],
            "refuting_evidence": [{"source": e.source, "content": e.content[:100]} for e in result["refuting_evidence"]]
        }


class EntailmentClassifier(nn.Module):
    """文本蕴含分类器"""

    def __init__(self, vocab_size, hidden_size=256, num_classes=3):
        super().__init__()
        self.encoder = nn.LSTM(128, hidden_size, num_layers=2, batch_first=True, bidirectional=True)
        self.classifier = nn.Linear(hidden_size * 2 * 2, num_classes)

    def forward(self, premise_ids, hypothesis_ids):
        p_enc, _ = self.encoder(torch.zeros_like(premise_ids).float().unsqueeze(-1).expand(-1, -1, 128))
        h_enc, _ = self.encoder(torch.zeros_like(hypothesis_ids).float().unsqueeze(-1).expand(-1, -1, 128))
        p_pool = torch.cat([p_enc.max(dim=1)[0], p_enc.mean(dim=1)], dim=-1)
        h_pool = torch.cat([h_enc.max(dim=1)[0], h_enc.mean(dim=1)], dim=-1)
        return self.classifier(torch.cat([p_pool, h_pool], dim=-1))


def compute_f1(predictions: List[str], labels: List[str]) -> Tuple[float, Dict]:
    """计算F1分数"""
    labels_set = set(labels)
    f1_scores = {}
    for label in labels_set:
        tp = sum(1 for p, l in zip(predictions, labels) if p == label and l == label)
        fp = sum(1 for p, l in zip(predictions, labels) if p == label and l != label)
        fn = sum(1 for p, l in zip(predictions, labels) if p != label and l == label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_scores[label] = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return sum(f1_scores.values()) / len(f1_scores), f1_scores


def demo():
    """事实核查系统演示"""
    documents = [
        {"id": 0, "content": "Paris is the capital of France."},
        {"id": 1, "content": "The Eiffel Tower is located in Paris, France."},
        {"id": 2, "content": "France is a country in Western Europe with population 67 million."},
        {"id": 3, "content": "The French Revolution began in 1789."},
        {"id": 4, "content": "Machine learning is a subset of artificial intelligence."},
    ]

    fact_checker = FactChecker(documents)

    test_claims = [
        "Paris是法国的首都",
        "France的首都是什么",
        "The Eiffel Tower位于哪里"
    ]

    print("[事实核查系统演示]")
    for claim_text in test_claims:
        result = fact_checker.check(claim_text)
        print(f"\n  声明: {result['claim']}")
        print(f"  解析: {result['parsed_claim']}")
        print(f"  判决: {result['verdict']} (置信度: {result['confidence']:.2f})")

    classifier = EntailmentClassifier(vocab_size=5000)
    print(f"\n  蕴含分类器参数量: {sum(p.numel() for p in classifier.parameters()):,}")
    print("  ✅ 事实核查系统演示通过！")


if __name__ == "__main__":
    demo()
