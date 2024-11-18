import random
from typing import List, Any

# Constants for test outcomes
PASS = "pass"
FAIL = "fail"

# Test function to check if the failure-inducing set {7, 8} is present
def test_function(subset):
    return set(['night', 'Four NPCs']).issubset(subset)

# Update probabilities based on test results
def update_probabilities(probabilities, excluded_indices, test_result):
    product = 1.0
    for i in excluded_indices:
        product *= (1 - probabilities[i])

    if test_result == PASS:  # Passed test
        for i in excluded_indices:
            probabilities[i] = 0
    else:  # Failed test
        for i in excluded_indices:
            probabilities[i] = probabilities[i] / max(1 - product, 1e-6)  # Avoid division by zero

    probabilities = [1 if p >= 0.99 else (0 if p <= 0.01 else p) for p in probabilities]
    return probabilities

# Select a subset for testing, prioritizing elements with higher probabilities
def select_subset(input_sequence, probabilities, subset_size):
    # Include elements with probability 1
    included = [input_sequence[i] for i, p in enumerate(probabilities) if p == 1]
    remaining = [input_sequence[i] for i, p in enumerate(probabilities) if p < 1]

    # Sort remaining elements by their probability in descending order
    remaining_sorted = sorted(zip(remaining, [probabilities[i] for i in range(len(probabilities)) if probabilities[i] < 1]), key=lambda x: x[1], reverse=True)

    # Select from the top elements of the sorted remaining list
    remaining_sorted = remaining_sorted[:subset_size - len(included)]

    # Extract just the elements from the sorted list
    selected_from_remaining = [x[0] for x in remaining_sorted]

    return included + selected_from_remaining

# Probabilistic Delta Debugging Algorithm
def probabilistic_delta_debugging(input_sequence: List[Any], probabilities: List[float], sigma: float) -> List[Any]:
    iteration = 1
    subset_size = len(input_sequence) // 2  # Start with n/2
    active_indices = list(range(len(input_sequence)))  # Track active indices

    while True:
        print(f"Iteration {iteration}")

        # Filter the input sequence and probabilities based on active indices
        filtered_sequence = [input_sequence[i] for i in active_indices]
        filtered_probabilities = [probabilities[i] for i in active_indices]

        # Select a subset of the current size
        subset = select_subset(filtered_sequence, filtered_probabilities, subset_size)
        print(f"Subset selected (size {subset_size}): {subset}")

        if test_function(subset):
            print("Test passed")
            test_result = PASS
            excluded_indices = [i for i in active_indices if input_sequence[i] not in subset]
        else:
            print("Test failed")
            test_result = FAIL
            excluded_indices = [i for i in active_indices if input_sequence[i] not in subset]

        # Update probabilities based on excluded indices
        probabilities = update_probabilities(probabilities, excluded_indices, test_result)

        # Update active indices based on probabilities
        active_indices = [i for i in range(len(probabilities)) if probabilities[i] > 0]

        print(f"Updated probabilities: {probabilities}")

        # Check if all probabilities are either 0 or 1
        if all(p == 0 or p == 1 for p in probabilities):
            print("Converged: All probabilities are either 0 or 1.")
            break

        # Adjust subset size
        if test_result == PASS:
            subset_size = max(1, len(subset) // 2)  # Reduce subset size on pass
        else:
            if all(probabilities[i] == probabilities[j] for i in active_indices for j in active_indices):
                subset_size = min(len(filtered_sequence), subset_size + 1)  # Increase subset size if uniform probabilities

        iteration += 1

    final_set = [input_sequence[i] for i in range(len(input_sequence)) if probabilities[i] > 0]
    return final_set

# Initialize the input sequence and their probabilities
input_sequence = [6624907388525486529, 5590853173915701067, 11595376130058892747, 11261989655324469416, 10827724883280509631, 18345568482389893230, 1580899482231826983, 1760263306195875505, 12193930106007007199, 8965582157476607102, 2012950392265273169, 8202849075528332341, 6570133562374327036, 8588501765608435261, 3725429243769496776, 12942124512259043244, 4899373996816986076, 7783727404168196753, 1601677913125771255, 4983866454221917867, 793883526509223864, 11096794554960802340, 18125725892881901402, 9314362118298296807, 10311091484298245286, 12405707544884411272, 14597101749787311194, 1437529571490662170, 160167791312577125, 12317005202958092029, 2630081664371749371, 2795511079265638899, 17619596962267012938, 12253574462247490343, 3709560905934411224, 97, 98, 99, 100, 73, 72, 71, 70, 69, 68, 61, 50, 40, 24, 26, 25, 27, 130, 456, 440, 305, 301, 347, 122, 165, 166, 211, 212, 215, 217, 218, 242, 243, 244, 312, 323, 334, 344, 343, 345, 162, 163, 164, 241, 306, 307, 346,'rain', 'fog', 'cloudy', 'night','Bike', 'Pedestrian', 'Four NPCs']

probabilities = [0.25] * len(input_sequence)
sigma = 0.25  # Initial probability hyper-parameter

# Run the Probabilistic Delta Debugging Algorithm
result = probabilistic_delta_debugging(input_sequence, probabilities, sigma)
print(f"Final minimal failure-inducing set: {result}")
