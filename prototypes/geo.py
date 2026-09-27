"""Geographic helpers for ERA5 figures: map layout coordinates of the extraction protocol (spherical Lambert
cylindrical equal-area, standard parallel 52.5 deg, isotropic normalisation to a 120-unit span) and draw a
lat/lon graticule and field snapshots.
"""
import numpy as np
from netCDF4 import Dataset

R, PHI, C = 6371., 52.5, 120.


class Era5Geo:
    def __init__(self, nc_path, coords, grid=49):
        with Dataset(nc_path) as d:
            lat = np.asarray(d['latitude'][:]); lon = np.asarray(d['longitude'][:])
        self.lat0, self.lat1, self.lon0, self.lon1 = lat.min(), lat.max(), lon.min(), lon.max()
        self.co = np.cos(np.deg2rad(PHI))
        bx = R * self.co * np.deg2rad([self.lon0, self.lon1]); by = R * np.sin(np.deg2rad([self.lat0, self.lat1])) / self.co
        self.bx0, self.by0 = bx[0], by[0]
        self.factor = C / float(np.hypot(np.diff(bx)[0], np.diff(by)[0]))
        dx, dy = np.diff(bx)[0] / grid, np.diff(by)[0] / grid
        c = np.asarray(coords)
        self.offx = c[:, 0].min() - dx / 2 * self.factor; self.offy = c[:, 1].min() - dy / 2 * self.factor
        self.extent = [self.offx, self.offx + np.diff(bx)[0] * self.factor, self.offy, self.offy + np.diff(by)[0] * self.factor]

    def xy(self, lon, lat):
        X = R * self.co * np.deg2rad(lon); Y = R * np.sin(np.deg2rad(lat)) / self.co
        return (X - self.bx0) * self.factor + self.offx, (Y - self.by0) * self.factor + self.offy

    def graticule(self, ax, step=10, color='w', lw=.3, alpha=.6, labels=False):
        lats = np.linspace(self.lat0, self.lat1, 50); lons = np.linspace(self.lon0, self.lon1, 50)
        for lo in np.arange(np.ceil(self.lon0 / step) * step, self.lon1 + 1e-9, step):
            x, y = self.xy(np.full_like(lats, lo), lats); ax.plot(x, y, color=color, lw=lw, alpha=alpha)
            if labels: ax.text(x[0], y[0], f'{int(lo)}°', fontsize=5, color='#555555', ha='center', va='top')
        for la in np.arange(np.ceil(self.lat0 / step) * step, self.lat1 + 1e-9, step):
            x, y = self.xy(lons, np.full_like(lons, la)); ax.plot(x, y, color=color, lw=lw, alpha=alpha)
            if labels: ax.text(x[0], y[0], f'{int(la)}°', fontsize=5, color='#555555', ha='right', va='center')

    def coastlines(self, ax, path, color='k', lw=.35, alpha=.7):
        """Optional: Natural Earth coastline file (GeoJSON LineString/MultiLineString) if available."""
        import json
        try: gj = json.load(open(path))
        except Exception: return False
        for feat in gj.get('features', []):
            geom = feat['geometry']; parts = geom['coordinates'] if geom['type'] == 'MultiLineString' else [geom['coordinates']]
            for part in parts:
                a = np.asarray(part)
                m = (a[:, 0] >= self.lon0 - 1) & (a[:, 0] <= self.lon1 + 1) & (a[:, 1] >= self.lat0 - 1) & (a[:, 1] <= self.lat1 + 1)
                if m.sum() < 2: continue
                x, y = self.xy(np.where(m, a[:, 0], np.nan), np.where(m, a[:, 1], np.nan)); ax.plot(x, y, color=color, lw=lw, alpha=alpha)
        return True
