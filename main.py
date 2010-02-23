#!/usr/bin/env python

import os, cgi, urllib
from random import shuffle
from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import django.utils.simplejson as json

class Supporter(db.Model):
    name        = db.StringProperty(required=True)
    address     = db.PostalAddressProperty()
    geoloc      = db.GeoPtProperty()
    email       = db.EmailProperty()
    website     = db.LinkProperty()
    image       = db.StringProperty()
    video_url   = db.LinkProperty()
    video_embed = db.StringProperty()
    reason      = db.StringProperty()
    is_org      = db.BooleanProperty(default=False)
    approved    = db.BooleanProperty(default=False)
    timestamp   = db.DateTimeProperty(auto_now_add=True)

class MainHandler(webapp.RequestHandler):

    def get(self):
        if self.request.get('clearcache') == "1":
            memcache.flush_all()
                    
        # Check for a hit in memcache
        html_cache = memcache.get("html")
        if html_cache:
            self.response.out.write(html_cache)
            return

        # Fetch all of the markers
        markers = []
        supporters = Supporter.all().filter('is_org = ', False).filter('approved = ', True)
        for supporter in supporters:
            markers.append(supporter)
        
        # Fetch all of the organizations
        orgs = []
        supporters = Supporter.all().filter('is_org = ', True).filter('approved = ', True)
        
        for supporter in supporters:
            orgs.append(supporter)
        
        shuffle(orgs)
        
        template_values = {"markers": markers, "orgs": orgs, "total_marks": len(markers) }
        template_file = os.path.join(os.path.dirname(__file__), 'index.html')
        html = template.render(template_file, template_values)
        
        # Cache for 30 minutes
        memcache.add("html", html, 1800)
        
        self.response.out.write(html)

    def post(self):
        name        = cgi.escape(self.request.get('name'), True)
        reason      = cgi.escape(self.request.get('reason'), True)
        address     = cgi.escape(self.request.get('address'), True)
        geolat      = float(self.request.get('geolat', 0))
        geolng      = float(self.request.get('geolng', 0))
        email       = cgi.escape(self.request.get('email'), True)
        website     = self.request.get('website')
        video_url   = self.request.get('video_url')
        is_org      = cgi.escape(self.request.get('is_org'), True)
        
        # Fetch oEmbed response
        video_embed = None
        if video_url:
            url = "http://www.youtube.com/oembed?url=%s&format=json&maxwidth=%d" % (urllib.quote(video_url), 200)
            result = urlfetch.fetch(url)
            if result.status_code == 200:
                resp = json.loads(result.content)
                video_embed = resp['html']
        
        s = Supporter(name=name, reason=reason, is_org=True, image="")
        if email:       s.email = db.Email(email)
        if website:     s.website = db.Link(website)
        if video_url:   s.video_url = db.Link(video_url)
        if video_embed: s.video_embed = video_embed
        
        if is_org == "no":
            s.address = db.PostalAddress(address)
            s.geoloc  = db.GeoPt(geolat, geolng)
            s.is_org  = False

        key = s.put()
        
        subject = "New Supporter: %s" % name
        to_email = "jonlesser@gmail.com"
        from_email = "jonlesser@gmail.com"
        body = """
            Name: %s
            Address: %s
            email: %s
            reason: %s
            website: %s
            Org: %s
            
            http://www.bmorefiber.com/admin
            """ % (name, address, email, reason, website, is_org)
        mail.send_mail(from_email, to_email, subject, body)
        
        self.response.out.write("Post Worked")

class CsvOutput(webapp.RequestHandler):
    def get(self):
        rows = []
        result = Supporter.all()
        for row in result:
            if row.name: row.name = row.name.replace('"','""')
            if row.address: row.address = row.address.replace('"','""')
            if row.reason: row.reason = row.reason.replace('"','""')
            if row.website: row.website = row.website.replace('"','""')
            rows.append(row)
        
        self.response.headers.add_header("Content-Type", "text/csv")
        self.response.out.write(template.render('csv.html', {"rows": rows}))

class Moderate(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")
        
        unapproved_people = []
        result = Supporter.all().filter('is_org = ', False).filter('approved = ', False)
        for row in result:
            unapproved_people.append(row)
        
        unapproved_org = []
        result = Supporter.all().filter('is_org = ', True).filter('approved = ', False)
        for row in result:
            unapproved_org.append(row)
        
        approved_people = []
        result = Supporter.all().filter('is_org = ', False).filter('approved = ', True)
        for row in result:
            approved_people.append(row)
            
        approved_org = []
        result = Supporter.all().filter('is_org = ', True).filter('approved = ', True)
        for row in result:
            approved_org.append(row)
            
        self.response.out.write(template.render('admin.html', {
            "unapproved_people": unapproved_people, 
            "unapproved_org": unapproved_org,
            "approved_people": approved_people,
            "approved_org": approved_org,
            "logout_url": logout_url,
        }))
    
    def post(self):
        action = cgi.escape(self.request.get('action'))
        key = cgi.escape(self.request.get('key'))
        if action == "approve":
            row = db.get(key)
            row.approved = True
            row.put()
            memcache.flush_all()
        elif action == "unapprove":
            row = db.get(key)
            row.approved = False
            row.put()
            memcache.flush_all()
        elif action == "delete":
            row = db.get(key)
            row.delete()
            memcache.flush_all()
        self.redirect("/admin/")

def main():
    urls = [ ('/', MainHandler), 
             ('/admin/csv/', CsvOutput), 
             ('/admin/csv', CsvOutput), 
             ('/admin/', Moderate),
             ('/admin', Moderate),
           ]
    util.run_wsgi_app(webapp.WSGIApplication(urls, debug=True))

if __name__ == '__main__':
    main()