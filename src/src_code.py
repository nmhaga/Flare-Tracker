#This is where the source code is written.
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
#We need to use 'Agg' before we import pyplot, as that prevents issues when running it from cron

#http://stackoverflow.com/questions/4931376/generating-matplotlib-graphs-without-a-running-x-server

import matplotlib.dates as mdates
from datetime import datetime, timedelta
from BeautifulSoup import BeautifulSoup
from urllib2 import Request, urlopen, URLError, HTTPError
from sqlalchemy import create_engine, update, insert
from sqlalchemy.orm import Session
import pylab
from decimal import Decimal
from swp_database import Base, Solarsoft, Xrayflux
import os
import sys

def initialise_database():
    engine = create_engine('sqlite:///swp_flares.db')
    Base.metadata.create_all(engine)   
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
def get_solarsoft_data(date=None):
    print "Trying to get SolarSoft Data\n---------------------------"
    try: 
        response = urlopen('http://www.lmsal.com/solarsoft/last_events/')
        print 'everything is fine for Solarsoft data'
    except HTTPError as e:
        print "The server couldn't fulfill the request."
        print 'Error code: ', e.code
        print 'Attempting to continue...\n--------------------------'
        return []
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason 
        return []
    
    html_content = response.read()
    
    return read_solarsoft_data(html_content)

#Extracting and parsing of SolarSoft data
def read_solarsoft_data(html_content):
    soup = BeautifulSoup(html_content)
    table = soup.find('table', border=2, cellpadding=5, cellspacing=2)
    resultset = []
    if table is None: #the website doesn't look how we expect
        return resultset
    for row in table.findAll('tr'):
        col = row.findAll('td')
        if len(col) < 7:
            continue
        Datetime = col[2].string
        Peaktime = col[4].string
        #we need to extract date information from the start date to get the peak datetime:
        Peak = get_peakdate_from_startdate(Datetime, Peaktime)
        Start = datetime.strptime(Datetime, "%Y/%m/%d %H:%M:%S") 
        
        GOES_class = col[5].string
        GOES_flare = convert_flare_format_into_decimal(GOES_class)
        
        if col[6].find('a') is not None:
            Derived_position = col[6].find('a').string.lstrip()
            Region = col[6].find('font').contents[1]
        else: #if there is no link, we assume it's an unnamed region & just derived position is available. 
            Derived_position = col[6].string.strip()
      
            Region = ""

        newR = Region.replace("(", "").replace(")", "").strip() #get the number from inside the brackets!
        
        result = Solarsoft(ut_datetime=Start, peak=Peak, derived_position=Derived_position, goes_class=GOES_flare, region=newR)
        resultset.append(result)  
    return resultset
    
def convert_flare_format_into_decimal(GOES_class):
    try:
        conversion_lookup_table = {'X':-4, 'M':-5, 'C':-6, 'B':-7, 'A':-8}
        class_letter = GOES_class[0]
        class_exponent = conversion_lookup_table[class_letter]
        digits = float(GOES_class[1:])  #TODO CHECK IF THERE SHOULD BE DECIMAL/NUMERIC
        thenumber = digits * (10 ** class_exponent)
    except Exception, e:
        raise Exception("Error converting flare format to decimal", e)
    return thenumber
    
def get_peakdate_from_startdate(start, peak):
    #convert start date into datetime
    start_datetime = datetime.strptime(start, "%Y/%m/%d %H:%M:%S") 
    #get date part out
    peak_time = datetime.strptime(peak, "%H:%M:%S").time()
    
    #we assume that an event is shorter than 24 hours
    if (start_datetime.time() <= peak_time): #same day
        peak_datetime = datetime.combine(start_datetime.date(), peak_time)
    else: #peak time is the following day  
        peak_datetime = datetime.combine(start_datetime.date() + timedelta(days=1), peak_time)

    return peak_datetime     
    
