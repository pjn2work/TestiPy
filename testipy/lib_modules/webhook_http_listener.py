#!/usr/bin/env python3

import sys
import threading
import json
import re

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
from typing import Dict, List


HOST = '127.0.0.1'      # Hostname to bind
_listeners = list()     # list with all listeners passed on start()
_servers_list = dict()  # list with all http servers, mapped by port (for later .close())
_verbose = False
last_message_received = dict()


def print_message(message):
    if _verbose:
        print(message, file=sys.stderr)


def _notify_listeners(message_dict):
    for lst in _listeners:
        try:
            lst(message_dict)
        except Exception as ex:
            print_message(f"Failed to call listener. {ex}")


def prettify(json_obj) -> str:
    try:
        if isinstance(json_obj, (dict, list)):
            return json.dumps(json_obj, indent=3)
        return json.dumps(json.loads(json_obj), indent=3)
    except:
        return str(json_obj)


def _demo_listener(message_dict):
    print(prettify(message_dict))


def _save_message_listener(message_dict):
    global last_message_received
    last_message_received = message_dict


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        if _verbose:
            super().log_message(format, *args)

    def _send_formated_response(self, message):
        self.send_response(200)

        if isinstance(message, dict):
            self.send_header('Content-type', "application/json")
            message = json.dumps(message).encode("utf-8")
        else:
            self.send_header('Content-type', 'text/html')
            message = str(message).encode("utf-8")
        self.end_headers()

        self.wfile.write(message)

    # return a dict with all received headers
    def _parse_headers(self) -> Dict[str, str]:
        return {k: v for k, v in self.headers.items()}

    # return a string with path (omitting http://address:port and ?querystring=stuff)
    def _parse_path(self) -> str:
        if "?" in self.path:
            return self.path[:self.path.index("?")]
        return self.path

    # return a dict with all parameters on the querystring
    def _parse_querystring(self) -> Dict[str, str]:
        res = dict()
        if "?" in self.path:
            for kv in self.path[self.path.index("?")+1:].split("&"):
                k, v = kv.split("=")
                res[k] = unquote(v)
        return res

    # used on posts
    def _parse_post_body(self) -> Dict[str, str]:
        resp = dict()

        if 'Content-Length' in self.headers:
            body = self.rfile.read(int(self.headers['Content-Length'])).decode("utf8")

            ct = "multipart/form-data; boundary="
            if self.headers["Content-Type"].startswith(ct):
                boundary = self.headers["Content-Type"][len(ct):]

                for row in body.split(boundary):
                    if row and row != "--" and row != "--\r\n":
                        re_groups = re.search(r'Content-Disposition: form-data; name=\"(.+)\"\r\n\r\n(.+)\r\n--', row)
                        if re_groups:
                            field_name = re_groups.group(1)
                            field_value = re_groups.group(2)
                            resp[field_name] = field_value
            elif self.headers["Content-Type"].startswith("application/x-www-form-urlencoded"):
                for kv in body.split("&"):
                    k, v = kv.split("=")
                    resp[k] = unquote(v)
            else:
                resp["raw"] = body

        return resp

    # dictionary with all http info
    def _get_response_dict(self) -> Dict[str, str]:
        return dict(method=self.command,
                    headers=self._parse_headers(),
                    address=self.address_string(),
                    fullpath=self.path,
                    path=self._parse_path(),
                    querystring=self._parse_querystring(),
                    body=self._parse_post_body())

    def do_GET(self):
        if self.path != "/favicon.ico":
            message = self._get_response_dict()
            self._send_formated_response(message)
            _notify_listeners(message)

    def do_POST(self):
        message = self._get_response_dict()
        self._send_formated_response(message)
        _notify_listeners(message)


def get_last_message_received() -> Dict:
    return last_message_received


def set_listeners(listeners_list: List, append: bool = False):
    global _listeners

    if not isinstance(listeners_list, List):
        listeners_list = [listeners_list] if listeners_list else []

    if append:
        if _save_message_listener not in _listeners:
            _listeners.append(_save_message_listener)
        _listeners += listeners_list
    else:
        _listeners = [_save_message_listener] + listeners_list


def is_port_open(port: int) -> bool:
    return port in _servers_list


def close_http_port(port: int):
    if port in _servers_list:
        http_server = _servers_list.pop(port)
        try:
            http_server.server_close()
            print_message(f"Closed HTTP Server {http_server.server_port}")
        except:
            print_message(f"Error closing HTTP Server {port}")


def close_all_http_ports():
    for port in dict(_servers_list):
        close_http_port(port)
    _servers_list.clear()
    # unbind takes time (~4sec) for the OS to react


def _open_tcp_port(host: str, port: int):
    if port not in _servers_list:
        httpd = HTTPServer((host, port), SimpleHTTPRequestHandler)
        print_message(f"Running Server http://{host}:{port}")

        # append to list for later closure
        _servers_list[port] = httpd

        httpd.serve_forever()
        httpd.server_close()


def start_http_servers(tcp_ports_list: list, listeners_list: list = None, blocking: bool = False, verbose: bool = False):
    global _verbose
    _verbose = verbose

    if not isinstance(tcp_ports_list, list):
        tcp_ports_list = [tcp_ports_list]

    set_listeners(listeners_list)

    # start threads
    list_of_threads = list()
    for port in tcp_ports_list:
        if port not in _servers_list:
            x = threading.Thread(target=_open_tcp_port, args=(HOST, int(port)), daemon=True)
            list_of_threads.append(x)
            x.start()

    if blocking:
        try:
            for x in list_of_threads:
                x.join()
        except KeyboardInterrupt:
            close_all_http_ports()


if __name__ == "__main__":
    tcp_ports_list = sys.argv[1:] or ["8081"]
    start_http_servers(tcp_ports_list=tcp_ports_list, listeners_list=[_demo_listener], blocking=True, verbose=True)
