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

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from models import Pointers, Albums

class MainPage(webapp.RequestHandler):
  def get(self):

    
    # First of all get the pointer number out of pointers
    pointers = db.GqlQuery("SELECT * FROM Pointers")
    
    if pointers.count() == 0:
      print ''
      print 'we dont have a pointers record yet, we should let tasks/findOutLatest run first to create it'
      sys.exit()
      
    # grab the record
    status = pointers[0]
    json = simplejson.loads(status.json)
    
    # Cant be bothered to sort properly so lets do it the dufus way
    scores = []
    totalTracks = 0
    
    for track in json['tracks']:
      thisTrack = json['tracks'][track]
      totalTracks+=int(thisTrack['count'])
      if thisTrack['count'] not in scores:
        scores.append(thisTrack['count'])
        
    scores.sort()
    scores.reverse()
    
    counter = 1
    tracksOrdered = []
    trackNames = []
    
    topPositionMaxCount = 0.0
    topFollowMaxCount = 0.0

    #
    # put all the scores stuff together
    #
    for score in scores:
      for track in json['tracks']:
        thisTrack = json['tracks'][track]
        if thisTrack['count'] == score:
          
          trackNames.append(thisTrack['name'])
          
          # Work out which position on the album this track normally appears in
          maxCount = 0
          topPosition = 0
          for posCount in thisTrack['positions']:
            thisCount = thisTrack['positions'][posCount]

            if thisCount > maxCount:
              maxCount = thisCount
              topPosition = posCount

            # get the overall top position
            if thisCount > topPositionMaxCount:
              topPositionMaxCount = thisCount
              
          thisTrack['topPosition'] = str(topPosition)
          thisTrack['maxCount'] = maxCount
          

          # Work out which track normally follows this one
          maxCount = 0
          topTrack = 0
          topTrackId = ''
          
          for follower in thisTrack['followers']:
            thisFollower = thisTrack['followers'][follower]

            if thisFollower['count'] > maxCount:
              maxCount = thisFollower['count']
              topTrack = thisFollower['name']
              topTrackId = thisFollower['id']
              
            # get the overall top position
            if thisFollower['count'] > topFollowMaxCount:
              topFollowMaxCount = thisFollower['count']

          
          thisTrack['topFollower'] = topTrack
          thisTrack['topFollowerId'] = topTrackId
          thisTrack['maxFollowerCount'] = maxCount
          

          tracksOrdered.append(thisTrack)
          

    # Now go thru the ordered track, putting the % values in for the positions
    for track in tracksOrdered:
      winningPositions = []
      for i in range(1,11):
        if str(i) in track['positions']:
          winningPosition = {'position': i, 'count': track['positions'][str(i)], 'percent': int(float(track['positions'][str(i)]) / topPositionMaxCount * 100)}
          winningPositions.append(winningPosition)
          
      track['winningPositions'] = winningPositions
          
    # Do the same again for following stuff
    trackNames.sort()
    for track in tracksOrdered:
      winningPositions = []
      for trackName in trackNames:
        foundMatch = False
        for follower in track['followers']:
          thisFollower = track['followers'][follower]
          if trackName in thisFollower['name']:
            foundMatch = True
            winningPosition = {'id': thisFollower['id'], 'name': thisFollower['name'], 'count': thisFollower['count'], 'percent': int(float(thisFollower['count']) / topFollowMaxCount * 100)}
            winningPositions.append(winningPosition)
      
        if foundMatch == False:
          trackThingy = ''
          for zerotrack in tracksOrdered:
           if zerotrack['name'] == trackName:
              trackThingy = zerotrack['id']

          winningPosition = {'id': trackThingy, 'name': trackName, 'count': 0, 'percent': 0}
          winningPositions.append(winningPosition)
        
      track['winningFollows'] = winningPositions
    

    #
    # I want to put the "winning" track for each position in here
    #
    
    totalPositionMaxCount = 0
    
    for position in json['positions']:
      thisPosition = json['positions'][position]

      maxCount = 0
      maxTrack = ''
      
      for track in thisPosition['tracks']:
        thisTrack = thisPosition['tracks'][track]

        if thisTrack['count'] > maxCount:
          maxCount = thisTrack['count']
          maxTrack = thisTrack['id']
      
        if thisTrack['count'] > totalPositionMaxCount:
          totalPositionMaxCount = thisTrack['count']
      
      thisPosition['maxCount'] = maxCount
      thisPosition['maxTrack'] = maxTrack

    
    # now I want to sort them so lets put them into an array
    sortedPositions = []
    for pos in range(1,11):
      thisPosition = json['positions'][str(pos)]
      for track in thisPosition['tracks']:
        thisTrack = thisPosition['tracks'][track]
        thisTrack['percent'] = int(float(thisTrack['count'])/totalPositionMaxCount*100)
        
      sortedPositions.append(thisPosition)
      
    albums = db.GqlQuery("SELECT * FROM Albums WHERE purchases > 1")
    extras = 0
    for album in albums:
      extras+=album.purchases
      
    extras-=albums.count()
    

    
    template_values = {
      'current': status.pointer,
      'last': status.latestAlbum,
      'tracksOrdered': tracksOrdered,
      'trackNames': trackNames,
      'totalTracks': totalTracks,
      'totalAlbums': totalTracks/10,
      'totalSold': (totalTracks/10)+extras,
      'data': json,
      'trackrange': ['1','2','3','4','5','6','7','8','9','10'],
      'sortedPositions': sortedPositions,
    }

    path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
    self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('.*', MainPage)],
                                     debug=True)
    
def main():
  webapp.template.register_template_library('django.contrib.humanize.templatetags.humanize')
  run_wsgi_app(application)

  
if __name__ == "__main__":
  main()