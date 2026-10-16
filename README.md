# PriceScope — Data Pipeline

Repositorio responsable de la **recolección, validación, normalización y preparación de datos** para PriceScope, una plataforma B2B de monitoreo de precios e inflación real multimoneda.

El objetivo es construir un pipeline reproducible que obtenga precios desde tiendas online, consulte tipos de cambio y entregue información consistente al backend para calcular indicadores y detectar anomalías.

## 1. Objetivo del proyecto

Construir un pipeline de datos capaz de:

- Recolectar precios desde un conjunto acotado de tiendas online.
- Consultar tipos de cambio desde una API externa.
- Normalizar los registros recolectados.
- Identificar y gestionar observaciones duplicadas o inválidas.
- Mantener las fechas de observación y recolección.
- Preparar datos históricos para el análisis de precios.
- Entregar información persistible y consultable por el backend.
- Generar datos de prueba para validar el flujo completo del MVP.

**Principio del MVP:** priorizar la calidad, trazabilidad y reproducibilidad de los datos antes que ampliar la cantidad de fuentes o productos.

## 2. Alcance

### Incluido

- Recolección desde 2 tiendas online, sujeto a la viabilidad técnica.
- Dataset inicial de aproximadamente 50–200 productos o publicaciones.
- Extracción de nombre, precio, moneda, URL y fecha.
- Consulta periódica de tipos de cambio.
- Normalización de formatos y monedas.
- Validaciones de calidad.
- Detección de duplicados.
- Registro de errores de recolección.
- Persistencia o entrega de datos mediante el contrato acordado con backend.
- Datos sintéticos para pruebas controladas.

### Fuera del alcance inicial

- Recolección de 10.000 productos desde 15 tiendas.
- Scraping distribuido.
- Evasión de CAPTCHA o mecanismos de acceso.
- Matching semántico avanzado entre productos de diferentes tiendas.
- Detección automática y definitiva de shrinkflation.
- Modelos predictivos complejos.
- Infraestructura de streaming con Kafka.
- Orquestación distribuida.

La recolección debe respetar las condiciones de uso, las restricciones de acceso y las políticas aplicables de cada fuente.

## 3. Stack tecnológico propuesto

Las tecnologías son una propuesta inicial que debe confirmarse con el equipo.

| Componente | Tecnología propuesta |
|---|---|
| Lenguaje | Python |
| Scraping | Playwright o Scrapy |
| Solicitudes HTTP | Requests o HTTPX |
| Procesamiento | Pandas |
| Validación | Pydantic |
| Tipos de cambio | API externa configurable |
| Persistencia | PostgreSQL mediante el contrato del backend |
| Pruebas | Pytest |
| Configuración | Variables de entorno |
| Ejecución periódica | Cron o scheduler simple |

No es necesario utilizar Playwright y Scrapy simultáneamente. Seleccionar la herramienta según el comportamiento de las tiendas y la complejidad real de la extracción.

## 4. Arquitectura propuesta

```text
data/
├── src/
│   ├── config/
│   │   └── settings.py
│   ├── collectors/
│   │   ├── base.py
│   │   ├── store_a.py
│   │   └── store_b.py
│   ├── exchange_rates/
│   │   └── client.py
│   ├── normalization/
│   │   ├── prices.py
│   │   └── products.py
│   ├── validation/
│   │   └── price_observation.py
│   ├── pipelines/
│   │   └── collect_prices.py
│   ├── persistence/
│   │   └── repository.py
│   └── main.py
├── tests/
│   ├── test_normalization.py
│   ├── test_validation.py
│   ├── test_collectors.py
│   └── test_exchange_rates.py
├── samples/
├── .env.example
├── requirements.txt
└── README.md
```

La estructura es orientativa. Los nombres definitivos de los módulos y la responsabilidad de la persistencia deben coordinarse con el backend.

### Responsabilidades

- **Collectors:** extraer información de cada tienda.
- **Exchange rates:** consultar y validar tipos de cambio.
- **Normalization:** convertir los datos a formatos consistentes.
- **Validation:** comprobar que cada registro cumple el contrato.
- **Pipelines:** coordinar la ejecución de la recolección.
- **Persistence:** guardar o entregar los registros al mecanismo acordado.
- **Tests:** validar el comportamiento con datos reales controlados y fixtures.

