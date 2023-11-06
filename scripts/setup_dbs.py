import pymongo
import sys

from dotenv import dotenv_values

# Usage: python3 setup_dbs.py env_path
assert len(sys.argv) == 2, 'ERROR: Please provide the path to the env file as the first argument.'
env_path = sys.argv[1]


env_config = dotenv_values(env_path)

##### MONGODB #####
print('Setting up MongoDB...')

client = pymongo.MongoClient(
    host=env_config['MONGODB_HOST'],
    port=int(env_config['MONGODB_PORT']),
    username=env_config['MONGO_USER'],
    password=env_config['MONGO_PASSWORD'],
)
db = client["boe_db"]
collection = db["boe"]

collection.create_index([("identificador", pymongo.DESCENDING)], name="id_index", unique=True)
print('Done!')

##### ELASTICSEARCH #####


##### GRAPHDB #####