Insertion Sort - 插入排序

原理: O(n^2), 稳定, 适合小规模数据

def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i-1
        while j>=0 and arr[j]>key:
            arr[j+1] = arr[j]
            j -= 1
        arr[j+1] = key
    return arr
