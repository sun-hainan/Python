# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / pos_tagging

本文件实现 pos_tagging 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import math


class HMMPosTagger:
    """
    基于HMM的词性标注器
    """
    
    def __init__(self):
        # 词性集合
        self.tags: set = set()
        
        # 词性到索引的映射
        self.tag_to_idx: Dict[str, int] = {}
        
        # 初始概率 P(tag)
        self.initial_probs: Dict[str, float] = {}
        
        # 转移概率 P(tag2 | tag1)
        self.transition_probs: Dict[Tuple[str, str], float] = {}
        
        # 发射概率 P(word | tag)
        self.emission_probs: Dict[Tuple[str, str], float] = {}
        
        # 平滑参数
        self.lambda_smooth = 0.1
        
        # 训练好的标志
        self.trained = False
    
    def train(self, sentences: List[List[Tuple[str, str]]]):
        """
        训练HMM模型
        
        参数:
            sentences: 训练数据，每个句子是[(词, 词性), ...]的列表
        """
        # 统计计数
        tag_counts: Dict[str, int] = defaultdict(int)
        initial_counts: Dict[str, int] = defaultdict(int)
        transition_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        emission_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        
        # 收集所有词性
        for sentence in sentences:
            for word, tag in sentence:
                self.tags.add(tag)
                tag_counts[tag] += 1
        
        # 建立索引映射
        self.tag_to_idx = {tag: idx for idx, tag in enumerate(sorted(self.tags))}
        
        # 统计初始概率
        for sentence in sentences:
            if sentence:
                first_word, first_tag = sentence[0]
                initial_counts[first_tag] += 1
        
        # 统计转移和发射概率
        for sentence in sentences:
            prev_tag = None
            for word, tag in sentence:
                # 初始概率
                if prev_tag is None:
                    initial_counts[tag] += 1
                else:
                    # 转移概率
                    transition_counts[(prev_tag, tag)] += 1
                
                # 发射概率
                emission_counts[(tag, word)] += 1
                prev_tag = tag
        
        # 计算概率（使用加法平滑）
        vocab_size = len(set(word for _, word in sum(sentences, [])))
        
        # 初始概率
        total_sentences = len(sentences)
        for tag in self.tags:
            self.initial_probs[tag] = (initial_counts[tag] + self.lambda_smooth) / (
                total_sentences + self.lambda_smooth * len(self.tags)
            )
        
        # 转移概率
        for tag1 in self.tags:
            for tag2 in self.tags:
                count = transition_counts[(tag1, tag2)]
                self.transition_probs[(tag1, tag2)] = (
                    count + self.lambda_smooth
                ) / (tag_counts[tag1] + self.lambda_smooth * len(self.tags))
        
        # 发射概率
        for tag in self.tags:
            for word, _ in sum(sentences, []):
                count = emission_counts[(tag, word)]
                self.emission_probs[(tag, word)] = (
                    count + self.lambda_smooth
                ) / (tag_counts[tag] + self.lambda_smooth * (vocab_size + 1))
        
        self.trained = True
    
    def viterbi(self, words: List[str]) -> List[str]:
        """
        Viterbi算法找最可能的词性序列
        
        参数:
            words: 词序列
        
        返回:
            词性序列
        """
        if not self.trained:
            raise RuntimeError("Model not trained yet")
        
        T = len(words)
        N = len(self.tags)
        
        if T == 0:
            return []
        
        # DP表：dp[t][s] = 到第t个词，状态为s的最大概率
        dp = [[float('-inf')] * N for _ in range(T)]
        
        # 回溯表
        backpointer = [[-1] * N for _ in range(T)]
        
        tag_list = sorted(self.tags)
        
        # 初始化第一列
        for s, tag in enumerate(tag_list):
            word = words[0]
            emit_prob = self.emission_probs.get((tag, word), self.lambda_smooth / 
                                                (self.lambda_smooth * (len(set(w for _, w in [])) + 1)))
            dp[0][s] = math.log(self.initial_probs.get(tag, 1e-10)) + math.log(emit_prob)
        
        # 动态规划
        for t in range(1, T):
            word = words[t]
            
            for s2, tag2 in enumerate(tag_list):
                max_prob = float('-inf')
                best_prev = -1
                
                for s1, tag1 in enumerate(tag_list):
                    trans_prob = self.transition_probs.get((tag1, tag2), 
                                                          self.lambda_smooth)
                    prob = dp[t-1][s1] + math.log(trans_prob)
                    
                    if prob > max_prob:
                        max_prob = prob
                        best_prev = s1
                
                emit_prob = self.emission_probs.get((tag2, word),
                                                   self.lambda_smooth)
                dp[t][s2] = max_prob + math.log(emit_prob)
                backpointer[t][s2] = best_prev
        
        # 找到最后一个时间步的最佳状态
        last_col = dp[T-1]
        best_last_state = max(range(N), key=lambda s: last_col[s])
        
        # 回溯
        best_path = [0] * T
        best_path[T-1] = best_last_state
        
        for t in range(T-2, -1, -1):
            best_path[t] = backpointer[t+1][best_path[t+1]]
        
        # 转换为词性序列
        return [tag_list[s] for s in best_path]
    
    def tag(self, sentence: str) -> List[Tuple[str, str]]:
        """
        对句子进行词性标注
        
        参数:
            sentence: 输入句子
        
        返回:
            [(词, 词性), ...]列表
        """
        words = sentence.split()
        tags = self.viterbi(words)
        return list(zip(words, tags))


