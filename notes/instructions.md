# Instrucciones de uso

## 1. Levantar el entorno en Docker
Primero se debe ir a la carpeta `environment`. Copiar `example.env` a `.env` y levantar con `compose`.
```
cp example.env .env
docker-compose up
```

## 2. Configurar las bases de datos
Lanzar el script `setup_dbs` con el archivo de entorno como primera variable_
```
cp example.env .env
python3 setup_dbs environment/.env
```

## 3. Cargar datos en las bases de datos
