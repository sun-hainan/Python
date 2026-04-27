# -*- coding: utf-8 -*-

"""

算法实现：24_应用领域 / nagel_schrekenberg



本文件实现 nagel_schrekenberg 相关的算法功能。

"""



from random import randint, random







# construct_highway 函数实现

def construct_highway(

    number_of_cells: int,

    frequency: int,

    initial_speed: int,

    random_frequency: bool = False,

    random_speed: bool = False,

    max_speed: int = 5,

) -> list:

    """

    Build the highway following the parameters given

    >>> construct_highway(10, 2, 6)

    [[6, -1, 6, -1, 6, -1, 6, -1, 6, -1]]

    >>> construct_highway(10, 10, 2)

    [[2, -1, -1, -1, -1, -1, -1, -1, -1, -1]]

    """



    highway = [[-1] * number_of_cells]  # Create a highway without any car

    i = 0

    initial_speed = max(initial_speed, 0)

    while i < number_of_cells:

    # 条件循环

        highway[0][i] = (

            randint(0, max_speed) if random_speed else initial_speed

        )  # Place the cars

        i += (

            randint(1, max_speed * 2) if random_frequency else frequency

        )  # Arbitrary number, may need tuning

    return highway

    # 返回结果







# get_distance 函数实现

def get_distance(highway_now: list, car_index: int) -> int:

    """

    Get the distance between a car (at index car_index) and the next car

    >>> get_distance([6, -1, 6, -1, 6], 2)

    1

    >>> get_distance([2, -1, -1, -1, 3, 1, 0, 1, 3, 2], 0)

    3

    >>> get_distance([-1, -1, -1, -1, 2, -1, -1, -1, 3], -1)

    4

    """



    distance = 0

    cells = highway_now[car_index + 1 :]

    for cell in range(len(cells)):  # May need a better name for this

    # 遍历循环

        if cells[cell] != -1:  # If the cell is not empty then

    # 条件判断

            return distance  # we have the distance we wanted

    # 返回结果

        distance += 1

    # Here if the car is near the end of the highway

    return distance + get_distance(highway_now, -1)

    # 返回结果







# update 函数实现

def update(highway_now: list, probability: float, max_speed: int) -> list:

    """

    Update the speed of the cars

    >>> update([-1, -1, -1, -1, -1, 2, -1, -1, -1, -1, 3], 0.0, 5)

    [-1, -1, -1, -1, -1, 3, -1, -1, -1, -1, 4]

    >>> update([-1, -1, 2, -1, -1, -1, -1, 3], 0.0, 5)

    [-1, -1, 3, -1, -1, -1, -1, 1]

    """



    number_of_cells = len(highway_now)

    # Beforce calculations, the highway is empty

    next_highway = [-1] * number_of_cells



    for car_index in range(number_of_cells):

    # 遍历循环

        if highway_now[car_index] != -1:

    # 条件判断

            # Add 1 to the current speed of the car and cap the speed

            next_highway[car_index] = min(highway_now[car_index] + 1, max_speed)

            # Number of empty cell before the next car

            dn = get_distance(highway_now, car_index) - 1

            # We can't have the car causing an accident

            next_highway[car_index] = min(next_highway[car_index], dn)

            if random() < probability:

    # 条件判断

                # Randomly, a driver will slow down

                next_highway[car_index] = max(next_highway[car_index] - 1, 0)

    return next_highway

    # 返回结果







# simulate 函数实现

def simulate(

    highway: list, number_of_update: int, probability: float, max_speed: int

) -> list:

    """

    The main function, it will simulate the evolution of the highway

    >>> simulate([[-1, 2, -1, -1, -1, 3]], 2, 0.0, 3)

    [[-1, 2, -1, -1, -1, 3], [-1, -1, -1, 2, -1, 0], [1, -1, -1, 0, -1, -1]]

    >>> simulate([[-1, 2, -1, 3]], 4, 0.0, 3)

    [[-1, 2, -1, 3], [-1, 0, -1, 0], [-1, 0, -1, 0], [-1, 0, -1, 0], [-1, 0, -1, 0]]

    """



    number_of_cells = len(highway[0])



    for i in range(number_of_update):

    # 遍历循环

        next_speeds_calculated = update(highway[i], probability, max_speed)

        real_next_speeds = [-1] * number_of_cells



        for car_index in range(number_of_cells):

    # 遍历循环

            speed = next_speeds_calculated[car_index]

            if speed != -1:

    # 条件判断

                # Change the position based on the speed (with % to create the loop)

                index = (car_index + speed) % number_of_cells

                # Commit the change of position

                real_next_speeds[index] = speed

        highway.append(real_next_speeds)



    return highway

    # 返回结果





if __name__ == "__main__":

    # 条件判断

    import doctest



    doctest.testmod()

