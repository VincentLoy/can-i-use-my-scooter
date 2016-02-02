#!/usr/bin/env python3

from __future__ import unicode_literals

from urllib import parse
import json
import optparse

import requests

from os import getenv


class CanIUseMyScooter(object):

    def __init__(self, region, city):
        self.api_key = getenv('WUNDERGROUND_API_KEY')
        self.sms_user = getenv('SMS_USER')
        self.sms_pass = getenv('SMS_PASS')
        self.api_end_point = 'http://api.wunderground.com/api'
        self.sms_endpoint = 'https://smsapi.free-mobile.fr/sendmsg?{}'
        self.region = region
        self.city = city
        self.message = 'Prévision pour la journée : \n\n{}'

    def send_sms(self, message):
        r = requests.get(self.sms_endpoint.format(
            parse.urlencode({
                'user': self.sms_user,
                'pass': self.sms_pass,
                'msg': self.message.format(message)
            })
        ))

        if r.status_code == 200:
            print('ok, message sent')
            return True
        else:
            print('Error sending the message : {}'.format(r.status_code))
            return False

    def make_request(self, method):
        fc_endpoint = '{end_point}/{api_key}/{method}/q/{region}/{city}.json'.format(
            end_point=self.api_end_point,
            api_key=self.api_key,
            method=method,
            region=self.region,
            city=self.city
        )
        r = requests.get(fc_endpoint)

        if r.status_code == 200:
            return json.loads(r.text)
        else:
            self.send_sms('Sorry, me cyan send di message man, error {}'.format(r.status_code))

    @staticmethod
    def parse_hourly(hourly_result):
        MORNING = [9, 10, 11]
        MORNING_POP = []
        AFTERNOON = [14, 15, 16, 17, 18, 19]
        AFTERNOON_POP = []
        PHRASE = []
        MESSAGE = ''
        WANTED = MORNING + AFTERNOON

        def hourly():
            for hourly in hourly_result['hourly_forecast']:
                current_hour = hourly['FCTTIME']['hour']

                if int(current_hour) in WANTED:
                    yield {
                        'hour': int(current_hour),
                        'pop': int(hourly['pop'])
                    }

        for x in hourly():
            if x['hour'] in MORNING:
                MORNING_POP.append(x['pop'])
            elif x['hour'] in AFTERNOON:
                AFTERNOON_POP.append(x['pop'])

            PHRASE.append('{}h : {}%'.format(x['hour'], x['pop']))


        morning_avg = sum(MORNING_POP) / float(len(MORNING_POP))
        afternoon_avg = sum(AFTERNOON_POP) / float(len(AFTERNOON_POP))
        global_avg = (morning_avg + afternoon_avg) / 2.0

        MESSAGE += ', '.join(PHRASE) + '.\n\n'
        MESSAGE += 'Moyenne du matin : {}% \n'.format(morning_avg)
        MESSAGE += 'Moyenne de l\'après-midi : {}% \n'.format(afternoon_avg)
        MESSAGE += 'Moyenne de la journée : {}% \n\n'.format(global_avg)

        if global_avg <= 33:
            MESSAGE += 'Result : Ideal'

        elif global_avg <= 50:

            MESSAGE += 'Result : Favorable'
        else:
            MESSAGE += 'Result : Défavorable'

        return MESSAGE

    def get_hourly(self, parsed=True):
        resp = self.make_request('hourly')

        if not parsed:
            return resp

        return self.parse_hourly(resp)


def main():
    p = optparse.OptionParser()

    p.add_option('--city', '-c', default='la rochelle')
    p.add_option('--region', '-r', default='fr')
    p.add_option('--method', '-m', default='hourly')

    options, arguments = p.parse_args()
    fc = CanIUseMyScooter(options.region.upper(), options.city.title().replace(' ', '_'))
    fc.send_sms(fc.get_hourly())

if __name__ == '__main__':
    main()
