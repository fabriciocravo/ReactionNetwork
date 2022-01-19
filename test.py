import copy
import itertools

list_of_lists = [
    ['A', 'B', 'C'],
    ['Hey', 'Ho'],
    ['1', '0']
]

comb = []
for i in itertools.product(*list_of_lists):
    comb.append(i)
    print(i)


