#!/usr/bin/env python
from libs.PorterStemmer import PorterStemmer
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
import django.utils.simplejson as json
from datetime import datetime

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
        markers = {}
        total_supporters = 0
        supporters = Supporter.all().filter('is_org = ', False).filter('approved = ', True)
        for supporter in supporters:
            total_supporters += 1
            key = "%.3f, %.3f" % (supporter.geoloc.lat, supporter.geoloc.lon)
            if key in markers:
                markers[key]['total'] += 1
                markers[key]['data'].append({"name":supporter.name, "reason": supporter.reason, "date":supporter.timestamp})
                if markers[key]['total'] > 99:
                    markers[key]['lots'] = True
            else:
                markers[key] = {}
                markers[key]['total'] = 1
                markers[key]['data'] = [{"name":supporter.name, "reason": supporter.reason, "date":supporter.timestamp}]
                markers[key]['lots'] = False
        
        # if total_supporters > 200:
        #     markers = markers[len(markers)-200:len(markers)]
        
        # Fetch all of the organizations
        orgs = []
        supporters = Supporter.all().filter('is_org = ', True).filter('approved = ', True)
        
        for supporter in supporters:
            orgs.append(supporter)
        
        total_orgs = len(orgs)
        shuffle(orgs)
        
        template_values = {"markers": markers, "orgs": orgs, "total_orgs": total_orgs, "total_supporters": total_supporters}
        template_file = os.path.join(os.path.dirname(__file__), 'index.html')
        html = template.render(template_file, template_values)
        
        # Cache for 6 hours. (approvals will clear cache)
        memcache.add("html", html, 21600)
        
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

