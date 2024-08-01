from grabtide import TideGrabber, checkDirExists, initializeTideGrabber
import tempfile
from unittest.mock import Mock, patch
from requests import Response
import os
import csv

def test_checkDirExists(mocker):    
    """
        Test grabtide.checkDirExists 

        pass conditions:
            function exits with code 1 on non existent path 
            does not exit when given directory exists 
    """
    temp_path = tempfile.TemporaryDirectory()
    nonExistentFilePath = "/non/existent/path/"
    existentFilePath = temp_path.name

    # it exits with code 1 if path does not exist
    try:
        checkDirExists(nonExistentFilePath)
    except SystemExit as e:
        assert True 
        assert e.code == 1
    else:
        assert False 

    # it does not exit if path exist
    try:
        checkDirExists(existentFilePath)
    except SystemExit as e:
        assert False
    else:
        assert True

def test_initializeTideGrabber(mocker):
    """test initializeTideGrabber"""
    startDate = "20240101"
    endDate = "20240131"
    saveDir = "path/to/saveDir/"
    station_id = '11111'
    expected_savePath = f"{saveDir}{startDate}_{endDate}_tides.csv"

    args = [startDate, endDate, saveDir, station_id]

    # mock checkPath
    mocker.patch('grabtide.tide_grabber.checkDirExists')

    tide_grabber =  initializeTideGrabber(args)
    assert isinstance(tide_grabber, TideGrabber)

    assert tide_grabber.startDate == startDate
    assert tide_grabber.endDate == endDate
    assert tide_grabber.savePath == expected_savePath 
    assert tide_grabber.stationID == station_id 

    # set 2: even when save dir is lacking a trailing /
    startDate = "20240101"
    endDate = "20240131"
    saveDir = "path/to/saveDir"
    station_id = '11111'
    expected_savePath = f"{saveDir}/{startDate}_{endDate}_tides.csv"

    args = [startDate, endDate, saveDir, station_id]

    tide_grabber =  initializeTideGrabber(args)
    assert isinstance(tide_grabber, TideGrabber)

    assert tide_grabber.startDate == startDate
    assert tide_grabber.endDate == endDate
    assert tide_grabber.savePath == expected_savePath
    assert tide_grabber.stationID == station_id 

def test_TideGrabber_request_sucess():
    """Test the behaviour of of TideGrabber.request on success

    expect function to call request with the correct params 
    expect function to return a response object if status code  == 200 
    expect function to return with sys exit 1 if status code is not == 200
    """
    startDate = "20240101"
    endDate = "20240131"
    saveDir = "path/to/saveDir"
    station_id = '9440083'

    correct_url = 'https://tidesandcurrents.noaa.gov/api/datagetter' 
    correct_params = {
        'product': 'predictions',
        'application': 'NOS.COOPS.TAC.WL',
        'begin_date': startDate,
        'end_date': endDate,
        'datum': 'MSL',
        'station': station_id, 
        'time_zone': 'GMT',
        'units': 'metric',
        'interval': 'h',
        'format': 'csv'
    }

    tide_grabber = TideGrabber(startDate, endDate, saveDir, station_id)

    successful_response = Mock() 
    successful_response.status_code = 200 
    successful_response.content = b'sucess'
    with patch("requests.get", return_value=successful_response) as mock_get:

        try:
            response_content = tide_grabber.request()
        except SystemExit as e:
            assert False, "sucessful request exited, when expected not to"
        else:
            assert True

        mock_get.assert_called_once_with(correct_url, correct_params)
        assert isinstance(response_content, bytes)

