from django.db import models

from gmap.utils import geolocate


CATEGORY_LOOKUP = {'1': 'Cirrus Authorized Service Center (ASC)', '2': 'Cirrus Sales Representative or Center',
                   '3': 'Cirrus Training Center (CTC)', '4': 'Cirrus Standardized Instructor Pilot (CSIP)'}

INVERSE_CATEGORY = dict((v, k) for k, v in CATEGORY_LOOKUP.items())

SUBCATEGORY_LOOKUP = {

    '1': 'Composite & Paint Repair',
    '2': 'Pickup & Delivery Service',
    '3': 'Parts Distributor',
    '4': 'Air Conditioning Service',
    '5': 'Garmin Service',
    '6': 'Avidyne Service',
    '7': 'Full Avionics Facility',
    '8': 'Oxygen Service',
    '9': 'Wi-Fi Equipped',
    '10': 'CAPS Overhaul',
    '11': 'Cirrus Platinum Service Partner',
    '12': 'Ice Protection System Maintenance',
    '13': 'SR20 Rental',
    '14': 'SR22 Rental',
    '15': 'SR22T Rental',
    '16': 'Cirrus Perspective Avionics Available',
    '17': 'Avidyne Entegra Avionics Available',
    '18': 'Cirrus Platinum Training Partner',
    '19': 'Simulator Available',
    '20': 'Cirrus Perspective Qualified',
    '21': 'Avidyne Entegra Qualified',
    '22': 'New Cirrus Sales',
    '23': 'Used Cirrus Sales',
    '24': 'n/a'

}

INVERSE_SUBCATEGORY = dict((v, k) for k, v in SUBCATEGORY_LOOKUP.items())

# name, category, platinum partner, contacT_name, contact_title, airport_name, airport_code, address, phone, fax, email, url, sub_category1, ..., sub_categoryN

SUBCAT_IDX = 18
# SUBCAT_IDX = 12

# NAME_COLUMN = 2
NAME_COLUMN = 0
#CATEGORY_COLUMN = 3
CATEGORY_COLUMN = 1
#ADDRESS_COLUMN = 9
ADDRESS_COLUMN = 7
SUBCATEGORY_COLUMN = SUBCAT_IDX


class SalesBoundary(models.Model):
    boundary_code = models.CharField('Boundary Code', max_length=75)
    owner = models.ForeignKey('SalesDirector');

    class Meta:
        unique_together = ("boundary_code", "owner")

    def __str__(self):
        return self.boundary_code


class SalesDirector(models.Model):
    name = models.CharField('Name', max_length=100, unique=True)
    title = models.CharField(max_length=50, blank=True)
    phone = models.CharField('Phone Number', max_length=40, blank=True)
    email = models.EmailField('Email', blank=True)
    airport_code = models.CharField(max_length=8, blank=True)
    airport_name = models.CharField(max_length=50, blank=True)
    address = models.TextField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=100, blank=True)
    zipcode = models.CharField(max_length=10, blank=True)
    url = models.URLField(blank=True)
    country = models.ForeignKey('CountryISOCode', blank=True)

    def from_csv(self, row, row_id, errors):

        local_errors = False

        '''
        self.name, cat, plat, self.contact_name, self.contact_title = row[0:5] 
        self.airport_name, self.airport_code, self.address, self.phone, self.fax = row[5:10]
        self.email, self.url = row[10:12]

        subcategories = row[12:]
        '''

        cat, plat = '', ''
        subcategories = []

        try:

            self.name, cat, plat, self.contact_name, self.title = row[0:5]
            self.airport_name, self.airport_code, self.address, self.phone, fax = row[5:10]
            self.email, self.url, self.state, iso_3, self.city, self.zipcode, latitude, longitude = row[10:SUBCAT_IDX]

            subcat_string = row[SUBCAT_IDX]

            if ',' in subcat_string:
                subcategories = subcat_string.split(',')

            else:
                subcategories = [subcat_string]

        except IndexError:
            error_string = "Entry does not contain required number of fields: %s < %s" % (len(row), SUBCAT_IDX)
            errors.append(('%s : %s' % (row_id, error_string)))
            return

        except ValueError:
            error_string = "Entry does not contain required number of fields: %s < %s" % (len(row), SUBCAT_IDX)
            errors.append(('%s : %s' % (row_id, error_string)))
            return

        if not self.name:
            local_errors = True
            row[NAME_COLUMN] = '<font color="red">INSERT_NAME</font>'

        if local_errors:
            error_string = ', '.join(row)
            errors.append(('%s : %s' % (row_id, error_string)))
            return

        try:
            self.country = CountryISOCode.objects.get(long_name=iso_3)

        except:

            try:
                self.country = CountryISOCode.objects.get(iso_3=iso_3)

            except:

                try:
                    self.country = CountryISOCode.objects.get(iso_2=iso_3)

                except:
                    error_string = "Unable to map %s to ISO long name, two letter abbreviation, or three letter abbreviation" % iso_3
                    errors.append(('%s : %s' % (row_id, error_string)))

        # Ask django really, really nicely not to insert our object twice
        self.save()

    def __str__(self):
        return self.name


class MarkerCategoryManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name=name)


class MarkerCategory(models.Model):
    objects = MarkerCategoryManager()
    name = models.CharField('type', max_length=200, unique=True)
    position = models.IntegerField(default=0);
    icon = models.ImageField('icon', blank=True, upload_to='gmap-icons/')
    platinum_icon = models.ImageField('platinum icon', blank=True, upload_to='gmap-icons/')
    shadow = models.ImageField('icon shadow', blank=True, upload_to='gmap-icons/')

    def natural_key(self):
        return self.name

    def __str__(self):
        return self.name


class MarkerSubCategory(models.Model):
    objects = MarkerCategoryManager()
    name = models.CharField('Name', max_length=200, unique=True)

    def natural_key(self):
        return self.name

    def __str__(self):
        return self.name


class GeolocateFailure(Exception):
    def __init__(self, message, address):
        self.message = message
        self.address = address

    def __str__(self):
        return '%s - %s' % (self.message, self.address)


class CountryISOCode(models.Model):
    long_name = models.CharField(max_length=200)
    iso_3 = models.CharField(max_length=10, blank=True)
    iso_2 = models.CharField(max_length=10, blank=True)

    def natural_key(self):
        return self.long_name

    def __str__(self):
        return self.long_name


class MapMarker(models.Model):
    name = models.CharField(max_length=200)
    latitude = models.CharField(max_length=30, blank=True)
    longitude = models.CharField(max_length=30, blank=True)
    category = models.ForeignKey('MarkerCategory')
    platinum = models.BooleanField('Platinum Partner', default=False)
    sub_categories = models.ManyToManyField(MarkerSubCategory, related_name='sub_categories')
    contact_name = models.CharField(max_length=50, blank=True)
    contact_title = models.CharField(max_length=50, blank=True)
    airport_name = models.CharField(max_length=100, blank=True)
    airport_code = models.CharField(max_length=6, blank=True)
    address = models.TextField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=50, blank=True)
    zipcode = models.CharField(max_length=10, blank=True)
    country = models.ForeignKey('CountryISOCode', null=True, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    fax = models.CharField(max_length=40, blank=True)
    email = models.EmailField(blank=True)
    url = models.URLField(blank=True)

    # Make sure we update the lat/long with the location
    def save(self, *args, **kwargs):

        if not self.latitude and not self.longitude:
            full_address = "%s, %s, %s, %s, %s" % (self.address, self.city, self.state, self.zipcode, self.country)
            latlng = geolocate(repr(full_address))

            if latlng != None:
                self.latitude = latlng['latitude']
                self.longitude = latlng['longitude']

            else:
                raise GeolocateFailure("Failed to geolocate address for %s" % self.name, full_address)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def from_csv(self, row, row_id, errors):

        local_errors = False

        '''
        self.name, cat, plat, self.contact_name, self.contact_title = row[0:5] 
        self.airport_name, self.airport_code, self.address, self.phone, self.fax = row[5:10]
        self.email, self.url = row[10:12]

        subcategories = row[12:]
        '''

        cat, plat = '', ''
        subcategories = []

        try:

            self.name, cat, plat, self.contact_name, self.contact_title = row[0:5]
            self.airport_name, self.airport_code, self.address, self.phone, self.fax = row[5:10]
            self.email, self.url, self.state, iso_3, self.city, self.zipcode, self.latitude, self.longitude = row[
                                                                                                              10:SUBCAT_IDX]

            subcat_string = row[SUBCAT_IDX]

            if ',' in subcat_string:
                subcategories = subcat_string.split(',')

            else:
                subcategories = [subcat_string]

        except IndexError:
            error_string = "Entry does not contain required number of fields: %s < %s" % (len(row), SUBCAT_IDX)
            errors.append(('%s : %s' % (row_id, error_string)))
            return

        except ValueError:
            error_string = "Entry does not contain required number of fields: %s < %s" % (len(row), SUBCAT_IDX)
            errors.append(('%s : %s' % (row_id, error_string)))
            return

        if not self.name:
            local_errors = True
            row[NAME_COLUMN] = '<font color="red">INSERT_NAME</font>'

        if not cat:
            local_errors = True
            row[CATEGORY_COLUMN] = '<font color="red">INSERT_CATEGORY</font>'

        #if not self.address:
        #    local_errors = True
        #    row[ADDRESS_COLUMN] = '<font color="red">INSERT_ADDRESS</font>'

        if not len(subcategories):
            local_errors = True
            row.append('<font color="red">INSERT_SUBCATEGORY</font>')

        elif not subcategories[0]:
            local_errors = True
            row[SUBCATEGORY_COLUMN] = '<font color="red">INSERT_SUBCATEGORY</font>'

        if local_errors:
            error_string = ', '.join(row)
            errors.append(('%s : %s' % (row_id, error_string)))
            return

        self.platinum = True if plat == '1' else False

        self.category = MarkerCategory.objects.get(pk=cat.strip().strip("'"))

        try:
            self.country = CountryISOCode.objects.get(long_name=iso_3)

        except:

            try:
                self.country = CountryISOCode.objects.get(iso_3=iso_3)

            except:

                try:
                    self.country = CountryISOCode.objects.get(iso_2=iso_3)

                except:
                    error_string = "Unable to map %s to ISO long name, two letter abbreviation, or three letter abbreviation" % iso_3
                    errors.append(('%s : %s' % (row_id, error_string)))

        # object's gotta be in the DB before it can get M2M mapping...
        #
        try:
            self.save()

        except GeolocateFailure as inst:
            errors.append('%s : %s' % (row_id, inst))
            return

        # ...like this one!
        for subcategory in subcategories:
            if subcategory:
                self.sub_categories.add(MarkerSubCategory.objects.get(pk=subcategory.strip().strip("'")))


        # Ask django really, really nicely not to insert our object twice
        self.save(force_update=True)

    # Expected csv format: 
    #
    # name, category, platinum partner, contacT_name, contact_title, airport_name, airport_code, address, phone, fax, email, url, sub_category1, ..., sub_categoryN
    #
    def csv_row(self):

        # my baseline doesn't have: plat partner, contact_name, contact_title, airport_name, 
        # TODO: now it does!

        '''
        return [self.latitude, self.longitude, self.name, INVERSE_CATEGORY[self.category.name], str(self.platinum), self.contact_name, self.contact_title,
                self.airport_name, self.airport_code, self.address, self.phone, self.fax,
                self.email, self.url] + [INVERSE_SUBCATEGORY[subcat.name] for subcat in self.sub_categories.all()]
        '''

        return [self.name, INVERSE_CATEGORY[self.category.name], str(self.platinum), self.contact_name,
                self.contact_title,
                self.airport_name, self.airport_code, self.address, self.phone, self.fax,
                self.email, self.url] + [INVERSE_SUBCATEGORY[subcat.name] for subcat in self.sub_categories.all()]

    
