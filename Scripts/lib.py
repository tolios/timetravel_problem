import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import copy
from glob import glob
import re
from tqdm import tqdm

class wallet():
    '''
    Basic class, performing trading calculations and updates.
    This class is used to contain and update wallet and portofolio, during trading.
    Is also used for the agent class.
    Methods:
    -execute: Receives relevant information and performs trade if valid.
    -update: Updates portofolio and wallet entries. To be used when all orders of a day have finished.
    -is_valid: Calculates if a trade is possible.
    -projected_worth: simply returns latest wallet and portofolio profits.
    '''

    def __init__(self, start = 1.0, stocks_directory = 'Stocks'):

        self.start = start
        self.balance = [start]
        self.portofolio = [0]
        self.own_stocks = dict()
        self.balance_change = 0
        ##########################
        #specifically used for the is_valid method...
        self.highlow_flag = dict()
        self.close_flag = dict()
        self.daily_stocks_bought = dict()
        self.daily_stocks_sold = dict()
        self.previous_day_stocks = dict()

    def execute(self, date, action, name, stocks):
        #main part
        exchange, when = action.split('-')
        company = company_stocks(name)
        stock_worth = float(company.dataset[company.dataset['Date'] == date][when.capitalize()])
        stock_volume = int(company.dataset[company.dataset['Date'] == date]['Volume'])
        worth = stock_worth*int(stocks)

        if name not in self.highlow_flag:
            self.highlow_flag[name] = False
        if name not in self.close_flag:
            self.close_flag[name] = False

        #checks if transaction is valid...
        if int(stock_volume) != 0:
            valid_transaction = self.is_valid(name, exchange, when, stocks, stock_volume, worth)
        else:
            valid_transaction = False
        if not valid_transaction:
            return False



        if exchange == 'buy':
            #buying stocks...
            self.balance_change -= worth
            if name in self.own_stocks:
                self.own_stocks[name] += int(stocks)
            else:
                self.own_stocks[name] = int(stocks)

            #for is_valid...
            if name in self.daily_stocks_bought:
                self.daily_stocks_bought[name] += int(stocks)
            else:
                self.daily_stocks_bought[name] = int(stocks)

            #raising flags for is_valid method
            if when == 'close':
                self.close_flag[name] = True
            if when == 'high' or when == 'low':
                self.highlow_flag[name] = True

        else:
            #selling stocks
            self.balance_change += worth
            self.own_stocks[name] -= int(stocks)

            #for is_valid...
            if name in self.daily_stocks_sold:
                self.daily_stocks_sold[name] += int(stocks)
            else:
                self.daily_stocks_sold[name] = int(stocks)

            #raising flags for is_valid method
            if when == 'close':
                self.close_flag[name] = True
            if when == 'high' or when == 'low':
                self.highlow_flag[name] = True
            if self.own_stocks[name] == 0:
                #no longer have stocks in said company...
                del self.own_stocks[name]


        #returns True if valid transaction
        return True


    def update(self, date):
        #lower flags when day is over...
        self.highlow_flag = dict()
        self.close_flag = dict()
        #change of balance in the end of day.
        self.balance.append(self.balance[-1] + self.balance_change)
        self.balance_change = 0
        #zeroing memory for new day...
        self.daily_stocks_sold = dict()
        self.daily_stocks_bought = dict()
        self.previous_day_stocks = copy.deepcopy(self.own_stocks)
        self.previous_gain = 0
        #iterates through own stocks updating total portofolio worth
        possible_worth = 0
        try:
            if self.own_stocks:
                for name in self.own_stocks:
                    company = company_stocks(name)
                    #dataset might not contain the date...
                    stock_worth = float(company.dataset[company.dataset['Date'] == date]['Close'])
                    possible_worth += stock_worth*int(self.own_stocks[name])
            self.portofolio.append(possible_worth)
        except:
            #if some dont have values, we skip calculation of portofolio and keep the last one
            #remember that self.own_stocks contains the new stocks, so we wont get wrong portofolio,
            #once we have for all dates.
            self.portofolio.append(self.portofolio[-1])


    def is_valid(self, name, exchange, when, stocks, stock_volume, worth):
        valid = True

        if self.highlow_flag[name]:
            if when == 'open':
                #inappropriate timing
                valid = False
        if self.close_flag[name]:
            if when == 'open' or when == 'high' or when == 'low':
                #inappropriate timing
                valid = False
        #timeline consistencies...
        if name not in self.daily_stocks_sold:
            self.daily_stocks_sold[name] = 0
        if name not in self.daily_stocks_bought:
            self.daily_stocks_bought[name] = 0
        if exchange == 'buy' and (self.daily_stocks_bought[name]+int(stocks))/int(stock_volume) > 0.1:
            valid = False
        if exchange == 'sell' and (self.daily_stocks_sold[name]+int(stocks))/int(stock_volume) > 0.1:
            valid = False
        if name not in self.previous_day_stocks:
            self.previous_day_stocks[name] = 0
        if exchange == 'buy' and self.previous_day_stocks[name] + 1 < self.daily_stocks_bought[name]:
            valid = False
        #checks if the transactions are possible
        if exchange == 'sell' and self.own_stocks[name] < int(stocks):
            valid = False
        if exchange == 'buy' and self.balance[-1] + self.balance_change < worth:
            #print(name, exchange, when, stocks, stock_volume, worth)
            valid = False

        return valid

    def projected_worth(self):
            #what if i sold everything in the closing of a day...
            return self.portofolio[-1] + self.balance[-1]

