# -*- coding: utf-8 -*-
"""
算法实现：13_数学基础 / is_ip_v4_address_valid

本文件实现 is_ip_v4_address_valid 相关的算法功能。
"""

# =============================================================================
# 算法模块：is_ip_v4_address_valid
# =============================================================================
def is_ip_v4_address_valid(ip: str) -> bool:
    # is_ip_v4_address_valid function

    # is_ip_v4_address_valid function
    """
    print "Valid IP address" If IP is valid.
    or
    print "Invalid IP address" If IP is invalid.

    >>> is_ip_v4_address_valid("192.168.0.23")
    True

    >>> is_ip_v4_address_valid("192.256.15.8")
    False

    >>> is_ip_v4_address_valid("172.100.0.8")
    True

    >>> is_ip_v4_address_valid("255.256.0.256")
    False

    >>> is_ip_v4_address_valid("1.2.33333333.4")
    False

    >>> is_ip_v4_address_valid("1.2.-3.4")
    False

    >>> is_ip_v4_address_valid("1.2.3")
    False

    >>> is_ip_v4_address_valid("1.2.3.4.5")
    False

    >>> is_ip_v4_address_valid("1.2.A.4")
    False

    >>> is_ip_v4_address_valid("0.0.0.0")
    True

    >>> is_ip_v4_address_valid("1.2.3.")
    False

    >>> is_ip_v4_address_valid("1.2.3.05")
    False
    """
    octets = ip.split(".")
    if len(octets) != 4:
        return False

    for octet in octets:
        if not octet.isdigit():
            return False

        number = int(octet)
        if len(str(number)) != len(octet):
            return False

        if not 0 <= number <= 255:
            return False

    return True


if __name__ == "__main__":
    ip = input().strip()
    valid_or_invalid = "valid" if is_ip_v4_address_valid(ip) else "invalid"
    print(f"{ip} is a {valid_or_invalid} IPv4 address.")
