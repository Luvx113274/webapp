import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

import matplotlib.pyplot as plt

from datetime import datetime

ticker = st.sidebar.text_input('Ticker')

if not ticker:
    st.title('WELCOME TO OUR WEBSITE')

else:
    st.title(ticker)
    mck = yf.Ticker(ticker)
    bsheet = mck.balance_sheet
    income = mck.income_stmt
    cfs = mck.cashflow
    years = bsheet.columns[-5:]  # 4 cột cho 4 năm và 1 cột cho TTM

    quarter_bsheet = mck.quarterly_balance_sheet
    first_column_index = quarter_bsheet.columns[0]
    TTM_bsheet = quarter_bsheet[first_column_index]
    second_column_index = quarter_bsheet.columns[1]
    TTM_bsheet2 = quarter_bsheet[second_column_index]

    quarter_income = mck.quarterly_income_stmt
    TTM = quarter_income.iloc[:, :4].sum(axis=1)

    quarter_cfs = mck.quarterly_cashflow
    TTM_cfs = quarter_cfs.iloc[:, :4].sum(axis=1)

    data = [
        ('Time', *[year.date().strftime("%Y-%m-%d") for year in years[::-1]], 'TTM'),
        ('Revenue', *[income[year]['Total Revenue'] for year in years[::-1]], TTM['Total Revenue']),
        ('Net Income', *[income[year]['Net Income'] for year in years[::-1]], TTM['Net Income']),
        ('Operating Cash Flow', *[cfs[year]['Operating Cash Flow'] for year in years[::-1]],
         TTM_cfs['Operating Cash Flow']),
        ('Free Cash Flow', *[cfs[year]['Free Cash Flow'] for year in years[::-1]], TTM_cfs['Free Cash Flow']),
        ('Basic EPS', *[income[year]['Basic EPS'] for year in years[::-1]], TTM['Basic EPS']),
        ('ROE',
         *[income[year]['Net Income'] / bsheet[year]['Total Equity Gross Minority Interest'] for year in years[::-1]],
         TTM['Net Income'] / TTM_bsheet.loc['Total Equity Gross Minority Interest']),
        ('Current Ratio',
         *[bsheet[year]['Current Assets'] / bsheet[year]['Current Liabilities'] for year in years[::-1]],
         TTM_bsheet.loc['Current Assets'] / TTM_bsheet.loc['Current Liabilities']),
        ('Debt to Equity Ratio',
         *[bsheet[year]['Total Debt'] / bsheet[year]['Total Equity Gross Minority Interest'] for year in years[::-1]],
         TTM_bsheet.loc['Total Debt'] / TTM_bsheet.loc['Total Equity Gross Minority Interest']),
        ('Long Term Debt',
         *[bsheet[year]['Long Term Debt'] if 'Long Term Debt' in bsheet[year] else None for year in years[::-1]],
         TTM_bsheet.loc['Long Term Debt'] if 'Long Term Debt' in TTM_bsheet else None),
        ('Short Term Debt', *[bsheet[year]['Current Debt'] if 'Current Debt' in bsheet[year] else bsheet[year][
            'Current Capital Lease Obligation'] if 'Current Capital Lease Obligation' in bsheet[year] else None for year
                              in
                              years[::-1]], TTM_bsheet['Current Debt'] if 'Current Debt' in TTM_bsheet else TTM_bsheet[
            'Current Capital Lease Obligation'] if 'Current Capital Lease Obligation' in TTM_bsheet else None),
        ('Cash, Cash Equivalents & Short Term Investments', *[bsheet[year][
                                                                  'Cash Cash Equivalents And Short Term Investments'] if 'Cash Cash Equivalents And Short Term Investments' in
                                                                                                                         bsheet[
                                                                                                                             year] else None
                                                              for year in years[::-1]], TTM_bsheet.loc[
             'Cash Cash Equivalents And Short Term Investments']),
        ('Accounts Receivable', *[bsheet[year]['Accounts Receivable'] for year in years[::-1]],
         TTM_bsheet.loc['Accounts Receivable'] if TTM_bsheet.loc['Accounts Receivable'] in TTM_bsheet else
         TTM_bsheet2.loc['Accounts Receivable'])

    ]
    df = pd.DataFrame(data[1:], columns=data[0])
    pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))

    # F-score
    # Score #1 - change in Total Revenue (Thay đổi doanh thu)
    revenue_values = [income[year]['Total Revenue'] for year in years[::-1]]
    rv_scores = [1 if revenue_values[i] < revenue_values[i + 1] else 0 for i in range(len(revenue_values) - 1)]
    annual_rv_score = sum(rv_scores)
    TTM_rv_score = 1 if TTM['Total Revenue'] > income[years[-3]]['Total Revenue'] else 0
    total_rv_score = annual_rv_score + TTM_rv_score

    # Score #2 - change in Net Income (Thay đổi lợi nhuận)
    ni_values = [income[year]['Net Income'] for year in years[::-1]]
    ni_scores = [1 if ni_values[i] < ni_values[i + 1] else 0 for i in range(len(ni_values) - 1)]
    annual_ni_score = sum(ni_scores)
    TTM_ni_score = 1 if TTM['Net Income'] > income[years[-3]]['Net Income'] else 0
    total_ni_score = annual_ni_score + TTM_ni_score

    # Score #3 - change in Operating Cash Flow (Thay đổi dòng tiền đầu tư)
    opcf_values = [cfs[year]['Operating Cash Flow'] for year in years[::-1]]
    opcf_scores = [1 if opcf_values[i] < opcf_values[i + 1] else 0 for i in range(len(opcf_values) - 1)]
    annual_opcf_score = sum(opcf_scores)
    TTM_opcf_score = 1 if TTM_cfs['Operating Cash Flow'] > cfs[years[-3]]['Operating Cash Flow'] else 0
    total_opcf_score = annual_opcf_score + TTM_opcf_score

    # Score #4 - change in Free Cash Flow
    fcf_values = [cfs[year]['Free Cash Flow'] for year in years[::-1]]
    fcf_scores = [1 if fcf_values[i] < fcf_values[i + 1] else 0 for i in range(len(fcf_values) - 1)]
    annual_fcf_score = sum(fcf_scores)
    TTM_fcf_score = 1 if TTM_cfs['Free Cash Flow'] > cfs[years[-3]]['Free Cash Flow'] else 0
    total_fcf_score = annual_fcf_score + TTM_fcf_score

    # Score #5 - change in EPS
    eps_values = [income[year]['Basic EPS'] for year in years[::-1]]
    eps_scores = [1 if eps_values[i] < eps_values[i + 1] else 0 for i in range(len(eps_values) - 1)]
    annual_eps_score = sum(eps_scores)
    TTM_eps_score = 1 if TTM['Basic EPS'] > income[years[-3]]['Basic EPS'] else 0
    total_eps_score = annual_eps_score + TTM_eps_score

    # Score #6 - change in ROE
    roe_values = [income[year]['Net Income'] / bsheet[year]['Total Equity Gross Minority Interest']
                  for year in years[::-1]]
    roe_scores = [1 if roe_values[i] < roe_values[i + 1] else 0 for i in range(len(roe_values) - 1)]
    annual_roe_score = sum(roe_scores)
    TTM_roe_score = 1 if TTM['Net Income'] / TTM_bsheet.loc['Total Equity Gross Minority Interest'] > income[years[-3]][
        'Net Income'] / bsheet[years[-3]]['Total Equity Gross Minority Interest'] else 0
    total_roe_score = annual_roe_score + 0

    # Score #7 - change in Current Ratio
    cr_values = [bsheet[year]['Current Assets'] / bsheet[year]['Current Liabilities'] for year in years[::-1]]
    cr_scores = [1 if cr_values[i] < cr_values[i + 1] else 0 for i in range(len(cr_values) - 1)]
    annual_cr_score = sum(cr_scores)
    TTM_cr_score = 1 if TTM_bsheet.loc['Current Assets'] / TTM_bsheet.loc['Current Liabilities'] > bsheet[years[-3]][
        'Current Assets'] / bsheet[years[-3]]['Current Liabilities'] else 0
    total_cr_score = annual_cr_score + TTM_cr_score

    # Score #8 - change in Debt to Equity Ratio
    der_values = [bsheet[year]['Total Debt'] / bsheet[year]['Total Equity Gross Minority Interest'] for year in
                  years[::-1]]
    der_scores = [1 if der_values[i] > der_values[i + 1] else 0 for i in range(len(der_values) - 1)]
    annual_der_score = sum(der_scores)
    TTM_der_score = 1 if TTM_bsheet.loc['Total Debt'] / TTM_bsheet.loc['Total Equity Gross Minority Interest'] < \
                         bsheet[years[-3]]['Total Debt'] / bsheet[years[-3]][
                             'Total Equity Gross Minority Interest'] else 0
    total_der_score = annual_der_score + TTM_der_score

    # Score #9 - change in Accounts Receivable
    ar_values = [bsheet[year]['Accounts Receivable'] for year in years[::-1]]
    ar_scores = [1 if ar_values[i] > ar_values[i + 1] else 0 for i in range(len(ar_values) - 1)]
    annual_ar_score = sum(ar_scores)
    TTM_ar_score = 1 if TTM_bsheet.loc['Accounts Receivable'] < bsheet[years[-3]]['Accounts Receivable'] else 0
    total_ar_score = annual_ar_score + TTM_ar_score

    # Calculate the total score
    total_score = total_rv_score + total_ni_score + total_opcf_score + total_fcf_score + total_roe_score + total_eps_score + total_cr_score + total_der_score + total_ar_score

    summary, f_score, valuation = st.tabs(
        ["Summary", "F-Score", "Valuation"])

    with (summary):
        start_date = st.date_input('Start Date')
        end_date = st.date_input('End Date')

        dataf = yf.download(ticker, start=start_date, end=end_date)

        if dataf.empty:
            st.write("<p style='color:red'><strong>Please reset the date to see the chart</strong></p>",
                     unsafe_allow_html=True)
        else:
            fig = px.line(dataf, x=dataf.index, y=dataf['Adj Close'], title=ticker)  # x is index (time)
            st.plotly_chart(fig)

        st.subheader('Pricing Data')
        dataa = dataf
        dataa['% Change'] = dataf['Adj Close'] / dataf['Adj Close'].shift(
            1) - 1  # lấy giá đóng cửa hôm nay/giá đóng cửa ngày trước đó -1
        dataa.dropna(inplace=True)  # Loại bỏ các dòng trong dataframe mà có missing values (NaN or Null)
        st.write(dataa)

        cash_flow = mck.cashflow
        quarter_income = mck.quarterly_income_stmt
        TTM_income = quarter_income.sum(axis=1)

        datav = {
            'Time': [year.date().strftime("%Y-%m-%d") for year in years[::-1]] + ['TTM'],
            'Revenue': [income.loc['Total Revenue', year] for year in years[::-1]] + [TTM['Total Revenue']],
            'Net Income': [income.loc['Net Income', year] for year in years[::-1]] + [TTM['Net Income']],
            'Free Cash Flow': [cash_flow.loc['Free Cash Flow', year] for year in years[::-1]] + [
                TTM_cfs['Free Cash Flow']],
            'Operating Cash Flow': [cash_flow.loc['Operating Cash Flow', year] for year in years[::-1]] + [
                TTM_cfs['Operating Cash Flow']],
            'ROE': [income.loc['Net Income', year] / (bsheet.loc['Total Equity Gross Minority Interest', year] or 1) for
                    year in years[::-1]] + [TTM['Net Income'] / TTM_bsheet.loc['Total Equity Gross Minority Interest']],
            'EPS': [income.loc['Net Income', year] / (mck.info['sharesOutstanding'] or 1) for year in years[::-1]] + [
                TTM['Basic EPS']],
            'Current Ratio': [bsheet.loc['Current Assets', year] / (bsheet.loc['Current Liabilities', year] or 1) for
                              year in years[::-1]] + [
                                 TTM_bsheet.loc['Current Assets'] / TTM_bsheet.loc['Current Liabilities']],
            'Debt to Equity Ratio': [bsheet.loc['Total Debt', year] / (
                        bsheet.loc['Total Equity Gross Minority Interest', year] or 1) for year in years[::-1]] + [
                                        TTM_bsheet.loc['Total Debt'] / TTM_bsheet.loc[
                                            'Total Equity Gross Minority Interest']],
        }

        dfv = pd.DataFrame(datav)
        st.subheader('Fundamental Data')
        st.write(df)

        # Plot the chart using Plotly Express
        # Revenue, Net Income, Operating Cash Flow
        # create plot
        columns_to_plot = ['Revenue', 'Net Income', 'Operating Cash Flow', 'Free Cash Flow']
        x = ['['] + dfv['Time'] + [']']
        # Vẽ biểu đồ cột ghép
        fig = px.bar(dfv, x, y=columns_to_plot, title='Financial Ratios',
                     labels={'value': 'Value', 'variable': 'Legend'},
                     height=400, width=800, barmode='group')
        fig.update_xaxes(fixedrange=True)
        fig.update_xaxes(title_text="Time")
        st.plotly_chart(fig)

        # EPS
        # Vẽ biểu đồ đường sử dụng Plotly Express
        fig = px.line(dfv, x, y='EPS', title='EPS', markers='o')
        fig.update_xaxes(fixedrange=True)
        fig.update_xaxes(title_text="Time")
        # Thay đổi màu của đường
        fig.update_traces(line=dict(color='firebrick'))
        # Hiển thị biểu đồ trong ứng dụng Streamlit
        st.plotly_chart(fig)

        # ROE
        # Vẽ biểu đồ đường sử dụng Plotly Express
        fig = px.line(dfv, x, y='ROE', title='ROE', markers='o')
        fig.update_xaxes(fixedrange=True)
        fig.update_xaxes(title_text="Time")
        # Thay đổi màu của đường
        fig.update_traces(line=dict(color='mediumspringgreen'))
        # Hiển thị biểu đồ trong ứng dụng Streamlit
        st.plotly_chart(fig)

        # Debt to Equity Ratio
        # Vẽ biểu đồ đường sử dụng Plotly Express
        fig = px.line(dfv, x, y='Debt to Equity Ratio', title='Debt to Equity Ratio', markers='o')
        fig.update_xaxes(fixedrange=True)
        fig.update_xaxes(title_text="Time")
        # Thay đổi màu của đường
        fig.update_traces(line=dict(color='dodgerblue'))
        # Hiển thị biểu đồ trong ứng dụng Streamlit
        st.plotly_chart(fig)

        # Current Ratio
        # Vẽ biểu đồ đường sử dụng Plotly Express
        fig = px.line(dfv, x, y='Current Ratio', title='Current Ratio', markers='o')
        fig.update_xaxes(fixedrange=True)
        # Thay đổi các chú thích trên trục x
        fig.update_xaxes(title_text="Time")
        # Thay đổi màu của đường
        fig.update_traces(line=dict(color='rosybrown'))
        # Hiển thị biểu đồ trong ứng dụng Streamlit
        st.plotly_chart(fig)

    with f_score:
        st.subheader('F-Score')
        data00 = [
            ('Time', *[year.date().strftime("%Y-%m-%d") for year in years[::-1]], 'TTM', 'Total'),
            ('Revenue', '-', *[rv_scores[i] for i in range(len(rv_scores))], str(TTM_rv_score),
             str(total_rv_score) + ' / ' + str(len(rv_scores) + 1)),
            ('Net Income', '-', *[ni_scores[i] for i in range(len(ni_scores))], str(TTM_ni_score),
             str(total_ni_score) + ' / ' + str(len(ni_scores) + 1)),
            ('Operating Cash Flow', '-', *[opcf_scores[i] for i in range(len(opcf_scores))], str(TTM_opcf_score),
             str(total_opcf_score) + ' / ' + str(len(opcf_scores) + 1)),
            ('Free Cash Flow', '-', *[fcf_scores[i] for i in range(len(fcf_scores))], str(TTM_fcf_score),
             str(total_fcf_score) + ' / ' + str(len(fcf_scores) + 1)),
            ('EPS', '-', *[eps_scores[i] for i in range(len(eps_scores))], str(TTM_eps_score),
             str(total_eps_score) + ' / ' + str(len(eps_scores) + 1)),
            ('ROE', '-', *[roe_scores[i] for i in range(len(roe_scores))], str(TTM_roe_score),
             str(total_roe_score) + ' / ' + str(len(roe_scores) + 1)),
            ('Current Ratio', '-', *[cr_scores[i] for i in range(len(cr_scores))], str(TTM_cr_score),
             str(total_cr_score) + ' / ' + str(len(cr_scores) + 1)),
            ('Debt to Equity Ratio', '-', *[der_scores[i] for i in range(len(der_scores))], str(TTM_der_score),
             str(total_der_score) + ' / ' + str(len(der_scores) + 1)),
            ('Accounts Receivable', '-', *[ar_scores[i] for i in range(len(ar_scores))], str(TTM_ar_score),
             str(total_ar_score) + ' / ' + str(len(ar_scores) + 1)),
        ]

        df00 = pd.DataFrame(data00[1:], columns=data00[0])
        pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))
        st.write(df00)

        st.subheader('Total F-Score = ' + str(total_score) + ' / ' + str((len(rv_scores) + 1) * 9))

        percentage = (total_score / ((len(rv_scores) + 1) * 9)) * 100
        st.subheader('Percentage = {:.2f} %'.format(percentage))

    with valuation:

        # Current year
        current_year = datetime.now().year
        st.subheader("Current Year")
        number0 = st.number_input("Current Year:", value=current_year, placeholder="Type a number...")
        st.write(f"Current Year: {current_year}")
        # beta
        beta_value = mck.info['beta']
        st.subheader("Company Beta")
        number1 = st.number_input("Company Beta:", value=beta_value, placeholder="Type a number...")
        st.write(f"Company Beta: {beta_value:,.2f}")

        # fcf
        display_options = ["Free Cash Flow", "Net Income", "Operating Cash Flow"]
        selected_display_option = st.radio("Select display option:", display_options)

        if selected_display_option == "Free Cash Flow":
            free_cash_flow = TTM_cfs['Free Cash Flow']
            number2 = st.number_input("Free Cash Flow (current):", value=free_cash_flow, placeholder="Type a number...")
            st.write(f"Free Cash Flow: {free_cash_flow:,.2f}")


        elif selected_display_option == "Net Income":
            net_income = TTM['Net Income']
            number3 = st.number_input("Net Income:", value=net_income, placeholder="Type a number...")
            st.write(f"Net Income: {net_income:,.2f}")

        elif selected_display_option == "Operating Cash Flow":
            operating_cash_flow = TTM_cfs['Operating Cash Flow']
            number4 = st.number_input("Operating Cash Flow:", value=operating_cash_flow, placeholder="Type a number...")
            st.write(f"Operating Cash Flow: {operating_cash_flow:,.2f}")


        # debt
        ttm_cr = TTM_bsheet['Current Debt'] if 'Current Debt' in TTM_bsheet else TTM_bsheet[
            'Current Capital Lease Obligation'] if 'Current Capital Lease Obligation' in TTM_bsheet else 0
        st.subheader("Current Debt")
        number5 = st.number_input("Current Debt:", value=ttm_cr, placeholder="Type a number...")
        st.write(f"Current Debt: {ttm_cr:.2f}")

        # cash
        cash = TTM_bsheet.loc['Cash Cash Equivalents And Short Term Investments']
        st.subheader("Cash and Short Term Investments:")
        number6 = st.number_input("Cash and Short Term Investments:", value=cash, placeholder="Type a number...")
        st.write(f"Cash and Short Term Investments: {cash:,.2f}")

        # shares
        shares_outstanding = mck.info['sharesOutstanding']
        st.subheader("Shares Outstanding:")
        number7 = st.number_input("Shares Outstanding:", value=shares_outstanding, placeholder="Type a number...")
        st.write(f"Shares Outstanding: {shares_outstanding:,.2f}")


        # Tính toán discount rate dựa trên giá trị beta

        def calculate_discount_rate(beta):
            if number1 < 1.00:
                return 0.05
            elif 1.00 <= number1 < 1.1:
                return 0.06
            elif 1.1 <= number1 < 1.2:
                return 0.065
            elif 1.2 <= number1 < 1.3:
                return 0.07
            elif 1.3 <= number1 < 1.4:
                return 0.075
            elif 1.4 <= number1 < 1.5:
                return 0.08
            elif 1.5 <= number1 < 1.6:
                return 0.085
            elif number1 >= 1.6:
                return 0.09


        # Tính toán discount rate tương ứng
        discount_rate_value = calculate_discount_rate(beta_value)

        # Nhập growth rate
        st.subheader("Growth Rate")
        growth_rate1 = st.number_input('Growth rate Y1-5')
        growth_rate2 = st.number_input('Growth rate Y6-10')
        growth_rate3 = st.number_input('Growth rate Y11-20')
        # Hiển thị discount rate trên Streamlit
        st.subheader(" Discount Rate")
        number8 = st.number_input('Discount Rate: ', value=discount_rate_value, placeholder="Type a number...")
        st.write(f"Discount Rate: {discount_rate_value:,.3f}")
    # Creating the first table
        data1 = {
        'Operating Cash Flow': [number4],
        'Growth rate (Y 1-5)': growth_rate1,
        'Growth rate (Y 6-10)': growth_rate2,
        'Growth rate (Y 11-20)': growth_rate3,
        'Discount rate': number8,
        'Current year': number0
        }

        table1 = pd.DataFrame(data=data1)

        # Creating the second table with calculations based on the first table
        years = [
            ((table1['Current year'][0]) + i)
            for i in range(21)
        ]
        cash_flows = [
            (table1['Operating Cash Flow'][0] * ((1 + table1['Growth rate (Y 1-5)'][0]) ** i)) if i <= 5
            else ((table1['Operating Cash Flow'][0] * ((1 + table1['Growth rate (Y 1-5)'][0]) ** 5)) * (
                    (1 + table1['Growth rate (Y 6-10)'][0]) ** (i - 5))) if 6 <= i <= 10
            else ((table1['Operating Cash Flow'][0] * ((1 + table1['Growth rate (Y 1-5)'][0]) ** 5)) * (
                    (1 + table1['Growth rate (Y 6-10)'][0]) ** 5) * (
                              (1 + table1['Growth rate (Y 11-20)'][0]) ** (i - 10)))
            for i in range(21)
        ]

        discount_factors = [(1 / ((1 + table1['Discount rate'][0]) ** i)) for i in range(21)]
        discounted_values = [cf * df for cf, df in zip(cash_flows, discount_factors)]

        data2 = {
            'Year': years[1:],
            'Cash Flow': cash_flows[1:],
            'Discount Factor': discount_factors[1:],
            'Discounted Value': discounted_values[1:]
        }

        table2 = pd.DataFrame(data=data2)
        pd.set_option('display.float_format', lambda x: '{:,.2f}'.format(x))
        table2['Year'] = table2['Year'].astype(str).str.replace(',', '')
        st.subheader('Discounted Cash Flow')
        st.write(table2)

        # Chart
        cash_flow = table2['Cash Flow']
        discounted_value = table2['Discounted Value']
        years = table2['Year']
        columns_to_plot = ['Cash Flow', 'Discounted Value']
        fig = px.line(table2, x=years, y=columns_to_plot,
                      title='Intrinsic Value Calculator (Discounted Cash Flow Method 10 years)',
                      labels={'value': 'Value', 'variable': 'Legend'},
                      height=500, width=800, markers='o')
        fig.update_xaxes(fixedrange=True)

        # Thay đổi các chú thích trên trục x
        fig.update_xaxes(
            tickvals=years[0:]
        )
        fig.update_xaxes(title_text="Time")
        st.plotly_chart(fig)

        # Tính Intrinsic Value
        total_discounted_value = sum(discounted_values)
        st.write(f"PV of 20 yr Cash Flows: {total_discounted_value:.2f}")

        intrinsic_value = sum(discounted_values) / number5
        st.write(f"Intrinsic Value before cash/debt: {intrinsic_value:.2f}")

        debt_per_share = number5 / number7
        st.write(f"Debt per Share: {debt_per_share:.2f}")

        cash_per_share = number6 / number7
        st.write(f"Cash per Share: {cash_per_share:.2f}")

        final_intrinsic_value = intrinsic_value - debt_per_share + cash_per_share
        st.subheader(f"Final Intrinsic Value per Share: {final_intrinsic_value:.2f}")









