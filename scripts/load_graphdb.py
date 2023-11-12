import argparse
import pymongo
import re

from datetime import datetime
from dotenv import dotenv_values
from SPARQLWrapper import SPARQLWrapper, POST

##### Parse arguments #####
parser = argparse.ArgumentParser(
    prog='ESLoad',
    description=('Performs an insertion of the selected MongDB entries of the BOE.'),
)

parser.add_argument('--env-file', default="./.env")

subparsers = parser.add_subparsers(dest="command", help="Provide the start and end date to select from MongoDB.")
subparsers.required = True

date_mode_parser = subparsers.add_parser("dates")
date_mode_parser.add_argument('-s', '--start-date', default=datetime.today().strftime('%Y-%m-%d'))
date_mode_parser.add_argument('-e', '--end-date', default=datetime.today().strftime('%Y-%m-%d'))

full_mode_parser = subparsers.add_parser("full")

args = parser.parse_args()
env_config = dotenv_values(args.env_file)

##### Connect to DBs #####
sparql = SPARQLWrapper(
    f"http://{env_config['GRAPHDB_HOST']}:{env_config['GRAPHDB_PORT']}"
    f"/repositories/{env_config['GRAPHDB_REPOSITORY']}/statements"
)
sparql.setMethod(POST)

mongo_client = pymongo.MongoClient(
    host=env_config['MONGODB_HOST'],
    port=int(env_config['MONGODB_PORT']),
    username=env_config['MONGO_USER'],
    password=env_config['MONGO_PASSWORD'],
)
mongo_collection = mongo_client["boe_db"]["boe"]


###### Auxiliar functions ######
def to_title_case(s):
    return re.sub(r"(\s+|[;,.'])", "", s.title())

def to_camel_case(s):
    title_case = to_title_case(s)
    return title_case[0].lower() + title_case[1:]

def encode_string(s):
    scaped = s.replace('"', '\\"')
    return f'"{scaped}"^^xsd:string'

def encode_integer(x):
    return f'"{x}"^^xsd:integer'

def encode_date(date):
    return f'"{date.strftime("%Y-%m-%d")}"^^xsd:date'

