from click_shell import shell

@shell(prompt='todo-list> ', intro='Starting my app...')
def cli():
    pass

@cli.command()
def testcommand():
    print('testcommand is running')

# more commands

if __name__ == '__main__':
    cli()