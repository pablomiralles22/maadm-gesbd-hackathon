import pymongo
import sys
import argparse

from dotenv import dotenv_values
from elasticsearch import Elasticsearch

parser = argparse.ArgumentParser(
    prog='DB Setup',
    description=(
        'Create DBs for our setup.'
    ),
)
parser.add_argument('--env-file', default="./.env")
args = parser.parse_args()

env_config = dotenv_values(args.env_file)

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
collection.create_index([("materias", pymongo.DESCENDING)], name="materias_index")
collection.create_index([("fecha_publicacion", pymongo.ASCENDING)], name="date_index")
print('Done!')

##### ELASTICSEARCH #####
print('Setting up Elasticsearch...')
client = Elasticsearch(f"http://{env_config['ELASTICSEARCH_HOST']}:{env_config['ELASTICSEARCH_PORT']}")

es_index_configuration = {
    "settings": {
        "analysis": {
            "filter": {
                "spanish_stop": {
                    "type": "stop",
                    "stopwords": "_spanish_",
                },
                "spanish_stemmer": {
                    "type": "stemmer",
                    "language": "light_spanish",
                }
            },
            "analyzer": {
                "spanish_html_stripper": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "char_filter": [
                        "html_strip",
                    ],
                    "filter": [
                        "lowercase",
                        "spanish_stop",
                        "spanish_stemmer",
                    ]
                }
            }
        },
        "number_of_shards": 2,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "text": {
                "type": "text",
                "analyzer": "spanish_html_stripper",
            },
            "embedding": {
                "type": "dense_vector",
                "dims": env_config["EMBEDDING_DIM"],
                "similarity": "cosine",
                "index": True,
            },
            "boe-id": { "type": "keyword", }
        }
    }
}

elastic_search_index_name = "boe"
try:
    client.indices.delete(index=elastic_search_index_name)
    print("Index deleted. Recreating index...")
except:
    print("Index does not exist. Creating...")
try:
    client.indices.create(
        index = elastic_search_index_name,
        settings = es_index_configuration["settings"],
        mappings = es_index_configuration["mappings"]
    )
    print("Done!")
except Exception as error:
    print("Error:", error)
    
##### GRAPHDB #####