# -*- coding: utf-8 -*-
"""
算法实现：26_网页与编程 / covid_stats_via_xpath

本文件实现 covid_stats_via_xpath 相关的算法功能。
"""

# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
#     "lxml",
# ]
# ///

from typing import NamedTuple

import httpx
from lxml import html


# CovidData 类
class CovidData(NamedTuple):
    # CovidData class

    # CovidData class
    cases: str
    deaths: str
    recovered: str


def covid_stats(
    # covid_stats function

    # covid_stats function
    url: str = (
        "https://web.archive.org/web/20250825095350/"
        "https://www.worldometers.info/coronavirus/"
    ),
) -> CovidData:
    xpath_str = '//div[@class = "maincounter-number"]/span/text()'
    try:
        response = httpx.get(url, timeout=10).raise_for_status()
    except httpx.TimeoutException:
        print(
            "Request timed out. Please check your network connection "
            "or try again later."
        )
        return CovidData("N/A", "N/A", "N/A")
    except httpx.HTTPStatusError as e:
        print(f"HTTP error occurred: {e}")
        return CovidData("N/A", "N/A", "N/A")
    data = html.fromstring(response.content).xpath(xpath_str)
    if len(data) != 3:
        print("Unexpected data format. The page structure may have changed.")
        data = "N/A", "N/A", "N/A"
    return CovidData(*data)


if __name__ == "__main__":
    fmt = (
        "Total COVID-19 cases in the world: {}\n"
        "Total deaths due to COVID-19 in the world: {}\n"
        "Total COVID-19 patients recovered in the world: {}"
    )
    print(fmt.format(*covid_stats()))
