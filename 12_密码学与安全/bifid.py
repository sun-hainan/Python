# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / bifid



本文件实现 bifid 相关的算法功能。

"""



#!/usr/bin/env python3

"""

==============================================================

密码学与安全 - Bifid 密码

==============================================================

Bifid 密码：一种使用 Polybius 方表的古典密码。



加密原理：

1. 将每个字母转换为方表中的 (行, 列) 坐标

2. 按顺序写下所有行坐标，再写下所有列坐标

3. 重新配对为 (行, 列)，查表得到密文



特点：

- 同时使用行和列信息，增加了安全性

- 属于替换密码，易受频率分析攻击



参考：https://www.braingle.com/brainteasers/codes/bifid.php

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





class BifidCipher:

    """

    Bifid 密码加解密类。

    

    使用 5x5 Polybius 方表进行字符坐标编码。

    """



    def __init__(self) -> None:

        self.SQUARE = np.array(SQUARE)



    def letter_to_numbers(self, letter: str) -> np.ndarray:

        """

        将字母转换为方表坐标。

        

        Args:

            letter: 单个字母（a-z）

        

        Returns:

            坐标数组 [行号, 列号]（1-based）

        

        示例:

            >>> np.array_equal(BifidCipher().letter_to_numbers('a'), [1,1])

            True

            >>> np.array_equal(BifidCipher().letter_to_numbers('u'), [4,5])

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

            >>> BifidCipher().numbers_to_letter(4, 5) == "u"

            True

        """

        letter = self.SQUARE[index1 - 1, index2 - 1]

        return letter



    def encode(self, message: str) -> str:

        """

        加密消息。

        

        Args:

            message: 明文（字母和空格）

        

        Returns:

            密文（小写字母）

        

        示例:

            >>> BifidCipher().encode('testmessage') == 'qtltbdxrxlk'

            True

        """

        message = message.lower()  # 转小写

        message = message.replace(" ", "")  # 去除空格

        message = message.replace("j", "i")  # j 映射为 i



        # 第一步：获取所有字母的坐标

        first_step = np.empty((2, len(message)))

        for letter_index in range(len(message)):

            numbers = self.letter_to_numbers(message[letter_index])

            first_step[0, letter_index] = numbers[0]

            first_step[1, letter_index] = numbers[1]



        # 第二步：展平坐标序列

        second_step = first_step.reshape(2 * len(message))

        

        # 第三步：重新配对并查表

        encoded_message = ""

        for numbers_index in range(len(message)):

            index1 = int(second_step[numbers_index * 2])

            index2 = int(second_step[(numbers_index * 2) + 1])

            letter = self.numbers_to_letter(index1, index2)

            encoded_message = encoded_message + letter



        return encoded_message



    def decode(self, message: str) -> str:

        """

        解密消息。

        

        Args:

            message: 密文（小写字母）

        

        Returns:

            明文

        

        示例:

            >>> BifidCipher().decode('qtltbdxrxlk') == 'testmessage'

            True

        """

        message = message.lower()

        message.replace(" ", "")

        

        # 第一步：将消息转换为坐标序列

        first_step = np.empty(2 * len(message))

        for letter_index in range(len(message)):

            numbers = self.letter_to_numbers(message[letter_index])

            first_step[letter_index * 2] = numbers[0]

            first_step[letter_index * 2 + 1] = numbers[1]



        # 第二步：重组为 2 行

        second_step = first_step.reshape((2, len(message)))

        

        # 第三步：查表还原

        decoded_message = ""

        for numbers_index in range(len(message)):

            index1 = int(second_step[0, numbers_index])

            index2 = int(second_step[1, numbers_index])

            letter = self.numbers_to_letter(index1, index2)

            decoded_message = decoded_message + letter



        return decoded_message





# ==========================================================

# 测试代码

# ==========================================================

if __name__ == "__main__":

    cipher = BifidCipher()

    plaintext = "Hello World"

    encrypted = cipher.encode(plaintext)

    decrypted = cipher.decode(encrypted)

    print(f"明文: {plaintext}")

    print(f"加密: {encrypted}")

    print(f"解密: {decrypted}")

