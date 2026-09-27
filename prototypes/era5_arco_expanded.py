"""Fetch ERA5 MSLP on an EXPANDED domain (20-90N, 50W-60E, every 12 h) from the public ARCO-ERA5 mirror.

Why: the protocol window (30-75N, 30W-40E) cuts cyclones at its edges; the cut flanks become spurious boundary
minima (62% of ERA5 leaves, see prototypes/boundary.py). The expanded field lets prototypes/era5_expanded.py smooth
with real data beyond the window and keep only minima that are true local minima of the larger field.
Output layout matches prototypes/era5_arco.py (latitude descending, longitude -50..60, msl in Pa).
Run: .venv/bin/python prototypes/era5_arco_expanded.py 1999-11-17T00 2000-01-15T00 data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco_expanded.nc
     .venv/bin/python prototypes/era5_arco_expanded.py 2013-12-01T00 2014-02-01T00 data/real/ERA5_MSLP/ERA5_MSLP_20131201_20140131_12h_arco_expanded.nc
"""
from pathlib import Path
import sys
import numpy as np, xarray as xr
from netCDF4 import Dataset
from era5_arco import URL

LAT = (90., 20.); LON_W = (310., 359.75); LON_E = (0., 60.)


def main(start, end, out):
    OUTP = Path(out)
    if OUTP.exists(): print('exists, skip', OUTP); return
    ds = xr.open_zarr(URL, chunks=None, storage_options=dict(token='anon'))
    times = np.arange(np.datetime64(start), np.datetime64(end), np.timedelta64(12, 'h'))
    v = ds['mean_sea_level_pressure'].sel(time=times, latitude=slice(*LAT))
    west = v.sel(longitude=slice(*LON_W)); east = v.sel(longitude=slice(*LON_E))
    data = xr.concat([west, east], dim='longitude')
    lon = np.r_[west.longitude.values - 360, east.longitude.values]
    arr = data.values.astype(np.float32)
    ny, nx = arr.shape[1:]
    assert (ny, nx) == (281, 441) and np.isfinite(arr).all(), arr.shape
    tmp = OUTP.with_suffix('.part'); OUTP.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(tmp, 'w', format='NETCDF4') as nc:
        nc.createDimension('valid_time', len(times)); nc.createDimension('latitude', ny); nc.createDimension('longitude', nx)
        t = nc.createVariable('valid_time', 'i8', ('valid_time',)); t.units = 'seconds since 1970-01-01'; t.calendar = 'proleptic_gregorian'
        t[:] = ((times - np.datetime64('1970-01-01T00')) // np.timedelta64(1, 's')).astype(np.int64)
        la = nc.createVariable('latitude', 'f8', ('latitude',)); la[:] = data.latitude.values; la.units = 'degrees_north'
        lo = nc.createVariable('longitude', 'f8', ('longitude',)); lo[:] = lon; lo.units = 'degrees_east'
        m = nc.createVariable('msl', 'f4', ('valid_time', 'latitude', 'longitude'), zlib=True); m[:] = arr; m.units = 'Pa'
        nc.source = URL; nc.note = 'expanded-domain 12-hourly subset for RA-MTM prototypes'
    tmp.rename(OUTP)
    print(OUTP, arr.shape, f'{OUTP.stat().st_size/1e6:.1f} MB')


if __name__ == '__main__':
    main(*sys.argv[1:4])