class AdminUnapprovedOrg(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")

        unapproved_org = []
        result = Supporter.all().filter('is_org = ', True).filter('approved = ', False)
        for row in result:
            unapproved_org.append(row)
        
        self.response.out.write(template.render('admin_unapproved_org.html', {
            "unapproved_org": unapproved_org,
            "logout_url": logout_url,
        }))

class AdminApprovedOrg(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")

        approved_org = []
        result = Supporter.all().filter('is_org = ', True).filter('approved = ', True)
        for row in result:
            approved_org.append(row)

        self.response.out.write(template.render('admin_approved_org.html', {
            "approved_org": approved_org,
            "logout_url": logout_url,
        }))
        
class AdminApprovedPeople(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")

        approved_people = []
        result = Supporter.all().filter('is_org = ', False).filter('approved = ', True)
        for row in result:
            approved_people.append(row)

        self.response.out.write(template.render('admin_approved_people.html', {
            "approved_people": approved_people,
            "logout_url": logout_url,
        }))

class AdminUnapprovedPeople(webapp.RequestHandler):
    def get(self):
        logout_url = users.create_logout_url("/")
        
        unapproved_people = []
        result = Supporter.all().filter('is_org = ', False).filter('approved = ', False)
        for row in result:
            unapproved_people.append(row)
            
        self.response.out.write(template.render('admin.html', {
            "unapproved_people": unapproved_people, 
            "logout_url": logout_url,
        }))
    
    def post(self):
        action = cgi.escape(self.request.get('action'))
        return_to = cgi.escape(self.request.get('return'))
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
        self.redirect(return_to)

class MakeCloud(webapp.RequestHandler):
    def sortfunc(self, x, y):
        return cmp(y[1], x[1])

    def makeCloud(self, steps, input):
        if not type(input) == types.ListType or len(input) <= 0 or steps <= 0:
            raise InvalidInputException,\
                  "Please be sure steps > 0 and your input list is not empty."
        else:
            temp, newThresholds, results = [], [], []
            for item in input:
                if not type(item) == types.TupleType:
                    raise InvalidInputException, "Be sure input list holds tuples."
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
        stoplist = [   
                    "verizon", "comcast", "fios", "baltimore", "city", "i", "a", 
                    "about", "an", "are", "as", "at", "be", "because", "by", "com", 
                    "for", "from", "how", "in", "internet", "is", "it", "of", "on", 
                    "or", "tech", "that", "the", "this", "to", "was", "what", "when", 
                    "where", "who", "will", "with", "www", "and", "like", "we", "would",
                    "have", "has", "more", "our", "high", "all", "not", "here", "one",
                    "other", "get", "also", "good", "test", "we're", "its", "were", "use",
                    "could", "can", "many", "us", "google", "population", "service", "large",
                    "small", "amp", "dc", "lots", "cities", "really"]
        
        stoplist += [
            "a","able","about","above","act","add","afraid","after","again","against","age","ago","agree","air","all","allow","also","always","am","among","an","and","anger","animal","answer","any","appear","apple","are","area","arm","arrange","arrive","art","as","ask","at","atom","baby","back","bad","ball","band","bank","bar","base","basic","bat","be","bear","beat","beauty","bed","been","before","began","begin","behind","believe","bell","best","better","between","big","bird","bit","black","block","blood","blow","blue","board","boat","body","bone","book","born","both","bottom","bought","box","boy","branch","bread","break","bright","bring","broad","broke","brother","brought","brown","build","burn","busy","but","buy","by","call","came","camp","can","capital","captain","car","card","care","carry","case","cat","catch","caught","cause","cell","cent","center","century","certain","chair","chance","change","character","charge","chart","check","chick","chief","child","children","choose","chord","circle","city","claim","class","clean","clear","climb","clock","close","clothe","cloud","coast","coat","cold","collect","colony","color","column","come","common","company","compare","complete","condition","connect","consider","consonant","contain","continent","continue","control","cook","cool","copy","corn","corner","correct","cost","cotton","could","count","country","course","cover","cow","crease","create","crop","cross","crowd","cry","current","cut","dad","dance","danger","dark","day","dead","deal","dear","death","decide","decimal","deep","degree","depend","describe","desert","design","determine","develop","dictionary","did","die","differ","difficult","direct","discuss","distant","divide","division","do","doctor","does","dog","dollar","done","don't","door","double","down","draw","dream","dress","drink","drive","drop","dry","duck","during","each","ear","early","earth","ease","east","eat","edge","effect","egg","eight","either","electric","element","else","end","enemy","energy","engine","enough","enter","equal","equate","especially","even","evening","event","ever","every","exact","example","except","excite","exercise","expect","experience","experiment","eye","face","fact","fair","fall","family","famous","far","farm","fast","fat","father","favor","fear","feed","feel","feet","fell","felt","few","field","fig","fight","figure","fill","final","find","fine","finger","finish","fire","first","fish","fit","five","flat","floor","flow","flower","fly","follow","food","foot","for","force","forest","form","forward","found","four","fraction","free","fresh","friend","from","front","fruit","full","fun","game","garden","gas","gather","gave","general","gentle","get","girl","give","glad","glass","go","gold","gone","good","got","govern","grand","grass","gray","great","green","grew","ground","group","grow","guess","guide","gun","had","hair","half","hand","happen","happy","hard","has","hat","have","he","head","hear","heard","heart","heat","heavy","held","help","her","here","high","hill","him","his","history","hit","hold","hole","home","hope","horse","hot","hot","hour","house","how","huge","human","hundred","hunt","hurry","i","ice","idea","if","imagine","in","inch","include","indicate","industry","insect","instant","instrument","interest","invent","iron","is","island","it","job","join","joy","jump","just","keep","kept","key","kill","kind","king","knew","know","lady","lake","land","language","large","last","late","laugh","law","lay","lead","learn","least","leave","led","left","leg","length","less","let","letter","level","lie","life","lift","light","like","line","liquid","list","listen","little","live","locate","log","lone","long","look","lost","lot","loud","love","low","machine","made","magnet","main","major","make","man","many","map","mark","market","mass","master","match","material","matter","may","me","mean","meant","measure","meat","meet","melody","men","metal","method","middle","might","mile","milk","million","mind","mine","minute","miss","mix","modern","molecule","moment","money","month","moon","more","morning","most","mother","motion","mount","mountain","mouth","move","much","multiply","music","must","my","name","nation","natural","nature","near","necessary","neck","need","neighbor","never","new","next","night","nine","no","noise","noon","nor","north","nose","note","nothing","notice","noun","now","number","numeral","object","observe","occur","ocean","of","off","offer","office","often","oh","oil","old","on","once","one","only","open","operate","opposite","or","order","organ","original","other","our","out","over","own","oxygen","page","paint","pair","paper","paragraph","parent","part","particular","party","pass","past","path","pattern","pay","people","perhaps","period","person","phrase","pick","picture","piece","pitch","place","plain","plan","plane","planet","plant","play","please","plural","poem","point","poor","populate","port","pose","position","possible","post","pound","power","practice","prepare","present","press","pretty","print","probable","problem","process","produce","product","proper","property","protect","prove","provide","pull","push","put","quart","question","quick","quiet","quite","quotient","race","radio","rail","rain","raise","ran","range","rather","reach","read","ready","real","reason","receive","record","red","region","remember","repeat","reply","represent","require","rest","result","rich","ride","right","ring","rise","river","road","rock","roll","room","root","rope","rose","round","row","rub","rule","run","safe","said","sail","salt","same","sand","sat","save","saw","say","scale","school","science","score","sea","search","season","seat","second","section","see","seed","seem","segment","select","self","sell","send","sense","sent","sentence","separate","serve","set","settle","seven","several","shall","shape","share","sharp","she","sheet","shell","shine","ship","shoe","shop","shore","short","should","shoulder","shout","show","side","sight","sign","silent","silver","similar","simple","since","sing","single","sister","sit","six","size","skill","skin","sky","slave","sleep","slip","slow","small","smell","smile","snow","so","soft","soil","soldier","solution","solve","some","son","song","soon","sound","south","space","speak","special","speech","speed","spell","spend","spoke","spot","spread","spring","square","stand","star","start","state","station","stay","stead","steam","steel","step","stick","still","stone","stood","stop","store","story","straight","strange","stream","street","stretch","string","strong","student","study","subject","substance","subtract","success","such","sudden","suffix","sugar","suggest","suit","summer","sun","supply","support","sure","surface","surprise","swim","syllable","symbol","system","table","tail","take","talk","tall","teach","team","teeth","tell","temperature","ten","term","test","than","thank","that","the","their","them","then","there","these","they","thick","thin","thing","think","third","this","those","though","thought","thousand","three","through","throw","thus","tie","time","tiny","tire","to","together","told","tone","too","took","tool","top","total","touch","toward","town","track","trade","train","travel","tree","triangle","trip","trouble","truck","true","try","tube","turn","twenty","two","type","under","unit","until","up","us","use","usual","valley","value","vary","verb","very","view","village","visit","voice","vowel","wait","walk","wall","want","war","warm","was","wash","watch","water","wave","way","we","wear","weather","week","weight","well","went","were","west","what","wheel","when","where","whether","which","while","white","who","whole","whose","why","wide","wife","wild","will","win","wind","window","wing","winter","wire","wish","with","woman","women","wonder","won't","wood","word","work","world","would","write","written","wrong","wrote","yard","year","yellow","yes","yet","you","young","your"
        ]
                    
        corpus = Store.all().filter("name = ","corpus").fetch(1).pop().val
        
        # Strip puntuation and "&quot"
        punctuation = re.compile(r'[.?\'!,":;&\-\+=]*')
        corpus = punctuation.sub('', corpus)
        corpus = corpus.replace("&quot", "")
        corpus = corpus.replace("/", " ")
        corpus = corpus.replace("(", " ")
        corpus = corpus.replace(")", " ")
        corpus = corpus.replace("\\", " ")
        
        # Tokenize
        tokens = re.split('\s+', corpus.lower().strip())
        stemdict, tempdict, finaldict = {}, {}, {}
        
        # FIRST LOOP
        p = PorterStemmer()
        for w in tokens:
            if w in stoplist:
                continue
            s = p.stem(w, 0,len(w)-1)
            try:
                tempdict[w] += 1
            except:
                tempdict[w] = 1
            stemdict.setdefault(s,{}).update({w:tempdict[w]})
        
        # SECOND LOOP
        cumfreq = 0
        for k, v in stemdict.items():
            for l, m in v.items():
                cumfreq = cumfreq + m
            items = v.items()
            items.sort(self.sortfunc)
            finaldict[items[0][0]] = cumfreq
            cumfreq = 0

        a = finaldict.items()
        a.sort(self.sortfunc)

        results = self.makeCloud(15, a)
        
        self.response.out.write(results)
        # for r in results:
        #     self.response.out.write(r)
        #     self.response.out.write(str(r) + "<br/>")


class ApiSupporters(webapp.RequestHandler):
    
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
        self.response.headers.add_header("Content-Type", "application/javascript")
        
        # Set default params
        limit = 10
        offset = 0
        markers = False
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
        cache_key = "api/supporters?limit=%s&offset=%s&markers=%s" % (limit, offset, markers)
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
                    
            # convert into a list of objects
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
        
        # Cache for 6 hours. (approvals will clear cache)
        memcache.add(cache_key, resp, 2)
        
        # Respond with JSON
        if pprint:
            self.response.out.write(json.dumps(resp, indent=2))
        else:
            self.response.out.write(json.dumps(resp))

def main():
    urls = [ ('/', MainHandler),  
             ('/admin/csv', CsvOutput), 
             ('/admin', AdminUnapprovedPeople),
             ('/admin/', AdminUnapprovedPeople),
             ('/admin/approvedpeople', AdminApprovedPeople),
             ('/admin/approvedorgs', AdminApprovedOrg),
             ('/admin/unapprovedorgs', AdminUnapprovedOrg),
             # ('/api/makecloud', MakeCloud),
             ('/api/supporters', ApiSupporters),
           ]
    util.run_wsgi_app(webapp.WSGIApplication(urls, debug=True))

if __name__ == '__main__':
    main()