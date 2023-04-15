
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum, auto
from prompt_toolkit import prompt
from prompt_toolkit import PromptSession
from sqlmodel import SQLModel
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

from todolist.db import User, Worklist, Task, get_users, get_worklists, get_tasks 


custom_theme = Theme({
    "info": "bold cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green"
})
console = Console(theme=custom_theme)

def bp(question: str, suffix:str = ' > '):
    return f"{question}{suffix}"

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

def get_item(id, item_list, key="id"):
    for item in item_list:
        if int(id) == getattr(item, key):
            return item
    return None


class AppStep(Enum):
    SELECT_USER = auto()
    SELECT_WORKLIST = auto()
    SELECT_TASKLIST = auto()

@dataclass
class AppState():
    app_step:AppStep = AppStep.SELECT_USER
    all_user_list: List[User] = field(default_factory=list)
    all_worklist_list: List[Worklist] = field(default_factory=list)
    all_tasklist_list: List[Task] = field(default_factory=list)
    active_user: Optional[User] = None
    active_worklist: Optional[Worklist] = None

    def __init__(self):
        self.refresh_users()

    def refresh_users(self):
        self.all_user_list = get_users()

    def refresh_worklist_list(self):
        self.all_worklist_list = get_worklists(self.active_user.id)

    def refresh_tasklist_list(self):
        self.all_tasklist_list = get_tasks(self.active_worklist.id)

    def set_active_user(self, id:int):
        self.active_user = get_item(id, self.all_user_list)
        self.refresh_worklist_list()

    def set_active_worklist(self, id:int):
        self.active_worklist = get_item(id, self.all_worklist_list)
        self.refresh_task_list()

def select_user(session:PromptSession, state:AppState):
    console.print(create_table_from_schema(User, state.all_user_list))
    response = session.prompt(bp("Choose an action and user, e.g. 'select 1'"))
    action, value = response.split(" ")
    if action.lower() == 'select':
        state.set_active_user(value)
        state.app_step = AppStep.SELECT_WORKLIST
    else:
        console.print("[danger]Not supported!")

def select_worklist(session:PromptSession, state:AppState):
    console.print(create_table_from_schema(Worklist, state.all_worklist_list))
    response = session.prompt(bp("Choose an action and a worklist, e.g. 'select 1' or 'add priority' or 'delete 1'"))
    action, value = response.split(" ")
    if action.lower() == 'select':
        state.set_active_worklist(value)
        state.app_step = AppStep.SELECT_WORKLIST
    else:
        console.print("[danger]Not supported!")

def select_task(session:PromptSession, state:AppState):
    console.print(create_table_from_schema(Task, state.all_tasklist_list))
    worklist_id = session.prompt(bp("Choose a task to mark as done"))
    state.set_active_worklist(worklist_id)

def cli():

    state = AppState()
    session = PromptSession()

    console.print("You can exit the program by pressing [success]CTRL+D[/success] at anytime")
    console.print("Select a choice by the [info]number[/info] presented in the prior table")
    console.print()
    
    while True:
        try:
            if state.app_step == AppStep.SELECT_USER:
                select_user(session, state)
            elif state.app_step == AppStep.SELECT_WORKLIST:
                select_worklist(session, state)
            elif state.app_step == AppStep.SELECT_TASKLIST:
                select_task(session, state)


        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception:
            console.print("\n[danger]Error! Read instructions carefully[/danger]\n")
            
    print('GoodBye!')


if __name__ == '__main__':
    cli()