# -x-
""" special constants used throughout jupyter_lsp
"""

# the current `entry_point` to use for python-based spec finders
EP_SPEC_V1 = "jupyter_lsp_spec_v1"

# the current `entry_point`s to use for python-based listeners
EP_LISTENER_ALL_V1 = "jupyter_lsp_listener_all_v1"
EP_LISTENER_CLIENT_V1 = "jupyter_lsp_listener_client_v1"
EP_LISTENER_SERVER_V1 = "jupyter_lsp_listener_server_v1"

# jupyter*config.d where language_servers can be defined
APP_CONFIG_D_SECTIONS = ["_", "_notebook_", "_server_"]
""" tornado handler for managing and communicating with language servers
"""

from typing import Optional, Text

from jupyter_core.utils import ensure_async
from jupyter_server.base.handlers import APIHandler, JupyterHandler
from jupyter_server.utils import url_path_join as ujoin
from tornado import web
from tornado.websocket import WebSocketHandler

try:
    from jupyter_server.auth.decorator import authorized
except ImportError:

    def authorized(method):  # type: ignore
        """A no-op fallback for `jupyter_server 1.x`"""
        return method


try:
    from jupyter_server.base.websocket import WebSocketMixin
except ImportError:
    from jupyter_server.base.zmqhandlers import WebSocketMixin

from .manager import LanguageServerManager
from .schema import SERVERS_RESPONSE
from .specs.utils import censored_spec

AUTH_RESOURCE = "lsp"


class BaseHandler(APIHandler):
    manager = None  # type: LanguageServerManager

    def initialize(self, manager: LanguageServerManager):
        self.manager = manager


class BaseJupyterHandler(JupyterHandler):
    manager = None  # type: LanguageServerManager

    def initialize(self, manager: LanguageServerManager):
        self.manager = manager


class LanguageServerWebSocketHandler(  # type: ignore
    WebSocketMixin, WebSocketHandler, BaseJupyterHandler
):
    """Setup tornado websocket to route to language server sessions.

    The logic of `get` and `pre_get` methods is derived from jupyter-server ws handlers,
    and should be kept in sync to follow best practice established by upstream; see:
    https://github.com/jupyter-server/jupyter_server/blob/v2.12.5/jupyter_server/services/kernels/websocket.py#L36
    """

    auth_resource = AUTH_RESOURCE

    language_server: Optional[Text] = None

    async def pre_get(self):
        """Handle a pre_get."""
        # authenticate first
        # authenticate the request before opening the websocket
        user = self.current_user
        if user is None:
            self.log.warning("Couldn't authenticate WebSocket connection")
            raise web.HTTPError(403)

        if not hasattr(self, "authorizer"):
            return

        # authorize the user.
        is_authorized = await ensure_async(
            self.authorizer.is_authorized(self, user, "execute", AUTH_RESOURCE)
        )
        if not is_authorized:
            raise web.HTTPError(403)

    async def get(self, *args, **kwargs):
        """Get an event socket."""
        await self.pre_get()
        res = super().get(*args, **kwargs)
        if res is not None:
            await res

    async def open(self, language_server):
        await self.manager.ready()
        self.language_server = language_server
        self.manager.subscribe(self)
        self.log.debug("[{}] Opened a handler".format(self.language_server))
        super().open()

    async def on_message(self, message):
        self.log.debug("[{}] Handling a message".format(self.language_server))
        await self.manager.on_client_message(message, self)

    def on_close(self):
        self.manager.unsubscribe(self)
        self.log.debug("[{}] Closed a handler".format(self.language_server))


class LanguageServersHandler(BaseHandler):
    """Reports the status of all current servers

    Response should conform to schema in schema/servers.schema.json
    """

    auth_resource = AUTH_RESOURCE
    validator = SERVERS_RESPONSE

    @web.authenticated
    @authorized
    async def get(self):
        """finish with the JSON representations of the sessions"""
        await self.manager.ready()

        response = {
            "version": 2,
            "sessions": {
                language_server: session.to_json()
                for language_server, session in self.manager.sessions.items()
            },
            "specs": {
                key: censored_spec(spec)
                for key, spec in self.manager.all_language_servers.items()
            },
        }

        errors = list(self.validator.iter_errors(response))

        if errors:  # pragma: no cover
            self.log.warning("{} validation errors: {}".format(len(errors), errors))

        self.finish(response)


