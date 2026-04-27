# -*- coding: utf-8 -*-

"""

算法实现：example / example_usage



本文件实现 example_usage 相关的算法功能。

"""



#  Created by: Ramy-Badr-Ahmed (https://github.com/Ramy-Badr-Ahmed)

#  in Pull Request: #11554

#  https://github.com/TheAlgorithms/Python/pull/11554

#

#  Please mention me (@Ramy-Badr-Ahmed) in any issue or pull request

#  addressing bugs/corrections to this file.

#  Thank you!



"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""



from data_structures.suffix_tree.suffix_tree import SuffixTree







# =============================================================================

# 算法模块：main

# =============================================================================

def main() -> None:

    # main function



    # main function

    """

    Demonstrate the usage of the SuffixTree class.



    - Initializes a SuffixTree with a predefined text.

    - Defines a list of patterns to search for within the suffix tree.

    - Searches for each pattern in the suffix tree.



    Patterns tested:

        - "ana" (found) --> True

        - "ban" (found) --> True

        - "na" (found) --> True

        - "xyz" (not found) --> False

        - "mon" (found) --> True

    """



    text = "monkey banana"

    suffix_tree = SuffixTree(text)



    patterns = ["ana", "ban", "na", "xyz", "mon"]

    for pattern in patterns:

        found = suffix_tree.search(pattern)

        print(f"Pattern '{pattern}' found: {found}")





if __name__ == "__main__":

    main()

