import os
import sys
import pymongo

from xml.etree import ElementTree as ET
from datetime import datetime
from dotenv import dotenv_values

# Usage: python3 setup_dbs.py env_path files_path
assert len(sys.argv) == 3, 'ERROR: Please provide the path to the env file and the path to the XML files as the second argument'
env_path = sys.argv[1]
files_path = sys.argv[2]

env_config = dotenv_values(env_path)

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
    ("fecha_publicacion", lambda x: datetime.strptime(x, "%Y%m%d")),
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
        text = element.text
        entry_json[tag] = parser(text) if parser is not None else text
    
    # get topics
    entry_json["materias"] = [topic.text for topic in xml.findall(".//materia")]

    # get references
    past_refs = []
    for ref in xml.findall(".//anterior"):
        past_refs.append({
            "identificador": ref.get("referencia"),
            "texto": ref.find("texto").text,
        })
    entry_json["anteriores"] = past_refs

    future_refs = []
    for ref in xml.findall(".//posterior"):
        future_refs.append({
            "identificador": ref.get("referencia"),
            "texto": ref.find("texto").text,
        })
    entry_json["posteriores"] = future_refs

    # get XML text
    xml_text = xml.find("texto")
    html_text = ET.tostring(xml_text, encoding='utf8', method="html").decode('utf8')
    html_text = "\n".join(html_text.split("\n")[1:-1])
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
for filepath in read_xml_files(files_path):
    # read file
    xml = ET.parse(filepath)
    entry_json = jsonify_boe_entry(xml)
    collection.insert_one(entry_json)
