# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / crf



本文件实现 crf 相关的算法功能。

"""



import numpy as np

from typing import List, Tuple, Dict



def crf_score(x, y, weights):

    # crf_score function



    # crf_score function

    """Compute sequence score"""

    score = 0.0

    for position in range(len(x)):

        word = x[position]

        label = y[position]

        key = (f'word={word}', label)

        score += weights.get(key, 0)

        if position > 0:

            prev_word = x[position-1]

            key2 = (f'bigram={prev_word}_{word}', label)

            score += weights.get(key2, 0)

    return score



def viterbi_decode(x, n_labels, weights):

    """Viterbi decoding for CRF"""

    T = len(x)

    delta = np.zeros((T, n_labels))

    psi = np.zeros((T, n_labels), dtype=int)

    for label in range(n_labels):

        delta[0, label] = crf_score(x, [label], weights)

    for t in range(1, T):

        for j in range(n_labels):

            candidates = [(delta[t-1, i] + crf_score(x, [i, j], weights), i) for i in range(n_labels)]

            best_score, best_prev = max(candidates, key=lambda x: x[0])

            delta[t, j] = best_score

            psi[t, j] = best_prev

    best_path = [0] * T

    best_path[T-1] = np.argmax(delta[T-1])

    for t in range(T-2, -1, -1):

        best_path[t] = psi[t+1, best_path[t+1]]

    return best_path



if __name__ == '__main__':

    print('=== CRF test ===')

    x = ['Hello', 'World', 'This', 'is', 'Python']

    n_labels = 2

    weights = {

        ('word=Hello', 1): 1.0,

        ('word=World', 1): 1.0,

        ('bigram=Hello_World', 1): 0.5,

    }

    best_path = viterbi_decode(x, n_labels, weights)

    print(f'Input: {x}')

    print(f'Best labels: {best_path}')

