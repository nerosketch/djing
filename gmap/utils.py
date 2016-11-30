import json
import urllib
import urllib2
import csv
import codecs
import cStringIO


def csvByLine(csvFile, lineHandler):
    errors = ''
    for row_id, line in enumerate(UnicodeReader(csvFile)):
        print "Calling Line handler for %s" % line
        errors = ''.join([errors, lineHandler(line)])
    return errors


def geolocate(location, sensor=False):
    """
    Take a "location" and return its latitude and longitude

    Keyword arguments:
    location - String defining a geographical location (address, zip code, etc)
    sensor - Boolean defining whether the location was taken from
        an on-device sensor

    Output:
    latitude and logitude in an dict
    """
    sensor = str(sensor).lower()
    url = "http://maps.googleapis.com/maps/api/geocode/json?"
    url += urllib.urlencode({'address': location, 'sensor': sensor})
    data = urllib2.urlopen(url).read()
    data = json.loads(data)
    if data and data['status'] == 'OK':
        return ({
                    'latitude': data['results'][0]['geometry']['location']['lat'],
                    'longitude': data['results'][0]['geometry']['location']['lng']
                })
    else:
        return None


def georeverse(lat, lon):
    # construct url for reverse geocoding with google-maps
    url = "http://maps.googleapis.com/maps/api/geocode/json?"
    url += urllib.urlencode({'latlng': lat + ',' + lon, 'sensor': 'false'})

    # retrieve and load google-map data
    data = urllib2.urlopen(url).read()
    data = json.loads(data)

    # if request goes through, return the state and country of the location
    if data['status'] == 'OK':
        address_components = data['results'][0]['address_components']

        # these probably shouldn't be booleans (test with None data-type at some point)
        country = False
        state = False

        for component in address_components:

            try:
                if component['types'][0] == 'country':
                    country = component['long_name']

                if component['types'][0] == 'administrative_area_level_1':
                    state = component['long_name']
            except Exception:
                pass

        return ({
                    'state': state,
                    'country': country
                })
    return ({
                'state': False,
                'country': False
            })


class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """

    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        # return self.reader.next().decode("cp1252").encode("utf-8")
        return self.reader.next().encode("utf-8")


class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    # def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
    def __init__(self, f, dialect=csv.excel, encoding="cp1252", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
