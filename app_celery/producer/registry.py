from pydantic import BaseModel


class TaskParams(BaseModel):
    name: str
    queue: str
    options: dict = {}


AllTasks: dict[str, TaskParams] = {  # label: TaskParams
    "ping": TaskParams(
        name="app_celery.consumer.tasks.ping.ping",
        queue="ping"
    ),
}
