# Examen Parcial: Sistema de Gestión de Estacionamiento «AutoPark»

**Materia:** Programación I
**Carrera:** Tecnicatura Superior en Desarrollo de Software — 2.º Año  
**Instituto:** Instituto Roque González  
**Modalidad:** Individual  

---

## 1. Modalidad y alcance

Se debe desarrollar el sistema base descripto en esta consigna, respetando la modularización y las reglas de negocio. Además, cada estudiante debe elegir e implementar **al menos uno de los desafíos del Nivel 1** de la sección 8. Se pueden implementar desafíos adicionales.

La selección debe quedar indicada en la entrega. Los desafíos elegidos se integran al sistema base y deben poder demostrarse desde el menú o mediante los archivos de salida correspondientes.

## 2. Objetivo

La empresa de estacionamientos comerciales **AutoPark** necesita una aplicación modular de consola en Python que permita:

1. Registrar en ventanilla el cobro manual de un vehículo y guardar el comprobante en CSV.
2. Procesar por lote movimientos de vehículos almacenados en JSON, validar los datos, calcular las tarifas y producir reportes CSV.
3. Incorporar al menos uno de los desafíos individuales del Nivel 1.

## 3. Organización del proyecto

El programa debe estar modularizado y separar responsabilidades. Como referencia, se pueden utilizar módulos como:

- `main.py`: menú principal y coordinación del programa.
- `validaciones.py`: normalización y validación de patentes, tipos y horarios.
- `liquidaciones.py`: cálculo de estadías, beneficios e importes.
- `procesamiento.py`: lectura y procesamiento de movimientos JSON.
- `reportes.py`: escritura de CSV y presentación de métricas.

La distribución concreta de archivos puede variar, siempre que las responsabilidades estén separadas y el código sea fácil de mantener.

## 4. Archivos de entrada

El proyecto utiliza `tarifas.json` y `movimientos.json`.

### 4.1. `tarifas.json`

El archivo contiene una sección `configuracion` con estos valores:

| Clave                         | Valor | Uso                                                |
| ----------------------------- | ----: | -------------------------------------------------- |
| `minutos_bloque_inicial`      |    30 | Duración de cada bloque de las primeras dos horas. |
| `minutos_limite_primer_tramo` |   120 | Duración del primer tramo tarifario.               |
| `minutos_hora_adicional`      |    60 | Duración de cada bloque posterior al primer tramo. |
| `minutos_dia_completo`        |  1440 | Minutos de una jornada completa de 24 horas.       |

En la sección `tarifas`, cada categoría tiene precio por bloque inicial, precio por hora adicional, tope diario y precio de lavado:

| Tipo        | Bloque de 30 min | Hora adicional | Tope diario | Lavado |
| ----------- | ---------------: | -------------: | ----------: | -----: |
| `moto`      |             $400 |           $700 |      $9.000 | $2.500 |
| `auto`      |             $700 |         $1.200 |     $16.000 | $5.000 |
| `camioneta` |           $1.000 |         $1.800 |     $24.000 | $7.500 |

El programa debe leer los valores desde el archivo, en lugar de depender de importes escritos directamente en la lógica de cálculo.

### 4.2. `movimientos.json`

El objeto raíz contiene `fecha_operacion` con formato `AAAA-MM-DD` y una lista `movimientos`. Cada movimiento contiene:

| Campo             | Tipo / formato | Descripción                      |
| ----------------- | -------------- | -------------------------------- |
| `id`              | Texto          | Identificador del movimiento.    |
| `patente`         | Texto          | Patente del vehículo.            |
| `tipo_vehiculo`   | Texto          | `auto`, `moto` o `camioneta`.    |
| `entrada`         | Texto `HH:MM`  | Hora de ingreso.                 |
| `salida`          | Texto `HH:MM`  | Hora de salida.                  |
| `solicito_lavado` | Booleano       | Indica si se contrató el lavado. |

El archivo provisto contiene ejemplos de datos con mayúsculas o espacios en patentes y tipos, además de registros inválidos. La normalización debe aplicarse antes de decidir si esos valores son válidos.

## 5. Menú y funciones obligatorias

El menú principal debe ofrecer, como mínimo:

