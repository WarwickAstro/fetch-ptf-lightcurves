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
import urllib.request
import numpy as np

PTF_QUERY_URL = "http://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query?catalog=ptf_lightcurves"\
    "&spatial=cone&radius=2&radunits=arcsec&constraints=(fid%3D{})AND(goodflag%3D1)"\
    "&selcols=hmjd,mag_autocorr,mag_auto,magerr_auto,fwhm_image,fwhmsex,xpeak_image,ypeak_image,"\
    "ra,dec&outfmt=1&objstr={},{}"

def get_filter(raw_data):
    # Start by excluding any points that are nan ('null' magnitude in the PTF database)
    # or negative ('null' zero point -> 0 in the PTF database)
    filt = raw_data['mag_autocorr'] > 0

    # We also want to discard anything that is more than twice the average field FWHM
    fwhm_ratio = raw_data['fwhm_image'] / raw_data['fwhmsex']
    filt = np.logical_and(filt, fwhm_ratio < 1.5)

    # Points within 5px of the edge of the frame are also bad
    filt = np.logical_and(filt, raw_data['xpeak_image'] > 5)
    filt = np.logical_and(filt, raw_data['xpeak_image'] < 2043)
    filt = np.logical_and(filt, raw_data['ypeak_image'] > 5)
    filt = np.logical_and(filt, raw_data['ypeak_image'] < 4091)

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

def generate_lightcurve(target_ra, target_dec, filt, output):
    print('Input arguments:')
    print('   Target RA:', target_ra)
    print('  Target Dec:', target_dec)
    print('      Filter:', filt)
    fid = 2 if filt == 'R' else 1

    print('Querying data from IRSA...')
    print('URL is:', PTF_QUERY_URL.format(fid, target_ra, target_dec))
    data_request = urllib.request.urlopen(PTF_QUERY_URL.format(fid, target_ra, target_dec))

    # Table contains both \ and | style comments, which genfromtxt can't handle
    # Instead read line by line and manually filter comments before loading data
    lines = [line for line in data_request.readlines() if line[0] != 92 and line[0] != 124]

    # Defaults for if there are no acceptable points
    reference_hmjd = -2400000.5
    outdata = np.empty(0)
    excluded_points = 0
    median_absolute_correction = 0

    # Write just the file header if there are no data
    if lines:
        data = np.array(np.genfromtxt(lines, usecols=(0, 1, 2, 3, 4, 5, 6, 7), dtype=[
            ('hmjd', 'f8'), ('mag_autocorr', 'f8'), ('mag_auto', 'f8'), ('magerr_auto', 'f8'),
            ('fwhm_image', 'f8'), ('fwhmsex', 'f8'),
            ('xpeak_image', 'f8'), ('ypeak_image', 'f8')]))

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
    header += 'Filter: {}\n'.format(filt)
    header += 'Reference HJD(UTC?): {}\n'.format(reference_hmjd + 2400000.5)
    header += 'Excluded (bad mag / FWHM / correction): {}\n'.format(excluded_points)
    header += 'Median absolute correction (mag): {:.4f}\n'.format(median_absolute_correction)
    header += 'HJD(UTC?) Mag  Error'

    np.savetxt(output, outdata, fmt='%.5f', header=header)
    print('Saved to', output)

if __name__ == '__main__':
    parser = ap.ArgumentParser(
        description="Generate a lightcurve from publicly available PTF data.")
    parser.add_argument('ra',
                        type=str,
                        help='Target RA (decimal degrees or sexagesimal).')
    parser.add_argument('dec',
                        type=str,
                        help='Target Dec (decimal degrees or sexagesimal).')
    parser.add_argument('filter',
                        type=str,
                        choices=set(('R', 'g')),
                        default='R',
                        help='Filter to query.')
    parser.add_argument('output',
                        type=str,
                        help='Output data file.')
    args = parser.parse_args()
    generate_lightcurve(args.ra, args.dec, args.filter, args.output)
