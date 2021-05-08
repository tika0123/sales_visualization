import pandas as pd
import sales_functions
import datetime
import utils


estimation_df = pd.read_csv('./prediction_data/sales_estimation.csv', index_col='Lineitem sku')
order_df = pd.read_csv('./prediction_data/order_data.csv', index_col='Lineitem sku')
stock_df = pd.read_csv('./prediction_data/stock_data.csv')

stock = sales_functions.cleanStockData(stock_df)
for key, val in stock.items():
    stock_date = key
    stock_df = val

SIZE_LIST = ['XS', 'S', 'M', 'L', 'XL']
style_list = order_df['style'].unique()
all_sku = stock_df.index

order_df.columns = [datetime.datetime.strptime(x, "%Y/%m/%d").date() if x[:2] == "20" else x for x in order_df.columns]
order_dict = {}
for col in order_df:
    if type(col) == datetime.date:
        order_dict[col] = order_df[col]

start_date = stock_date
end_date = datetime.date(2021, 11, 30)
dateIndex = pd.date_range(start=start_date, end=end_date, freq="D")

case = 'base'
daily_sales = estimation_df[case].astype('float64')
storage_df = pd.DataFrame(index=all_sku)
remaining = stock_df['stock'].astype('float64')

for date in dateIndex:
    remaining = remaining - daily_sales

    if date in order_dict.keys():
        storage_df[date] = remaining + order_dict[date]



def getOrderMatrix(style, order_df, d):
    _df = order_df[order_df['Type'] == style]
    return_dict = {}

    for size in SIZE_LIST:
        _dict = {}
        for color in _df['Color'].unique():
            check_bool = (_df['Size'] == size) & (_df['Color'] == color)
            val = _df.loc[check_bool, d].values
            _dict[color] = val[0] if val.size > 0 else 0

        return_dict[size] = _dict

    return pd.DataFrame().from_dict(return_dict).T


def change_total(style, total, d, order_df, color = None, size = None):

    setting = {'style': style, 'color': color, 'size': size}
    _df = utils.selectSKU(order_df, setting)[d]
    t = _df.sum()
    _df = _df.map(lambda x : round(x * total / t))

    return _df


def change_style_proportion(style, proportion, d, order_df):

    if not 0 <= proportion <= 1:
        raise Exception('porportion not in range 0 to 1')

    number_dict = {}
    df_dict = {}
    total = 0

    for s in style_list:
        setting = {'style': s, 'color': None, 'size': None}
        _df = utils.selectSKU(order_df, setting)[d]
        df_dict[s] = _df
        unit = sum(_df)

        total = total + unit
        number_dict[s] = unit


    orig_style_proportion = number_dict[style] / total
    orig_non_style_proportion = (total - number_dict[style]) / total

    style_coefficient = proportion / orig_style_proportion
    non_style_coefficient = (1 - proportion) / orig_non_style_proportion

    return_df = pd.DataFrame()

    for s in style_list:
        if s == style:

            _df = df_dict[s].map(lambda x: round(x * style_coefficient))

        else:
            _df = df_dict[s].map(lambda x: round(x * non_style_coefficient))

        return_df = pd.concat([return_df, _df],)

    return return_df


change_style_proportion('full', 100, datetime.date(2021,6,10), order_df)

