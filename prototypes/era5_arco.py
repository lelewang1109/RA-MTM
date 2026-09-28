"""Fetch the ERA5 MSLP frames used by the RA-MTM protocol from the public ARCO-ERA5 mirror.

Source : gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3 (anonymous,
         Google Cloud public dataset of ECMWF ERA5, 0.25 deg hourly).
Subset : mean_sea_level_pressure, 30-75N, 30W-40E, 1999-11-17 00:00 .. 2000-01-14 12:00
         every 12 h (the 118 frames experiments/era5.py::extract(step=12) uses).
Output : data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc (git-ignored),
         laid out like the CDS file (latitude descending, longitude -30..40, msl in Pa,
         valid_time in seconds since 1970-01-01). Byte hash differs from the CDS file;
         equivalence is checked by reproducing the collaborator's shared features.
"""
from pathlib import Path
import numpy as np, xarray as xr
from netCDF4 import Dataset

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/real/ERA5_MSLP/ERA5_MSLP_19991117_20000114_12h_arco.nc'
import sys
URL = 'gs://gcp-public-data-arco-era5/ar/full_37-1h-0p25deg-chunk-1.zarr-v3'


def main(start='1999-11-17T00', end='2000-01-15T00', out=OUT):
    """Default = the protocol period; pass start/end (exclusive) and an output path for other winters."""
    OUTP = Path(out)
    ds = xr.open_zarr(URL, chunks=None, storage_options=dict(token='anon'))
    times = np.arange(np.datetime64(start), np.datetime64(end), np.timedelta64(12, 'h'))
    v = ds['mean_sea_level_pressure'].sel(time=times, latitude=slice(75, 30))
    west = v.sel(longitude=slice(330, 359.75)); east = v.sel(longitude=slice(0, 40))
    data = xr.concat([west, east], dim='longitude')
    lon = np.r_[west.longitude.values - 360, east.longitude.values]
    arr = data.values.astype(np.float32)                       # triggers the download
    assert arr.shape == (len(times), 181, 281) and np.isfinite(arr).all(), arr.shape
    OUTP.parent.mkdir(parents=True, exist_ok=True)
    with Dataset(OUTP, 'w') as nc:
        nc.createDimension('valid_time', len(times)); nc.createDimension('latitude', 181); nc.createDimension('longitude', 281)
        t = nc.createVariable('valid_time', 'i8', ('valid_time',)); t.units = 'seconds since 1970-01-01'; t.calendar = 'proleptic_gregorian'
        t[:] = ((times - np.datetime64('1970-01-01T00')) // np.timedelta64(1, 's')).astype(np.int64)
        la = nc.createVariable('latitude', 'f8', ('latitude',)); la[:] = data.latitude.values; la.units = 'degrees_north'
        lo = nc.createVariable('longitude', 'f8', ('longitude',)); lo[:] = lon; lo.units = 'degrees_east'
        m = nc.createVariable('msl', 'f4', ('valid_time', 'latitude', 'longitude'), zlib=True); m[:] = arr; m.units = 'Pa'
        nc.source = URL; nc.note = '12-hourly subset for RA-MTM prototypes; not byte-identical to the CDS file'
    print(OUTP, arr.shape, float(arr.min()), float(arr.max()), f'{OUTP.stat().st_size/1e6:.1f} MB')


if __name__ == '__main__':
    main(*sys.argv[1:4]) if len(sys.argv) > 1 else main()
