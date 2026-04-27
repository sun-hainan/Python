# -*- coding: utf-8 -*-

"""

算法实现：03_字符串算法 / autocomplete_using_trie



本文件实现 autocomplete_using_trie 相关的算法功能。

"""



from __future__ import annotations



END = "#"





class Trie:

    # Trie 类实现

    def __init__(self) -> None:

        self._trie: dict = {}



    def insert_word(self, text: str) -> None:

    # insert_word 函数实现

        trie = self._trie

        for char in text:

            if char not in trie:

                trie[char] = {}

            trie = trie[char]

        trie[END] = True



    def find_word(self, prefix: str) -> tuple | list:

    # find_word 函数实现

        trie = self._trie

        for char in prefix:

            if char in trie:

                trie = trie[char]

            else:

                return []

        return self._elements(trie)



    def _elements(self, d: dict) -> tuple:

        result = []

        for c, v in d.items():

            sub_result = [" "] if c == END else [(c + s) for s in self._elements(v)]

            result.extend(sub_result)

        return tuple(result)





trie = Trie()

words = ("depart", "detergent", "daring", "dog", "deer", "deal")

for word in words:

    trie.insert_word(word)





def autocomplete_using_trie(string: str) -> tuple:

    # autocomplete_using_trie 函数实现

    """

    >>> trie = Trie()

    >>> for word in words:

    ...     trie.insert_word(word)

    ...

    >>> matches = autocomplete_using_trie("de")

    >>> "detergent " in matches

    True

    >>> "dog " in matches

    False

    """

    suffixes = trie.find_word(string)

    return tuple(string + word for word in suffixes)





def main() -> None:

    # main 函数实现

    print(autocomplete_using_trie("de"))





if __name__ == "__main__":

    import doctest



    doctest.testmod()

    main()

