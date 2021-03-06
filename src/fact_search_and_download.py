#!/usr/bin/env python3
'''
    FACT Search and Download
    Copyright (C) 2017-2018  Fraunhofer FKIE

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import argparse
import json
import logging
import requests
import sys

from helper.logging import setup_logging
from helper.rest_download import download_file
from helper.rest_query import make_search_request_file, make_search_request_firmware, get_and_validate_query
from helper.storage import prepare_storage_dir


PROGRAM_NAME = 'FACT Search and Download'
PROGRAM_VERSION = '0.3'
PROGRAM_DESCRIPTION = 'This program finds and downloads files matching a specific query.'


def check_arguments():
    parser = argparse.ArgumentParser(description=PROGRAM_DESCRIPTION)
    parser.add_argument('-V', '--version', action='version', version='{} {}'.format(PROGRAM_NAME, PROGRAM_VERSION))
    parser.add_argument('-H', '--host', help='Change the host', default='http://localhost:5000')
    parser.add_argument('-q', '--query', help='A search query as a string', default=None)
    parser.add_argument('-Q', '--queryfile', help='A search query in a .json file', default=None)
    parser.add_argument('-F', '--firmware', action='store_true', help='download firmwares including files matching the query', default=False)
    parser.add_argument('-D', '--destination', help='store files in this folder', default='.')
    parser.add_argument('-d', '--debug', action='store_true', help='print debug messages', default=False)
    arguments = parser.parse_args()
    return arguments


def _make_search_request(host, query, firmware_flag):
    if firmware_flag:
        return make_search_request_firmware(host, query)
    else:
        return make_search_request_file(host, query)


def main():
    arguments = check_arguments()
    setup_logging(arguments.debug)
    try:
        search_query = get_and_validate_query(arguments.query, arguments.queryfile)
    except json.JSONDecodeError as e:
        sys.exit('Invalid json: {}'.format(e))
    except RuntimeError as e:
        sys.exit('No query given. Use -q or -Q option')
    host = arguments.host
    storage_directory = prepare_storage_dir(arguments.destination)
    try:
        search_result_json = _make_search_request(host, search_query, arguments.firmware)
    except (requests.RequestException, requests.HTTPError, requests.ConnectionError) as e:
        sys.exit('FACT not reachable: {}'.format(e))
    except json.JSONDecodeError as e:
        sys.exit('Server\'s response is invalid: {}'.format(e))
    except RuntimeError as e:
        sys.exit('Query not accepted: {}'.format(e))

    downloaded_files = 0
    logging.info('start download of {} files'.format(len(search_result_json['uids'])))
    for firmware_uid in search_result_json['uids']:
        if download_file(host, firmware_uid, storage_directory) is not None:
            downloaded_files = downloaded_files + 1
        if downloaded_files % 10 == 0 or downloaded_files == len(search_result_json['uids']):
            logging.info('{} / {}'.format(downloaded_files, len(search_result_json['uids'])))
    logging.info('Found {} files(s), downloaded {} files(s)'.format(len(search_result_json['uids']), downloaded_files))
    return 0


if __name__ == '__main__':
    exit(main())
