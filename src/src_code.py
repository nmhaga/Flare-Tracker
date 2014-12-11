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
import argparse

def initialise_database():
    engine = create_engine('sqlite:///swp_flares.db')
    Base.metadata.create_all(engine)   
    session = Session(bind=engine)
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
    if GOES_class is None:
        return None
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
        response = urlopen('ftp://ftp.swpc.noaa.gov/pub/lists/xray/'+filename)
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
        
def plot_data(xrayfluxobjects, solarsoftobjects, issixhour=True, title='GOES X-ray Flux (1 minute data)', path=None):
    if path is None:
        path=""
        
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
    my_dpi = 100 #this gives a size on this machine of 800x600px.
    figure = plt.figure(figsize=(800/my_dpi,600/my_dpi), dpi = my_dpi)
    # ^^ from http://stackoverflow.com/a/13714720/3714005 
    plt.plot(ut_datetimes, shorts, 'b', label='0.5--4.0 $\AA$', lw=1.2)
    plt.plot(ut_datetimes, longxs, 'r', label='1.0--8.0 $\AA$', lw=1.2)
    plt.figtext(.95, .40, "GOES 15 0.5-4.0 A", color='blue', size='large', rotation='vertical')
    plt.figtext(.95, .75, "GOES 15 1.0-8.0 A", color='red', size='large', rotation='vertical')
    
    for peakdt, g_class, region_no, position in solarsofttuples:
        if region_no != "":
            plt.annotate(region_no, xy=(mdates.date2num(peakdt + timedelta(minutes=5)), g_class*Decimal(1.8)), rotation=45, fontsize=8)
        else:
            plt.annotate(position, xy=(mdates.date2num(peakdt + timedelta(minutes=5)), g_class*Decimal(1.8)), rotation=45, fontsize=8)   
                
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
    
 
    dtn = datetime.now()    
    xticks = []
    if issixhour: #grid and ticks should be hourly     
        filename = "latest6hr.png" 
        filename = os.path.join(path, filename)     
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
        filename = os.path.join(path, filename) 
        formatter = mdates.DateFormatter('%b %d')
        locator = mdates.HourLocator(interval=6)
        axes.xaxis.set_major_formatter(formatter)
        startdt = datetime(dtn.year, dtn .month, dtn.day, 0, 0, 0) - timedelta(days=2)
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
    #axes.xaxis.set_major_locator(HourLocator(byhour=range(24))
    
    try:
        figure.savefig(filename, dpi = my_dpi)   
        print "done plotting"

    except IOError, e:
        print "Could not find the path!! Please ensure that when providing a path you choose a valid path that exists!"
        
        

def makeaplot(session, issixhour=True, threshold=None, path=None):
    #threshold should be in decimal format
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
    plot_data(xrayobjects, solarsoftobjects, issixhour, title, path) 


def main(getoldstuff=False, threshold=None, path=None):

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

    numberthreshold = convert_flare_format_into_decimal(threshold)
    makeaplot(session, True, numberthreshold, path) #6hour
    makeaplot(session, False, numberthreshold, path) #3day
 
  
if __name__ == "__main__":
            
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--flarestrength", help="Number of the cutoff Flare in format 'C4.7'")
    parser.add_argument("-o", "--getoldstuff", help="Present if program should fetch older data from 3 days ago (takes longer)", action="store_true")
    parser.add_argument("-p", "--path", help="Specify the folder path where the plots should be stored")
    args = parser.parse_args()
    
    main(args.getoldstuff, args.flarestrength, args.path)

  
