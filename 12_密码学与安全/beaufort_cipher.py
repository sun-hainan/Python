# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / beaufort_cipher



本文件实现 beaufort_cipher 相关的算法功能。

"""



from string import ascii_uppercase



dict1 = {char: i for i, char in enumerate(ascii_uppercase)}

dict2 = dict(enumerate(ascii_uppercase))





# This function generates the key in

# a cyclic manner until it's length isn't

# equal to the length of original text



# generate_key 函数实现

def generate_key(message: str, key: str) -> str:

    """

    >>> generate_key("THE GERMAN ATTACK","SECRET")

    'SECRETSECRETSECRE'

    """

    x = len(message)

    i = 0

    while True:

    # 条件循环

        if x == i:

    # 条件判断

            i = 0

        if len(key) == len(message):

    # 条件判断

            break

        key += key[i]

        i += 1

    return key

    # 返回结果





# This function returns the encrypted text

# generated with the help of the key



# cipher_text 函数实现

def cipher_text(message: str, key_new: str) -> str:

    """

    >>> cipher_text("THE GERMAN ATTACK","SECRETSECRETSECRE")

    'BDC PAYUWL JPAIYI'

    """

    cipher_text = ""

    i = 0

    for letter in message:

    # 遍历循环

        if letter == " ":

    # 条件判断

            cipher_text += " "

        else:

            x = (dict1[letter] - dict1[key_new[i]]) % 26

            i += 1

            cipher_text += dict2[x]

    return cipher_text

    # 返回结果





# This function decrypts the encrypted text

# and returns the original text



# original_text 函数实现

def original_text(cipher_text: str, key_new: str) -> str:

    """

    >>> original_text("BDC PAYUWL JPAIYI","SECRETSECRETSECRE")

    'THE GERMAN ATTACK'

    """

    or_txt = ""

    i = 0

    for letter in cipher_text:

    # 遍历循环

        if letter == " ":

    # 条件判断

            or_txt += " "

        else:

            x = (dict1[letter] + dict1[key_new[i]] + 26) % 26

            i += 1

            or_txt += dict2[x]

    return or_txt

    # 返回结果







# main 函数实现

def main() -> None:

    message = "THE GERMAN ATTACK"

    key = "SECRET"

    key_new = generate_key(message, key)

    s = cipher_text(message, key_new)

    print(f"Encrypted Text = {s}")

    print(f"Original Text = {original_text(s, key_new)}")





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

    main()

