import click

def yes_no_prompt(prompt: str) -> bool:
    response = ''

    while response not in ['y', 'n', 'Y', 'N']:
        response = click.input(prompt, prompt_suffix=' [y/N] ')

    if response in ['y', 'Y']:
        return True
    else:
        return False
