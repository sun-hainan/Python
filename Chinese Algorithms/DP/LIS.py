LIS - 最长递增子序列

原理: dp[i] = max(dp[j]+1) for j<i and arr[j]<arr[i]

def lis(arr):
    if not arr: return 0
    n = len(arr)
    dp = [1]*n
    for i in range(1, n):
        for j in range(i):
            if arr[j]<arr[i]:
                dp[i] = max(dp[i], dp[j]+1)
    return max(dp)
