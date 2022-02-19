#!/usr/bin/python3

# IMPORTS
import urwid # TUI
from pyfiglet import Figlet # Logo
from shutil import get_terminal_size, rmtree # File stuff + terminal size
from os import path, system, geteuid, mkdir # os stuff
from json import load, dump, loads # Json
from random import choice # Used for random app and splashes
from github import Github, GithubException # Github support
from thefuzz import process # Fuzzy search

# CONSTANT PATHS
FILEPATH = '/opt/tui-shop'
REPONAME = 'Gcat101/tui-shop-repo'

# Create opt path if it doesn't exist
if not path.exists(FILEPATH): mkdir(FILEPATH)

# FUNCTIONS

# Change displayed widget
def change_screen(name:str): loop.widget = urwid.Filler(globals()[name])

# Update install dict
def update_installed(name:str):
    global install, installscreen # Globals 

    install = load(open(FILEPATH + '/installed.json')) # Get install dict from file
    # Update installed screen
    installscreen[2].widget_list.pop()
    installscreen[2].widget_list.append(urwid.Pile([urwid.Button(('inv', f'{i[0] + 1}. {i[1]}'), on_press=page_gen(i[1])) for i in enumerate(install)]))

    # Set widget to download page
    page_gen(name)('')

# Clear screen
def clear_screen():
    global loop # Globals 
    loop.screen.clear() # Stop loop drawing
    system('clear') # Clear screen

# Add characters to input box on search screens
def search(k:str): 
    global listscreen, loop # Globals 

    try:
        if loop.widget.base_widget.widget_list == listscreen.widget_list: # If scrren is set to search
            if k=='backspace': listscreen[2][2][0].set_text(listscreen[2][2][0].get_text()[0][:-1]) # Backspace handling
            elif len(listscreen[2][2][0].text) <= 15 and len(k)==1: # Other keys
                listscreen[2][2][0].set_text(listscreen[2][2][0].get_text()[0] + k)
    except TypeError: pass # Skip mouse input

# Download app 
def download(name:str):
    global apps, install, loop # Globals 

    clear_screen() # Clear 

    # Dependencies
    if system(f'apt -y install {" ".join(apps[name]["dependencies"])} || pacman -Syu --noconfirm {" ".join(apps[name]["dependencies"])} || yum -y install {" ".join(apps[name]["dependencies"])} || zypper -n {" ".join(apps[name]["dependencies"])} || nix {" ".join(apps[name]["dependencies"])}') != 0:
        print("\u001b[1m\u001b[31mYOUR DISTRO ISN'T SUPPORTED\u001b[0m") # If package manager not found
        quit(1) # Quit with error
    print() # Linebreak
    # Clone repo
    if apps[name]['repo']:
        system(f'git clone https://github.com/{apps[name]["repo"]}.git {FILEPATH}/tmp')
        print() # Linebreak
    system('; '.join([f'cd {FILEPATH}/tmp'] + apps[name]['actions']['install'])) # Install action

    # Add app to installed
    with open(FILEPATH + '/installed.json', 'w') as f:
        if name not in install: install.append(name) # If not updating
        dump(install, f) # Dump to file
    rmtree(FILEPATH + '/tmp') # Remove tmp directory

    input('\nP\u001b[1mress enter to continue...\u001b[0m') # Click to continue
    update_installed(name) # Update install dict

# Remove app 
def remove(name:str):
    global apps, install # Globals 

    clear_screen() # Clear 

    # Clone repo
    system(f'git clone https://github.com/{apps[name]["repo"]}.git {FILEPATH}/tmp')
    print() # Linebreak
    system('; '.join([f'cd {FILEPATH}/tmp'] + apps[name]['actions']['remove']))
    
    # Remove app from installed
    with open(FILEPATH + '/installed.json', 'w') as f:
        install.remove(name)
        dump(install, f)
    rmtree(FILEPATH + '/tmp') # Remove tmp directory

    input('\n\u001b[1mPress enter to continue...\u001b[0m') # Click to continue
    update_installed(name) # Update install dict

