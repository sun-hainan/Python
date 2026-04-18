Floyd-Warshall - 全源最短路径

原理: dp[k][i][j] = min(dp[k-1][i][j], dp[k-1][i][k]+dp[k-1][k][j])

def floyd(g):
    n = len(g)
    d = [row[:] for row in g]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k]+d[k][j] < d[i][j]:
                    d[i][j] = d[i][k]+d[k][j]
    return d
