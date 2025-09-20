from pydantic import BaseModel


class TaskParams(BaseModel):
    name: str
    queue: str
    options: dict = dict()


AllTasks: dict[str, TaskParams] = {
    "aping": TaskParams(
        name="aping",
        queue="aping"
    ),
}
