# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / ngram



本文件实现 ngram 相关的算法功能。

"""



def create_ngram(sentence: str, ngram_size: int) -> list[str]:

    # create_ngram function



    # create_ngram function

    # create_ngram 函数实现

    """

    Create ngrams from a sentence



    >>> create_ngram("I am a sentence", 2)

    ['I ', ' a', 'am', 'm ', ' a', 'a ', ' s', 'se', 'en', 'nt', 'te', 'en', 'nc', 'ce']

    >>> create_ngram("I am an NLPer", 2)

    ['I ', ' a', 'am', 'm ', ' a', 'an', 'n ', ' N', 'NL', 'LP', 'Pe', 'er']

    >>> create_ngram("This is short", 50)

    []

    """

    return [sentence[i : i + ngram_size] for i in range(len(sentence) - ngram_size + 1)]





if __name__ == "__main__":

    from doctest import testmod



    testmod()

