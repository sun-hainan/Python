# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / vigenere_cipher

本文件实现 vigenere_cipher 相关的算法功能。
"""

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"



# main 函数实现
def main() -> None:
    message = input("Enter message: ")
    key = input("Enter key [alphanumeric]: ")
    mode = input("Encrypt/Decrypt [e/d]: ")

    if mode.lower().startswith("e"):
    # 条件判断
        mode = "encrypt"
        translated = encrypt_message(key, message)
    elif mode.lower().startswith("d"):
        mode = "decrypt"
        translated = decrypt_message(key, message)

    print(f"\n{mode.title()}ed message:")
    print(translated)



# encrypt_message 函数实现
def encrypt_message(key: str, message: str) -> str:
    """
    >>> encrypt_message('HDarji', 'This is Harshil Darji from Dharmaj.')
    'Akij ra Odrjqqs Gaisq muod Mphumrs.'
    """
    return translate_message(key, message, "encrypt")
    # 返回结果



# decrypt_message 函数实现
def decrypt_message(key: str, message: str) -> str:
    """
    >>> decrypt_message('HDarji', 'Akij ra Odrjqqs Gaisq muod Mphumrs.')
    'This is Harshil Darji from Dharmaj.'
    """
    return translate_message(key, message, "decrypt")
    # 返回结果



# translate_message 函数实现
def translate_message(key: str, message: str, mode: str) -> str:
    translated = []
    key_index = 0
    key = key.upper()

    for symbol in message:
    # 遍历循环
        num = LETTERS.find(symbol.upper())
        if num != -1:
    # 条件判断
            if mode == "encrypt":
    # 条件判断
                num += LETTERS.find(key[key_index])
            elif mode == "decrypt":
                num -= LETTERS.find(key[key_index])

            num %= len(LETTERS)

            if symbol.isupper():
    # 条件判断
                translated.append(LETTERS[num])
            elif symbol.islower():
                translated.append(LETTERS[num].lower())

            key_index += 1
            if key_index == len(key):
    # 条件判断
                key_index = 0
        else:
            translated.append(symbol)
    return "".join(translated)
    # 返回结果


if __name__ == "__main__":
    # 条件判断
    main()
