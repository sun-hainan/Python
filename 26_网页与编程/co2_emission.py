# -*- coding: utf-8 -*-

"""

算法实现：26_网页与编程 / co2_emission



本文件实现 co2_emission 相关的算法功能。

"""



# /// script

# requires-python = ">=3.13"

# dependencies = [

#     "httpx",

# ]

# ///



from datetime import date



import httpx



BASE_URL = "https://api.carbonintensity.org.uk/intensity"





# Emission in the last half hour

def fetch_last_half_hour() -> str:

    # fetch_last_half_hour function



    # fetch_last_half_hour function

    # fetch_last_half_hour 函数实现

    last_half_hour = httpx.get(BASE_URL, timeout=10).json()["data"][0]

    return last_half_hour["intensity"]["actual"]





# Emissions in a specific date range

def fetch_from_to(start, end) -> list:

    # fetch_from_to function



    # fetch_from_to function

    # fetch_from_to 函数实现

    return httpx.get(f"{BASE_URL}/{start}/{end}", timeout=10).json()["data"]





if __name__ == "__main__":

    for entry in fetch_from_to(start=date(2020, 10, 1), end=date(2020, 10, 3)):

        print("from {from} to {to}: {intensity[actual]}".format(**entry))

    print(f"{fetch_last_half_hour() = }")

