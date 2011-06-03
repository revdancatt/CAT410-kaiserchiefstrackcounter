#!/usr/bin/env python
#
# Code to grab the tracks used in user created albums on the Kaiser Chief's
# website
#
# Quickly hacked together with not enough error checking
#
import simplejson
from google.appengine.ext import db
from models import Pointers



# First of all get the pointer number out of pointers
pointers = db.GqlQuery("SELECT * FROM Pointers")

print 'Content-Type: application/json; charset=UTF-8'
print ''
print pointers[0].json
