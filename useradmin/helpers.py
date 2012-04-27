"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to templates as 'h'.
"""
# Import helpers as desired, or define your own, ie:
#from webhelpers.html.tags import checkbox, password

import cookielib
import socket
import base64
import cgi
import os
import calendar
import datetime as date

from logging import getLogger
from re import findall
from socket import setdefaulttimeout
from urllib import urlencode
from urllib2 import Request, urlopen, build_opener, install_opener, URLError, HTTPCookieProcessor
from string import Template

from pyramid.config import Configurator
from pyramid.threadlocal import get_current_registry
from pyramid.httpexceptions import HTTPFound

log     = getLogger(__name__)
AGENT   = {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}

__all__ = ['objectAsDict', 'escapeValue', 'escapeValues', 'price', 'number', 'getSettings', 'getSessionData', 'getHttpRequest', 'getStartEnd']

def objectAsDict(obj, dict={}):
    for elem in obj.__dict__.keys():
        if elem.startswith("_"):
            continue
        else:
            dict[elem] = obj.__dict__[elem]
    return dict

def escapeValue(obj, elem=None):
    if elem:
        return cgi.escape(obj.__dict__[elem])
    else:
        return cgi.escape(obj)

def escapeValues(dict={}, elements=[]):
    for elem in elements:
        log.debug('==== elem [%s]'%(elem))
        dict[elem] = escape_value(dict[elem])
    return dict

def price(n):
    if n is None: return "$0.00"
    n = str("%.2f" % float(n))
    negative = False
    n = str(n)
    if '.' in n:
        dollars, cents = n.split('.')
    else:
        dollars, cents = n, None
    if dollars.find("-") >= 0:
      negative = True
      dollars = dollars.replace("-","")
    r = []
    for i, c in enumerate(reversed(str(dollars))):
        if i and (not (i % 3)):
            r.insert(0, ',')
        r.insert(0, c)
    out = "$" + ''.join(r)
    if cents:
        out += '.' + cents[0:2]
    if negative:
        out = '<span style="color: red;">-' + out + '</span>'
    return out

def number(n):
    if n is None: return '0'
    negative = False
    n = str(n)
    if '.' in n:
        number, decimal = n.split('.')
    else:
        number, decimal = n, None
    if number.find("-") >= 0:
      negative = True
      number = number.replace("-","")
      
    r = []
    for i, c in enumerate(reversed(str(number))):
        if i and (not (i % 3)):
            r.insert(0, ',')
        r.insert(0, c)
    out = ''.join(r)
    if decimal:
        out += '.' + decimal[0:2]
    if negative:
        out = '<span style="color: red;">-' + out + '</span>'
    return out

def getStartEnd(start=None, end=None, type='short'):
    if start:
        start = date.datetime.strptime(start, getSettings('date.short'))
        if not end:
            end = start + date.timedelta(days=DAYS)
    if end:
        end = date.datetime.strptime(end, getSettings('date.short'))+date.timedelta(days=1)
        if not start:
            start = end - date.timedelta(days=DAYS)
    start = start.strftime(getSettings('date.%s'%type))
    end   = end.strftime(getSettings('date.%s'%type))
    return start, end

def getSessionData(session=None, key=None):
    if session.has_key(key):
      return session[key]
    return ''

def getSettings(key=None):
    return get_current_registry().settings[key]

def getHttpRequest(uri=None, data=None):
    if data:
        data = urlencode(data)
    setdefaulttimeout(3)
    req   = Request(uri, data, AGENT)
    response = urlopen(req)
    try: content = response.read()
    except Exception, e: print "Failed to content: "%(e.reason)
    return content
