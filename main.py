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
from google.appengine.api import urlfetch
from models import Pointers
from BeautifulSoup import BeautifulSoup

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util


class MainHandler(webapp.RequestHandler):
  def get(self):
    
    # First of all get the pointer number out of pointers
    pointers = db.GqlQuery("SELECT * FROM Pointers")
    trackjson = {}

    if pointers.count() == 0:
      pointer = Pointers()
      pointer.pointer = 2199
      pointer.json = simplejson.dumps(trackjson)
      pointer.put()
    else:
      pointer = pointers[0]
      trackjson = simplejson.loads(pointer.json)
      
    # Now go get the URL...
    # This needs error checking
    url = 'http://kaiserchiefs.com/album/%s' % pointer.pointer
    result = urlfetch.fetch(url=url)

    
    if result.status_code != 200:
      self.response.out.write('No Album ID %s<br />' % pointer.pointer)
      pointer.pointer+=1
      pointer.put()

      self.response.out.write('<br /><a href="/">Next!</a><br /><br /><br />')
      self.response.out.write('<br />You may want to check that we haven\'t run off the end of the albums')
      self.response.out.write('<br />View the <a href="/json">JSON</a> results')
      
      #
      # WARNING
      #
      # Comment out the below line if you don't want to have to click next
      # all the time when there's a missing album
      #
      # But be sure you know what the last album ID is so you can kill it!
#      self.response.out.write('<script>document.location="/"</script>')
      
    else:

      # This also needs error checking
      body = BeautifulSoup(result.content)
      body.prettify()
      
      # extract the tracks from teh album listing
      try:
        album = body.find('div', {'class' : 'secondary-content'}).findAll('li', {'class' : 'clearfix'})
      except:
        print ''
        print pointer.pointer
        print result.status_code
        print body
        sys.exit()
      
      if len(album) == 0:
        self.response.out.write('All done (or there was an error)<br>')
        self.response.out.write('View the <a href="/json">JSON</a> results')
      else:
        
        # Now go thru each one and grab the track id, name, ignore the position for the moment
        self.response.out.write('Album ID %s' % pointer.pointer)
        self.response.out.write('<ol>')
        
        for track in album:
          trackId = track.find('a')['id']
          trackTitle = track.find('span', {'class' : 'track-title'}).contents[0]
          
          self.response.out.write('<li>%s</li>' % trackTitle)
          
          if trackId not in trackjson:
            trackjson[trackId] = {'title': trackTitle, 'count': 1}
          else:
            trackjson[trackId]['count']+=1
          
        self.response.out.write('</ol>')
    
        # Now we need to put it into the database, move the record up one
        pointer.json = simplejson.dumps(trackjson)
        pointer.pointer+=1
        pointer.put()
  
        self.response.out.write('<br />Next!')
        self.response.out.write('<script>document.location="/"</script>')


def main():
  application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
