import numpy

from deampy import format_functions as form
from deampy import statistics as stat


def print_results(stat):
    print('   Average =', form.format_number(stat.get_mean(), deci=3))
    print('   St Dev =', form.format_number(stat.get_stdev(), deci=3))
    print('   Min =', form.format_number(stat.get_min(), deci=3))
    print('   Max =', form.format_number(stat.get_max(), deci=3))
    print('   Median =', form.format_number(stat.get_percentile(50), deci=3))
    print('   95% Mean Confidence Interval (t-based) =',
          form.format_interval(stat.get_t_CI(0.05), 3))
    print('   95% Mean Confidence Interval (bootstrap) =',
          form.format_interval(stat.get_bootstrap_CI(0.05, 1000), 3))
    print('   95% Percentile Interval =',
          form.format_interval(stat.get_PI(0.05), 3))


def mytest_summary_stat(data):
    # define a summary statistics
    sum_stat = stat.SummaryStat(data=data, name='Test summary statistics', )
    print('Testing summary statistics:')
    print_results(sum_stat)


def mytest_discrete_time(data):
    # define a discrete-time statistics
    discrete_stat = stat.DiscreteTimeStat('Test discrete-time statistics')
    # record data points
    for point in data:
        discrete_stat.record(point)

    print('Testing discrete-time statistics:')
    print_results(discrete_stat)


def mytest_continuous_time(times, observations):
    # define a continuous-time statistics
    continuous_stat = stat.ContinuousTimeStat(initial_time=0, name='Test continuous-time statistics')

    for obs in range(0, len(times)):
        # find the increment
        inc = 0
        if obs == 0:
            inc = observations[obs]
        else:
            inc = observations[obs] - observations[obs - 1]
        continuous_stat.record(times[obs], inc)

    print('Testing continuous-time statistics:')
    print_results(continuous_stat)


def mytest_diff_stat_indp(x, y):
    # define
    diff_stat = stat.DifferenceStatIndp(x, y, name='Test DifferenceStatIndp')
    print('Testing DifferenceStatIndp:')
    print_results(diff_stat)


def mytest_diff_stat_paired(x, y):
    # define
    diff_stat = stat.DifferenceStatPaired(x, y, name='Test DifferenceStatPaired')
    print('Testing DifferenceStatPaired:')
    print_results(diff_stat)


def mytest_ratio_stat_indp(x, y):
    # define
    ratio_stat = stat.RatioStatIndp(x, y, name='Test RatioStatIndp')
    print('Testing RatioStatIndp:')
    print_results(ratio_stat)


def mytest_ratio_stat_paied(x, y):
    # define
    ratio_stat = stat.RatioStatPaired(x, y, name='Test RatioStatPaired')

    print('Testing RatioStatPaired:')
    print_results(ratio_stat)


def mytest_relativeDiff_stat_paied(x, y):
    # define
    relative_stat = stat.RelativeDifferencePaired(x, y, name='Test RelativeDifferencePaired')

    print('Testing RelativeDifferencePaired:')
    print_results(relative_stat)

def mytest_relativeDiff_stat_indp(x, y):
    # define
    relative_stat = stat.RelativeDifferenceIndp(x, y, name='Test RelativeDifferenceIndp')

    print('Testing RelativeDifferenceIndp:')
    print_results(relative_stat)


# generate sample data
x = numpy.random.normal(10, 4, 1000)
y_ind = numpy.random.normal(5, 2, 1000)
delta = numpy.random.normal(5, 1, 1000)
y_diff_paired = x - delta
ratio = numpy.random.normal(2, 1, 1000)
y_ratio_paired = numpy.divide(x, ratio)

relative_ratio = numpy.random.normal(0.5, 0.1, 1000)
y_relativeRatio_paired = numpy.divide(x, 1+relative_ratio)


# populate a data set to test continuous-time statistics
sampleT = []
sampleObs = []
i = 0
for i in range(0, 100):
    t = numpy.random.uniform(i, i + 1)
    sampleT.append(t)
    sampleObs.append(10*t)

# test summary statistics
mytest_summary_stat(x)
# test discrete-time statistics
mytest_discrete_time(x)
# test continuous-time statistics
mytest_continuous_time(sampleT, sampleObs)
# test statistics for the difference of two independent samples
mytest_diff_stat_paired(x, y_diff_paired)
# test statistics for the ratio of two independent samples
mytest_diff_stat_indp(x, y_ind)
# test statistics for the difference of two paired samples
mytest_ratio_stat_paied(x, y_ratio_paired)
# test statistics for the relative difference of two paired samples
mytest_ratio_stat_indp(x, y_ind)
# test statistics for the ratio of two paired samples
mytest_relativeDiff_stat_paied(x, y_relativeRatio_paired)
# test statistics for the relative difference of two independent samples
mytest_relativeDiff_stat_indp(x, y_ind)
