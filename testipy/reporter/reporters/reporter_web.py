#!/usr/bin/env python3
import webbrowser
import html
import base64
import os

from typing import List, Dict
from threading import Thread
from flask import Flask, render_template, copy_current_request_context, request
from flask_socketio import SocketIO, emit, disconnect

from testipy.configs import enums_data
from testipy.lib_modules.common_methods import Timer, sleep, format_duration, prettify
from testipy.lib_modules.start_arguments import StartArguments
from testipy.reporter.report_manager import ReportManager, ReportBase

from engineio.payload import Payload
Payload.max_decode_packets = 100


WAIT_FOR_FIRST_CLIENT = True
DEBUG_MODE_SOCKET_IO = False
PORT = 9204
TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "templates")
STATUS_TO_CLASS = {
    enums_data.STATE_PASSED: "passed",
    enums_data.STATE_SKIPPED: "skipped",
    enums_data.STATE_FAILED: "failed",
    enums_data.STATE_FAILED_KNOWN_BUG: "failed_bug"
}

clients_connected = []
cached_content: Dict[str, List[Dict]] = dict()
response = None

app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_url_path="/templates", static_folder=TEMPLATE_FOLDER)
app.use_reloader = False
app.config["SECRET_KEY"] = "dGVzdGlweSBzZWNyZXQgZm9yIHdlYnNvY2tldHM="
socket_io = SocketIO(app, async_mode=None, engineio_logger=DEBUG_MODE_SOCKET_IO)


def escaped_text(text):
    return html.escape(str(text)).replace("\n", "<br>").replace(" ", "&nbsp;")


def get_image_from_attachment(attachment: Dict) -> str:
    if isinstance(attachment, dict) and attachment.get("mime", "").startswith("image/"):
        img_b64 = base64.b64encode(attachment["data"]).decode("utf-8")
        return f"<div> <p>{attachment['name']}</p> <img src='data:{attachment['mime']};base64,{img_b64}'/> </div>"
    return ""


def _run_flask_in_thread():
    socket_io.run(app, host="0.0.0.0", port=PORT, debug=False, log_output=DEBUG_MODE_SOCKET_IO, allow_unsafe_werkzeug=True)


def _send_cached_content():
    for event, data_list in cached_content.items():
        for data in data_list:
            emit(event, data)


def _push_to_cache(event, data):
    if event not in cached_content:
        cached_content[event] = list()
    cached_content[event].append(data)


def _delete_from_cache(event):
    if event in cached_content:
        del cached_content[event]


def _callback_response(resp):
    global response
    response = resp


class ServerSocketIO:

    def __init__(self, app, socket_io, namespace: str):
        self.setup(app, socket_io, namespace)

    def setup(self, app, socket_io, namespace: str):
        @app.route('/')
        def index():
            return render_template('webreport.html', async_mode=socket_io.async_mode)

        @socket_io.on('my_ping', namespace=namespace)
        def ping_pong():
            emit('my_pong')

        @socket_io.on('connect', namespace=namespace)
        def new_client_connect():
            global WAIT_FOR_FIRST_CLIENT

            _client_connected()
            _send_cached_content()
            WAIT_FOR_FIRST_CLIENT = False

        @socket_io.on('disconnect_request', namespace=namespace)
        def disconnect_request():
            @copy_current_request_context
            def can_disconnect():
                _client_disconnected()
                disconnect()

            # for this emit we use a callback function
            # when the callback function is invoked we know that the message has been received and it is safe to disconnect
            emit('s2c', "Server Disconnected!", callback=can_disconnect)


