# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / lda_topic_model



本文件实现 lda_topic_model 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple



class LDA:

    # LDA class



    # LDA class

    def __init__(self, n_topics, alpha=0.1, beta=0.01):

    # __init__ function



    # __init__ function

        self.n_topics = n_topics

        self.alpha = alpha

        self.beta = beta



    def fit(self, documents, n_iter=50):

    # fit function



    # fit function

        self.n_vocab = max(w for doc in documents for w in doc) + 1

        n_docs = len(documents)

        topic_word_count = np.zeros((self.n_topics, self.n_vocab))

        doc_topic_count = np.zeros((n_docs, self.n_topics))

        doc_total_count = np.zeros(n_docs)

        z = []

        for d, doc in enumerate(documents):

            z_d = []

            for w in doc:

                k = np.random.randint(self.n_topics)

                z_d.append(k)

                topic_word_count[k, w] += 1

                doc_topic_count[d, k] += 1

                doc_total_count[d] += 1

            z.append(z_d)

        for iteration in range(n_iter):

            for d, doc in enumerate(documents):

                for n, w in enumerate(doc):

                    k = z[d][n]

                    topic_word_count[k, w] -= 1

                    doc_topic_count[d, k] -= 1

                    probs = np.zeros(self.n_topics)

                    for k_new in range(self.n_topics):

                        numerator = (topic_word_count[k_new, w] + self.beta) / (topic_word_count[k_new].sum() + self.n_vocab * self.beta)

                        numerator *= (doc_topic_count[d, k_new] + self.alpha) / (doc_total_count[d] + self.n_topics * self.alpha)

                        probs[k_new] = numerator

                    probs /= probs.sum()

                    k_new = np.random.choice(self.n_topics, p=probs)

                    z[d][n] = k_new

                    topic_word_count[k_new, w] += 1

                    doc_topic_count[d, k_new] += 1

        self.phi = (topic_word_count + self.beta) / (topic_word_count.sum(axis=1, keepdims=True) + self.n_vocab * self.beta)

        self.theta = (doc_topic_count + self.alpha) / (doc_topic_count.sum(axis=1, keepdims=True) + self.n_topics * self.alpha)



    def get_top_words(self, vocab, n_words=10):

    # get_top_words function



    # get_top_words function

        results = []

        for k in range(self.n_topics):

            top_indices = np.argsort(self.phi[k])[::-1][:n_words]

            top_words = [(vocab[i], self.phi[k, i]) for i in top_indices]

            results.append(top_words)

        return results



if __name__ == '__main__':

    print('=== LDA test ===')

    np.random.seed(42)

    documents = [[0, 1, 2, 3, 4], [0, 1, 5, 6, 7], [2, 3, 8, 9, 10], [4, 5, 8, 11, 12]]

    vocab = ['government', 'policy', 'economy', 'market', 'tech', 'company', 'innovation', 'stock', 'investment', 'bank', 'enterprise', 'AI', 'data']

    lda = LDA(n_topics=2)

    lda.fit(documents, n_iter=30)

    print('Topic words:')

    for k, topic_words in enumerate(lda.get_top_words(vocab, 5)):

        print(f'  Topic {k}: {topic_words}')

