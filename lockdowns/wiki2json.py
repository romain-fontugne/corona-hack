"""Convert copy/pasted text from this table 
https://en.wikipedia.org/wiki/Template:2020_coronavirus_quarantines_outside_Hubei
into a JSON object"""

import sys
import json
import requests
import country_converter as coco
import datetime

APNIC_URL = 'http://v6data.data.labs.apnic.net/ipv6-measurement/Economies/{cc}/{cc}.asns.json?m=10'
input_fname = sys.argv[1]
countries_info = {}

with open(input_fname, 'r') as input_fp:
    for line in input_fp:
        # format: country name, lockdown start, end, scope
        field = line.split()
        if len(field) == 4:
            country, start, end, scope = [x.strip() for x in field]
        elif len(field) == 5:
            country, state, start, end, scope = [x.strip() for x in field]
        else:
            continue

        # Remove reference from dates
        start = start.partition('[')[0]
        end = end.partition('[')[0]

        # Keep only national lockdowns
        if scope != "National":
            continue

        country_info = {'start': start, 'end': end, 'scope': scope}

        # Country code
        cc = coco.convert(names=[country], to='ISO2')
        if cc == 'not found':
            # it might be a country with a composed name
            country = country+" "+state
            cc = coco.convert(names=[country], to='ISO2')

        if cc == 'not found':
            continue

        country_info['name'] = country
        country_info['cc'] = cc

        # get top country's eyeball networks
        r = requests.get(APNIC_URL.format(cc=cc))
        country_info['eyeball'] = r.json()


        # compute monitoring dates
        # Find monday before the lockdown
        ye, mo, da = start.split('-')
        startdate = datetime.datetime(year=int(ye), month=int(mo), day=int(da))
        monday = startdate - datetime.timedelta(days=startdate.weekday())
        sunday = monday + datetime.timedelta(days=6)

        country_info['monitoring_dates'] = {'lockdown': {
                                            'monday':monday.strftime("%Y-%m-%d"), 
                                            'sunday':sunday.strftime("%Y-%m-%d")} 
                                            }

        # One month before lockdown
        before_monday = monday - datetime.timedelta(days=28)
        before_sunday = sunday - datetime.timedelta(days=28)
        country_info['monitoring_dates']['before'] = {
                                    'monday':before_monday.strftime("%Y-%m-%d"), 
                                    'sunday':before_sunday.strftime("%Y-%m-%d") 
                                    }

        countries_info[country] = country_info


with open('lockdowns.json', 'w') as output_fp:
    json.dump(countries_info, output_fp, sort_keys=True, indent=4)
