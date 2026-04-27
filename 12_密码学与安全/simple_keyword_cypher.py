# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / simple_keyword_cypher

本文件实现 simple_keyword_cypher 相关的算法功能。
"""

# remove_duplicates 函数实现
def remove_duplicates(key: str) -> str:
    """
    Removes duplicate alphabetic characters in a keyword (letter is ignored after its
    first appearance).

    :param key: Keyword to use
    :return: String with duplicates removed

    >>> remove_duplicates('Hello World!!')
    'Helo Wrd'
    """

    key_no_dups = ""
    for ch in key:
    # 遍历循环
        if ch == " " or (ch not in key_no_dups and ch.isalpha()):
    # 条件判断
            key_no_dups += ch
    return key_no_dups
    # 返回结果



# create_cipher_map 函数实现
def create_cipher_map(key: str) -> dict[str, str]:
    """
    Returns a cipher map given a keyword.

    :param key: keyword to use
    :return: dictionary cipher map
    """
    # Create a list of the letters in the alphabet
    alphabet = [chr(i + 65) for i in range(26)]
    # Remove duplicate characters from key
    key = remove_duplicates(key.upper())
    offset = len(key)
    # First fill cipher with key characters
    cipher_alphabet = {alphabet[i]: char for i, char in enumerate(key)}
    # Then map remaining characters in alphabet to
    # the alphabet from the beginning
    for i in range(len(cipher_alphabet), 26):
    # 遍历循环
        char = alphabet[i - offset]
        # Ensure we are not mapping letters to letters previously mapped
        while char in key:
    # 条件循环
            offset -= 1
            char = alphabet[i - offset]
        cipher_alphabet[alphabet[i]] = char
    return cipher_alphabet
    # 返回结果



# encipher 函数实现
def encipher(message: str, cipher_map: dict[str, str]) -> str:
    """
    Enciphers a message given a cipher map.

    :param message: Message to encipher
    :param cipher_map: Cipher map
    :return: enciphered string

    >>> encipher('Hello World!!', create_cipher_map('Goodbye!!'))
    'CYJJM VMQJB!!'
    """
    return "".join(cipher_map.get(ch, ch) for ch in message.upper())
    # 返回结果



# decipher 函数实现
def decipher(message: str, cipher_map: dict[str, str]) -> str:
    """
    Deciphers a message given a cipher map

    :param message: Message to decipher
    :param cipher_map: Dictionary mapping to use
    :return: Deciphered string

    >>> cipher_map = create_cipher_map('Goodbye!!')
    >>> decipher(encipher('Hello World!!', cipher_map), cipher_map)
    'HELLO WORLD!!'
    """
    # Reverse our cipher mappings
    rev_cipher_map = {v: k for k, v in cipher_map.items()}
    return "".join(rev_cipher_map.get(ch, ch) for ch in message.upper())
    # 返回结果



# main 函数实现
def main() -> None:
    """
    Handles I/O

    :return: void
    """
    message = input("Enter message to encode or decode: ").strip()
    key = input("Enter keyword: ").strip()
    option = input("Encipher or decipher? E/D:").strip()[0].lower()
    try:
        func = {"e": encipher, "d": decipher}[option]
    except KeyError:
        raise KeyError("invalid input option")
    cipher_map = create_cipher_map(key)
    print(func(message, cipher_map))


if __name__ == "__main__":
    # 条件判断
    import doctest

    doctest.testmod()
    main()
