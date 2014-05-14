Functional Specification
========================
Space Weather X-Ray flux with Active Region Numbers Display
Nomajama Mhaga
Last Update: 12 May 2014
Version 0.1
This document explains the fuctional design of the X-ray plot from GOES with annotations of Active Region. 



Overview
---------
For the new display, the program will pull data from online resources. When a flare occurs, an X-ray plot from the GOES with Active Region numbers to see which Active region the flare has come from.

System Flow plan
----------------

Technical Design
----------------
Matplotlib will be used to plot the x-ray which is going to be used in Python script. It will run every five minutes. The data will be pulled from online sources, insert it into a database. Every time a flare occurs i.e from C to X or higher level Class, an X-ray plot with Active Region annotation will be displayed. 

###Program Flow Chart


1. See program_flow_chart_1 for the X-ray Flux
![program_flow_chart_1](program_flow_chart_1.png "Flow chart 1")

2. See program_flow_chart_2 for the Active Region Annotation
![program_flow_chart_2](program_flow_chart_2.png "Flow chart 2")


###Conditions

1. X-ray solar flare 
   Background: between A and C level
   flare: between C and X
2. Solar soft (Annotations)
   if class level is greater or equal to M: Annotate with Active region
   Otherwise do not annotate


###Database Format
Database wil have two tables, one for the data of GOES Solar X-ray flux and one for the data of Active Regions.


X-ray Flux
Pull from:[http://www.swpc.noaa.gov/ftpdir/lists/xray/20140513_Gp_xr_5m.txt]

| Id  |   Date time         | Short   | Long   |
|-----|---------------------|---------|--------|
|  1  | 2014 05 13  0020    |1.00e-09 |6.03e-07|
|  2  | 2014 05 13  0025    |1.02e-09 |6.02e-07|  
The X-ray Flux will be converted to human readable format. 

Solar Soft
Pull from: [http://www.lmsal.com/solarsoft/last_events/]

| Event | date       | Start    | Peak      | GOES class | Derived position |
|-------|------------|----------|-----------|------------|------------------|
| 1     | 2014/05/07 | 04:39:00 | 04:45:00  | C1.5       | N06E71 ( 2056 )  |
| 2     | 2014/05/07 | 06:21:00 | 06:30:00  | C3.6       | S10W89 ( 2047 )  |
