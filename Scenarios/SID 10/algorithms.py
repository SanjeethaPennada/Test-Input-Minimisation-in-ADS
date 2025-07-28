import itertools
import json
import logging
import math
import os
import random
import sys
import time
from enum import Enum
from typing import Callable, Sequence, Any, Tuple, List, Optional



class Outcome(Enum):
    PASS = 'PASS'  # Collision (property not satisfied)
    FAIL = 'FAIL'  # No Collision (property satisfied)

    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

class ZellerSplit(object):
  
    def __init__(self, n=2):
        
        self._n = n

    def __call__(self, subsets):
   
        config = [c for s in subsets for c in s]
        length = len(config)
        n = min(length, len(subsets) * self._n)
        
        next_subsets = []
        start = 0
        for i in range(n):
            stop = start + (length - start) // (n - i)
            next_subsets.append(config[start:stop])
            start = stop
        return next_subsets

    def __str__(self):
        cls = self.__class__
        return '%s.%s(n=%s)' % (cls.__module__, cls.__name__, self._n)



class OutcomeCache(object):

    def set_test_builder(self, test_builder):
     
        pass

    def add(self, config, result):
    
        pass

    def lookup(self, config):
     
        return None

    def clear(self):
   
        pass

    def __str__(self):
        return '{}'


class ConfigCache(OutcomeCache):
  
    class _Entry(object):

        def __init__(self):
            self.result = None  # Result so far
            self.tail = {}   # Points to outcome of tail



    def __init__(self):
        self._root = self._Entry()

    def add(self, config, result):
        p = self._root
        for cs in config:
            if cs not in p.tail:
                p.tail[cs] = self._Entry()
            p = p.tail[cs]
        p.result = result

    def lookup(self, config):
        p = self._root
        for cs in config:
            if cs not in p.tail:
                return None
            p = p.tail[cs]
        return p.result

    def clear(self):
        self._root = self._Entry()

    def __str__(self):
        def _str(p):
            if p.result is not None:
                s.append('\t[%s]: %r,\n' % (', '.join(repr(cs) for cs in config), p.result.name))
            for cs, e in sorted(p.tail.items()):
                config.append(cs)
                _str(e)
                config.pop()

        config, s = [], []
        s.append('{\n')
        _str(self._root)
        s.append('}')
        return ''.join(s)


class utils:
    @staticmethod
    def generate_log(indices, prefix, print_idx=True, threshold=30):
        if len(indices) > threshold:
            return f"\t{prefix}: {len(indices)} elements"
        return f"\t{prefix}: {[f'idx={i}' if print_idx else i for i in indices]}"