def add_handlers(nbapp):
    """Add Language Server routes to the notebook server web application"""
    lsp_url = ujoin(nbapp.base_url, "lsp")
    re_langservers = "(?P<language_server>.*)"

    opts = {"manager": nbapp.language_server_manager}

    nbapp.web_app.add_handlers(
        ".*",
        [
            (ujoin(lsp_url, "status"), LanguageServersHandler, opts),
            (
                ujoin(lsp_url, "ws", re_langservers),
                LanguageServerWebSocketHandler,
                opts,
            ),
        ],
    )
# -x-
""" A configurable frontend for stdio-based Language Servers
"""

import asyncio
import os
import sys
import traceback
from typing import Dict, Text, Tuple, cast

# See compatibility note on `group` keyword in
# https://docs.python.org/3/library/importlib.metadata.html#entry-points
if sys.version_info < (3, 10):  # pragma: no cover
    from importlib_metadata import entry_points
else:  # pragma: no cover
    from importlib.metadata import entry_points

from jupyter_core.paths import jupyter_config_path
from jupyter_server.services.config import ConfigManager

try:
    from jupyter_server.transutils import _i18n as _
except ImportError:  # pragma: no cover
    from jupyter_server.transutils import _

from traitlets import Bool
from traitlets import Dict as Dict_
from traitlets import Instance
from traitlets import List as List_
from traitlets import Unicode, default

from .constants import (
    APP_CONFIG_D_SECTIONS,
    EP_LISTENER_ALL_V1,
    EP_LISTENER_CLIENT_V1,
    EP_LISTENER_SERVER_V1,
    EP_SPEC_V1,
)
from .schema import LANGUAGE_SERVER_SPEC_MAP
from .session import LanguageServerSession
from .trait_types import LoadableCallable, Schema
from .types import (
    KeyedLanguageServerSpecs,
    LanguageServerManagerAPI,
    MessageScope,
    SpecBase,
    SpecMaker,
)


