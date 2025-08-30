from bs4 import BeautifulSoup, Tag
from dataclasses import asdict, dataclass
import datetime
import pandas as pd
import re
import requests
from requests.cookies import RequestsCookieJar
import time

# Constants
URL = 'https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion'
HANDSHAKE_GET = {'querySentence': '台灣電力', 'tenderStatusType': '招標', 'tenderStatusType': '決標', 'sortCol': 'TENDER_NOTICE_DATE', 'timeRange': '88', 'pageSize': '100'}
HEADER = {'Accept': 'text/html;charset=UTF-8',
          'Accept-Encoding': 'gzip, deflate, br, zstd',
          'Accept-Language': 'en-US',
          'Cache-Control': 'no-cache',
          'Origin': 'https://web.pcc.gov.tw',
          'Pragma': 'no-cache',
          'Referer': 'https://web.pcc.gov.tw/prkms/tender/common/bulletion/readBulletion',
          'Sec-Ch-Ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
          'Sec-Ch-Ua-Mobile': '?0',
          'Sec-Ch-Ua-Platform': '"Windows"',
          'Sec-Fetch-Dest': 'document',
          'Sec-Fetch-Mode': 'navigate',
          'Sec-Fetch-Site': 'same-origin',
          'Sec-Fetch-User': '?1',
          'Upgrade-Insecure-Requests': '1',
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'}
SPACING = 2

@dataclass
class PageParam:
    title: str | None
    count: int
    cookies: RequestsCookieJar

    def get_page_url(self, q: str, year: int, page: int) -> str:
        assert (page >= 1) & (page <= self.count)
        return f'{URL}?sortCol=TENDER_NOTICE_DATE&querySentence={q}&{self.title}={page}&pageSize=100&tenderStatusType=招標&tenderStatusType=決標&timeRange={year}'

@dataclass
class Record:
    title: str | None = None
    authority: str | None = None
    date: datetime.datetime | None = None
    url: str | None = None

    def __repr__(self):
        return f'({self.title}, {self.authority}, {self.date}, {self.url})'

def get_page_param(s: requests.Session, q: str, year: int) -> PageParam:
    url = f'{URL}?querySentence={q}&tenderStatusType=招標&tenderStatusType=決標&sortCol=TENDER_NOTICE_DATE&timeRange={year}&pageSize=100'
    raw = s.post(url, headers=HEADER)
    bs = BeautifulSoup(raw.text, 'html.parser')

    page_links = bs.select_one('#pagelinks')
    assert isinstance(page_links, Tag)
    
    last_page_link = page_links.select_one('a:nth-child(2)')
    if isinstance(last_page_link, Tag):
        assert 'href' in last_page_link.attrs
        filtered = re.sub(r'(?:\&|\?)(?:querySentence\=.+?(?=\&|$)|tenderStatusType\=.+?(?=\&|$)|sortCol\=TENDER_NOTICE_DATE|pageSize\=\d+?(?=\&|$)|timeRange\=\d+?(?=\&|$))', '',  str(last_page_link.attrs['href']))
        match = re.search(r'(?<=(?:\?|\&))(.+?)\=(\d+)', filtered)
        if (match is None):
            return PageParam(None, 1, s.cookies)
        else:
            assert len(match.groups()) == 2
            return PageParam(match.group(1), int(match.group(2)), s.cookies)
    else:
        return PageParam(None, 1, s.cookies)

def get_records(s: requests.Session, q: str, **kwargs) -> list[Record]:
    log_level: str = 'info'
    minguo: bool = True
    sp: float = SPACING
    time_start: int = 88 # CE 1999
    time_end: int = datetime.datetime.now().year - 1911 # CE 20xx

    if 'level' in kwargs.keys():
        level = kwargs.get('level')
        if (level is None):
            pass
        elif (isinstance(level, str)):
            if level in ['none', 'info', 'verbose']:
                log_level = level

    if 'minguo' in kwargs.keys():
        minguo_input = kwargs.get('minguo')
        if (minguo_input is None):
            pass
        elif (isinstance(minguo_input, bool)):
            minguo = minguo_input

    if 'range' in kwargs.keys():
        time_range = kwargs.get('range')
        if (time_range is None):
            pass
        elif (not isinstance(time_range, tuple)):
            pass
        elif (not len(time_range) == 2):
            pass
        else:
            if isinstance(time_range[0], int):
                time_start = time_range[0]
                if (not minguo):
                    time_start -= 1911
            if isinstance(time_range[1], int):
                time_end = time_range[1]
                if (not minguo):
                    time_end -= 1911

    if 'spacing' in kwargs.keys():
        spacing = kwargs.get('spacing')
        if (spacing is None):
            pass
        elif (isinstance(spacing, float) | isinstance(spacing, int)):
            sp = float(spacing)
    
    if (log_level == 'verbose'):
        print(f'Input params:\n\tlevel = \'{log_level}\'\n\tminguo = {minguo}\n\trange = ({time_start}, {time_end})\n\tspacing = {sp}')

    failed = False
    years = range(time_start, time_end + 1)
    records = list()

    for year in years:
        param = get_page_param(s, q, year)
        if (log_level != 'none'):
            print(f'Year: {year + 1911}, Page Count: {param.count}')
        time.sleep(sp)

        for page in range(1, param.count + 1):
            sub_raw = s.post(param.get_page_url(q, year, page), headers=HEADER)
            sub_bs = BeautifulSoup(sub_raw.text, 'html.parser')
            try:
                if (log_level == 'verbose'):
                    print(f'Searching at: Y{year + 1911} | P{page}')
                get_records_from_bulletin(sub_bs, records)
            except:
                if (log_level != 'none'):
                    print(f'Failed at: Y{year + 1911} | P{page}')
                break
            time.sleep(sp)
        
        if (failed):
            break

    return records

def get_records_as_dataframe(q: str, **kwargs) -> pd.DataFrame:
    '''
    Retrieve the tender records as a pandas dataframe.

    Parameter
    -------
    q: str
        The query string.
    minguo: bool, default True
        Whether to treat the number in `range` as a minguo year.
    range: tuple[int, int], default tuple[88, current year]
        The time period to search from.
    spcaing: float, default 2
        The request interval in seconds.
    '''
    # Make sure the public tender website is accessible.
    s = requests.Session()
    handshake(s)

    # Get tender records.
    records = get_records(s, q, **kwargs)
    return pd.DataFrame([asdict(r) for r in records])

def get_records_from_bulletin(bs: BeautifulSoup, records: list[Record]) -> None:
    bulletin = bs.select_one('#bulletion > tbody')
    assert isinstance(bulletin, Tag)

    for row in bulletin.children:
        if not isinstance(row, Tag):
            continue
        
        no_match_cell = row.select_one('td[colspan]')
        if isinstance(no_match_cell, Tag):
            return

        record = Record()
        category = row.select_one(':nth-child(2)')
        assert isinstance(category, Tag)
        is_award = '決標公告' in category.get_text(strip=True)

        auth = row.select_one(':nth-child(3)')
        assert isinstance(auth, Tag)
        record.authority = auth.get_text(strip=True)

        title = row.select_one(':nth-child(4) > a > span > script')
        assert isinstance(title, Tag)
        title_text = title.get_text(strip=True)        
        text_match = re.search(r'(?<=pageCode2Img\(\").+?(?=\")', title_text)
        if (text_match is None):
            record.title = ''
        else:
            record.title = text_match[0]

        url = row.select_one(':nth-child(4) > a')
        assert isinstance(url, Tag)
        attrs = url.attrs
        if ('href' in attrs):
            record.url = f'https://web.pcc.gov.tw{attrs["href"]}'
        else:
            record.url = ''
        
        date_texts: list[str] = list()
        if (is_award):
            date = row.select_one(':nth-child(6)')
            assert isinstance(date, Tag)
            date_text = date.find(text=True, recursive=False)
            assert isinstance(date_text, str)
            date_texts = date_text.split('/')
        else:
            date = row.select_one(':nth-child(5)')
            assert isinstance(date, Tag)
            date_texts = date.get_text(strip=True).split('/')
        if (len(date_texts) == 3):
            date_components = [int(x) for x in date_texts]
            date_components[0] += 1911
            record.date = datetime.datetime(date_components[0], date_components[1], date_components[2])
        else:
            record.date = None

        records.append(record)

# Handshake
def handshake(s: requests.Session) -> None:
    raw = s.get(URL, params=HANDSHAKE_GET, headers=HEADER)
    bs = BeautifulSoup(raw.text, 'html.parser')

    # Test 1: Does the target website exist?
    assert isinstance(bs.title, Tag)
    assert '政府電子採購網' in bs.title.text

    # Test 2: Does the search success?
    assert is_search_success(bs)
    
    del raw, bs

def is_search_success(bs: BeautifulSoup, verbose: bool = True) -> bool:
    tag = bs.find(id = 'checkSearchFailure')

    if (not isinstance(tag, Tag)):
        if (verbose):
            print('Failed test 2-1: there\'s no tag with the id `checkSearchFailure`.')
        return False
    
    if (tag.name != 'div'):
        if (verbose):
            print('Failed test 2-2: the tag `checkSearchFailure` is not a div element.')
        return False
    
    attrs = tag.attrs
    if ('style' not in attrs):
        if (verbose):
            print('Failed test 2-3: the tag has no style attribute.')
        return False
    
    styles = attrs['style']
    if (not isinstance(styles, str)):
        if (verbose):
            print('Failed test 2-4: the style attribute is invalid.')
        return False
    
    styles = styles.strip()
    if ('display:none;' not in styles):
        if (verbose):
            print('Failed test 2-5: the failure message presents.')
        return False
    
    bulletin = bs.find(id = 'bulletion') # Original typo as is.

    if (not isinstance(bulletin, Tag)):
        print('Failed test 2-6: there\'s no tag with the id `bulletion`.')
        return False
    
    if (bulletin.name != 'table'):
        print('Failed test 2-7: the tag `bulletion` is not a table element.')
        return False
    
    return True