class AbstractCDD:
    
    def __init__(self, test, split, id_prefix=(), other_config=None):
        if other_config is None:
            other_config = {}
        self._test = test
        self._split = split
        self._id_prefix = id_prefix
        self.init_probability = other_config.get("init_probability", 0.09)
        self.dd = other_config.get("dd", "cdd")
        self.shuffle = other_config.get("shuffle")
        self.threshold = other_config.get("threshold", 0.9)

    def __call__(self, config):
        time_start = time.time()
        self.original_config = config[:]

        if self.shuffle is not None:
            random.seed(self.shuffle)
	 # initialize based on the specificed sample startegy
        if self.dd == "cdd":
         # initialize counters
            self.counters = [0 for _ in range(len(config))]
            self.sample = self.sample_by_counter
            self.update_when_pass = self.update_when_pass_cdd
            self.update_when_fail = self.update_when_fail_cdd
            self._test_done = self._test_done_cdd
        elif self.dd == "probdd":
            self.probabilities = [self.init_probability for _ in range(len(config))]
            self.sample = self.sample_by_probability
            self.update_when_pass = self.update_when_pass_probdd
            self.update_when_fail = self.update_when_fail_probdd
            self._test_done = self._test_done_probdd
        else:
            raise ValueError("dd should be either cdd or probdd")

        self.current_best_config_idx = [True for _ in range(len(config))]

        assert self._test_config(self.current_best_config_idx, ('assert',)) is Outcome.PASS

        logger.info('Run #%d', 0)
        logger.info('\tConfig size: %d', self.get_current_config_size())
        log_to_print = utils.generate_log(list(range(self.get_current_config_size())), "Try deleting", print_idx=True, threshold=30)
        logger.info(log_to_print)
        config_log_id = ('r%d' % 0,)
        outcome = self._test_config([False] * self.get_current_config_size(), config_log_id)

        if outcome is Outcome.PASS:
            logger.info("Final size: %d/%d" % (0, len(config)))
            logger.info("Execution time at this level: %f s" % (time.time() - time_start))
            return self.map_idx_to_config([False] * self.get_current_config_size())

        run = 1
        while not self._test_done():
            config_idx_to_delete = self.sample()
            if len(config_idx_to_delete) == self.get_current_config_size():
                logger.info('Deletion size too large, skip')
      
                self.update_when_pass(config_idx_to_delete)
                continue

            logger.info('Run #%d', run)
            logger.info('\tConfig size: %d', self.get_current_config_size())

            log_to_print = utils.generate_log(config_idx_to_delete, "Try deleting", print_idx=True, threshold=30)
            logger.info(log_to_print)
            config_log_id = ('r%d' % run,)

            config_to_keep = self.current_best_config_idx[:]
            for idx in config_idx_to_delete:
                config_to_keep[idx] = False
            outcome = self._test_config(config_to_keep, config_log_id)
            # FAIL means current variant cannot satisfy the property

            if outcome is Outcome.FAIL:
                self.update_when_pass(config_idx_to_delete)
            else:
                self.update_when_fail(config_idx_to_delete)
                log_to_print = utils.generate_log(config_idx_to_delete, "Deleted", print_idx=True, threshold=30)
                logger.info(log_to_print)

            run += 1

        logger.info("Final size: %d/%d" % (self.get_current_config_size(), len(config)))
        logger.info("Execution time at this level: %f s" % (time.time() - time_start))
        return self.map_idx_to_config(self.current_best_config_idx)

    def get_current_config_size(self):
        return sum(self.current_best_config_idx)

    def compute_size(self, counter):
        current_probability = self.init_probability
        factor = 1 - pow(math.e, -1)
        for _ in range(counter):
            current_probability /= factor
        max_size = 1
        max_gain = 0
        size = 1
        while True:
            gain = size * pow(1 - current_probability, size)
            if gain > max_gain:
                max_gain = gain
                max_size = size
            elif gain == max_gain:
                max_size = size
            else:
                break
            size += 1
        max_size = min(max_size, len(self.counters))
        max_size = max(max_size, 1)
        return max_size
 # increase all counters by 1
    def increase_all_counters(self):
        for idx in range(len(self.counters)):
            if self.counters[idx] != -1:
                self.counters[idx] = self.counters[idx] + 1
                
 # find out the minimal counter among all available elements
    def find_min_counter(self):
        current_min = sys.maxsize
        for counter in self.counters:
            if counter != -1 and current_min > counter:
                current_min = counter
        return current_min
        
  # how cdd compute the next subset to delete
    def sample_by_counter(self):
      # Filter out those removed elements (counter is -1)
        available_idx_with_counter = [
            (idx, counter) for idx, counter in enumerate(self.counters) if counter != -1
        ]
           # Shuffle the list first if self.shuffle is not None
        if self.shuffle is not None:
            random.shuffle(available_idx_with_counter)
            
         # Sort the list by counter
        sorted_available_idx_with_counter = sorted(available_idx_with_counter, key=lambda x: x[1])
        
          # Extract sorted indices
        available_idx = [idx for idx, _ in sorted_available_idx_with_counter]
        
           # Compute the size based on the minimum counter
        counter_min = self.find_min_counter()
        current_size = self.compute_size(counter_min)
        
             # Select indices to delete
        config_idx_to_delete = available_idx[:current_size]
        logger.info("\tSelected deletion size (cdd): " + str(len(config_idx_to_delete)))
        return config_idx_to_delete
        
 # how probdd compute the next subset to delete
    def sample_by_probability(self):
       # Filter out those removed elements (probability is -1)
        available_idx_with_probability = [
            (idx, probability) for idx, probability in enumerate(self.probabilities) if probability != -1
        ]
           # Shuffle the list first if self.shuffle is not None
        if self.shuffle is not None:
            random.shuffle(available_idx_with_probability)
            
             # Sort the list by probability
        sorted_available_idx_with_probability = sorted(available_idx_with_probability, key=lambda x: x[1])
        
         # Extract sorted indices
        available_idx = [idx for idx, _ in sorted_available_idx_with_probability]
        current_size = 0
        accumulated_probability = 1
        current_gain = 1
        last_gain = 0
        while current_size < len(available_idx):
            current_size += 1
            current_idx = available_idx[current_size - 1]
            accumulated_probability = accumulated_probability * (1 - self.probabilities[current_idx])
            current_gain = accumulated_probability * current_size
             # Find out the size with max gain and stop
            if current_gain < last_gain:
                current_size -= 1
                break
            last_gain = current_gain
        config_idx_to_delete = available_idx[:current_size]
        logger.info("\tSelected deletion size (probdd): " + str(len(config_idx_to_delete)))
        #logger.info("\tSelected deletion size (probdd): %d", len(config_idx_to_delete))
        return config_idx_to_delete

    # Given a subset failed to be deleted,
    # compute the ratio to increase the probability of each element in this subset
    def compute_ratio(self, config_idx_to_delete):
        accumulated_probability = 1
        for idx in config_idx_to_delete:
            accumulated_probability = accumulated_probability * (1 - self.probabilities[idx])

        ratio = 1 / (1 - accumulated_probability)
        return ratio

    def update_when_pass_cdd(self, config_idx_to_delete):
        for idx in config_idx_to_delete:
            self.counters[idx] = self.counters[idx] + 1
        if (len(config_idx_to_delete) == 1):
            # assign the counter to maxsize and never consider this element
            self.counters[config_idx_to_delete[0]] = -1

    def update_when_pass_probdd(self, config_idx_to_delete):
        ratio = self.compute_ratio(config_idx_to_delete)

        for idx in config_idx_to_delete:
            self.probabilities[idx] = self.probabilities[idx] * ratio
            if (self.probabilities[idx] > self.threshold):
                self.probabilities[idx] = -1

        if (len(config_idx_to_delete) == 1):
            # never consider this element
            self.probabilities[config_idx_to_delete[0]] = -1

    def update_when_fail_cdd(self, config_idx_to_delete):
        for idx in config_idx_to_delete:
            self.counters[idx] = -1
            self.current_best_config_idx[idx] = False

    def update_when_fail_probdd(self, config_idx_to_delete):
        for idx in config_idx_to_delete:
            self.probabilities[idx] = -1
            self.current_best_config_idx[idx] = False

    def _test_done_cdd(self):
        all_decided = True
        for counter in self.counters:
            if (counter != -1):
                all_decided = False
        if (all_decided == True):
            logger.info("Iteration needs to stop because all elements are decided.")
            return True
        else:
            return False

    def _test_done_probdd(self):
        all_decided = True
        for probability in self.probabilities:
            if (probability != -1):
                all_decided = False
        if (all_decided == True):
            logger.info("Iteration needs to stop because all elements are decided.")
            return True
        else:
            return False

    def map_idx_to_config(self, config_idx):
        new_config = []
        for idx, availability in enumerate(config_idx):
            if (availability == True):
                new_config.append(self.original_config[idx])

        return new_config


    def _test_config(self, config_idx, config_log_id):
        config_log_id = self._id_prefix + config_log_id
        logger.debug('\t[ %s ]: test...', self._pretty_config_id(config_log_id))
        new_config = self.map_idx_to_config(config_idx)
        tstart = time.time()
        outcome = self._test(new_config, config_log_id)
        logger.info("execution time of this test: %.6f s", time.time() - tstart)
        logger.debug('\t[ %s ]: test = %r', self._pretty_config_id(config_log_id), outcome)
        return outcome

    @staticmethod
    def _pretty_config_id(config_id):
        return ' / '.join(str(i) for i in config_id)
        
        

