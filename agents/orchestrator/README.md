# Módulo: Cognitive Orchestrator (Orquestador Cognitivo) 🧠

Este módulo constituye el núcleo de procesamiento lógico, razonamiento y toma de decisiones autónomas del ecosistema **Campuslands Inteligente**. Está diseñado sobre una arquitectura de agentes reactivos distribuidos, utilizando **LangGraph** para la gestión de estados y la suite de **LangChain** para la interfaz con modelos de lenguaje masivos (LLM).

---

## 🏗️ Arquitectura del Sistema y Flujo de Datos

El orquestador funciona como un consumidor asíncrono que reacciona en tiempo real a los estímulos del sistema, integrando la telemetría de los modelos de visión con la lógica de negocio de la plataforma académica.

[Módulo de Visión] ➡️ (VisionEvent) ➡️ [EventBus] ➡️ graph.py ➡️ [AgentState] ➡️ Máquina de Estados (LangGraph)

### 🔄 Ciclo de Vida del Estado (`AgentState`)

El procesamiento de cualquier estímulo sigue un flujo controlado por una máquina de estados finitos orientada a grafos cíclicos dirigidos (DAGs), cuyo ciclo operativo es:

1. **`router` (Nodo de Enrutamiento)**: Evalúa el contexto actual de los mensajes o eventos acumulados en el estado a través del LLM (o el componente Mock de contingencia). Determina si la resolución del problema requiere información externa o acciones en el sistema.
2. **Decisión Condicional (`_hay_tools_pendientes`)**: 
   * Si el modelo solicita la invocación de funciones de la plataforma, el flujo se desvía automáticamente hacia el nodo de ejecución.
   * Si no hay acciones pendientes en el canal, se desvía al nodo de respuesta final.
3. **`ejecutar_herramienta` (Nodo de Acción)**: Invoca de manera asíncrona los contratos mapeados en el catálogo de herramientas. Registra una auditoría detallada del éxito/fallo de la operación en el historial del estado (`ToolExecutionRecord`) y regresa secuencialmente al nodo `router` para evaluar si se requieren más acciones.
4. **`responder` (Nodo de Cierre)**: Consolida los resultados obtenidos de los plugins ejecutados, genera la síntesis final de la información para el usuario o administrador, y transiciona el grafo hacia el estado de finalización (`END`).

---

## 🛠️ Especificación de Componentes del Módulo

* **`state.py` (Estructura de Datos Local)**: Define el objeto central `AgentState` que se propaga a lo largo del grafo. Este componente encapsula el historial de mensajes, rastrea el ID de la sesión, el origen del estímulo (`OrigenEntrada`), el aula asociada, y mantiene la lista de auditoría con los registros de ejecución de herramientas ejecutadas durante el ciclo de vida del agente.
* **`tools.py` (Catálogo de Capacidades)**: Expone las interfaces decoradas con `@tool` que permiten al agente interactuar con los servicios del negocio:
  * `registrar_asistencia`: Registro automatizado basado en telemetría visual.
  * `consultar_analitica_estudiante`: Extracción de métricas de rendimiento y alertas de deserción.
  * `evaluar_anomalia`: Detección sostenida de incidentes o ausencias prolongadas en el aula.
  * `optimizar_espacio`: Análisis de aforo y eficiencia de la infraestructura física.
* **`nodes.py` (Unidades de Cómputo)**: Define las funciones de transición del estado. Incluye una capa de contingencia (`MockChatOpenAI`) diseñada para ejecutar el plan de pruebas locales mediante llamadas estructuradas (`Tool Calling`) basadas en reglas semánticas, garantizando la continuidad operativa sin dependencias obligatorias de API Keys.
* **`graph.py` (Orquestador de Eventos)**: Ensambla el flujo mediante la API de `StateGraph`. Contiene el listener asíncrono `start_event_listener`, el cual se suscribe al `EventBus` global, encapsula los estímulos bajo el esquema de `AgentState` e inicializa de manera aislada y concurrentemente el motor de inferencia.

---

## 🔗 Integración del Ecosistema (Visión + Orquestador)

El flujo completo de telemetría reactiva en la plataforma se acopla de la siguiente manera utilizando las capacidades distribuidas del repositorio:

1. **Captura y Extracción (`agents/vision/embedding_engine.py`)**: El módulo de visión procesa los frames de las cámaras del aula y genera los vectores de características (embeddings) correspondientes.
2. **Clasificación y Pipeline (`agents/vision/classifier.py` y `pipeline.py`)**: Clasifica el estado del Camper (atento, distraído, ausente) y publica un `VisionEvent` formal a través del bus de eventos.
3. **Consumo y Orquestación (`agents/orchestrator/graph.py`)**: El listener asíncrono de este módulo intercepta el evento del bus, mapea los datos y arranca la ejecución del grafo para tomar decisiones o alertar de forma autónoma.

---

## 🚀 Guía de Validación Rápida

Para comprobar la integridad del módulo y verificar que no existan regresiones en las importaciones o la sintaxis, ejecute desde la raíz:

python -m py_compile agents/orchestrator/graph.py agents/orchestrator/nodes.py agents/orchestrator/tools.py agents/orchestrator/state.py