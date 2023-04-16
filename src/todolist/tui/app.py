from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal, Container
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Header,
    Footer,
    Static,
    Switch,
    Label,
    ListItem,
    ListView,
    Input,
)
from todolist.db import (
    Task,
    Worklist,
    create_task,
    create_worklist,
    get_users,
    get_worklists,
    get_tasks,
    update_entity,
    delete_entity
)
from .widgets.select import Select
from typing import List

class TaskItem(Static):
    """A Task Item Widget. Holds a task text, date, completed, and remove button"""

    def __init__(self, task: Task) -> None:
        super().__init__()
        self.my_task: Task = task

    def compose(self) -> ComposeResult:
        """Create child widgets of a stopwatch."""
        yield Label(self.my_task.task, classes="task-words")
        yield Label(self.my_task.date_created, classes="task-date")
        yield Switch(classes="task-checkbox", value=self.my_task.completed, name=self.my_task.id)
        yield Button.error("Remove", name=self.my_task.id)

    def on_switch_changed(self, message):
        self.my_task.completed = message.value
        self.my_task = update_entity(self.my_task)

    def on_button_pressed(self, message:Button.Pressed):
        old_tasks:List = self.parent.tasks # get the tasks from the parent
        old_tasks.remove(self.my_task) # remove the old task
        self.parent.tasks = old_tasks # this causes an update on the parent
        delete_entity(self.my_task) # delete from database

class TaskItems(Vertical):
    tasks: List[Task] = reactive([], always_update=True)
    async def watch_tasks(self):
        try:
            await self.query("TaskItem").remove()
        except:
            pass
        for task in self.tasks:
            self.mount(TaskItem(task))

class Worklists(ListView):
    """This holds the names of the worklists on the left sidebar"""
    worklists = reactive([], always_update=True)
    async def watch_worklists(self):
        return await self.reload_list(self.worklists)
    
    async def reload_list(self, worklists: List[Worklist]):
        cache_index = self.index
        await self.query(".worklist-item-container").remove()
        for worklist in worklists:
            self.mount(
                ListItem(
                    Horizontal(
                    Label(worklist.name, name=worklist.id, classes="worklist-item"),
                    Button.error("X", classes="worklist-item-button", name=worklist)), 
                classes="worklist-item-container", name=worklist.id)
            )
        self.refresh(layout=True)
        self.index = cache_index if cache_index is not None else 0
    
    def on_button_pressed(self, message:Button.Pressed):
        """Called when the delete button is pressed on a worklist"""
        worklist = message.button.name
        self.worklists.remove(worklist) # remove the old task
        self.worklists = self.worklists # this causes an update on the parent
        if len(self.worklists) == 0:
            tasklist_widget: TaskItems = self.parent.parent.parent.parent.parent.query_one("#task-items")
            tasklist_widget.tasks =  [] # change to zero
        delete_entity(worklist) # delete from database
        self.refresh(layout=True)


class TodoListApp(App):
    """A Textual app to manage a todo list."""

    CSS_PATH = "style.css"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    worklist_id = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.users = get_users()
        self.user_name_list = [
            dict(value=i, text=f"{user.first_name} {user.last_name}")
            for i, user in enumerate(self.users)
        ]
        self.user = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""

        yield Header()
        # Main App
        with Container(id="app-grid"):
            # Left Sidebar
            with Container(id='sidebar-vertical'):
                # user dropdown selection
                yield Select(
                    items=self.user_name_list,
                    placeholder="Select user ...",
                    list_mount="#sidebar-vertical",
                    id="user-list-widget",
                )
                # Worklists
                with Vertical(id='worklists-container-sub'):
                    yield Worklists(id="worklists")
                # Input to add a new worklist
                yield Input(placeholder="New Worklist", id="worklist-input")
            # Right Section
            with Vertical(id='right-section'):
                # All the task items
                with Vertical(id="task-item-container"):
                    yield TaskItems(id="task-items")
                # input to add a new task item
                yield Input(placeholder="New Task", id="task-input")
        yield Footer()

    def on_input_submitted(self, message):
        """This function is called anytime a user enters text in an input widget
        """
        if message.input.id == "task-input":
            task = create_task(message.value, worklist_id=self.worklist_id)
            message.input.value = ""
            # Weird way of forcing a change
            tasks = self.query_one("#task-items").tasks
            tasks.append(task)
            self.query_one("#task-items").tasks = tasks
        if message.input.id == "worklist-input":
            if self.user is not None:
                create_worklist(message.value, user_id=self.user.id)
                self.update_worklist_widget()
                message.input.value = ""

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def update_worklist_widget(self):
        """This will ensure the work list is updated and refreshed"""
        # Update the GUI and the worklist widget
        worklists = get_worklists(self.user.id) # get worklist from database
        worklists_widget: ListView = self.query_one("#worklists") 
        worklists_widget.worklists = worklists
        worklists_widget.refresh(layout=True)

    def on_select_changed(self, event: Select.Changed) -> None:
        """This function is called when the a user is selected from the dropdown
        It will load all the users workslists and load the all the tasks from the first worklist
        """
        self.user = self.users[int(event.value)] # get the user_id selected
        self.update_worklist_widget()

    def on_list_view_highlighted(self, event):
        "This function is called anytime a user clicks on a worklist"
        worklists_widget: ListView = self.query_one("#worklists")
        if worklists_widget.highlighted_child is not None:
            self.worklist_id = int(worklists_widget.highlighted_child.name)
            tasklist_widget: TaskItems = self.query_one("#task-items")
            tasklist_widget.tasks =  get_tasks(self.worklist_id)


def main():
    app = TodoListApp()
    app.run()


if __name__ == "__main__":
    main()