class CarlaCDD(AbstractCDD):
    def _processElementToPreserve(self, toBePreserve):
        return toBePreserve

    def _process(self, config, outcome):
        return config, outcome




class AbstractDD(object):
    """
    Abstract super-class of the parallel and non-parallel DD classes.
    """

    def __init__(self, test, *, split=None, cache=None, id_prefix=None, other_config=None):
           
        if other_config is None:
            other_config = {}
        self._test = test
        self._split = split or ZellerSplit()
        self._cache = cache or OutcomeCache()
        self._id_prefix = id_prefix or ()  # Changed to tuple for consistency
        self.onepass = other_config.get("onepass")
        self.start_from_n = other_config.get("start_from_n", 0)

    def __call__(self, config):
       
        time_start = time.time()
        subsets = [config]
        complement_offset = 0

        self.original_config = config[:]
        self.original_config_size = len(self.original_config)
        self.original_config_idx = list(range(self.original_config_size))
        current_config_idx = self.original_config_idx[:]

        assert self._test_config(current_config_idx, ('assert',)) is Outcome.PASS

        if self.start_from_n:
            subsets = split_list(self.original_config_idx, self.start_from_n)
        else:
            subsets = [self.original_config_idx]

        for run in itertools.count():
            logger.info('Run #%d', run)
            logger.info('\tConfig size: %d', len(current_config_idx))

            if len(current_config_idx) < 2:
                logger.info('\tGranularity: %d', len(subsets))
                logger.debug('\tConfig: %r', subsets)
                logger.info("\tFinal result: %d/%d", len(flatten(subsets)), self.original_config_size)
                logger.info("Execution time at this level: %.6f s", time.time() - time_start)
                return self.idx2config(current_config_idx)

            if len(subsets) < 2:
                assert len(subsets) == 1
                subsets = self._split(subsets)

            logger.info('\tGranularity: %d', len(subsets))
            logger.debug('\tConfig: %r', subsets)

            next_subsets, complement_offset = self._reduce_config(run, subsets, complement_offset)

            if next_subsets is not None:
            # Interesting configuration is found, start new iteration.
                subsets = next_subsets
                current_config_idx = [c for s in subsets for c in s]
                logger.info('\tReduced')
            elif len(subsets) < len(current_config_idx):
             # No interesting configuration is found but it is still not the finest splitting, start new iteration.
                next_subsets = self._split(subsets)
                complement_offset = 0
                subsets = next_subsets
                logger.info('\tIncreased granularity')
            else:
             # Minimization ends if no interesting configuration was found by the finest splitting.
                logger.info("\tFinal result: %d/%d", len(flatten(subsets)), self.original_config_size)
                logger.info("Execution time at this level: %.6f s", time.time() - time_start)
                return self.idx2config(current_config_idx)

    def _reduce_config(self, run, subsets, complement_offset):
         
        for i, subset in enumerate(subsets):
            cached_result = self._lookup_cache(subset, (f'r{run}', f's{i}'))
            if cached_result is not None:
                outcome = cached_result
            else:
                outcome = self._test_config(subset, (f'r{run}', f's{i}'))
            if outcome is Outcome.PASS:
                return [subset], 0

        for i in range(complement_offset, len(subsets)):
            complement = [c for s in subsets[:i] + subsets[i + 1:] for c in s]
            cached_result = self._lookup_cache(complement, (f'r{run}', f'c{i}'))
            if cached_result is not None:
                outcome = cached_result
            else:
                outcome = self._test_config(complement, (f'r{run}', f'c{i}'))
            if outcome is Outcome.PASS:
                return [complement], i + 1

        return None, complement_offset

    def _lookup_cache(self, config, config_id):
  
        cached_result = self._cache.lookup(config)
        if cached_result is not None:
            logger.debug('\t[ %s ]: cache = %r', self._pretty_config_id(self._id_prefix + config_id), cached_result.name)
        return cached_result

    def _test_config(self, config_idx, config_unique_id):
   
        config_unique_id = self._id_prefix + config_unique_id
        logger.debug('\t[ %s ]: test...', self._pretty_config_id(config_unique_id))
        start_time = time.time()
        config = self.idx2config(config_idx)
        outcome = self._test(config, config_unique_id)
        logger.info("execution time of this test: %.6f s", time.time() - start_time)
        logger.debug('\t[ %s ]: test = %r', self._pretty_config_id(config_unique_id), outcome)
        if 'assert' not in config_unique_id:
            self._cache.add(config_idx, outcome)
        return outcome

    @staticmethod
    def _pretty_config_id(config_id):
          
        return ' / '.join(str(i) for i in config_id)

    def idx2config(self, indices):
        new_indices = indices[:]
        new_indices.sort()
        config = []
        for i in indices:
            config.append(self.original_config[i])
        return config