```text
==================================================
   SISTEMA DE GESTIÓN DE ESTACIONAMIENTO AUTOPARK
==================================================
1. Registrar cobro manual
2. Procesar lote de movimientos
3. Salir
Seleccione una opción:
```

Se deben agregar al menú las opciones necesarias para los desafíos individuales elegidos.

### 5.1. Cobro manual en ventanilla

1. Solicitar la patente y validarla.
2. Solicitar el tipo de vehículo: `auto`, `moto` o `camioneta`.
3. Preguntar cuántos días completos pasaron. El valor debe ser un entero no negativo.
   - Si es `0`, solicitar hora de entrada y hora de salida en formato `HH:MM`.
   - Si es mayor que `0`, liquidar por jornadas completas; no solicitar horarios.
4. Preguntar si se solicitó lavado (`S/N`).
5. Mostrar el detalle de la liquidación: duración, estacionamiento base, bonificación, lavado y total.
6. Agregar el registro a `liquidacion-manual.csv`, conservando las operaciones anteriores.

### 5.2. Procesamiento por lote

1. Leer `tarifas.json` y `movimientos.json`.
2. Validar y procesar cada movimiento por separado.
3. Guardar los movimientos válidos en `liquidacion.csv`.
4. Guardar los descartados en `rechazados.csv`, junto con el motivo del rechazo.
5. Mostrar en consola la cantidad procesada, la cantidad rechazada y el total recaudado.

Los errores de un movimiento no deben impedir que se procesen los demás registros del lote.

## 6. Validaciones y reglas de liquidación

### 6.1. Patentes y tipos de vehículo

Antes de validar una patente, quitar todos sus espacios y convertirla a mayúsculas. Solo se aceptan estos formatos:

- Tradicional: tres letras seguidas de tres números, por ejemplo `ABC123`.
- Mercosur: dos letras, tres números y dos letras, por ejemplo `AA123BB`.

El tipo de vehículo se normaliza quitando espacios al comienzo y al final y convirtiéndolo a minúsculas. Solo se aceptan `auto`, `moto` y `camioneta`.

### 6.2. Estadías de cero días

Para una estadía del mismo día, calcular los minutos entre entrada y salida. Validar ambos horarios con formato de 24 horas `HH:MM`.

- De 1 a 120 minutos: cobrar bloques de 30 minutos, redondeando hacia arriba. Por ejemplo, 1–30 minutos equivalen a un bloque y 91–120 a cuatro bloques.
- Desde el minuto 121: cobrar cuatro bloques iniciales de 30 minutos más un bloque de 60 minutos por cada fracción excedente, redondeando hacia arriba. Por ejemplo, 135 minutos equivalen a cuatro bloques iniciales y una hora adicional.
- Una duración de cero minutos no genera importe de estacionamiento.
- El importe de estacionamiento no puede superar el `tope_dia` de la categoría.

### 6.3. Estadías de uno o más días

Para `días > 0`, cobrar el tope diario multiplicado por la cantidad de días completos. No se solicitan horarios. Si se contrata lavado en una estadía prolongada, sumar el precio fijo del lavado al estacionamiento; no se bonifica el estacionamiento.

### 6.4. Beneficio por lavado

- Sin lavado: cobrar el estacionamiento normal.
- Con lavado y estadía de hasta 120 minutos: bonificar todo el estacionamiento y cobrar únicamente el lavado.
- Con lavado y estadía mayor a 120 minutos: bonificar las primeras dos horas y cobrar solo los bloques de hora adicional correspondientes al tiempo excedente, más el lavado. El estacionamiento cobrable sigue sujeto al `tope_dia`.
- Con lavado y estadía de uno o más días: cobrar los días de estacionamiento más el lavado, sin bonificación.

### 6.5. Rechazo de movimientos

En el procesamiento por lote se deben rechazar, como mínimo, movimientos con patente o tipo de vehículo inválidos, horarios faltantes o inválidos, campos requeridos ausentes o valores de tipos incorrectos. En el sistema base, una salida anterior a la entrada también se rechaza; el desafío 4 modifica esta regla cuando se elige.

## 7. Archivos de salida

Los CSV deben incluir encabezados. Como mínimo, los registros de liquidación deben conservar datos suficientes para identificar el vehículo y reconstruir el cálculo: fecha de operación cuando corresponda, identificador, patente normalizada, tipo de vehículo, duración en minutos o días, horas si aplican, estacionamiento base, bonificación, costo de lavado y total cobrado.

