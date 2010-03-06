#!/usr/bin/env python
import os, cgi, urllib, re, types, math
from random import shuffle
from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from libs.Counter import *
import django.utils.simplejson as json
from datetime import datetime

"""
Models
"""
class Cloud(db.Model):
    stem = db.StringProperty()
    key_list = db.ListProperty(db.Key)
    key_total = db.IntegerProperty()
    word = db.StringProperty()
    word_list = db.ListProperty(unicode)
    size = db.IntegerProperty()

class Store(db.Model):
    name      = db.StringProperty()
    val       = db.TextProperty()
    timestamp = db.DateTimeProperty(auto_now=True)

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

"""
Handlers
"""
class MainHandler(webapp.RequestHandler):

    def get(self):
        if self.request.get('clearcache') == "1":
            memcache.flush_all()
                    
        # Check for a hit in memcache
        html_cache = memcache.get("html")
        if html_cache:
            self.response.out.write(html_cache)
            return
        
        # Fetch words for the word club
        words = Cloud.all().order("word").fetch(100)
        
        # Count up the supporters
        total_supporters = get_count("approved_supporters")
        
        # Fetch all of the organizations
        orgs = []
        supporters = Supporter.all().filter('is_org = ', True).filter('approved = ', True)
        
        for supporter in supporters:
            orgs.append(supporter)
        
        total_orgs = get_count("approved_orgs")
        shuffle(orgs)
        
        template_values = {"orgs": orgs, "total_orgs": total_orgs, "total_supporters": total_supporters, "words": words}
        html = template.render('templates/index.html', template_values)
        
        # Cache for 24 hours. (approvals will clear cache)
        memcache.add("html", html, 86400)
        
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
        
        # Fetch oEmbed response (This is not used at the moment. Using YouTube Direct solution instead.)
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
        
        self.response.headers['Content-Type'] = "text/csv; charset=utf-8"
        self.response.out.write(template.render('templates/csv.html', {"rows": rows}))

class CsvImport(webapp.RequestHandler):
    def get(self):
        """Imports CSV data into local datastore for easier offline development"""
        return # safety first
        import csv
        infile = csv.DictReader(open('csv.csv'), delimiter=',', quotechar='"')
        db.delete(Supporter.all())
        for row in infile:
            timestamp = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            approved = row['approved']
            name = unicode(row['name'])
            address = unicode(row['address'])
            email = unicode(row['email'])
            reason = unicode(row['reason'])
            is_org = row['is_org']
            lat = row['lat']
            lon = row['lon']
            # image = row['image']
            website = unicode(row['website'])
            
            s = Supporter(timestamp=timestamp, name=name, address=address, email=email, reason=reason)
            if(website <> "None"): s.website = website
            # if(image <> "None"): s.image = image
            s.approved = True if approved == "True" else False
            s.is_org = True if is_org == "True" else False
            if lat and lon and lat <> "None" and lon <> "None":
                s.geoloc = db.GeoPt(float(lat),float(lon)) 
            s.put()
        self.response.out.write("Danger averted")