class company_stocks():
    '''
    Stocks of a company.
    Given a compant name, produces all relevant information from the txt file of
    that company. Used in both stock_dataset and agent classes.
    -plot: plots all stock values of that company.
    '''

    def __init__(self, name):

        self.name = name
        self.dataset = pd.read_csv('Stocks/'+name.lower()+'.us.txt')
        self.dataset['Date'] =  pd.to_datetime(self.dataset['Date'])
        self.dates = self.dataset['Date']
        self.open = self.dataset['Open']
        self.high = self.dataset['High']
        self.low = self.dataset['Low']
        self.close = self.dataset['Close']
        self.volume = self.dataset['Volume']
        self.openint = self.dataset['OpenInt']
        self.rows = len(self.dataset)
        self.first_date = self.dates[0]
        self.last_date = self.dates[self.rows-1]
        self.dates_normal = self.normal_dates()

    def normal_dates(self):
        dates = []
        for date in self.dates:
            dates.append(str(date)[:-9])
        return np.array(dates)

    def plot(self):

        fig, ax = plt.subplots(figsize=(15, 8))
        ax.set_title(self.name + ' stocks over time')
        ax.plot(self.open, label = 'open')
        ax.plot(self.high, label = 'high')
        ax.plot(self.low, label = 'low')
        ax.plot(self.close, label = 'close')

        ax.set_xlabel('Date')
        ax.set_ylabel('Stock Value')

        idx = np.round(np.linspace(0, self.rows - 1, 10)).astype(int)

        plt.yscale('log')
        ax.set_xticks(idx)
        ax.set_xticklabels(self.dates_normal[idx], minor=False)
        plt.legend()
        plt.show()

