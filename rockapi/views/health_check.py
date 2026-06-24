from django.http import JsonResponse
import requests
import os

def health_check(request):
    return JsonResponse({
        "status": "ok",
        "task": get_task_id()
    })

def get_task_id():
    try:
        # ECS provides task metadata at this endpoint
        resp = requests.get(
            "http://169.254.170.2/v2/metadata",
            timeout=0.2
        )
        metadata = resp.json()
        
        # Extract just the task ID from the full ARN
        # ARN format: arn:aws:ecs:region:account:task/cluster-name/task-id
        task_arn = metadata.get('TaskARN', '')
        task_id = task_arn.split('/')[-1] if task_arn else 'unknown'
        
        return task_id
    except Exception as e:
        return "unknown"