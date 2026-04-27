# -*- coding: utf-8 -*-
"""
算法实现：trie / trie

本文件实现 trie 相关的算法功能。
"""

# =============================================================================
# 算法模块：print_words
# =============================================================================
class TrieNode:
    # TrieNode class

    # TrieNode class
    def __init__(self) -> None:
    # __init__ function

    # __init__ function
        self.nodes: dict[str, TrieNode] = {}  # Mapping from char to TrieNode
        self.is_leaf = False

    def insert_many(self, words: list[str]) -> None:
    # insert_many function

    # insert_many function
        """
        Inserts a list of words into the Trie
        :param words: list of string words
        :return: None
        """
        for word in words:
            self.insert(word)

    def insert(self, word: str) -> None:
    # insert function

    # insert function
        """
        Inserts a word into the Trie
        :param word: word to be inserted
        :return: None
        """
        curr = self
        for char in word:
            if char not in curr.nodes:
                curr.nodes[char] = TrieNode()
            curr = curr.nodes[char]
        curr.is_leaf = True

    def find(self, word: str) -> bool:
    # find function

    # find function
        """
        Tries to find word in a Trie
        :param word: word to look for
        :return: Returns True if word is found, False otherwise
        """
        curr = self
        for char in word:
            if char not in curr.nodes:
                return False
            curr = curr.nodes[char]
        return curr.is_leaf

    def delete(self, word: str) -> None:
    # delete function

    # delete function
        """
        Deletes a word in a Trie
        :param word: word to delete
        :return: None
        """

        def _delete(curr: TrieNode, word: str, index: int) -> bool:
    # _delete function

    # _delete function
            if index == len(word):
                # If word does not exist
                if not curr.is_leaf:
                    return False
                curr.is_leaf = False
                return len(curr.nodes) == 0
            char = word[index]
            char_node = curr.nodes.get(char)
            # If char not in current trie node
            if not char_node:
                return False
            # Flag to check if node can be deleted
            delete_curr = _delete(char_node, word, index + 1)
            if delete_curr:
                del curr.nodes[char]
                return len(curr.nodes) == 0
            return delete_curr

        _delete(self, word, 0)


def print_words(node: TrieNode, word: str) -> None:
    # print_words function

    # print_words function
    """
    Prints all the words in a Trie
    :param node: root node of Trie
    :param word: Word variable should be empty at start
    :return: None
    """
    if node.is_leaf:
        print(word, end=" ")

    for key, value in node.nodes.items():
        print_words(value, word + key)


def test_trie() -> bool:
    # test_trie function

    # test_trie function
    words = "banana bananas bandana band apple all beast".split()
    root = TrieNode()
    root.insert_many(words)
    # print_words(root, "")
    assert all(root.find(word) for word in words)
    assert root.find("banana")
    assert not root.find("bandanas")
    assert not root.find("apps")
    assert root.find("apple")
    assert root.find("all")
    root.delete("all")
    assert not root.find("all")
    root.delete("banana")
    assert not root.find("banana")
    assert root.find("bananas")
    return True


def print_results(msg: str, passes: bool) -> None:
    # print_results function

    # print_results function
    print(str(msg), "works!" if passes else "doesn't work :(")


def pytests() -> None:
    # pytests function

    # pytests function
    assert test_trie()


def main() -> None:
    # main function

    # main function
    """
    >>> pytests()
    """
    print_results("Testing trie functionality", test_trie())


if __name__ == "__main__":
    main()
