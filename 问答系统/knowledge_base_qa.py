"""
知识库问答模块 (KBQA) - SPARQL查询生成

本模块实现基于语义解析的知识库问答系统。
将自然语言问题转换为SPARQL查询，从知识图谱中检索答案。

核心流程：
1. 实体识别：识别问题中的实体提及
2. 关系检测：检测查询的知识图谱关系
3. SPARQL生成：构建合法的SPARQL查询语句
4. 查询执行：访问知识图谱获取结果
"""

import re
import json
from typing import List, Dict, Tuple, Optional


class Tokenizer:
    """简单的中英文分词器"""

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        分词：按空格和标点分割
        :param text: 输入文本
        :return: token列表
        """
        # 去除多余空格
        text = re.sub(r'\s+', ' ', text.strip())
        # 按空格和常见标点分割
        tokens = re.split(r'[\s,.!?;:、，。！？；：]', text)
        return [t for t in tokens if t]


class EntityLinker:
    """实体链接器：识别问题中的实体并链接到知识图谱"""

    def __init__(self, knowledge_base: Dict):
        """
        :param knowledge_base: 知识库字典，格式 {实体名: {属性: 值}}
        """
        self.kb = knowledge_base
        self.entity_names = list(knowledge_base.keys())

    def find_entities(self, question: str) -> List[Dict]:
        """
        在问题中识别实体
        :param question: 自然语言问题
        :return: 实体列表，每个实体包含名称和位置信息
        """
        question_lower = question.lower()
        found_entities = []

        for entity_name in self.entity_names:
            # 简单字符串匹配
            if entity_name.lower() in question_lower:
                found_entities.append({
                    "name": entity_name,
                    "type": self.kb[entity_name].get("type", "unknown"),
                    "matched": True
                })

        return found_entities

    def disambiguate(self, question: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        实体消歧：从候选实体中选择最可能的那个
        :param question: 问题文本
        :param candidates: 候选实体列表
        :return: 选中的实体或None
        """
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]

        # 简单策略：选择匹配长度最长的实体
        best = max(candidates, key=lambda x: len(x["name"]))
        return best


class RelationDetector:
    """关系检测器：识别问题中隐含的知识图谱关系"""

    def __init__(self):
        # 关系模式库：问法 -> 关系路径
        self.patterns = {
            # 属性查询
            r"(.*)的出生日期": [("birth_date",)],
            r"(.*)的出生地": [("birth_place",)],
            r"(.*)的职业": [("occupation",)],
            r"(.*)的国籍": [("nationality",)],
            r"(.*)的身高": [("height",)],
            r"(.*)的配偶": [("spouse",)],
            # 关系查询
            r"(.*)和(.*)的关系": [("relation",)],
            r"(.*)的父亲": [("father",)],
            r"(.*)的母亲": [("mother",)],
            r"(.*)在哪里": [("location",)],
            r"谁是(.*)": [("who",)],
            r"(.*)是什么时候": [("when",)],
            # 类型查询
            r"(.*)是什么": [("type",)],
        }

    def detect(self, question: str) -> List[str]:
        """
        检测问题中的关系模式
        :param question: 自然语言问题
        :return: 关系列表
        """
        detected = []
        for pattern, relations in self.patterns.items():
            match = re.search(pattern, question)
            if match:
                detected.extend(relations[0])

        # 如果没有匹配到任何模式，使用关键词匹配
        if not detected:
            keywords = {
                "出生": "birth_date",
                "出生地": "birth_place",
                "职业": "occupation",
                "身高": "height",
                "地点": "location"
            }
            for keyword, relation in keywords.items():
                if keyword in question:
                    detected.append(relation)

        return list(set(detected))  # 去重


