# -*- coding: utf-8 -*-

"""

算法实现：26_网页与编程 / get_top_hn_posts



本文件实现 get_top_hn_posts 相关的算法功能。

"""



from __future__ import annotations





# /// script

# requires-python = ">=3.13"

# dependencies = [

#     "httpx",

# ]

# ///





import httpx





def get_hackernews_story(story_id: str) -> dict:

    url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json?print=pretty"

    return httpx.get(url, timeout=10).json()





def hackernews_top_stories(max_stories: int = 10) -> list[dict]:

    """

    Get the top max_stories posts from HackerNews - https://news.ycombinator.com/

    """

    url = "https://hacker-news.firebaseio.com/v0/topstories.json?print=pretty"

    story_ids = httpx.get(url, timeout=10).json()[:max_stories]

    return [get_hackernews_story(story_id) for story_id in story_ids]





def hackernews_top_stories_as_markdown(max_stories: int = 10) -> str:

    stories = hackernews_top_stories(max_stories)

    return "\n".join("* [{title}]({url})".format(**story) for story in stories)





if __name__ == "__main__":

    print(hackernews_top_stories_as_markdown())

