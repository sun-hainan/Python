# -*- coding: utf-8 -*-
"""
算法实现：12_密码学与安全 / rsa_cipher

本文件实现 rsa_cipher 相关的算法功能。
"""

import os
import sys

from . import rsa_key_generator as rkg

DEFAULT_BLOCK_SIZE = 128
BYTE_SIZE = 256



# get_blocks_from_text 函数实现
def get_blocks_from_text(
    message: str, block_size: int = DEFAULT_BLOCK_SIZE
) -> list[int]:
    message_bytes = message.encode("ascii")

    block_ints = []
    for block_start in range(0, len(message_bytes), block_size):
    # 遍历循环
        block_int = 0
        for i in range(block_start, min(block_start + block_size, len(message_bytes))):
    # 遍历循环
            block_int += message_bytes[i] * (BYTE_SIZE ** (i % block_size))
        block_ints.append(block_int)
    return block_ints
    # 返回结果



# get_text_from_blocks 函数实现
def get_text_from_blocks(
    block_ints: list[int], message_length: int, block_size: int = DEFAULT_BLOCK_SIZE
) -> str:
    message: list[str] = []
    for block_int in block_ints:
    # 遍历循环
        block_message: list[str] = []
        for i in range(block_size - 1, -1, -1):
    # 遍历循环
            if len(message) + i < message_length:
    # 条件判断
                ascii_number = block_int // (BYTE_SIZE**i)
                block_int = block_int % (BYTE_SIZE**i)
                block_message.insert(0, chr(ascii_number))
        message.extend(block_message)
    return "".join(message)
    # 返回结果



# encrypt_message 函数实现
def encrypt_message(
    message: str, key: tuple[int, int], block_size: int = DEFAULT_BLOCK_SIZE
) -> list[int]:
    encrypted_blocks = []
    n, e = key

    for block in get_blocks_from_text(message, block_size):
    # 遍历循环
        encrypted_blocks.append(pow(block, e, n))
    return encrypted_blocks
    # 返回结果



# decrypt_message 函数实现
def decrypt_message(
    encrypted_blocks: list[int],
    message_length: int,
    key: tuple[int, int],
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> str:
    decrypted_blocks = []
    n, d = key
    for block in encrypted_blocks:
    # 遍历循环
        decrypted_blocks.append(pow(block, d, n))
    return get_text_from_blocks(decrypted_blocks, message_length, block_size)
    # 返回结果



# read_key_file 函数实现
def read_key_file(key_filename: str) -> tuple[int, int, int]:
    with open(key_filename) as fo:
        content = fo.read()
    key_size, n, eor_d = content.split(",")
    return (int(key_size), int(n), int(eor_d))
    # 返回结果



# encrypt_and_write_to_file 函数实现
def encrypt_and_write_to_file(
    message_filename: str,
    key_filename: str,
    message: str,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> str:
    key_size, n, e = read_key_file(key_filename)
    if key_size < block_size * 8:
    # 条件判断
        sys.exit(
            f"ERROR: Block size is {block_size * 8} bits and key size is {key_size} "
            "bits. The RSA cipher requires the block size to be equal to or greater "
            "than the key size. Either decrease the block size or use different keys."
        )

    encrypted_blocks = [str(i) for i in encrypt_message(message, (n, e), block_size)]

    encrypted_content = ",".join(encrypted_blocks)
    encrypted_content = f"{len(message)}_{block_size}_{encrypted_content}"
    with open(message_filename, "w") as fo:
        fo.write(encrypted_content)
    return encrypted_content
    # 返回结果



# read_from_file_and_decrypt 函数实现
def read_from_file_and_decrypt(message_filename: str, key_filename: str) -> str:
    key_size, n, d = read_key_file(key_filename)
    with open(message_filename) as fo:
        content = fo.read()
    message_length_str, block_size_str, encrypted_message = content.split("_")
    message_length = int(message_length_str)
    block_size = int(block_size_str)

    if key_size < block_size * 8:
    # 条件判断
        sys.exit(
            f"ERROR: Block size is {block_size * 8} bits and key size is {key_size} "
            "bits. The RSA cipher requires the block size to be equal to or greater "
            "than the key size. Were the correct key file and encrypted file specified?"
        )

    encrypted_blocks = []
    for block in encrypted_message.split(","):
    # 遍历循环
        encrypted_blocks.append(int(block))

    return decrypt_message(encrypted_blocks, message_length, (n, d), block_size)
    # 返回结果



# main 函数实现
def main() -> None:
    filename = "encrypted_file.txt"
    response = input(r"Encrypt\Decrypt [e\d]: ")

    if response.lower().startswith("e"):
    # 条件判断
        mode = "encrypt"
    elif response.lower().startswith("d"):
        mode = "decrypt"

    if mode == "encrypt":
    # 条件判断
        if not os.path.exists("rsa_pubkey.txt"):
    # 条件判断
            rkg.make_key_files("rsa", 1024)

        message = input("\nEnter message: ")
        pubkey_filename = "rsa_pubkey.txt"
        print(f"Encrypting and writing to {filename}...")
        encrypted_text = encrypt_and_write_to_file(filename, pubkey_filename, message)

        print("\nEncrypted text:")
        print(encrypted_text)

    elif mode == "decrypt":
        privkey_filename = "rsa_privkey.txt"
        print(f"Reading from {filename} and decrypting...")
        decrypted_text = read_from_file_and_decrypt(filename, privkey_filename)
        print("writing decryption to rsa_decryption.txt...")
        with open("rsa_decryption.txt", "w") as dec:
            dec.write(decrypted_text)

        print("\nDecryption:")
        print(decrypted_text)


if __name__ == "__main__":
    # 条件判断
    main()
