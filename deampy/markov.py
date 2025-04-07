import enum

import numpy as np
from numpy.random import RandomState

from deampy.random_variates import Empirical, Exponential, Multinomial


def continuous_to_discrete(trans_rate_matrix, delta_t):
    """
    :param trans_rate_matrix: (list of lists) transition rate matrix (assumes None or 0 for diagonal elements)
    :param delta_t: cycle length
    :return: transition probability matrix (list of lists)
             and the upper bound for the probability of two transitions within delta_t (float)
        converting [p_ij] to [lambda_ij] where
            mu_i = sum of rates out of state i
            p_ij = exp(-mu_i*delta_t),      if i = j,
            p_ij = (1-exp(-mu_i*delta_t))*lambda_ij/mu_i,      if i != j.

    """

    # list of rates out of each row
    rates_out = []
    for i, row in enumerate(trans_rate_matrix):
        rates_out.append(out_rate(row, i))

    prob_matrix = []
    for i in range(len(trans_rate_matrix)):
        prob_row = []   # list of probabilities
        # calculate probabilities
        for j in range(len(trans_rate_matrix[i])):
            prob = 0
            if i == j:
                prob = np.exp(-rates_out[i] * delta_t)
            else:
                if rates_out[i] > 0:
                    prob = (1 - np.exp(-rates_out[i] * delta_t)) * trans_rate_matrix[i][j] / rates_out[i]
            # append this probability
            prob_row.append(prob)

        # append this row of probabilities
        prob_matrix.append(prob_row)

    # probability that transition occurs within delta_t for each state
    probs_out = []
    for rate in rates_out:
        probs_out.append(1-np.exp(-delta_t*rate))

    # calculate the probability of two transitions within delta_t for each state
    prob_out_out = []
    for i in range(len(trans_rate_matrix)):

        # probability of leaving state i withing delta_t
        prob_out_i = probs_out[i]

        # probability of leaving the new state after i withing delta_t
        prob_out_again = 0

        for j in range(len(trans_rate_matrix[i])):
            if not i == j:

                # probability of transition from i to j
                prob_i_j = 0
                if rates_out[i]>0:
                    prob_i_j = trans_rate_matrix[i][j] / rates_out[i]
                # probability of transition from i to j and then out of j within delta_t
                prob_i_j_out = prob_i_j * probs_out[j]
                # update the probability of transition out of i and again leaving the new state
                prob_out_again += prob_i_j_out

        # store the probability of leaving state i to a new state and leaving the new state withing delta_t
        prob_out_out.append(prob_out_i*prob_out_again)

    # return the probability matrix and the upper bound for the probability of two transitions with delta_t
    return prob_matrix, max(prob_out_out)


def out_rate(rates, idx):
    """
    :param rates: list of rates leaving this state
    :param inx: index of this state
    :returns the rate of leaving this state (the sum of rates)
    """

    sum_rates = 0
    for i, v in enumerate(rates):
        if i != idx and v is not None:
            sum_rates += v
    return sum_rates


def discrete_to_continuous(trans_prob_matrix, delta_t):
    """
    :param trans_prob_matrix: (list of lists) transition probability matrix
    :param delta_t: cycle length
    :return: (list of lists) transition rate matrix
        Converting [p_ij] to [lambda_ij] where
            lambda_ii = None, and
            lambda_ij = -ln(p_ii) * p_ij / ((1-p_ii)*Delta_t)
    """

    assert type(trans_prob_matrix) == list, \
        "prob_matrix is a matrix that should be represented as a list of lists: " \
        "For example: [ [0.1, 0.9], [0.8, 0.2] ]."

    rate_matrix = []
    for i, row in enumerate(trans_prob_matrix):
        rate_row = []   # list of rates
        # calculate rates
        for j in range(len(row)):
            # rate is None for diagonal elements
            if i == j:
                rate = None
            else:
                # rate is zero if this is an absorbing state
                if trans_prob_matrix[i][i] == 1:
                    rate = 0
                else:
                    rate = -np.log(trans_prob_matrix[i][i]) * trans_prob_matrix[i][j] / ((1 - trans_prob_matrix[i][i]) * delta_t)
            # append this rate
            rate_row.append(rate)
        # append this row of rates
        rate_matrix.append(rate_row)

    return rate_matrix


