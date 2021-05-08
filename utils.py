import pandas as pd
import datetime
import constants


def cleanSalesData(df):
    ## Lineitemの列を分割してstyle, color, sizeの列を作成
    df['style'] = df['Lineitem name'].str.split(' ', expand=True)[0]
    df['color'] = df['Lineitem name'].str.split(' ', expand=True)[2]
    df['size'] = df['Lineitem name'].str.split(' ', expand=True)[4]

    ##不要な行を削除する
    exclude_list = ['送料', '配送料', '再送料', '決済方法の変更']
    exclude_index = df[df['style'].isin(exclude_list)].index
    df = df.drop(exclude_index)

    ##カードの行の書式を整える
    card_list = ['best', 'happy', 'thank', 'white', 'international', 'merry']  # cardに該当するリスト
    df['style'] = df['style'].mask(df['style'].isin(card_list), 'card')  # リストのどれかの値に該当する場合、styleを”card”にする
    df['color'] = df['color'].where(df['style'] != 'card', 'card')
    df['size'] = df['size'].where(df['style'] != 'card', 'card')
    df['item_category'] = df['size'].where(df['style'] != 'card', 'card')

    ##バッグの行の書式を整える
    df['style'] = df['style'].mask(df['style'] == 'shopping', 'bag')
    df['color'] = df['color'].where(df['style'] != 'bag', 'bag')
    df['size'] = df['size'].where(df['style'] != 'bag', 'bag')
    df['item_category'] = df['size'].where(df['style'] != 'card', 'bag')

    # pos用のitem_categoryを作成する
    df['item_category'] = df['style'].mask(df['style'].str.contains('pos'), 'pos_item')

    # pos用のitem_categoryを作成する
    regular_item_list = ['standard', 'full', 'slim']
    df['item_category'] = df['item_category'].mask(df['item_category'].isin(regular_item_list), 'regular_item')

    # refundの注文をマイナスに処理
    def _subtractRefund(df, col):
        df[col] = df[col].where(df['Financial Status'] != 'refunded', -df[col])
        return df

    df = _subtractRefund(df, 'Subtotal')
    df = _subtractRefund(df, 'Lineitem quantity')
    df = _subtractRefund(df, 'Lineitem quantity')
    df = _subtractRefund(df, 'Shipping')
    df = _subtractRefund(df, 'Taxes')
    df = _subtractRefund(df, 'Total')

    # 日時の列を文字列から日付型に変換し、Indexを注文日に変更
    df['Created at'] = df['Created at'].map(lambda x: x[:19])
    df['Created at'] = pd.to_datetime(df['Created at'])

    # df['Paid at'] = df['Paid at'].map(lambda x : x[:19])
    df = df.set_index('Created at')

    # 2020年5月28日以前を削除
    start_date = datetime.datetime(2020, 5, 28, 0)
    df = df[df.index > start_date]

    return df


def cleanManufactureData(manufacture_df):
    manufacture_df = manufacture_df.set_index('Lineitem sku')
    manufacture_df = manufacture_df.iloc[:, 5:]
    manufacture_df = manufacture_df.fillna(0)
    manufacture_df.columns = pd.to_datetime(manufacture_df.columns)

    return manufacture_df


def cleanStockData(stock_df):
    stock_df = stock_df.set_index('Lineitem sku')

    ## stock_dfの日付データを日付型に変換
    stock_df['date'] = pd.to_datetime(stock_df['date'])

    ## 最新の日付を使用する
    stock_date = stock_df['date'].max()
    stock_df = stock_df[stock_df['date'] == stock_date]

    _dict = {stock_date: stock_df}

    return _dict


