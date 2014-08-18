Functional Specification
========================
######Space Weather X-Ray flux with Active Region Numbers Display
######Nomajama Mhaga
######Last Update: 12 May 2014
######Version 0.1
This document explains the fuctional design of the X-ray plot from GOES with annotations of Active Region. 



Overview
---------
The Flare-Tracker program will pull data from online resources every 5 minutes. It will organise and store data into a database, and then pull that data from the database and plot X-ray flux with annotations of Active Region numbers. The plot will be displayed on one of the screens in the Space Weather Centre.

Technical Design
----------------
Matplotlib will be used to plot the x-ray which is going to be used in Python script. The data will be pulled from online sources, and inserted into a database. Every five minutes a graph will be plotted annotating the areas with the flare i.e from C to X or higher level Class. A for-loop will be implemented to determine whether it falls under background class or flare class. In a case where there is no active region, we assume it is an unnamed region and annotate with the derived position.

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
   if class level is greater or equal to C: Annotate with Active region
   Otherwise do not annotate

###Data Extraction and Parsing
//For both of them, we use the standard URL fetching library, URLLib. Then we make a request for the URL and get the HTML content. (split this out, only put detail into the subsections where required.)

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
//specific to this is generating the filename. This file is only updated every hour or so, we may wish to pull from Gp_xr_1m.txt. 

Since the lines in the X-ray Flux file are separated by white space and in plain text we will loop over the file and use .split().

####Solar Soft

//specific to this is converting Xray class into number. 
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
Inorder to get the peak datetime, we will extract the date information from the startdate.

###Inserting into database
For both of them the data will come as a list of tuples.
- import sqlalchemy
- Open database connection with create_engine method
- Prepare a session object using the session() object
- create an empty list
- create a 'for loop' for the rows
- To persist xrayflux objects to database use session.add()
- Issue all remaining changes to the database and commit with session.commit()
- Rollback in case there is any error with session.rollback()

###Pulling from database
- import module to access SQLAlchemy database 
- connect to the database server to access the database
- prepare a cursor 
- make the query to be executed 
- execute the query
- retrieve the results 
- Close cursor and connection 

###Plotting
- import matplotlib pyplot module
- Plot graph

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

| Id    |   Date time  	       | Peak      | GOES class | Derived position |Region |
|-------|----------------------|-----------|------------|------------------|-------|
| 1     | 2014 05 07 04:39:00  | 04:45:00  | C1.5       | N06E71           |2056   |
| 2     | 2014 05 07 06:21:00  | 06:30:00  | C3.6       | S10W89           |2047   |

The goes class column comes in a string format, it will be converted to a decimak format.

