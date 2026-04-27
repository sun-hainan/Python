# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / tf_idf

本文件实现 tf_idf 相关的算法功能。
"""

from typing import List, Dict, Tuple, Set
from collections import Counter, defaultdict
import math


class TFIDFVectorizer:
    """
    TF-IDF向量化器
    """
    
    def __init__(self):
        self.documents: List[List[str]] = []      # 文档集合
        self.vocabulary: Dict[str, int] = {}      # 词到索引的映射
        self.idf: Dict[str, float] = {}          # 逆文档频率
        self.num_docs: int = 0                   # 文档数量
        self.tfidf_matrix: List[List[float]] = [] # TF-IDF矩阵
    
    def fit(self, documents: List[str]):
        """
        构建词汇表和IDF
        
        参数:
            documents: 文档列表
        """
        # 分词
        self.documents = [self._tokenize(doc) for doc in documents]
        self.num_docs = len(self.documents)
        
        # 构建词汇表
        vocab_set: Set[str] = set()
        for doc in self.documents:
            vocab_set.update(doc)
        
        self.vocabulary = {word: idx for idx, word in enumerate(sorted(vocab_set))}
        
        # 计算IDF
        doc_freq = Counter()
        for doc in self.documents:
            for word in set(doc):
                doc_freq[word] += 1
        
        # 计算IDF
        for word in self.vocabulary:
            df = doc_freq[word]
            self.idf[word] = math.log(self.num_docs / (df + 1)) + 1
        
        # 计算TF-IDF矩阵
        self._compute_tfidf_matrix()
    
    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词
        
        参数:
            text: 输入文本
        
        返回:
            单词列表
        """
        # 简单分词：小写化，按空格和标点分割
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def _compute_tfidf_matrix(self):
        """
        计算TF-IDF矩阵
        """
        self.tfidf_matrix = []
        
        for doc in self.documents:
            # 计算TF
            tf = Counter(doc)
            
            # 计算TF-IDF
            vector = [0.0] * len(self.vocabulary)
            for word, idx in self.vocabulary.items():
                tf_val = tf.get(word, 0)
                idf_val = self.idf.get(word, 1.0)
                vector[idx] = tf_val * idf_val
            
            # 归一化
            norm = math.sqrt(sum(v * v for v in vector))
            if norm > 0:
                vector = [v / norm for v in vector]
            
            self.tfidf_matrix.append(vector)
    
    def transform(self, document: str) -> List[float]:
        """
        将单个文档转换为TF-IDF向量
        
        参数:
            document: 输入文档
        
        返回:
            TF-IDF向量
        """
        tokens = self._tokenize(document)
        tf = Counter(tokens)
        
        vector = [0.0] * len(self.vocabulary)
        for word, idx in self.vocabulary.items():
            tf_val = tf.get(word, 0)
            idf_val = self.idf.get(word, 1.0)
            vector[idx] = tf_val * idf_val
        
        # 归一化
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        
        return vector
    
    def fit_transform(self, documents: List[str]) -> List[List[float]]:
        """
        拟合并转换
        
        参数:
            documents: 文档列表
        
        返回:
            TF-IDF矩阵
        """
        self.fit(documents)
        return self.tfidf_matrix
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量的余弦相似度
        
        参数:
            vec1: 第一个向量
            vec2: 第二个向量
        
        返回:
            余弦相似度
        """
        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
        norm1 = math.sqrt(sum(v * v for v in vec1))
        norm2 = math.sqrt(sum(v * v for v in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def most_important_words(self, document_idx: int, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        获取文档中最重要的词
        
        参数:
            document_idx: 文档索引
            top_k: 返回前k个词
        
        返回:
            [(词, TF-IDF值), ...]
        """
        if document_idx >= len(self.tfidf_matrix):
            return []
        
        vector = self.tfidf_matrix[document_idx]
        word_scores = []
        
        for word, idx in self.vocabulary.items():
            word_scores.append((word, vector[idx]))
        
        word_scores.sort(key=lambda x: -x[1])
        
        return word_scores[:top_k]


def compute_tf(text: str) -> Dict[str, float]:
    """
    计算词频（简化版本）
    
    参数:
        text: 输入文本
    
    返回:
        词频字典
    """
    import re
    tokens = re.findall(r'\b\w+\b', text.lower())
    total = len(tokens)
    
    if total == 0:
        return {}
    
    counter = Counter(tokens)
    return {word: count / total for word, count in counter.items()}


