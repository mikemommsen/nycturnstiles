# mike mommsen
# july 2013
# read in turnstile data from the MTA from crappy format to csv
# to call enter in command line: python turnstile.py infile outfile

# import statements
from collections import defaultdict
import datetime
import sys
import time

# headers for the output csv
HEADERS = "ca,unit,scp,start_time,end_time,duration,enter,exit\n"

def processrow(inrow):
    """takes an input row and process into something reasonable"""
    # splite the inrow up
    inrow = inrow.strip().split(',')
    # take the defining attributes, used for the key
    k = tuple(inrow[:3])
    # take every 5th item because lines are varying lengths
    date = inrow[3::5]
    time = inrow[4::5]
    desc = inrow[5::5]
    # same here but turn them into integers so math can be done
    entries = map(int, inrow[6::5])
    exits = map(int,inrow[7::5])
    # merge all of the lists together to create a list of values
    value = zip(date, time, entries, exits)
    # blank list to be filled
    mylist = []
    # loop through each row
    for date, time, entries, exits in value:
        # pull out the date and time data as integers
        hour,minute,second = map(int,time.split(':'))
        month,day,year = map(int,date.split('-'))
        # add 20 to the start of year so its the real year
        year = int('20' + str(year))
        # create a datetime object for easy use
        dt = datetime.datetime(year,month,day,hour,minute,second)
        # add everything to the list
        mylist.append((dt, entries, exits))
    return k, mylist

def processlist(inlist):
    """processes the sorted data for one turnstile"""
    # blank list
    mylist = []
    # loop through the list - not sure if this is the best way
    # go from [1,2,3,4] to [(1,2),(2,3),(3,4)]
    for start, end in zip(inlist[:-1],inlist[1:]):
        newlist = []
        # zip together the start and end lists for easy math
        for a,b in zip(start, end):
            # probably should not do this
            if type(a) == datetime.datetime:
                # when it is datetime add to list so we know what time
                newlist.append(a)
                newlist.append(b)
            # subtract end val from start val
            delta = b - a
            newlist.append(delta)
        mylist.append(tuple(newlist))
    return mylist

def run(infile,outfile):
    """function to feed into other functions"""
    # open the input file
    f = open(infile)
    # create a blank defaultdict that handles lists
    mydict = defaultdict(list)
    # loop through each row of the input file
    for r in f:
        # send to processrow function
        k,v = processrow(r)
        # add to the dictionary
        mydict[k] += v
    # close the input file
    f.close()
    # open the output file
    f = open(outfile, 'w')
    # write the csv headers to the output file
    f.write(HEADERS)
    # loop through the dictionary of values
    for k in mydict:
        # send list of data for each turnstile to processlist function
        # and update dictionary with new delta values
        mydict[k] = processlist(sorted(mydict[k]))
        # turn key into csv string
        partone = ','.join(map(str, k))
        # loop through each record in delta list for given turnstile
        
        for i in mydict[k]:
            # turn values into csv string
            parttwo = ','.join(map(str,i))
            # write to output file the key, value joined with a comma
            f.write('{0},{1}\n'.format(partone,parttwo))
    f.close()

def main():
    # start a timer to see how long it takes
    t1 = time.time()
    # take the arguments from the command line
    infile = sys.argv[1]
    outfile = sys.argv[2]
    # call the run function
    run(infile, outfile)
    # let the user know it is done
    print 'success!!!!'
    print 'infile: {0} outfile: {1}'.format(infile, outfile)
    print 'total time: {0} seconds'.format(time.time() - t1)

if __name__ == '__main__':
    main()
