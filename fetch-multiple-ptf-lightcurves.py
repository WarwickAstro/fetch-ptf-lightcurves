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
# pylint: disable=missing-docstring

import argparse as ap
import concurrent.futures
import os
import subprocess
import sys
import time
import numpy as np

if __name__ == '__main__':
    parser = ap.ArgumentParser(
        description="Fetch multiple PTF lightcurves from an input CSV file.")
    parser.add_argument('input',
                        type=str,
                        help='Path to csv file. Columns should be name, ra, dec.')
    parser.add_argument('filter',
                        type=str,
                        choices=set(('R', 'g')),
                        default='R',
                        help='Filter to query.')
    parser.add_argument('outdir',
                        type=str,
                        help='Path to a directory to save generated lightcurves.')
    parser.add_argument('--concurrent-queries',
                        type=int,
                        default=3,
                        help='Maximum number of queries to run in parallel.')
    args = parser.parse_args()

    targets = np.genfromtxt(args.input, delimiter=',', dtype='str', skip_header=1)

    def run_query(ra, dec, outpath):
        try:
            path = os.path.join(os.path.dirname(sys.argv[0]), 'fetch-ptf-lightcurve.py')
            subprocess.check_output([path, ra, dec, args.filter, outpath], universal_newlines=True)
        except subprocess.CalledProcessError:
            print('Failed to query ' + outpath)

    skipped_jobs = 0
    print('Querying lightcurves...')
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrent_queries) as ex:
        jobs = []
        for t in targets:
            datafile = os.path.join(args.outdir, t[0]+'_ptf.dat')
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