## 5. Contrato de datos

Todos los collectors deben entregar registros con una estructura común, independientemente de la tienda de origen.

### Observación de precio

```json
{
  "source": "store_a",
  "external_id": "SKU-123",
  "source_url": "https://example.com/product/123",
  "product_name": "Producto de ejemplo",
  "brand": "Marca de ejemplo",
  "category": "Electrónica",
  "price": 12990,
  "currency_code": "CLP",
  "is_promotion": false,
  "observed_at": "2026-10-16T08:00:00Z",
  "fetched_at": "2026-10-16T08:00:05Z"
}
```

Este ejemplo es ilustrativo. Debe ajustarse al esquema acordado con el backend antes de comenzar la integración.

### Reglas importantes

- `price` debe ser numérico y mayor que cero.
- `currency_code` debe utilizar códigos normalizados, por ejemplo `CLP`, `USD` o `EUR`.
- `source` debe identificar de manera consistente la tienda o fuente.
- `external_id` puede ser nulo si la tienda no expone un identificador confiable.
- `source_url` debe identificar la publicación observada.
- `observed_at` representa el momento al que corresponde el precio.
- `fetched_at` representa el momento en que el sistema obtuvo el registro.
- Las fechas deben utilizar una convención consistente, preferentemente UTC.
- No se deben reemplazar los precios originales por valores convertidos a otra moneda.
- Los registros inválidos deben rechazarse o marcarse explícitamente; nunca corregirse silenciosamente mediante valores inventados.

## 6. Recolección de precios

Cada tienda debe implementar un collector que cumpla el contrato común.

### Flujo recomendado

1. Obtener las URL o identificadores de los productos a monitorear.
2. Consultar la página o fuente de datos autorizada.
3. Extraer el nombre, precio, moneda y datos disponibles.
4. Registrar la fecha de observación y de recolección.
5. Normalizar los campos.
6. Validar el registro.
7. Identificar duplicados según las reglas definidas.
8. Guardar o entregar las observaciones.
9. Registrar métricas y errores de ejecución.

### Estrategia para el MVP

- Comenzar con una tienda y un grupo pequeño de productos.
- Verificar la extracción manualmente contra la página de origen.
- Agregar la segunda tienda después de validar el primer collector.
- Mantener una lista controlada de productos para hacer reproducibles las pruebas.
- Implementar reintentos limitados para fallos transitorios.
- Evitar consultas excesivas y respetar las restricciones de acceso de las fuentes.

Los collectors deben estar separados por tienda para que un cambio en una página no afecte al resto del pipeline.

## 7. Integración con tipos de cambio

El pipeline consultará una API de tipos de cambio configurable.

### Datos mínimos

| Campo | Descripción |
|---|---|
| `base_currency` | Moneda base |
| `quote_currency` | Moneda cotizada |
| `rate` | Tipo de cambio |
| `observed_at` | Fecha a la que corresponde la tasa |
| `fetched_at` | Fecha en que se consultó la fuente |
| `source` | Proveedor del dato |

### Reglas

- Documentar la convención utilizada para cada tasa.
- Validar que el valor sea positivo y numérico.
- Registrar la fuente y las fechas.
- Evitar crear registros nuevos si la API devuelve datos inválidos.
- Controlar límites de consumo y errores del proveedor.
- Conservar las tasas históricas disponibles.

La frecuencia de consulta —por ejemplo, horaria— debe depender de las capacidades de la API y de la frecuencia real de actualización de los datos.

**Importante:** consultar una API cada hora no significa que el tipo de cambio publicado cambie cada hora. Se debe conservar la fecha efectiva de la tasa proporcionada por la fuente.

## 8. Normalización de precios y productos

La normalización busca que los datos de distintas tiendas puedan compararse sin perder la información original.

### Precios

- Convertir precios a un tipo numérico consistente.
- Interpretar correctamente separadores decimales y de miles.
- Eliminar símbolos monetarios del valor numérico.
- Conservar el código de moneda por separado.
- Rechazar precios negativos, nulos o no interpretables.
- Mantener el precio observado y la información de promociones.

