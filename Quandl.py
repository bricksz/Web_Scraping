import quandl

quandl.ApiConfig.api_key = '6x7-xyr_2vY3k5aLyHsM'
df = quandl.get_table('ZACKS/FE', per_end_date='2018-12-31', ticker='AAPL')
print(df)