class LanguageServerManager(LanguageServerManagerAPI):
    """Manage language servers"""

    conf_d_language_servers = Schema(  # type:ignore[assignment]
        validator=LANGUAGE_SERVER_SPEC_MAP,
        help=_("extra language server specs, keyed by implementation, from conf.d"),
    )  # type: KeyedLanguageServerSpecs

    language_servers = Schema(  # type:ignore[assignment]
        validator=LANGUAGE_SERVER_SPEC_MAP,
        help=_("a dict of language server specs, keyed by implementation"),
    ).tag(
        config=True
    )  # type: KeyedLanguageServerSpecs

    autodetect: bool = Bool(  # type:ignore[assignment]
        True, help=_("try to find known language servers in sys.prefix (and elsewhere)")
    ).tag(config=True)

    sessions: Dict[Tuple[Text], LanguageServerSession] = (
        Dict_(  # type:ignore[assignment]
            trait=Instance(LanguageServerSession),
            default_value={},
            help="sessions keyed by language server name",
        )
    )

    virtual_documents_dir = Unicode(
        help="""Path to virtual documents relative to the content manager root
        directory.

        Its default value can be set with JP_LSP_VIRTUAL_DIR and fallback to
        '.virtual_documents'.
        """
    ).tag(config=True)

    _ready = Bool(
        help="""Whether the manager has been initialized""", default_value=False
    )

    all_listeners = List_(  # type:ignore[var-annotated]
        trait=LoadableCallable  # type:ignore[arg-type]
    ).tag(config=True)
    server_listeners = List_(  # type:ignore[var-annotated]
        trait=LoadableCallable  # type:ignore[arg-type]
    ).tag(config=True)
    client_listeners = List_(  # type:ignore[var-annotated]
        trait=LoadableCallable  # type:ignore[arg-type]
    ).tag(config=True)

    @default("language_servers")
    def _default_language_servers(self):
        return {}

    @default("virtual_documents_dir")
    def _default_virtual_documents_dir(self):
        return os.getenv("JP_LSP_VIRTUAL_DIR", ".virtual_documents")

    @default("conf_d_language_servers")
    def _default_conf_d_language_servers(self) -> KeyedLanguageServerSpecs:
        language_servers: KeyedLanguageServerSpecs = {}

        manager = ConfigManager(read_config_path=jupyter_config_path())

        for app in APP_CONFIG_D_SECTIONS:
            language_servers.update(
                **manager.get(f"jupyter{app}config")
                .get(self.__class__.__name__, {})
                .get("language_servers", {})
            )

        return language_servers

    def __init__(self, **kwargs: Dict):
        """Before starting, perform all necessary configuration"""
        self.all_language_servers: KeyedLanguageServerSpecs = {}
        self._language_servers_from_config: KeyedLanguageServerSpecs = {}
        super().__init__(**kwargs)

    def initialize(self, *args, **kwargs):
        self.init_language_servers()
        self.init_listeners()
        self.init_sessions()
        self._ready = True

    async def ready(self):
        while not self._ready:  # pragma: no cover
            await asyncio.sleep(0.1)
        return True

    def init_language_servers(self) -> None:
        """determine the final language server configuration."""
        # copy the language servers before anybody monkeys with them
        self._language_servers_from_config = dict(self.language_servers)
        self.language_servers = self._collect_language_servers(only_installed=True)
        self.all_language_servers = self._collect_language_servers(only_installed=False)

    def _collect_language_servers(
        self, only_installed: bool
    ) -> KeyedLanguageServerSpecs:
        language_servers: KeyedLanguageServerSpecs = {}

        language_servers_from_config = dict(self._language_servers_from_config)
        language_servers_from_config.update(self.conf_d_language_servers)

        if self.autodetect:
            language_servers.update(
                self._autodetect_language_servers(only_installed=only_installed)
            )

        # restore config
        language_servers.update(language_servers_from_config)

        # coalesce the servers, allowing a user to opt-out by specifying `[]`
        return {key: spec for key, spec in language_servers.items() if spec.get("argv")}

    def init_sessions(self):
        """create, but do not initialize all sessions"""
        sessions = {}
        for language_server, spec in self.language_servers.items():
            sessions[language_server] = LanguageServerSession(
                language_server=language_server, spec=spec, parent=self
            )
        self.sessions = sessions

    def init_listeners(self):
        """register traitlets-configured listeners"""

        scopes = {
            MessageScope.ALL: [self.all_listeners, EP_LISTENER_ALL_V1],
            MessageScope.CLIENT: [self.client_listeners, EP_LISTENER_CLIENT_V1],
            MessageScope.SERVER: [self.server_listeners, EP_LISTENER_SERVER_V1],
        }
        for scope, trt_ep in scopes.items():
            listeners, entry_point = trt_ep

            for ept in entry_points(group=entry_point):  # pragma: no cover
                try:
                    listeners.append(ept.load())
                except Exception as err:
                    self.log.warning("Failed to load entry point %s: %s", ept.name, err)

            for listener in listeners:
                self.__class__.register_message_listener(scope=scope.value)(listener)

    def subscribe(self, handler):
        """subscribe a handler to session, or sta"""
        session = self.sessions.get(handler.language_server)

        if session is None:
            self.log.error(
                "[{}] no session: handler subscription failed".format(
                    handler.language_server
                )
            )
            return

        session.handlers = set([handler]) | session.handlers

    async def on_client_message(self, message, handler):
        await self.wait_for_listeners(
            MessageScope.CLIENT, message, handler.language_server
        )
        session = self.sessions.get(handler.language_server)

        if session is None:
            self.log.error(
                "[{}] no session: client message dropped".format(
                    handler.language_server
                )
            )
            return

        session.write(message)

    async def on_server_message(self, message, session):
        language_servers = [
            ls_key for ls_key, sess in self.sessions.items() if sess == session
        ]

        for language_servers in language_servers:
            await self.wait_for_listeners(
                MessageScope.SERVER, message, language_servers
            )

        for handler in session.handlers:
            handler.write_message(message)

    def unsubscribe(self, handler):
        session = self.sessions.get(handler.language_server)

        if session is None:
            self.log.error(
                "[{}] no session: handler unsubscription failed".format(
                    handler.language_server
                )
            )
            return

        session.handlers = [h for h in session.handlers if h != handler]

    def _autodetect_language_servers(self, only_installed: bool):
        _entry_points = None

        try:
            _entry_points = entry_points(group=EP_SPEC_V1)
        except Exception:  # pragma: no cover
            self.log.exception("Failed to load entry_points")

        skipped_servers = []

        for ep in _entry_points or []:
            try:
                spec_finder: SpecMaker = ep.load()
            except Exception as err:  # pragma: no cover
                self.log.warning(
                    _("Failed to load language server spec finder `{}`: \n{}").format(
                        ep.name, err
                    )
                )
                continue

            try:
                if only_installed:
                    if hasattr(spec_finder, "is_installed"):
                        spec_finder_from_base = cast(SpecBase, spec_finder)
                        if not spec_finder_from_base.is_installed(self):
                            skipped_servers.append(ep.name)
                            continue
                specs = spec_finder(self) or {}
            except Exception as err:  # pragma: no cover
                self.log.warning(
                    _(
                        "Failed to fetch commands from language server spec finder"
                        " `{}`:\n{}"
                    ).format(ep.name, err)
                )
                traceback.print_exc()

                continue

            errors = list(LANGUAGE_SERVER_SPEC_MAP.iter_errors(specs))

            if errors:  # pragma: no cover
                self.log.warning(
                    _(
                        "Failed to validate commands from language server spec finder"
                        " `{}`:\n{}"
                    ).format(ep.name, errors)
                )
                continue

            for key, spec in specs.items():
                yield key, spec

        if skipped_servers:
            self.log.info(
                _("Skipped non-installed server(s): {}").format(
                    ", ".join(skipped_servers)
                )
            )


