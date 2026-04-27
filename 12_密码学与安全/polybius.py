# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / polybius



本文件实现 polybius 相关的算法功能。

"""



#!/usr/bin/env python3

"""

==============================================================

密码学与安全 - Polybius 密码

==============================================================

Polybius 方表：一种将字母转换为数字的古典密码。



加密原理：

- 使用 5x5 方表（字母 i 和 j 合并）

- 每个字母对应 (行号, 列号)，形成两位数字



特点：

- 简单易实现

- 可作为其他密码的基础（如 Bifid）

- 数字序列便于传递



参考：https://www.braingle.com/brainteasers/codes/polybius.php

"""



import numpy as np



# Polybius 方表（5x5，j 和 i 合并）

SQUARE = [

    ["a", "b", "c", "d", "e"],

    ["f", "g", "h", "i", "k"],

    ["l", "m", "n", "o", "p"],

    ["q", "r", "s", "t", "u"],

    ["v", "w", "x", "y", "z"],

]





class PolybiusCipher:

    """

    Polybius 密码加解密类。

    

    使用 5x5 方表进行字符坐标编码。

    """



    def __init__(self) -> None:

        self.SQUARE = np.array(SQUARE)



    def letter_to_numbers(self, letter: str) -> np.ndarray:

        """

        将字母转换为方表坐标。

        

        Args:

            letter: 单个字母

        

        Returns:

            坐标数组 [行号, 列号]（1-based）

        

        示例:

            >>> np.array_equal(PolybiusCipher().letter_to_numbers('a'), [1,1])

            True

        """

        index1, index2 = np.where(letter == self.SQUARE)

        indexes = np.concatenate([index1 + 1, index2 + 1])

        return indexes



    def numbers_to_letter(self, index1: int, index2: int) -> str:

        """

        将方表坐标转换为字母。

        

        Args:

            index1: 行号（1-based）

            index2: 列号（1-based）

        

        Returns:

            对应字母

        

        示例:

            >>> PolybiusCipher().numbers_to_letter(4, 5) == "u"

            True

        """

        return self.SQUARE[index1 - 1, index2 - 1]



    def encode(self, message: str) -> str:

        """

        加密消息。

        

        Args:

            message: 明文

        

        Returns:

            密文（数字序列，空格保留）

        

        示例:

            >>> PolybiusCipher().encode("test message")

            '44154344 32154343112215'

        """

        message = message.lower()

        message = message.replace("j", "i")



        encoded_message = ""

        for letter_index in range(len(message)):

            if message[letter_index] != " ":

                numbers = self.letter_to_numbers(message[letter_index])

                encoded_message = encoded_message + str(numbers[0]) + str(numbers[1])

            elif message[letter_index] == " ":

                encoded_message = encoded_message + " "



        return encoded_message



    def decode(self, message: str) -> str:

        """

        解密消息。

        

        Args:

            message: 密文（数字序列）

        

        Returns:

            明文

        

        示例:

            >>> PolybiusCipher().decode("44154344 32154343112215")

            'test message'

        """

        message = message.replace(" ", "  ")

        decoded_message = ""

        for numbers_index in range(int(len(message) / 2)):

            if message[numbers_index * 2] != " ":

                index1 = message[numbers_index * 2]

                index2 = message[numbers_index * 2 + 1]



                letter = self.numbers_to_letter(int(index1), int(index2))

                decoded_message = decoded_message + letter

            elif message[numbers_index * 2] == " ":

                decoded_message = decoded_message + " "



        return decoded_message





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    cipher = PolybiusCipher()

    plaintext = "Hello World"

    encrypted = cipher.encode(plaintext)

    decrypted = cipher.decode(encrypted)

    print(f"明文: {plaintext}")

    print(f"加密: {encrypted}")

    print(f"解密: {decrypted}")

