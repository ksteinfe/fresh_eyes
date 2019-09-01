import os

# env variable must be set in the anaconda environment, as per https://conda.io/docs/user-guide/tasks/manage-environments.html#saving-environment-variables
DATA_PATH = os.environ['FRESH_EYES_DATA_PATH']
PRIMARY_DATA_PATH = os.path.join(DATA_PATH,'datasets_primary')

geojson_path = os.path.join(PRIMARY_DATA_PATH,'microsoft_us_building_footprints','geojson')

print(os.listdir(geojson_path))