#!/usr/bin/env python

from google.appengine.ext import db

class Attachment(db.Model):
  """Represents an attachment stored in the datastore"""
  
  # unique attachment_id, when used with paperclip
  # concatenated <table_name>_<attachment>_<id>_<style> (eg: users_image_23) 
  attachment_id = db.StringProperty(required=True)
  # content type
  content_type = db.StringProperty(required=True)
  # blob properties storing up to 1MB of binary data
  data = db.BlobProperty(required=True)
