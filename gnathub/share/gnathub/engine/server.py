# GNAThub (GNATdashboard)
# Copyright (C) 2018, AdaCore
#
# This is free software;  you can redistribute it  and/or modify it  under
# terms of the  GNU General Public License as published  by the Free Soft-
# ware  Foundation;  either version 3,  or (at your option) any later ver-
# sion.  This software is distributed in the hope  that it will be useful,
# but WITHOUT ANY WARRANTY;  without even the implied warranty of MERCHAN-
# TABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for  more details.  You should have  received  a copy of the GNU
# General  Public  License  distributed  with  this  software;   see  file
# COPYING3.  If not, go to http://www.gnu.org/licenses for a complete copy
# of the license.

"""GNAThub plug-in for launching the WebUI server.

"""
from flask import Flask, request, make_response
from logging.config import dictConfig

import GNAThub
import os
import subprocess
import re

# To hide server banner, and so production warning.
import sys
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

# GLOBAL VARIABLE
# The repository where .json files are supposed to be located
SERVER_DIR_PATH = GNAThub.html_data()

OUTPUT_DIR = GNAThub.output_dir()
DB_DIR = GNAThub.db_dir()
OBJECT_DIR = GNAThub.Project.object_dir()
PROJECT_PATH = GNAThub.Project.path()
CODEPEER_OBJ_DIR = os.path.join(GNAThub.Project.object_dir(), 'codepeer')

# The info for the logs
GNATHUB_LOG = GNAThub.logs()
SERVER_LOG = os.path.join(GNATHUB_LOG, "webui_server.log")

STATIC_FOLDER = os.environ.get('WEBUI_HTML_FOLDER')
DEFAULT_PORT = 8080

# Create logging handlers
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s: %(message)s',
    }},
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': SERVER_LOG,
            'mode': 'a',
            'level': 'DEBUG',
            'formatter': 'default'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'default',
            'stream': 'ext://sys.stdout'
            }
    },
    'loggers': {
        'console': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': 'no'},
        'file': {
            'level': 'DEBUG',
            'handlers': ['file'],
            'propagate': 'no'
            }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
})


app = Flask(__name__, static_url_path='', static_folder=STATIC_FOLDER)


@app.route('/')
def root():
    return app.send_static_file('index.html')


@app.route('/json/<filename>', methods=['GET'])
def get_json(filename):
    serverpath = os.path.join(os.getcwd(), SERVER_DIR_PATH)
    filepath = ''

    # Find the path to the asked file
    for root, dirs, files in os.walk(serverpath):
        if filename in files:
            filepath = os.path.join(root, filename)

    if os.path.isfile(filepath):
        with open(filepath, 'r') as myFile:
            data = myFile.read()
            return data
    else:
        resp = make_response(404)
        return resp


@app.route('/source/<filename>', methods=['GET'])
def get_source(filename):
    serverpath = os.path.join(os.getcwd(), SERVER_DIR_PATH)
    filepath = ''
    # Find the path to the asked file
    for root, dirs, files in os.walk(serverpath):
        if filename in files:
            filepath = os.path.join(root, filename)
    if os.path.isfile(filepath):
        with open(filepath, 'r') as myFile:
            data = myFile.read()
            return data
    else:
        resp = make_response(404)
        return resp


@app.route('/get-review/<filename>', methods=['GET'])
def _get_review(filename):
    _export_codeper_bridge(filename)

    serverpath = os.path.join(os.getcwd(), SERVER_DIR_PATH)
    filepath = ''

    # Find the path to the asked file
    for root, dirs, files in os.walk(serverpath):
        if filename in files:
            filepath = os.path.join(root, filename)

    if os.path.isfile(filepath):
        with open(filepath, 'r') as myFile:
            data = myFile.read()
            return data
    else:
        resp = make_response("Not Found", 404)
        return resp


