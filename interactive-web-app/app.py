#!/usr/bin/env python
# coding: utf-8

# # Interactive dashboard for Sentinel-2 satellite imagery
# ---

# ## Overview
# 
# In this notebook, we will take a look at how to retrieve Sentinel-2 L2A satellite imagery from the [Microsoft Planetary Computer Data Catalog (MSPC)](https://planetarycomputer.microsoft.com/catalog). We will go over how to interact with the Data Catalog, which exposes a [SpatioTemporal Asset Catalog (STAC)](https://stacspec.org/en) interface for querying, searching and retrieving data. We will use the [odc-stac](https://odc-stac.readthedocs.io/en/latest/) package to load the data lazily, which means data is not *actually* read unless required (say, for plotting). Once loaded, we will process the data and make a simple interactive dashboard to look at the satellite imagery over a location for different seasons. We will use the [HoloViz ecosystem](https://holoviz.org/background.html) for the interactive dashboard.

# ## Prerequisites
# 
# | Concepts | Importance | Notes |
# |---|---|---|
# |[Xarray](https://foundations.projectpythia.org/core/xarray.html)|Helpful|Background|
# |[Dask + Xarray](https://foundations.projectpythia.org/core/xarray/dask-arrays-xarray.html)|Necessary|Background|
# |[About the Microsoft Planetary Computer (MSPC)](https://planetarycomputer.microsoft.com/docs/overview/about/)|Helpful|Background|
# |[Documentation of pystac-client](https://pystac-client.readthedocs.io/en/stable/)|Helpful|Consult as needed|
# |[Landsat ML Cookbook](https://projectpythia.org/landsat-ml-cookbook/README.html)|Helpful|Similar cookbook, illustrates accessing Landsat data from MSPC|
# |[About the HoloViz ecosystem](https://holoviz.org/background.html)|Helpful|How different HoloViz packages work with each other|
# |[Sentinel-2 L2A User Guide](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/processing-levels/level-2)|Necessary|Background about the satellite data|
# |[Sentinel-2 L2A data definitions](https://sentinel.esa.int/documents/247904/685211/Sen2-Cor-L2A-Input-Output-Data-Definition-Document.pdf/e2dd6f01-c9c7-494d-a7f2-cd3be9ad891a?t=1506524754000)|Helpful|Section 2.3.10 has some useful information about the data we access in this cookbook|
# - **Time to learn**: 15 minutes

# ## Imports

# In[1]:


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


# Since we will use dask to distribute our computation, we can create a dask cluster and connect to it via a dask client. For this recipe, we will create a [`LocalCluster`](https://docs.dask.org/en/stable/deploying-python.html#localcluster) with default values.

# In[ ]:


cluster = LocalCluster()
client = Client(cluster)
client


# # Open the catalog

# The root of Microsoft Planetary Computer's STAC API endpoint is located at [https://planetarycomputer.microsoft.com/api/stac/v1](https://planetarycomputer.microsoft.com/api/stac/v1). We will load in the catalog using the `pystac_client.Client.open` method. Even though the STAC metadata in MSPC is publicly accessible, authentication is required to access the actual data. The `modifier` keyword can be used to explicitly "sign" an item, which basically means we can access the privately stored data (more information [here](https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/)).

# In[ ]:


stac_root = 'https://planetarycomputer.microsoft.com/api/stac/v1'
catalog = pystac_client.Client.open(
    stac_root,
    modifier=planetary_computer.sign_inplace
)
print(f"{catalog.title} - {catalog.description}")


# Let's search for any collections that have the substring "sentinel-2" in it to discover the sentinel-2 data.

# In[ ]:


sentinel2_collections = [collection for collection in catalog.get_collections() if "sentinel-2" in collection.id]
sentinel2_collections


# Looks like there is only one collection (`sentinel-2-l2a`) available in the catalog - which is the dataset we want to use.

# # Query, Filter and Load the collection

# Now that we have the ID of the collection of interest, we can specify certain filters to narrow down to exactly the data we want to look at. The final visualization in the recipe will look at how the NCAR Mesa Lab, Boulder CO looks like throughout the year as seen from space. To narrow down our search, we will use the following criteria -
# - Bounding box: We will limit our spatial extent to the bounding box of the NCAR Mesa Lab region.
# - Date range: We will look at the year 2022
# - Collection: `sentinel-2-l2a` (from previous cell)
# - Cloud threshold: Since cloud can block the satellite from making an observation of the ground, we will limit our search to satellite images where the cloud cover is less than a certain threshold, 40% in this case.
# 
# Feel free to change these filtering paramters to suit your needs when running in an interactive session.

# In[ ]:


bbox = [-105.283263,39.972809,-105.266569,39.987640] # NCAR, boulder, CO. bbox from http://bboxfinder.com/
date_range = "2022-01-01/2022-12-31"
collection = "sentinel-2-l2a"                        # full id of collection
cloud_thresh = 30


# In[ ]:


search = catalog.search(
    collections = sentinel2_collections,
    bbox = bbox,
    datetime = date_range,
    query={"eo:cloud_cover": {"lt": cloud_thresh}}
)
items = search.item_collection()
print(f"Found {len(items)} items in the {collection}")


