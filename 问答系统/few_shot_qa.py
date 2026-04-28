"""
少样本问答模块 - Prompt Learning

本模块实现基于Prompt Learning的少样本问答系统。
利用预训练语言模型，通过设计prompt模板和标签映射，
在极少标注数据的情况下完成问答任务。

核心方法：
1. Prompt设计：构造问题描述和答案格式模板
2. 标签映射：定义答案到标签词的映射
3. 答案评分：计算每个候选答案的概率
4. 上下文学习：利用少量示例引导模型
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional


class PromptTemplate:
    """Prompt模板：定义问答的输入格式"""

    def __init__(self, template: str, label_words: Dict[str, List[str]]):
        """
        :param template: Prompt模板字符串，如 "Question: {question} Answer: {answer}"
        :param label_words: 标签到答案词的映射，如 {"A": ["A", "option A"], "B": ["B", "option B"]}
        """
        self.template = template
        self.label_words = label_words

    def fill(self, question: str, answer: Optional[str] = None) -> str:
        """填充模板"""
        if answer is not None:
            return self.template.format(question=question, answer=answer)
        else:
            return self.template.format(question=question, answer="")

    def get_label_words(self, label: str) -> List[str]:
        """获取某标签对应的答案词"""
        return self.label_words.get(label, [])


class Verbalizer:
    """标签词管理器：将标签映射到模型词汇"""

    def __init__(self, label_to_words: Dict[str, List[str]], tokenizer):
        """
        :param label_to_words: 标签到词表的映射
        :param tokenizer: 分词器
        """
        self.label_to_words = label_to_words
        self.tokenizer = tokenizer
        # 反向映射：词到标签
        self.word_to_label = {}
        for label, words in label_to_words.items():
            for word in words:
                self.word_to_label[word.lower()] = label

    def get_label_score(self, logits: torch.Tensor, label: str) -> float:
        """
        计算某个标签的总得分
        :param logits: 模型输出的logits [vocab_size]
        :param label: 目标标签
        :return: 该标签的总概率
        """
        words = self.get_label_words(label)
        score = 0.0

        for word in words:
            word_ids = self.tokenizer.encode(word)
            for wid in word_ids:
                score += logits[wid].item()

        return score

    def get_label_scores_batch(self, logits: torch.Tensor) -> Dict[str, float]:
        """批量计算所有标签的得分"""
        scores = {}
        for label in self.label_to_words.keys():
            scores[label] = self.get_label_score(logits, label)
        return scores

    def get_label_words(self, label: str) -> List[str]:
        """获取标签对应的词"""
        return self.label_to_words.get(label, [])


class FewShotQA:
    """少样本问答系统"""

    def __init__(self, model, tokenizer, prompt_template: PromptTemplate, verbalizer: Verbalizer):
        """
        :param model: 预训练语言模型
        :param tokenizer: 分词器
        :param prompt_template: Prompt模板
        :param verbalizer: 标签词管理器
        """
        self.model = model
        self.tokenizer = tokenizer
        self.prompt_template = prompt_template
        self.verbalizer = verbalizer

    def predict(self, question: str, options: Optional[List[str]] = None) -> Dict:
        """
        预测答案
        :param question: 问题文本
        :param options: 选项列表（可选）
        :return: 预测结果
        """
        # 构造输入
        if options:
            # 多选题：构造带选项的prompt
            prompt = self.prompt_template.fill(question, "")
            input_text = prompt + " Options: " + ", ".join(options)
        else:
            prompt = self.prompt_template.fill(question, "")
            input_text = prompt

        # Tokenize
        inputs = self.tokenizer.encode(input_text, return_tensors="pt")

        # 前向传播
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(inputs)
            logits = outputs.logits[0]  # 最后一个token的logits

        # 计算每个标签的得分
        label_scores = self.verbalizer.get_label_scores_batch(logits)

        # 归一化为概率
        total = sum(label_scores.values())
        label_probs = {k: v / total for k, v in label_scores.items()}

        # 选择最高概率的标签
        pred_label = max(label_probs, key=label_probs.get)

        return {
            "question": question,
            "prediction": pred_label,
            "probabilities": label_probs,
            "scores": label_scores
        }


class InContextLearner:
    """上下文学习器：利用少量示例引导模型"""

    def __init__(self, model, tokenizer, num_demonstrations: int = 4):
        self.model = model
        self.tokenizer = tokenizer
        self.num_demonstrations = num_demonstrations
        self.demonstrations = []  # 存储示例 (question, answer) 对

    def add_demonstration(self, question: str, answer: str):
        """添加一个问答示例"""
        self.demonstrations.append((question, answer))

    def construct_prompt(self, question: str) -> str:
        """构造包含示例的prompt"""
        parts = []
        # 添加示例
        for q, a in self.demonstrations[:self.num_demonstrations]:
            parts.append(f"Q: {q}")
            parts.append(f"A: {a}\n")
        # 添加当前问题
        parts.append(f"Q: {question}")
        parts.append("A:")
        return "\n".join(parts)

    def predict(self, question: str) -> str:
        """基于上下文学习预测"""
        prompt = self.construct_prompt(question)

        # 编码输入
        inputs = self.tokenizer.encode(prompt, return_tensors="pt")

        # 生成答案（简化版：取最可能的next token）
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(inputs)
            logits = outputs.logits[0, -1, :]
            pred_id = logits.argmax(dim=-1).item()

        return self.tokenizer.decode([pred_id])


class PromptTuner(nn.Module):
    """Prompt微调器：可学习的soft prompt"""

    def __init__(self, vocab_size, embed_dim=128, num_prompt_tokens=20):
        super().__init__()
        self.num_prompt_tokens = num_prompt_tokens
        # 可学习的prompt token嵌入
        self.prompt_embeddings = nn.Embedding(num_prompt_tokens, embed_dim)
        # 初始化
        nn.init.normal_(self.prompt_embeddings.weight, mean=0, std=0.02)

    def forward(self, input_ids, embedding_layer):
        """
        前向传播：插入soft prompt
        :param input_ids: 输入token ids
        :param embedding_layer: 模型的词嵌入层
        :return: 带prompt的嵌入序列
        """
        batch_size = input_ids.size(0)

        # 原始嵌入
        inputs_embed = embedding_layer(input_ids)

        # 生成prompt嵌入
        prompt_ids = torch.arange(self.num_prompt_tokens, device=input_ids.device)
        prompt_ids = prompt_ids.unsqueeze(0).expand(batch_size, -1)
        prompt_embed = self.prompt_embeddings(prompt_ids)

        # 拼接：prompt + input
        combined = torch.cat([prompt_embed, inputs_embed], dim=1)

        return combined


class LMForClassification(nn.Module):
    """用于分类的语言模型（简化实现）"""

    def __init__(self, vocab_size, hidden_size=256, num_classes=3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers=2, batch_first=True, bidirectional=True)
        self.classifier = nn.Linear(hidden_size * 2, num_classes)

    def forward(self, input_ids):
        embed = self.embedding(input_ids)
        outputs, (h_n, _) = self.lstm(embed)
        # 取最后隐藏状态
        hidden = torch.cat([h_n[-2], h_n[-1]], dim=-1)
        return self.classifier(hidden)


def compute_prompt_acc(predictions: List[str], labels: List[str]) -> float:
    """计算Prompt QA准确率"""
    correct = sum(1 for p, l in zip(predictions, labels) if p == l)
    return correct / len(predictions) if predictions else 0.0


def demo():
    """少样本问答系统演示"""
    vocab_size = 5000
    embed_dim = 64
    hidden_size = 128

    print("[少样本问答演示]")

    # 定义prompt模板
    template = PromptTemplate(
        template="Question: {question} Answer: {answer}",
        label_words={
            "A": ["A", "option A"],
            "B": ["B", "option B"],
            "C": ["C", "option C"]
        }
    )

    # 模拟tokenizer
    class SimpleTokenizer:
        def encode(self, text):
            words = text.lower().split()
            return [hash(w) % vocab_size + 1 for w in words]
        def decode(self, ids):
            return " ".join(str(i) for i in ids)

    tokenizer = SimpleTokenizer()

    # 模拟verbalizer
    class SimpleVerbalizer:
        def __init__(self):
            self.label_to_words = {"A": ["a"], "B": ["b"], "C": ["c"]}
        def get_label_scores_batch(self, logits):
            return {"A": logits[10].item(), "B": logits[11].item(), "C": logits[12].item()}

    verbalizer = SimpleVerbalizer()

    # 模拟语言模型
    model = LMForClassification(vocab_size, hidden_size, num_classes=3)

    # 初始化少样本QA
    few_shot_qa = FewShotQA(model, tokenizer, template, verbalizer)

    # 预测
    result = few_shot_qa.predict("What is the capital of France?", options=["A", "B", "C"])
    print(f"  问题: {result['question']}")
    print(f"  预测: {result['prediction']}")
    print(f"  概率: {result['probabilities']}")

    # 上下文学习器
    in_context_learner = InContextLearner(model, tokenizer, num_demonstrations=2)
    in_context_learner.add_demonstration("What is 2+2?", "4")
    in_context_learner.add_demonstration("What is 3+3?", "6")
    prompt = in_context_learner.construct_prompt("What is 4+4?")
    print(f"\n  构造的Prompt:\n{prompt}")

    # Prompt Tuner
    prompt_tuner = PromptTuner(vocab_size, embed_dim, num_prompt_tokens=10)
    print(f"  Prompt Tuner参数: {sum(p.numel() for p in prompt_tuner.parameters()):,}")

    print("  ✅ 少样本问答演示通过！")


if __name__ == "__main__":
    demo()