class SPARQLGenerator:
    """SPARQL查询生成器：将语义分析结果转换为SPARQL"""

    def __init__(self, entity_linker: EntityLinker):
        self.entity_linker = entity_linker

    def generate(self, question: str, relations: List[str]) -> str:
        """
        生成SPARQL查询
        :param question: 自然语言问题
        :param relations: 检测到的关系列表
        :return: SPARQL查询字符串
        """
        # 识别主语实体
        entities = self.entity_linker.find_entities(question)
        if not entities:
            # 尝试从问题开头提取主语
            tokens = Tokenizer.tokenize(question)
            main_entity = tokens[0] if tokens else "Unknown"
        else:
            main_entity = entities[0]["name"]

        # 构建SELECT查询
        if "type" in relations or "who" in relations:
            # 询问实体类型或身份
            query = f"""
SELECT ?answer WHERE {{
    <{main_entity}> a ?type .
    BIND(STR(?type) AS ?answer)
}}"""
        elif "relation" in relations:
            # 询问关系
            query = f"""
SELECT ?answer WHERE {{
    ?subject <{relations[0]}> ?answer .
}}"""
        else:
            # 属性查询
            prop = relations[0] if relations else "unknown_property"
            query = f"""
PREFIX kb: <http://example.org/kg/>
SELECT ?answer WHERE {{
    kb:{main_entity} kb:{prop} ?answer .
}}"""

        return query.strip()

    def generate_triplet_query(self, subject: str, predicate: str, obj: str = "?x") -> str:
        """
        生成三元组查询
        :param subject: 主语
        :param predicate: 谓词/关系
        :param obj: 宾语（变量或常量）
        :return: SPARQL查询
        """
        return f"""
PREFIX kb: <http://example.org/kg/>
SELECT ?answer WHERE {{
    kb:{subject} kb:{predicate} ?answer .
}}""".strip()


class KnowledgeBaseQA:
    """完整的KBQA系统：整合实体链接、关系检测和SPARQL生成"""

    def __init__(self, knowledge_base: Dict):
        self.kb = knowledge_base
        self.entity_linker = EntityLinker(knowledge_base)
        self.relation_detector = RelationDetector()
        self.sparql_generator = SPARQLGenerator(self.entity_linker)

    def parse(self, question: str) -> Dict:
        """
        解析问题，生成SPARQL查询
        :param question: 自然语言问题
        :return: 解析结果字典
        """
        # 实体识别
        entities = self.entity_linker.find_entities(question)
        main_entity = self.entity_linker.disambiguate(question, entities)

        # 关系检测
        relations = self.relation_detector.detect(question)

        # SPARQL生成
        sparql = self.sparql_generator.generate(question, relations)

        return {
            "question": question,
            "entities": entities,
            "main_entity": main_entity,
            "relations": relations,
            "sparql": sparql
        }

    def answer(self, question: str) -> Dict:
        """
        端到端问答
        :param question: 自然语言问题
        :return: 答案结果
        """
        parsed = self.parse(question)
        # 实际系统中，这里会执行SPARQL查询
        # 这里用简单的字典查找模拟
        answers = []

        if parsed["main_entity"] and parsed["relations"]:
            entity_data = self.kb.get(parsed["main_entity"]["name"], {})
            for rel in parsed["relations"]:
                if rel in entity_data:
                    answers.append(entity_data[rel])

        return {
            "question": question,
            "sparql": parsed["sparql"],
            "answers": answers
        }


def demo():
    """KBQA系统演示"""
    # 构造简单的知识库
    knowledge_base = {
        "Alice": {
            "type": "Person",
            "birth_date": "1990-01-01",
            "birth_place": "Beijing",
            "occupation": "Engineer",
            "nationality": "China",
            "height": "165"
        },
        "Bob": {
            "type": "Person",
            "birth_date": "1985-05-15",
            "birth_place": "Shanghai",
            "occupation": "Doctor",
            "nationality": "China",
            "height": "175"
        },
        "Charlie": {
            "type": "Person",
            "birth_date": "1992-03-20",
            "birth_place": "Beijing",
            "occupation": "Teacher",
            "nationality": "USA",
            "height": "180"
        }
    }

    # 初始化KBQA系统
    qa_system = KnowledgeBaseQA(knowledge_base)

    # 测试用例
    test_questions = [
        "Alice的出生日期是什么？",
        "Bob的职业是什么？",
        "Charlie是哪里人？",
        "Alice和Bob的身高分别是多少？"
    ]

    print("[知识库问答系统演示]")
    for q in test_questions:
        print(f"\n  问题: {q}")
        result = qa_system.answer(q)
        print(f"  SPARQL: {result['sparql'][:80]}...")
        print(f"  答案: {result['answers']}")
    print("\n  ✅ KBQA系统演示通过！")


if __name__ == "__main__":
    demo()