# the listener decorator
lsp_message_listener = LanguageServerManager.register_message_listener  # noqa
# -x-
"""
Derived from

> https://github.com/rudolfwalter/pygdbmi/blob/0.7.4.2/pygdbmi/gdbcontroller.py
> MIT License  https://github.com/rudolfwalter/pygdbmi/blob/master/LICENSE
> Copyright (c) 2016 Chad Smith <grassfedcode <at> gmail.com>
"""

import os

if os.name == "nt":  # pragma: no cover
    import msvcrt
    from ctypes import POINTER, WinError, byref, windll, wintypes  # type: ignore
    from ctypes.wintypes import BOOL, DWORD, HANDLE  # type: ignore
else:  # pragma: no cover
    import fcntl


def make_non_blocking(file_obj):  # pragma: no cover
    """
    make file object non-blocking

    Windows doesn't have the fcntl module, but someone on
    stack overflow supplied this code as an answer, and it works
    http://stackoverflow.com/a/34504971/2893090
    """

    if os.name == "nt":
        LPDWORD = POINTER(DWORD)
        PIPE_NOWAIT = wintypes.DWORD(0x00000001)

        SetNamedPipeHandleState = windll.kernel32.SetNamedPipeHandleState
        SetNamedPipeHandleState.argtypes = [HANDLE, LPDWORD, LPDWORD, LPDWORD]
        SetNamedPipeHandleState.restype = BOOL

        h = msvcrt.get_osfhandle(file_obj.fileno())

        res = windll.kernel32.SetNamedPipeHandleState(h, byref(PIPE_NOWAIT), None, None)
        if res == 0:
            raise ValueError(WinError())

    else:
        # Set the file status flag (F_SETFL) on the pipes to be non-blocking
        # so we can attempt to read from a pipe with no new data without locking
        # the program up
        fcntl.fcntl(file_obj, fcntl.F_SETFL, os.O_NONBLOCK)
# -x-
import os
import re
from pathlib import Path
from typing import Union
from urllib.parse import unquote, urlparse

RE_PATH_ANCHOR = r"^file://([^/]+|/[A-Z]:)"

# -x-
def normalized_uri(root_dir):
    """Attempt to make an LSP rootUri from a ContentsManager root_dir

    Special care must be taken around windows paths: the canonical form of
    windows drives and UNC paths is lower case
    """
    root_uri = Path(root_dir).expanduser().resolve().as_uri()
    root_uri = re.sub(
        RE_PATH_ANCHOR, lambda m: "file://{}".format(m.group(1).lower()), root_uri
    )
    return root_uri

