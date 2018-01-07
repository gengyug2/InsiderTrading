import pandas as pd
import datetime as dt
import requests
import numpy as np


# get html from a given url
def get_page(url):
    return requests.get(url).content.decode('utf-8')


# request key persons details from REUTERS
def get_kp(ticker):
    page_tabs = pd.read_html('https://www.reuters.com/finance/stocks/company-officers/' + ticker, skiprows=1)
    kp = page_tabs[0]
    kp['Biography'] = page_tabs[1][1]
    kp.columns = ['name', 'age', 'since', 'current_position', 'biography']
    kp_list = kp.name.tolist()
    kp.name = [x.replace(u'\xa0', u' ') for x in kp_list]
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
    relation = ''
    rs_script = page[page.find('<reportingOwnerRelationship>'): page.find('</reportingOwnerRelationship>')]
    # one owner might have multiple relationships
    if '<isDirector>1<' in rs_script or '<isDirector>true<' in rs_script \
            or '<isDirector>True<' in rs_script or '<isDirector>TRUE<' in rs_script:
        relation += 'Director/'
    if '<isOfficer>1<' in rs_script or '<isOfficer>true<' in rs_script \
            or '<isOfficer>True<' in rs_script or '<isOfficer>TRUE<' in rs_script:
        relation += 'Officer/'
    if '<isTenPercentOwner>1<' in rs_script or '<isTenPercentOwner>true<' in rs_script \
            or '<isTenPercentOwner>True<' in rs_script or '<isTenPercentOwner>TRUE<' in rs_script:
        relation += '10% Owner/'
    if '<isOther>1<' in rs_script or '<isOther>true<' in rs_script \
            or '<isOther>True<' in rs_script or '<isOther>TRUE<' in rs_script:
        relation += 'Other/'
    relation = relation[:-1]
    # report transaction records
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


# crawl the data and save csv
def proc(ticker):
    sp500 = splist()
    cik = str(sp500[sp500.ticker == ticker.upper()].cik.get_values()[0])
    end = dt.datetime.today()
    start = end - dt.timedelta(days=365)
    form_list, filing_date = get_f4(cik, start, end)
    form_data = pd.DataFrame()
    for (i, j) in zip(form_list, filing_date):
        form_data = form_data.append(extract_f4(i, j), ignore_index=True)
    form_data.to_csv('./f4_' + ticker + '.csv')
    return form_data


# calculate key person action percentage
def calc(form_data, kp):
    key_person_list = kp.name.tolist()
    trans_person_list = form_data.name.tolist()
    if_key_person = [if_kp(name, key_person_list) for name in trans_person_list]
    form_data['if_key_person'] = if_key_person
    all_acq = form_data[form_data.a_or_d == 'A']
    kp_acq = all_acq[all_acq.if_key_person]
    try:
        kp_acq_rate = str(np.round(kp_acq.amount.sum() / all_acq.amount.sum() * 100, 2)) + '%'
    except:
        kp_acq_rate = 'N/A'
    all_disp = form_data[form_data.a_or_d == 'D']
    kp_disp = all_disp[all_disp.if_key_person]
    try:
        kp_disp_rate = str(np.round(kp_disp.amount.sum() / all_disp.amount.sum() * 100, 2)) + '%'
    except:
        kp_disp_rate = 'N/A'
    return [kp_acq_rate, kp_disp_rate]


# recognize key person
def if_kp(trans_person, key_person_list):
    trans_person_parts = trans_person.split()
    ifk = False
    for key_person in key_person_list:
        match_part = 0
        logic_one = 0
        for part in trans_person_parts:
            if part in key_person:
                match_part += 1
        # Logic 1: if more than two parts of names match, it is a key person.
        if match_part >= 2:
            ifk = True
            logic_one = 1
        # Logic 2: if the FAMILY NAME matches and Initial for the FIRST NAME matches, it is a key person.
        if match_part == 1 and trans_person_parts[0] in key_person:
            if trans_person_parts[1][0] == key_person[0]:
                ifk = True
                match_part += 1
        # Logic 3: if there is Von-names, there should be THREE parts match.
        # von-names (not Von-names) could be included in first two logics.
        if 'Van ' in key_person or 'Von ' in key_person:
            if logic_one and ifk:
                ifk = match_part >= 3
        # If it is a key person, break.
        if ifk:
            break
        # Logic system works but still has defects.
        # SHOULD enrich the system in the future.
    return ifk
