import math
def CDD(L, ψ, p0=0.05):
    """
    Counter-Based Delta Debugging (CDD) algorithm.
    Inputs:
    - L: List of elements to minimize.
    - ψ: Property function, returns False for failure-inducing inputs.
    - p0: Initial probability (default is 0.05).
    
    Output:
    - Reduced list L that still satisfies the failure-inducing property ψ.
    """
    r = 0  # Round number
    while True:
        # Compute subset size for the current round
        pr = compute_probability(r, p0)
        s = compute_subset_size(pr, len(L))
        print(f"\nRound {r}: Subset size = {s}, Current L = {L}")
        
        if not L:  # Terminate if the list is empty
            break
        
        # Partition L into subsets of size s
        subsets = partition(L, s)
        removed_any = False
        
        for subset in subsets:
            temp = [item for item in L if item not in subset]
            
            # Skip empty temp lists
            if not temp:
                continue
            
            print(f"Testing subset: {subset}, Temp = {temp}, ψ(temp) = {ψ(temp)}")
            if ψ(temp):  # If the property still holds, update L
                print(f"Subset {subset} is removable. Updating L to {temp}.")
                L = temp
                removed_any = True
                break  # Restart after modifying L
        
        if not removed_any:
            # Perform an exhaustive check of single elements when no progress is made
            for item in L:
                temp = [i for i in L if i != item]
                if ψ(temp):  # Check if the property holds without this single item
                    print(f"Single element {item} is removable. Updating L to {temp}.")
                    L = temp
                    removed_any = True
                    break
            
            if not removed_any:
                print("No subsets removed in this round.")
                break  # Stop if no progress is made
        
        r += 1  # Move to the next round

    print(f"\nFinal minimized list: {L}")
    return L


def compute_probability(r, p0):
    """
    Compute the probability for the current round.
    Inputs:
    - r: Current round number.
    - p0: Initial probability.
    
    Output:
    - Probability for the current round.
    """
    return p0 * (1.582 ** r)


def compute_subset_size(pr, L_len):
    """
    Compute the optimal subset size for the given probability.
    Inputs:
    - pr: Current probability.
    - L_len: Length of the current list.

    Output:
    - Subset size for the current round.
    """
    s = -1 / math.log(1 - pr)  # Compute subset size based on probability
    return max(1, min(round(s), L_len))  # Ensure subset size is at least 1 and does not exceed L_len


def partition(L, size):
    """
    Partition the list L into subsets of the given size.
    Inputs:
    - L: List to be partitioned.
    - size: Size of each subset.

    Output:
    - List of subsets.
    """
    return [L[i:i + size] for i in range(0, len(L), size)]


def ψ(L):
    """
    Property function: ψ returns True if both 2 and 3 are in the list, indicating a failure-inducing condition.
    """
    return 3 in L and 4 in L


# Input List
L = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Run CDD
reduced_list = CDD(L, ψ)
print("Reduced List:", reduced_list)
