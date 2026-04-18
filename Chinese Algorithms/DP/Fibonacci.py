Fibonacci - 斐波那契数列

原理: DP, F(n)=F(n-1)+F(n-2)

class Fib:
    def __init__(self):
        self.c = [0,1]
    def get(self, n):
        for i in range(len(self.c), n+1):
            self.c.append(self.c[-1]+self.c[-2])
        return self.c[:n]
