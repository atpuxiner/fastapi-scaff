from pydantic import BaseModel


class TaskParams(BaseModel):
    name: str
    queue: str
    options: dict = {}


AllTasks: dict[str, TaskParams] = {  # label: TaskParams
    "health": TaskParams(
        name="celery_app.consumer.tasks.health.health",
        queue="health",
    ),
}
