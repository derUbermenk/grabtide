#!/usr/bin/env python

import argparse
import requests
import os
import sys

class TideGrabber():
    def __init__(self, startDate: str, endDate: str, saveDir: str, station_id: str, interval: str = 'h'):
        """Initializes a tide grabber object

        Parameters
        ----------
        startDate: str
            yyyymmdd
        endDate: str
            yyyymmdd
        saveDir: str
            yyyymmdd
        """
        self.startDate = startDate
        self.endDate = endDate
        self.saveDir = saveDir.rstrip('/')
        self.stationID = station_id

        self.savePath = self.formatSavePath()
        self.interval = interval
        return

    def formatSavePath(self):
        return os.path.join(self.saveDir, f"{self.startDate}_{self.endDate}_tides.csv")
        # return os.path.join(self.saveDir, "tides.csv")

    def request(self):
        url = 'https://tidesandcurrents.noaa.gov/api/datagetter' 
        params = {
            'product': 'predictions',
            'application': 'NOS.COOPS.TAC.WL',
            'begin_date': self.startDate,
            'end_date': self.endDate,
            'datum': 'MSL',
            'station': self.stationID,
            'time_zone': 'GMT',
            'units': 'metric',
            'interval': self.interval,
            'format': 'csv'
        }

        response = requests.get(url, params)

        if response.status_code == 200:
            return response.content
        else:
            print(f'Failed to retrieve data: {response.status_code}')
            sys.exit(1)

    def saveResponse(self, content: bytes):
        """
        saves a given content to a csv file defined by self.savePath

        Parameters
        ----------
        content: bytes
        """
        new_headers = ["dates","tide"]

        # Decode bytes to string assuming UTF-8 encoding
        content_string = content.decode('utf-8')

        # Split the content into lines
        lines = content_string.splitlines()

        # Replace the header with new_headers
        lines[0] = ','.join(new_headers)

        updated_content = '\n'.join(lines)

        with open(self.savePath, 'w', newline='') as file:
            file.write(updated_content)

    def run(self):    
        response_content = self.request()
        self.saveResponse(response_content)

def checkDirExists(path: str):
    """Checks if save directory exists 

    checks if the dir in the given path exists. exists the program if it doesnt

    Paremeters:
    ----------
    path: str
        path to directory 
    """
    if os.path.exists(path) and os.path.isdir(path):
        return
    else:
        sys.exit(1)
    
def initializeTideGrabber(args) -> TideGrabber:
    parser = argparse.ArgumentParser(
        prog="TideGrabber",
        description="downloads a csv file of MSL tide data from NOAA websites"
    )

    parser.add_argument('startdate', help='start date of range (yyyymmdd)')
    parser.add_argument('enddate', help='end date of range (yyyymmdd)')
    parser.add_argument('saveDir', help='save dir of csv file')
    parser.add_argument('stationid', help='stationid')
    parser.add_argument('--units', help='units')
    parser.add_argument('--interval', help='interval')
    parser.add_argument('--timezone', help='timezone')
    parser.add_argument('--datum', help='datum')

    args_ = parser.parse_args(args)

    checkDirExists(args_.saveDir)

    tide_grabber = TideGrabber(args_.startdate, args_.enddate, args_.saveDir, args_.stationid)
    return tide_grabber

if __name__ == "__main__":
    tide_grabber = initializeTideGrabber(sys.argv[1:])
    tide_grabber.run()