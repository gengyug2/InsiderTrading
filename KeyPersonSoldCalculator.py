from Form4Crawler import *
from tkinter import *
import os


def verify():
    t = str(ticker.get()).upper()
    try:
        company_name = sp500[sp500.ticker == t].name.get_values()[0]
        company_cik = str(sp500[sp500.ticker == t].cik.get_values()[0])
        verification.config(text=company_name + ', SEC CIK: ' + company_cik, fg='black')
        analyze.config(text='Analyze', fg='black', command=analysis)
    except:
        verification.config(text='Invalid ticker. Please try again.', fg='red')
        analyze.config(text='Please input ticker before analyzing.')


def analysis():
    t = str(ticker.get()).upper()
    result = calc(proc(t), get_kp(t))
    company_name = sp500[sp500.ticker == t].name.get_values()[0]
    text1 = 'Please find the insider trading records of ' + company_name + ' for most recent year at f4_' + t + '.csv'
    text2 = 'Please find the key persons list of ' + company_name + ' at kperson_' + t + '.csv'
    text3 = 'Out of total insider buys, key person percentage is about ' + result[0]
    text4 = 'Out of total insider sells, key person percentage is about ' + result[1]
    result_line_1.config(text=text1)
    result_line_2.config(text=text2)
    result_line_3.config(text=text3)
    result_line_4.config(text=text4)
    analyze.config(text='Please input ticker before analyzing.', command=NONE)


def delete_files():
    file_list = os.listdir()
    for file in file_list:
        if '.csv' in file:
            os.remove(file)
    delete_result.config(text='All downloaded .CSV files deleted')


root = Tk()
root.wm_title('SP500 Company Key Person Actions Analysis')
sp500 = splist()
Label(root, text='Please input the ticker of target company from SP500 '
                 'and verify it.').grid(row=0, column=0, columnspan=3)
Label(root, text='E.g. AAPL, FB, GOOG, MSFT. Then Click "Analyze" button').grid(columnspan=3)
Label(root, text='by Johnny MOON, GIES COB @UIUC').grid(columnspan=3)
Label(root, text='Ticker').grid(column=0, sticky=W)
ticker = Entry(root)
ticker.grid(row=3, column=1, sticky=W)
Button(root, text='Verify', command=verify).grid(row=3, column=2)
verification = Label(root, text='')
verification.grid(columnspan=3)
analyze = Button(root, text='Please input ticker before analyzing.')
analyze.grid(columnspan=3)
Label(root, text='Summary:').grid(column=0, sticky=W)
result_line_1 = Label(root, text=' ')
result_line_2 = Label(root, text=' ')
result_line_3 = Label(root, text=' ')
result_line_4 = Label(root, text=' ')
result_line_1.grid(columnspan=3, sticky=W)
result_line_2.grid(columnspan=3, sticky=W)
result_line_3.grid(columnspan=3, sticky=W)
result_line_4.grid(columnspan=3, sticky=W)
Button(root, text='Delete Downloaded Files', command=delete_files).grid(column=1)
delete_result = Label(root, text=' ')
delete_result.grid(columnspan=3)
root.mainloop()
