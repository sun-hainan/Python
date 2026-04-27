# -*- coding: utf-8 -*-












































A row of five grey square tiles is to have a number of its tiles




replaced with coloured oblong tiles chosen




from red (length two), green (length three), or blue (length four).









If red tiles are chosen there are exactly seven ways this can be done.









    |red,red|grey|grey|grey|    |grey|red,red|grey|grey|









    |grey|grey|red,red|grey|    |grey|grey|grey|red,red|









    |red,red|red,red|grey|      |red,red|grey|red,red|









    |grey|red,red|red,red|









If green tiles are chosen there are three ways.









    |green,green,green|grey|grey|    |grey|green,green,green|grey|









    |grey|grey|green,green,green|









And if blue tiles are chosen there are two ways.









    |blue,blue,blue,blue|grey|    |grey|blue,blue,blue,blue|









Assuming that colours cannot be mixed there are 7 + 3 + 2 = 12 ways




of replacing the grey tiles in a row measuring five units in length.









How many different ways can the grey tiles in a row measuring fifty units in length




be replaced if colours cannot be mixed and at least one coloured tile must be used?









    of the given length be replaced if colours cannot be mixed




    and at least one coloured tile must be used









    >>> solution(5)




    12


