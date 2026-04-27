# -*- coding: utf-8 -*-
"""
算法实现：26_网页与编程 / giphy

本文件实现 giphy 相关的算法功能。
"""

#!/usr/bin/env python3
"""
giphy

算法分类：网页与编程
描述：实现 giphy 算法的核心逻辑。
"""



# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
# ]
# ///

import httpx

giphy_api_key = "YOUR API KEY"
# Can be fetched from https://developers.giphy.com/dashboard/


def get_gifs(query: str, api_key: str = giphy_api_key) -> list:
    """
    Get a list of URLs of GIFs based on a given query..
    """
    formatted_query = "+".join(query.split())
    url = f"https://api.giphy.com/v1/gifs/search?q={formatted_query}&api_key={api_key}"
    gifs = httpx.get(url, timeout=10).json()["data"]
    return [gif["url"] for gif in gifs]


if __name__ == "__main__":
    print("\n".join(get_gifs("space ship")))
