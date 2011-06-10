#!/usr/bin/env python
#
# Code to grab the tracks used in user created albums on the Kaiser Chief's
# website
#
# Quickly hacked together with not enough error checking
#
#
# When running make a note of the most recent album on this page...
# http://www.kaiserchiefs.com/album-gallery
# On the bottom left, 5 small thumbnails with "Recently created albums" underneaths

import os
import simplejson
import sys
import logging

from google.appengine.ext import db
from google.appengine.api import urlfetch
from models import Pointers, Albums
from BeautifulSoup import BeautifulSoup
from google.appengine.api.labs import taskqueue

# First of all get the pointer number out of pointers
pointers = db.GqlQuery("SELECT * FROM Pointers")
trackjson = {}

if pointers.count() == 0:
  print ''
  print 'we dont have a pointers record yet, we should let tasks/findOutLatest run first to create it'
  sys.exit()
  
# grab the record
status = pointers[0]
  
# check to see if the current pointer is > than the latestAlbum if so then
# we need to stop and wait until it's time to try again
if status.pointer > status.latestAlbum:
  status.pointer = status.latestAlbum + 1
  status.put()
  
  print ''
  print 'we have finished for the moment, no new albums to fetch'
  sys.exit()
  

# Ok, we need to go and get a new record, let's do that now  
url = 'http://kaiserchiefs.com/album/%s' % status.pointer
result = urlfetch.fetch(url=url)


# If we have gotten back any page but a 200, then we want to skip over to the
# next record


if result.status_code != 200:

  print ''
  print '<h1>No Album ID %s</h1>' % status.pointer

  status.pointer+=1
  status.put()

else:

  ##############################################################################
  # NOTE
  #
  # I'm *not* putting error trapping around this as I want it to throw an error
  # so I can see it in the Dashboard, rather than silently logging it
  # Once I've seen a few errors I can think about what types I want to catch
  # and what to do with them
  #
  ##############################################################################



  # Ok we have got back a 200, that's good, we want to work with that now  

  body = BeautifulSoup(result.content)
  body.prettify()
  
  
  # extract the tracks from teh album listing
  album = body.find('div', {'class' : 'secondary-content'}).findAll('li', {'class' : 'clearfix'})
    
  if len(album) == 0:
    print ''
    print '<h1>No tracks found for Album ID %s</h1>' % status.pointer
  else:
    
    # Now go thru each one and grab the track id, name, ignore the position for the moment

    # Get the track JSON
    trackjson = simplejson.loads(status.json)
    
    oldTrack = {
      'id': 0,
      'name': '',
    }
    
    albumJSON = {}
    
    for track in album:

      # make a newTrack object, which is the default that can be used
      newTrack = {
        'id'        : str(track.find('a')['id']),
        'name'      : str(track.find('span', {'class' : 'track-title'}).contents[0]),
        'count'     : 0,
        'positions' : {
          '1'   : 0,
          '2'   : 0,
          '3'   : 0,
          '4'   : 0,
          '5'   : 0,
          '6'   : 0,
          '7'   : 0,
          '8'   : 0,
          '9'   : 0,
          '10'  : 0,
        },
        'followers': {
        }
      }
      
      # and we want to which position it's in
      position = track.find('span', {'class' : 'track-number'}).contents[0]

      albumJSON[position] = {'id': newTrack['id'], 'name': newTrack['name']}
      
      # Now we want to add the track to the tally count in the JSON
      if newTrack['id'] not in trackjson['tracks']:
        trackjson['tracks'][newTrack['id']] = newTrack

      # now add one to the counters
      trackjson['tracks'][newTrack['id']]['count']+= 1
      trackjson['tracks'][newTrack['id']]['positions'][position]+= 1
      
      
      #
      # We also want to put it into the overall position tally
      #
      if newTrack['id'] not in trackjson['positions'][position]['tracks']:
        trackjson['positions'][position]['tracks'][newTrack['id']] = {
                                                                      'id': newTrack['id'],
                                                                      'name': newTrack['name'],
                                                                      'count': 1
                                                                      }
      else:
        trackjson['positions'][position]['tracks'][newTrack['id']]['count']+=1
        
      
      #
      # Finaly we want to keep track if which tracks tend to follow each other
      #
      if oldTrack['id'] != 0:
        if newTrack['id'] not in trackjson['tracks'][oldTrack['id']]['followers']:
          trackjson['tracks'][oldTrack['id']]['followers'][newTrack['id']] = {
                                                                      'id': newTrack['id'],
                                                                      'name': newTrack['name'],
                                                                      'count': 1
          }
        else:
          trackjson['tracks'][oldTrack['id']]['followers'][newTrack['id']]['count']+=1
        
      oldTrack = newTrack

    
    # Get the name of the album, and the number of purchases for this album
    name = str(body.find('div', {'role' : 'main'}).find('h1').contents[0].replace(' album', '').replace('\'s', '').replace('\'',''))
    purchases = body.find('aside', {'id' : 'statistics'}).find('li', {'class': 'purchases'}).find('span').contents[0]
    cover = body.find('div', {'class': 'primary-content'}).find('img')['src'].split('/')
    cover.reverse()
    cover = cover[0]
    
    
    # And add the album
    album = Albums()
    album.id                = status.pointer
    album.name              = unicode(name, 'utf-8')
    album.purchases         = int(purchases)
    album.cover             = cover
    album.track1            = albumJSON['1']['id']
    album.track1name        = albumJSON['1']['name']
    album.track2            = albumJSON['2']['id']
    album.track2name        = albumJSON['2']['name']
    album.track3            = albumJSON['3']['id']
    album.track3name        = albumJSON['3']['name']
    album.track4            = albumJSON['4']['id']
    album.track4name        = albumJSON['4']['name']
    album.track5            = albumJSON['5']['id']
    album.track5name        = albumJSON['5']['name']
    album.track6            = albumJSON['6']['id']
    album.track6name        = albumJSON['6']['name']
    album.track7            = albumJSON['7']['id']
    album.track7name        = albumJSON['7']['name']
    album.track8            = albumJSON['8']['id']
    album.track8name        = albumJSON['8']['name']
    album.track9            = albumJSON['9']['id']
    album.track9name        = albumJSON['9']['name']
    album.track10            = albumJSON['10']['id']
    album.track10name        = albumJSON['10']['name']
    album.put()
    
    # Now we need to put it into the database, move the record up one
    status.json = simplejson.dumps(trackjson)
    status.pointer+=1
    status.put()

    print 'Content-Type: application/json; charset=UTF-8'
    print ''
    print simplejson.dumps(trackjson)

# Now we need to put the thing back into the task queue so it can run again
taskqueue.add(url='/getAlbum', countdown=2, method='GET')