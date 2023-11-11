# Instrucciones de uso

## 1. Levantar el entorno en Docker
Copiar `example.env` a `.env` y levantar con `compose`.
```
cp example.env .env
docker-compose up
```

## 2. Configurar las bases de datos
Lanzar el script `setup_dbs`. Este requiere del archivo `.env` que se utilice, y de los archivos para inicializar el repositorio de GraphDB.
```
python scripts/setup_dbs.py --env-file .env --graphdb-repo-init-file rdf/graphdb_init.ttl --graphdb-init-query rdf/graphdb_init_query.txt
```

## 3. Scrapear datos del BOE
Lanzar el script de *scrapping*. Este admite tres parámetros: el directorio donde guardar los ficheros, y dos fechas que definen el rango de días en el que scrapear. Por ejemplo:
```
 python scripts/scrape.py --target-path downloads -s 2023-11-10 -e 2023-11-11
```
Recomendamos no descargar muchos días, especialmente de cara a la carga en ElasticSearch que requiere de *embeddings* costosos de calcular.

## 4. Cargar datos en bases de datos
La carga de los datos en BBDD se realiza en los scripts `load_mongodb`, `load_elasticsearch` y `load_graphdb`. Estos scripts comparten ciertos parámetros ya que requieren: archivo `.env` (`--env-file`), feha de inicio `-s` y fecha fin `-e`.
Las fechas pueden estar o no presentes: Si se incluyen los parámetros `-s` y `-e`, se debe señalar que se va a indicar un rango inluyendo `dates` antes de estos flags. Si no se indica el rango de fechas se ha de indicar `full` para procesar todos los archivos independientemente de las fechas.

### 4.1 Cargar datos en MongoDB
Lanzar el script `load_mongodb`. Además de los parámetros mencionados, este script recibe `--path` indicando la ruta de los xml a insertar en MongoDB. 
```
 python scripts/load_mongodb.py --path downloads dates -s 2023-11-10 -e 2023-11-11
```

### 4.2 Cargar datos en ElasticSearch
Lanzar el script `load_elasticsearch`. Carga datos desde MongoDB a ElasticSearch. El script recibe también el parámetro `-c` o `--char-threshold`, donde se indica el tamaño mínimo del párrafo para ElasticSearch (`20` por defecto).
```
 python scripts/load_elasticsearch.py -c 20 dates -s 2023-11-10 -e 2023-11-11
```

### 4.3 Cargar datos en GraphDB
Lanzar el script `load_graphdb`. Carga datos desde MongoDB a GraphDB. Este script recibe los parámetros por defecto.
```
 python scripts/load_graphdb.py dates -s 2023-11-10 -e 2023-11-11
```

## 5. Jugar con los ejemplos de *queries*
En la carpeta `working_examples` se encuentran dos *notebooks* con ejemplos de *queries* que se pueden hacer y ser de utilidad a un usuario final.