# -*- coding: utf-8 -*-

"""

算法实现：26_网页与编程 / fetch_quotes



本文件实现 fetch_quotes 相关的算法功能。

"""



# /// script

# requires-python = ">=3.13"

# dependencies = [

#     "httpx",

# ]

# ///



import pprint



import httpx



API_ENDPOINT_URL = "https://zenquotes.io/api"





def quote_of_the_day() -> list:

    # quote_of_the_day function



    # quote_of_the_day function

    # quote_of_the_day 函数实现

    return httpx.get(API_ENDPOINT_URL + "/today", timeout=10).json()





def random_quotes() -> list:

    # random_quotes function



    # random_quotes function

    # random_quotes 函数实现

    return httpx.get(API_ENDPOINT_URL + "/random", timeout=10).json()





if __name__ == "__main__":

    """

    response object has all the info with the quote

    To retrieve the actual quote access the response.json() object as below

    response.json() is a list of json object

        response.json()[0]['q'] = actual quote.

        response.json()[0]['a'] = author name.

        response.json()[0]['h'] = in html format.

    """

    response = random_quotes()

    pprint.pprint(response)