class stocks_dataset():
    '''
    Class containing all useful companies. Is used to produce all relevant information
    for a given day. Filters the rest.
    Methods:
    -keep_good_companies: Filters only useful companies for the algorithm to work,
    as well as, for memory and time constraints.
    -prioritize: Produces list in descending order of highest valued companies in the end.
    This is crucial information for the algorith to work.
    '''


    def __init__(self, directory, slope = 4.0, future_profits = 100):

        self.companies = dict()
        self.directory = directory
        self.dictionary = {re.match(r'Stocks/(.*).us.txt', path).group(1).upper(): path for path in self.find_paths()}
        self.slope = slope
        self.future_profits = future_profits
        self.filtered = False
        if slope != -1:
            self.keep_good_companies(slope = slope)
        #loads filtered companies!
        self.load()
        self.hierarchy = self.prioritize()

    def __len__(self):
        return len(self.dictionary)

    def find_paths(self, sort = True):
        paths = glob(os.path.join(self.directory, "*.txt"))
        if sort:
            paths.sort()
        return paths

    def keep_good_companies(self, slope = 4.0):
        '''
        Given a slope, determine which countries have a slope bigger than,
        in logarithmic scale. Therefore only keep exponentially growing company stocks!
        Also, margin is used so as to pick countries that grow up to the margin and bigger.
        '''
        good = 0
        self.slope = slope
        new_dict = dict()
        good_companies = []
        for name in self.dictionary:
            try:
                company = company_stocks(name)

                #set to logarithmic scale to find all "exploding" companies
                y = np.log(company.low.to_numpy() + 0.0000001)
                x = np.arange(len(y))
                x = x/len(x)
                m, b = np.polyfit(x, y, 1)
                #GE is seed for early period!
                if (m > slope and company.high.to_numpy()[-1] > self.future_profits) or name == 'GE':
                    #companies we will keep!
                    good += 1
                    good_companies.append(name)
            except:
                #problematic files ...
                #ignored...
                pass

        new_dict = {name: self.dictionary[name] for name in good_companies}
        #gets filtered companies!
        self.dictionary = new_dict
        del new_dict, good_companies
        print('Kept only', good, 'companies')
        self.filtered = True

    def __getitem__(self, day):
        '''
        Given a day, returns a dictionary with names as keys and
        values, tuple with that company's stock values: open, high, low, close, vol
        '''
        #finds for specified date, all relevant stocks in our collection
        day_dict = dict()
        #iterates through all selected companies to get their daily information...
        for name in self.companies:
            company = self.companies[name]
            try:
                _, open_, high, low, close, vol, _ = company.dataset[company.dates == day].values[0]
                day_dict[name] = (open_, high, low, close, vol)
            except:
                pass
        return day_dict

    def load(self):
        if self.filtered:
            print('Loading filtered companies for speed')
        for name in tqdm(self.dictionary, desc = 'Loading companies ...'):
            self.companies[name] = company_stocks(name)

    def prioritize(self):
        #returns a list with ordered from best to worst future stock value!
        #stocks like BRK-A will be first
        hierarchy = []
        highest = []
        for name in self.companies:
            company = self.companies[name]
            highest.append(company.high[len(company.high)-1])
            hierarchy.append(name)

        #returns company names sorted with descending order of future value!
        return [name for _, name in sorted(zip(highest, hierarchy))][::-1]

