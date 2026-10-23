This Python repository contains multiple utility functions that allow for geospatial operations. 

# Installation 

Installation requires conda. Run the following code in your terminal to install dependencies 

```bash
git clone https://github.com/mickymags/gis_dev
cd gis_dev
conda env create -f geospatial_utils.yaml
```

# Usage 

Different functions can be called from the command line. You can see the different functions that are available by running 

```bash
python geospatial_main.py -h
```

### GeoJSON Creator 

Variables indicated by <<>> indicate things that need to be replaced with your own variables. 

python geospatial_main.py geojson_creator --outfile <<OUTFILE>> --xmin <<XMIN>> --ymin <<YMIN>> --xmax <<XMAX>> --ymax <<YMAX>>




