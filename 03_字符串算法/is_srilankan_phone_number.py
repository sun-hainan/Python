# -*- coding: utf-8 -*-
"""
算法实现：03_字符串算法 / is_srilankan_phone_number

本文件实现 is_srilankan_phone_number 相关的算法功能。
"""

import re


def is_sri_lankan_phone_number(phone: str) -> bool:
    # is_sri_lankan_phone_number function

    # is_sri_lankan_phone_number function
    # is_sri_lankan_phone_number 函数实现
    """
    Determine whether the string is a valid sri lankan mobile phone number or not
    References: https://aye.sh/blog/sri-lankan-phone-number-regex

    >>> is_sri_lankan_phone_number("+94773283048")
    True
    >>> is_sri_lankan_phone_number("+9477-3283048")
    True
    >>> is_sri_lankan_phone_number("0718382399")
    True
    >>> is_sri_lankan_phone_number("0094702343221")
    True
    >>> is_sri_lankan_phone_number("075 3201568")
    True
    >>> is_sri_lankan_phone_number("07779209245")
    False
    >>> is_sri_lankan_phone_number("0957651234")
    False
    """

    pattern = re.compile(r"^(?:0|94|\+94|0{2}94)7(0|1|2|4|5|6|7|8)(-| |)\d{7}$")

    return bool(re.search(pattern, phone))


if __name__ == "__main__":
    phone = "0094702343221"

    print(is_sri_lankan_phone_number(phone))