# -x-
def file_uri_to_path(file_uri):
    """Return a path string for give file:/// URI.

    Respect the different path convention on Windows.
    Based on https://stackoverflow.com/a/57463161/6646912, BSD 0
    """
    windows_path = os.name == "nt"
    file_uri_parsed = urlparse(file_uri)
    file_uri_path_unquoted = unquote(file_uri_parsed.path)
    if windows_path and file_uri_path_unquoted.startswith("/"):
        result = file_uri_path_unquoted[1:]  # pragma: no cover
    else:
        result = file_uri_path_unquoted  # pragma: no cover
    return result

# -x-
def is_relative(root: Union[str, Path], path: Union[str, Path]) -> bool:
    """Return if path is relative to root"""
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False
# -x-
""" A session for managing a language server process
"""

import asyncio
import atexit
import os
import string
import subprocess
from datetime import datetime, timezone

from tornado.ioloop import IOLoop
from tornado.queues import Queue
from tornado.websocket import WebSocketHandler
from traitlets import Bunch, Instance, Set, Unicode, UseEnum, observe
from traitlets.config import LoggingConfigurable

from . import stdio
from .schema import LANGUAGE_SERVER_SPEC
from .specs.utils import censored_spec
from .trait_types import Schema
from .types import SessionStatus


