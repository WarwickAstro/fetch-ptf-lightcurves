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

import os
import subprocess
import sys

def print_usage(name):
    """Prints the utility help"""
    print('Usage: {} command'.format(name))
    print()
    print('    {} input output'.format(name))
    print()
    print('  Re-fetch a PTF lightcurve')
    print()
    return 1

if __name__ == '__main__':
    if len(sys.argv) > 2:

        with open(sys.argv[1]) as data:
            header = [next(data) for x in range(3)]
        ra = header[1].split(' ')[2][:-1]
        dec = header[2].split(' ')[2][:-1]
        outpath = sys.argv[2]

        path = os.path.join(os.path.dirname(sys.argv[0]), 'fetch-ptf-lightcurve.py')
        subprocess.check_output([path, ra, dec, outpath], universal_newlines=True)
    else:
        sys.exit(print_usage(os.path.basename(sys.argv[0])))