@app.route('/get-race-condition', methods=['GET'])
def _get_race_condition():
    serverpath = os.path.join(os.getcwd(), SERVER_DIR_PATH)
    filename = 'race_conditions.xml'
    filepath = ''

    # Find the path to the asked file
    for root, dirs, files in os.walk(serverpath):
        if filename in files:
            filepath = os.path.join(root, filename)

    if os.path.isfile(filepath):
        with open(filepath, 'r') as myFile:
            data = myFile.read()
            return data
    else:
        return make_response("Not Found", 404)


def _export_codeper_bridge(filename):
    app.logger.info("Export info from codepeer_bridge")
    name = 'codepeer_bridge'
    cmd = ['codepeer_bridge',
           '--output-dir=' + OUTPUT_DIR,
           '--db-dir=' + DB_DIR,
           '--export-reviews=' + os.path.join(
               GNAThub.Project.object_dir(),
               'gnathub', 'html-report',
               'data', filename)]
    GNAThub.Run(name, cmd, out=SERVER_LOG, append_out=True)


@app.route('/online-server', methods=['GET'])
def _get_online():
    app.logger.info("Flask server is online and reachable")
    resp = make_response("OK", 200)
    return resp


def getCodepeerVersion(data):
    tmp = ""
    try:
        tmp = re.match(".* ([0-9]+\.[0-9]+[w]?) .*", data).groups()[0]
    except Exception as e:
        print e
    return tmp


@app.route('/codepeer-passed', methods=['GET'])
def _get_codepeer():
    cmd = 'codepeer' + ' -v'
    output = subprocess.check_output(cmd, shell=True)
    actual_version = getCodepeerVersion(output)
    old_version = ""

    version_path = os.path.join(CODEPEER_OBJ_DIR, 'version.txt')

    if os.path.isfile(version_path):
        with open(version_path, 'r') as myFile:
            old_version = myFile.read()
    else:
        app.logger.error("File version.txt not found.")

    if (actual_version != "" and actual_version == old_version):
        app.logger.debug("Codepeer executable found and good version used")
        resp = make_response("OK", 200)
        return resp
    elif (actual_version != ""):
        app.logger.debug("Codepeer executable found but bad version used")
        resp = make_response("OK", 202)
        return resp
    else:
        app.logger.debug("Codepeer executable not found")
        resp = make_response("NOT OK", 204)
        return resp


@app.route('/post-review/', methods=['POST'])
def _post_review():
    temp_filename = 'user_review_temp.xml'
    post_data = request.data
    app.logger.info(post_data)

    app.logger.info("Create user_review_temp.xml")
    tempFile = open(temp_filename, "wb")
    tempFile.write(post_data)
    tempFile.close()

    _import_codepeer_bridge(temp_filename)

    app.logger.info("Remove user_review_temp.xml")
    os.remove(temp_filename)

    resp = make_response("OK", 200)
    return resp


def _import_codepeer_bridge(filename):
    app.logger.info("Import info into codepeer_bridge")
    name = 'codepeer_bridge'
    cmd = ['codepeer_bridge',
           '--output-dir=' + OUTPUT_DIR,
           '--db-dir=' + DB_DIR,
           '--import-reviews=' + filename]
    GNAThub.Run(name, cmd, out=SERVER_LOG, append_out=True)


@app.route('/<path:other>')
def fallback(other):
    app.logger.error("Bad request used.")
    app.logger.error(other)
    return make_response("Wrong request", 404)


if __name__ == '__main__':
    flask_port = GNAThub.port() if GNAThub.port() else DEFAULT_PORT

    if flask_port > 1024:
        print "Launching flask server on port {}".format(flask_port)
        print "Logs redirected to {}".format(SERVER_LOG)
        # TODO : Error occur when lauching with debug=True
        # app.run(port=flask_port, debug=True)
        app.run(host='0.0.0.0', port=flask_port, threaded=True)
    else:
        app.logger.error("Bad port used. Please relauch with port above 1024.")
        print "Please use a port above 1024"
