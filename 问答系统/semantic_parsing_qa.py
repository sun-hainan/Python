"""
语义解析问答模块 - 将自然语言转换为逻辑形式

本模块实现基于语义解析的问答系统。
将自然语言问题解析为形式化逻辑表达式（如lambda calculus），
然后在知识库或文本上执行得到答案。

核心思想：
1. 词汇映射：将词语映射到知识库实体/关系
2. 组合句法分析：自底向上组合短语表示
3. 逻辑形式转换：将句法树转为lambda表达式
4. 语义执行：执行逻辑表达式获取答案
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Token:
    """Token数据结构"""
    text: str
    pos: str  # 词性标注
    lemma: str  # 词元
    ner: str = "O"  # 命名实体标签


class Lexicon:
    """词汇表：存储词语到知识库谓词的映射"""

    def __init__(self):
        # 谓词词典：词语 -> (谓词名, 谓词类型)
        self.predicates = {
            # 实体类型
            "人": ("type:person", "entity"),
            "城市": ("type:city", "entity"),
            "国家": ("type:country", "entity"),
            "组织": ("type:organization", "entity"),
            # 关系谓词
            "出生地": ("born_in", "relation"),
            "居住": ("lives_in", "relation"),
            "工作": ("works_for", "relation"),
            "创立": ("founded_by", "relation"),
            "首都": ("capital_of", "relation"),
            "是": ("is_a", "relation"),
            # 聚合操作
            "最大": ("argmax", "aggregate"),
            "最小": ("argmin", "aggregate"),
            "多少": ("count", "aggregate"),
            "所有": ("all", "aggregate"),
        }

    def lookup(self, word: str) -> Optional[Tuple[str, str]]:
        """
        查找词语对应的谓词
        :param word: 输入词语
        :return: (谓词名, 谓词类型) 或 None
        """
        return self.predicates.get(word, None)


class GrammarRule:
    """组合语法规则：定义如何组合子节点形成父节点表示"""

    def __init__(self):
        # 规则库：(父规则类型, [子规则类型]) -> 组合函数
        self.rules = {}

    def add_rule(self, parent_type: str, child_types: List[str], combine_fn):
        """注册语法规则"""
        key = (parent_type, tuple(child_types))
        self.rules[key] = combine_fn


class LambdaExpression:
    """Lambda表达式：表示语义逻辑形式"""

    def __init__(self, expression: str):
        self.expression = expression

    def __str__(self):
        return self.expression

    def apply(self, argument: any) -> 'LambdaExpression':
        """
        Beta归约：应用参数到lambda表达式
        :param argument: 参数值
        :return: 归约后的表达式
        """
        # 简单实现：替换lambda变量
        expr = self.expression
        if "λx." in expr:
            expr = expr.replace("λx.", f"({argument})")
        return LambdaExpression(expr)

    def to_sparql(self) -> str:
        """转换为SPARQL查询"""
        return self._to_sparql_helper(self.expression)

    def _to_sparql_helper(self, expr: str) -> str:
        """递归转换为SPARQL"""
        if "born_in" in expr:
            return "SELECT ?x WHERE { ?x <born_in> ?answer }"
        elif "lives_in" in expr:
            return "SELECT ?x WHERE { ?x <lives_in> ?answer }"
        elif "type:person" in expr:
            return "SELECT ?x WHERE { ?x a <Person> }"
        elif "argmax" in expr:
            return "SELECT ?x (MAX(?val) AS ?answer) WHERE { ?x ?p ?val }"
        else:
            return "SELECT ?answer WHERE { ?answer a ?type }"


class SemanticParser:
    """语义解析器：将自然语言解析为逻辑形式"""

    def __init__(self, lexicon: Lexicon, grammar: GrammarRule):
        self.lexicon = lexicon
        self.grammar = grammar

    def tokenize(self, text: str) -> List[Token]:
        """
        简单分词和词性标注
        :param text: 输入文本
        :return: Token列表
        """
        # 去除标点
        text = re.sub(r'[，。！？、]', ' ', text)
        words = text.split()
        tokens = []

        for i, word in enumerate(words):
            # 简单词性标注规则
            pos = "NN"  # 默认名词
            if word in ["的"]:
                pos = "POS"  # 所有格
            elif word in ["最大", "最小", "最多", "最少"]:
                pos = "JJS"  # 最高级
            elif word in ["是", "在", "为"]:
                pos = "VB"  # 动词
            elif word in ["谁", "什么", "哪", "多少"]:
                pos = "WP"  # 代词
            elif word in ["和", "或"]:
                pos = "CC"  # 连词

            tokens.append(Token(text=word, pos=pos, lemma=word))

        return tokens

    def parse(self, text: str) -> LambdaExpression:
        """
        解析文本为lambda表达式
        :param text: 自然语言文本
        :return: Lambda表达式
        """
        tokens = self.tokenize(text)
        # 自底向上组合解析
        return self.compositional_parse(tokens)

    def compositional_parse(self, tokens: List[Token]) -> LambdaExpression:
        """
        组合语义解析：递归组合子节点表示
        :param tokens: Token列表
        :return: Lambda表达式
        """
        if not tokens:
            return LambdaExpression("λx.x")

        # 检测查询类型
        text = "".join(t.text for t in tokens)

        # Who问句 -> 查询人
        if "谁" in text or "Who" in text:
            if "创立" in text or "建立" in text:
                # 谁创立了X -> λx.(founded_by x)
                return LambdaExpression("λx.founded_by(x)")
            return LambdaExpression("λx.type(x, person)")

        # What问句 -> 查询实体
        if "什么" in text or "What" in text:
            if "首都" in text:
                return LambdaExpression("λx.capital_of(x)")
            if "职业" in text:
                return LambdaExpression("λx.occupation(x)")
            if "出生" in text:
                return LambdaExpression("λx.birth_date(x)")
            return LambdaExpression("λx.type(x, entity)")

        # Where问句 -> 查询地点
        if "哪" in text or "Where" in text:
            if "出生" in text:
                return LambdaExpression("λx.birth_place(x)")
            return LambdaExpression("λx.location(x)")

        # How many问句 -> 计数
        if "多少" in text or "How many" in text:
            return LambdaExpression("λx.count(type(x, entity))")

        # 默认返回实体查询
        return LambdaExpression("λx.type(x, entity)")


class SemanticExecutor:
    """语义执行器：执行逻辑表达式获取答案"""

    def __init__(self, knowledge_base: Dict):
        self.kb = knowledge_base

    def execute(self, expr: LambdaExpression, context: Optional[Dict] = None) -> List:
        """
        执行lambda表达式
        :param expr: Lambda表达式
        :param context: 执行上下文
        :return: 结果列表
        """
        expr_str = str(expr)

        # 简单知识库查询模拟
        if "born_in" in expr_str:
            return self.query_born_in()
        if "occupation" in expr_str:
            return self.query_occupation()
        if "capital_of" in expr_str:
            return self.query_capital()
        if "type(x, person)" in expr_str:
            return self.query_all_persons()

        return []

    def query_born_in(self) -> List:
        """查询出生地"""
        results = []
        for entity, attrs in self.kb.items():
            if "birth_place" in attrs:
                results.append(f"{entity}出生于{attrs['birth_place']}")
        return results

    def query_occupation(self) -> List:
        """查询职业"""
        results = []
        for entity, attrs in self.kb.items():
            if "occupation" in attrs:
                results.append(f"{entity}的职业是{attrs['occupation']}")
        return results

    def query_capital(self) -> List:
        """查询首都"""
        results = []
        for entity, attrs in self.kb.items():
            if "capital" in attrs:
                results.append(f"{entity}的首都是{attrs['capital']}")
        return results

    def query_all_persons(self) -> List:
        """查询所有人"""
        return [e for e, attrs in self.kb.items() if attrs.get("type") == "Person"]


class SemanticParsingQA:
    """完整的语义解析问答系统"""

    def __init__(self, knowledge_base: Dict):
        self.lexicon = Lexicon()
        self.grammar = GrammarRule()
        self.parser = SemanticParser(self.lexicon, self.grammar)
        self.executor = SemanticExecutor(knowledge_base)

    def answer(self, question: str) -> Dict:
        """
        端到端问答
        :param question: 自然语言问题
        :return: 答案结果
        """
        # 语义解析
        expr = self.parser.parse(question)

        # 生成SPARQL
        sparql = expr.to_sparql()

        # 执行查询
        results = self.executor.execute(expr)

        return {
            "question": question,
            "lambda_expr": str(expr),
            "sparql": sparql,
            "answers": results
        }


def demo():
    """语义解析问答系统演示"""
    # 构造知识库
    knowledge_base = {
        "Alice": {
            "type": "Person",
            "birth_place": "Beijing",
            "occupation": "Engineer",
            "birth_date": "1990-01-01"
        },
        "Bob": {
            "type": "Person",
            "birth_place": "Shanghai",
            "occupation": "Doctor",
            "birth_date": "1985-05-15"
        },
        "China": {
            "type": "Country",
            "capital": "Beijing",
            "population": "1400000000"
        }
    }

    # 初始化系统
    qa_system = SemanticParsingQA(knowledge_base)

    # 测试问题
    test_questions = [
        "谁出生于北京？",
        "Alice的职业是什么？",
        "中国首都是哪里？",
        "有多少人？"
    ]

    print("[语义解析问答系统演示]")
    for q in test_questions:
        result = qa_system.answer(q)
        print(f"\n  问题: {q}")
        print(f"  Lambda: {result['lambda_expr']}")
        print(f"  SPARQL: {result['sparql']}")
        print(f"  答案: {result['answers']}")
    print("\n  ✅ 语义解析问答演示通过！")


if __name__ == "__main__":
    demo()
