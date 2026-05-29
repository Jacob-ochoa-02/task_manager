"""
Task Manager — AWS Lambda Handler
Operaciones: GET /tasks | POST /tasks | PUT /tasks/{id} | DELETE /tasks/{id}
"""

import json
import uuid
import boto3
import os
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key

# ─── DynamoDB ─────────────────────────────────────────────────────────────────
dynamodb  = boto3.resource('dynamodb')
TABLE_NAME = os.environ.get('TABLE_NAME', 'Tasks')
table      = dynamodb.Table(TABLE_NAME)

# ─── CORS headers ─────────────────────────────────────────────────────────────
HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
}


def response(status_code: int, body):
    return {
        'statusCode': status_code,
        'headers': HEADERS,
        'body': json.dumps(body, default=str),
    }


# ─── HANDLERS ─────────────────────────────────────────────────────────────────

def get_tasks(event):
    """Listar todas las tareas (scan simple; en prod usar query con GSI)."""
    result = table.scan()
    items  = result.get('Items', [])
    # Ordenar por fecha de creación descendente
    items.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return response(200, items)


def create_task(event):
    """Crear una nueva tarea."""
    body = json.loads(event.get('body') or '{}')

    title    = (body.get('title') or '').strip()
    priority = body.get('priority', 'medium')

    if not title:
        return response(400, {'error': 'El campo "title" es requerido'})
    if priority not in ('high', 'medium', 'low'):
        priority = 'medium'

    task = {
        'id':        str(uuid.uuid4()),
        'title':     title,
        'priority':  priority,
        'done':      False,
        'createdAt': datetime.now(timezone.utc).isoformat(),
        'updatedAt': datetime.now(timezone.utc).isoformat(),
    }
    table.put_item(Item=task)
    return response(201, task)


def update_task(event, task_id: str):
    """Actualizar título, prioridad o estado de una tarea."""
    body = json.loads(event.get('body') or '{}')

    update_expr   = 'SET updatedAt = :ts'
    expr_values   = {':ts': datetime.now(timezone.utc).isoformat()}
    expr_names    = {}

    if 'title' in body:
        update_expr += ', #t = :title'
        expr_names[':t'] = 'title'          # evitar keyword reservada
        expr_names['#t'] = 'title'
        expr_values[':title'] = body['title'].strip()

    if 'priority' in body and body['priority'] in ('high', 'medium', 'low'):
        update_expr += ', priority = :p'
        expr_values[':p'] = body['priority']

    if 'done' in body:
        update_expr += ', done = :d'
        expr_values[':d'] = bool(body['done'])

    kwargs = {
        'Key':                     {'id': task_id},
        'UpdateExpression':        update_expr,
        'ExpressionAttributeValues': expr_values,
        'ReturnValues':            'ALL_NEW',
    }
    if expr_names:
        kwargs['ExpressionAttributeNames'] = expr_names

    try:
        result = table.update_item(**kwargs)
    except Exception as e:
        return response(404, {'error': 'Tarea no encontrada', 'detail': str(e)})

    return response(200, result.get('Attributes', {}))


def delete_task(task_id: str):
    """Eliminar una tarea por ID."""
    table.delete_item(Key={'id': task_id})
    return response(200, {'message': 'Tarea eliminada', 'id': task_id})


# ─── ROUTER ───────────────────────────────────────────────────────────────────

def lambda_handler(event, context):
    method   = event.get('httpMethod', '')
    path     = event.get('path', '')
    path_params = event.get('pathParameters') or {}
    task_id  = path_params.get('id')

    # Preflight CORS
    if method == 'OPTIONS':
        return response(200, {})

    try:
        if method == 'GET'    and path.endswith('/tasks'):
            return get_tasks(event)

        if method == 'POST'   and path.endswith('/tasks'):
            return create_task(event)

        if method == 'PUT'    and task_id:
            return update_task(event, task_id)

        if method == 'DELETE' and task_id:
            return delete_task(task_id)

        return response(404, {'error': 'Ruta no encontrada'})

    except Exception as e:
        print(f'[ERROR] {e}')
        return response(500, {'error': 'Error interno del servidor'})
