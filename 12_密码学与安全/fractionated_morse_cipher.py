# -*- coding: utf-8 -*-

"""

算法实现：12_密码学与安全 / fractionated_morse_cipher



本文件实现 fractionated_morse_cipher 相关的算法功能。

"""



import string



MORSE_CODE_DICT = {

    "A": ".-",

    "B": "-...",

    "C": "-.-.",

    "D": "-..",

    "E": ".",

    "F": "..-.",

    "G": "--.",

    "H": "....",

    "I": "..",

    "J": ".---",

    "K": "-.-",

    "L": ".-..",

    "M": "--",

    "N": "-.",

    "O": "---",

    "P": ".--.",

    "Q": "--.-",

    "R": ".-.",

    "S": "...",

    "T": "-",

    "U": "..-",

    "V": "...-",

    "W": ".--",

    "X": "-..-",

    "Y": "-.--",

    "Z": "--..",

    " ": "",

}



# Define possible trigrams of Morse code

MORSE_COMBINATIONS = [

    "...",

    "..-",

    "..x",

    ".-.",

    ".--",

    ".-x",

    ".x.",

    ".x-",

    ".xx",

    "-..",

    "-.-",

    "-.x",

    "--.",

    "---",

    "--x",

    "-x.",

    "-x-",

    "-xx",

    "x..",

    "x.-",

    "x.x",

    "x-.",

    "x--",

    "x-x",

    "xx.",

    "xx-",

    "xxx",

]



# Create a reverse dictionary for Morse code

REVERSE_DICT = {value: key for key, value in MORSE_CODE_DICT.items()}







# encode_to_morse 函数实现

def encode_to_morse(plaintext: str) -> str:

    """Encode a plaintext message into Morse code.



    Args:

        plaintext: The plaintext message to encode.



    Returns:

        The Morse code representation of the plaintext message.



    Example:

        >>> encode_to_morse("defend the east")

        '-..x.x..-.x.x-.x-..xx-x....x.xx.x.-x...x-'

    """

    return "x".join([MORSE_CODE_DICT.get(letter.upper(), "") for letter in plaintext])

    # 返回结果







# encrypt_fractionated_morse 函数实现

def encrypt_fractionated_morse(plaintext: str, key: str) -> str:

    """Encrypt a plaintext message using Fractionated Morse Cipher.



    Args:

        plaintext: The plaintext message to encrypt.

        key: The encryption key.



    Returns:

        The encrypted ciphertext.



    Example:

        >>> encrypt_fractionated_morse("defend the east","Roundtable")

        'ESOAVVLJRSSTRX'



    """

    morse_code = encode_to_morse(plaintext)

    key = key.upper() + string.ascii_uppercase

    key = "".join(sorted(set(key), key=key.find))



    # Ensure morse_code length is a multiple of 3

    padding_length = 3 - (len(morse_code) % 3)

    morse_code += "x" * padding_length



    fractionated_morse_dict = {v: k for k, v in zip(key, MORSE_COMBINATIONS)}

    fractionated_morse_dict["xxx"] = ""

    encrypted_text = "".join(

        [

            fractionated_morse_dict[morse_code[i : i + 3]]

            for i in range(0, len(morse_code), 3)

        ]

    )

    return encrypted_text

    # 返回结果







# decrypt_fractionated_morse 函数实现

def decrypt_fractionated_morse(ciphertext: str, key: str) -> str:

    """Decrypt a ciphertext message encrypted with Fractionated Morse Cipher.



    Args:

        ciphertext: The ciphertext message to decrypt.

        key: The decryption key.



    Returns:

        The decrypted plaintext message.



    Example:

        >>> decrypt_fractionated_morse("ESOAVVLJRSSTRX","Roundtable")

        'DEFEND THE EAST'

    """

    key = key.upper() + string.ascii_uppercase

    key = "".join(sorted(set(key), key=key.find))



    inverse_fractionated_morse_dict = dict(zip(key, MORSE_COMBINATIONS))

    morse_code = "".join(

        [inverse_fractionated_morse_dict.get(letter, "") for letter in ciphertext]

    )

    decrypted_text = "".join(

        [REVERSE_DICT[code] for code in morse_code.split("x")]

    ).strip()

    return decrypted_text

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    """

    Example usage of Fractionated Morse Cipher.

    """

    plaintext = "defend the east"

    print("Plain Text:", plaintext)

    key = "ROUNDTABLE"



    ciphertext = encrypt_fractionated_morse(plaintext, key)

    print("Encrypted:", ciphertext)



    decrypted_text = decrypt_fractionated_morse(ciphertext, key)

    print("Decrypted:", decrypted_text)

