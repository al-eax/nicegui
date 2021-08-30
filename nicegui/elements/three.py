from __future__ import annotations
import asyncio
from typing import Callable
import uuid
from justpy.htmlcomponents import WebPage
from .element import Element
from .custom_view import CustomView

class ThreeView(CustomView):

    objects: list[Object3D] = []

    def __init__(self, *, width: int, height: int, on_click: Callable):
        dependencies = ['three.min.js', 'OrbitControls.js']
        super().__init__('three', __file__, dependencies, width=width, height=height)
        self.on_click = on_click
        self.allowed_events = ['onConnect', 'onClick']
        self.initialize(temp=False, onConnect=self.handle_connect, onClick=self.handle_click)

    def run_command(self, command: str, socket=None):
        sockets = [socket] if socket is not None else WebPage.sockets.get(Element.wp.page_id, {}).values()
        for socket in sockets:
            asyncio.get_event_loop().create_task(self.run_method(command, socket))

    def handle_connect(self, msg):
        for object in self.objects:
            self.run_command(object._create_command, msg.websocket)
            self.run_command(object._material_command, msg.websocket)
            self.run_command(object._move_command, msg.websocket)

    def handle_click(self, msg):
        if self.on_click is not None:
            return self.on_click(msg)
        return False


class Three(Element):

    view: ThreeView = None

    def __init__(self, width: int = 400, height: int = 300, on_click: Callable = None):
        super().__init__(ThreeView(width=width, height=height, on_click=on_click))

    def __enter__(self):
        Three.view = self.view
        return self

    def __exit__(self, *_):
        Three.view = None

class Object3D:

    group_stack: list[Object3D] = []

    def __init__(self, type: str, *args):
        self.view = Three.view
        self.type = type
        self.id = 'scene' if type == 'scene' else str(uuid.uuid4())
        self.args = args
        self.color = '#ffffff'
        self.opacity = 1.0
        self.x = 0
        self.y = 0
        self.z = 0
        self.parent = Object3D.group_stack[-1] if Object3D.group_stack else None
        self.view.run_command(self._create_command)
        self.view.objects.append(self)

    def __enter__(self):
        Object3D.group_stack.append(self)
        return self

    def __exit__(self, *_):
        Object3D.group_stack.pop()

    @property
    def _create_command(self):
        parent_id = f'"{self.parent.id}"' if self.parent else 'null'
        return f'create("{self.type}", "{self.id}", {parent_id}, {str(self.args)[1:-1]})'

    @property
    def _material_command(self):
        return f'material("{self.id}", "{self.color}", "{self.opacity}")'

    @property
    def _move_command(self):
        return f'move("{self.id}", {self.x}, {self.y}, {self.z})'

    def material(self, color: str = '#ffffff', opacity: float = 1.0):
        self.color = color
        self.opacity = opacity
        self.view.run_command(self._material_command)
        return self

    def move(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Object3D:
        self.x = x
        self.y = y
        self.z = z
        self.view.run_command(self._move_command)
        return self

class Scene(Object3D):

    def __init__(self):
        super().__init__('scene')

class Group(Object3D):

    def __init__(self):
        super().__init__('group')

class Box(Object3D):

    def __init__(self,
                 width: float = 1.0,
                 height: float = 1.0,
                 depth: float = 1.0,
                 ):
        super().__init__('box', width, height, depth)

class Sphere(Object3D):

    def __init__(self,
                 radius: float = 1.0,
                 width_segments: int = 32,
                 height_segments: int = 16,
                 ):
        super().__init__('sphere', radius, width_segments, height_segments)

class Cylinder(Object3D):

    def __init__(self,
                 top_radius: float = 1.0,
                 bottom_radius: float = 1.0,
                 height: float = 1.0,
                 radial_segments: int = 8,
                 height_segments: int = 1,
                 ):
        super().__init__('cylinder', top_radius, bottom_radius, height, radial_segments, height_segments)
