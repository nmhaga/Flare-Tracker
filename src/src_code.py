#This is where the source code is written.

import urllib2
from BeautifulSoup import BeautifulSoup

def get_solarsoft_data():
    response = urllib2.urlopen('http://www.lmsal.com/solarsoft/last_events/')
    html_content = response.read()
    
    return read_solarsoft_data(html_content)


def read_solarsoft_data(html_content):
    soup = BeautifulSoup(html_content)
    table = soup.findAll('table')[2]

    resultset = []
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) < 7:
            continue
        Event = col[0].string
        Datetime = col[2].string
        Peak = col[4].string
        GOES_class = col[5].string
        if col[6].find('a') is not None:
            Derived_position = col[6].find('a').string
            Region = col[6].find('font').contents[1]
        else: #if there is no link, we assume it's an unnamed region & just derived position is available. 
            Derived_position = col[6].string
            Region = ""

        newR = Region.replace("(", "").replace(")", "").strip() #get the number from inside the brackets!

        result = (Event, Datetime, Peak, GOES_class, Derived_position, newR)
        resultset.append(result)  
    return resultset
        
resset = get_solarsoft_data()
print resset

