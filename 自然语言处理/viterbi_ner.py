# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / viterbi_ner

本文件实现 viterbi_ner 相关的算法功能。
"""

import numpy as np
from collections import defaultdict


class ViterbiNER:
    """基于 Viterbi 的命名实体识别器（使用 HMM）"""

    def __init__(self):
        # 状态集合（IOB 标注：B-PER, I-PER, B-LOC, I-LOC, O, ...）
        self.states = []
        self.state_to_idx = {}
        self.idx_to_state = {}

        # 词到索引
        self.word_to_idx = {}
        self.idx_to_word = {}

        # HMM 参数
        self.init_prob = {}  # π[s] = P(s_1 = s)
        self.trans_prob = {}  # trans_prob[prev_s][s] = P(s | prev_s)
        self.emit_prob = {}  # emit_prob[s][word] = P(word | s)

        self._fitted = False

    def fit(self, sentences, tags):
        """训练 HMM-NER 模型
        sentences: List[List[str]]，分词后的句子列表
        tags: List[List[str]]，对应的标注列表
        """
        # 收集词汇和状态
        word_counts = defaultdict(int)
        state_counts = defaultdict(int)
        trans_counts = defaultdict(lambda: defaultdict(int))
        emit_counts = defaultdict(lambda: defaultdict(int))
        init_counts = defaultdict(int)

        for sent, tag_seq in zip(sentences, tags):
            prev_tag = None
            for word, tag in zip(sent, tag_seq):
                word_counts[word] += 1
                state_counts[tag] += 1
                emit_counts[tag][word] += 1
                trans_counts[prev_tag][tag] += 1
                if prev_tag is None:
                    init_counts[tag] += 1
                prev_tag = tag

        # 建立索引
        for word in word_counts:
            if word not in self.word_to_idx:
                self.word_to_idx[word] = len(self.word_to_idx)
        self.idx_to_word = {v: k for k, v in self.word_to_idx.items()}

        for state in state_counts:
            if state not in self.state_to_idx:
                idx = len(self.state_to_idx)
                self.state_to_idx[state] = idx
                self.idx_to_state[idx] = state

        vocab_size = len(self.word_to_idx)
        state_size = len(self.state_to_idx)

        # 平滑参数
        eps = 1e-8

        # 初始概率
        total_init = sum(init_counts.values())
        for state, idx in self.state_to_idx.items():
            self.init_prob[idx] = (init_counts.get(state, 0) + eps) / (total_init + eps * state_size)

        # 转移概率
        for prev_idx in range(state_size):
            prev_state = self.idx_to_state[prev_idx]
            total = sum(trans_counts[prev_state].values())
            self.trans_prob[prev_idx] = {}
            for curr_idx in range(state_size):
                curr_state = self.idx_to_state[curr_idx]
                count = trans_counts[prev_state].get(curr_state, 0)
                self.trans_prob[prev_idx][curr_idx] = (count + eps) / (total + eps * state_size)

        # 发射概率（使用 Add-1 平滑）
        for state_idx in range(state_size):
            state = self.idx_to_state[state_idx]
            total_emit = sum(emit_counts[state].values())
            self.emit_prob[state_idx] = {}
            for word, idx in self.word_to_idx.items():
                count = emit_counts[state].get(word, 0)
                self.emit_prob[state_idx][idx] = (count + eps) / (total_emit + eps * vocab_size)

        self._fitted = True
        return self

    def viterbi_decode(self, sentence):
        """Viterbi 解码：找出最优标注序列
        返回: List[str] 最优标签序列
        """
        T = len(sentence)
        state_size = len(self.state_to_idx)

        # 将词转换为索引（未知词用均匀分布）
        word_indices = []
        for word in sentence:
            idx = self.word_to_idx.get(word, -1)
            word_indices.append(idx)

        # DP 表：dp[t][s] = 到第 t 个词、状态为 s 的最大概率
        dp = np.full((T, state_size), -np.inf)
        # 回溯表：backpointer[t][s] = 前一个最优状态
        backpointer = np.zeros((T, state_size), dtype=int)

        # 初始化 t=0
        for s in range(state_size):
            emit = self.emit_prob[s].get(word_indices[0], 1.0 / len(self.word_to_idx))
            dp[0][s] = np.log(self.init_prob.get(s, 1e-8) + 1e-8) + np.log(emit + 1e-8)

        # 动态规划
        for t in range(1, T):
            for curr_s in range(state_size):
                best_prev_s = 0
                best_score = -np.inf
                for prev_s in range(state_size):
                    # 概率 = dp[t-1][prev_s] * trans_prob[prev_s][curr_s] * emit_prob[curr_s][word]
                    trans = self.trans_prob.get(prev_s, {}).get(curr_s, 1e-8)
                    emit = self.emit_prob[curr_s].get(word_indices[t], 1.0 / len(self.word_to_idx))
                    score = dp[t - 1][prev_s] + np.log(trans + 1e-8) + np.log(emit + 1e-8)
                    if score > best_score:
                        best_score = score
                        best_prev_s = prev_s
                dp[t][curr_s] = best_score
                backpointer[t][curr_s] = best_prev_s

        # 回溯
        best_path = [0] * T
        best_last_state = int(np.argmax(dp[T - 1]))
        best_path[T - 1] = best_last_state
        for t in range(T - 2, -1, -1):
            best_path[t] = backpointer[t + 1][best_path[t + 1]]

        # 转换为标签
        return [self.idx_to_state[s] for s in best_path]


def demo():
    """NER 示例"""
    # 训练数据（简单中文命名实体数据）
    sentences = [
        ["北", "京", "是", "中", "国", "的", "首", "都"],
        ["张", "三", "在", "北", "京", "工", "作"],
        ["上", "海", "是", "一", "座", "大", "城", "市"],
        ["李", "四", "毕", "业", "于", "清", "华", "大", "学"],
        ["机", "器", "学", "习", "是", "一", "门", "技", "术"],
    ]
    # IOB 标注：B-LOC(I-LOC)* = 地点, B-PER(I-PER)* = 人名, O = 其他
    tags = [
        ["B-LOC", "I-LOC", "O", "O", "O", "O", "O", "O"],
        ["B-PER", "I-PER", "O", "B-LOC", "I-LOC", "O", "O"],
        ["B-LOC", "I-LOC", "O", "O", "O", "O", "O", "O"],
        ["B-PER", "I-PER", "O", "O", "O", "B-ORG", "I-ORG", "I-ORG", "I-ORG"],
        ["O", "O", "O", "O", "O", "O", "O", "O", "O"],
    ]

    ner = ViterbiNER()
    ner.fit(sentences, tags)

    # 测试
    test_sentences = [
        ["北", "京", "今", "天", "很", "热"],
        ["张", "三", "去", "了", "上", "海"],
    ]
    print("NER 识别结果:")
    for sent in test_sentences:
        pred_tags = ner.viterbi_decode(sent)
        entities = []
        current_entity = []
        current_type = None
        for word, tag in zip(sent, pred_tags):
            if tag.startswith("B-"):
                if current_entity:
                    entities.append(("".join(current_entity), current_type))
                current_entity = [word]
                current_type = tag[2:]
            elif tag.startswith("I-") and current_type == tag[2:]:
                current_entity.append(word)
            else:
                if current_entity:
                    entities.append(("".join(current_entity), current_type))
                    current_entity = []
                    current_type = None
        if current_entity:
            entities.append(("".join(current_entity), current_type))
        print(f"  句子: {''.join(sent)}")
        print(f"  标签: {pred_tags}")
        print(f"  实体: {entities}")


if __name__ == "__main__":
    demo()
