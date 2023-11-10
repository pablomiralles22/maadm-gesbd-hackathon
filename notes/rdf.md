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

- Ley
    - codigo: str
    - nombre: str
    - definida_en: EntradaBOE

- RelacionPosterior
    - codigo
    - descripcion

- RelacionAnterior
    - codigo
    - descripcion


Otras tuplas:
* EntradaBOE - RelacionPosterior concreta - EntradaBOE
* EntradaBOE - RelacionAnterior concreta - EntradaBOE


## Notas de implementaciñon
- Estado, ComunidadAutonoma, Localidad espero poder encontrarlos en otras bases de datos
- Además, creo que se le puede poner cardinalidad
- Las referencias (anterior y posterior) pueden apuntar a entradas "DOUE", que no sé lo que son, pero hay que filtrarlas.