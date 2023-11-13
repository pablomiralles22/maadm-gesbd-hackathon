import pymongo
import argparse
import requests

from dotenv import dotenv_values
from elasticsearch import Elasticsearch
from SPARQLWrapper import SPARQLWrapper, POST

parser = argparse.ArgumentParser(
    prog='DB Setup',
    description=(
        'Create DBs for our setup.'
    ),
)
parser.add_argument('--env-file', default="./.env")
parser.add_argument('--graphdb-repo-init-file', default="rdf/graphdb_init.ttl")
parser.add_argument('--graphdb-init-query', default="rdf/graphdb_init_query.txt")
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
collection.create_index([("materias.codigo", pymongo.DESCENDING)], name="materias_index")
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
print('Setting up GraphDB...')

url = (
    f"http://{env_config['GRAPHDB_HOST']}:{env_config['GRAPHDB_PORT']}"
    f"/rest/repositories"
)

with open(args.graphdb_repo_init_file, 'r') as f:
    files=[ ('config', ('file', f, 'application/octet-stream') ) ]
    response = requests.request("POST", url, headers={}, data={}, files=files)

print(response.text)

##############

sparql = SPARQLWrapper(
    f"http://{env_config['GRAPHDB_HOST']}:{env_config['GRAPHDB_PORT']}"
    f"/repositories/{env_config['GRAPHDB_REPOSITORY']}/statements"
)
sparql.setMethod(POST)

with open(args.graphdb_init_query, 'r') as f:
    rdf_init = f.read()

sparql.setQuery(rdf_init)
print(sparql.query().info())