def create_sample_training_data() -> List[List[Tuple[str, str]]]:
    """
    创建示例训练数据
    
    返回:
        训练数据列表
    """
    return [
        # 简单句子
        [('The', 'DET'), ('cat', 'N'), ('eats', 'V'), ('the', 'DET'), ('fish', 'N'), ('.', 'PUNCT')],
        [('The', 'DET'), ('dog', 'N'), ('runs', 'V'), ('.', 'PUNCT')],
        [('I', 'PRON'), ('see', 'V'), ('the', 'DET'), ('cat', 'N'), ('.', 'PUNCT')],
        [('The', 'DET'), ('cat', 'N'), ('sees', 'V'), ('the', 'DET'), ('dog', 'N'), ('.', 'PUNCT')],
        
        # 更多句子
        [('A', 'DET'), ('big', 'ADJ'), ('dog', 'N'), ('eats', 'V'), ('a', 'DET'), ('small', 'ADJ'), ('fish', 'N'), ('.', 'PUNCT')],
        [('The', 'DET'), ('big', 'ADJ'), ('cat', 'N'), ('sees', 'V'), ('a', 'DET'), ('small', 'ADJ'), ('fish', 'N'), ('.', 'PUNCT')],
        [('I', 'PRON'), ('am', 'V'), ('a', 'DET'), ('student', 'N'), ('.', 'PUNCT')],
        [('She', 'PRON'), ('is', 'V'), ('a', 'DET'), ('teacher', 'N'), ('.', 'PUNCT')],
        [('He', 'PRON'), ('is', 'V'), ('a', 'DET'), ('programmer', 'N'), ('.', 'PUNCT')],
        [('We', 'PRON'), ('are', 'V'), ('students', 'N'), ('.', 'PUNCT')],
    ]


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：训练和标注
    print("=" * 50)
    print("测试1: HMM词性标注")
    print("=" * 50)
    
    # 准备训练数据
    training_data = create_sample_training_data()
    
    # 创建并训练标注器
    tagger = HMMPosTagger()
    tagger.train(training_data)
    
    print("训练完成！")
    print(f"学习到的词性: {sorted(tagger.tags)}")
    
    # 测试标注
    test_sentences = [
        "The cat eats the fish .",
        "A big dog runs .",
        "I am a student .",
    ]
    
    print("\n词性标注结果:")
    for sentence in test_sentences:
        result = tagger.tag(sentence)
        print(f"\n句子: {sentence}")
        print("标注:", " / ".join([f"{w}({t})" for w, t in result]))
    
    # 测试用例2：概率信息
    print("\n" + "=" * 50)
    print("测试2: 模型概率")
    print("=" * 50)
    
    print("\n初始概率:")
    for tag, prob in sorted(tagger.initial_probs.items(), key=lambda x: -x[1])[:5]:
        print(f"  P({tag}) = {prob:.4f}")
    
    print("\n转移概率 (部分):")
    for (tag1, tag2), prob in list(tagger.transition_probs.items())[:5]:
        print(f"  P({tag2} | {tag1}) = {prob:.4f}")
    
    print("\n发射概率 (部分):")
    for (tag, word), prob in list(tagger.emission_probs.items())[:5]:
        print(f"  P({word} | {tag}) = {prob:.4f}")
    
    # 测试用例3：未知词处理
    print("\n" + "=" * 50)
    print("测试3: 未知词处理")
    print("=" * 50)
    
    test_sentence = "The strange animal runs ."
    result = tagger.tag(test_sentence)
    print(f"句子: {test_sentence}")
    print("标注:", " / ".join([f"{w}({t})" for w, t in result]))
    
    # 测试用例4：长句处理
    print("\n" + "=" * 50)
    print("测试4: 长句处理")
    print("=" * 50)
    
    training_data_extended = training_data + [
        [('The', 'DET'), ('quick', 'ADJ'), ('brown', 'ADJ'), ('fox', 'N'), 
         ('jumps', 'V'), ('over', 'P'), ('the', 'DET'), ('lazy', 'ADJ'), 
         ('dog', 'N'), ('.', 'PUNCT')],
        [('I', 'PRON'), ('like', 'V'), ('programming', 'N'), ('in', 'P'),
         ('Python', 'N'), ('.', 'PUNCT')],
    ]
    
    tagger2 = HMMPosTagger()
    tagger2.train(training_data_extended)
    
    test_sentence = "The quick brown fox jumps over the lazy dog ."
    result = tagger2.tag(test_sentence)
    print(f"句子: {test_sentence}")
    print("标注:", " / ".join([f"{w}({t})" for w, t in result]))
    
    # 测试用例5：中文标注（需要不同的训练数据）
    print("\n" + "=" * 50)
    print("测试5: 中文词性标注概念")
    print("=" * 50)
    
    # 中文训练数据示例
    chinese_data = [
        [('我', 'PRON'), ('爱', 'V'), ('中国', 'N'), ('。', 'PUNCT')],
        [('北京', 'N'), ('是', 'V'), ('中国', 'N'), ('的', 'DE'), ('首都', 'N'), ('。', 'PUNCT')],
    ]
    
    chinese_tagger = HMMPosTagger()
    chinese_tagger.train(chinese_data)
    
    print("注意：中文词性标注需要更大的训练语料库")
    print(f"学习到的词性: {chinese_tagger.tags}")