class _Markov:

    def __init__(self, matrix, state_descriptions=None):
        """
        :param state_descriptions: (Enum) description of the states in the format of Enum
        """

        if len(matrix) == 0:
            raise ValueError('An empty probability or rate matrix is provided.')
        else:
            self._n_states = len(matrix)

        if state_descriptions is not None:
            assert type(state_descriptions) is enum.EnumType, 'State description should be an enumeration.'
            assert len(state_descriptions) == len(matrix), \
                ('The number of states in the transition probability/rate matrix '
                 'and the state description should be equal.')

            for i, element in enumerate(state_descriptions):
                assert i == element.value, \
                    'The elements in the state description should be indexed 0, 1, 2, ...' \
                    'The state {} is indexed {} but should be indexed {}.'.format(str(element), element.value, i)

        self._ifStateDescriptionProvided = False if state_descriptions is None else True
        if self._ifStateDescriptionProvided:
            self._states = list(state_descriptions)

    def _error_check(self, current_state_index=None, current_state=None):

        if current_state_index is None and current_state is None:
            raise ValueError('Either current_state_index or current_state should be provided.')

        if current_state_index is not None:
            if not (0 <= current_state_index < self._n_states):
                raise ValueError('The value of the current state index should be greater '
                                 'than 0 and smaller than the number of states. '
                                 'Value provided for current state index is {}.'.format(current_state_index))
        elif current_state is not None:
            assert current_state in self._states, \
                'The current state is invalid and not in the state description enumeration.'
            current_state_index = current_state.value

        return current_state_index


class MarkovJumpProcess(_Markov):

    def __init__(self, transition_prob_matrix, state_descriptions=None):
        """
        :param transition_prob_matrix: (list) transition probability matrix of a discrete-time Markov model
        :param state_descriptions: (Enum) description of the states in the format of Enum
        """

        assert type(transition_prob_matrix) is list, \
            'Transition probability matrix should be a list'

        _Markov.__init__(self,matrix=transition_prob_matrix, state_descriptions=state_descriptions)

        self._empiricalDists = []

        for i, probs in enumerate(transition_prob_matrix):

            # check if the sum of probabilities in this row is 1.
            s = sum(probs)
            if s < 0.99999 or s > 1.00001:
                raise ValueError('Sum of each row in a probability matrix should be 1. '
                                 'Sum of row {0} is {1}.'.format(i, s))

            # create an empirical distribution over the future states from this state
            self._empiricalDists.append(Empirical(probabilities=probs))

        self._n_states = len(self._empiricalDists)

    def get_next_state(self, current_state_index=None, current_state=None, rng=None):
        """
        :param current_state_index: (int) index of the current state
        :param current_state: (an element of an enumeration) current state
        :param rng: random number generator object
        :return: the index of the next state or the state description of the next state
        """

        # get current state index
        current_state_index = self._error_check(current_state_index=current_state_index, current_state=current_state)

        # find the next state index by drawing a sample from
        # the empirical distribution associated with this state
        next_state_index = self._empiricalDists[current_state_index].sample(rng=rng)

        if self._ifStateDescriptionProvided:
            # if the state description is provided, return the state description
            return self._states[next_state_index]
        else:
            # return the index of the next state
            return next_state_index


class Gillespie(_Markov):

    def __init__(self, transition_rate_matrix, state_descriptions=None):
        """
        :param transition_rate_matrix: transition rate matrix of the continuous-time Markov model
        :param state_descriptions: (Enum) description of the states in the format of Enum
        """

        assert isinstance(transition_rate_matrix, list), \
            'transition_rate_matrix should be an array, {} was provided'.format(type(transition_rate_matrix))

        _Markov.__init__(self, matrix=transition_rate_matrix, state_descriptions=state_descriptions)


        self._rateMatrix = transition_rate_matrix
        self._expDists = []
        self._empiricalDists = []

        for i, row in enumerate(transition_rate_matrix):

            # make sure all rates are non-negative
            for r in row:
                if r is not None and r < 0:
                    raise ValueError('All rates in a transition rate matrix should be non-negative. '
                                     'Negative rate ({}) found in row index {}.'.format(r, i))

            # find sum of rates out of this state
            rate_out = out_rate(row, i)
            # if the rate is 0, put None as the exponential and empirical distributions
            if rate_out > 0:
                # create an exponential distribution with rate equal to sum of rates out of this state
                self._expDists.append(Exponential(scale=1/rate_out))
                # find the transition rates to other states
                # assume that the rate into this state is 0
                rates = []
                for j, v in enumerate(row):
                    if i == j:
                        rates.append(0)
                    else:
                        rates.append(v)

                # calculate the probability of each event (prob_j = rate_j / (sum over j of rate_j)
                probs = np.array(rates) / rate_out
                # create an empirical distribution over the future states from this state
                self._empiricalDists.append(Empirical(probs))

            else:  # if the sum of rates out of this state is 0
                self._expDists.append(None)
                self._empiricalDists.append(None)

    def get_next_state(self, current_state_index=None, current_state=None, rng=None):
        """
        :param current_state_index: index of the current state
        :param current_state: (an element of an enumeration) current state
        :param rng: random number generator object
        :return: (dt, i) where dt is the time until next event, and i is the index of the next state
                or the state description of the next state.
               It returns None for dt if the process is in an absorbing state
        """

        # get current state index
        current_state_index = self._error_check(current_state_index=current_state_index, current_state=current_state)

        # if this is an absorbing state (i.e. sum of rates out of this state is 0)
        if self._expDists[current_state_index] is None:
            # the process stays in the current state
            dt = None
            i = current_state_index
        else:
            # find the time until next event
            dt = self._expDists[current_state_index].sample(rng=rng)
            # find the next state
            i = self._empiricalDists[current_state_index].sample(rng=rng)

        i = self._states[i] if self._ifStateDescriptionProvided else i

        return dt, i


