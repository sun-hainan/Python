# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / boyer_moore_search

本文件实现 boyer_moore_search 相关的算法功能。
"""

class BoyerMooreSearch:
    # BoyerMooreSearch 类实现
    """
    Example usage:

        bms = BoyerMooreSearch(text="ABAABA", pattern="AB")
        positions = bms.bad_character_heuristic()

    where 'positions' contain the locations where the pattern was matched.
    """

    def __init__(self, text: str, pattern: str):
        self.text, self.pattern = text, pattern
        self.textLen, self.patLen = len(text), len(pattern)

    def match_in_pattern(self, char: str) -> int:
    # match_in_pattern 函数实现
        """
        Finds the index of char in pattern in reverse order.

        Parameters :
            char (chr): character to be searched

        Returns :
            i (int): index of char from last in pattern
            -1 (int): if char is not found in pattern

        >>> bms = BoyerMooreSearch(text="ABAABA", pattern="AB")
        >>> bms.match_in_pattern("B")
        1
        """

        for i in range(self.patLen - 1, -1, -1):
            if char == self.pattern[i]:
                return i
        return -1

    def mismatch_in_text(self, current_pos: int) -> int:
    # mismatch_in_text 函数实现
        """
        Find the index of mis-matched character in text when compared with pattern
        from last.

        Parameters :
            current_pos (int): current index position of text

        Returns :
            i (int): index of mismatched char from last in text
            -1 (int): if there is no mismatch between pattern and text block

        >>> bms = BoyerMooreSearch(text="ABAABA", pattern="AB")
        >>> bms.mismatch_in_text(2)
        3
        """

        for i in range(self.patLen - 1, -1, -1):
            if self.pattern[i] != self.text[current_pos + i]:
                return current_pos + i
        return -1

    def bad_character_heuristic(self) -> list[int]:
    # bad_character_heuristic 函数实现
        """
        Finds the positions of the pattern location.

        >>> bms = BoyerMooreSearch(text="ABAABA", pattern="AB")
        >>> bms.bad_character_heuristic()
        [0, 3]
        """

        positions = []
        for i in range(self.textLen - self.patLen + 1):
            mismatch_index = self.mismatch_in_text(i)
            if mismatch_index == -1:
                positions.append(i)
            else:
                match_index = self.match_in_pattern(self.text[mismatch_index])
                i = (
                    mismatch_index - match_index
                )  # shifting index lgtm [py/multiple-definition]
        return positions


if __name__ == "__main__":
    import doctest

    doctest.testmod()
