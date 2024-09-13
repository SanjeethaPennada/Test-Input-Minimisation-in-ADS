from typing import Callable, Sequence, Any, List

PASS = 0
FAIL = 1

def induce_failure(x: Sequence, F: Sequence[Sequence[int]]) -> int:
    """Simulate a test failure induced by the input x and the set of failure-inducing entities F.
    Return PASS if the failure is not induced, FAIL otherwise."""
    for subset in F:
        if set(subset).issubset(set(x)):
            return FAIL
    return PASS

def find_all_minimal_failure_inducing_subsets(test: Callable, inp: Sequence, *test_args: Any) -> List[Sequence]:
    """Find all minimal failure-inducing subsets of inp using the Delta Debugging approach."""
    
    minimal_subsets = []
    
    def ddmin_rec(inp: Sequence) -> Sequence:
        """Recursive helper function to find minimal failure-inducing subsets."""
        n = 2  # Initial granularity
        while len(inp) >= 2:
            start = 0
            subset_length = int(len(inp) / n)
            some_complement_is_failing = False

            while start < len(inp):
                complement = (inp[:int(start)] + inp[int(start + subset_length):])
                error_triggered = test(complement, *test_args) == FAIL
                if error_triggered:
                    inp = complement
                    n = max(n - 1, 2)
                    some_complement_is_failing = True
                    break
                start += subset_length

            if not some_complement_is_failing:
                if n == len(inp):
                    break
                n = min(n * 2, len(inp))
        
        # Once a minimal failure-inducing subset is found, save it.
        if inp not in minimal_subsets:
            minimal_subsets.append(inp)
        
        # Now, try to find other minimal subsets by excluding elements from the original input.
        for elem in inp:
            reduced_input = [x for x in inp if x != elem]
            if test(reduced_input, *test_args) == FAIL and reduced_input not in minimal_subsets:
                ddmin_rec(reduced_input)

    ddmin_rec(inp)
    
    # After finding the first minimal set, search the remaining part of the input for others
    for elem in inp:
        remaining_input = [x for x in inp if x != elem]
        if test(remaining_input, *test_args) == FAIL:
            ddmin_rec(remaining_input)
            
    return minimal_subsets

# Example usage
if __name__ == "__main__":
    # Original test input and failure-inducing sets
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    F = [[3, 8], [2, 8]]

    # Define test function
    def test_function(inp):
        return induce_failure(inp, F)

    # Apply modified Delta Debugging algorithm to find all minimal subsets
    all_minimal_inputs = find_all_minimal_failure_inducing_subsets(test_function, x)
    
    # Print results
    print("All minimal failure-inducing subsets:")
    for subset in all_minimal_inputs:
        print(subset)
