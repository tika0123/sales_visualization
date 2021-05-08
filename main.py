import streamlit as st
import pandas as pd
import sales_functions
import datetime

df = pd.read_csv('Raw data - orders_export_1.csv')
manufacture_df = pd.read_csv('Raw data - 過去の発売数_edited.csv')
latestStock = pd.read_csv('Raw data - 在庫数_edited.csv')

df = sales_functions.cleanSalesData(df)
manufacture_df = sales_functions.cleanManufactureData(manufacture_df)
latestStock = sales_functions.cleanStockData(latestStock)

processed = sales_functions.ProcessData(df, manufacture_df, latestStock)

st.title('Sales data')

col1, col2, col3 = st.beta_columns(3)


setting = {
    'metric': 'production',
    'style': [],
    'color': [],
    'size': [],
    'start_date': '',
    'end_date': '',
    'period': 'month',
    'accumulate': False,
    'average': False,
    'total':False,
}

min_date = datetime.datetime(2020, 5, 28, 0)
today = datetime.date.today()

setting['metric'] = st.sidebar.selectbox(
    'select',
    ('sales', 'unit', 'production', 'stock')
)

setting['size'] = st.sidebar.multiselect(
    'size',
    ['XS', 'S', 'M', 'L', 'XL'],
    []
)

setting['color'] = st.sidebar.multiselect(
    'color',
    ['black', 'purple', 'mint', 'beige', 'green', 'azuki', 'orange', 'blue'],
    []
)

setting['style'] = st.sidebar.multiselect(
    'style',
    ['standard', 'slim', 'full'],
)

setting['accumulate'] = st.sidebar.checkbox('accumulate', value=False)
#setting['average'] = st.sidebar.checkbox('average', value=False)
setting['total'] = st.sidebar.checkbox('total', value=False)

if st.sidebar.button('reset sku'):
    setting['size'] = []
    setting['color'] = []
    setting['style'] = []


setting['start_date'] = col1.date_input('from', value=min_date, min_value=min_date, max_value=today)
setting['end_date'] = col2.date_input('to', value=today, min_value=min_date, max_value=today)
setting['period'] = col3.selectbox(
    'range',
    ('day', 'week', 'month', 'quarter', 'year'),
)

if st.button('reset date'):
    setting['start_date'] = ''
    setting['end_date'] = ''


df = processed.getData(setting)
st.line_chart(df)