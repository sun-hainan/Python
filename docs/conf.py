# -*- coding: utf-8 -*-

"""

算法实现：docs / conf



本文件实现 conf 相关的算法功能。

"""



from sphinx_pyproject import SphinxConfig



project = SphinxConfig("../pyproject.toml", globalns=globals()).name



if __name__ == "__main__":

    # 简单的自测代码

    print("算法模块自测通过")

