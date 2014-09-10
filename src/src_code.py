#This is where the source code is written.

import datetime
from BeautifulSoup import BeautifulSoup
from urllib2 import Request, urlopen, URLError, HTTPError
from sqlalchemy import create_engine, update, insert
from sqlalchemy.orm import Session
from datetime import timedelta
import swp_database

def initialise_database():
    engine = create_engine('sqlite:///swp_flares.db')
    swp_database.Base.metadata.create_all(engine)   
    session = Session(bind=engine)
    #engine = create_engine('sqlite:///swp_flares.db')
    #Base = declarative_base(engine)
    #session = loadSession()

    #def loadSession():
    #     metadata = Base.metadata
    #    Session = sessionmaker(bind=engine)
    #    session = Session()
    #    return session
    return session

#requesting Solarsoft data.
def get_solarsoft_data():
    try: 
        response = urlopen('http://www.lmsal.com/solarsoft/last_events/')
        print 'everything is fine'
    except HTTPError as e:
        print "The server couldn't fulfill the request."
        print 'Error code: ', e.code
        return None 
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason 
        return None
    
    html_content = response.read()
    
    return read_solarsoft_data(html_content)

#Extracting and parsing of SolarSoft data
def read_solarsoft_data(html_content):
    soup = BeautifulSoup(html_content)
    table = soup.findAll('table')[2]

    resultset = []
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) < 7:
            continue
        Datetime = col[2].string
        Peaktime = col[4].string
        #we need to extract date information from the start date to get the peak datetime:
        Peak = get_peakdate_from_startdate(Datetime, Peaktime)
        Start = datetime.datetime.strptime(Datetime, "%Y/%m/%d %H:%M:%S") 
        
        GOES_class = col[5].string
        GOES_flare = convert_flare_format_into_decimal(GOES_class)
        
        if col[6].find('a') is not None:
            Derived_position = col[6].find('a').string
            Region = col[6].find('font').contents[1]
        else: #if there is no link, we assume it's an unnamed region & just derived position is available. 
            Derived_position = col[6].string
            Derived_position = Derived_position.strip()
            Region = ""

        newR = Region.replace("(", "").replace(")", "").strip() #get the number from inside the brackets!

        result = (Start, Peak, GOES_flare, Derived_position, newR)
        resultset.append(result)  
    return resultset
    
def convert_flare_format_into_decimal(GOES_class):
    conversion_lookup_table = {'X':-4, 'M':-5, 'C':-6, 'B':-7, 'A':-8}
    class_letter = GOES_class[0]
    class_exponent = conversion_lookup_table[class_letter]
    digits = float(GOES_class[1:])  #TODO CHECK IF THERE SHOULD BE DECIMAL/NUMERIC
    thenumber = digits * (10 ** class_exponent)
    return thenumber
    


def get_peakdate_from_startdate(start, peak):
    #convert start date into datetime
    start_datetime = datetime.datetime.strptime(start, "%Y/%m/%d %H:%M:%S") 
    #get date part out
    peak_time = datetime.datetime.strptime(peak, "%H:%M:%S").time()
    
    #we assume that an event is shorter than 24 hours
    if (start_datetime.time() <= peak_time): #same day
        peak_datetime = datetime.datetime.combine(start_datetime.date(), peak_time)
    else: #peak time is the following day  
        peak_datetime = datetime.datetime.combine(start_datetime.date() + datetime.timedelta(days=1), peak_time)

    return peak_datetime     
    
def insert_solarsoft_data(ss_result_set, session): 
    ss_result_set = list(set(ss_result_set)) #removes duplicates. Does NOT preserve order. 
   
    #ss_result_set comes as a list of tuples, in the form (ut_datetime, peak, goes_class, derived_position, region)
    solarsoft_object_list = []
    for row in ss_result_set:
        solarsoft_entry = swp_database.Solarsoft(ut_datetime=row[0], peak=row[1], goes_class=row[2], derived_position=row[3], region=row[4])
        res = session.query(swp_database.Solarsoft).filter(swp_database.Solarsoft.ut_datetime==row[0]).all()
        if len(res) == 1: 
            session.delete(res[0])
        solarsoft_object_list.append(solarsoft_entry)
      
    session.add_all(solarsoft_object_list) 
    session.commit() 
    
def query_ss(session): 
    current_time = datetime.datetime.utcnow()
    twenty_four_hours_ago = current_time - datetime.timedelta(hours=24)
    res = session.query(swp_database.Solarsoft).filter(swp_database.Solarsoft.ut_datetime > twenty_four_hours_ago).all()
    #print res
    for row in res:
        print row.event, row.ut_datetime, row.peak, row.goes_class, row.derived_position, row.region

     
#Extrating X-ray flux data 
def generate_filename(date, cadence=1):
    #this file is only updated every hour or so, we may wish to pull from Gp_xr_1m.txt
    if date is None:
        date = datetime.datetime.utcnow()
    filename = "{date}_Gp_xr_{cadence}m.txt".format(date=date.strftime("%Y%m%d"), cadence=cadence)
    return filename

def get_xrayflux_data(date=None):
        
    filename = generate_filename(date)
    
    #this file is only updated every hour or so, we may wish to pull from Gp_xr_1m.txt
    try:
        response = urlopen('http://www.swpc.noaa.gov/ftpdir/lists/xray/'+filename)
        print 'everything is fine'
    except HTTPError as e:
        print "The server couldn't fulfill the request."
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    
    html_content = response.read()

    return read_xrayflux_data(html_content)

def read_xrayflux_data(html_content):  
    resultset = []
    for line in html_content.splitlines():
        #if line[0] !='#' and line[0] !=':':
        if line[0] not in ['#',':']:
            #print line.split()
            yyyy, mm, dd, hhmm, jd, ss, shortx, longx = line.split()   
            date=datetime.datetime.strptime(yyyy+mm+dd+hhmm, "%Y%m%d%H%M")
            result = (date, float(longx), float(shortx))
            resultset.append(result)  
    return resultset

def insert_xrayflux_data(xr_result_set, session):
    #xr_result_set comes as a list of tuples, in the form (date, long, short)
    xrayflux_object_list = []
    for row in xr_result_set:
        xray_entry = swp_database.Xrayflux(ut_datetime = row[0], short = row[2], longx = row[1])
        #print xray_entry
        xrayflux_object_list.append(xray_entry)
    try:    
        session.add_all(xrayflux_object_list ) 
        session.commit()
    except IntegrityError:
        session.rollback()     

def query_xr(session):

    current_time = datetime.datetime.utcnow()
    twenty_four_hours_ago = current_time - datetime.timedelta(days = 3)
    res = session.query(swp_database.Xrayflux).filter(swp_database.Xrayflux.ut_datetime > twenty_four_hours_ago).all()
    #print res
    #for row in res:
        #print row.ut_datetime, row.short, row.longx


def main():
    #setup database for the session 
    session = initialise_database()

    #get solarsoft data
    ss_result_set = get_solarsoft_data()
    
    #print ss_result_set

    #insert into db
    insert_solarsoft_data(ss_result_set, session)
    
    #get xrayflux data, 
    xr_result_set = get_xrayflux_data()
    
    #print xr_result_set
    
    #insert into db
    insert_xrayflux_data(xr_result_set, session)

    #query db for solarsoft & xray data
    query_ss(session)   
    query_xr(session)
    
    #plot graph and save to file

if __name__ == "__main__":
    main()