# Generate download page
def page_gen(name:str): 
    global loop # Globals

    def page(_):
        global apps, loop, install, config, github # Globals

        # Render logo
        logo = []
        for line in apps[name]['logo']:
            for i in line:
                if i=='n': logo.append(' ') # If n then no color
                else: logo.append((i, '█')) # Else add color
            logo.append('\n') # Linebreak

        # Get data from github
        ghdata = github.get_repo(apps[name]['repo'])

        # Generate page
        downpage = urwid.Pile((
            BAR,
            LINEBREAK,

            urwid.Pile((
                urwid.Text(('bold', name), align=urwid.CENTER), # Name
                urwid.Text(apps[name]['description'], align=urwid.CENTER), # description
                
                LINEBREAK,
                urwid.Text(logo, align=urwid.CENTER), # Logo
                LINEBREAK
            ))
        ))
        if name in install: # If installed
            downpage.widget_list.append(urwid.Columns((
                urwid.Button('REMOVE', on_press=lambda _: remove(name)), # Remove button
                urwid.Button('UPDATE', on_press=lambda _: download(name)) # Update button
            ), 3))
        # If not installed
        else: downpage.widget_list.append(urwid.Button('INSTALL', on_press=lambda _: download(name))) # Install button

        downpage.widget_list.append(LINEBREAK) # Linebreak
        # Github data
        downpage.widget_list.append(urwid.Columns((
            urwid.Pile((
                urwid.Text(('bold', 'Stars'), align=urwid.CENTER), # Stars
                urwid.Text(str(ghdata.stargazers_count), align=urwid.CENTER)
            )),
            urwid.Pile((
                urwid.Text(('bold', 'Written in'), align=urwid.CENTER), # Language
                urwid.Text(ghdata.language if ghdata.language else '???', align=urwid.CENTER)
            )),
            urwid.Pile((
                urwid.Text(('bold', 'License'), align=urwid.CENTER), # License
                urwid.Text(ghdata.raw_data['license']['spdx_id'] if ghdata.raw_data['license'] else 'None', align=urwid.CENTER)
            )),
        )))
        
        loop.widget = urwid.Filler(downpage) # Update page

    # Return function pointer
    try: return page
    except Exception: # If there's an error with the app
        loop.stop()
        print("\u001b[1m\u001b[31mTHERE'S SOMETHING WRONG WITH THAT APP, TRY TO DOWNLOAD ANOTHER ONE\u001b[0m")
        quit(1) # Quit with error

# Generate search page
def gen_search(_):
    global listscreen # Globals

    # Get query
    q = listscreen[2][2][0].text

    # Make a new screen
    searchscreen = urwid.Pile((
        BAR,
        LINEBREAK,

        urwid.Pile((
            urwid.Text(('bold', 'SEARCH'), align=urwid.CENTER), # Title

            # Search box
            LINEBREAK,
            urwid.Columns((
                urwid.Text(''),
                urwid.Button('OK', on_press=gen_search) # OK button
            )),
            LINEBREAK,

            # App list
            urwid.Pile([urwid.Button(('inv', f'{i[0] + 1}. {i[1][0]}'), on_press=page_gen(i[1][0])) for i in enumerate(process.extract(q, apps.keys(), limit=5))])
        ))
    ))

    listscreen = searchscreen # Set search screen to new search screen
    change_screen('listscreen') # Update screen

# VARIABLES

# Config
if not path.exists(FILEPATH + '/config.json'): # If file doesn't exist
    with open(FILEPATH + '/config.json', 'w+') as f: f.write('''{
    "github": ""
}''') # Create
config = load(open(FILEPATH + '/config.json')) # Load

# Github client
github = Github(config['github'])

# Apps dict
try: apps = {i.name.replace('.json', '').replace('_', ' '):loads(i.decoded_content.decode('utf-8')) for i in github.get_repo(REPONAME).get_contents('apps')}
except GithubException: # If github token invalid
    print(f'\u001b[1m\u001b[31mPUT A VALID GITHUB TOKEN IN THE CONFIG ({FILEPATH}/config.json)\u001b[0m')
    exit(1)

# Install dict
if not path.exists(FILEPATH + '/installed.json'): # If file doesn't exist
    with open(FILEPATH + '/installed.json', 'w+') as f: f.write('["tui-shop"]') # Create
install = load(open(FILEPATH + '/installed.json')) # Load

# CONSTANTS

LINEBREAK = urwid.Text('') # Urwid text linebreak
BAR = urwid.Columns((
    urwid.Button(('bold', 'HOME'), on_press=lambda _: change_screen('mainscreen')),
    urwid.Button(('bold', 'SEARCH'), on_press=lambda _: change_screen('listscreen')),
    urwid.Button(('bold', 'INSTALLED'), on_press=lambda _: change_screen('installscreen')),
    urwid.Button(('bold', 'ABOUT'), on_press=lambda _: change_screen('aboutscreen')),
    urwid.Button(('bold', 'QUIT'), on_press=lambda _: change_screen('quitscreen'))
), 5) # Bar (self-explanatory button names)

# SCREENS

# Load screen
loadscreen = urwid.Pile((
    urwid.Text(Figlet().renderText('TUI-SHOP'), align=urwid.CENTER), # Logo

    urwid.Text(choice(('Welcome!', 'Your favorite package manager!', 'Also try apt!', 'Made with python!')), align=urwid.CENTER), # Splash
    urwid.Button('OK', on_press=lambda _: change_screen('mainscreen')) # OK button
))

rand = choice(list(apps.keys())) # Random app

