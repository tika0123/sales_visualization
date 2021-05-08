import streamlit as st
import pandas as pd
import utils
import datetime
import constants



@st.cache
def read_files():
    #
    estimation_df = pd.read_csv('./prediction_data/sales_estimation.csv', index_col='Lineitem sku')

    # convert order_df column name to date format
    order_df = pd.read_csv('./prediction_data/order_data.csv', index_col='Lineitem sku')
    order_df.columns = \
        [datetime.datetime.strptime(x, "%Y/%m/%d").date() if x[:2] == "20" else x for x in
                        order_df.columns]

    # convert to dictionary of {orderdate: units per sky}
    order_dict = {}
    for col in order_df:
        if type(col) == datetime.date:
            order_dict[col] = order_df[col]

    stock_df = pd.read_csv('./prediction_data/stock_data.csv')


    return estimation_df, order_dict, stock_df

estimation_df, order_dict, stock_df = read_files()



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

case = st.selectbox('select case',constants.SCENARIO_LIST , 1)


for dt in order_dict.keys():
    order_df = order_dict[dt]

    full_matrix = utils.getOrderMatrix('full', order_df, dt)
    standard_matirx = utils.getOrderMatrix('standard', order_df, dt)
    slim_matrix = utils.getOrderMatrix('slim', order_df, dt)

    col1, col2, col3 = st.beta_columns(3)

    with st.beta_container():
        st.header(dt)
        col1.dataframe(full_matrix)
        col2.dataframe(standard_matirx)
        col3.dataframe(slim_matrix)

#
# with st.form("my_form"):
#     st.write('June')
#     st.write("Inside the form")
#     checkbox_val = st.checkbox("Form checkbox")
#
#     submitted = st.form_submit_button("Submit")
#     if submitted:
#     st.write("slider", slider_val, "checkbox", checkbox_val)
#
