# mike mommsen
# july 2013
# read in turnstile data from the MTA from crappy format to csv
# to call enter in command line: python read_turnstile.py infile outfile

# import statements
from collections import defaultdict
import datetime
import sys
import time

# headers for the output csv
HEADERS = "ca,unit,scp,start_time,end_time,"
HEADERS += "start_desc,end_desc,duration,enter_count,exit_count\n"
GOOD_TIMES = [0,4,8,12,16,20]
GOOD_TIMES = [datetime.time(t) for t in GOOD_TIMES]

def processrow(inrow):
    """takes an input row and process into something reasonable"""
    # split the inrow up
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
    value = zip(date, time, desc, entries, exits)
    # blank list to be filled
    mylist = []
    # loop through each row
    for date, time,desc, entries, exits in value:
        # pull out the date and time data as integers
        hour,minute,second = map(int,time.split(':'))
        month,day,year = map(int,date.split('-'))
        # add 20 to the start of year so its the real year
        year = int('20' + str(year))
        # create a datetime object for easy use
        dt = datetime.datetime(year, month, day, hour, minute, second)
        # add everything to the list
        mylist.append((dt, desc, entries, exits))
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
        date, desc, entry, exit = zip(start, end)
        timedelta = date[1] - date[0]
        starttime, endtime = date
        startdesc, enddesc = desc
        entrydelta = entry[1] - entry[0]
        exitdelta = exit[1] - exit[0]
        # make sure that the count is postive and
        if 100000 > entrydelta >= 0 and 100000 > exitdelta >= 0:
            newlist = [starttime, endtime, startdesc, enddesc, timedelta, entrydelta, exitdelta]
            mylist.append(newlist)
    return mylist

def mergeDeltaTuples(intuples):
    """merges two lists into one list (input is twolists in a list)"""
    # functions like this make me think that this should be a class for sure
    # zip together the input tuples (there are always two)
    merged = zip(*intuples)
    starttime = min(merged[0])
    endtime = max(merged[1])
    startdesc = intuples[0][2]
    enddesc = intuples[-1][3]
    timedelta = merged[4][0] + merged[4][1]
    entrydelta = merged[5][0] + merged[5][1]
    exitdelta = merged[6][0] + merged[6][1]
    return [starttime, endtime, startdesc, enddesc, timedelta, entrydelta, exitdelta]

def splitFunction(inlist, ratio, starttime):
    """takes a list from turnstile data and splits it based off of a ratio"""
    midtime = starttime + datetime.timedelta(0, 14400)
    endtime = inlist[1]
    startdesc = inlist[2]
    middesc = 'SPLIT'
    enddesc = inlist[3]
    timedelta1 = datetime.timedelta(0, 14400)
    timedelta2 = inlist[1] - midtime
    entrydelta1 = int(inlist[5] * ratio)
    entrydelta2 = inlist[5] - entrydelta1
    exitdelta1 = int(inlist[6] * ratio)
    exitdelta2 = inlist[6] - exitdelta1
    inlist = [starttime, midtime, startdesc, middesc, timedelta1, entrydelta1, exitdelta1]
    outlist = [midtime,endtime, middesc, enddesc, timedelta2, entrydelta2, exitdelta2]
    return inlist, outlist

def interpolate(inlist):
    """function to harmonize all of the time data to 4 hour intervals"""
    # section below finds the first GOOD_TIME on day of first record
    first_date = inlist[0][0]
    g_time = max([g for g in GOOD_TIMES if g <= first_date.time()])
    dtlist = [first_date.year, first_date.month, first_date.day]
    dtlist += [g_time.hour, g_time.minute, g_time.second]
    start_time = datetime.datetime(*dtlist)
    # create a blank list
    mylist = []
    carryover = None
    # loop through each record
    for i in inlist:
        # check if something is left over from last time looping through
        if carryover:
            i = mergeDeltaTuples([carryover, i])
            carryover = None
        # find the time between the records end and the start time
        time_seconds = i[1] - start_time
        time_seconds = time_seconds.total_seconds()
        # now the conditional loops
        # when duration is 4 hours long everything is good
        if time_seconds == 14400:
            # just set the lists starttime to the real starttime
            i[0] = start_time
            # and the time delta in the list to 4 hours
            i[4] = datetime.timedelta(0,14400)
            # add to the output list
            mylist.append(i)
            # set the start time for the next time through the loop
            start_time = i[1]
        # when duration is greater than 4 hours we need to split it apart
        elif time_seconds > 14400:
            ratio = 14400 / time_seconds
            # split the tuple into part that is in time window and part past 
            intime, outtime = splitFunction(i, ratio,start_time)
            start_time = intime[1]
            mylist.append(intime)
            # set carryover to the remainder so it is used in the next time 
            carryover = outtime
        # if duration < 4 hours carryover until we get to a time in GOOD_TIMES
        else:
            carryover = i
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
        mydict[k] = interpolate(mydict[k])
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
