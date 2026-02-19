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
    PASS = 'PASS'  # property not satisfied
    FAIL = 'FAIL'  # property satisfied

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

        assert self._test_config(self.current_best_config_idx, ('assert',)) is Outcome.FAIL

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

        assert self._test_config(current_config_idx, ('assert',)) is Outcome.FAIL

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
  14629083126418030590,
        12044691803723055623,
        11787230782715619853,
        16249365206454237195,
        10524282694208318484,
        4990921837289591321,
        14415130445061220374,
        13682437728760514584,
        16887196612155340823,
        5365658124388683805,
        15046929213216099359,
        10843952666397045793,
        5526699101654839333,
        16806868381472798751,
        12215923361026932776,
        17150913427873212966,
        3740906564190154284,
        12495691760231386670,
        12382831330667386415,
        13849945566840305199,
        14545609827858096178,
        984531414431178308,
        14323467047825696831,
        14724389718272911423,
        11375386848259744832,
        2484650683583877705,
        10944871636349280329,
        553336168711390803,
        14260382128454729806,
        6152357290997665370,
        1840917525183906911,
        4428826972742246495,
        9625298279031795291,
        15504585032343404639,
        8759686939644524643,
        17755514505869882463,
        8176918256333549158,
        11645801049091093097,
        8083786122614449263,
        4687515420348263031,
        1562699237605548669,
        11732188704403739769,
        6958315545574823548,
        6599157963354147460,
        17605158174447176836,
        12496842162389383821,
        1273653098034431123,
        6432541834932299922,
        17235122108563265677,
        16186209201407313554,
        8223934525506136217,
        11415255042173040792,
        2661338064383788189,
        17560626991655729319,
        8072835138550753452,
        3670187631272361134,
        7762665143441393836,
        10199914373438228143,
        12266203196460257454,
        8794281533802726069,
        5238057263115307703,
        13939520498437195445,
        12078131182523114168,
        17475296379880973499,
        13820588846531928767,
        8167058584016693954,
        15238124405572899009,
        9510000523093073609,
        13518946051787357386,
        8323587211028569294,
        8732043879944152783,
        16313181619495315148,
        1309893919863712474,
        12261070413986386661,
        9600090438672914153,
        2787361543575081199,
        15282366474488082155,
        7880905633739802351,
        12740515991975753969,
        4593551479207885563,
        6104543018473576193,
        15407330551144689921,
        11302300036802702085,
        7032373181792815366,
        4864804515467129098,
        15737085178123335430,
        1645911225909649688,
        13813312462682639650,
        5344815380947694886,
        8480431953392606504,
        6514095914585850669,
        17267652342373700911,
        9079601028819634996,
        14296769888808808242,
        12481717351552901938,
        16152256174392885045,
        6197096724272461116,
        9608007272875567931,
        6139975750507333448,
        4604006333330424137,
        10322437638966093127,
        12268002719898572616,
        4932649977950198601,
        374504254492218192,
        12086686027909790032,
        6296819417829721943,
        17760334406089631573,
        17375226849935201624,
        11825076767809190749,
        16003504632672611165,
        7163339591923479905,
        12992265346355791711,
        8866738546483557729,
        9048112478154102623,
        13294177301177361765,
        9321473667010108263,
        3640266726395249515,
        16723804405178321254,
        5506737825174028137,
        16450635686025597802,
        5137500351520999792,
        13725883985223258990,
        13686071092872147315,
        4406556482947455355,
        16553804302339654005,
        9588893588573876609,
        12114179282472363398,
        5227126492445849998,
        8104127134131416466,
        4912923282932965273,
        14836321169981662108,
        11431439876557050271,
        2426856128320948644,
        6579379009551399333,
        2986529683977740202,
        15844954996823609767,
        11482994972927240106,
        7236970622029314987,
        10553693741256470958,
        5433768364331453362,
        10649589213450182065,
        18104486075086832559,
        11411500431478922680,
        18151811547478754741,
        9490097917423573432,
        15185986500752298423,
        18302541309294182842,
        10138450464556999615,
        17960218237713351102,
        8645966189909333956,
        3289943016631938504,
        10888068353317610949,
        16491570393976167878,
        6030763135588007373,
        12689337117691487696,
        3746263829671719894,
        16575173394337365969,
        107554107361481176,
        8351388965014716886,
        17798064116822404580,
        4908027782056315882,
        4681809741947632111,
        9337363127694677489,
        11128530166464526833
    ]
    

weather_time_conditions = ["morning", "dry", "clear"]

# List of streetlight IDs that should be turned off in the selected scenario

streetlight_ids =  [
     132,
        133,
        394,
        395,
        397,
        144,
        401,
        406,
        408,
        153,
        410,
        412,
        413,
        414,
        415,
        159,
        417,
        418,
        163,
        164,
        165,
        301,
        305,
        306,
        307,
        308,
        311,
        312,
        313,
        440,
        317,
        192,
        323,
        334,
        471,
        472,
        473,
        474,
        343,
        344,
        345,
        222,
        223,
        347,
        346
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
        
    logger.info("\n=== DD Run ===")
    dd_result = run_dd("dd")

	logger.info("=== CDD Run ===")
    cdd_result = run_dd("cdd")
   
    logger.info("\n=== ProbDD Run ===")
    probdd_result = run_dd("probdd")

    logger.info("\n=== Results ===")
  
    logger.info("DD Minimal Input: %s", dd_result)
    logger.info("CDD Minimal Input: %s", cdd_result)     
    logger.info("ProbDD Minimal Input: %s", probdd_result)
