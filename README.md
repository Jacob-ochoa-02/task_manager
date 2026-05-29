# Task Manager — AWS Serverless

Aplicación CRUD de tareas construida sobre servicios administrados de AWS.

## Arquitectura

```
GitHub → CodePipeline → S3 (frontend)
Usuario → S3 (HTML/JS) → API Gateway → Lambda → DynamoDB
```

## Servicios utilizados

| Servicio | Rol |
|---|---|
| **S3** | Hosting del frontend estático |
| **CodePipeline + CodeBuild** | CI/CD automático al hacer push a main |
| **API Gateway** | REST API (HTTPS + CORS) |
| **Lambda** | Lógica de negocio (Python 3.12) |
| **DynamoDB** | Persistencia de tareas (on-demand) |

## Endpoints API

| Método | Ruta | Descripción |
|---|---|---|
| GET | /tasks | Listar todas las tareas |
| POST | /tasks | Crear tarea |
| PUT | /tasks/{id} | Actualizar tarea |
| DELETE | /tasks/{id} | Eliminar tarea |

### Payload tarea

```json
{
  "id":        "uuid",
  "title":     "Texto de la tarea",
  "priority":  "high | medium | low",
  "done":      false,
  "createdAt": "2025-01-15T10:30:00Z",
  "updatedAt": "2025-01-15T10:30:00Z"
}
```

## Despliegue

### Prerrequisitos

```bash
pip install aws-sam-cli
aws configure   # configura credenciales
```

### 1. Clonar y construir

```bash
git clone https://github.com/Jacob-ochoa-02/task-manager
cd task-manager
sam build
```

### 2. Deploy inicial

```bash
sam deploy --guided \
  --template infrastructure/template.yaml \  
  --parameter-overrides \
    GitHubOwner=JXXXXX \
    GitHubRepo=tXXXXX \
    GitHubToken=XXXX
```

### 3. Actualizar la URL de la API en el frontend

Edita `frontend/index.html` y reemplaza:

```js
const API_BASE = 'https://YOUR_API_ID.execute-api.us-east-1.amazonaws.com/prod';
```

con la URL del Output `ApiUrl` que arroja el deploy.

### 4. Despliegue continuo

A partir de aquí, cualquier `git push` a `main` dispara CodePipeline automáticamente.

## Estructura del proyecto

```
task-manager/
├── frontend/
│   └── index.html          ← SPA (HTML + JS + CSS)
├── backend/
│   └── src/
│       └── handler.py      ← Lambda handler (Python)
└── infrastructure/
    └── template.yaml       ← CloudFormation / SAM template
```

## Estimación de costos (carga baja)

| Servicio | Costo/mes estimado |
|---|---|
| S3 hosting | ~$0.01 |
| Lambda (1M req/mes) | ~$0.20 |
| API Gateway (1M req) | ~$3.50 |
| DynamoDB on-demand | ~$0.25 |
| CodePipeline | ~$1.00 |
| **Total** | **~$5.00/mes** |

Dentro del Free Tier el primer año el costo real es **$0**.
