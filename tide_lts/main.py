#!/usr/bin/env python

import board
import neopixel
import logging
import csv
from datetime import datetime, timedelta
from time import sleep
import sys
import requests


# set the logging level
log_level = logging.INFO
# create logger
_LOGGER = logging.getLogger('tide_lights')
_LOGGER.setLevel(log_level)
# create log file handler
fh = logging.FileHandler('tide_lights.log')
fh.setLevel(log_level)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(log_level)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
_LOGGER.addHandler(fh)
_LOGGER.addHandler(ch)

# intake two integer arguments: station_id and number of pixels to use
try:
    station_id = sys.argv[1]
    num_pixels_to_use = sys.argv[2]
except IndexError:
    _LOGGER.error("Usage: main.py station_id num_pixels_to_use")
    _LOGGER.error(f"System arguments: {sys.argv}")
    sys.exit(1)

# check that the station_id is a 7 digit integer and the number of pixels is an integer
try:
    station_id = int(station_id)
    num_pixels_to_use = int(num_pixels_to_use)
except ValueError:
    _LOGGER.error("station_id must be a 7 digit integer and num_pixels_to_use must be an integer")
    sys.exit(1)

# variables for tide data
datum = 'MLLW'
product = 'predictions'
time_zone = 'lst_ldt'
interval = 'hilo'
units = 'english'

# pixel strip variables
rising_color = (0, 0, 255) # blue
falling_color = (255, 165, 0) 
middle_pixel = round(num_pixels_to_use / 2)

# Light Class definition
class Lights(object):
    """
    Class to control the lights
    """
    def __init__(self, num_lights, pin):
        self.num_pixels = num_lights
        self.__pixel = neopixel.NeoPixel(pin, num_lights, auto_write=False)
        _LOGGER.info(f"Initializing pixel strip of {self.num_pixels} lights on pin {pin}")

    def __setitem__(self, key, value):
        self.__pixel[key] = value
        _LOGGER.debug(f"Setting pixel {key} to {value}")

    def __getitem__(self, idx):
        return self.__pixel[idx]
    
    def clear(self):
        """
        Turn off all the lights
        """
        _LOGGER.info("Clearing all pixels")
        for i in range(self.num_pixels):
            self.__pixel[i] = (0, 0, 0)
        self.__pixel.show()

    def show(self):
        pix_list = []
        for p in self.__pixel:
            if p == (0, 0, 0):
                pix_list.append('-')
            else:
                pix_list.append('o')
        _LOGGER.debug(''.join(pix_list))
        # Send the command to change the lights
        self.__pixel.show()

class NOAATidePrediction:
    def __init__(self, station_id, datum, product, time_zone, interval, units):
        """
        Initialize the class with the station id, datum, product, time zone, interval, and units
        """
        # https://tidesandcurrents.noaa.gov/api/
        self.base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
        self.station_id = station_id
        self.datum = datum
        self.product = product
        self.time_zone = time_zone
        self.interval = interval
        self.units = units

    # Build the URL to query the API
    def build_url(self, begin_date, end_date):
        url = f"{self.base_url}begin_date={begin_date}&end_date={end_date}&station={self.station_id}&product={self.product}&datum={self.datum}&time_zone={self.time_zone}&interval={self.interval}&units={self.units}&format=json"
        return url
    
    # Query the API and return a dictionary of the data
    def get_data(self, url):
        response = requests.get(url)
        return response.json()
    
    # Get the tide data for 48 hours around now
    def get_tide_data_now(self):
        begin_date = (datetime.now() - timedelta(hours=24)).strftime("%Y%m%d %H:%M")
        end_date = (datetime.now() + timedelta(hours=24)).strftime("%Y%m%d %H:%M")
        url = self.build_url(begin_date, end_date)
        return self.get_data(url)
    
    # Get the tide data for a specific time range
    def get_tide_data(self, begin_date, end_date):
        # check if time is in the correct format
        try:
            datetime.strptime(begin_date, "%Y%m%d %H:%M")
            datetime.strptime(end_date, "%Y%m%d %H:%M")
        except ValueError:
            print("Incorrect data format, should be YYYYMMDD HH:MM")
            return None
        
        url = self.build_url(begin_date, end_date)
        return self.get_data(url)
    

