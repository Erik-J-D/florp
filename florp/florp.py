import logging
import os
import sys
import webbrowser
from threading import Timer
from typing import Union

import markdown
from flask import Flask, Response, render_template, send_from_directory
from flask_socketio import SocketIO  # type: ignore
from watchdog.events import (  # type: ignore
    DirModifiedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer  # type: ignore

from .markdown_checklist import CheckboxExtension

# Turn off flask banner
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None  # type: ignore

# Flask app + turn off logging
app = Flask(__name__)
app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True
socketio = SocketIO(app)

PORT = 6453
NO_FILENAME_ERR = '''
florp needs a filename to run:
  $ florp myfile.md
'''.strip()


def markdown_file_to_html(filename: str) -> str:
    with open(filename, "r", encoding="utf-8") as input_file:
        text = input_file.read()
    return markdown.markdown(text, extensions=[
        'sane_lists',
        'md_in_html',
        'fenced_code',
        'codehilite',
        CheckboxExtension()
    ])


@app.route('/')
def serve() -> str:
    """Start up a server serving html of the filename"""
    html = markdown_file_to_html(app.config['FILENAME'])

    return render_template('template.html',
                           content=html,
                           title=app.config['FILENAME'])


@app.route('/css/<path:path>')
def send_css(path: str) -> Response:
    """Serve the contents of templates/css at the /css/<file> endpoint"""
    return send_from_directory('templates/css', path)


@app.route('/js/<path:path>')
def send_js(path: str) -> Response:
    """Serve the contents of templates/js at the /js/<file> endpoint"""
    return send_from_directory('templates/js', path)


def open_browser() -> None:
    """Open a browser to the page"""
    webbrowser.open(f'http://127.0.0.1:{PORT}/')


class evtHandler(FileSystemEventHandler):
    def on_modified(self, event: Union[FileModifiedEvent, DirModifiedEvent]):
        if type(event) == FileModifiedEvent:
            socketio.emit(
                "new body",
                markdown_file_to_html(app.config['FILENAME'])
            )


def florp_cli(args: list[str] = None) -> None:
    """Process command line arguments."""
    if not args:
        if len(sys.argv) > 1:
            args = sys.argv[1:]
        else:
            sys.exit(NO_FILENAME_ERR)

    filename = args[0]
    if not os.path.isfile(filename):
        sys.exit(f"File not found: {filename}")
    app.config['FILENAME'] = filename

    observer = Observer()
    event_handler = evtHandler()
    observer.schedule(event_handler, filename)
    observer.start()

    print(f'Serving {filename} at http://127.0.0.1:{PORT}/')

    Timer(0.1, open_browser).start()
    socketio.run(app, port=PORT)