class AdminUnapprovedOrg(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")

        unapproved_org = []
        result = Supporter.all().filter('is_org = ', True).filter('approved = ', False).order("email")
        for row in result:
            unapproved_org.append(row)
        
        self.response.out.write(template.render('templates/admin_unapproved_org.html', {
            "unapproved_org": unapproved_org,
            "logout_url": logout_url,
        }))

class AdminApprovedOrg(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")

        approved_org = []
        result = Supporter.all().filter('is_org = ', True).filter('approved = ', True).order("email")
        for row in result:
            approved_org.append(row)

        self.response.out.write(template.render('templates/admin_approved_org.html', {
            "approved_org": approved_org,
            "logout_url": logout_url,
        }))
        
class AdminApprovedPeople(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")

        approved_people = []
        result = Supporter.all().filter('is_org = ', False).filter('approved = ', True).order("email")
        for row in result:
            approved_people.append(row)

        self.response.out.write(template.render('templates/admin_approved_people.html', {
            "approved_people": approved_people,
            "logout_url": logout_url,
        }))

class AdminUnapprovedPeople(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")
        
        unapproved_people = []
        result = Supporter.all().filter('is_org = ', False).filter('approved = ', False).order("email")
        for row in result:
            unapproved_people.append(row)
            
        self.response.out.write(template.render('templates/admin.html', {
            "unapproved_people": unapproved_people, 
            "logout_url": logout_url,
        }))
    
    def post(self):
        action = cgi.escape(self.request.get('action'))
        return_to = cgi.escape(self.request.get('return'))
        key = cgi.escape(self.request.get('key'))
        if action == "approve":
            row = db.get(key)
            increment("approved_orgs") if row.is_org else increment("approved_supporters")
            row.approved = True
            row.put()
            memcache.flush_all()
        elif action == "unapprove":
            row = db.get(key)
            increment("approved_orgs", -1) if row.is_org else increment("approved_supporters", -1)
            row.approved = False
            row.put()
            memcache.flush_all()
        elif action == "delete":
            row = db.get(key)
            row.delete()
            memcache.flush_all()
        self.redirect(return_to)



class AdminInitCounters(webapp.RequestHandler):
    """Zeros and recomputes counters."""
    def get(self):
        
        # Reset counters
        reset_count("approved_supporters")
        reset_count("approved_orgs")
        
        approved = 0
        approved_orgs = 0

        self.response.out.write("approved: %d<br>" % approved)
        self.response.out.write("approved counter: %s<br>" % get_count("approved_supporters"))
        self.response.out.write("approved_orgs: %d<br>" % approved_orgs)
        self.response.out.write("approved_orgs counter: %s<br>" % get_count("approved_orgs"))

        q = Supporter.all(keys_only=True).filter('is_org = ', False).filter('approved = ', True)
        for row in q:
            approved += 1
            
        q = Supporter.all(keys_only=True).filter('is_org = ', True).filter('approved = ', True)
        for row in q:
            approved_orgs += 1
        
        increment("approved_supporters", approved)
        increment("approved_orgs", approved_orgs)
        self.response.out.write("approved: %d<br>" % approved)
        self.response.out.write("approved counter: %s<br>" % get_count("approved_supporters"))
        self.response.out.write("approved_orgs: %d<br>" % approved_orgs)
        self.response.out.write("approved_orgs counter: %s<br>" % get_count("approved_orgs"))

class UpdateCloud(webapp.RequestHandler):
    """Sift through user generated reasons and extract keywords."""
    def sortfunc(self, x, y):
        return cmp(y[1], x[1])

    def size_words(self, steps, input):
        """This is pulled from Chase Davis (http://www.chasedavis.com/2007/feb/11/word-stemming-tag-clouds/)"""
        if not type(input) == types.ListType or len(input) <= 0 or steps <= 0:
            raise Exception("Please be sure steps > 0 and your input list is not empty.")
        else:
            temp, newThresholds, results = [], [], []
            for item in input:
                if not type(item) == types.TupleType:
                    raise InvalidInputException("Be sure input list holds tuples.")
                else: temp.append(item[1])
            maxWeight = float(max(temp))
            minWeight = float(min(temp))
            newDelta = (maxWeight - minWeight)/float(steps)
            for i in range(steps + 1):
               newThresholds.append((100 * math.log((minWeight + i * newDelta) + 2), i))
            for tag in input:
                fontSet = False
                for threshold in newThresholds[1:int(steps)+1]:
                    if (100 * math.log(tag[1] + 2)) <= threshold[0] and not fontSet:
                        results.append(dict({str(tag[0]):str(threshold[1])}))
                        fontSet = True
            return results

    def get(self):
        from libs.stoplist import stoplist
        from libs.PorterStemmer import PorterStemmer
        stemmer = PorterStemmer()
        punctuation = re.compile(r'[.?\'!,":;&\-\+=]*')
        stems = {}
        base_text_size = int(cgi.escape(self.request.get('base_text_size', "12")))
        min_freq = int(cgi.escape(self.request.get('min_freq', "5")))
        target_keyword_count = int(cgi.escape(self.request.get('target_keyword_count', "21")))
        
        for row in Supporter.all().filter("approved = ", True).filter("is_org = ", False):
            corpus = row.reason
            # Strip puntuation and "&quot"
            corpus = punctuation.sub('', corpus)
            corpus = corpus.replace("&quot", "")
            corpus = corpus.replace("/", " ")
            corpus = corpus.replace("(", " ")
            corpus = corpus.replace(")", " ")
            corpus = corpus.replace("\\", " ")
        
            # Tokenize
            tokens = re.split('\s+', corpus.lower().strip())
            for token in tokens:
                if token in stoplist or token == "":
                    continue
                stem = stemmer.stem(token, 0, len(token)-2)
                try:
                    stems[stem]["keys"].add(row.key())
                    stems[stem]["words"].add(token)
                except:
                    stems[stem] = {}
                    stems[stem]["keys"] = set([row.key()])
                    stems[stem]["words"] = set([token])
        
        # cleanup extra keys and build tuple list for sizing function
        for stem in stems.keys():
            stems[stem]["words"] = list(stems[stem]["words"])
            stems[stem]["word"] = stems[stem]["words"].pop() # This grabs a random word
            stems[stem]["keys"] = list(stems[stem]["keys"])
            stems[stem]["key_total"] = len(stems[stem]["keys"])

            # This is where we set the cutoff for min frequency required to be in the cloud
            if stems[stem]["key_total"] < min_freq: del(stems[stem])
        
        # We want a list of 20 keywords, so continue upping the min_freq until the list is 20 or less
        while len(stems.keys()) > target_keyword_count:
            min_freq += 1
            for stem in stems.keys():
                if stems[stem]["key_total"] < min_freq: del(stems[stem])
            
        
        # Create a tuple of items for the sizing function
        sized_tuple = [(stem, stems[stem]["key_total"]) for stem in stems]
        
        # Get a list of stems with a relative size and add that size to the stems dictionary
        sized_stems = self.size_words(12, sized_tuple)
        for item in sized_stems:
            stem = item.keys().pop()
            stems[stem]["size"] = int(item[stem]) + base_text_size
        
        # Make some cloud row objects
        cloud_rows = []
        for stem, data in stems.items():
            row = Cloud(stem=stem, key_total=data['key_total'], size=data['size'], 
                        word=data['word'], key_list=data['keys'], word_list=data['words'])
            cloud_rows.append(row)
            self.response.out.write("%s: %s <br/>" % (data['word'], data['key_total']))

        # Update the Cloud table
        if len(cloud_rows):
            db.delete(Cloud.all())
            db.put(cloud_rows)
            self.response.out.write("Updated %s rows" % len(cloud_rows))
        else: 
            self.response.out.write("I didn't update the table because I didn't have any rows to update.")
        

class ApiSupporters(webapp.RequestHandler):
    """Expose supporter data as JSON over a REST api. Used by the map and public api."""
    def formatSupporter(self, supporter, loc=False):
        data = {
            "name": supporter.name, 
            "reason": supporter.reason, 
            "date": supporter.timestamp.strftime("%B %d, %Y"),
            "datetime": supporter.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        if loc and not supporter.is_org: 
            data['geoloc'] = "%.5f, %.5f" % (supporter.geoloc.lat, supporter.geoloc.lon)
            data['location'] = supporter.address
        return data
    
    def get(self):
        self.response.headers['Content-Type'] = "application/javascript; charset=utf-8"
        
        # Set default params
        limit = 10
        offset = 0
        markers = False
        word = False
        pprint = False
        app_id = "None"
        app_email = "None"
        
        # Get passed params
        try:
            if self.request.get('limit'):
                limit = int(self.request.get('limit'))                
                if limit > 1001 or limit < 1:
                    raise Exception("limit out of range")
            
            if self.request.get('offset'):
                offset = int(self.request.get('offset'))
                if offset > 5000 or offset < 0:
                    raise Exception("offset out of range")

            if self.request.get('word'):
                if re.match("^[a-z]{2,18}$", self.request.get('word')):
                    word = self.request.get('word')
                else:
                    raise Exception("word may only contain 2 to 18 lowercase letters")
            
            if self.request.get('markers'):
                if self.request.get('markers') not in ["true", "false"]:
                    raise Exception("markers must be 'true' or 'false'")
                if self.request.get('markers') == "true":
                    markers = True
                    
            if self.request.get('pprint'):
                if self.request.get('pprint') not in ["true", "false"]:
                    raise Exception("pprint must be 'true' or 'false'")
                if self.request.get('pprint') == "true":
                    pprint = True

        except Exception, e:
            self.error(400)
            resp = {"error": True, "message": e.message}
            self.response.out.write(json.dumps(resp, indent=2))
            return
        
        # Look for a cache hit
        cache_key = "api/supporters?limit=%s&offset=%s&markers=%sword=%s" % (limit, offset, markers, word)
        resp = memcache.get(cache_key)
        if resp:
            resp['metadata']['from_cache'] = True
            if pprint:
                self.response.out.write(json.dumps(resp, indent=2))
            else:
                self.response.out.write(json.dumps(resp))
            return
        
        # Setup variables
        start = datetime.now()
        data = []
        total_supporters = 0
        if word:
            key_list = Cloud.all().filter('word = ', word).get().key_list[:limit]
            result = db.get(key_list)
        else:
            query = Supporter.all().filter('approved = ', True).filter('is_org = ', False).order('-timestamp')        
            # Try to fetch some results
            try:
                result = query.fetch(limit, offset)
            except Exception, e:
                self.error(400)
                resp = {"error": True, "message": e.message}
                self.response.out.write(json.dumps(resp))
                return
        
        # Group supporters by location and return data for map markers
        if markers:
            marks = {}
            for row in result:
                total_supporters += 1
                key = "%.3f, %.3f" % (row.geoloc.lat, row.geoloc.lon)
                if key in marks:
                    marks[key]['count'] += 1
                    marks[key]['supporters'].append(self.formatSupporter(row))
                else:
                    marks[key] = {}
                    marks[key]['count'] = 1
                    marks[key]['supporters'] = [self.formatSupporter(row)]
                    
            # convert into a list of objects (Should probably be a list comprehension)
            for k, v in marks.items():
                v['location'] = k
                data.append(v)
        else:
            for row in result:
                total_supporters += 1
                data.append(self.formatSupporter(row, loc=True))
        
        # Setup response object
        resp = {
            "error": False,
            "metadata": {
                "total_supporters": total_supporters,
                "from_cache": False,
                "process_time": str(datetime.now() - start),
                "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "data": data
        }
        
        if markers:
            resp['metadata']['total_markers'] = len(marks)
        
        # Cache for 24 hours. (approvals will clear cache)
        memcache.add(cache_key, resp, 86400)
        
        # Respond with JSON
        if pprint:
            self.response.out.write(json.dumps(resp, indent=2))
        else:
            self.response.out.write(json.dumps(resp))

def main():
    urls = [ ('/', MainHandler),  
             ('/admin/csv', CsvOutput), 
             # ('/admin/csvimport', CsvImport), 
             ('/admin', AdminUnapprovedPeople),
             ('/admin/', AdminUnapprovedPeople),
             ('/admin/approvedpeople', AdminApprovedPeople),
             ('/admin/approvedorgs', AdminApprovedOrg),
             ('/admin/unapprovedorgs', AdminUnapprovedOrg),
             ('/admin/initcounters', AdminInitCounters),
             ('/admin/updatecloud', UpdateCloud),
             ('/api/supporters', ApiSupporters),
           ]
    util.run_wsgi_app(webapp.WSGIApplication(urls, debug=True))

if __name__ == '__main__':
    main()