### Productos

- Limpiar espacios y caracteres innecesarios en los nombres.
- Normalizar campos de marca y categoría cuando sea posible.
- Conservar el nombre original publicado por la tienda.
- Mantener un identificador por publicación.
- No asumir que dos nombres similares representan el mismo producto.

Para el MVP, se recomienda utilizar identificadores confiables, como SKU, código de barras o una relación revisada manualmente, cuando estén disponibles. El matching avanzado entre productos queda fuera del alcance inicial.

## 9. Calidad de datos

Cada ejecución debe validar los registros antes de entregarlos al backend.

### Controles mínimos

- Precio presente, numérico y positivo.
- Moneda reconocida.
- Fuente identificable.
- URL válida cuando esté disponible.
- Fechas válidas y consistentes.
- Ausencia de duplicados según la clave acordada.
- Cambios de precio extremos marcados para revisión, no eliminados automáticamente.
- Registro de campos faltantes.
- Registro de errores por tienda.

Un aumento brusco no necesariamente es un error: puede ser una promoción terminada o una variación real. Por eso, las validaciones deben distinguir entre errores estructurales y valores inusuales que requieren análisis.

### Métricas sugeridas

- Número de productos consultados.
- Número de observaciones válidas.
- Número de observaciones rechazadas.
- Porcentaje de éxito por tienda.
- Cantidad de duplicados detectados.
- Tiempo total de ejecución.
- Fecha de la última recolección exitosa.

Estas métricas permiten detectar problemas en la fuente antes de que afecten a los indicadores y al detector de anomalías.

## 10. Persistencia e integración con backend

Antes de implementar la persistencia, el equipo debe elegir y documentar un único mecanismo de integración.

**Opción A: escritura directa en PostgreSQL.** El pipeline utiliza un repositorio de datos y respeta el esquema y las migraciones acordados con backend.

**Opción B: importación mediante API.** El pipeline envía observaciones validadas a un endpoint de ingesta definido por backend.

Para el MVP, elegir la opción más simple que permita completar el flujo y probarlo de forma reproducible. No implementar ambas opciones sin una necesidad concreta.

### Reglas de integración

- Compartir el esquema de observación de precios.
- Acordar los campos obligatorios y opcionales.
- Definir cómo se gestionan duplicados y reintentos.
- Mantener la trazabilidad de la fuente.
- Evitar que el pipeline y el backend mantengan esquemas incompatibles.
- Probar la integración con datos de ejemplo antes de utilizar la recolección completa.

## 11. Configuración

Crear un archivo `.env` local a partir de `.env.example`.

Ejemplo orientativo:

```dotenv
APP_ENV=development
LOG_LEVEL=INFO

EXCHANGE_RATE_API_URL=
EXCHANGE_RATE_API_KEY=

DATABASE_URL=postgresql+psycopg://pricescope:pricescope@localhost:5432/pricescope

COLLECTION_TIMEOUT_SECONDS=30
COLLECTION_MAX_RETRIES=3
```

Las variables deben ajustarse a las implementaciones reales. Si se utiliza integración por API en lugar de escritura directa a PostgreSQL, la configuración deberá incluir la URL correspondiente del backend.

**Seguridad:** nunca subir claves, contraseñas o tokens reales al repositorio. Mantener `.env` fuera del control de versiones.

## 12. Instalación y ejecución local

Los siguientes comandos son una guía y pueden requerir ajustes según los archivos reales del proyecto.

### Requisitos

- Python 3.11 o la versión acordada por el equipo.
- Git.
- Acceso a las fuentes de datos seleccionadas.
- PostgreSQL, si se utiliza persistencia directa.

### Instalar dependencias

```bash
git clone <URL_DEL_REPOSITORIO_DATA>
cd <CARPETA_DEL_REPOSITORIO>

python -m venv .venv
```

Activar el entorno virtual.

**Windows PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux / macOS**

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Si se utiliza Playwright, instalar también el navegador requerido por la configuración elegida:

```bash
playwright install chromium
```