class CarlaDD(AbstractDD):
    def _processElementToPreserve(self, toBePreserve):
        return toBePreserve

    def _process(self, config, outcome):
        return config, outcome



def split_list(input_list, chunk_size):
    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]


def flatten(l):
    return [item for sublist in l for item in sublist]


# CARLA simulation inputs


building_ids =   [
     11342267235671975038,
        15146692655721919741,
        444841318533572875,
        13307823757810026017,
        8883492342647673892,
        11318628607696758695,
        7314560581807414853,
        11136825046378637381,
        208766127642313803,
        6261186871686652622,
        10048214635049444300,
        7544612541256656848,
        16028723518164977748,
        11462137898848434263,
        210281769574983517,
        16000137402557712606,
        16281037675279273570,
        12302345139433072102,
        3519859878641663338,
        4841309662827135598,
        7501315804848990965,
        17406996573242554994
    ]
    

weather_time_conditions = ["morning", "dry", "clear"]

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =  [
              387,
        20,
        21,
        22,
        23,
        162,
        291,
        420,
        292,
        293,
        167,
        448,
        196,
        74,
        75,
        77,
        346,
        484,
        485,
        498
    ]
npc_ids = ['npc1', 'npc2', 'npc3', 'npc4']


# Simulation functions
def get_collision_rate(inp):
    with open('test_input.json', 'w') as f:
        json.dump(inp, f)

    output_file = "collision_output.txt"
    if os.path.exists(output_file):
        os.remove(output_file)

    carla_pid_file = "carla_terminal_pid.txt"
    remo_pid_file = "remo_terminal_pid.txt"
    replay_pid_file = "replay_terminal_pid.txt"
    collision_pid_file = "collision_terminal_pid.txt"

    try:
        os.system(f"gnome-terminal -- bash -c 'cd carla_server; ./CarlaUE4.sh; exec bash' & echo $! > {carla_pid_file}")
        logger.info("Started CARLA. Waiting 10 seconds...")
        time.sleep(10)
        os.system(f"gnome-terminal -- bash -c 'source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && bash run_remo.sh; exec bash' & echo $! > {remo_pid_file}")
        logger.info("Started run_remo.sh. Waiting 5 seconds...")
        time.sleep(5)
        npc_flags = [f"--{npc}" for npc in npc_ids if npc in inp]
        replay_command = f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && python3 replay_json.py {' '.join(npc_flags)}" if npc_flags else "source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && python3 replay_json.py"
        os.system(f"gnome-terminal -- bash -c '{replay_command}; exec bash' & echo $! > {replay_pid_file}")
        logger.info("Started replay_json.py. Waiting 3 seconds...")
        time.sleep(10)
        collision_command = f"source ~/anaconda3/etc/profile.d/conda.sh && conda activate king && python3 collisiontype.py > {output_file} 2>&1" #collision.py for weak oracle
        os.system(f"gnome-terminal -- bash -c '{collision_command}' & echo $! > {collision_pid_file}")
        logger.info("Started collision.py. Waiting 25 seconds...")
        time.sleep(25)

        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                output = f.read()
            logger.info("collision.py output:\n%s", output)
        else:
            raise ValueError("collision_output.txt not created")

        if "Front" in output:  #Accident for weak oracle
            return 1
        elif "Safe" in output:
            return 0
        else:
            raise ValueError("Collision or No Collision not found in collision.py output")

    except Exception as e:
        logger.error("Error parsing collision result: %s", e)
        return 0
    finally:
        logger.info("Cleaning up terminals for this test step...")
        for pid_file in [carla_pid_file, remo_pid_file, replay_pid_file, collision_pid_file]:
            if os.path.exists(pid_file):
                try:
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    if pid:
                        os.system(f"kill -SIGTERM {pid}")
                        logger.info("Terminated terminal with PID %s (%s)", pid, pid_file)
                except Exception as e:
                    logger.error("Error terminating terminal from %s: %s", pid_file, e)
                finally:
                    os.remove(pid_file)
        os.system("pkill -f CarlaUE4")
        os.system("pkill -f 'python3 replay_json.py'")
        os.system("pkill -f 'python3 collision.py'")
        if os.path.exists(output_file):
            os.remove(output_file)


