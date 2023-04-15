from enum import Enum
from prompt_toolkit.completion import NestedCompleter
from sqlmodel import SQLModel
from typing import List
from rich.table import Table

from .console import console

class EntityNotFound(Exception):
    def __init__(self, id, model:SQLModel):
        message = f"id={id} not found in {model.schema()['title']} table"        
        super().__init__(message)
        self.id = id
        self.model = model
        self.message = message
    def __str__(self):
        return f"[danger]EntityNotFound[/danger]: {self.message}"

class Command(str, Enum):
    select = 'select'
    remove = 'remove'
    complete = 'complete'
    add = 'add'
    reset = "reset"
    quit = 'quit'

def generate_completer(items):
    ids = get_ids(items)
    ids = dict(zip(ids, [None]*len(ids)))
    completer = NestedCompleter.from_nested_dict({
        'select': ids,
        'remove': ids,
        'complete': ids,
        'add': None,
        'reset': dict(user=None, worklist=None),
        'quit': None
        })
    return completer

def get_item(id, item_list, key="id", model:SQLModel=SQLModel):
    for item in item_list:
        if int(id) == getattr(item, key):
            return item
    raise EntityNotFound(id, model)


def bp(question: str, suffix:str = ' > '):
    return f"{question}{suffix}"

def get_ids(item_list, to_str=True):
    return [str(item.id) if to_str else item.id for item in item_list]

def create_table_from_schema(item_class:SQLModel, items:List, title:str=None):
    # get the schema for this model
    schema = item_class.schema()
    title = title if title else schema['title']
    fields = schema['properties']
    field_ids = list(fields.keys())
    # create the table
    table = Table(title=title)
    # create the table header
    for _, props in fields.items():
        no_wrap = False if props['type'] == 'string' else True
        table.add_column(props["title"], justify="left", style="cyan", no_wrap=no_wrap)
    # create the table rows
    for item in items:
        field_values = [str(getattr(item, field_id)) for field_id in field_ids]
        table.add_row(*field_values)
    # return our table
    return table

def show_table_and_ask_for_command(session, state, state_key, model):
    items = getattr(state, state_key)
    console.print(create_table_from_schema(model, items))
    
    completer = generate_completer(items)
    response = session.prompt(bp("Choose an action"), completer=completer)
    console.print()


    return response