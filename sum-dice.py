from itertools import combinations, product
from math import comb


def calc_probability(S:int, n_dice:int):
    total = 6 ** n_dice
    count = 0
    for roll in product(range(1, 7), repeat=n_dice):
        for i, j in combinations(range(n_dice), 2):
            if roll[i] + roll[j] == S:
                count += 1
                break
    return count, total

def get_parameters(prompt:str, min_val:int, max_val:int):
    while True:
        try:
            val = int(input(prompt))
            if min_val <= val <= max_val:
                return val
            print(f"  please enter a value between {min_val} and {max_val}.")
        except ValueError:
            print("  please enter a valid integer.")

n_dice = get_parameters("\nnumber of dice (2 to 8): ", 2, 8)

min_sum = 2
max_sum = 12
sum = get_parameters(f"target sum S ({min_sum} to {max_sum}): ", min_sum, max_sum)

n_pairs = comb(n_dice, 2)
total_outcomes = 6 ** n_dice

print(f"\n{'=' * 60}")
print(f"  dice => {n_dice}   |   sum => {sum}")
print(f"  total outcomes : 6^{n_dice} = {total_outcomes:,}")
print(f"  number of pairs: C({n_dice},2) = {n_pairs}")
print(f"{'=' * 60}")

print(f"\ncalculating probabilityat least one pair of dice sums to {sum}...")
count, total = calc_probability(sum, n_dice)
p_exact = count / total

pairs = [(a, b) for a in range(1, 7) for b in range(a, 7) if a + b == sum]
print(f"pairs that sum to {sum}: {pairs}")

print(f"\nfavorable outcomes : {count:,} / {total:,}")
print(f"probability  : {p_exact:.6f}  ({p_exact*100:.2f}%)")