if __name__ == '__main__':
    _LOGGER.info("Starting tide_lights service")
    noaa = NOAATidePrediction(station_id, datum, product, time_zone, interval, units)
    fieldnames = ['t', 'v', 'type']

    # create the pixel objects
    # TODO - do something wih the second pixel strip
    # left_pixel = Lights(num_pixels_to_use, board.D12)
    tide_position_strip = Lights(num_pixels_to_use, board.D21)

    # clear the pixels
    tide_position_strip.clear()

    # set the middle pixel to white
    tide_position_strip[middle_pixel] = (255, 255, 255)
    tide_position_strip.show()
    # check for an existing tide data file
    try:
        with open('data.csv', 'r') as csvfile:
            data = csv.DictReader(csvfile)
            _LOGGER.debug("Found data.csv file")
    except FileNotFoundError:
        _LOGGER.debug("No data.csv file found")
        data = None
    
    # if there is no data.csv file, pull the data from the API
    if data == None:
        # call the NOAA API to get the tide data
        data = noaa.get_tide_data_now()
        data = data['predictions']
        _LOGGER.debug("Pulled NOAA data:")
        _LOGGER.debug(data)

        # save the data to a csv file
        with open('data.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)

    while True:
        _LOGGER.info("Starting loop")
        with open('data.csv', 'r') as csvfile:
            data = csv.DictReader(csvfile)
            _LOGGER.debug("Found data.csv file")
            data = list(data)
            _LOGGER.debug(data)

        # get the tide data if the first data point is more than 32 hours old
        try:
            earliest_tide = (datetime.strptime(data[0]['t'], "%Y-%m-%d %H:%M") - datetime.now()).total_seconds() / 3600
        except IndexError:
            earliest_tide = -999

        if earliest_tide < -32:
            _LOGGER.info("Tide data is more than 8 hours old")
            # call the NOAA API to get the tide data
            data = noaa.get_tide_data_now()
            data = data['predictions']
            _LOGGER.debug("Pulled NOAA data:")
            _LOGGER.debug(data)
            with open('data.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
        else:
            _LOGGER.info("Tide data is less than 8 hours old")
            pass

        #  open the data.csv file and read the data
        with open('data.csv', 'r') as csvfile:
            data = list(data)
            _LOGGER.debug(data)

        # add the time difference and pixel columns to the data
        for row in data:
            # calculate the time difference in hours between t and the current time for all data points
            row['time_diff'] = (datetime.strptime(row['t'], "%Y-%m-%d %H:%M")- datetime.now()).total_seconds() / 3600
            # create a data point based on time_diff to light up the pixels
            row['pixel'] = round(row['time_diff'] * 2)
            # strip the spaces from the type column and the v column
            row['type'] = row['type'].strip()
            row['v'] = row['v'].strip()
            _LOGGER.debug("Tide data:")
            _LOGGER.debug(data)

        # find the next tide event from now
        for idx, row in enumerate(data):
            if row['time_diff'] > 0:
                next_tide = row
                prev_tide = data[idx - 1]
                break

        # set the tide direction
        if next_tide['type'] == 'H':
            tide_direction = "rising"
        elif next_tide['type'] == 'L':
            tide_direction = "falling"
    
        # get the difference between the previous and next tide times
        current_tide_length = next_tide['time_diff'] - prev_tide['time_diff']
        time_to_next_tide = next_tide['time_diff']

        # set the number of pixels to light based on the time to the next tide and the curren tide length
        proportion_to_light = (1-(time_to_next_tide / current_tide_length))

        _LOGGER.info(f"Next tide: {next_tide}")
        _LOGGER.info(f"Previous tide: {prev_tide}")
        _LOGGER.info(f"Tide direction: {tide_direction}")
        _LOGGER.info(f"Current tide length: {current_tide_length}")
        _LOGGER.info(f"Proportion to light: {proportion_to_light}")
        _LOGGER.info(f"Time to next tide: {time_to_next_tide}")

        # light up from the left with a full bar meaning high tide and an empty bar meaning low tide
        pixels_to_light = round(num_pixels_to_use * proportion_to_light)
        _LOGGER.info(f"Pixels to light: {pixels_to_light} based on proportion {proportion_to_light}")
        
        # If proportion_to_light is 0, create a series of the odd numbers in the range of num_pixels_to_use
        if proportion_to_light == 0:
            pixels_to_light = list(range(1, num_pixels_to_use, 2))
            light_color = falling_color
            _LOGGER.info(f"Setting Low tide output")
        # If proportion_to_light is 1, create a series of the even numbers in the range of num_pixels_to_use
        elif proportion_to_light == 1:
            pixels_to_light = list(range(0, num_pixels_to_use, 2))
            light_color = rising_color
            _LOGGER.info(f"Setting High tide output")
        # If proportion_to_light is between 0 and 1, set the pixels to light based on the tide direction
        else:
            _LOGGER.info(f"Setting in between tide output")
            # create a series starting at 0 and ending at the number of pixels to light for rising tides
            if tide_direction == "rising":
                light_color = rising_color
                pixels_to_light = list(range(0, pixels_to_light, 1))
            # create a series starting at the number of pixels to light and ending at the number of pixels to use for falling tides 
            elif tide_direction == "falling":
                light_color = falling_color
                pixels_to_light = list(range(num_pixels_to_use - pixels_to_light, num_pixels_to_use, 1))
        
        _LOGGER.info(f"Pixels to light: {pixels_to_light}")
        # Decide which pixels to light up
        for i in range(num_pixels_to_use):
            if i in pixels_to_light:
                tide_position_strip[i] = light_color
                _LOGGER.debug(f"Pixel {i} is on")
            else:
                tide_position_strip[i] = (0, 0, 0)
                _LOGGER.debug(f"Pixel {i} is off")

        tide_position_strip.show()

        # sleep for 5 minutes
        _LOGGER.info("Sleeping for 5 minutes")
        sleep(300)