class ProcessData():

    def __init__(self, df, manufacture_df, latestStock):

        start_date = datetime.date(2020, 5, 28)
        today = datetime.date.today()
        dateIndex = pd.date_range(start=start_date, end=today, freq="D")

        self.date_df = pd.DataFrame(index=dateIndex)
        self.sku_info = self.getSKUDataFrame(df)

        self.sales = self.getSubtotal(df)
        self.unit = self.getUnit(df)
        self.production = self.getManufacture(manufacture_df)
        self.stock = self.getStock(latestStock)

        self.dict = {
            'sales': self.sales,
            'unit': self.unit,
            'production': self.production,
            'stock': self.stock,
        }

    ## SKUのIDとstyle, color, sizeの対応表を作成
    def getSKUDataFrame(self, df):
        sku_dict = {}
        for sku in df['Lineitem sku'].unique():
            _df = df[df['Lineitem sku'] == sku]
            try:
                sku_dict[sku] = {
                    'style': _df['style'][0],
                    'color': _df['color'][0],
                    'size': _df['size'][0],
                    'name': f"{sku}: {_df['style'][0]},{_df['color'][0]},{_df['size'][0]}",
                }
            except:
                continue

        return pd.DataFrame(sku_dict).T.sort_index()

    ##売上のデータフレームからSKU別の売上のデータを作成, index = date, columns = SKUID,
    def getSubtotal(self, df):

        # 空の日付をindexに持つデータフレームを使用
        sku_subtotal_df = self.date_df

        for sku in self.sku_info.index:
            _df = df[df['Lineitem sku'] == sku]
            try:
                # 売上枚数、金額の一覧を辞書に格納
                sku_subtotal_df[sku] = _df['Subtotal'].resample('d').sum()

            except:
                continue

        sku_subtotal_df = sku_subtotal_df.fillna(0).sort_index(axis=1)

        return sku_subtotal_df

    ##売上のデータフレームからSKU別の販売個数のデータを作成。index = date, columns = SKUID,
    def getUnit(self, df):

        # 空の日付をindexに持つデータフレームを使用
        sku_quantity_df = self.date_df

        for sku in self.sku_info.index:
            _df = df[df['Lineitem sku'] == sku]

            ##nanなどがあると辞書エラーが出るのでtry, exceptを仕様
            try:
                # 売上枚数、金額の一覧を辞書に格納
                sku_quantity_df[sku] = _df['Lineitem quantity'].resample('d').sum()

            except:
                continue

        sku_quantity_df = sku_quantity_df.fillna(0).sort_index(axis=1)

        return sku_quantity_df

    ##売上のデータフレームからSKU別の販売個数のデータを作成。index = date, columns = SKUID,
    def getManufacture(self, manufacture_df):
        sku_manufacture_df = self.date_df

        for sku in self.sku_info.index:
            try:
                sku_manufacture_df[sku] = manufacture_df[manufacture_df.index == sku].T
            except:
                continue

        sku_manufacture_df = sku_manufacture_df.fillna(0).sort_index(axis=1)
        return sku_manufacture_df

    ##在庫情報を取得
    def getStock(self, latestStock):

        ## stockのデータフレームを準備。各SKU,各日のデータを引き算することで各SKU／日毎の出入りを作成
        stock_df = self.production - self.unit
        ## 初日からの出入りを累計値にすることで在庫的な計算にする。
        stock_df = stock_df.cumsum()

        ## latestStockで確認した日付とのギャップを解消する
        ## latestStockのkeyストックを確認した日付の一つ、
        for key in latestStock.keys():
            calculated = stock_df[stock_df.index == key].fillna(0)  # 上記のstock_dfの確認日時点での数値を取る
            actual = latestStock[key]['stock'].fillna(0)  # 確認した値
            difference = actual - calculated  # 差分をとる

        for col in stock_df.columns:
            stock_df[col] = stock_df[col] + float(difference[col])  # stock_dfの差分を加えることで、確認日の差分を０に

        return stock_df

    def _selectSKU(self, df, setting_dict):

        sku_info = self.sku_info

        categories = ['style', 'color', 'size']
        for category in categories:
            if not setting_dict[category]:
                continue
            else:
                _list = setting_dict[category]
                sku_info = sku_info[sku_info[category].map(lambda x: x in _list)]

        return df[sku_info.index]

    def _selectDate(self, df, date_dict):

        _df = df.copy()
        startDate = date_dict['startDate']
        endDate = date_dict['endDate']

        if (startDate):
            _df = _df[_df.index >= startDate]

        if (endDate):
            _df = _df[_df.index <= endDate]

        return _df

    def getData(self, setting_dict):
        ##　アウトプットを選ぶ
        _df = self.dict[setting_dict['metric']]

        ## SKUを選ぶ - style
        _df = self._selectSKU(_df, setting_dict)

        ## 日付を選ぶ
        if setting_dict['start_date']:

            _list = [x >= setting_dict['start_date'] for x in _df.index]
            _df = _df.loc[_list,:]

        if setting_dict['end_date']:
            _list = [x <= setting_dict['end_date'] for x in _df.index]
            _df = _df.loc[_list,:]


        ## 当日か累計か
        if setting_dict['accumulate']:
            _df = _df.cumsum()

        ## 集計期間
        if setting_dict['period']:
            _period = setting_dict['period'][0]
            _df = _df.resample(_period).sum()

        if setting_dict['total']:
            _df = _df.sum(axis=1)
            _df.columns = ['total']

        # 列名を変換
        convert_dict = dict(zip(self.sku_info.index, self.sku_info['name']))
        try:
            _df = _df.rename(columns=convert_dict)
        except:
            pass

        return _df




def selectSKU(df, setting_dict, asIndex=False):

    sku_df = pd.read_json('sku.json').T

    print(setting_dict)
    categories = ['style', 'color', 'size']
    for category in categories:

        if not setting_dict[category]:
            continue

        else:
            sku_df = sku_df[sku_df[category] == setting_dict[category]]

    idx = sku_df.index

    if asIndex:
        return idx

    return df.loc[idx]


def getOrderMatrix(style, order_df, d):

    return_dict = {}

    for size in constants.SIZE_LIST:
        _dict = {}
        for color in constants.COLOR_LIST:

            setting = {'style':style, 'size':size, 'color':color}

            _df = selectSKU(order_df, setting)
            _dict[color] = _df.sum() if len(_df) == 1 else 0

        return_dict[size] = _dict

    return pd.DataFrame().from_dict(return_dict).T