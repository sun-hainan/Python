# -*- coding: utf-8 -*-

"""

算法实现：09_机器学习 / word_frequency_functions



本文件实现 word_frequency_functions 相关的算法功能。

"""



word_frequency_functions.py

"""



import string

from math import log10





def term_frequency(term: str, document: str) -> int:

    """

    Return the number of times a term occurs within a given document.

    @params: term, the term to search a document for, and document,

        the document to search within

    @returns: an integer representing the number of times a term is

        found within the document

    @examples:

    >>> term_frequency("to", "To be, or not to be")

    2

    """

    document_without_punctuation = document.translate(

        str.maketrans("", "", string.punctuation)

    ).replace("\n", "")

    tokenize_document = document_without_punctuation.split(" ")

    return len([word for word in tokenize_document if word.lower() == term.lower()])





def document_frequency(term: str, corpus: str) -> tuple[int, int]:

    """

    Calculate the number of documents in a corpus that contain a given term.

    @params: term, the term to search each document for, and corpus, a collection

        of documents. Each document should be separated by a newline.

    @returns: the number of documents containing the term and the total number of docs

    @examples:

    >>> document_frequency("first", "This is the first document.\\nThis is the second.\\nTHIS is the third.")

    (1, 3)

    """

    corpus_without_punctuation = corpus.lower().translate(

        str.maketrans("", "", string.punctuation)

    )

    docs = corpus_without_punctuation.split("\n")

    term = term.lower()

    return (len([doc for doc in docs if term in doc]), len(docs))





def inverse_document_frequency(df: int, n: int, smoothing=False) -> float:

    """

    Return a float denoting the importance of a word.

    Calculated by log10(N/df), where N is the number of documents

    and df is the Document Frequency.

    @params: df (Document Frequency), n (number of documents in corpus),

        smoothing (if True return smoothed IDF)

    @returns: log10(N/df) or 1+log10(N/(1+df))

    """

    if smoothing:

        if n == 0:

            raise ValueError("log10(0) is undefined.")

        return round(1 + log10(n / (1 + df)), 3)



    if df == 0:

        raise ZeroDivisionError("df must be > 0")

    elif n == 0:

        raise ValueError("log10(0) is undefined.")

    return round(log10(n / df), 3)





def tf_idf(tf: int, idf: int) -> float:

    """

    Combine term frequency and inverse document frequency.

    tf-idf = TF * IDF

    @params: tf (term frequency), idf (inverse document frequency)

    @examples:

    >>> tf_idf(2, 0.477)

    0.954

    """

    return round(tf * idf, 3)





if __name__ == "__main__":

    # 测试词频统计函数

    doc = "Hello world hello Python world"

    print(f"term_frequency('hello', doc) = {term_frequency('hello', doc)}")

    corpus = "Hello world\\nHello Python\\nWorld hello"

    print(f"document_frequency('hello', corpus) = {document_frequency('hello', corpus)}")

    print(f"inverse_document_frequency(3, 100) = {inverse_document_frequency(3, 100)}")

    print(f"tf_idf(5, 0.477) = {tf_idf(5, 0.477)}")

