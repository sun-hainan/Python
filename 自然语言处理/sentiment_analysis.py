# -*- coding: utf-8 -*-
"""
算法实现：自然语言处理 / sentiment_analysis

本文件实现 sentiment_analysis 相关的算法功能。
"""

from typing import List, Dict, Tuple, Optional
from collections import Counter, defaultdict
import math


class NaiveBayesSentimentAnalyzer:
    """
    朴素贝叶斯情感分析器
    """
    
    def __init__(self, alpha: float = 1.0):
        """
        初始化
        
        参数:
            alpha: 平滑参数（拉普拉斯平滑）
        """
        self.alpha = alpha
        self.vocabulary: Dict[str, int] = {}
        self.class_priors: Dict[str, float] = {}
        self.word_probs: Dict[Tuple[str, str], float] = {}
        self.classes: set = set()
        self.num_docs: int = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词
        
        参数:
            text: 输入文本
        
        返回:
            单词列表
        """
        import re
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def fit(self, documents: List[str], labels: List[str]):
        """
        训练模型
        
        参数:
            documents: 文档列表
            labels: 对应的标签列表
        """
        self.classes = set(labels)
        self.num_docs = len(documents)
        
        # 构建词汇表
        vocab_set = set()
        doc_word_counts = []
        
        for doc in documents:
            words = self._tokenize(doc)
            vocab_set.update(words)
            doc_word_counts.append(Counter(words))
        
        self.vocabulary = {word: idx for idx, word in enumerate(sorted(vocab_set))}
        vocab_size = len(self.vocabulary)
        
        # 计算类先验概率 P(c)
        class_counts = Counter(labels)
        for cls in self.classes:
            self.class_priors[cls] = class_counts[cls] / self.num_docs
        
        # 计算条件概率 P(word | class)
        for cls in self.classes:
            # 统计该类中每个词的出现次数
            word_counts = Counter()
            class_doc_count = 0
            
            for doc, label in zip(documents, labels):
                if label == cls:
                    class_doc_count += 1
                    for word in self._tokenize(doc):
                        word_counts[word] += 1
            
            # 计算 P(word | class) with 平滑
            total_words = sum(word_counts.values())
            
            for word in self.vocabulary:
                count = word_counts.get(word, 0)
                # 拉普拉斯平滑
                prob = (count + self.alpha) / (total_words + self.alpha * vocab_size)
                self.word_probs[(word, cls)] = prob
    
    def _compute_log_prob(self, text: str, cls: str) -> float:
        """
        计算文本属于某类的对数概率
        
        参数:
            text: 输入文本
            cls: 类别
        
        返回:
            log P(text | class) + log P(class)
        """
        words = self._tokenize(text)
        
        # log P(class)
        log_prob = math.log(self.class_priors.get(cls, 1e-10))
        
        # log P(words | class)
        for word in words:
            prob = self.word_probs.get((word, cls), self.alpha / self.alpha)
            log_prob += math.log(prob)
        
        return log_prob
    
    def predict(self, text: str) -> str:
        """
        预测文本的情感类别
        
        参数:
            text: 输入文本
        
        返回:
            预测类别
        """
        best_class = None
        best_prob = float('-inf')
        
        for cls in self.classes:
            prob = self._compute_log_prob(text, cls)
            if prob > best_prob:
                best_prob = prob
                best_class = cls
        
        return best_class
    
    def predict_proba(self, text: str) -> Dict[str, float]:
        """
        预测各类别的概率
        
        参数:
            text: 输入文本
        
        返回:
            {类别: 概率}
        """
        log_probs = {}
        
        for cls in self.classes:
            log_probs[cls] = self._compute_log_prob(text, cls)
        
        # 归一化（使用softmax）
        max_log = max(log_probs.values())
        
        normalized = {}
        total = 0.0
        
        for cls, log_p in log_probs.items():
            normalized[cls] = math.exp(log_p - max_log)
            total += normalized[cls]
        
        for cls in normalized:
            normalized[cls] /= total
        
        return normalized


class MultinomialNaiveBayes:
    """
    多项式朴素贝叶斯（更优化的实现）
    """
    
    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.feature_log_prob: Dict[str, List[float]] = {}
        self.class_log_prior: Dict[str, float] = {}
        self.classes: List[str] = []
        self.vocabulary: Dict[str, int] = {}
    
    def fit(self, X: List[List[str]], y: List[str]):
        """
        训练模型
        
        参数:
            X: 文档列表（每文档是词列表）
            y: 标签列表
        """
        self.classes = sorted(set(y))
        
        # 构建词汇表
        vocab_set = set()
        for doc in X:
            vocab_set.update(doc)
        self.vocabulary = {w: i for i, w in enumerate(sorted(vocab_set))}
        
        vocab_size = len(self.vocabulary)
        
        # 统计
        class_counts = Counter(y)
        word_counts = {cls: Counter() for cls in self.classes}
        
        for doc, label in zip(X, y):
            word_counts[label].update(doc)
        
        # 计算类先验
        for cls in self.classes:
            self.class_log_prior[cls] = math.log(class_counts[cls] / len(y))
        
        # 计算词概率
        for cls in self.classes:
            total_count = sum(word_counts[cls].values())
            log_prob = []
            
            for word, idx in self.vocabulary.items():
                count = word_counts[cls].get(word, 0)
                # 加法平滑
                prob = (count + self.alpha) / (total_count + self.alpha * vocab_size)
                log_prob.append(math.log(prob))
            
            self.feature_log_prob[cls] = log_prob
    
    def predict_log_proba(self, X: List[List[str]]) -> List[List[float]]:
        """
        预测对数概率
        
        参数:
            X: 文档列表
        
        返回:
            对数概率矩阵
        """
        results = []
        
        for doc in X:
            log_probs = []
            
            for cls in self.classes:
                # 类先验
                log_prob = self.class_log_prior[cls]
                
                # 词概率
                word_counter = Counter(doc)
                for word, count in word_counter.items():
                    if word in self.vocabulary:
                        idx = self.vocabulary[word]
                        log_prob += count * self.feature_log_prob[cls][idx]
                
                log_probs.append(log_prob)
            
            results.append(log_probs)
        
        return results
    
    def predict(self, X: List[List[str]]) -> List[str]:
        """
        预测
        
        参数:
            X: 文档列表
        
        返回:
            预测标签列表
        """
        log_probs = self.predict_log_proba(X)
        
        predictions = []
        for probs in log_probs:
            best_idx = max(range(len(probs)), key=lambda i: probs[i])
            predictions.append(self.classes[best_idx])
        
        return predictions


# ==================== 测试代码 ====================
if __name__ == "__main__":
    # 测试用例1：基本情感分析
    print("=" * 50)
    print("测试1: 朴素贝叶斯情感分析")
    print("=" * 50)
    
    # 训练数据
    train_docs = [
        "I love this movie, it's great",
        "This film is wonderful and fantastic",
        "What a great experience",
        "I really enjoyed this",
        "Best movie ever",
        
        "This is a terrible movie",
        "I hate this film, it's awful",
        "What a waste of time",
        "This is the worst film ever",
        "I didn't like it at all",
    ]
    
    train_labels = [
        "positive", "positive", "positive", "positive", "positive",
        "negative", "negative", "negative", "negative", "negative",
    ]
    
    # 训练
    analyzer = NaiveBayesSentimentAnalyzer(alpha=1.0)
    analyzer.fit(train_docs, train_labels)
    
    print(f"词汇表大小: {len(analyzer.vocabulary)}")
    print(f"类别: {analyzer.classes}")
    print(f"类先验: {analyzer.class_priors}")
    
    # 测试
    test_docs = [
        "I love this film",
        "This is terrible",
        "Great movie, highly recommend",
        "What a waste",
        "It's okay, not great not terrible"
    ]
    
    print("\n情感预测结果:")
    for doc in test_docs:
        pred = analyzer.predict(doc)
        proba = analyzer.predict_proba(doc)
        print(f"  '{doc}'")
        print(f"    预测: {pred}, 概率: {proba}")
    
    # 测试用例2：多项式朴素贝叶斯
    print("\n" + "=" * 50)
    print("测试2: 多项式朴素贝叶斯")
    print("=" * 50)
    
    # 准备词列表数据
    X_train = [
        ["love", "this", "movie", "great"],
        ["film", "wonderful", "fantastic"],
        ["great", "experience"],
        ["really", "enjoyed", "this"],
        ["best", "movie", "ever"],
        
        ["terrible", "movie"],
        ["hate", "film", "awful"],
        ["waste", "time"],
        ["worst", "film", "ever"],
        ["didn't", "like"],
    ]
    
    y_train = train_labels
    
    nb = MultinomialNaiveBayes(alpha=1.0)
    nb.fit(X_train, y_train)
    
    print(f"类别: {nb.classes}")
    
    # 测试
    X_test = [
        ["love", "film"],
        ["terrible", "waste"],
        ["good", "movie"],
    ]
    
    predictions = nb.predict(X_test)
    print("\n预测结果:")
    for doc, pred in zip(X_test, predictions):
        print(f"  {' '.join(doc)}: {pred}")
    
    # 测试用例3：概率分析
    print("\n" + "=" * 50)
    print("测试3: 概率分析")
    print("=" * 50)
    
    analyzer2 = NaiveBayesSentimentAnalyzer(alpha=1.0)
    analyzer2.fit(train_docs, train_labels)
    
    test_doc = "This movie is absolutely amazing"
    proba = analyzer2.predict_proba(test_doc)
    
    print(f"文本: '{test_doc}'")
    print(f"词汇: {analyzer2._tokenize(test_doc)}")
    print("\n各类别概率:")
    for cls, prob in sorted(proba.items(), key=lambda x: -x[1]):
        print(f"  {cls}: {prob:.4f}")
    
    # 测试用例4：词概率分析
    print("\n" + "=" * 50)
    print("测试4: 词概率分析")
    print("=" * 50)
    
    print("正面类别的特征概率 (部分):")
    for word, idx in sorted(analyzer2.vocabulary.items(), key=lambda x: x[1])[:10]:
        prob = analyzer2.word_probs.get((word, "positive"), 0)
        print(f"  P({word} | positive) = {prob:.6f}")
    
    # 测试用例5：置信度分析
    print("\n" + "=" * 50)
    print("测试5: 置信度分析")
    print("=" * 50)
    
    test_cases = [
        "I love it",
        "I hate it so much",
        "It was okay",
        "Perfect in every way",
        "Absolutely terrible and awful"
    ]
    
    for doc in test_cases:
        proba = analyzer.predict_proba(doc)
        pred = analyzer.predict(doc)
        confidence = proba[pred]
        print(f"'{doc}'")
        print(f"  预测: {pred}, 置信度: {confidence:.4f}")