class _CohortMarkov:

    def __init__(self):

        self._numInStates = [] # list of state sizes
        self._numInStatesOverTime = [] # list of number of patients in each state over time
        self._numToStatesOverTime = [] # list of number of transitions to each state over time
        self._n_time_steps = 0

    def get_state_size_over_time(self, state_index):
        """
        :return: list of state sizes
        """

        return self._numInStatesOverTime[state_index]

    def get_transition_to_states_over_time(self):
        """
        :return: list of number of transitions to each state
        """

        return self._numToStatesOverTime

    def get_sum_size_multiple_states(self, state_indices):
        """
        :param state_indices: list of indices of states
        :return: sum of the sizes of the states in the list
        """

        sum_size = 0
        for i in state_indices:
            sum_size += self._numInStates[i]

        return sum_size

    def get_sum_size_multiple_states_over_time(self, state_indices):
        """
        :param state_indices: list of indices of states
        :return: sum of the sizes of the states in the list
        """

        sum_size = np.zeros(self._n_time_steps+1)
        for i in state_indices:
            sum_size += np.array(self._numInStatesOverTime[i])

        return sum_size


class CohortMarkov(_CohortMarkov):

    def __init__(self, transition_prob_matrix):
        """
        :param transition_prob_matrix: (list of lists) transition probability matrix
        """

        assert type(transition_prob_matrix) is list, \
            'Transition probability matrix should be a list'

        _CohortMarkov.__init__(self)

        self._transition_prob_matrix = transition_prob_matrix
        self._nonZeroProbs = [] # list of non-zero probabilities
        self._indicesNonZeroProbs = [] # list of indices of non-zero probabilities

        for i, probs in enumerate(transition_prob_matrix):

            # check if the sum of probabilities in this row is 1.
            s = sum(probs)
            if s < 0.99999 or s > 1.00001:
                raise ValueError('Sum of each row in a probability matrix should be 1. '
                                 'Sum of row {0} is {1}.'.format(i, s))

            # find the indices of non-zero probabilities
            non_zero_probs = []
            non_zero_probs_indices = []
            for j, p in enumerate(probs):
                if p > 0:
                    non_zero_probs.append(p)
                    non_zero_probs_indices.append(j)

            self._nonZeroProbs.append(non_zero_probs)
            self._indicesNonZeroProbs.append(non_zero_probs_indices)

        self._n_states = len(self._transition_prob_matrix)


    def simulate(self, initial_condition, n_time_steps, rng=None):

        if rng is None:
            rng = RandomState(seed=0)

        self._n_time_steps = n_time_steps
        self._numInStates = initial_condition
        self._numInStatesOverTime = [[] for i in range(self._n_states)]
        self._numToStatesOverTime = [[] for i in range(self._n_states)]

        for k in range(n_time_steps):

            # store the size of each state
            for i in range(self._n_states):
                self._numInStatesOverTime[i].append(self._numInStates[i])

            # initialize the number of transitions to each state
            num_to_states = [0] * self._n_states

            for s in range(self._n_states):
                if self._numInStates[s] > 0:
                    # find the number of transitions to each state
                    binomial = Multinomial(N=self._numInStates[s],
                                           pvals=self._nonZeroProbs[s])
                    outs = binomial.sample(rng)
                    # update the number of transitions to each state
                    for i in range(len(outs)):
                        if i != s:
                            num_to_states[self._indicesNonZeroProbs[s][i]] += outs[i]
                    # update the number of patients in this state
                    self._numInStates[s] -= sum(outs)
                    # update the number of patients in states
                    for i in range(len(outs)):
                        self._numInStates[self._indicesNonZeroProbs[s][i]] += outs[i]

            # store the number of transitions to each state
            for i in range(self._n_states):
                self._numToStatesOverTime[i].append(num_to_states[i])

        # store the size of each state
        for i in range(self._n_states):
            self._numInStatesOverTime[i].append(self._numInStates[i])


class ContinuousTimeCohortMarkov(_CohortMarkov):

    def __init__(self, transition_rate_matrix, delta_t):
        """
        :param transition_rate_matrix: (list of lists) transition rate matrix
        :param delta_t: (float) cycle length
        """

        assert isinstance(transition_rate_matrix, list), \
            'transition_rate_matrix should be an array, {} was provided'.format(type(transition_rate_matrix))

        _CohortMarkov.__init__(self)

        self._markov = CohortMarkov(
            transition_prob_matrix = continuous_to_discrete(
                trans_rate_matrix=transition_rate_matrix,
                delta_t= delta_t))

    def simulate(self, initial_condition, n_time_steps, rng=None):
        """
        :param initial_condition: (list) initial size of each state
        :param n_time_steps: (int) number of time steps to simulate the cohort
        :param rng: random number generator object
        """

        self._markov.simulate(
            initial_condition=initial_condition,
            n_time_steps=n_time_steps,
            rng=rng)