
from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum, auto
from prompt_toolkit import PromptSession
from sqlmodel import SQLModel

from todolist.db import User, Worklist, Task, get_users, get_worklists, get_tasks, create_worklist, create_task, get_entity, update_entity
from .console import console
from .helper import get_item, show_table_and_ask_for_command, Command

class Step(Enum):
    select_user = auto()
    select_worklist = auto()
    select_task = auto()


@dataclass
class AppState():
    app_step:Step = Step.select_user
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
        self.refresh_tasklist_list()

def execute_command(session:PromptSession, state:AppState, state_key:str, model:SQLModel):
    
    response = show_table_and_ask_for_command(session, state, state_key, model)
    if len(response.split(' ')) < 2:
        # user wants to quit
        if response == Command.quit:
            return False # return false to make the program exit
        # user just entered a bad command
        # warn them and then loop again
        console.print("[danger]You must type in a command and a value: Eg. 'select 1'")
        return True

    command, value = response.split(' ', 1)
    command = command.lower()
    if command == Command.select:
        if model == User:
            state.set_active_user(value)
            state.app_step = Step.select_worklist
        elif model == Worklist:
            state.set_active_worklist(value)
            state.app_step = Step.select_task
    elif command == Command.remove:
        if model == User:
            console.print("[warning]Not supported currently")
        elif model == Worklist:
            console.print("[warning]Not supported currently")
        else:
            console.print("[warning]Not supported currently")
    elif command == Command.complete:
        if model == Task:
            task:Task = get_entity(Task, int(value))
            task.completed = not task.completed
            update_entity(task)
            state.refresh_tasklist_list()
        else:
            console.print("[danger]Not supported")
    elif command == Command.add:
        if model == Task:
            create_task(task=value, worklist_id=state.active_worklist.id)
            state.refresh_tasklist_list()
        elif model == Worklist:
            create_worklist(name=value, user_id=state.active_user.id)
            state.refresh_worklist_list()
        else:
            console.print("[danger]Not supported")
    elif command == Command.reset:
        if value == "worklist":
            state.app_step = Step.select_worklist
        elif value == "user":
            state.app_step = Step.select_user
    else:
        console.print("[danger]Unknown command")

    return True

def cli():

    state = AppState()
    session = PromptSession()

    console.print("You can exit the program by pressing [success]CTRL+D[/success] at anytime")
    console.print("You must type in a command and a value: Eg. 'select 1', 'complete 1'")
    console.print()
    loop = True
    while loop:
        try:
            if state.app_step == Step.select_user:
                loop = execute_command(session, state, 'all_user_list', model=User)
            elif state.app_step == Step.select_worklist:
                loop = execute_command(session, state, 'all_worklist_list', model=Worklist)
            elif state.app_step == Step.select_task:
                loop = execute_command(session, state, 'all_tasklist_list', model=Task)
        except KeyboardInterrupt:
            continue
        except EOFError:
            break
        except Exception:
            console.print_exception()
            
    print('GoodBye!')


if __name__ == '__main__':
    cli()