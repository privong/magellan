#!/usr/bin/python2
#
# plot_histogram.py
#
# Plot already computed weekly analysis.

import sys,time,math,numpy,MySQLdb,argparse,ConfigParser
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from datetime import date

parser=argparse.ArgumentParser(description='Plot information on home/away/travel based on different time intervals.')
parser.add_argument('-week',action='store_true',default=False,help='Plot analyitics for the past 10 weeks.')
parser.add_argument('-year',action='store_true',default=False,help='Plot analyitics for the current year.')
args=parser.parse_args()

# load information from the configuration file
config=ConfigParser.RawConfigParser()
config.read('.magellan')
if not(config.get('Server Config','server')) or not(config.get('Server Config','user')) or not(config.get('Server Config','password')) or not(config.get('Server Config','db')):
  sys.stderr.write('Configuration file error. Please check the configuration file.\n')
  sys.exit(-1)
else:
  Mserver=config.get('Server Config','server')
  Muser=config.get('Server Config','user')
  Mpw=config.get('Server Config','password')
  Mdb=config.get('Server Config','db')

TABLENAME="analyze_weekly"

# set up mySQL connection
scon=MySQLdb.connect(host=Mserver,user=Muser,passwd=Mpw,db=Mdb)
cursor=scon.cursor()

if args.week:
  print "Retreiving analyzed weekly data for the past 10 weeks...\n"
  
  # get the previous iso week (to use as the end of the plot)
  today=date.today()
  week=(today.isocalendar())[1]-1
  year=(today.isocalendar())[0]
  
  # here, retreive all the data from the past 10 weeks
  if week<=10:
    # get the number of weeks last year
    lyweeks=date.isocalendar(date(year-1,12,31))[1]
    command='SELECT year,week,homefrac,awayfrac,travelfrac from analysis_weekly where (YEAR=%i) OR (YEAR=%i AND WEEK > %i) ORDER BY year,week' % (year,year-1,lyweeks-10+week)
  else:
    # it's far enough into the year we can just grab the last 10
    command='SELECT year,week,homefrac,awayfrac,travelfrac from analysis_weekly where WEEK > %i AND YEAR=%i ORDER BY week' % (week-10,year)
  file='latest.png'
elif args.year:
  today=date.today()
  year=(today.isocalendar())[0]
  command='SELECT year,week,homefrac,awayfrac,travelfrac from analysis_weekly where YEAR=%i ORDER BY week' % (year)
  file='year.png'

# run the command
cursor.execute(command)
recs=cursor.fetchall()

if len(recs)==0:
  print "ERROR: no analysis data found."
  sys.exit

print "Retreived %i results" % (len(recs))

results=numpy.array(recs)

plt.ioff()
# plot home, away, travel
plotsym=['ro','go','bo']
plotlabel=['Home','Away','Travel']
for i in range(2,5):
  plt.plot(results[:,1],results[:,i],plotsym[i-2],label=plotlabel[i-2])
plt.ylim([-0.01,1.1])
(x1,x2)=plt.xlim()
plt.xlim(x1-1,x2+1)
plt.ylabel('Fraction')
plt.xlabel('Week Number')
plt.savefig('/srv/http/local/location/'+file,transparent=True)

# close SQL
cursor.close()
scon.close()
