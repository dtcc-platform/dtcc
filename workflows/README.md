DTCC Workflows
----------------------------

## workflow_sanjay
### 1\. Setting up the Conda Environment

-   Create a new conda environment with the following command:
    `conda env create -f workflow_sanjay.yaml`

    or 
    
    `python -m venv dtcc_fme_workflow`

    `source dtcc_fme_workflow/bin/activate`

    `pip install -r workflow_sanjay.txt`

    `deactivate`

### 2\. Preparing the Data

-   Obtain the necessary data from Lantmäteriet.
-   Place the data in the following directories within the `workflows` directory:
    -   `data/dem_data` for DEM data (.tif)
    -   `data/landuse_data` for land use data (.shp)
    -   `data/road_data` for road data (.shp)
    -   `data/overlay_data` for road data (.zip) (hardcoded for TV noise data by SWECO) 
    
    Note: Noise data can be found at : `GIS-data Buller\Buller_ljudutbredning\ <select one scenario>`

### 3\. Activating the Conda Environment

-   Activate the conda environment using:
    `conda activate dtcc_fme_workflow`

    or

    `source dtcc_fme_workflow/bin/activate`


### 4\. Navigate to the Workflows Directory

-   Change to the `workflows` directory:
    `cd path/to/workflows`

### 5\. Run the Workflow Script

-   Execute the `workflow_sanjay.py` script using:
    `python workflow_sanjay.py`

Upon successful execution, this will produce a new folder named `unreal_tiles` within the `workflows` directory.