def test_function(inp, config_log_id):
    try:
        collision_result = get_collision_rate(inp)
        return Outcome.PASS if collision_result == 1 else Outcome.FAIL
    except Exception as e:
        logger.error("Error during test: %s", e)
        return Outcome.FAIL



# Custom logging formatter
class CustomFormatter(logging.Formatter):
    def format(self, record):
        if record.msg.startswith('Run #%d'):
            return f"{record.msg % record.args}"
        elif record.msg == '\tConfig size: %d':
            return f"{'':<5} | {record.args[0]:<12} |"
        elif record.msg.startswith('\tTry deleting:') or record.msg.startswith('\tDeleted:'):
            return f"{'':<5} | {'':<12} | {record.msg % record.args}"
        elif record.msg == "\tSelected deletion size (cdd): %d" or record.msg == "\tSelected deletion size (probdd): %d":
            return f"{'':<5} | {'':<12} | Deletion size: {record.args[0]}"
        elif record.msg == '\tGranularity: %d':
            return f"{'':<5} | {'':<12} | Granularity: {record.args[0]}"
        elif record.msg == '\tReduced':
            return f"{'':<5} | {'':<12} | Reduced"
        elif record.msg == '\tIncreased granularity':
            return f"{'':<5} | {'':<12} | Increased granularity"
        elif record.msg == "execution time of this test: %.6f s":
            return f"{'':<5} | {'':<12} | Test time: {record.args[0]:.6f} s"
        elif record.msg == "Final size: %d/%d" or record.msg == "\tFinal result: %d/%d":
            return f"Final size: {record.args[0]}/{record.args[1]}"
        elif record.msg == "Execution time at this level: %.6f s":
            return f"Total time to evaluate: {record.args[0]:.6f} seconds"
        elif record.msg.startswith("collision.py output:"):
            return f"{record.msg % record.args}"
        elif record.msg.startswith("Started ") or record.msg == "Cleaning up terminals for this test step...":
            return record.msg
        elif record.msg.startswith("Terminated terminal with PID"):
            return record.msg % record.args
        elif record.msg == 'Deletion size too large, skip':
            return f"{'':<5} | {'':<12} | Deletion size too large, skipping"
        else:
            return super().format(record)