def compute_idf(documents: List[str]) -> Dict[str, float]:
    """
    计算逆文档频率
    
    参数:
        documents: 文档列表
    
    返回:
        IDF字典
    """
    num_docs = len(documents)
    
    # 统计文档频率
    doc_freq = Counter()
    
    for doc in documents:
        import re
        tokens = set(re.findall(r'\b\w+\b', doc.lower()))
        for word in tokens:
            doc_freq[word] += 1
    
    # 计算IDF
    idf = {}
    for word, df in doc_freq.items():
        idf[word] = math.log(num_docs / df) + 1
    
    return idf


def compute_tfidf(text: str, idf: Dict[str, float]) -> Dict[str, float]:
    """
    计算TF-IDF
    
    参数:
        text: 输入文本
        idf: 逆文档频率字典
    
    返回:
        TF-IDF字典
    """
    tf = compute_tf(text)
    return {word: tf_val * idf.get(word, 1.0) for word, tf_val in tf.items()}


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本TF-IDF
    print("=" * 50)
    print("测试1: TF-IDF向量化")
    print("=" * 50)
    
    documents = [
        "The cat sat on the mat",
        "The dog ran in the park",
        "A cat is a good pet",
        "Dogs are loyal animals"
    ]
    
    vectorizer = TFIDFVectorizer()
    matrix = vectorizer.fit_transform(documents)
    
    print(f"词汇表大小: {len(vectorizer.vocabulary)}")
    print(f"词汇表: {list(vectorizer.vocabulary.keys())[:10]}...")
    
    print("\nTF-IDF矩阵 (每行一个文档):")
    for i, doc in enumerate(documents):
        print(f"  文档{i}: {doc[:30]}...")
        vec = matrix[i]
        non_zero = [(j, f"{v:.3f}") for j, v in enumerate(vec) if v > 0][:5]
        print(f"    非零元素: {non_zero}...")
    
    # 测试用例2：文档相似度
    print("\n" + "=" * 50)
    print("测试2: 文档相似度计算")
    print("=" * 50)
    
    for i in range(len(documents)):
        for j in range(i + 1, len(documents)):
            sim = vectorizer.cosine_similarity(matrix[i], matrix[j])
            print(f"文档{i} vs 文档{j}: {sim:.4f}")
    
    # 测试用例3：重要词提取
    print("\n" + "=" * 50)
    print("测试3: 重要词提取")
    print("=" * 50)
    
    for i, doc in enumerate(documents):
        important = vectorizer.most_important_words(i, top_k=3)
        print(f"\n文档{i}: {doc}")
        print("  关键词:", ", ".join([f"{w}({s:.3f})" for w, s in important]))
    
    # 测试用例4：新文档转换
    print("\n" + "=" * 50)
    print("测试4: 新文档转换")
    print("=" * 50)
    
    new_doc = "The cat and the dog"
    new_vec = vectorizer.transform(new_doc)
    
    print(f"新文档: '{new_doc}'")
    print(f"向量维度: {len(new_vec)}")
    print(f"非零元素数: {sum(1 for v in new_vec if v > 0)}")
    
    # 找到最相似的文档
    best_sim = -1
    best_idx = -1
    for i, vec in enumerate(matrix):
        sim = vectorizer.cosine_similarity(new_vec, vec)
        if sim > best_sim:
            best_sim = sim
            best_idx = i
    
    print(f"最相似文档{best_idx}: '{documents[best_idx]}' (相似度: {best_sim:.4f})")
    
    # 测试用例5：IDF值分析
    print("\n" + "=" * 50)
    print("测试5: IDF值分析")
    print("=" * 50)
    
    print("IDF值 (按值排序):")
    sorted_idf = sorted(vectorizer.idf.items(), key=lambda x: x[1])
    for word, idf_val in sorted_idf[:10]:
        print(f"  {word}: {idf_val:.4f}")
    
    print("\n高IDF词 (区分度高):")
    for word, idf_val in sorted(vectorizer.idf.items(), key=lambda x: -x[1])[:5]:
        print(f"  {word}: {idf_val:.4f}")
    
    # 测试用例6：简单TF计算
    print("\n" + "=" * 50)
    print("测试6: 词频计算")
    print("=" * 50)
    
    text = "the cat sat on the mat the cat"
    tf = compute_tf(text)
    print(f"文本: '{text}'")
    print("词频:")
    for word, freq in sorted(tf.items(), key=lambda x: -x[1]):
        print(f"  {word}: {freq:.4f}")