- `liquidacion-manual.csv`: transacciones manuales, acumuladas.
- `liquidacion.csv`: movimientos válidos del lote procesado.
- `rechazados.csv`: movimientos descartados y sus motivos.

Los desafíos pueden requerir archivos adicionales, detallados en la sección siguiente.

## 8. Desafíos individuales de Nivel 1

Implementar **al menos uno**. Al elegir un desafío, integrar su comportamiento al programa y conservar los datos necesarios en los CSV.

### 8.1. Búsqueda e historial por patente

Agregar una opción de menú para buscar una patente normalizada en los historiales CSV, incluyendo `liquidacion-manual.csv` y `liquidacion.csv` cuando existan. Informar:

- Cantidad de ingresos registrados.
- Dinero total abonado por esa patente.
- Promedio de minutos por estadía.

Para estadías prolongadas, convertir los días completos a minutos usando 1440 minutos por día. Si no hay registros para la patente, informarlo sin producir un error.

### 8.2. Reporte estadístico y métricas del negocio

Al finalizar el procesamiento del lote, mostrar:

- La categoría que generó mayor recaudación.
- El porcentaje de vehículos que contrataron lavado sobre el total de movimientos válidos.
- El promedio de minutos de estadía por categoría.

Calcular las métricas con los registros válidos del lote. Si no hay registros válidos o falta información para una categoría, mostrarlo claramente y evitar divisiones por cero.

### 8.3. Ordenamiento y ranking en CSV

Generar `liquidacion_ranking.csv` con los registros válidos del lote ordenados de mayor a menor por `total_cobrado`. Para importes iguales, se puede usar la duración como criterio secundario. Se puede implementar un algoritmo de ordenamiento estudiado en la materia o utilizar `sorted()` con una clave personalizada.

### 8.4. Tratamiento de medianoche

Si una estadía del mismo día tiene una hora de salida menor que la de entrada, asumir que cruzó una vez la medianoche y calcular el tiempo transcurrido hasta el día siguiente. Por ejemplo, de `23:00` a `02:30` son 210 minutos.

Este desafío reemplaza la regla base que rechaza salidas anteriores a la entrada. Los horarios deben seguir siendo válidos y el cálculo debe considerar el cruce de las 24:00.

### 8.5. Simulación de promociones

Elegir e implementar **una** de estas alternativas:

- **Opción A — Franja horaria:** aplicar un 15 % de descuento al estacionamiento si el ingreso fue antes de las 08:00 o después de las 16:00. No se descuenta el costo del lavado. En esta opción, la promoción se aplica a estadías con hora de entrada disponible.
- **Opción B — Cliente frecuente:** si la patente tiene al menos un registro previo en los CSV históricos, descontar un 10 % del total de la operación actual.

Mostrar la promoción y el descuento en el desglose y guardar el importe final en el CSV. No acumular ambas promociones.

### 8.6. Exportación filtrada por categoría

Agregar una opción para generar:

- `liquidacion_autos.csv`
- `liquidacion_motos.csv`
- `liquidacion_camionetas.csv`

Cada archivo debe tener su propio encabezado, incluir únicamente registros válidos de su categoría y terminar con una fila de subtotal que muestre la recaudación de esa categoría.

### 8.7. Detección de estadías excesivas

Durante el procesamiento, detectar estadías de más de 10 horas (más de 600 minutos). Mostrar una advertencia y registrar cada caso en `alertas_seguridad.csv`, conservando al menos el identificador, la patente, el tipo de vehículo y la duración.

Las alertas no reemplazan la liquidación ni implican por sí mismas que el movimiento sea inválido.

### 8.8. Paginador de resultados en consola

Después de procesar el lote, permitir consultar las liquidaciones válidas en una tabla de texto, mostrando 5 o 10 registros por página. Al terminar cada página, esperar que el usuario presione `ENTER` para continuar. La última página debe finalizar sin exigir otra entrada.

## 9. Entrega

Entregar el código fuente modular y los archivos de datos utilizados. Indicar qué desafío o desafíos del Nivel 1 se implementaron y demostrar el funcionamiento del sistema base junto con cada desafío elegido.
