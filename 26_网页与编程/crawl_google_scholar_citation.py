# -*- coding: utf-8 -*-

"""

算法实现：26_网页与编程 / crawl_google_scholar_citation



本文件实现 crawl_google_scholar_citation 相关的算法功能。

"""



# /// script

# requires-python = ">=3.13"

# dependencies = [

#     "beautifulsoup4",

#     "httpx",

# ]

# ///



import httpx

from bs4 import BeautifulSoup





def get_citation(base_url: str, params: dict) -> str:

    # get_citation function



    # get_citation function

    # get_citation 函数实现

    """

    Return the citation number.

    """

    soup = BeautifulSoup(

        httpx.get(base_url, params=params, timeout=10).content, "html.parser"

    )

    div = soup.find("div", attrs={"class": "gs_ri"})

    anchors = div.find("div", attrs={"class": "gs_fl"}).find_all("a")

    return anchors[2].get_text()





if __name__ == "__main__":

    params = {

        "title": (

            "Precisely geometry controlled microsupercapacitors for ultrahigh areal "

            "capacitance, volumetric capacitance, and energy density"

        ),

        "journal": "Chem. Mater.",

        "volume": 30,

        "pages": "3979-3990",

        "year": 2018,

        "hl": "en",

    }

    print(get_citation("https://scholar.google.com/scholar_lookup", params=params))