def test_TideGrabber_request_unsucessful():
    """Test the behaviour of of TideGrabber.request on fail 

    expect function to call request with the correct params 
    expect function to return a response object if status code  == 200 
    expect function to return with sys exit 1 if status code is not == 200
    """
    startDate = "20240101"
    endDate = "20240131"
    saveDir = "path/to/saveDir"
    station_id = '9440083'

    correct_url = 'https://tidesandcurrents.noaa.gov/api/datagetter' 
    correct_params = {
        'product': 'predictions',
        'application': 'NOS.COOPS.TAC.WL',
        'begin_date': startDate,
        'end_date': endDate,
        'datum': 'MSL',
        'station': station_id,
        'time_zone': 'GMT',
        'units': 'metric',
        'interval': 'h',
        'format': 'csv'
    }


    tide_grabber = TideGrabber(startDate, endDate, saveDir, station_id)

    unsuccessful_response = Mock() 
    unsuccessful_response.status_code = 404

    with patch("requests.get", return_value=unsuccessful_response) as mock_get:
        with patch("builtins.print") as mock_print:
            response_content = None
            try:
                response_content = tide_grabber.request()
            except SystemExit as e:
                assert True 
                assert e.code == 1
            else:
                assert False, "unsuccessful request did not exit when expected to have"

            mock_get.assert_called_once_with(correct_url, correct_params)
            mock_print.assert_called_once_with(f'Failed to retrieve data: 404')
            assert response_content == None

def test_TideGrabber_saveResponse():
    """test the behavour of TideGrabber.saveResponse
    
    expected behaviour:
    saves a new file to savePath when nothing exists
    overwrites any file with save same name when it exists
    """
    tmp_dir = tempfile.TemporaryDirectory()

    startDate = "20240101"
    endDate = "20240131"
    saveDir = tmp_dir.name 
    station_id = '9440083'
    expected_savePath = os.path.join(saveDir, f"{startDate}_{endDate}_tides.csv")

    tide_grabber = TideGrabber(startDate, endDate, saveDir, station_id)

    initial_data = b'dates,tide\nvalue1,value2\nvalue3,value4'
    new_data = b'dates,tide\nvalue5,value6\nvalue7,value8'

    # it saves a new file in given dir 
    tide_grabber.saveResponse(initial_data)
    assert os.path.exists(expected_savePath)
    assert os.path.isfile(expected_savePath)
    with open(expected_savePath, 'rb') as f:
        contents = f.read()
        assert contents == initial_data

    # it overwrites an old file if it already exists
    tide_grabber.saveResponse(new_data)
    assert os.path.exists(expected_savePath)
    assert os.path.isfile(expected_savePath)
    with open(expected_savePath, 'rb') as f:
        contents = f.read()
        assert contents == new_data 

def test_TideGrabber_run():
    """unit test for tideGrabber.run()
    
    assert if it calls the necessary functions
    """

    startDate = "20240101"
    endDate = "20240131"
    saveDir = "path/to/saveDir"
    station_id = '9440083'

    mock_content = b'content'
    with patch('grabtide.TideGrabber.request', return_value=mock_content) as mock_request:
        with patch('grabtide.TideGrabber.saveResponse') as mock_saveResponse:
            tide_grabber = TideGrabber(startDate, endDate, saveDir, station_id)
            tide_grabber.run()

            mock_request.assert_called_once() 
            mock_saveResponse.assert_called_once_with(mock_content)

def test_integration_TideGrabber_run():
    """integration test for behaviour of TideGrabber.run()

    expect function to save the content of response to correct file path
    after querying to correct path

    basically an integration test for TideGrabber.request and TideGrabber.saveResponse
    """

    tmp_dir = tempfile.TemporaryDirectory()

    startDate = "20240101"
    endDate = "20240131"
    saveDir = tmp_dir.name 
    station_id = '9440083'

    tide_grabber = TideGrabber(startDate, endDate, saveDir, station_id)

    expected_savePath = os.path.join(saveDir, f"{startDate}_{endDate}_tides.csv")
    expected_columns = ["dates","tide"]


    tide_grabber.run()

    assert os.path.exists(expected_savePath)
    assert os.path.isfile(expected_savePath)
    with open(expected_savePath, mode='r', newline='', encoding='utf-8') as output:
        output = csv.reader(output)
        rows = list(output)

        # assert that we get the correct headers  
        assert rows[0] == expected_columns
        
        # assert that the first Date time is whats expected
        assert rows[1][0] == "2024-01-01 00:00"
        assert rows[-1][0] == "2024-01-31 23:00"

    


