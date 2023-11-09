# Notas sobre MongoDB
- Uso de índice con ID y materias por posibles casos de uso.
- Uso de índices por fecha, para las *queries* de ingesta en otros sistemas, y para un posible uso de comprobación diaria. La otra opción era usar booleanos, pero ocupan espacio. Además, no hay tantas entradas por día, es una buena unidad a considerar para la ingesta.