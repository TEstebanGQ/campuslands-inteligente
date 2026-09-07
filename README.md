# 🧠 Campuslands Inteligente — Multi-Agent System & Computer Vision

<div align="center">

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agents-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C.svg?logo=pytorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Plataforma inteligente y ecosistema distribuido para análisis de aulas, telemetría de atención y toma de decisiones autónomas mediante IA.**

</div>

---

## 📌 Visión General

**Campuslands Inteligente** es un sistema integral de IA que combina visión computacional, arquitecturas multi-agente basadas en grafos de estado (**LangGraph**) y microservicios asíncronos (**FastAPI**). Permite monitorear aulas en tiempo real, procesar telemetría visual, inferir estados de atención/ausencia de estudiantes y orquestar intervenciones académicas y operativas automáticas a través de un bus de eventos y un sistema de plugins extensibles.

---

## 🏗️ Arquitectura del Sistema

- **API REST & Chat (FastAPI):** Endpoints asíncronos para telemetría, chat interactivo y administración.
- **Vision Agent (PyTorch / ResNet):** Motor de embeddings visuales, clasificador de estados y seguimiento de centroides.
- **Orchestrator Agent (LangGraph):** Grafo de estados con memoria persistente, matriz de decisiones e invocación de herramientas LLM.
- **Core Event Bus:** Manejador de persistencia SQLite y orquestador FiftyOne.
- **Plugins Extensibles:** Registro de asistencia, notificador de anomalías, optimizador de espacios y analíticas de estudiantes.

---

## 🚀 Componentes Principales

1. **Orquestador Cognitivo (`agents/orchestrator`):**
   * Diseñado con **LangGraph** para manejar máquinas de estado cíclicas con persistencia de memoria.
   * Coordina la invocación de herramientas, análisis de anomalías e interacción conversacional contextual con administradores.
2. **Motor de Visión Computacional (`agents/vision`):**
   * Extracción de embeddings visuales mediante modelos profundos en **PyTorch**.
   * Clasificación de estados de aula (Atento, Distraído, Ausente) y seguimiento de centroides.
3. **API Asíncrona & Webhooks (`api`):**
   * Endpoints en **FastAPI** con validación estricta mediante **Pydantic v2**.
   * Rutas de administración y canales de chat interactivo en tiempo real.
4. **Sistema de Plugins Desacoplado (`plugins`):**
   * `attendance_ledger.py`: Registro y libro contable de asistencia.
   * `anomaly_notifier.py`: Alertas tempranas ante deserción o patrones anómalos.
   * `space_optimizer.py`: Métricas de ocupación y optimización de espacios físicos.
   * `student_analytics.py`: Análisis longitudinal del rendimiento y participación.

---

## 🛠️ Instalación y Uso

### 1. Clonar el repositorio
```bash
git clone https://github.com/TEstebanGQ/campuslands-inteligente.git
cd campuslands-inteligente
```

### 2. Crear y activar entorno virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
```

### 5. Iniciar la API
```bash
uvicorn api.main:app --reload --port 8000
```

### 6. Ejecutar tests automatizados
```bash
pytest tests/ -v
```

---

## 👨‍💻 Autor

**Tomas Esteban Gonzalez Quintero** — *Desarrollador Full Stack*

- 🌐 [Portafolio Web](https://portafolio-tegq.netlify.app/)
- 🐙 [GitHub: @TEstebanGQ](https://github.com/TEstebanGQ)
- 💼 [LinkedIn](https://www.linkedin.com/in/tomas-esteban-gonzalez-quintero/)
- 📧 [Email](mailto:tomasestebangonzalezquintero@gmail.com)

---

<div align="center">
  <br/>
  <a href="https://github.com/TEstebanGQ">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/TEstebanGQ/TEstebanGQ/main/assets/logo_white.png">
      <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/TEstebanGQ/TEstebanGQ/main/assets/logo_clean.png">
      <img src="https://raw.githubusercontent.com/TEstebanGQ/TEstebanGQ/main/assets/logo_white.png" width="100" alt="TEGQ Brand Logo" />
    </picture>
  </a>
  <br/>
  <sub><b>© Tomas Esteban González Quintero — TEGQ</b></sub>
</div>