def insert_solarsoft_data(ss_result_set, session): 
    ss_result_set = list(set(ss_result_set)) #removes duplicates. Does NOT preserve order. 
   
    #ss_result_set comes as a list of SolarSoft objects
    solarsoft_object_list = []
    for row in ss_result_set:
        res = session.query(Solarsoft).filter(Solarsoft.ut_datetime==row.ut_datetime).all()
        if len(res) >= 1: 
            for r in res:
                session.delete(r)
        solarsoft_object_list.append(row)
      
    session.add_all(solarsoft_object_list) 
    session.commit() 
    
def query_ss(session, duration, minimum): 
    current_time = datetime.utcnow()
    six_hour_data = current_time - duration
    res = session.query(Solarsoft).filter(Solarsoft.ut_datetime > six_hour_data).filter(Solarsoft.goes_class > minimum).all()
    return res
    #print res
    #for row in res:
        #print row.event, row.ut_datetime, row.peak, row.goes_class, row.derived_position, row.region

     
#Extrating X-ray flux data 
def generate_filename(date, cadence=1):
    #if date is None, we pull from the realtime Gp_xr_1m.txt since the other file is only updated every hour or so.
    if date is None:
        filename = "Gp_xr_{cadence}m.txt".format(cadence=cadence)
    else:
        filename = "{date}_Gp_xr_{cadence}m.txt".format(date=date.strftime("%Y%m%d"), cadence=cadence)
    return filename

def get_xrayflux_data(date=None):
        
    filename = generate_filename(date) #if date is None, does realtime.
    
    print "Trying to get XrayFlux data\n--------------------------"
    try:
        response = urlopen('http://www.swpc.noaa.gov/ftpdir/lists/xray/'+filename)
        print 'Everything is fine for Xrayflux data'
    except HTTPError as e:
        print "The server couldn't fulfill the request."
        print 'Error code: ', e.code
        print 'Attempting to continue...\n--------------------------'
        return ""
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
        return ""
        
    html_content = response.read()

    return read_xrayflux_data(html_content)

def read_xrayflux_data(html_content): 
    resultset = []
    for line in html_content.splitlines():
        #if line[0] !='#' and line[0] !=':':
        if line[0] not in ['#',':']:
            #print line.split()
            yyyy, mm, dd, hhmm, jd, ss, shortx, longx = line.split()   
            date = datetime.strptime(yyyy+mm+dd+hhmm, "%Y%m%d%H%M")
            result = Xrayflux(ut_datetime=date, longx=float(longx), short=float(shortx))
            resultset.append(result)  
    return resultset

def insert_xrayflux_data(xr_result_set, session):
    xs_result_set = list(set(xr_result_set))
    
    #xr_result_set comes as a list of Xrayflux objects
    xrayflux_object_list = []
    for row in xr_result_set:
        res = session.query(Xrayflux).filter(Xrayflux.ut_datetime==row.ut_datetime).all()
        if len(res) >= 1: 
            for r in res:
                session.delete(r)
        xrayflux_object_list.append(row)
    
    session.add_all(xrayflux_object_list) 
    session.commit()
     
def query_xr(session, duration):
    
    current_time = datetime.utcnow()
    six_hours_data = current_time - duration
    res = session.query(Xrayflux).filter(Xrayflux.ut_datetime > six_hours_data).order_by(Xrayflux.ut_datetime).all()
    return res
    #print res
    #for row in res:
        #print row.ut_datetime, row.short, row.longx
        
     