class agent():
    '''
    Agent class responsible for executing the trading strategy and policies.
    Contains the basic policies, used in the algorithm.
    Policies are:
    -sell_all_policy: When the final_day is reached, start selling all stocks, respevting spacetime constains.
    -sell_policy: Determines whether to sell all but one stocks.
    -infection_policy: Determines which new company to acquire a stock of. Aquires the cheapest one in that day.
    -buy_policy: Determines which stocks to buy, from already owned companies. Buys hierarchically the best valued,
    using the self.hierarchy list.
    -intra_day_policy: If able, performs intra day trading, keeping the same stocks and producing small profit.
    Basic methods:
    -act: This method is used in a day to produce the actions for our algorithm.
    Selects one policy and acts with it.
    -execute: This method, simply uses the execute functionality of the wallet class.
    -premonition: Using the patience parameter, determines which is the best day in a window of dates
    is best to sell.
    -update_wallet: Updates wallet.
    Decision of policies:
    If a policy produces result, then all the next are not used.
    ex. if infection_policy produces actions, buy and intra day policies simply are not accessed for that day.
    Also this means that the previous policies did not produce any action.
    '''

    def __init__(self, hierarchy, patience = 500, margin = 4.0, final_day = -1):

        #hierarchy contains a list of names ordered with descending order of future value.
        #the first is the most valuable stock.
        self.hierarchy = hierarchy
        #patience parameter determines window of search for sell
        self.patience = patience
        #margin is used for determiming if intra day will be used.
        self.margin = margin
        #wallet, used for calculations.
        self.wallet = wallet()
        self.memory = dict()
        self.final_day = final_day
        self.flag = False
        #flags to determine which policy happened!
        self.sell_all_policy_ = False
        self.sell_policy_ = False
        self.buy_policy_ = False
        self.infection_policy_ = False
        self.intra_day_policy_ = False


    def act(self, stocks, dates, day, day_index):
        '''
        Basic method of the agent class. Given stocks, dates, day and day_index,
        determines which policy happens. Only one policy may happen. All policies,
        if they cannot be performed simply output an empty list.
        Order of hierarchy of policies:
        -sell_all_policy
        -sell_policy
        -infection_policy
        -buy_policy
        -intra_day_policy
        if no policy happens, outputs ([], True)
        '''

        daily_stocks = stocks[day]

        #only activates when it is the appropriate day...
        actions, valid = self.sell_all_policy(daily_stocks, day)
        if not actions and not self.flag:
            actions, valid = self.sell_policy(stocks, dates, day_index)
        if not actions and not self.flag:
            actions, valid = self.infection_policy(daily_stocks, day)
        if not actions and not self.flag:
            actions, valid = self.buy_policy(daily_stocks, day)
        if not actions and not self.flag:
            actions, valid = self.intra_day_policy(daily_stocks, day)
        return actions, valid

    def sell_all_policy(self, daily_stocks, day):
        '''
        When the day comes, sell everything you own!
        Outputs actions, valid
        valid is False only when a transaction is not allowed.
        '''
        valid = True
        actions = []
        if day == self.final_day:
            self.flag = True

        if self.flag:
            #start selling everything you can!
            for company in self.wallet.own_stocks.copy():
                if company in daily_stocks:
                    stocks_ = self.wallet.own_stocks[company]
                    _, _, _, _, vol = daily_stocks[company]
                    #spacetime protection...
                    stocks_ = stocks_ if stocks_ < int(0.1*vol) else int(0.1*vol)
                    action, valid_ = self.execute(day, 'sell-high', company, stocks_)
                    actions.append(action)
                    valid = valid and valid_
        if actions:
            self.sell_all_policy_ = True
        return actions, valid

    def sell_policy(self, stocks, dates, day_index):
        '''
        Sells stocks at a date determined in memory. If no memory of an owned company
        memory is made here using the premonition method.
        Outputs actions, valid
        valid is False only when a transaction is not allowed.
        '''
        #memory of best day sell!
        #selling policy
        day = dates[day_index]
        valid = True
        actions = []

        daily_stocks = stocks[day]
        if daily_stocks:
            for company in self.hierarchy[::-1]:
                if company in self.memory:
                    if self.memory[company] == day:
                        stocks_ = self.wallet.own_stocks[company]
                        _, _, _, _, vol = daily_stocks[company]
                        #spacetime safety...
                        #sell all but one
                        stocks_ = stocks_-1 if stocks_ < int(0.1*vol) else int(0.1*vol)-1
                        action, valid_ = self.execute(day, 'sell-high', company, stocks_)
                        actions.append(action)
                        valid = valid and valid_
                        del self.memory[company]
                else:
                    if company in self.wallet.own_stocks:
                        #could probably make it so only the lowest get sold!
                        if self.wallet.own_stocks[company] > 1:
                            #puts into memory!
                            self.premonition(company, stocks, dates, day_index)
        if actions:
            self.sell_policy_ = True
        return actions, valid

    def buy_policy(self, daily_stocks, day):
        '''
        Buys as many stocks as possible from the best
        Outputs actions, valid
        valid is False only when a transaction is not allowed.
        '''
        actions = []
        valid = True
        #buy stocks if possible
        for company in self.hierarchy:
            if company in daily_stocks:
                if company in self.wallet.own_stocks:
                    stocks = self.wallet.own_stocks[company]
                    _, _, low, _, vol = daily_stocks[company]
                    for able_stocks in range(stocks+1, 0, -1):
                        if able_stocks*low < self.wallet.balance[-1] + self.wallet.balance_change and able_stocks < int(0.1*vol):
                            action, valid_ = self.execute(day, 'buy-low', company, able_stocks)
                            actions.append(action)
                            valid = valid and valid_
                            break
        if actions:
            self.buy_policy_ = True
        return actions, valid

    def infection_policy(self, daily_stocks, day):
        '''
        Finds the cheapest not owned company and buys it.
        Outputs actions, valid
        valid is False only when a transaction is not allowed.
        '''
        actions = []
        valid = True
        infection = False
        min_ = 1e6
        for company in self.hierarchy:
            if company in daily_stocks:
                if company not in self.wallet.own_stocks:
                    _, _, low, _, _ = daily_stocks[company]
                    if low < min_:
                        infection = True
                        company_infected = company
                        min_ = low

        if infection and self.wallet.balance[-1] > min_:
            #perform infection!
            action, valid_ = self.execute(day, 'buy-low', company_infected, 1)
            actions.append(action)
            valid = valid and valid_

        if actions:
            self.infection_policy_ = True
        return actions, valid

    def intra_day_policy(self, daily_stocks, day):
        '''
        Sells then buys the same amount of stocks, if it is
        profitable enough. Main money making policy of the algorithm.
        Outputs actions, valid
        valid is False only when a transaction is not allowed.
        '''
        actions = []
        valid = True
        #this policy activates when you simply want
        #to keep current stocks, and generate small profits
        #intra day trading!
        for company in daily_stocks:
            if company in self.wallet.own_stocks:
                #if we have that company in our stocks!
                #want to buy only when profits are acceptable
                open_, high, low, close, vol = daily_stocks[company]
                #find biggest profit action per day
                profit1 = float(high) - float(close)
                profit2 = float(open_) - float(low)

                #spacetime safety!
                stock_num = self.wallet.own_stocks[company]
                stock_num = stock_num if stock_num < int(0.1*vol) else int(0.1*vol)

                #if not positive, we shouldn't trade!
                if profit1 >= profit2 and profit1 > self.margin:
                    #sell high, buy close
                    action, valid_ = self.execute(day, 'sell-high', company, stock_num)
                    actions.append(action)
                    valid = valid and valid_
                    action, valid_ = self.execute(day, 'buy-close', company, stock_num)
                    actions.append(action)
                    valid = valid and valid_
                if profit2 > profit1 and profit2 > self.margin:
                    #sell open, buy low
                    action, valid_ = self.execute(day, 'sell-open', company, stock_num)
                    actions.append(action)
                    valid = valid and valid_
                    action, valid_ = self.execute(day, 'buy-low', company, stock_num)
                    actions.append(action)
                    valid = valid and valid_
        if actions:
            self.intra_day_policy_ = True
        return actions, valid

    def execute(self, date, action, name, stocks):
        #basically executes the wallet action
        #valid is True, when transaction is allowed by all rules!
        valid = self.wallet.execute(date, action, name, stocks)
        return str(date)[:-9]+' '+action+' '+name+' '+str(stocks), valid

    def premonition(self, company, stocks, dates, day_index):
        '''
        Finds best day to sell, inside a window
        of days and years!
        '''
        max_sell = -1
        profit_day = None
        #find best sell day within time window...
        for date in dates[day_index: day_index+self.patience]:
            daily_stock = stocks[date]
            if company in daily_stock:
                _, high, _, _, _ = daily_stock[company]
                if high >= max_sell:
                    max_sell = high
                    profit_day = date
        #memory entry!
        if profit_day != dates[day_index]:
            self.memory[company] = profit_day
        else:
            for i in range(10):
                if company in stocks[dates[day_index+i]]:
                    self.memory[company] = dates[day_index+i]
                    break

    def update_wallet(self, day):
        #switch off flags for next day!
        self.sell_all_policy_ = False
        self.sell_policy_ = False
        self.buy_policy_ = False
        self.infection_policy_ = False
        self.intra_day_policy_ = False
        self.wallet.update(day)

    def which_policy(self):
        #determines which policy happened from flags
        #returns string with policy name!
        if self.sell_all_policy_:
            return 'sell all'
        if self.sell_policy_:
            return 'sell'
        if self.buy_policy_:
            return 'buy'
        if self.infection_policy_:
            return 'infection'
        if self.intra_day_policy_:
            return 'intra day'
        return 'no policy'

    def stock_info(self):
        #determines how many stocks the agent owns.
        #returns a tuple which is comprised of:
        #A list of company of stocks owned normalized to one
        #total number of stocks owned.
        N_stocks = 0
        stock_membership = []
        for company in self.hierarchy:
            if company in self.wallet.own_stocks:
                n = self.wallet.own_stocks[company]
                stock_membership.append(n)
                N_stocks += n
            else:
                stock_membership.append(0)
        stock_membership = np.array(stock_membership)/N_stocks
        return stock_membership, N_stocks

if __name__ == '__main__':
    N = 0
    path_dataset = stocks_dataset('Stocks')

    for name in path_dataset.dictionary:
        try:
            company = company_stocks(name)

            # m, b = np.polyfit(x, y, 1)
        except:
            N += 1

    print('Problematic stock files: ', N)
