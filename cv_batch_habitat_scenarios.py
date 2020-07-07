import logging
import os
import argparse
import sys

from natcap.invest import coastal_vulnerability

logging.basicConfig(
    level=logging.DEBUG,
    format=(
        '%(asctime)s (%(relativeCreated)d) %(levelname)s %(name)s'
        ' [%(funcName)s:%(lineno)d] %(message)s'),
    stream=sys.stdout)
LOGGER = logging.getLogger(__name__)
logging.getLogger('taskgraph').setLevel(logging.INFO)
logging.getLogger().addHandler(logging.FileHandler('logfile.txt'))


AOI_PATTERN = 'aoi.shp'  # all AOI's should have this filename pattern
HABITAT_TABLE_NAME = 'habitat_CV.csv'


def generate_base_args(base_data_dir):
    # Here's where all the non-changing inputs are defined.
    # Edit values here as-needed. 
    args = {
        'bathymetry_raster_path': os.path.join(base_data_dir, 'bathy_GEBCO_2014_global_NAD83.tif'),
        'dem_averaging_radius': '900',
        'dem_path': os.path.join(base_data_dir, 'DEM_SRTM_90m_MAR_v4.tif'),
        'geomorphology_fill_value': '4',
        'geomorphology_vector_path': os.path.join(base_data_dir, 'geomorph_MAR_v4_shift_BZ_MX.shp'),
        'landmass_vector_path': os.path.join(base_data_dir, 'landmass_adjusted_clipped_shift_BZ_MX_NAD83.shp'),
        'max_fetch_distance': '30000',
        'model_resolution': '10000',
        'population_radius': '500',
        'population_raster_path': os.path.join(base_data_dir, 'WorldPop_2019_MAR.tif'),
        'shelf_contour_vector_path': os.path.join(base_data_dir, 'continental_shelf_global_NAD83.shp'),
        'wwiii_vector_path': os.path.join(base_data_dir, 'WaveWatchIII_global_unprocessed_NAD83.shp'),
    }
    return args


def run_invest(aoi_path, habitat_table_path, suffix, output_dir):
    """Execute CV with a given AOI."""
    args['aoi_vector_path'] = aoi_path
    args['habitat_table_path'] = habitat_table_path
    args['results_suffix'] = suffix
    args['workspace_dir'] = output_dir

    try:
        coastal_vulnerability.execute(args)
    except Exception as e:
        LOGGER.error(f'Something went wrong during {scenario}')
        LOGGER.error(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='CV batch scenarios')
    parser.add_argument(
        '--aoi_dir', type=str, required=True,
        help='path to directory with an AOI and scenario subfolders')
    parser.add_argument(
        '--base_data_dir', type=str, required=True,
        help='path to a directory that contains all the data that '
             'is shared across scenarios & AOIs')
    parser.add_argument(
        '--output_dir', type=str, required=True,
        help='path to an output directory that will be created if '
             'it does not exist. This directory will get a subfolder '
             'for each scenario.')

    args = parser.parse_args()
    # Make the output directory. If it already exists, do nothing
    try:
        os.makedirs(args.output_dir)
    except OSError:
        pass

    # Find the AOI shapefile in the country directory
    files = os.listdir(args.aoi_dir)
    aoi = [x for x in files if x.endswith(AOI_PATTERN)]
    if not aoi:
        raise ValueError(
            f'aoi_dir ({args.aoi_dir}) does not contain an aoi shapefile')
    elif len(aoi) != 1:
        raise ValueError(
            f'aoi_dir ({args.aoi_dir}) contains multiple aoi shapefiles: {aoi}')
    else:
        aoi_path = os.path.join(args.aoi_dir, aoi[0])
        LOGGER.info(f'Found AOI: {aoi_path}')

    # Find the scenario subfolders
    scenarios = [x for x in files if os.path.isdir(
        os.path.join(args.aoi_dir, x))]
    LOGGER.info(f'Found Scenarios: {scenarios}')

    # Get all the CV args that are the same across scenarios
    cv_args = generate_base_args(args.base_data_dir)
    cv_args['aoi_vector_path'] = aoi_path

    for scenario in scenarios:
        # Insert all the CV args that are unique to each scenario
        habitat_table_path = os.path.join(
            args.aoi_dir, scenario, HABITAT_TABLE_NAME)
        cv_args['habitat_table_path'] = habitat_table_path
        cv_args['results_suffix'] = scenario
        cv_args['workspace_dir'] = args.output_dir

        LOGGER.info(
            f'\n'
            f'------------------------------------------------------------\n'
            f'                    STARTING {scenario}                     \n'
            f'------------------------------------------------------------\n')
        coastal_vulnerability.execute(cv_args)
