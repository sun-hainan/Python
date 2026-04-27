# -*- coding: utf-8 -*-












































Passcode derivation









A common security method used for online banking is to ask the user for three




random characters from a passcode. For example, if the passcode was 531278,




they may ask for the 2nd, 3rd, and 5th characters; the expected reply would




be: 317.









The text file, keylog.txt, contains fifty successful login attempts.









Given that the three characters are always asked for in order, analyse the file




so as to determine the shortest possible secret passcode of unknown length.









    >>> find_secret_passcode(["135", "259", "235", "189", "690", "168", "120",




    ...     "136", "289", "589", "160", "165", "580", "369", "250", "280"])




    12365890









    >>> find_secret_passcode(["426", "281", "061", "819" "268", "406", "420",




    ...     "428", "209", "689", "019", "421", "469", "261", "681", "201"])




    4206819




    for successful login attempts given by `input_file` text file.









    >>> solution("keylog_test.txt")




    6312980


