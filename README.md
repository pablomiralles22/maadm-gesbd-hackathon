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

### 4.1 Cargar datos en MongoDB

### 4.2 Cargar datos en ElasticSearch

### 4.3 Cargar datos en GraphDB

## 5. Jugar con los ejemplos de *queries*
En la carpeta `working_examples` se encuentran dos *notebooks* con ejemplos de *queries* que se pueden hacer y ser de utilidad a un usuario final.