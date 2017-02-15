#!/usr/bin/env python3
#
# Copyright (C) 2017 Paul Chote
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=invalid-name

import concurrent.futures
import numpy as np
import os
import subprocess
import sys
import time

CONCURRENT_DOWNLOAD_COUNT = 3

def print_usage(name):
    """Prints the utility help"""
    print('Usage: {} command'.format(name))
    print()
    print('    {} input outputdir'.format(name))
    print()
    print('  Download lightcurves from PTF')
    print()
    print('  input is the path to a csv file with rows of name, ra, dec.')
    print('  output is the directory where downloaded files are saved.')
    return 1

if __name__ == '__main__':
    if len(sys.argv) > 2:
        targets = np.genfromtxt(sys.argv[1], delimiter=',', dtype='str', skip_header=1)
        output = sys.argv[2]

        def run_query(ra, dec, outpath):
            try:
                path = os.path.join(os.path.dirname(sys.argv[0]), 'fetch-ptf-lightcurve.py')
                subprocess.check_output([path, ra, dec, outpath], universal_newlines=True)
            except subprocess.CalledProcessError:
                print('Failed to query ' + outpath)
                pass

        skipped_jobs = 0
        print('Querying lightcurves...')
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOAD_COUNT) as ex:
            jobs = []
            for t in targets:
                datafile = output + '/' + t[0]+'_ptf.dat'
                if not os.path.isfile(datafile):
                    jobs.append(ex.submit(run_query, t[1], t[2], datafile))
                else:
                    skipped_jobs += 1

            total_jobs = len(jobs)
            while True:
                completed = sum(j.done() for j in jobs)
                if completed == total_jobs:
                    break

                all_complete = skipped_jobs + completed
                all_total = skipped_jobs + total_jobs
                all_percent = int(round(all_complete * 100. / all_total, 0))
                sys.stdout.write('Downloading {}/{} ({}%)\r'.format(all_complete, all_total,
                                                                    all_percent))
                time.sleep(5.)
            ex.shutdown()
    else:
        sys.exit(print_usage(os.path.basename(sys.argv[0])))
