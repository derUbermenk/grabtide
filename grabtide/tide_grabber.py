#!/usr/bin/env python

import argparse
import requests
import os
import sys
import boto3



class TideGrabber():
    def __init__(self, startDate: str, endDate: str, saveDir: str, station_id: str, bucketName: str, s3Key: str, interval: str = 'h', useAccessKeys: bool = False, access_key_id: str = None, secret_access_key: str = None):
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
        self.bucketName = bucketName 
        self.s3Key = s3Key 
        self.useAccessKeys = useAccessKeys
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
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
    
    def uploadTides(self):
        # Initialize the S3 client
        if self.useAccessKeys:
            s3_client = boto3.client(
                's3',
                aws_access_key_id='your_access_key',
                aws_secret_access_key='your_secret_key'
            )
        else:
            s3_client = boto3.client('s3')

        # Upload the file
        s3_client.upload_file(self.savePath, self.bucketName, self.s3Key)

        print(f"File uploaded to s3://{self.bucketName}/{self.s3Key}")

    def run(self):    
        response_content = self.request()
        self.saveResponse(response_content)
        self.uploadTides()

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
    parser.add_argument('bucketName', help='bucket name')
    parser.add_argument('s3Key', help='s3 key')
    parser.add_argument('--units', help='units')
    parser.add_argument('--interval', help='interval')
    parser.add_argument('--timezone', help='timezone')
    parser.add_argument('--datum', help='datum')
    parser.add_argument('--useAccessKeys', action='store_true', help='Use when using env variables as access keys')

    args_ = parser.parse_args(args)

    checkDirExists(args_.saveDir)

    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    if args_.useAccessKeys and access_key_id is None and secret_access_key is None:
        sys.exit(1)

    tide_grabber = TideGrabber(args_.startdate, args_.enddate, args_.saveDir, args_.stationid, args_.bucketName, args_.s3Key, useAccessKeys = args_.useAccessKeys, access_key_id=access_key_id, secret_access_key=secret_access_key)
    return tide_grabber

if __name__ == "__main__":
    tide_grabber = initializeTideGrabber(sys.argv[1:])
    tide_grabber.run()