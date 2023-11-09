import argparse
import pymongo

from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from xml.etree import ElementTree as ET
from datetime import datetime
from dotenv import dotenv_values

##### Parse arguments #####
parser = argparse.ArgumentParser(
    prog='ESLoad',
    description=('Performs an insertion of the selected MongDB entries of the BOE.'),
)

parser.add_argument('--env-file', default="./.env")
parser.add_argument('-c', '--char-threshold', type=int, default=20, help="Min number of characters to be considered a paragraph.")

subparsers = parser.add_subparsers(dest="command", help="Provide the start and end date to select from MongoDB.")
subparsers.required = True

date_mode_parser = subparsers.add_parser("dates")
date_mode_parser.add_argument('-s', '--start-date', default=datetime.today().strftime('%Y-%m-%d'))
date_mode_parser.add_argument('-e', '--end-date', default=datetime.today().strftime('%Y-%m-%d'))

full_mode_parser = subparsers.add_parser("full")

args = parser.parse_args()
env_config = dotenv_values(args.env_file)

##### Connect to DBs #####
es_client = Elasticsearch(f"http://{env_config['ELASTICSEARCH_HOST']}:{env_config['ELASTICSEARCH_PORT']}")

mongo_client = pymongo.MongoClient(
    host=env_config['MONGODB_HOST'],
    port=int(env_config['MONGODB_PORT']),
    username=env_config['MONGO_USER'],
    password=env_config['MONGO_PASSWORD'],
)
mongo_collection = mongo_client["boe_db"]["boe"]


###### Semantic embeddings ######
model = SentenceTransformer(env_config["SENTENCE_TRANSFORMER_MODEL"])

###### Inserting into Elasticsearch ######
def load(document):
    soup = BeautifulSoup(document['texto'], "html.parser")
    doc_id = document['identificador']

    print(f"Processing {doc_id}...")
    for par in soup.find_all('p'):
        # ignore nested paragraphs
        if len(par.find_all("p")) > 0: continue
        text = par.get_text().strip()
        if len(text) < args.char_threshold: continue

        document = {
            "doc_id": doc_id,
            "embedding": model.encode(text),
            "text": text,
        }

        try:
            es_client.index(index="boe", document = document)
        except Exception as e:
            print(f"Error while processing {doc_id}, paragraph {text}. Got {e}.")

def main():
    query = {}
    if args.command == "dates":
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        query = {
            "fecha_publicacion": {
                "$gte": start_date,
                "$lte": end_date,
            }
        }

    for document in mongo_collection.find(query):
        try:
            load(document)
        except Exception as e:
            print(f"Error while processing {document['identificador']}. Got {e}.")


if __name__ == "__main__":
    main()