# We now have an ItemCollection with the data that we need. Let's look at one of the items in the collection and explore what assets it has.

# In[ ]:


first_item = items.items[0]
all_bands = list(first_item.assets.keys())
print("Assets available:")
print(*all_bands, sep=', ')


# Seems like there are a lot of assets associated with the item - you can read about them [here](https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/processing-levels/level-2). We are interested in the assets that start with a 'B', which are the bands associated with the different spectral bands in which the [MultiSpectral Instrument (MSI)](https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/msi-instrument) of the satellite captures observations. Specifically, the RGB – or Red, Green and Blue - bands that we need to create a "True color" image are as follows:
# |band|corresponds to|
# |-|-|
# |B04|Red|
# |B03|Green|
# |B02|Blue|
# 
# We will use the `odc.stac.stac_load` function to load in the assets that start with the alphabet 'B'. This function will return a lazily-loaded `xr.DataSet` (using dask). For plotting purposes it is better if we have the data as a `xr.DataArray` instead with the bands as a dimension. We can do that using `.to_array(dim=<dim_name>)` method of a dataset.

# In[ ]:


bands_of_interest = [b for b in all_bands if b.startswith('B')]

da = odc.stac.stac_load(
    items,
    bands=bands_of_interest,
    bbox=bbox,
    chunks={},  # <-- use Dask
).to_array(dim='band')
da


# ## Prepare the data for visualization

# On January 25th, 2022, the European Space Agency (data provider for Sentinel-2 satellite) made a change in their processing pipeline to address some issues that you can read about [here](https://sentinels.copernicus.eu/web/sentinel/-/copernicus-sentinel-2-major-products-upgrade-upcoming) if interested. For the purpose of this notebook, we will process the newer dataset such that it is harmonized with the old processing pipeline - in simple words, we will make sure that the data has the same statistical properties so that we can visualize them seamlessly.

# In[ ]:


# from https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a#Baseline-Change
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
da


# Now that we have a harmonized dataset, we still need to process the data as follows:
# - Sentinel-2 L2A provides the Surface Reflectance (SR) data, which usually ranges from 0 (no reflection) to 1.0 (complete reflection). However, the actual values in the loaded dataset ranges from 0 to ~10,000. These data values need to be scaled to 0.0-1.0 by dividing the data by 10,000. More details can be found in [section 2.3.10 of this document](https://sentinel.esa.int/documents/247904/685211/Sen2-Cor-L2A-Input-Output-Data-Definition-Document.pdf/e2dd6f01-c9c7-494d-a7f2-cd3be9ad891a?t=1506524754000).
# 
# We will then explicitly trigger the dask computation using the `compute()` method and load the result into memory. This is to reduce repeated calls to retrieve data from MSPC. By loading the processed  This wouldn't have been possible if the dataset was large.

# In[ ]:


da = da / 1e4   # Scale data values from 0:10000 to 0:1.0
da = da / da.max(dim='band')  # additionally scale from 0-max -> 0-1 for visual quality
da = da.compute()


# We have now processed the data so that we can visualize it!
# 
# Let's look at the Blue, Green and Red bands.

# In[ ]:


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

(plot_band('B04', 'Blues') + plot_band('B03', 'Greens') + plot_band('B02', 'Reds')).cols(2)


# Let us make a dashboard composed of 4 different interactive plots showing the RGB view of the satellite observation for four different seasons.
# We need a function that will take a `time` input and does the following tasks:
#  1. plot an interactive RGB image of the data and overlay it on a map of the world.
#  2. provide a [date slider widget](https://panel.holoviz.org/reference/widgets/DateSlider.html) which can be used to interact with the plot.
#  3. only set the default value of the date slider to the `time`, but allow the user to slide through the length of the entire dataset.
# 
# Using this function, we will be able to compose the dashboard.

# In[ ]:


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


# In[ ]:


rgb_during('2022-02-01')


# Let's now compose a dashboard using `panel`.

# In[ ]:


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


# ---
# ## Summary
# In this recipe, we looked at how to access Sentinel-2 satellite data over a region of interest and create an interactive dashboard to visualize the data.
# 
# ### What's next?
# We plotted the RGB or True color image of our region of interest using a subset of all the bands available. We can further calculate useful indices, such as the [Normalized Difference Snow Index (NDSI)](https://nsidc.org/data/user-resources/help-center/what-ndsi-snow-cover-and-how-does-it-compare-fsc) or the [Normalized Difference Vegetation Index](https://en.wikipedia.org/wiki/Normalized_difference_vegetation_index).
# 
# ## Resources and references
# - Authored by Pritam Das ([@pritamd47](https://github.com/pritamd47)), June 2023 during Project Pythia cookoff 2023.
# - This notebook takes a lot of inspiration from the [Landsat ML Cookbook](https://github.com/ProjectPythia/landsat-ml-cookbook/) by Demetris Roumis.
# - This notebook uses concepts and code illustrated in the [Reading Data from the STAC API](https://planetarycomputer.microsoft.com/docs/quickstarts/reading-stac/).
