import os
import subprocess
from os.path import dirname
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

from flask import Flask, request, render_template
from subprocess import check_output
from uuid import uuid4
import json
from subprocess import Popen


wsgi_app = Flask(__name__)


@wsgi_app.route('/')
def index():
    return render_template('index.html')


@wsgi_app.route('/mm_abc', methods=['POST'])
def mm_abc():
    key = uuid4()
    tmp = Path(mkdtemp())

    try:
        # read config from post json data
        config = request.json
        config_fname = tmp / f'{key}.json'
        data_fname = tmp / f'{key}.csv'

        # write config file
        with open(config_fname, 'w') as config_fp:
            json.dump({
                'file_name': {'file': str(data_fname)},
                'experiment_details': {**config},
                'abc_details': {**config},
            }, config_fp)

        # write data file
        with open(data_fname, 'w') as data_fp:
            data_fp.writelines(config['data'])

        # run mm_abc.py ...
        script = f'{dirname(__file__)}/mm_abc.py'
        proc = Popen(['python3', script],
                     cwd=tmp,
                     stdout=subprocess.PIPE,
                     stdin=subprocess.PIPE,
                     stderr=subprocess.PIPE)
        stdout, _ = proc.communicate(input=str(config_fname).encode())

        # exit early in case of errors
        if proc.returncode:
            return {
                'returncode': proc.returncode,
                'output': stdout.decode()
            }

        # read results and return results
        with open(tmp / 'results.txt') as results_fp:
            output = results_fp.read()
        return {
            'returncode': proc.returncode,
            'output': output
        }
    finally:
        rmtree(tmp)


if __name__ == '__main__':
    wsgi_app.run(
        host='0.0.0.0',
        port='1337',
        debug=os.environ['DEBUG']
    )
