import pandas as pd
import datetime as dt
import requests


# get html from a given url
def get_page(url):
    return requests.get(url).content.decode('utf-8')


# request key persons details from REUTERS
def get_kp(ticker):
    page_tabs = pd.read_html('https://www.reuters.com/finance/stocks/company-officers/' + ticker, skiprows=1)
    kp = page_tabs[0]
    kp['Biography'] = page_tabs[1][1]
    kp.columns = ['name', 'age', 'since', 'current_position', 'biography']
    kp.to_csv('./kperson_' + ticker + '.csv')
    return kp


# request sp500 ticker/name/cik
def splist():
    sp500 = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", skiprows=1)[0][[0, 1, 7]]
    sp500.columns = ['ticker', 'name', 'cik']
    return sp500


# request form4 data
def get_f4(cik, start, end):
    page = get_page('https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + cik +
                    '&type=4&dateb=' + end.strftime('%Y%m%d') + '&owner=only&count=100')
    page = page[page.find('nowrap="nowrap"><a href="') + 1:]
    form_list = []
    filing_date = []
    d = end
    count = 0
    while d > start:
        ahref = get_page("https://www.sec.gov" + page[page.find('a href="') + 8: page.find('"', 35)])
        ahref = ahref[ahref.find('.xml') + 1:]
        ahref = "https://www.sec.gov" + ahref[ahref.find('a href="') + 8: ahref.find('.xml')] + '.xml'
        form_list.append(ahref)
        for _ in range(2):
            page = page[page.find('</td>') + 1:]
        try:
            d = dt.datetime.strptime(page[page.find('<td>') + 4: page.find('</td>')], '%Y-%m-%d')
        except:
            break  # if not a date, stop here and get the list.
        filing_date.append(d)
        if d <= start:
            form_list.pop()
            filing_date.pop()
        page = page[page.find('</tr>') + 1:]
        if len(form_list) % 100 == 0:
            count += 1
            page = get_page('https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=' + cik
                            + '&type=4&dateb=' + end.strftime('%Y%m%d') + '&owner=only&count=100&start='
                            + str(count * 100))
        page = page[page.find('nowrap="nowrap"><a href="') + 1:]
    return form_list, filing_date


# extract useful info from form 4
def extract_f4(form, filing_date):
    page = get_page(form)
    # report owner's name
    page = page[page.find('<rptOwnerName>'):]
    name = page[page.find('<rptOwnerName>') + 14: page.find('</rptOwnerName')].split()
    name = [x.capitalize() for x in name]
    temp = ''
    for part in name:
        temp += part + ' '
    name = temp[:-1]
    # report owner's relationship to company
    title_set = ['Director/', 'Officer/', '10% Owner/', 'Other/']
    relation = ''
    rs_script = page[page.find('<reportingOwnerRelationship>'): page.find('</reportingOwnerRelationship>')]
    if '<isDirector>1<' in rs_script or '<isDirector>true<' in rs_script \
            or '<isDirector>True<' in rs_script or '<isDirector>TRUE<' in rs_script:
        relation += title_set[0]
    if '<isOfficer>1<' in rs_script or '<isOfficer>true<' in rs_script \
            or '<isOfficer>True<' in rs_script or '<isOfficer>TRUE<' in rs_script:
        relation += title_set[1]
    if '<isTenPercentOwner>1<' in rs_script or '<isTenPercentOwner>true<' in rs_script \
            or '<isTenPercentOwner>True<' in rs_script or '<isTenPercentOwner>TRUE<' in rs_script:
        relation += title_set[2]
    if '<isOther>1<' in rs_script or '<isOther>true<' in rs_script \
            or '<isOther>True<' in rs_script or '<isOther>TRUE<' in rs_script:
        relation += title_set[3]
    relation = relation[:-1]
    page = page[page.find('<nonDerivativeTable'):]
    form_data = pd.DataFrame()
    while '<nonDerivativeTransaction>' in page:
        page = page[page.find('<transactionDate>'):]
        page = page[page.find('<value>'):]
        trans_date = dt.datetime.strptime(page[7:17], '%Y-%m-%d')
        page = page[page.find('<transactionShares>'):]
        page = page[page.find('<value>'):]
        amount = float(page[7:page.find('</value>')])
        page = page[page.find('<transactionAcquiredDisposedCode>'):]
        page = page[page.find('<value>'):]
        aord = page[7]
        form_data = form_data.append(pd.DataFrame([[filing_date, name, relation, trans_date, aord, amount]],
                                                  columns=['filing_date', 'name', 'relationship',
                                                           'trans_date', 'a_or_d', 'amount']), ignore_index=True)
    return form_data


def proc(ticker):
    sp500 = splist()
    cik = sp500[sp500.ticker == ticker].cik.get_values()[0]
    end = dt.datetime.today()
    start = end - dt.timedelta(days=365)
    form_list, filing_date = get_f4(cik, start, end)
    form_data = pd.DataFrame()
    for (i, j) in zip(form_list, filing_date):
        form_data = form_data.append(extract_f4(i, j))

