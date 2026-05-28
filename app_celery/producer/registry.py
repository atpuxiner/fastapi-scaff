from pydantic import BaseModel


class TaskParams(BaseModel):
    name: str
    queue: str
    options: dict = {}


AllTasks: dict[str, TaskParams] = {  # label: TaskParams
    "health": TaskParams(
        name="app_celery.consumer.tasks.health.health",
        queue="health",
    ),
}
