# API de producción y monitoreo

API FastAPI asíncrona para un grafo multi-agente. Los jobs y los checkpoints de LangGraph se persisten en Redis. Las tareas con `critical: true` se interrumpen hasta una aprobación externa. Si se configura `LANGSMITH_API_KEY`, cada nodo queda trazado en LangSmith.

## Ejecutar

Requiere Python 3.12+ y Docker. El Compose usa Redis Stack porque `RedisSaver`
necesita RedisJSON y RediSearch.

```powershell
docker compose up -d
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:REDIS_URL="redis://localhost:6379/0"
uvicorn app.main:app --reload
```

Para trazas y métricas de costo/latencia, exportá `LANGSMITH_API_KEY` antes de iniciar Uvicorn. El proyecto aparecerá como `api-produccion-monitoreo` en LangSmith. Guardá las capturas de trazas, costo por ejecución y p95 de la prueba en `screenshots/`.

## API

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/tasks -ContentType application/json -Body '{"task":"Preparar reporte","critical":false}'
Invoke-RestMethod http://127.0.0.1:8000/tasks/<job_id>
```

Para una tarea crítica, consultá el estado hasta `WAITING_APPROVAL` y aprobala:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:8000/tasks/<job_id>/approve -ContentType application/json -Body '{"approved":true}'
```

## Prueba concurrente (5 tareas)

Con la API activa:

```powershell
1..5 | ForEach-Object -Parallel {
  Invoke-RestMethod -Method Post http://127.0.0.1:8000/tasks -ContentType application/json -Body "{\"task\":\"Tarea $_\",\"critical\":false}"
}
```

En LangSmith, filtrá esas cinco trazas por el proyecto y capturá el costo por ejecución y la latencia p95.
