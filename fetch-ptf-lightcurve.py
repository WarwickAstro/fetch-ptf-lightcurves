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

import numpy as np
import os
import sys
import urllib.request

PTF_QUERY_URL = "http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query?catalog=ptf_lightcurves"\
    "&spatial=cone&radius=2&radunits=arcsec&constraints=(fid%3E1)AND(goodflag%3E0)"\
    "&selcols=hmjd,mag_autocorr,mag_auto,magerr_auto,fwhm_image,fwhmsex,ra,dec&outfmt=1&objstr={},{}"

def print_usage(name):
    """Prints the utility help"""
    print('Usage: {} command'.format(name))
    print()
    print('    {} ra dec outputfile'.format(name))
    print()
    print('  Generate a R-band lightcurve from publically available PTF data')
    print()
    print('  ra and dec can be in any format understood by the query API (decimal degrees, ' \
        'sexagesimal, etc')
    return 1

def get_filter(raw_data):
    # Start by excluding any points that are nan ('null' magnitude in the PTF database)
    # or negative ('null' zero point -> 0 in the PTF database)
    filt = raw_data['mag_autocorr'] > 0

    # We also want to discard anything that is more than twice the average field FWHM
    fwhm_ratio = raw_data['fwhm_image'] / raw_data['fwhmsex']
    filt = np.logical_and(filt, fwhm_ratio < 1.5)

    # Finally any points that had more than 0.5 mag photometry correction
    filt = np.logical_and(filt, abs(raw_data['mag_autocorr'] - raw_data['mag_auto']) < 0.5)

    n = 0
    mean = None
    while True:
        if n > 50:
            print("Failed to converge on FWHM cut after 50 iterations")
            break

        # Filter discarded all the points!
        if np.sum(filt) == 0:
            break

        last_mean = mean
        mean = np.mean(fwhm_ratio[filt])
        std = np.std(fwhm_ratio[filt])
        filt = np.logical_and(filt, fwhm_ratio <= (mean + 3*std))
        n += 1

        if mean == last_mean:
            break

    return filt

if __name__ == '__main__':
    if len(sys.argv) > 3:
        target_ra = sys.argv[1]
        target_dec = sys.argv[2]
        output = sys.argv[3]
        print('Input arguments:')
        print('  Target RA:', target_ra)
        print('  Target Dec:', target_dec)

        print('Querying data from IRSA...')
        print('URL is:', PTF_QUERY_URL.format(target_ra, target_dec))
        data_request = urllib.request.urlopen(PTF_QUERY_URL.format(target_ra, target_dec))

        # Table contains both \ and | style comments, which genfromtxt can't handle
        # Instead read line by line and manually filter comments before loading data
        lines = [line for line in data_request.readlines() if line[0] != 92 and line[0] != 124]

        # Defaults for if there are no acceptable points
        reference_hmjd = -2400000.5
        outdata = np.empty(0)
        excluded_points = 0
        median_absolute_correction = 0

        # Write just the file header if there are no data
        if len(lines) > 0:
            data = np.array(np.genfromtxt(lines, usecols=(0, 1, 2, 3, 4, 5), dtype=[
                ('hmjd', 'f8'), ('mag_autocorr', 'f8'), ('mag_auto', 'f8'), ('magerr_auto', 'f8'),
                ('fwhm_image', 'f8'), ('fwhmsex', 'f8')]))

            good_points = get_filter(data)
            if np.sum(good_points) > 0:
                hmjd = data['hmjd'][good_points]
                reference_hmjd = np.min(hmjd)
                outdata = np.transpose((hmjd - reference_hmjd,
                                        data['mag_autocorr'][good_points],
                                        data['magerr_auto'][good_points]))

                outdata = outdata[outdata[:, 0].argsort()]
                excluded_points = len(data) - np.sum(good_points)
                median_absolute_correction = np.median(abs(data['mag_autocorr'] - data['mag_auto']))

        header = 'get-gator-lightcurve.py output file\n'
        header += 'RA: {}\n'.format(target_ra)
        header += 'Dec: {}\n'.format(target_dec)
        header += 'Reference HJD(UTC?): {}\n'.format(reference_hmjd + 2400000.5)
        header += 'Excluded (bad mag / FWHM / correction): {}\n'.format(excluded_points)
        header += 'Median absolute correction (mag): {:.4f}\n'.format(median_absolute_correction)
        header += 'HJD(UTC?) Mag  Error'

        np.savetxt(output, outdata, fmt='%.5f', header=header)
        print('Saved to', output)
    else:
        sys.exit(print_usage(os.path.basename(sys.argv[0])))
