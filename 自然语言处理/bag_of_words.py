# -*- coding: utf-8 -*-

"""

算法实现：自然语言处理 / bag_of_words



本文件实现 bag_of_words 相关的算法功能。

"""



from typing import List, Dict, Set

from collections import Counter





class BagOfWords:

    """

    词袋模型

    """

    

    def __init__(self):

        self.vocabulary: Dict[str, int] = {}  # 词到索引

        self.documents: List[Counter] = []    # 文档词频列表

    

    def fit(self, documents: List[str]):

        """

        构建词汇表

        

        参数:

            documents: 文档列表

        """

        # 构建词汇表

        vocab_set = set()

        for doc in documents:

            tokens = self._tokenize(doc)

            vocab_set.update(tokens)

        

        self.vocabulary = {word: idx for idx, word in enumerate(sorted(vocab_set))}

    

    def transform(self, documents: List[str]) -> List[List[int]]:

        """

        转换文档为词频向量

        

        参数:

            documents: 文档列表

        

        返回:

            词频向量列表

        """

        vectors = []

        

        for doc in documents:

            tokens = self._tokenize(doc)

            counter = Counter(tokens)

            

            vector = [0] * len(self.vocabulary)

            for word, count in counter.items():

                if word in self.vocabulary:

                    vector[self.vocabulary[word]] = count

            

            vectors.append(vector)

        

        return vectors

    

    def _tokenize(self, text: str) -> List[str]:

        """简单分词"""

        import re

        return re.findall(r'\b\w+\b', text.lower())





if __name__ == "__main__":

    print("=" * 50)

    print("词袋模型演示")

    print("=" * 50)

    

    bow = BagOfWords()

    

    docs = [

        "the cat sat on the mat",

        "the dog ran in the park"

    ]

    

    bow.fit(docs)

    vectors = bow.transform(docs)

    

    print(f"词汇表: {bow.vocabulary}")

    print(f"向量1: {vectors[0]}")

    print(f"向量2: {vectors[1]}")

