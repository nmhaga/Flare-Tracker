Functional Specification
========================
######Space Weather X-Ray flux with Active Region Numbers Display
######Nomajama Mhaga
######Last Update: 05 September 2014
######Version 0.1
This document explains the fuctional design of the X-ray plot from GOES with annotations of Active Region. 

Overview
---------
The Flare-Tracker program will pull data from online resources every 5 minutes. It will organise and store data into a database, and then pull that data from the database and plot X-ray flux with annotations of Active Region numbers. The plot will be displayed on one of the screens in the Space Weather Centre.

Technical Design
----------------
The program will be written in Python, using sqlite3 (connecting to python with SQLALchemy) and matplotlib. The data will be pulled from online sources, and inserted into a database. Every five minutes a graph will be plotted using matplotlib annotating the areas with the flare i.e from C to X or higher level Class. In a case where there is no active region number, we assume it is an unnamed region and annotate with the derived position.

###Program Flow Chart

|                 **Program Flow Table**                                       |
|------------------------------------------------------------------------------|
|  1. Setup Database connection (create db if doesn't exist)                   |
|  2. Fetch Data From GOES                                                     |
|  3. Parse Data From GOES                                                     |
|  4. Insert GOES Data into Database                                           |
|  5. Fetch Data From SolarSoft                                                |
|  6. Parse Data From SolarSoft                                                |
|  7. Insert SolarSoft Data into Database                                      |
|  8. Fetch 24 hours of GOES & Solarsoft data from database, check thresholds  |
| 10. Plot the graph                                                           |
| 11. Annotate the graph                                                       |
| 12. Save the graph to an image file.                                         |


###Conditions

1. Solar soft (Annotations)
   if class level is greater or equal to M: Annotate with Active region
   Otherwise do not annotate

###Data Extraction and Parsing
//For both of GOES and SolarSoft, we use the standard URL fetching library, URLLib. Then we make a request for the URL and get the HTML content. (split this out, only put detail into the subsections where required.)

URLError will be raised when there is a problem with the network connection.
We can be prepared for the HTTPError or URLError by an approach of this nature:

```python
	from urllib2 import request, urlopen, URLError
	req = Request (url)
	try:
		response = urlopen(req)
	    print 'everything is fine'
    except HTTPError as e:
        print "The server couldn't fulfill the request."
        print 'Error code: ', e.code
    except URLError as e:
        print 'We failed to reach a server.'
        print 'Reason: ', e.reason
    
```

####X-ray Flux
//Specific to this is generating the filename. This file is only updated every hour or so, we may wish to pull from Gp_xr_1m.txt. 

Since the lines in the X-ray Flux file are separated by white space and in plain text we will loop over the file and use .split().

####Solar Soft

//Since the GOES class comes in a string format, we will convert it to a decimal type. The first element of the string represent the classification of a solar flare according to the peak flux, ie. A, B, C, M or X. Each X-ray class category is divided into a logarithmic scale from 1 to 9. The second element is the class exponent which ranges from {-8 to -4}.

The module BeautifulSoup will be used for parsing html once the data is already fetched. 
e.g
```python
	from bs4 import beautifulsoup
	soup = BeautifulSoup(html_content)
	table = soup.findAll ("table")
	row = table.findAll('tr')
	for tr in rows:
		cols = tr.findAll('td')
```
In the Solarsoft table the peak time has no date so inorder to get the peak datetime, we will extract the date information from the startdate. We need this date to know exactly which date the flare reaches a peak.

Possible scenarios:
start datetime           Peak         Peak datetime
2014/01/01 23:59         00:00        2014/01/02 00:00
2014/01/01 00:00         00:00        2014/01/01 00:00
2014/01/02 00:00         00:05        2014/01/02 00:05

###Inserting into database
For both of them the data will come as a list of tuples.
- import sqlalchemy
- Open database connection with create_engine method
- Prepare a session object using the session() object
- create an empty list
- create a 'for loop' for the rows
- To persist the objects to database use session.add()
- Issue all remaining changes to the database and commit with session.commit()
- You can Rollback in case there is any error with session.rollback(), but we won't implement this yet. 

###Pulling from database
- import module to access SQLAlchemy database 
- connect to the database server to access the database
- prepare a cursor 
- make the query to be executed (see below)
- execute the query
- retrieve the results and store in variables
- Close cursor and connection 

#### Pull x-ray data: 
//Explain here how you would specify date-range. Where datetime > (end of today - 3 days) 
We want to specify the date between now and 3 days ago. we can do this in python using the datetime and timedelta functions.
We want it to snap to the nearest date. to do this: 
 
we set up the datetime where hour, minute and second is equal to zero.
By the end of the day we want the plot to be full.

##come back to this! Think about how to make the graph look niiice. 
````python
dtnow = datetime.datetime.utcnow()
dt3days = dtnow - datetime.timedelta(days=3)
3day_ago_data = session.query(data).filter(data.datetime > dt3days).all()
#(fetch data where datetime <=  
````

#### Pull solarsoft data
As well as the dtnow that we do above, we also need to specify the threshold for region annotation. The threshold will be M-class (which corresponds to greater than 10*-5). This would be specified as "WHERE GOES_CLASS M >= 1.0e-*-5" 


###Plotting
- import matplotlib pyplot module
- Configure/create the axes
- Put the data into the format required by matplotlib (probably using a list comprehension) 
- Plot graph

The background colour will be white. 
The short plot will be Blue
The long plot will be Red
Annotations will be in blackack and we want to annotate the long only. 
The y-scale needs to be logorithmic.
We will want to mark the class scale on the other axis

###Database Format
We will use the Python toolkit and Object Relational Mapper (ORM) called SQLAlchemy.
Database will have two tables, one for the data of GOES Solar X-ray flux and one for the data of Active Regions.

X-ray Flux
Pull from [NOAA](http://www.swpc.noaa.gov/ftpdir/lists/xray/20140513_Gp_xr_5m.txt)

| Id |   Date time         | Shortx  | Longx  |
|----|---------------------|---------|--------|
| 1  | 2014 05 13  0020    |1.00e-09 |6.03e-07|
| 2  | 2014 05 13  0025    |1.02e-09 |6.02e-07| 
The X-ray Flux will be converted to human readable format. 

Solar Soft
Pull from: [http://www.lmsal.com/solarsoft/last_events/]

| Id    |   Date time  	       | Peak      | GOES class   | Derived position |Region |
|-------|----------------------|-----------|--------------|------------------|-------|
| 1     | 2014 05 07 04:39:00  | 04:45:00  |0.000001500000| N06E71           |2056   |
| 2     | 2014 05 07 06:21:00  | 06:30:00  |0.000004400000| S10W89           |2047   |

The goes class column comes in a string format, it will be converted to a decimal format.

