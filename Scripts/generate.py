import time
import sys
import os
import lib
import numpy as np
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt
from tqdm import tqdm
import warnings

#ignores warnings of filtering function....
if not sys.warnoptions:
    warnings.simplefilter("ignore")


'''
Make actions, then record them to file.
Receives a name for a txt file, like small.txt,
and then creates the appropriate moves.
Finally records them to said file.
'''

#txt is to be inserted as: > python generate.py file.txt

file = sys.argv[1]

dates = pd.date_range(start="1960-01-01",end="2022-01-01")

#our dataset!
#future point 170
stock_dataset = lib.stocks_dataset('Stocks', slope = 4.0, future_profits = 300)


N = 0
start = 900
# finish = 17000
# sell_day = 15000
finish = 14390
sell_day = 14380
print(finish - start)

bond_james = lib.agent(stock_dataset.hierarchy, patience = 1000, margin = 0.50, final_day = dates[sell_day])
actions = []
moves_cumulative = []
stock_nums = []
membership = []

for day_index, day in enumerate(dates[start:finish]):

    action, valid = bond_james.act(stock_dataset, dates, day, day_index+start)
    if action:
        actions.extend(action)
        N += len(action)

    if not valid:
        #if not valid, raise error...
        print(action)
        raise Exception("Problematic transaction(s)")

    moves_cumulative.append(N)

    policy = bond_james.which_policy()

    stock_membership, N_stocks = bond_james.stock_info()
    stock_nums.append(N_stocks)
    membership.append(stock_membership)

    #day finished, update all values!
    bond_james.update_wallet(day)
    print(str(day)[:-9], ':', 'Total moves:', N, 'Policy:', policy, 'Valid? ', valid,':',
        'Wallet: ', bond_james.wallet.balance[-1], 'Portofolio: ',bond_james.wallet.portofolio[-1])

#write actions to file!
with open(file, 'w') as f:
    f.write(str(N)+'\n')
    for action in actions:
        f.write(action+'\n')


print('Actual moves: ', N)
print('Final earnings: ', bond_james.wallet.projected_worth())
print('Wallet portofolio: ', bond_james.wallet.portofolio[-1])
print('Wallet balance: ', bond_james.wallet.balance[-1])
print('Final owned stocks: ', bond_james.wallet.own_stocks)

plt.title(f'Evaluation of {file}')

plt.fill_between(dates[start:finish+1], bond_james.wallet.portofolio, color = 'orange', label = 'portofolio')
plt.fill_between(dates[start:finish+1], bond_james.wallet.balance, color = 'blue', label = 'balance')

plt.legend(loc = 'upper left')

plt.yscale('log')
plt.show()

#move_density plot

fig, ax = plt.subplots()
ax.set_title('Cumulative moves of '+ file)

ax.set_xlabel('Date')
ax.set_ylabel('Cumulative Moves')
plt.fill_between(dates[start:finish], moves_cumulative, color = 'cyan', alpha=0.5)


plt.yscale('log')
plt.show()

#Number of stocks plot...
plt.title('Total number of owned stocks over time')
plt.fill_between(dates[start:finish], stock_nums, color='green', alpha=0.5)
plt.yscale('log')
plt.show()

#imshow plot

idx = np.round(np.linspace(0, len(dates[start:finish]) - 1, 10)).astype(int)
dates_normal = [str(date)[:-15] for date in dates[idx]]

mems = np.stack(membership, axis = 1)
plt.title('Stock membership over time')
c = plt.imshow(mems[:, ::500], interpolation ='nearest')
ax = plt.gca()
idy = np.round(np.linspace(0, len(mems[:, ::500]) - 1, 10)).astype(int)
ax.set_xticks(idy)
ax.set_xticklabels(dates_normal)
ax.set_yticks(np.arange(-.4, len(stock_dataset)-1, 1))
ax.set_yticklabels(stock_dataset.hierarchy)

plt.show()
