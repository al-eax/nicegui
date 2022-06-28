from typing import List

from ..task_logger import create_task
from .element import Element


def update(self, *elements: List[Element]) -> None:
    for element in elements:
        create_task(element.view.update())
