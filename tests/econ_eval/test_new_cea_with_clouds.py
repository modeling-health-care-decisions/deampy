import numpy as np

from deampy import econ_eval as EV

np.random.seed(seed=1)

S0 = EV.Strategy(name='Base',
                 cost_obs=np.random.normal(loc=100, scale=10, size=100),
                 effect_obs=np.random.normal(loc=1, scale=.2, size=100),
                 color='red')
S1 = EV.Strategy(name='A1',
                 cost_obs=np.random.normal(loc=800, scale=50, size=100),
                 effect_obs=np.random.normal(loc=0.5, scale=0.1, size=100),
                 color='blue')
S2 = EV.Strategy(name='A2',
                 cost_obs=np.random.normal(loc=2000, scale=200, size=100),
                 effect_obs=np.random.normal(loc=10, scale=1, size=100),
                 color='green')
S3 = EV.Strategy(name='A3',
                 cost_obs=np.random.normal(loc=500, scale=50, size=100),
                 effect_obs=np.random.normal(loc=7, scale=1, size=100),
                 color='orange')
S4 = EV.Strategy(name='A4',
                 cost_obs=np.random.normal(loc=-100, scale=10, size=100),
                 effect_obs=np.random.normal(loc=2, scale=0.1, size=100),
                 color='purple')

cea = EV.CEA(strategies=[S0, S1, S2, S3, S4], if_paired=False, health_measure='u')

print('On frontier')
for s in cea.get_strategies_on_frontier():
    print(s.name)

print('Not on frontier')
for s in cea.get_strategies_not_on_frontier():
    print(s.name)

cea.plot_ce_plane(add_clouds=True)
cea.export_ce_table(cost_digits=1, interval_type='c')

#cea.print_pairwise_cea(interval_type='c')
cea.plot_pairwise_ceas(
    figure_size=(7, 7),
    font_size=7,
    effect_label='DALY Averted (Thousands)',
    cost_label='Additional Cost (Thousand Dollars)',
    center_s=40,
    cloud_s=10,
    transparency=0.1,
    x_range=[-20, 20],
    y_range=[-2500, 2500],
)