def plot_data(xrayfluxobjects, solarsoftobjects, issixhour=True, title='GOES X-ray Flux (1 minute data)'):
    # reformat data:
    ut_datetimes = []
    shorts = []
    longxs = []
   
    for xr in xrayfluxobjects:
        ut_datetimes.append(xr.ut_datetime)
        shorts.append(xr.short)
        longxs.append(xr.longx)
    
    solarsofttuples = []
    for ss in solarsoftobjects:
        solarsofttuples.append((ss.peak, ss.goes_class, ss.region, ss.derived_position))
    
    #Make Plot
    print "plotting" 
    #print "ut_datetimes = {}".format(ut_datetimes[1000:1500])
    #print "longxs = {}".format(longxs[1000:1500])
    #print "solarsofttuples = {}".format(solarsofttuples)
    figure = plt.figure()

    plt.plot(ut_datetimes, shorts, 'b', label='0.5--4.0 $\AA$', lw=1.2)
    plt.plot(ut_datetimes, longxs, 'r', label='1.0--8.0 $\AA$', lw=1.2)
    plt.figtext(.95, .40, "GOES 15 0.5-4.0 A", color='blue', size='large', rotation='vertical')
    plt.figtext(.95, .75, "GOES 15 1.0-8.0 A", color='red', size='large', rotation='vertical')
    
    for peakdt, g_class, region_no, position in solarsofttuples:
        if region_no != "":
            plt.annotate(region_no, xy=(mdates.date2num(peakdt + timedelta(minutes=5)), g_class*Decimal(1.8)), rotation=45, fontsize=8)
        else:
            plt.annotate(position, xy=(mdates.date2num(peakdt + timedelta(minutes=5)), g_class*Decimal(1.8)), rotation=45, fontsize=8)   
                #bbox=dict(boxstyle='round', fc='white', alpha=0.5))
        #plt.annotate('.', xy=(mdates.date2num(x), y), rotation=45 )

    #Define Axes limits
    axes = plt.gca()
    axes.set_yscale("log")
    axes.set_ylim(1e-9, 1e-2)
    axes.set_title(title, y=1.07)
    axes.set_ylabel('Watts m$^{-2}$')
    axes.set_xlabel('Universal Time')

    ax2 = axes.twinx()
    ax2.set_yscale("log")
    ax2.set_ylim(1e-9, 1e-2)
    ax2.set_yticks((1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3, 1e-2))
    ax2.set_yticklabels((' ', 'A', 'B', 'C', 'M', 'X', ' '))
    axes.yaxis.grid(True, 'major', ls='-')
    axes.xaxis.grid(True, 'major')
    
   #axes.legend(loc=3, ncol=2, bbox_to_anchor=(0., 1.02, 1., .102), borderaxespad=0.)
    
    dtn = datetime.now()    
    xticks = []
    if issixhour: #grid and ticks should be hourly     
        filename = "latest6hr.png"      
        formatter = mdates.DateFormatter('%H:%M')
        locator = mdates.MinuteLocator(interval=15)
        startdt = datetime(dtn.year, dtn.month, dtn.day, dtn.hour, 0, 0) - timedelta(hours=7)
        for i in range(0,7):
            xticks.append(startdt + timedelta(hours=i))
            
            
        utcnow = datetime.utcnow()
        plt.figtext(0, 0.02, utcnow.strftime("Updated: %d %b %Y %H:%M UT"))
        plt.figtext(0.6,0.92,startdt.strftime("Begin: %d %b %Y %H:%M UT"))
    
    else:
        filename = "latest3day.png" 
        formatter = mdates.DateFormatter('%b %d')
        locator = mdates.HourLocator(interval=6)
        axes.xaxis.set_major_formatter(formatter)
        startdt = datetime(dtn.year, dtn.month, dtn.day, 0, 0, 0) - timedelta(days=2)
        for i in range(0,4):
            xticks.append(startdt + timedelta(days=i))
        
        utcnow = datetime.utcnow()
        plt.figtext(0, 0.02, utcnow.strftime("Updated: %d %b %Y %H:%M UT"))
        plt.figtext(0.6,0.92,startdt.strftime("Begin: %d %b %Y %H:%M UT"))
    
    #this comes a little later to override whatever came before.
    
    axes.set_xticks(xticks)
    axes.set_xlim(xticks[0], xticks[-1])        
    axes.xaxis.set_minor_locator(locator)
    axes.xaxis.set_major_formatter(formatter)
    #axes.xaxis.set_major_locator(HourLocator(byhour=range(24)))
    
    #figure.show()
    #print filename
    figure.savefig(filename)
    print "done plotting"

