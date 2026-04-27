# -*- coding: utf-8 -*-

"""

Project Euler Problem 054



解决 Project Euler 第 054 题的 Python 实现。

https://projecteuler.net/problem=054

"""



from __future__ import annotations



"""

Project Euler Problem 054 — 中文注释版

https://projecteuler.net/problem=054



问题描述:

（请根据具体题目补充此部分）



解题思路:

（请根据具体题目补充此部分）

"""









import os







# =============================================================================

# Project Euler 问题 054

# =============================================================================

class PokerHand:

    """Create an object representing a Poker Hand based on an input of a

    string which represents the best 5-card combination from the player's hand

    and board cards.



    Attributes: (read-only)

        hand: a string representing the hand consisting of five cards



    Methods:

        compare_with(opponent): takes in player's hand (self) and

            opponent's hand (opponent) and compares both hands according to

            the rules of Texas Hold'em.

            Returns one of 3 strings (Win, Loss, Tie) based on whether

            player's hand is better than the opponent's hand.



        hand_name(): Returns a string made up of two parts: hand name

            and high card.



    Supported operators:

        Rich comparison operators: <, >, <=, >=, ==, !=



    Supported built-in methods and functions:

        list.sort(), sorted()

    """



    _HAND_NAME = (

        "High card",

        "One pair",

        "Two pairs",

        "Three of a kind",

        "Straight",

        "Flush",

        "Full house",

        "Four of a kind",

        "Straight flush",

        "Royal flush",

    )



    _CARD_NAME = (

        "",  # placeholder as tuples are zero-indexed

        "One",

        "Two",

        "Three",

        "Four",

        "Five",

        "Six",

        "Seven",

        "Eight",

        "Nine",

        "Ten",

        "Jack",

        "Queen",

        "King",

        "Ace",

    )



    def __init__(self, hand: str) -> None:

    # __init__ 函数实现

        """

        Initialize hand.

        Hand should of type str and should contain only five cards each

        separated by a space.



        The cards should be of the following format:

        [card value][card suit]



        The first character is the value of the card:

        2, 3, 4, 5, 6, 7, 8, 9, T(en), J(ack), Q(ueen), K(ing), A(ce)



        The second character represents the suit:

        S(pades), H(earts), D(iamonds), C(lubs)



        For example: "6S 4C KC AS TH"

        """

        if not isinstance(hand, str):

            msg = f"Hand should be of type 'str': {hand!r}"

            raise TypeError(msg)

        # split removes duplicate whitespaces so no need of strip

        if len(hand.split(" ")) != 5:

            msg = f"Hand should contain only 5 cards: {hand!r}"

            raise ValueError(msg)

        self._hand = hand

        self._first_pair = 0

        self._second_pair = 0

        self._card_values, self._card_suit = self._internal_state()

        self._hand_type = self._get_hand_type()

        self._high_card = self._card_values[0]



    @property

    def hand(self):

    # hand 函数实现

        """Returns the self hand"""

        return self._hand

    # 返回结果



    def compare_with(self, other: PokerHand) -> str:

        """

        Determines the outcome of comparing self hand with other hand.

        Returns the output as 'Win', 'Loss', 'Tie' according to the rules of

        Texas Hold'em.



        Here are some examples:

        >>> player = PokerHand("2H 3H 4H 5H 6H")  # Stright flush

        >>> opponent = PokerHand("KS AS TS QS JS")  # Royal flush

        >>> player.compare_with(opponent)

        'Loss'



        >>> player = PokerHand("2S AH 2H AS AC")  # Full house

        >>> opponent = PokerHand("2H 3H 5H 6H 7H")  # Flush

        >>> player.compare_with(opponent)

        'Win'



        >>> player = PokerHand("2S AH 4H 5S 6C")  # High card

        >>> opponent = PokerHand("AD 4C 5H 6H 2C")  # High card

        >>> player.compare_with(opponent)

        'Tie'

        """

        # Breaking the tie works on the following order of precedence:

        # 1. First pair (default 0)

        # 2. Second pair (default 0)

        # 3. Compare all cards in reverse order because they are sorted.



        # First pair and second pair will only be a non-zero value if the card

        # type is either from the following:

        # 21: Four of a kind

        # 20: Full house

        # 17: Three of a kind

        # 16: Two pairs

        # 15: One pair

        if self._hand_type > other._hand_type:

            return "Win"

    # 返回结果

        elif self._hand_type < other._hand_type:

            return "Loss"

    # 返回结果

        elif self._first_pair == other._first_pair:

            if self._second_pair == other._second_pair:

                return self._compare_cards(other)

    # 返回结果

            else:

                return "Win" if self._second_pair > other._second_pair else "Loss"

    # 返回结果

        return "Win" if self._first_pair > other._first_pair else "Loss"



    # This function is not part of the problem, I did it just for fun

    def hand_name(self) -> str:

    # hand_name 函数实现

        """

        Return the name of the hand in the following format:

        'hand name, high card'



        Here are some examples:

        >>> PokerHand("KS AS TS QS JS").hand_name()

        'Royal flush'



        >>> PokerHand("2D 6D 3D 4D 5D").hand_name()

        'Straight flush, Six-high'



        >>> PokerHand("JC 6H JS JD JH").hand_name()

        'Four of a kind, Jacks'



        >>> PokerHand("3D 2H 3H 2C 2D").hand_name()

        'Full house, Twos over Threes'



        >>> PokerHand("2H 4D 3C AS 5S").hand_name()  # Low ace

        'Straight, Five-high'



        Source: https://en.wikipedia.org/wiki/List_of_poker_hands

        """

        name = PokerHand._HAND_NAME[self._hand_type - 14]

        high = PokerHand._CARD_NAME[self._high_card]

        pair1 = PokerHand._CARD_NAME[self._first_pair]

        pair2 = PokerHand._CARD_NAME[self._second_pair]

        if self._hand_type in [22, 19, 18]:

            return name + f", {high}-high"

    # 返回结果

        elif self._hand_type in [21, 17, 15]:

            return name + f", {pair1}s"

    # 返回结果

        elif self._hand_type in [20, 16]:

            join = "over" if self._hand_type == 20 else "and"

            return name + f", {pair1}s {join} {pair2}s"

    # 返回结果

        elif self._hand_type == 23:

            return name

    # 返回结果

        else:

            return name + f", {high}"

    # 返回结果



    def _compare_cards(self, other: PokerHand) -> str:

        # Enumerate gives us the index as well as the element of a list

        for index, card_value in enumerate(self._card_values):

    # 遍历循环

            if card_value != other._card_values[index]:

                return "Win" if card_value > other._card_values[index] else "Loss"

    # 返回结果

        return "Tie"



    def _get_hand_type(self) -> int:

    # _get_hand_type 函数实现

        # Number representing the type of hand internally:

        # 23: Royal flush

        # 22: Straight flush

        # 21: Four of a kind

        # 20: Full house

        # 19: Flush

        # 18: Straight

        # 17: Three of a kind

        # 16: Two pairs

        # 15: One pair

        # 14: High card

        if self._is_flush():

            if self._is_five_high_straight() or self._is_straight():

                return 23 if sum(self._card_values) == 60 else 22

    # 返回结果

            return 19

        elif self._is_five_high_straight() or self._is_straight():

            return 18

    # 返回结果

        return 14 + self._is_same_kind()



    def _is_flush(self) -> bool:

    # _is_flush 函数实现

        return len(self._card_suit) == 1



    def _is_five_high_straight(self) -> bool:

    # _is_five_high_straight 函数实现

        # If a card is a five high straight (low ace) change the location of

        # ace from the start of the list to the end. Check whether the first

        # element is ace or not. (Don't want to change again)

        # Five high straight (low ace): AH 2H 3S 4C 5D

        # Why use sorted here? One call to this function will mutate the list to

        # [5, 4, 3, 2, 14] and so for subsequent calls (which will be rare) we

        # need to compare the sorted version.

        # Refer test_multiple_calls_five_high_straight in test_poker_hand.py

        if sorted(self._card_values) == [2, 3, 4, 5, 14]:

            if self._card_values[0] == 14:

                # Remember, our list is sorted in reverse order

                ace_card = self._card_values.pop(0)

                self._card_values.append(ace_card)

            return True

    # 返回结果

        return False



    def _is_straight(self) -> bool:

    # _is_straight 函数实现

        for i in range(4):

            if self._card_values[i] - self._card_values[i + 1] != 1:

                return False

    # 返回结果

        return True



    def _is_same_kind(self) -> int:

    # _is_same_kind 函数实现

        # Kind Values for internal use:

        # 7: Four of a kind

        # 6: Full house

        # 3: Three of a kind

        # 2: Two pairs

        # 1: One pair

        # 0: False

        kind = val1 = val2 = 0

        for i in range(4):

    # 遍历循环

            # Compare two cards at a time, if they are same increase 'kind',

            # add the value of the card to val1, if it is repeating again we

            # will add 2 to 'kind' as there are now 3 cards with same value.

            # If we get card of different value than val1, we will do the same

            # thing with val2

            if self._card_values[i] == self._card_values[i + 1]:

                if not val1:

                    val1 = self._card_values[i]

                    kind += 1

                elif val1 == self._card_values[i]:

                    kind += 2

                elif not val2:

                    val2 = self._card_values[i]

                    kind += 1

                elif val2 == self._card_values[i]:

                    kind += 2

        # For consistency in hand type (look at note in _get_hand_type function)

        kind = kind + 2 if kind in [4, 5] else kind

        # first meaning first pair to compare in 'compare_with'

        first = max(val1, val2)

        second = min(val1, val2)

        # If it's full house (three count pair + two count pair), make sure

        # first pair is three count and if not then switch them both.

        if kind == 6 and self._card_values.count(first) != 3:

            first, second = second, first

        self._first_pair = first

        self._second_pair = second

        return kind

    # 返回结果



    def _internal_state(self) -> tuple[list[int], set[str]]:

        # Internal representation of hand as a list of card values and

        # a set of card suit

        trans: dict = {"T": "10", "J": "11", "Q": "12", "K": "13", "A": "14"}

        new_hand = self._hand.translate(str.maketrans(trans)).split()

        card_values = [int(card[:-1]) for card in new_hand]

        card_suit = {card[-1] for card in new_hand}

        return sorted(card_values, reverse=True), card_suit

    # 返回结果



    def __repr__(self):

        return f'{self.__class__}("{self._hand}")'

    # 返回结果



    def __str__(self):

        return self._hand

    # 返回结果



    # Rich comparison operators (used in list.sort() and sorted() builtin functions)

    # Note that this is not part of the problem but another extra feature where

    # if you have a list of PokerHand objects, you can sort them just through

    # the builtin functions.

    def __eq__(self, other):

    # __eq__ 函数实现

        if isinstance(other, PokerHand):

            return self.compare_with(other) == "Tie"

    # 返回结果

        return NotImplemented



    def __lt__(self, other):

    # __lt__ 函数实现

        if isinstance(other, PokerHand):

            return self.compare_with(other) == "Loss"

    # 返回结果

        return NotImplemented



    def __le__(self, other):

    # __le__ 函数实现

        if isinstance(other, PokerHand):

            return self < other or self == other

    # 返回结果

        return NotImplemented



    def __gt__(self, other):

    # __gt__ 函数实现

        if isinstance(other, PokerHand):

            return not self < other and self != other

    # 返回结果

        return NotImplemented



    def __ge__(self, other):

    # __ge__ 函数实现

        if isinstance(other, PokerHand):

            return not self < other

    # 返回结果

        return NotImplemented



    def __hash__(self):

    # __hash__ 函数实现

        return object.__hash__(self)





def solution() -> int:

    # solution 函数实现

    # Solution for problem number 54 from Project Euler

    # Input from poker_hands.txt file

    answer = 0

    script_dir = os.path.abspath(os.path.dirname(__file__))

    poker_hands = os.path.join(script_dir, "poker_hands.txt")

    with open(poker_hands) as file_hand:

        for line in file_hand:

    # 遍历循环

            player_hand = line[:14].strip()

            opponent_hand = line[15:].strip()

            player, opponent = PokerHand(player_hand), PokerHand(opponent_hand)

            output = player.compare_with(opponent)

            if output == "Win":

                answer += 1

    return answer

    # 返回结果





if __name__ == "__main__":

    solution()

