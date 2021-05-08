import pandas as pd

def getSKUDataFrame(df):
    sku_dict = {}
    sku_list = df.index.unique()

    for sku in sku_list:
        _df = df[df.index == sku]
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

def selectSKU(df, setting_dict, asIndex=False):
    sku_info = getSKUDataFrame(df)

    categories = ['style', 'color', 'size']
    for category in categories:

        if not setting_dict[category]:
            continue
        else:
            _list = setting_dict[category]
            sku_info = sku_info[sku_info[category].map(lambda x: x in _list)]

    if asIndex:
        return sku_info.index
    return df.loc[sku_info.index, :]