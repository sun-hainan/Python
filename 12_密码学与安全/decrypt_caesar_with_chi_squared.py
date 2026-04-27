# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / decrypt_caesar_with_chi_squared

本文件实现 decrypt_caesar_with_chi_squared 相关的算法功能。
"""

#!/usr/bin/env python3
"""
==============================================================
密码学与安全 - Caesar 密码破解（卡方统计）
==============================================================
Caesar 密码：一种简单的替换密码，将每个字母循环移动固定位数。

破解方法：卡方统计（Chi-squared Statistic）
- 统计密文中各字母出现频率
- 与英文字母标准频率比较
- 卡方值最小的位移最可能是正确密钥

原理：
- 英文文本中各字母频率分布稳定（e 最常见，约 11%）
- 对于每个可能的位移，计算卡方值
- 卡方值越小，说明频率分布越接近英文

参考：
- https://en.wikipedia.org/wiki/Caesar_cipher
- http://practicalcryptography.com/cryptanalysis/text-characterisation/chi-squared-statistic/
"""

from __future__ import annotations


def decrypt_caesar_with_chi_squared(
    ciphertext: str,
    cipher_alphabet: list[str] | None = None,
    frequencies_dict: dict[str, float] | None = None,
    case_sensitive: bool = False,
) -> tuple[int, float, str]:
    """
    使用卡方统计破解 Caesar 密码。
    
    Args:
        ciphertext: 密文
        cipher_alphabet: 密码字母表（默认 a-z）
        frequencies_dict: 字母频率字典（默认英文频率）
        case_sensitive: 是否区分大小写
    
    Returns:
        (最可能的位移, 卡方值, 解密文本)
    
    示例:
        >>> decrypt_caesar_with_chi_squared('dof pz aol jhlzhy jpwoly zv wvwbshy?')
        (7, 3129.22..., 'why is the caesar cipher so popular?')
    """
    alphabet_letters = cipher_alphabet or [chr(i) for i in range(97, 123)]

    # 如果未提供频率，使用英文标准频率
    if not frequencies_dict:
        frequencies = {
            "a": 0.08497, "b": 0.01492, "c": 0.02202, "d": 0.04253,
            "e": 0.11162, "f": 0.02228, "g": 0.02015, "h": 0.06094,
            "i": 0.07546, "j": 0.00153, "k": 0.01292, "l": 0.04025,
            "m": 0.02406, "n": 0.06749, "o": 0.07507, "p": 0.01929,
            "q": 0.00095, "r": 0.07587, "s": 0.06327, "t": 0.09356,
            "u": 0.02758, "v": 0.00978, "w": 0.02560, "x": 0.00150,
            "y": 0.01994, "z": 0.00077,
        }
    else:
        frequencies = frequencies_dict

    if not case_sensitive:
        ciphertext = ciphertext.lower()

    # 存储每个位移的卡方值和解密文本
    chi_squared_statistic_values: dict[int, tuple[float, str]] = {}

    # 遍历所有可能的位移（0-25）
    for shift in range(len(alphabet_letters)):
        decrypted_with_shift = ""

        # 使用该位移解密
        for letter in ciphertext:
            try:
                # 计算解密后的字母索引
                new_key = (alphabet_letters.index(letter.lower()) - shift) % len(
                    alphabet_letters
                )
                decrypted_with_shift += (
                    alphabet_letters[new_key].upper()
                    if case_sensitive and letter.isupper()
                    else alphabet_letters[new_key]
                )
            except ValueError:
                # 非字母字符直接保留
                decrypted_with_shift += letter

        chi_squared_statistic = 0.0

        # 计算该解密的卡方值
        for letter in decrypted_with_shift:
            if case_sensitive:
                letter = letter.lower()
                if letter in frequencies:
                    occurrences = decrypted_with_shift.lower().count(letter)
                    expected = frequencies[letter] * occurrences
                    chi_letter_value = ((occurrences - expected) ** 2) / expected
                    chi_squared_statistic += chi_letter_value
            elif letter.lower() in frequencies:
                occurrences = decrypted_with_shift.count(letter)
                expected = frequencies[letter] * occurrences
                chi_letter_value = ((occurrences - expected) ** 2) / expected
                chi_squared_statistic += chi_letter_value

        chi_squared_statistic_values[shift] = (
            chi_squared_statistic,
            decrypted_with_shift,
        )

    # 找出卡方值最小的位移（最可能是正确密钥）
    def chi_squared_statistic_values_sorting_key(key: int) -> tuple[float, str]:
        return chi_squared_statistic_values[key]

    most_likely_cipher: int = min(
        chi_squared_statistic_values,
        key=chi_squared_statistic_values_sorting_key,
    )

    (
        most_likely_cipher_chi_squared_value,
        decoded_most_likely_cipher,
    ) = chi_squared_statistic_values[most_likely_cipher]

    return (
        most_likely_cipher,
        most_likely_cipher_chi_squared_value,
        decoded_most_likely_cipher,
    )


# ==========================================================
# 测试代码
# ==========================================================
if __name__ == "__main__":
    # 测试用例
    ciphertext = "dof pz aol jhlzhy jpwoly zv wvwbshy? pa pz avv lhzf av jyhjr!"
    shift, chi_sq, plaintext = decrypt_caesar_with_chi_squared(ciphertext)
    print(f"位移: {shift}")
    print(f"卡方值: {chi_sq:.2f}")
    print(f"解密: {plaintext}")