Configurar las variables de entorno y ejecutar el pipeline según el punto de entrada definido en el proyecto.

Ejemplo propuesto:

```bash
python -m src.main
```

El comando definitivo debe coincidir con la estructura y el punto de entrada implementados.

## 13. Pruebas

Las pruebas deben permitir validar el pipeline sin depender continuamente de las páginas web ni de una API externa.

### Pruebas unitarias

- Normalización de precios.
- Interpretación de monedas.
- Validación de observaciones.
- Manejo de fechas.
- Detección de duplicados.
- Normalización de nombres.

### Pruebas de integración

- Collector con respuestas controladas.
- Cliente de tipos de cambio con respuestas válidas e inválidas.
- Persistencia o envío al backend.
- Manejo de errores y reintentos.

### Datos de prueba

Utilizar fixtures y respuestas guardadas para simular:

- Precios normales.
- Promociones.
- Cambios bruscos.
- Productos sin precio.
- Monedas desconocidas.
- Respuestas incompletas.
- Errores HTTP y timeouts.

Comando propuesto:

```bash
pytest
```

Las pruebas automatizadas no deben depender del estado cambiante de una tienda real.

## 14. Plan de trabajo de tres semanas

### Semana 1 — Recolección inicial

- Confirmar el contrato de datos con backend.
- Seleccionar las dos fuentes del MVP.
- Implementar el primer collector.
- Definir el modelo de observación.
- Crear fixtures y pruebas de normalización.
- Guardar o entregar las primeras observaciones.

**Resultado esperado:** registros reales, validados y consultables por el mecanismo acordado.

### Semana 2 — Integración y calidad

- Implementar el segundo collector.
- Integrar la API de tipos de cambio.
- Mejorar validaciones y deduplicación.
- Registrar errores y métricas de ejecución.
- Completar la integración con PostgreSQL o con la API de ingesta.
- Entregar un historial suficiente para probar indicadores.

**Resultado esperado:** pipeline integrado con datos de varias fuentes y tipos de cambio.

### Semana 3 — Estabilización

- Ejecutar pruebas de extremo a extremo.
- Corregir errores de extracción y normalización.
- Verificar consistencia de fechas y monedas.
- Preparar un dataset reproducible para la demo.
- Documentar limitaciones y fuentes.
- Comprobar que el pipeline se puede ejecutar desde un entorno limpio.

**Resultado esperado:** flujo reproducible desde la recolección hasta los datos consumidos por el backend.

## 15. Criterios de aceptación

- [ ] Existe al menos un collector funcional y validado.
- [ ] La segunda fuente se integra si es técnicamente viable.
- [ ] Las observaciones cumplen el contrato acordado con backend.
- [ ] Los precios conservan moneda, fuente y fechas.
- [ ] Los tipos de cambio se almacenan con su convención documentada.
- [ ] Los datos inválidos se identifican y registran.
- [ ] La estrategia de duplicados está definida.
- [ ] Existen pruebas automatizadas de normalización y validación.
- [ ] La integración con backend está probada.
- [ ] La ejecución es reproducible y está documentada.
- [ ] Hay suficientes datos para demostrar indicadores y anomalías.
- [ ] Las limitaciones de cobertura e historial están documentadas.

## 16. Riesgos y decisiones pendientes

Antes de ampliar el pipeline, confirmar:

1. Qué tiendas se utilizarán y qué métodos de acceso permiten.
2. Qué campos entrega cada fuente.
3. Cuál será la clave para identificar una publicación.
4. Cómo se distinguirán productos equivalentes de publicaciones diferentes.
5. Qué proveedor de tipos de cambio se utilizará.
6. Qué frecuencia de recolección es realista.
7. Quién será responsable de las migraciones y la persistencia.
8. Cómo se ejecutarán los trabajos periódicos.
9. Qué volumen histórico estará disponible para evaluar el detector.
10. Qué información de promociones es fiable y cuál requiere revisión manual.

El objetivo del repositorio no es producir la mayor cantidad de datos posible, sino entregar un conjunto pequeño, consistente, trazable y suficientemente confiable para demostrar el valor de PriceScope.