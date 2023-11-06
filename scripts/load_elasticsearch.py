import os
import sys
from elasticsearch import Elasticsearch
from transformers import T5Model, T5Tokenizer

from xml.etree import ElementTree as ET
from datetime import datetime
from dotenv import dotenv_values
import pprint

# Usage: python3 load_elasticsearch.py env_path files_path
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

    # get paragraphs
    entry_json["parrafos"] = [paragraph.text for paragraph in xml_text.findall(".//p")]

    return entry_json


def get_embeddings(input_text, model, tokenizer, max_length=512):
    enc = tokenizer(input_text, return_tensors='pt', truncation=True, max_length=max_length)
    output = model.encoder(
        input_ids=enc['input_ids'],
        attention_mask=enc['attention_mask'],
        return_dict=True
        )
    return output.last_hidden_state.tolist()[0][0]

##### Setting up ELASTICSEARCH #####
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

###### Semantic embeddings ######
model = T5Model.from_pretrained('t5-small')
tokenizer = T5Tokenizer.from_pretrained('t5-small')

###### Inserting into Elasticsearch ######
for filepath in read_xml_files(files_path):
    # read file
    xml = ET.parse(filepath)
    entry_json = jsonify_boe_entry(xml)

    fecha = entry_json['fecha_publicacion']
    doc_id = entry_json['identificador']
    print(f"Processing {doc_id}...")

    for i, text in enumerate(entry_json['parrafos']):
        if text is not None: semantic_embeddigs = get_embeddings(text, model, tokenizer)
        document = {
                "doc_id": doc_id,
                "embeddings": semantic_embeddigs,
                "texto": text,
                #"fecha_publicacion": fecha,
                #"full_text": full_text,
                #"titulo": titulo
            }

        try:
            client.index(
                index = my_index,
                document = document
            )
        except Exception as e:
            print(e)
            print(f"len: {len(document)}")
            print(id)
            print(document)
    break