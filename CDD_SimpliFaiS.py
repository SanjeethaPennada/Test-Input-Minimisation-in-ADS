import math
def CDD(L, ψ, p0=0.02):
    """
    Counter-Based Delta Debugging (CDD) algorithm.
    Inputs:
    - L: List of elements to minimize.
    - ψ: Property function, returns False for failure-inducing inputs.
    - p0: Initial probability (default is less than 0.05), but here 0.02.
    
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
    pr = p0 * (1.582 ** r) #default value = 1.582
    return min(pr, 0.999)  # Cap the probability to avoid exceeding 1


def compute_subset_size(pr, L_len):
    """
    Compute the optimal subset size for the given probability.
    Inputs:
    - pr: Current probability.
    - L_len: Length of the current list.

    Output:
    - Subset size for the current round.
    """
    if pr >= 1:  # Handle edge case to avoid math domain error
        return 1
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
    return 'rain' in L and 'Four NPCs' in L or 'night' in L and 'Four NPCs' in L


# Input List
L = [6624907388525486529, 5590853173915701067, 11595376130058892747, 11261989655324469416, 10827724883280509631, 18345568482389893230, 1580899482231826983, 1760263306195875505, 12193930106007007199, 8965582157476607102, 2012950392265273169, 8202849075528332341, 6570133562374327036, 8588501765608435261, 3725429243769496776, 12942124512259043244, 4899373996816986076, 7783727404168196753, 1601677913125771255, 4983866454221917867, 793883526509223864, 11096794554960802340, 18125725892881901402, 9314362118298296807, 10311091484298245286, 12405707544884411272, 14597101749787311194, 1437529571490662170, 160167791312577125, 12317005202958092029, 2630081664371749371, 2795511079265638899, 17619596962267012938, 12253574462247490343, 3709560905934411224, 97, 98, 99, 100, 73, 72, 71, 70, 69, 68, 61, 50, 40, 24, 26, 25, 27, 130, 456, 440, 305, 301, 347, 122, 165, 166, 211, 212, 215, 217, 218, 242, 243, 244, 312, 323, 334, 344, 343, 345, 162, 163, 164, 241, 306, 307, 346,'rain', 'fog', 'cloudy', 'night','Bike', 'Pedestrian', 'Four NPCs']


# Run CDD
reduced_list = CDD(L, ψ)
print("Reduced List:", reduced_list)

