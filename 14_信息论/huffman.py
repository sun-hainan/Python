# -*- coding: utf-8 -*-
"""
算法实现：14_信息论 / huffman

本文件实现 huffman 相关的算法功能。
"""

huffman.py
"""

import sys
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class Letter:
    letter: str
    freq: int
    bitstring: dict = None

    def __post_init__(self):
        self.bitstring = {}


@dataclass
class TreeNode:
    freq: int
    left: Letter | TreeNode
    right: Letter | TreeNode


def parse_file(file_path: str) -> list[Letter]:
    """解析文件并统计字符频率"""
    chars: dict[str, int] = {}
    with open(file_path) as f:
        while True:
            c = f.read(1)
            if not c:
                break
            chars[c] = chars[c] + 1 if c in chars else 1
    return sorted((Letter(c, f) for c, f in chars.items()), key=lambda x: x.freq)


def build_tree(letters: list[Letter]) -> Letter | TreeNode:
    """
    Run through the list of Letters and build the min heap
    for the Huffman Tree.
    """
    response: list[Letter | TreeNode] = list(letters)
    while len(response) > 1:
        left = response.pop(0)
        right = response.pop(0)
        total_freq = left.freq + right.freq
        node = TreeNode(total_freq, left, right)
        response.append(node)
        response.sort(key=lambda x: x.freq)
    return response[0]


def traverse_tree(root: Letter | TreeNode, bitstring: str) -> list[Letter]:
    """
    Recursively traverse the Huffman Tree to set each
    Letter's bitstring dictionary, and return the list of Letters
    """
    if isinstance(root, Letter):
        root.bitstring[root.letter] = bitstring
        return [root]
    treenode: TreeNode = root
    letters = []
    letters += traverse_tree(treenode.left, bitstring + "0")
    letters += traverse_tree(treenode.right, bitstring + "1")
    return letters


def huffman(file_path: str) -> None:
    """
    Parse the file, build the tree, then run through the file
    again, using the letters dictionary to find and print out the
    bitstring for each letter.
    """
    letters_list = parse_file(file_path)
    root = build_tree(letters_list)
    letters = {
        k: v for letter in traverse_tree(root, "") for k, v in letter.bitstring.items()
    }
    print(f"Huffman Coding  of {file_path}: ")
    with open(file_path) as f:
        while True:
            c = f.read(1)
            if not c:
                break
            print(letters[c], end=" ")
    print()


if __name__ == "__main__":
    # pass the file path to the huffman function
    huffman(sys.argv[1])
