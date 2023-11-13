# Notas sobre MongoDB
- Uso de índice con ID y materias por posibles casos de uso.
- Uso de índices por fecha, para las *queries* de ingesta en otros sistemas, y para un posible uso de comprobación diaria. La otra opción era usar booleanos, pero ocupan espacio. Además, no hay tantas entradas por día, es una buena unidad a considerar para la ingesta.


## Schema

```json
{
	"title": "BOE entry",
	"type": "object",
	"properties": {
		"titulo": {
			"type": "string"
		},
		"fecha_publicacion": {
			"type": "date"
		},
		"identificador": {
			"type": "string"
		},
		"texto": {
			"type": "string"
		},
		"rango": {
			"type": "object",
			"properties": {
			    "codigo": {"type": "string"},
			    "texto": {"type": "string"}
			}
		},
		"origen_legislativo": {
			"type": "object",
			"properties": {
			    "codigo": {"type": "string"},
			    "texto": {"type": "string"}
			}
		},
		"materias": {
			"type": "array",
		    "properties": {
			    "codigo": {"type": "string"},
			    "texto": {"type": "string"}
			}
		},
		"anteriores": {
			"type": "array",
		    "properties": {
			    "identificador": {"type": "string"},
			    "texto": {"type": "string"},
			    "relacion": {
			        "type": "object",
			        "properties": {
			            "codigo": {"type": "string"},
			            "texto": {"type": "string"}
			        }
			    }
			}
		},
		"posteriores": {
			"type": "array",
		    "properties": {
			    "identificador": {"type": "string"},
			    "texto": {"type": "string"},
			    "relacion": {
			        "type": "object",
			        "properties": {
			            "codigo": {"type": "string"},
			            "texto": {"type": "string"}
			        }
			    }
			}
		}
	}
}
```