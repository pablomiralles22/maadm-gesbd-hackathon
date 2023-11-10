import os
import sys
import re
import pymongo
import argparse

from xml.etree import ElementTree as ET
from datetime import datetime, timedelta
from dotenv import dotenv_values

###### Parse arguments #######
parser = argparse.ArgumentParser(
    prog='MongoLoad',
    description=(
        'Performs an insertion of the selected XML entries of the BOE. '
        'The file structure of the directory with the files should match ',
        'the one given by the scraping script.'
    ),
)

parser.add_argument('--path', default="downloads")
parser.add_argument('--env-file', default="./.env")

subparsers = parser.add_subparsers(dest="command", help="Provide the start and end date to insert in MongoDB.")
subparsers.required = True

date_mode_parser = subparsers.add_parser("dates")
date_mode_parser.add_argument('-s', '--start-date', default=datetime.today().strftime('%Y-%m-%d'))
date_mode_parser.add_argument('-e', '--end-date', default=datetime.today().strftime('%Y-%m-%d'))

full_mode_parser = subparsers.add_parser("full")

args = parser.parse_args()
path = args.path
env_config = dotenv_values(args.env_file)

###### Parsing XML ######
def read_xml_files(path):
    for r, _, f in os.walk(path):
        for file in f:
            if '.xml' not in file or "BOE" not in file:
                continue
            yield os.path.join(r, file)

METADATA_FIELDS = [
    ("identificador", None),
    ("titulo", None),
    ("departamento", None),
    ("fecha_publicacion", lambda elem: datetime.strptime(elem, "%Y%m%d")),
    ("origen_legislativo", None),
    ("rango", None),
]

def jsonify_boe_entry(xml):
    entry_json = {}

    # get metadata
    metadata = xml.find("metadatos")
    for tag, parser in METADATA_FIELDS:
        element = metadata.find(tag)
        if element is None: continue
        text = parser(element.text) if parser is not None else element.text
        code = element.get("codigo")
        entry_json[tag] = text if code is None else {"codigo": code, "texto": text}
    
    # get topics
    entry_json["materias"] = [
        {
            "codigo": topic.get("codigo"),
            "texto": topic.text,
        }
        for topic in xml.findall(".//materia")
    ]

    # get references
    past_refs = []
    for ref in xml.findall(".//anterior"):
        past_refs.append({
            "identificador": ref.get("referencia"),
            "texto": ref.find("texto").text,
            "relacion": {
                "codigo": ref.find("palabra").get("codigo"),
                "texto": ref.find("palabra").text,
            }
        })
    entry_json["anteriores"] = past_refs

    future_refs = []
    for ref in xml.findall(".//posterior"):
        future_refs.append({
            "identificador": ref.get("referencia"),
            "texto": ref.find("texto").text,
            "relacion": {
                "codigo": ref.find("palabra").get("codigo"),
                "texto": ref.find("palabra").text,
            }
        })
    entry_json["posteriores"] = future_refs

    # get XML text
    xml_text = xml.find("texto")
    html_text = ET.tostring(xml_text, encoding='utf8', method="html").decode('utf8')
    html_text = re.sub(r"</?texto>", "", html_text).strip()
    entry_json["texto"] = html_text

    return entry_json

###### Setting up MongoDB ######
client = pymongo.MongoClient(
    host=env_config['MONGODB_HOST'],
    port=int(env_config['MONGODB_PORT']),
    username=env_config['MONGO_USER'],
    password=env_config['MONGO_PASSWORD'],
)
db = client["boe_db"]
collection = db["boe"]


###### Inserting into MongoDB ######
def insert_for_path(path):
    for filepath in read_xml_files(path):
        # read file
        xml = ET.parse(filepath)
        entry_json = jsonify_boe_entry(xml)

        try:
            collection.insert_one(entry_json)
        except pymongo.errors.DuplicateKeyError:
            print(f"Skipping {entry_json['identificador']}, already inserted.")
        except Exception as e:
            print(f"Unexpected error {e}.")

def main():
    if args.command == "dates":
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

        date = start_date
        while date <= end_date:
            path = os.path.join(args.path, date.strftime('%Y/%m/%d'))
            insert_for_path(path)
            date += timedelta(days=1)
    else:
        insert_for_path(args.path)

if __name__ == "__main__":
    main()