class ReporterWeb(ReportBase):

    def __init__(self, rm: ReportManager, sa: StartArguments):
        super().__init__(self.__class__.__name__)

        # save ReportManager
        self.rm = rm

        # get running parameters
        _push_to_cache("rm_params", {k: str(v) for k, v in sa.as_dict().items() if k not in ["results_folder_base", "foldername_runtime", "namespace"]})

        # setup socket_io
        self.socket_io = socket_io
        self.namespace = sa.namespace
        ServerSocketIO(app, socket_io, self.namespace)

        Thread(target=_run_flask_in_thread).start()

    def save_file(self, current_test, data, filename):
        pass

    def copy_file(self, current_test, orig_filename, dest_filename, data):
        pass

    def _format_info(self, current_test):
        mb = self.get_report_manager_base()  # get manager base

        str_res = "<br><strong>" + current_test.get_comment().replace("\n", "<br>") + "</strong><br>"
        str_res += f"meid({current_test.get_method_id()}) - test_id({current_test.get_test_id()}) - {mb.get_full_name(current_test, True)} - {current_test.get_usecase()} <strong>{current_test.get_counters().get_last_state()}</strong> - {current_test.get_counters().get_last_reason_of_state()}<br>"
        str_res += f"{current_test.get_counters().get_begin_time()} - {current_test.get_counters().get_end_time()} took {format_duration(current_test.get_duration())}"

        # add test info log
        for ts, current_time, level, info, attachment in current_test.get_info():
            data = f"<p>{escaped_text(info)}</p>{get_image_from_attachment(attachment)}"
            str_res += f"<hr><strong>{current_time} {level}</strong><br>{data}"

        # add test steps
        tc = current_test.get_test_step_counters()
        if len(tc.get_timed_laps()) > 0:
            str_res += "<hr>" + escaped_text(current_test.get_test_step_counters_tabulate()).replace("\n", "<br>")
            str_res += "<hr>Steps Summary: " + escaped_text(str(tc.summary()))
        else:
            str_res += "<hr>Test Summary: " + escaped_text(str(current_test.get_counters().summary(verbose=False)))

        return str_res

    def __startup__(self, selected_tests):
        try:
            webbrowser.open(f"http://127.0.0.1:{PORT}/?namespace={self.namespace}", new=2)
        except:
            pass
        _push_to_cache("rm_selected_tests", {"data": selected_tests["data"]})

    def __teardown__(self, end_state):
        global WAIT_FOR_FIRST_CLIENT

        mb = self.get_report_manager_base()  # get manager base
        msg = {"global_duration_value": "Ended after " + format_duration(mb.get_reporter_counter().get_timed_total_elapsed())}

        if mb.get_reporter_duration():
            msg["global_duration_value"] = "Ended within " + format_duration(mb.get_reporter_duration())

        self.notify_clients('teardown', msg)

        if WAIT_FOR_FIRST_CLIENT:
            # wait 5 sec for a client to connect - so it won't lose all results
            t = Timer(5)
            while WAIT_FOR_FIRST_CLIENT and not t.is_timer_over():
                sleep(1)
        else:
            # if client is connected give 2 sec to sync last results
            Timer(1).sleep_until_over()

        try:
            socket_io.stop()
        except Exception as e:
            self.rm._execution_log("WARNING", f"ReporterWeb - Failed to stop socket_io {e}")

    def startPackage(self, package_name):
        mb = self.get_report_manager_base()  # get manager base
        _delete_from_cache("start_suite")
        _delete_from_cache("start_test")
        self.notify_clients("start_package", {"name": package_name, "ncycle": mb.get_package_cycle_number()})

    def endPackage(self):
        pass

    def startSuite(self, suite_name, attr=None):
        mb = self.get_report_manager_base()  # get manager base
        _delete_from_cache("start_test")
        self.notify_clients("start_suite", {"name": suite_name, "ncycle": mb.get_suite_cycle_number()})

    def endSuite(self):
        pass

    def startTest(self, attr: Dict, test_name: str = "", usecase: str = "", description: str = ""):
        mb = self.get_report_manager_base()  # get manager base
        current_test = mb.get_current_test()
        test_details = {"name": current_test.get_name(),
                        "ncycle": current_test.get_cycle(),
                        "usecase": current_test.get_usecase(),
                        "method_id": current_test.get_method_id(),
                        "test_id": current_test.get_test_id(),
                        "comment": current_test.get_comment()}
        _delete_from_cache("start_test")
        self.notify_clients("start_test", test_details)

        self.testInfo(current_test, f"Test details:\n{prettify(current_test.get_attributes())}", "DEBUG")


    def testInfo(self, current_test, info, level, attachment=None):
        data = f"<p>{escaped_text(info)}</p>{get_image_from_attachment(attachment)}"
        msg = {"test_id": current_test.get_test_id(), "data": data}
        self.notify_clients("test_info", msg)

    def testStep(self, current_test, state: str, reason_of_state: str = "", description: str = "", take_screenshot: bool = False, qty: int = 1, exc_value: BaseException = None):
        self.showStatus(f"{state} || {reason_of_state} || {description}")

    def testSkipped(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_SKIPPED, reason_of_state, exc_value)

    def testPassed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_PASSED, reason_of_state, exc_value)

    def testFailed(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_FAILED, reason_of_state, exc_value)

    def testFailedKnownBug(self, current_test, reason_of_state="", exc_value: BaseException = None):
        self._endTest(current_test, enums_data.STATE_FAILED_KNOWN_BUG, reason_of_state, exc_value)

    def showStatus(self, message: str):
        self.notify_clients('show_status', message, save_to_cache=False)

    def showAlertMessage(self, message: str):
        self.notify_clients('show_alert_message', message, save_to_cache=False)

    def inputPromptMessage(self, message: str, default_value: str = ""):
        global response; response = None
        timer = Timer(25)

        self.notify_clients('input_prompt_message', {"message": message, "default_value": default_value}, save_to_cache=False, callback=_callback_response)
        while response is None and timer.is_timer_valid():
            timer.sleep_for_if_not_over(2)

        return response

    def _endTest(self, current_test, ending_state, end_reason, exc_value: BaseException = None):
        mb = self.get_report_manager_base()  # get manager base
        package_name = mb.get_package_name()
        suite_name = mb.get_suite_name()
        method_id = current_test.get_method_id()
        test_id = current_test.get_test_id()
        test_name = current_test.get_name()
        usecase = current_test.get_usecase()
        duration = current_test.get_duration()
        info = self._format_info(current_test)
        global_duration_value = format_duration(mb.get_reporter_counter().get_timed_total_elapsed())

        data = {"status": ending_state,
                "method_id": method_id,
                "test_id": test_id,
                "log_output": info,
                "data": (method_id, package_name, suite_name, test_name, test_id, usecase, ending_state, f"{duration:.3f} s", end_reason),
                "global_duration_value": global_duration_value,
                "status_class": STATUS_TO_CLASS.get(ending_state)}
        self.notify_clients('end_test', data)

    def notify_clients(self, event, msg, save_to_cache: bool = True, callback = None):
        if save_to_cache:
            _push_to_cache(event, msg)

        for client_sid in _get_clients_connected():
            self.socket_io.emit(event, msg, room=client_sid, include_self=True, namespace=self.namespace, callback=callback)
            if DEBUG_MODE_SOCKET_IO:
                print(f"--> Notify {event} - {client_sid}")


def _client_connected():
    if DEBUG_MODE_SOCKET_IO:
        print(f"--> connected {request.sid}")
    clients_connected.append(request.sid)


def _client_disconnected():
    if DEBUG_MODE_SOCKET_IO:
        print(f"--> disconnected {request.sid}")
    clients_connected.remove(request.sid)


def _get_clients_connected():
    return clients_connected