class LanguageServerSession(LoggingConfigurable):
    """Manage a session for a connection to a language server"""

    language_server = Unicode(help="the language server implementation name")
    spec = Schema(LANGUAGE_SERVER_SPEC)

    # run-time specifics
    process = Instance(
        subprocess.Popen, help="the language server subprocess", allow_none=True
    )
    writer = Instance(stdio.LspStdIoWriter, help="the JSON-RPC writer", allow_none=True)
    reader = Instance(stdio.LspStdIoReader, help="the JSON-RPC reader", allow_none=True)
    from_lsp = Instance(
        Queue, help="a queue for string messages from the server", allow_none=True
    )
    to_lsp = Instance(
        Queue, help="a queue for string message to the server", allow_none=True
    )
    handlers = Set(
        trait=Instance(WebSocketHandler),
        default_value=[],
        help="the currently subscribed websockets",
    )
    status = UseEnum(SessionStatus, default_value=SessionStatus.NOT_STARTED)
    last_handler_message_at = Instance(datetime, allow_none=True)
    last_server_message_at = Instance(datetime, allow_none=True)

    _tasks = None

    _skip_serialize = ["argv", "debug_argv"]

    def __init__(self, *args, **kwargs):
        """set up the required traitlets and exit behavior for a session"""
        super().__init__(*args, **kwargs)
        atexit.register(self.stop)

    def __repr__(self):  # pragma: no cover
        return (
            "<LanguageServerSession(" "language_server={language_server}, argv={argv})>"
        ).format(language_server=self.language_server, **self.spec)

    def to_json(self):
        return dict(
            handler_count=len(self.handlers),
            status=self.status.value,
            last_server_message_at=(
                self.last_server_message_at.isoformat()
                if self.last_server_message_at
                else None
            ),
            last_handler_message_at=(
                self.last_handler_message_at.isoformat()
                if self.last_handler_message_at
                else None
            ),
            spec=censored_spec(self.spec),
        )

    def initialize(self):
        """(re)initialize a language server session"""
        self.stop()
        self.status = SessionStatus.STARTING
        self.init_queues()
        self.init_process()
        self.init_writer()
        self.init_reader()

        loop = asyncio.get_event_loop()
        self._tasks = [
            loop.create_task(coro())
            for coro in [self._read_lsp, self._write_lsp, self._broadcast_from_lsp]
        ]

        self.status = SessionStatus.STARTED

    def stop(self):
        """clean up all of the state of the session"""

        self.status = SessionStatus.STOPPING

        if self.process:
            self.process.terminate()
            self.process = None
        if self.reader:
            self.reader.close()
            self.reader = None
        if self.writer:
            self.writer.close()
            self.writer = None

        if self._tasks:
            [task.cancel() for task in self._tasks]

        self.status = SessionStatus.STOPPED

    @observe("handlers")
    def _on_handlers(self, change: Bunch):
        """re-initialize if someone starts listening, or stop if nobody is"""
        if change["new"] and not self.process:
            self.initialize()
        elif not change["new"] and self.process:
            self.stop()

    def write(self, message):
        """wrapper around the write queue to keep it mostly internal"""
        self.last_handler_message_at = self.now()
        IOLoop.current().add_callback(self.to_lsp.put_nowait, message)

    def now(self):
        return datetime.now(timezone.utc)

    def init_process(self):
        """start the language server subprocess"""
        self.process = subprocess.Popen(
            self.spec["argv"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            env=self.substitute_env(self.spec.get("env", {}), os.environ),
            bufsize=0,
        )

    def init_queues(self):
        """create the queues"""
        self.from_lsp = Queue()
        self.to_lsp = Queue()

    def init_reader(self):
        """create the stdout reader (from the language server)"""
        self.reader = stdio.LspStdIoReader(
            stream=self.process.stdout, queue=self.from_lsp, parent=self
        )

    def init_writer(self):
        """create the stdin writer (to the language server)"""
        self.writer = stdio.LspStdIoWriter(
            stream=self.process.stdin, queue=self.to_lsp, parent=self
        )

    def substitute_env(self, env, base):
        final_env = base.copy()

        for key, value in env.items():
            final_env.update({key: string.Template(value).safe_substitute(base)})

        return final_env

    async def _read_lsp(self):
        await self.reader.read()

    async def _write_lsp(self):
        await self.writer.write()

    async def _broadcast_from_lsp(self):
        """loop for reading messages from the queue of messages from the language
        server
        """
        async for message in self.from_lsp:
            self.last_server_message_at = self.now()
            await self.parent.on_server_message(message, self)
            self.from_lsp.task_done()
# -x-
""" Language Server stdio-mode readers

Parts of this code are derived from:

> https://github.com/palantir/python-jsonrpc-server/blob/0.2.0/pyls_jsonrpc/streams.py#L83   # noqa
> https://github.com/palantir/python-jsonrpc-server/blob/45ed1931e4b2e5100cc61b3992c16d6f68af2e80/pyls_jsonrpc/streams.py  # noqa
> > MIT License   https://github.com/palantir/python-jsonrpc-server/blob/0.2.0/LICENSE
> > Copyright 2018 Palantir Technologies, Inc.
"""

# pylint: disable=broad-except
import asyncio
import io
import os
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Text

from tornado.concurrent import run_on_executor
from tornado.gen import convert_yielded
from tornado.httputil import HTTPHeaders
from tornado.ioloop import IOLoop
from tornado.queues import Queue
from traitlets import Float, Instance, default
from traitlets.config import LoggingConfigurable

from .non_blocking import make_non_blocking

# -x-
class LspStdIoBase(LoggingConfigurable):
    """Non-blocking, queued base for communicating with stdio Language Servers"""

    executor = None

    stream = Instance(  # type:ignore[assignment]
        io.RawIOBase, help="the stream to read/write"
    )  # type: io.RawIOBase
    queue = Instance(Queue, help="queue to get/put")

    def __repr__(self):  # pragma: no cover
        return "<{}(parent={})>".format(self.__class__.__name__, self.parent)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.log.debug("%s initialized", self)
        self.executor = ThreadPoolExecutor(max_workers=1)

    def close(self):
        self.stream.close()
        self.log.debug("%s closed", self)

# -x-
class LspStdIoReader(LspStdIoBase):
    """Language Server stdio Reader

    Because non-blocking (but still synchronous) IO is used, rudimentary
    exponential backoff is used.
    """

    max_wait = Float(help="maximum time to wait on idle stream").tag(config=True)
    min_wait = Float(0.05, help="minimum time to wait on idle stream").tag(config=True)
    next_wait = Float(0.05, help="next time to wait on idle stream").tag(config=True)

    @default("max_wait")
    def _default_max_wait(self):
        return 0.1 if os.name == "nt" else self.min_wait * 2

    async def sleep(self):
        """Simple exponential backoff for sleeping"""
        if self.stream.closed:  # pragma: no cover
            return
        self.next_wait = min(self.next_wait * 2, self.max_wait)
        try:
            await asyncio.sleep(self.next_wait)
        except Exception:  # pragma: no cover
            pass

    def wake(self):
        """Reset the wait time"""
        self.wait = self.min_wait

    async def read(self) -> None:
        """Read from a Language Server until it is closed"""
        make_non_blocking(self.stream)

        while not self.stream.closed:
            message = None
            try:
                message = await self.read_one()

                if not message:
                    await self.sleep()
                    continue
                else:
                    self.wake()

                IOLoop.current().add_callback(self.queue.put_nowait, message)
            except Exception as e:  # pragma: no cover
                self.log.exception(
                    "%s couldn't enqueue message: %s (%s)", self, message, e
                )
                await self.sleep()

    async def _read_content(
        self, length: int, max_parts=1000, max_empties=200
    ) -> Optional[bytes]:
        """Read the full length of the message unless exceeding max_parts or
           max_empties empty reads occur.

        See https://github.com/jupyter-lsp/jupyterlab-lsp/issues/450

        Crucial docs or read():
            "If the argument is positive, and the underlying raw
             stream is not interactive, multiple raw reads may be issued
             to satisfy the byte count (unless EOF is reached first)"

        Args:
           - length: the content length
           - max_parts: prevent absurdly long messages (1000 parts is several MBs):
             1 part is usually sufficient but not enough for some long
             messages 2 or 3 parts are often needed.
        """
        raw = None
        raw_parts: List[bytes] = []
        received_size = 0
        while received_size < length and len(raw_parts) < max_parts and max_empties > 0:
            part = None
            try:
                part = self.stream.read(length - received_size)
            except OSError:  # pragma: no cover
                pass
            if part is None:
                max_empties -= 1
                await self.sleep()
                continue
            received_size += len(part)
            raw_parts.append(part)

        if raw_parts:
            raw = b"".join(raw_parts)
            if len(raw) != length:  # pragma: no cover
                self.log.warning(
                    f"Readout and content-length mismatch: {len(raw)} vs {length};"
                    f"remaining empties: {max_empties}; remaining parts: {max_parts}"
                )

        return raw

    async def read_one(self) -> Text:
        """Read a single message"""
        message = ""
        headers = HTTPHeaders()

        line = await convert_yielded(self._readline())

        if line:
            while line and line.strip():
                headers.parse_line(line)
                line = await convert_yielded(self._readline())

            content_length = int(headers.get("content-length", "0"))

            if content_length:
                raw = await self._read_content(length=content_length)
                if raw is not None:
                    message = raw.decode("utf-8").strip()
                else:  # pragma: no cover
                    self.log.warning(
                        "%s failed to read message of length %s",
                        self,
                        content_length,
                    )

        return message

    @run_on_executor
    def _readline(self) -> Text:
        """Read a line (or immediately return None)"""
        try:
            return self.stream.readline().decode("utf-8").strip()
        except OSError:  # pragma: no cover
            return ""

# -x-
class LspStdIoWriter(LspStdIoBase):
    """Language Server stdio Writer"""

    async def write(self) -> None:
        """Write to a Language Server until it closes"""
        while not self.stream.closed:
            message = await self.queue.get()
            try:
                body = message.encode("utf-8")
                response = "Content-Length: {}\r\n\r\n{}".format(len(body), message)
                await convert_yielded(self._write_one(response.encode("utf-8")))
            except Exception:  # pragma: no cover
                self.log.exception("%s couldn't write message: %s", self, response)
            finally:
                self.queue.task_done()

    @run_on_executor
    def _write_one(self, message) -> None:
        self.stream.write(message)
        self.stream.flush()
# -x-
import traitlets


class Schema(traitlets.Any):
    """any... but validated by a jsonschema.Validator"""

    _validator = None

    def __init__(self, validator, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validator = validator

    def validate(self, obj, value):
        errors = list(self._validator.iter_errors(value))
        if errors:
            raise traitlets.TraitError(
                ("""schema errors:\n""" """\t{}\n""" """for:\n""" """{}""").format(
                    "\n\t".join([error.message for error in errors]), value
                )
            )
        return value

# -x-
class LoadableCallable(traitlets.TraitType):
    """A trait which (maybe) loads a callable."""

    info_text = "a loadable callable"

    def validate(self, obj, value):
        if isinstance(value, str):
            try:
                value = traitlets.import_item(value)
            except Exception:
                self.error(obj, value)

        if callable(value):
            return value
        else:
            self.error(obj, value)
# -x-