# Configure logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def run_dd(dd_type):
    initial_test_input =   npc_ids +  weather_time_conditions + building_ids + streetlight_ids







    logger.info("Initial Test Input: %s", initial_test_input)
    logger.info(f"Running {dd_type.upper()}...")
    logger.info(f"{'Run':<5} | {'Config Size':<12} | {'Tested Config':<60} | {'Test Step':<10} | {'Result'}")
    logger.info("-" * 100)

    test_count = 0
    def test_wrapper(inp, config_log_id):
        nonlocal test_count
        test_count += 1
        result = test_function(inp, config_log_id)
        config_str = str(inp)
        logger.info(f"{'':<5} | {sum(dd.current_best_config_idx if dd_type in ['cdd', 'probdd'] else [1 for _ in inp]):<12} | {config_str:<60} | {test_count:<10} | {'PASS' if result == Outcome.PASS else 'FAIL'}")
        return result

    if dd_type in ["cdd", "probdd"]:
        dd = CarlaCDD(
            test=test_wrapper,
            split=lambda x: [x[:len(x)//2], x[len(x)//2:]],
            id_prefix=(),
            other_config={
                "init_probability": 0.09,
                "dd": dd_type,
                "shuffle": 42,
                "threshold": 0.9
            }
        )
    elif dd_type == "dd":
        dd = CarlaDD(
            test=test_wrapper,
            split=ZellerSplit(n=2),
            cache=ConfigCache(),
            id_prefix=(),
            other_config={
                "onepass": False,
                "start_from_n": 0
            }
        )
    else:
        raise ValueError("dd_type should be 'cdd', 'probdd', or 'dd'")

    minimal_input = dd(initial_test_input)
    logger.info("-" * 100)
    logger.info("Minimal failure-inducing input found: %s", minimal_input)
    logger.info("Total number of test steps: %d", test_count)
    return minimal_input


if __name__ == "__main__":
        
    logger.info("=== CDD Run ===")
    cdd_result = run_dd("cdd")
   
    logger.info("\n=== ProbDD Run ===")
    probdd_result = run_dd("probdd")

    logger.info("\n=== DD Run ===")
    dd_result = run_dd("dd")
    
    logger.info("\n=== Results ===")

    logger.info("CDD Minimal Input: %s", cdd_result)     
    logger.info("ProbDD Minimal Input: %s", probdd_result)
    logger.info("DD Minimal Input: %s", dd_result)

