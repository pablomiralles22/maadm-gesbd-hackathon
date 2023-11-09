# Notas sobre la implementación en ElasticSearch

- Se pierde la búsqueda en documento completo, lo que afecta a la frecuencia de un término. Un término puede aparecer mucho en un solo párrafo de un texto muy grande, y no aparecer en el resto. Este documento aparecería muy arriba en los resultados.
- Uso de *key-value store cache* posiblemente para no tener que guardar el título con cada párrafo.