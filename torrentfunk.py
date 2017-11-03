#VERSION: 0.1
#AUTHORS: Charitoo Dunamis (charitoodunamis@gmail.com)
#LICENSE: GNU GPL v3

import logging
import sys
from os.path import join, dirname, abspath
try:
    from html.parser import HTMLParser
except ImportError as e:
    from HTMLParser import HTMLParser

sys.path.insert(0, abspath(join(dirname(__file__), 'qbt')))
from qbt.novaprinter import prettyPrinter
from qbt.helpers import retrieve_url

KILOBYTE = 1024
SIZES = {"kB": KILOBYTE, "MB": KILOBYTE ** 2, "GB": KILOBYTE ** 3,
         "TB": KILOBYTE ** 4}


class torrentfunk(object):
    """ Search engine class """
    url = 'https://www.torrentfunk.com'
    name = 'Torrent Funk'
    # 'all', 'movies', 'tv', 'music', 'games', 'anime', 'software', 'pictures',
    # 'books'
    supported_categories = {
        'all': 'all', 'music': 'music', 'movies': 'movies', 'games': 'games',
        'software': 'software', 'anime': 'anime', 'books': 'ebooks',
        'tv': 'television'}

    class FunkParser(HTMLParser):
        """ Parser class """
        def __init__(self, list_searches, url):
            HTMLParser.__init__(self)
            self.list_searches = list_searches
            self.url = url
            self.curritem = None
            self.key = None
            # the first td with class=tc contains date
            # while the second contains the size
            self.tc_count = 0
            # name is built from the contents of several tags
            self.build_name = False
            # mapping of css class for various td tags and corresponding
            # key the data must go in
            self.class_to_key = {"tc": "size", "tul": "seeds", "tdl": "leech",
                                 "": None}

        def dummy(self, attrs):
            """ Default handler for start tag dispatcher """
            pass

        def handle_start_tag_a(self, params):
            """ Handler for start tag a """
            link = params.get("href", "")
            if link.startswith("/torrent"):
                self.curritem = dict()
                self.curritem["desc_link"] = self.url + link
                self.curritem["name"] = ""
                self.curritem["link"] = "-1"
                # name of torrent may be spread over several tags
                # due to fomating to make search terms bold
                # end with the </a> closing tag
                self.build_name = True
                self.tc_count = 0

        def handle_start_tag_tr(self, params):
            """ Handler for start tag td """
            if self.build_name is True:
                self.build_name = False

        def handle_start_tag_td(self, params):
            css_class = params.get("class", "")
            if css_class == 'tc':
                _ = self.tc_count + 1
                self.tc_count = _ % 4
            self.key = self.class_to_key.get(css_class)

        def handle_starttag(self, tag, attrs):
            """ Parser's start tag handler """
            params = dict(attrs)
            # if self.curritem:
            func_name = "_".join(("handle_start_tag", tag))
            func = getattr(self, func_name, self.dummy)
            # logging.debug("Tag='%s' so calling %s" % (tag, func.__name__))
            func(params)

        def handle_endtag(self, tag):
            """ Parser's end tag handler """
            if self.curritem and tag == "tr":
                self.curritem["engine_url"] = self.url
                self.list_searches.append(self.curritem)
                self.curritem = None
                self.key = None
            elif tag == "a":
                self.build_name = False

        def handle_data(self, data):
            """ Parser's data handler """
            if self.build_name:
                self.curritem["name"] = self.curritem["name"] + data
            elif self.key and self.curritem:
                if self.key == 'size':
                    if self.tc_count != 2:
                        return
                    val, level = data.split(" ")
                    temp = float(val.strip()) * SIZES.get(level.strip(), 1)
                    data = str(int(temp))
                self.curritem[self.key] = data

    def search(self, what, cat='all'):
        """ Performs search """
        logging.info("Calling search")
        what = "-".join(what.split(" "))
        cat = cat.lower()
        query = self.url + "/{cat}/torrents/{what}.html?sort=seeds&o=desc"\
            .format(cat=cat, what=what)
        logging.debug("Query: %s" % query)
        response = retrieve_url(query)

        list_searches = []
        parser = self.FunkParser(list_searches, self.url)
        parser.feed(response)
        parser.close()
        logging.info("list_searches is empty: %s" % (len(list_searches) == 0))

        for torrent in list_searches:
            prettyPrinter(torrent)
        return


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger(__file__)

    tor = torrentfunk()
    tor.search("game of thrones", "all")
