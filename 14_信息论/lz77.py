# -*- coding: utf-8 -*-

"""

算法实现：14_信息论 / lz77



本文件实现 lz77 相关的算法功能。

"""



from dataclasses import dataclass



__version__ = "0.1"

__author__ = "Lucia Harcekova"





@dataclass

class Token:

    # Token class



    # Token class

    """

    Dataclass representing triplet called token consisting of length, offset

    and indicator. This triplet is used during LZ77 compression.

    """



    offset: int

    length: int

    indicator: str



    def __repr__(self) -> str:

    # __repr__ function



    # __repr__ function

        """

        >>> token = Token(1, 2, "c")

        >>> repr(token)

        '(1, 2, c)'

        >>> str(token)

        '(1, 2, c)'

        """

        return f"({self.offset}, {self.length}, {self.indicator})"





class LZ77Compressor:

    # LZ77Compressor class



    # LZ77Compressor class

    """

    Class containing compress and decompress methods using LZ77 compression algorithm.

    """



    def __init__(self, window_size: int = 13, lookahead_buffer_size: int = 6) -> None:

    # __init__ function



    # __init__ function

        self.window_size = window_size

        self.lookahead_buffer_size = lookahead_buffer_size

        self.search_buffer_size = self.window_size - self.lookahead_buffer_size



    def compress(self, text: str) -> list[Token]:

    # compress function



    # compress function

        """

        Compress the given string text using LZ77 compression algorithm.



        Args:

            text: string to be compressed



        Returns:

            output: the compressed text as a list of Tokens



        >>> lz77_compressor = LZ77Compressor()

        >>> str(lz77_compressor.compress("ababcbababaa"))

        '[(0, 0, a), (0, 0, b), (2, 2, c), (4, 3, a), (2, 2, a)]'

        >>> str(lz77_compressor.compress("aacaacabcabaaac"))

        '[(0, 0, a), (1, 1, c), (3, 4, b), (3, 3, a), (1, 2, c)]'

        """



        output = []

        search_buffer = ""



        # while there are still characters in text to compress

        while text:

            # find the next encoding phrase

            # - triplet with offset, length, indicator (the next encoding character)

            token = self._find_encoding_token(text, search_buffer)



            # update the search buffer:

            # - add new characters from text into it

            # - check if size exceed the max search buffer size, if so, drop the

            #   oldest elements

            search_buffer += text[: token.length + 1]

            if len(search_buffer) > self.search_buffer_size:

                search_buffer = search_buffer[-self.search_buffer_size :]



            # update the text

            text = text[token.length + 1 :]



            # append the token to output

            output.append(token)



        return output



    def decompress(self, tokens: list[Token]) -> str:

    # decompress function



    # decompress function

        """

        Convert the list of tokens into an output string.



        Args:

            tokens: list containing triplets (offset, length, char)



        Returns:

            output: decompressed text



        Tests:

            >>> lz77_compressor = LZ77Compressor()

            >>> lz77_compressor.decompress([Token(0, 0, 'c'), Token(0, 0, 'a'),

            ... Token(0, 0, 'b'), Token(0, 0, 'r'), Token(3, 1, 'c'),

            ... Token(2, 1, 'd'), Token(7, 4, 'r'), Token(3, 5, 'd')])

            'cabracadabrarrarrad'

            >>> lz77_compressor.decompress([Token(0, 0, 'a'), Token(0, 0, 'b'),

            ... Token(2, 2, 'c'), Token(4, 3, 'a'), Token(2, 2, 'a')])

            'ababcbababaa'

            >>> lz77_compressor.decompress([Token(0, 0, 'a'), Token(1, 1, 'c'),

            ... Token(3, 4, 'b'), Token(3, 3, 'a'), Token(1, 2, 'c')])

            'aacaacabcabaaac'

        """



        output = ""



        for token in tokens:

            for _ in range(token.length):

                output += output[-token.offset]

            output += token.indicator



        return output



    def _find_encoding_token(self, text: str, search_buffer: str) -> Token:

    # _find_encoding_token function



    # _find_encoding_token function

        """Finds the encoding token for the first character in the text.



        Tests:

            >>> lz77_compressor = LZ77Compressor()

            >>> lz77_compressor._find_encoding_token("abrarrarrad", "abracad").offset

            7

            >>> lz77_compressor._find_encoding_token("adabrarrarrad", "cabrac").length

            1

            >>> lz77_compressor._find_encoding_token("abc", "xyz").offset

            0

            >>> lz77_compressor._find_encoding_token("", "xyz").offset

            Traceback (most recent call last):

                ...

            ValueError: We need some text to work with.

            >>> lz77_compressor._find_encoding_token("abc", "").offset

            0

        """



        if not text:

            raise ValueError("We need some text to work with.")



        # Initialise result parameters to default values

        length, offset = 0, 0



        if not search_buffer:

            return Token(offset, length, text[length])



        for i, character in enumerate(search_buffer):

            found_offset = len(search_buffer) - i

            if character == text[0]:

                found_length = self._match_length_from_index(text, search_buffer, 0, i)

                # if the found length is bigger than the current or if it's equal,

                # which means it's offset is smaller: update offset and length

                if found_length >= length:

                    offset, length = found_offset, found_length



        return Token(offset, length, text[length])



    def _match_length_from_index(

    # _match_length_from_index function



    # _match_length_from_index function

        self, text: str, window: str, text_index: int, window_index: int

    ) -> int:

        """Calculate the longest possible match of text and window characters from

        text_index in text and window_index in window.



        Args:

            text: _description_

            window: sliding window

            text_index: index of character in text

            window_index: index of character in sliding window



        Returns:

            The maximum match between text and window, from given indexes.



        Tests:

            >>> lz77_compressor = LZ77Compressor(13, 6)

            >>> lz77_compressor._match_length_from_index("rarrad", "adabrar", 0, 4)

            5

            >>> lz77_compressor._match_length_from_index("adabrarrarrad",

            ...     "cabrac", 0, 1)

            1

        """

        if not text or text[text_index] != window[window_index]:

            return 0

        return 1 + self._match_length_from_index(

            text, window + text[text_index], text_index + 1, window_index + 1

        )





if __name__ == "__main__":

    from doctest import testmod



    testmod()

    # Initialize compressor class

    lz77_compressor = LZ77Compressor(window_size=13, lookahead_buffer_size=6)



    # Example

    TEXT = "cabracadabrarrarrad"

    compressed_text = lz77_compressor.compress(TEXT)

    print(lz77_compressor.compress("ababcbababaa"))

    decompressed_text = lz77_compressor.decompress(compressed_text)

    assert decompressed_text == TEXT, "The LZ77 algorithm returned the invalid result."

