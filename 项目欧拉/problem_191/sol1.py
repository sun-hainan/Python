# -*- coding: utf-8 -*-







































Problem 191









A particular school offers cash rewards to children with good attendance and




punctuality. If they are absent for three consecutive days or late on more




than one occasion then they forfeit their prize.









During an n-day period a trinary string is formed for each child consisting




of L's (late), O's (on time), and A's (absent).









Although there are eighty-one trinary strings for a 4-day period that can be




formed, exactly forty-three strings would lead to a prize:









OOOO OOOA OOOL OOAO OOAA OOAL OOLO OOLA OAOO OAOA




OAOL OAAO OAAL OALO OALA OLOO OLOA OLAO OLAA AOOO




AOOA AOOL AOAO AOAA AOAL AOLO AOLA AAOO AAOA AAOL




AALO AALA ALOO ALOA ALAO ALAA LOOO LOOA LOAO LOAA




LAOO LAOA LAAO









How many "prize" strings exist over a 30-day period?









References:




    - The original Project Euler project page:




    a clean interface for the solution() function below.









    It should get called with the number of days (corresponding




    to the desired length of the 'prize strings'), and the




    initial values for the number of consecutive absent days and




    number of total late days.









    >>> _calculate(days=4, absent=0, late=0)




    43




    >>> _calculate(days=30, absent=2, late=0)




    0




    >>> _calculate(days=30, absent=1, late=0)




    98950096




    of days, using a simple recursive function with caching to speed it up.









    >>> solution()




    1918080160




    >>> solution(4)




    43


