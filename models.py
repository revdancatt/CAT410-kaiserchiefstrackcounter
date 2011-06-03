#!/usr/bin/env python
from google.appengine.ext import db

class Pointers(db.Model):
  json              = db.TextProperty()
  pointer           = db.IntegerProperty(default=0)
