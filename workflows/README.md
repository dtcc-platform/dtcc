DTCC Workflows
----------------------------

## workflow_sanjay
### 1\. Setting up the Conda Environment

-   Create a new conda environment with the following command:
    `conda env create -f workflow_sanjay.yml`

### 2\. Preparing the Data

-   Obtain the necessary data from Lantmäteriet.
-   Place the data in the following directories within the `workflows` directory:
    -   `data/dem_data` for DEM data (.tif)
    -   `data/landuse_data` for land use data (.shp)
    -   `data/road_data` for road data (.shp)

### 3\. Activating the Conda Environment

-   Activate the conda environment using:
    `conda activate dtcc_fme_workflow`

### 4\. Navigate to the Workflows Directory

-   Change to the `workflows` directory:
    `cd path/to/workflows`

### 5\. Run the Workflow Script

-   Execute the `workflow_sanjay.py` script using:
    `python workflow_sanjay.py`

Upon successful execution, this will produce a new folder named `unreal_tiles` within the `workflows` directory.