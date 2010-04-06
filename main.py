#!/usr/bin/env python
#
# Luzifer Altenberg, luzifer@atomgas.de
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

METHOD_OVERRIDE_HEADER = 'X-HTTP-Method-Override'

import os, hmac, yaml, base64, hashlib, logging 

 

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util                      
from google.appengine.ext.webapp import template 

from models import Attachment
  
  
settings = yaml.load(open(os.path.join(os.path.dirname(__file__), 'settings.yaml')))     
 
def authorization_required(func):
  def callf(webappRequest, *args, **kwargs):       
    authHeader = webappRequest.request.headers.get('Authorization')
    
    if authHeader == None:
      webappRequest.response.set_status(401, message="Authorization Required")
    else:
      auth_parts = authHeader.split(' ')
      token_signature_parts = base64.b64decode(auth_parts[1]).split(':')
      token = token_signature_parts[0]
      signature = token_signature_parts[1]            
      if hmac.new(settings['shared_secret'], token, hashlib.sha256).hexdigest() != signature:  
        webappRequest.response.set_status(401, message="Authorization Required")      
      else:
        return func(webappRequest, *args, **kwargs)
  
  return callf      
  
  
class AttachmentGetByAttachmentIdHandler(webapp.RequestHandler):      

  def get(self, attachment_id, filename = None): 
    '''
    get attachment by nice url
    /attachment_id/[filename.ext]
    '''                                  
    attachment = Attachment.gql("WHERE attachment_id = :1", 
                                attachment_id).get()    
    if attachment:
      self.response.headers['Content-Type'] = attachment.content_type
      self.response.out.write( attachment.data ) 
    else:
      self.error(404)   
      
  def head(self, attachment_id, filename = None):    
    """allows to check if attachment exitsts?"""  
    
    attachment = Attachment.gql("WHERE attachment_id = :1", 
                                attachment_id).get()    
    if attachment:
      self.response.headers['Content-Type'] = attachment.content_type
      self.response.set_status(200)
    else:
      self.error(404)       

class AttachmentHandler(webapp.RequestHandler):  
  def get(self):
    """get attachment by key"""
    if self.request.get("key", None):
      attachment = Attachment.get(self.request.get("key"))
      if attachment:
        self.response.headers['Content-Type'] = attachment.content_type
        self.response.set_status(200)
      else:
        self.error(404)
    else:
      self.response.out.write("Paperclip storage engine")   

  @authorization_required
  def post(self):         
    """create attachment or update attachment for given attachment_id"""     
    
    logging.info("POST: _method:%s attachment_id: %s" % (self.request.get("_method"), self.request.get("attachment_id")))
     
    _method = self.request.headers.get(METHOD_OVERRIDE_HEADER, None)
    if _method == 'DELETE':
      self.handle_delete()        
    else:    
      self.do_delete()
      attachment = Attachment(attachment_id = self.request.get("attachment_id"),
                              content_type = self.request.get("content_type"),
                              data = self.request.get("data"))   
      attachment.put()

      # return xml
      path = os.path.join(os.path.dirname(__file__), 'templates','attachment.xml')
      self.response.out.write(template.render(path, {'attachment': attachment}))      
      
  def handle_delete(self): 
    if self.do_delete():
      self.response.set_status(200)      
    else:
      self.error(404) 

  def do_delete(self):
   attachment = Attachment.gql('WHERE attachment_id = :1', self.request.get("attachment_id")).get()
   if attachment:
     attachment.delete()
     return True
   else:
     return False
     

def main():
  application = webapp.WSGIApplication([
                                        ('/', AttachmentHandler),
                                        (r'/([^\/]+)(.*)', AttachmentGetByAttachmentIdHandler)
                                       ],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
