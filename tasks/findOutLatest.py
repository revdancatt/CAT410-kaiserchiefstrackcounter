#!/usr/bin/env python
#
# Grab the ID of the latest album from the Album HQ page

import os
import simplejson
import sys

from google.appengine.ext import db
from google.appengine.api import urlfetch
from models import Pointers
from BeautifulSoup import BeautifulSoup
from google.appengine.api.labs import taskqueue
    
# First of all get the pointer number out of pointers
pointers = db.GqlQuery("SELECT * FROM Pointers")

# Find out if we already have the data, if not then we need to make a new
# record and fill it with default data

if pointers.count() == 0:

  # Basic outline of an empty JSON file to hold everything
  trackjson = {
      'tracks' : {},
      'positions': {
        '1': {'tracks': {}},
        '2': {'tracks': {}},
        '3': {'tracks': {}},
        '4': {'tracks': {}},
        '5': {'tracks': {}},
        '6': {'tracks': {}},
        '7': {'tracks': {}},
        '8': {'tracks': {}},
        '9': {'tracks': {}},
        '10': {'tracks': {}}
      }
    }

  pointer = Pointers()
  pointer.pointer = 1064  # we know this is the first album ID from the site
  pointer.json = simplejson.dumps(trackjson)
  pointer.put()

else:

  # yeah, we knows it already
  pointer = pointers[0]
  
# Now go get the URL to find the latest album
# This needs error checking
url = 'http://kaiserchiefs.com/album-gallery'
result = urlfetch.fetch(url=url)

if result.status_code != 200:

  print ''
  print 'hummm, something didn\'t work, sucks :('
  sys.exit()
  

# This also needs error checking
body = BeautifulSoup(result.content)
body.prettify()
  
# extract the tracks from teh album listing
try:

  latestAlbum = int(body.find('section', {'id': 'recent-albums'}).find('a')['href'].split('/')[2])
  pointer.latestAlbum = latestAlbum
  pointer.put()
  print ''
  print latestAlbum

except:

  print ''
  print 'oops'

taskqueue.add(url='/getAlbum', countdown=2, method='GET')