# Render logo
logo = []
for line in apps[rand]['logo']:
    for i in line:
        if i=='n': logo.append(' ') # If n then no color
        else: logo.append((i, '█')) # Else add color
    logo.append('\n') # Linebreak

# Home screen
mainscreen = urwid.Pile((
    BAR,
    
    LINEBREAK,
    urwid.Text(('bold', 'HOME'), align=urwid.CENTER), # Title
    LINEBREAK,

    urwid.Columns((
        urwid.Pile((
            urwid.Text(('bold', 'NEWS'), align=urwid.CENTER), # Title
            LINEBREAK,
            urwid.Text(github.get_repo(REPONAME).get_contents('news.txt').decoded_content, align=urwid.CENTER), # Get news from github
        )),
        urwid.Text('|\n' * get_terminal_size().lines, align=urwid.CENTER),
        urwid.Pile((
            urwid.Text(('bold', 'RANDOM APP'), align=urwid.CENTER), # Title
            LINEBREAK,
            urwid.Pile((
                urwid.Text(('bold', rand), align=urwid.CENTER), # Name
                urwid.Text(logo, align=urwid.CENTER), # Logo
                urwid.Text(apps[rand]["description"], align=urwid.CENTER), # Description
                urwid.Button(('bold', 'GO'), on_press=page_gen(rand)) # GO button
            ))
        ))
    ))
))
# Serch screen
listscreen = urwid.Pile((
    BAR,
    LINEBREAK,

    urwid.Pile((
        urwid.Text(('bold', 'SEARCH'), align=urwid.CENTER), # Title

        LINEBREAK,
        # Search box
        urwid.Columns((
            urwid.Text(''), 
            urwid.Button('OK', on_press=gen_search) # OK button
        )),
        LINEBREAK,

        # App list
        urwid.Pile([urwid.Button(('inv', f'{i[0] + 1}. {i[1]}'), on_press=page_gen(i[1])) for i in enumerate(apps.keys())])
    ))
))
# Installed screen
installscreen = urwid.Pile((
    BAR,
    LINEBREAK,

    urwid.Pile((
        urwid.Text(('bold', 'INSTALLED'), align=urwid.CENTER), # Title
        LINEBREAK,
        urwid.Pile([urwid.Button(('inv', f'{i[0] + 1}. {i[1]}'), on_press=page_gen(i[1])) for i in enumerate(sorted(install))]) # App list
    ))
))
# About screen
aboutscreen = urwid.Pile((
    BAR,
    LINEBREAK,

    urwid.Text(('bold', 'ABOUT'), align=urwid.CENTER), # Title
    LINEBREAK,

    urwid.Pile((
        urwid.Text(('bold', 'Creator'), align=urwid.CENTER),
        urwid.Text('https://github.com/G_cat101', align=urwid.CENTER),
        LINEBREAK,

        urwid.Text(('bold', 'Repo'), align=urwid.CENTER),
        urwid.Text('https://github.com/G_cat101/tui-shop', align=urwid.CENTER),
        LINEBREAK,

        urwid.Text(('bold', 'App repo'), align=urwid.CENTER),
        urwid.Text('https://github.com/G_cat101/tui-shop-repo', align=urwid.CENTER),
        LINEBREAK,

        urwid.Text(('bold', 'License'), align=urwid.CENTER),
        urwid.Text('GPL-3.0', align=urwid.CENTER),
        LINEBREAK,
    )) # About (self-explanatory fields)
))
# Quit screen
quitscreen = urwid.Pile((
    BAR,
    LINEBREAK,

    urwid.Text(('bold', 'QUIT'), align=urwid.CENTER), # Title
    LINEBREAK,

    urwid.Text('Are you sure?', align=urwid.CENTER), # ?
    LINEBREAK,

    urwid.Columns((
        urwid.Button('Yes', on_press=lambda _: (loop.stop(), quit(0))), # Stops the loop and quits
        urwid.Button('No', on_press=lambda _: change_screen('mainscreen')) # Return to home screen
    ))
))

# If not imported
if __name__=='__main__':
    # Create loop
    loop = urwid.MainLoop(urwid.Filler(loadscreen), (
        ('bold', 'default,bold', 'default', 'bold'),
        ('inv', 'black', 'light gray'),

        ('r', 'dark red', ''),
        ('l', 'light green', ''),
        ('b', 'dark blue', ''),
        ('y', 'yellow', ''),
        ('p', 'dark magenta', ''),

        ('w', 'light gray', ''),
        ('g', 'dark gray', ''),
        ('d', 'black', '')
    ), unhandled_input=search)
    
    # If root
    if geteuid()==0:
            try: loop.run() # Run loop
            except KeyboardInterrupt: quit(0) # Quit on ctrl+c
            except AttributeError: quit(1) # Idk why this bug happends but it just quits with error
    else: # If not root
        print('\u001b[1m\u001b[31mRUN AS ROOT\u001b[0m')
        quit(1) # Quit with error

# THE END