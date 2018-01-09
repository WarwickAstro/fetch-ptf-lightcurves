Python scripts to fetch photometry from the iPTF lightcurve database and filter several classes of known bad points.

```
usage: fetch-ptf-lightcurve.py [-h] ra dec {g,R} output

Generate a lightcurve from publicly available PTF data.

positional arguments:
  ra          Target RA (decimal degrees or sexagesimal).
  dec         Target Dec (decimal degrees or sexagesimal).
  {g,R}       Filter to query.
  output      Output data file.

optional arguments:
  -h, --help  show this help message and exit
```

```
usage: fetch-multiple-ptf-lightcurves.py [-h]
                                         [--concurrent-queries CONCURRENT_QUERIES]
                                         input {R,g} outdir

Fetch multiple PTF lightcurves from an input CSV file.

positional arguments:
  input                 Path to csv file. Columns should be name, ra, dec.
  {R,g}                 Filter to query.
  outdir                Path to a directory to save generated lightcurves.

optional arguments:
  -h, --help            show this help message and exit
  --concurrent-queries CONCURRENT_QUERIES
                        Maximum number of queries to run in parallel.
```

```
usage: refetch-ptf-lightcurve.py [-h] input output

Regenerate a queried PTF lightcurve.

positional arguments:
  input       Path to the previously generated lightcurve.
  output      Path to save new lightcurve.

optional arguments:
  -h, --help  show this help message and exit

```
