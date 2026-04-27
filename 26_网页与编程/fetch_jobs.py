# -*- coding: utf-8 -*-

"""

算法实现：26_网页与编程 / fetch_jobs



本文件实现 fetch_jobs 相关的算法功能。

"""



from __future__ import annotations



"""

Project Euler Problem  - Chinese comment version

https://projecteuler.net/problem=



问题描述: (请补充关于此题目具体问题描述)

解题思路: (请补充关于此题目的解题思路和算法原理)

"""





"""

Project Euler Problem  -- Chinese comment version

https://projecteuler.net/problem=



Description: (placeholder - add problem description)

Solution: (placeholder - add solution explanation)

"""







# /// script

# requires-python = ">=3.13"

# dependencies = [

#     "beautifulsoup4",

#     "httpx",

# ]

# ///





from collections.abc import Generator



import httpx

from bs4 import BeautifulSoup



url = "https://www.indeed.co.in/jobs?q=mobile+app+development&l="





def fetch_jobs(location: str = "mumbai") -> Generator[tuple[str, str]]:

    # fetch_jobs function



    # fetch_jobs function

    # fetch_jobs 函数实现

    soup = BeautifulSoup(httpx.get(url + location, timeout=10).content, "html.parser")

    # This attribute finds out all the specifics listed in a job

    for job in soup.find_all("div", attrs={"data-tn-component": "organicJob"}):

        job_title = job.find("a", attrs={"data-tn-element": "jobTitle"}).text.strip()

        company_name = job.find("span", {"class": "company"}).text.strip()

        yield job_title, company_name





if __name__ == "__main__":

    for i, job in enumerate(fetch_jobs("Bangalore"), 1):

        print(f"Job {i:>2} is {job[0]} at {job[1]}")

