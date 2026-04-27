# -*- coding: utf-8 -*-








Using a combination of grey square tiles and oblong tiles chosen from:
red tiles (measuring two units), green tiles (measuring three units),
and blue tiles (measuring four units),
it is possible to tile a row measuring five units in length
in exactly fifteen different ways.

    |grey|grey|grey|grey|grey|       |red,red|grey|grey|grey|

    |grey|red,red|grey|grey|         |grey|grey|red,red|grey|

    |grey|grey|grey|red,red|         |red,red|red,red|grey|

    |red,red|grey|red,red|           |grey|red,red|red,red|

    |green,green,green|grey|grey|    |grey|green,green,green|grey|

    |grey|grey|green,green,green|    |red,red|green,green,green|

    |green,green,green|red,red|      |blue,blue,blue,blue|grey|

    |grey|blue,blue,blue,blue|

How many ways can a row measuring fifty units in length be tiled?


    >>> solution(5)
    15