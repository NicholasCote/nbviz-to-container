#!/usr/bin/env python
# coding: utf-8

# # Interactive dashboard for Sentinel-2 satellite imagery
# ---

import os
import pandas as pd
import numpy as np
import xarray as xr
import pystac_client
import planetary_computer
import panel as pn
import panel.widgets as pnw
import hvplot.xarray
import holoviews as hv
import geoviews as gv
from pystac.extensions.eo import EOExtension as eo
import datetime
from cartopy import crs
from dask.distributed import Client, LocalCluster
import odc.stac

xr.set_options(keep_attrs=True)
hv.extension('bokeh')
gv.extension('bokeh')

cluster = LocalCluster()
client = Client(cluster)
client

stac_root = 'https://planetarycomputer.microsoft.com/api/stac/v1'
catalog = pystac_client.Client.open(
    stac_root,
    modifier=planetary_computer.sign_inplace
)

sentinel2_collections = [collection for collection in catalog.get_collections() if "sentinel-2" in collection.id]
sentinel2_collections

bbox = [-105.283263,39.972809,-105.266569,39.987640] # NCAR, boulder, CO. bbox from http://bboxfinder.com/
date_range = "2022-01-01/2022-12-31"
collection = "sentinel-2-l2a"                        # full id of collection
cloud_thresh = 30

search = catalog.search(
    collections = sentinel2_collections,
    bbox = bbox,
    datetime = date_range,
    query={"eo:cloud_cover": {"lt": cloud_thresh}}
)
items = search.item_collection()

first_item = items.items[0]
all_bands = list(first_item.assets.keys())
print("Assets available:")
print(*all_bands, sep=', ')

bands_of_interest = [b for b in all_bands if b.startswith('B')]

da = odc.stac.stac_load(
    items,
    bands=bands_of_interest,
    bbox=bbox,
    chunks={},  # <-- use Dask
).to_array(dim='band')

def harmonize_to_old(data):  
    """
    Harmonize new Sentinel-2 data to the old baseline.

    Parameters
    ----------
    data: xarray.DataArray
        A DataArray with four dimensions: time, band, y, x

    Returns
    -------
    harmonized: xarray.DataArray
        A DataArray with all values harmonized to the old
        processing baseline.
    """
    cutoff = datetime.datetime(2022, 1, 25)
    offset = 1000
    bands = ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12"]

    old = data.sel(time=slice(cutoff))

    to_process = list(set(bands) & set(data.band.data.tolist()))
    new = data.sel(time=slice(cutoff, None)).drop_sel(band=to_process)

    new_harmonized = data.sel(time=slice(cutoff, None), band=to_process).clip(offset)
    new_harmonized -= offset

    new = xr.concat([new, new_harmonized], "band").sel(band=data.band.data.tolist())
    return xr.concat([old, new], dim="time")

da = harmonize_to_old(da)

da = da / 1e4   # Scale data values from 0:10000 to 0:1.0
da = da / da.max(dim='band')  # additionally scale from 0-max -> 0-1 for visual quality
da = da.compute()

def plot_band(band, cmap):
    return da.sel(band=band).isel(time=0).hvplot(
        x='x', y='y', data_aspect=1, 
        cmap=cmap, geo=True, tiles='ESRI', 
        crs=crs.epsg(items[0].properties['proj:epsg']), rasterize=True,
        title=f"band: {band}, cmap: {cmap}",
        clabel='surface reflectance [0.0-1.0]'
    ).opts(
        frame_width=300,
        xlabel='longitude',
        ylabel='latitude',
        
    )

def rgb_during(time):
    season_names = {
        1: 'Winter',
        2: 'Spring',
        3: 'Summer',
        4: 'Fall'
    }
    da_rgb = da.sel(band=['B04', 'B03', 'B02'])
    start_date = pd.to_datetime(da_rgb['time'].min().data).to_pydatetime()
    end_date = pd.to_datetime(da_rgb['time'].max().data).to_pydatetime()
    closest_date = pd.to_datetime(da_rgb.sel(time=time, method='nearest').time.data).to_pydatetime()
    dt_slider = pnw.DateSlider(name='Date', start=start_date, end=end_date, value=closest_date)
    
    def get_obs_on(t):
        season_key = [month%12 // 3 + 1 for month in range(1, 13)][t.month-1]
        season = season_names[season_key]
        return da.sel(band=['B04', 'B03', 'B02']).sel(time=t, method='nearest').transpose('y', 'x', 'band').hvplot.rgb(
            x='x', y='y', bands='band', 
            geo=True, tiles='ESRI', crs=crs.epsg(items[0].properties['proj:epsg']), 
            rasterize=True, title=f"{season}: {t.strftime('%Y-%m-%d')}"
        ).opts(
            frame_width=300,
            xlabel='longitude',
            ylabel='latitude',
        )
        
    
    return pn.panel(pn.Column(
                pn.bind(get_obs_on, t=dt_slider), 
                pn.Row(
                    pn.Spacer(width=60),
                    dt_slider,
                )
            ))

winter = '2022-01-15'
spring = '2022-04-30'
summer = '2022-08-01'
fall = '2022-09-15'

winter_plot = rgb_during(winter)
spring_plot = rgb_during(spring)
summer_plot = rgb_during(summer)
fall_plot = rgb_during(fall)

pn.Column(
    pn.Row(winter_plot, spring_plot),
    pn.Row(summer_plot, fall_plot)
).servable()
