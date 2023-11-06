import pymongo
from elasticsearch import Elasticsearch
import sys

from dotenv import dotenv_values

# Usage: python3 setup_dbs.py env_path
assert len(sys.argv) == 2, 'ERROR: Please provide the path to the env file as the first argument.'
env_path = sys.argv[1]


env_config = dotenv_values(env_path)

##### MONGODB #####
print('Setting up MongoDB...')

client_mongo = pymongo.MongoClient(
    host=env_config['MONGODB_HOST'],
    port=int(env_config['MONGODB_PORT']),
    username=env_config['MONGO_USER'],
    password=env_config['MONGO_PASSWORD'],
)
db = client_mongo["boe_db"]
collection = db["boe"]

collection.create_index([("identificador", pymongo.DESCENDING)], name="id_index", unique=True)
print('Done!')

##### ELASTICSEARCH #####
print('Setting up Elasticsearch...')
client = Elasticsearch(f"http://{env_config['ELASTICSEARCH_HOST']}:{env_config['ELASTICSEARCH_PORT']}")

es_config = {
    "mappings": {
        "properties": {
            "texto": {
                "type": "text"
            },
            "semantic_embeddig": {
                "type": "dense_vector",
                "dims": 512,
                "index": True,
                "similarity": "cosine"
            },
            #"titulo": {"type": "text"},
            "doc_id": {"type": "text"},
            #"fecha_publicacion": {"type": "date"}
        }
    },
    "settings": {
        "analysis": {
            "analyzer": {
                "my_analyzer": {
                "tokenizer": "keyword",
                "char_filter": [
                    "html_strip"
                ]
                }
            }
        },
        "number_of_shards": 2,
        "number_of_replicas": 1
    }
}

my_index = "boe"
try:
    client.indices.delete(index=my_index)
    print("Index deleted. Recreating index...")
except:
    print("Index does not exist. Creating...")
try:
    client.indices.create(
        index = my_index,
        settings = es_config["settings"],
        mappings = es_config["mappings"]
    )
except Exception as error:
    print("Error:", error)
finally:
    print("Done!")
##### GRAPHDB #####