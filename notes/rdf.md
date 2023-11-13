# Notas sobre la parte de ontologías

- EntradaBOE
    - identificador: str
    - titulo: str
    - departamento: Departamento
    - fecha_publicacion: date
    - rango: RangoLegislativo
    - materias: Materia
    - origen_legislativo: Estado, ComunidadAutonoma, Localidad

- Materia
    - codigo
    - nombre

- Departamento
    - codigo
    - nombre

- RangoLegislativo
    - codigo
    - descripcion

- RelacionPosterior
    - codigo
    - descripcion

- RelacionAnterior
    - codigo
    - descripcion


**Otras tuplas**
* EntradaBOE - RelacionPosterior concreta - EntradaBOE
* EntradaBOE - RelacionAnterior concreta - EntradaBOE

**Entidades externas**
ComunidadAutonoma: http://es.dbpedia.org/resource/Comunidad_autónoma
Provincia: http://es.dbpedia.org/resource/Provincia_(España)
Localidad: http://es.dbpedia.org/resource/Localidad
Estado: http://es.dbpedia.org/resource/Estado


## Notas de implementaciñon
- Además, creo que se le puede poner cardinalidad a los atributos
- Las referencias (anterior y posterior) pueden apuntar a entradas "DOUE", que no sé lo que son, pero hay que filtrarlas.

## Plantuml equivalente
```plantuml
@startuml
' Classes with Data Properties as Attributes
class OrigenLegislativo {
  nombre: string
}

class Departamento {
  codigo: int
  nombre: string
}

class EntradaBOE {
  fechaPublicacion: dateTime
  identificador: string
  titulo: string
}

class Materia {
  codigo: int
  nombre: string
}

class RangoLegislativo {
  codigo: int
  descripcion: string
  nombre: string
}

class RelacionAnterior {
  codigo: int
  descripcion: string
}

class RelacionPosterior {
  codigo: int
  descripcion: string
}

' Object Properties
EntradaBOE "1" -- "0..*" Departamento : departamento
EntradaBOE "1" -- "0..*" OrigenLegislativo : origenLegislativo

EntradaBOE "1" -- "0..*" RangoLegislativo : rangoLegislativo
EntradaBOE "0..*" -- "0..*" Materia : sobreMateria

EntradaBOE "0..*" -r- "0..*" EntradaBOE
(EntradaBOE, EntradaBOE) .. DEROGA
DEROGA ..|> RelacionAnterior

Estado .u.|> OrigenLegislativo
ComunidadAutónoma .u.|> OrigenLegislativo
Localidad .u.|> OrigenLegislativo
@enduml
```