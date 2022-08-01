import sys
import os
import lib
import pandas as pd
from tqdm import tqdm
import matplotlib.pyplot as plt

'''
This code is the simulation of our time traveling money scheme...
'''

#txt is to be inserted as: > python simulation.py file.txt

series_file = sys.argv[1]
#dates we will pass for our simulation...
dates = pd.date_range(start="1960-01-01",end="2022-01-01")
my_wallet = lib.wallet()
#here we will define our wallet
#my_wallet = lib.wallet

N = 0
passed = 0
with open(series_file, 'r') as series:
    moves = series.readline().split('\n')[0]
    #simulation begins...
    #date counting...
    for date in tqdm(dates, desc='Years passing by...'):

        try:
            #gets information about next date
            last_pos = series.tell()
            next_date, _, _, _  = series.readline().split('\n')[0].split(' ')
            next_date = pd.Timestamp(next_date)
            series.seek(last_pos)

            if next_date == date:

                in_day = True
                while in_day:

                    last_pos = series.tell()
                    f_date, action, company, stocks = series.readline().split('\n')[0].split(' ')
                    f_date = pd.Timestamp(f_date)

                    if f_date == date:
                        '''
                        Trading using our stocks and balances happens here!
                        '''

                        N += 1
                        #both portofolio and our stocks are changed
                        valid = my_wallet.execute(f_date, action, company, stocks)
                        #if not valid, terminates program...
                        if not valid:
                            #exits from try to except SystemExit
                            sys.exit()

                    else:
                        #when this happens, our actions ended for this day!
                        series.seek(last_pos)
                        break
        except SystemExit:
            sys.exit('Not valid transaction, terminating program...')

        except :
            #If this part is executed, no more series remains!
            #therefore, we simply break and finish.
            #final day closing updates...
            my_wallet.update(date)
            passed += 1
            break


        '''
        In this part the day stops, so we update all our stocks...
        '''
        #updates for all our stock values happen here
        #our balance stays the same...
        my_wallet.update(date)
        passed += 1


print('Predicted moves: ', moves)
print('Actual moves: ', N)
print('Final earnings: ', my_wallet.projected_worth())
print('Wallet portofolio: ', my_wallet.portofolio[-1])
print('Wallet balance: ', my_wallet.balance[-1])
print('Final owned stocks: ', my_wallet.own_stocks)

plt.title(f'Evaluation of {series_file}')

plt.fill_between(dates[:passed+1], my_wallet.portofolio, color = 'orange', label = 'portofolio')
plt.fill_between(dates[:passed+1], my_wallet.balance, color = 'blue', label = 'balance')

plt.legend(loc = 'upper left')

plt.yscale('log')
plt.show()
