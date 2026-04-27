# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / brute_force_caesar_cipher



本文件实现 brute_force_caesar_cipher 相关的算法功能。

"""



import string







# decrypt 函数实现

def decrypt(message: str) -> None:

    """

    >>> decrypt('TMDETUX PMDVU')

    Decryption using Key #0: TMDETUX PMDVU

    Decryption using Key #1: SLCDSTW OLCUT

    Decryption using Key #2: RKBCRSV NKBTS

    Decryption using Key #3: QJABQRU MJASR

    Decryption using Key #4: PIZAPQT LIZRQ

    Decryption using Key #5: OHYZOPS KHYQP

    Decryption using Key #6: NGXYNOR JGXPO

    Decryption using Key #7: MFWXMNQ IFWON

    Decryption using Key #8: LEVWLMP HEVNM

    Decryption using Key #9: KDUVKLO GDUML

    Decryption using Key #10: JCTUJKN FCTLK

    Decryption using Key #11: IBSTIJM EBSKJ

    Decryption using Key #12: HARSHIL DARJI

    Decryption using Key #13: GZQRGHK CZQIH

    Decryption using Key #14: FYPQFGJ BYPHG

    Decryption using Key #15: EXOPEFI AXOGF

    Decryption using Key #16: DWNODEH ZWNFE

    Decryption using Key #17: CVMNCDG YVMED

    Decryption using Key #18: BULMBCF XULDC

    Decryption using Key #19: ATKLABE WTKCB

    Decryption using Key #20: ZSJKZAD VSJBA

    Decryption using Key #21: YRIJYZC URIAZ

    Decryption using Key #22: XQHIXYB TQHZY

    Decryption using Key #23: WPGHWXA SPGYX

    Decryption using Key #24: VOFGVWZ ROFXW

    Decryption using Key #25: UNEFUVY QNEWV

    """

    for key in range(len(string.ascii_uppercase)):

    # 遍历循环

        translated = ""

        for symbol in message:

    # 遍历循环

            if symbol in string.ascii_uppercase:

    # 条件判断

                num = string.ascii_uppercase.find(symbol)

                num = num - key

                if num < 0:

    # 条件判断

                    num = num + len(string.ascii_uppercase)

                translated = translated + string.ascii_uppercase[num]

            else:

                translated = translated + symbol

        print(f"Decryption using Key #{key}: {translated}")







# main 函数实现

def main() -> None:

    message = input("Encrypted message: ")

    message = message.upper()

    decrypt(message)





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    main()

