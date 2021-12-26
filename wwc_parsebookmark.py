import dateparser
import datetime
from wwc_TOC import remove_square_brackets
import re

def getdayofWeek(dt):
    if dt:
        d=dt.weekday()
        if d==0:
            return 'M'
        elif d==1:
            return 'Tu'
        elif d==2:
            return 'W'
        elif d==3:
            return 'Th'
        elif d==4:
            return 'F'
        elif d==5:
            return 'Sa'
        elif d==6:
            return 'Su'
        else:
            return ''
    return ''


def makedateUniform(str):

    def replace_function1(matched_object):
        match=""
        try:
            match=matched_object.group(0).zfill(2)
            #match third group
        except:
            return ''
        else:
            return match
    str = re.sub(r'\b(\d{1,2})\b', replace_function1, str)
    return str



def getdatefromNode(tree,node,options=None):
    #returns date from node
    txt=", " + tree.item(node)['values'][0]
    return getdatefromText(txt, options)

def gettextfromNode(tree, node, options=None):
    #returns text without any date from node
    txt=tree.item(node)['text']
    txt=remove_square_brackets(txt)
    return gettextfromText(txt, options)

def gettextfromText(txt, options=None):
    #returns everything up to the last comma or, if no commas, the whole thing
    txt=remove_square_brackets(txt)
    rComma=txt.rfind(",")
    l=txt[:rComma]
    r=txt[rComma+1:].lstrip()
    if isValidDate(r): return l
    return txt

def getdate(txt):
    #takes 3/10/2020 10:12 and returns dt object

    def convertyytoYYYY(txt):
        if txt:
            txt=txt.lstrip('0')
            if len(txt)<=2:
                a=int(txt)
                if a<50:
                    return '20'+ str(a).zfill(2)
                else:
                    return '19'+str(a).zfill(2)
        return txt

    def getDt(txt):
        #takes 3/10/20 and returns day, month, year
        d=1
        m=1
        y=None
        x=txt.split('/')
        for a in x:
            if not a.lstrip('0').isnumeric(): return d,m,y
        if len(x)==3:
            d=int(x[0])
            m=int(x[1])
            y=int(convertyytoYYYY(x[2]))
        if len(x)==2:
            m=int(x[0])
            y=int(convertyytoYYYY(x[2]))
        if len(x)==1:
            y=int(convertyytoYYYY(x[0]))
        return d,m,y

    def getTm(txt):
        #takes 09:10:11:90 and returns hour, minute, seconds
        x=txt.split(":")
        h=0
        m=0
        s=0
        ms=0
        if len(x)==2:
            h=int(x[0])
            m=int(x[1])
        if len(x)==3:
            h=int(x[0])
            m=int(x[1])
            s=int(x[2])
        if len(x)==4:
            h=int(x[0])
            m=int(x[1])
            s=int(x[2])
            ms=int(x[3])
        return h,m,s,ms

    timeStr=""
    dateStr=""
    dt=None
    txt=txt.strip()
    rSpace=txt.rfind(' ')
    if rSpace>-1:
        timeStr=txt[rSpace+1:]
        dateStr=txt[:rSpace]
    else:
        dateStr=txt
    d,mo,y=getDt(dateStr)
    h,min,s,ms=getTm(timeStr)
    if h and y:
        dt=datetime.datetime(y,mo,d,h,min,s,ms)
    else:
        if y:
            dt=datetime.datetime(y,mo,d)
    return dt


def getsplit(txt):
    #returns tuple l, r splitting at the comma
    #returns dt (date object) and dy (day of week) if exists
    txt=remove_square_brackets(txt)
    rComma=txt.rfind(",")
    dt=None
    dy=None
    l=''
    r=''
    if rComma>-1:
        l=txt[:rComma]
        r = txt[rComma + 1:].lstrip()
        dt = getdate(r)
        if dt:
            r = makedateUniform(r)
        else:
            r=''
            l=txt

    else:
        l=txt
        r=""
    if dt: dy=getdayofWeek(dt)
    return l,r,dt,dy


def gettextpartDate(txt,options=None):
    #returns the text part of the date i.e. everything after last comma if that everything is a valid date
    txt=remove_square_brackets(txt)
    r=txt[txt.rfind(",")+1:].lstrip()
    return makedateUniform(r)
    #is this a valid date?
    if isValidDate(r,options):
        return makedateUniform(r)
    else:
        return ""


def isValidDate(txt, options=None):
    if dateparser.parse(txt, settings=getSettings(options)):
        return True
    return False

def getSettings(options=None):
    #returns standard settings for parser
    if options:
        if not 'date' in options:
            options['date']='DMY'
    else:
        options={'date': 'DMY'}
    settings={}
    if options['date'] == 'DMY':
        settings = {'DATE_ORDER': 'DMY'}
    elif options['date']=='MDY':
        settings = {'DATE_ORDER': 'MDY'}
    else: #default
        settings = {'DATE_ORDER': 'DMY'}

    settings['REQUIRE_PARTS']=['year']
    settings['PREFER_DAY_OF_MONTH']='first'

    return settings



def getdatefromText(txt, options=None):
    #where txt is in the format "text, 20/12/20 11:00"

    dtTxt=gettextpartDate(txt, options)

    #work around for when there is just a year
    if re.match('^\d{4}$',dtTxt):
        dtTxt="January " +dtTxt

    if not dtTxt=="":
        dt=dateparser.parse(dtTxt, settings=getSettings(options))
        return dt
    else:
        return None

def maketextfromDate(dt):
    #takes a datetime object and makes suitable text
    str=""

    def time_element(dt):
        s = dt.strftime('%S')
        tm_element = dt.strftime("%H:%M:%S")
        if tm_element=="00:00:00":
            return ""
        elif s=="00":
            return dt.strftime("%H:%M")
        else:
            return tm_element


    if dt:
        dt_element=dt.strftime("%d/%m/%Y")
        tm_element=time_element(dt)
        str=dt_element + " " + tm_element

    return str