def makeaplot(session, issixhour=True, threshold=None):
    if threshold is None: 
        threshold = Decimal(1e-5)
        
    theduration = timedelta(hours=6)
    
    title = "GOES X-ray Flux (1 minute data)"
    
    if not issixhour:
        theduration = timedelta(days=3)
        title = "GOES X-ray Flux (5 minute data)"
        
    xrayobjects = query_xr(session, theduration)
    solarsoftobjects = query_ss(session, theduration, threshold)
    #plot graph and save to file
    plot_data(xrayobjects, solarsoftobjects, issixhour, title) 


def main(getoldstuff=False, threshold=None):

    #setup database for the session 
    session = initialise_database()
    
    issixhour = True #change plot type here!
    #issixhour = False #change plot type here!
    dt = datetime.now()
    
    #get solarsoft data
    ss_result_set = get_solarsoft_data()
    ss_result_set += get_solarsoft_data(dt)
    #insert into db
    insert_solarsoft_data(ss_result_set, session)
    
    #get xrayflux data, 
    xr_result_set = get_xrayflux_data()
    xr_result_set += get_xrayflux_data(dt)
    #insert it
    insert_xrayflux_data(xr_result_set, session)
    
    
    if getoldstuff:
        #get more solarsoft data
        ss_result_set = get_solarsoft_data(dt - timedelta(days=1))
        ss_result_set += get_solarsoft_data(dt - timedelta(days=2))
        
        #and insert it
        insert_solarsoft_data(ss_result_set, session)
    
        #get more xrayflux data
        xr_result_set = get_xrayflux_data(dt - timedelta(days=1))
        xr_result_set += get_xrayflux_data(dt - timedelta(days=2))
       
        #and insert it
        insert_xrayflux_data(xr_result_set, session)


    makeaplot(session, True, threshold) #6hour
    makeaplot(session, False, threshold) #3day
   
        
def fakemain():
    #setup database for the session 
    session = initialise_database()
    makeaplot(session, True) #6hour
    makeaplot(session, False) #3day
    

def checkarg(thestring):
    if thestring.startswith("T") or thestring.startswith("F"):
        if thestring == "True":
            return ("getoldstuff", True)
        elif thestring == "False":
            return ("getoldstuff", False)
        else:
            return ("fail", 0)
    else:
        try:
            decimal = convert_flare_format_into_decimal(thestring)
            return ("threshold", decimal)
        except Exception, e:
            print e
            return ("failure", 0)
          
if __name__ == "__main__":
    usage = "USAGE: python src_code.py [True/False] [GOES_Class]\n The arguments can be in any order. GOES_Class must be a letter (A,B,C,M,X) followed by a number 1 or 1.4, like C1.4."
    
    if len(sys.argv) == 1:
        main() 
    elif len(sys.argv) == 2:
        #then it's one or the other
        mytype, value = checkarg(sys.argv[1])
        if mytype == "getoldstuff":
            main(getoldstuff=value)
        elif mytype == "threshold":
            main(threshold=value)
        else: #fail
            print usage
     
    elif len(sys.argv) == 3:
        #then it's both
        mytype, value = checkarg(sys.argv[1])
        mytype2, value2 = checkarg(sys.argv[2])
        if mytype == "getoldstuff" and mytype2 == "threshold":
            main(getoldstuff=value, threshold=value2)
        elif mytype == "threshold" and mytype2 == "getoldstuff":
            main(getoldstuff=value2, threshold=value)
        else: #too many of one type or fail. 
            print usage
        
    else:   
        print usage   
                  