PREFIXES = """
PREFIX  :     <http://www.semanticweb.org/hackathon/ontology/>
PREFIX  owl:  <http://www.w3.org/2002/07/owl#>
PREFIX  rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX  xml:  <http://www.w3.org/XML/1998/namespace>
PREFIX  xsd:  <http://www.w3.org/2001/XMLSchema#>
PREFIX  rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""

semantic_tuple = lambda subject, predicate, object: f"{subject} {predicate} {object} ."

def insert_tuples(tuples):
    tuple_lines = "\n".join(tuples)
    query = PREFIXES + "INSERT DATA {\n" + tuple_lines + "\n}"
    sparql.setQuery(query=query)
    return sparql.query()

def create_legislative_source(type, name):
    entity_name = to_title_case(name)
    tuples = [
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:NamedIndividual"),
        semantic_tuple(f":{entity_name}", "rdf:type", f":{type}"),
        semantic_tuple(f":{entity_name}", ":nombre", encode_string(name)),
    ]
    return entity_name, tuples

def create_range(name, code):
    entity_name = to_title_case(name)
    tuples = [
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:NamedIndividual"),
        semantic_tuple(f":{entity_name}", "rdf:type", ":RangoLegislativo"),
        semantic_tuple(f":{entity_name}", ":nombre", encode_string(name)),
        semantic_tuple(f":{entity_name}", ":codigo", encode_integer(code)),
    ]
    return entity_name, tuples

def create_relationship_type(name, code, is_previous):
    entity_name = to_camel_case(name)
    tuples = [
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:ObjectProperty"),
        semantic_tuple(f":{entity_name}", "rdfs:domain", ":EntradaBOE"),
        semantic_tuple(f":{entity_name}", "rdfs:range", ":EntradaBOE"),
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:NamedIndividual"),
        semantic_tuple(f":{entity_name}", "rdf:type", ":RelacionAnterior" if is_previous else ":RelacionPosterior"),
        semantic_tuple(f":{entity_name}", ":codigo", encode_integer(code)),
        semantic_tuple(f":{entity_name}", ":nombre", encode_string(name)),
    ]
    return entity_name, tuples

def create_topic(name, code):
    entity_name = to_title_case(name)
    tuples = [
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:NamedIndividual"),
        semantic_tuple(f":{entity_name}", "rdf:type", ":Materia"),
        semantic_tuple(f":{entity_name}", ":nombre", encode_string(name)),
        semantic_tuple(f":{entity_name}", ":codigo", encode_integer(code)),
    ]
    return entity_name, tuples

def create_department(name, code):
    entity_name = to_title_case(name)
    tuples = [
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:NamedIndividual"),
        semantic_tuple(f":{entity_name}", "rdf:type", ":Departamento"),
        semantic_tuple(f":{entity_name}", ":nombre", encode_string(name)),
        semantic_tuple(f":{entity_name}", ":codigo", encode_integer(code)),
    ]
    return entity_name, tuples

def create_named_individual(name):
    tuples = [
        semantic_tuple(f":{name}", "rdf:type", "owl:NamedIndividual"),
    ]
    return name, tuples

def create_boe_entry(title, code, date, department, topics, previous, posteriors, legislative_source):
    entity_name = code
    tuples = [
        semantic_tuple(f":{entity_name}", "rdf:type", "owl:NamedIndividual"),
        semantic_tuple(f":{entity_name}", "rdf:type", ":EntradaBOE"),
        semantic_tuple(f":{entity_name}", ":titulo", encode_string(title)),
        semantic_tuple(f":{entity_name}", ":identificador", encode_string(code)),
        semantic_tuple(f":{entity_name}", ":fechaPublicacion", encode_date(date)),
    ]

    if department is not None: 
        department_entity_name, department_tuples = create_department(department["texto"], department["codigo"])
        tuples.extend(department_tuples)
        tuples.append(semantic_tuple(f":{entity_name}", ":departamento", f":{department_entity_name}"))
    
    legislative_source_name, legislative_source_tuples = None, None
    if legislative_source == "Estatal":
        legislative_source_name, legislative_source_tuples = create_legislative_source("Estado", "España")
    elif legislative_source == "Autonómico":
        legislative_source_name, legislative_source_tuples = create_legislative_source("ComunidadAutónoma", department['texto'])
    elif legislative_source == "Local":
        locality_match = re.search(r", (?:de la|del?) ([^,(]*)(:? \([^)]*\))?,", title)
        if locality_match is not None:
            locality = locality_match.group(1)
            legislative_source_name, legislative_source_tuples = create_legislative_source("Localidad", locality)
    
    if legislative_source_name is not None:
        tuples.extend(legislative_source_tuples)
        tuples.append(semantic_tuple(f":{entity_name}", ":origenLegislativo", f":{legislative_source_name}"))
    
    for topic in topics:
        topic_entity_name, topic_tuples = create_topic(topic["texto"], topic["codigo"])
        tuples.extend(topic_tuples)
        tuples.append(semantic_tuple(f":{entity_name}", ":materia", f":{topic_entity_name}"))
    for prev in previous:
        prev_entity_name, prev_tuples = create_relationship_type(prev["relacion"]["texto"], prev["relacion"]["codigo"], True)
        related_code = prev["identificador"]
        tuples.extend(prev_tuples)
        tuples.append(semantic_tuple(f":{entity_name}", f":{prev_entity_name}", f":{related_code}"))
    for post in posteriors:
        post_entity_name, post_tuples = create_relationship_type(post["relacion"]["texto"], post["relacion"]["codigo"], False)
        related_code = post["identificador"]
        tuples.extend(post_tuples)
        tuples.append(semantic_tuple(f":{entity_name}", f":{post_entity_name}", f":{related_code}"))

    return entity_name, tuples


###### Inserting into GraphDB ######

def load(document):
    print(f"Processing {document['identificador']}")
    title = document["titulo"]
    code = document["identificador"]
    date = document["fecha_publicacion"]
    department = document.get("departamento")
    topics = document.get("materias")
    previous = document.get("anteriores")
    posteriors = document.get("posteriores")
    try:
        origen_legislativo = document.get("origen_legislativo")['texto']
    except Exception as e:
        origen_legislativo = ""
    entity_name, tuples = create_boe_entry(title, code, date, department, topics, previous, posteriors, origen_legislativo)
    try:
        insert_tuples(tuples)
    except Exception as e:
        print(f"Error while inserting {entity_name}. Got {e}.")
        print("Tuples:")
        print("\n".join(tuples))

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
        load(document)

if __name__ == "__main__":
    main()