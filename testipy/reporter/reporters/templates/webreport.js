let test_log = {};
let socket;
let id_window_polling;


$(document).ready(function() {
    const params = new Proxy(new URLSearchParams(window.location.search), {
        get: (searchParams, prop) => searchParams.get(prop),
    });
    const namespace = params.namespace; //'/testipytests';
    const rtt_polling_interval_ms = 1000;
    const number_of_samples = 30 * 1000 / rtt_polling_interval_ms;  // 30 sec of buffer

    // Connect to the Socket.IO server.
    // The connection URL has the following format, relative to the current page:
    //     http[s]://<domain>:<port>[/<namespace>]
    socket = io(namespace);

    // Event handler for new connections.
    socket.on('connect', function() {
        $('#ping-pong').text("connected");
        clear_all_tables();
    });
    socket.on('connect_error', function() { $('#ping-pong').text("connecting..."); });

    // Event handler for server disconnect request.
    socket.on('s2c', function(msg, cb) {
        console.log(msg);
        if (cb) { cb(); }
        $('#ping-pong').text(msg);
        socket.close();
    });

    //WebReporter Methods
    socket.on('start_package', function (msg) {
        rt_package(msg.name, msg.ncycle);
        rt_suite();
        rt_test();
    });
    socket.on('start_suite', function (msg) {
        rt_suite(msg.name, msg.ncycle);
        rt_test();
    });
    socket.on('start_test', function (msg) {
        let meid = msg.method_id.toString();
        change_row_class_method_test_running(meid, "method_running");
        rt_test(msg.name, msg.ncycle, msg.usecase, msg.comment, msg.method_id, msg.test_id);
    });
    socket.on('end_test', function (msg) {
        let ended_tests_table = document.getElementById('ended_tests').getElementsByTagName('tbody')[0];
        let row = ended_tests_table.insertRow();
        let status = msg.status.toLowerCase();
        let meid = msg.method_id.toString();
        let tid = msg.test_id;
        let global_duration_value = msg.global_duration_value;
        let status_class = msg.status_class.toLowerCase();
        test_log[msg.test_id] = msg.log_output;

        for(let key in msg.data) {
            let cell = row.insertCell();
            if (key == 3)
                cell.innerHTML = '<a href="#test_log_output" onclick="show_log(' + tid + ');">' + msg.data[key] + "</a>";
            else
                cell.innerText = msg.data[key];
            cell.className = status_class;
        }
        change_row_class_method_test_running(meid, "method_ended");
        update_totals_counters(status_class);
        update_global_duration(global_duration_value);
    });
    socket.on('test_info', function (msg) {
        $('#test_output').append(msg.data).append("<hr>");
    });
    socket.on('show_status', function (message) {
        show_status(message);
    });
    socket.on('show_alert_message', function (message) {
        window.alert(message);
        show_status(message);
    });
    socket.on('input_prompt_message', function (msg, cb) {
        let response = window.prompt(msg.message, msg.default_value);
        if (cb)
            cb(response);
        show_status(msg.message + " -> " + response);
    });


    // Event handler for server sent parameters.
    socket.on('rm_params', function(msg, cb) {
        let rm_params_table = document.getElementById('rm_params').getElementsByTagName('tbody')[0];
        for(let key in msg) {
            let row = rm_params_table.insertRow();
            let cell_key = row.insertCell(0);
            let cell_val = row.insertCell(1);
            cell_val.style = "word-wrap: break-word; max-width: 400px;";
            cell_key.innerText = key;
            cell_key.className = "label"
            cell_val.innerText = msg[key];
            cell_val.className = "label_value";
        }

        if (cb)
            cb();
    });

    // Event handler for server sent parameters.
    socket.on('rm_selected_tests', function(msg) {
        let rm_table = document.getElementById('rm_selected_tests').getElementsByTagName('tbody')[0];
        for (let i = 0; i < msg.data.length; i++) {
            let row = rm_table.insertRow();
            let selected_tests = msg.data[i];
            for(let j in selected_tests) {
                let cell_val = row.insertCell();
                cell_val.innerText = selected_tests[j];
                cell_val.className = "label_value";
            }
        }
    });

    socket.on('teardown', function (msg) {
        let global_duration_value = msg.global_duration_value;
        update_global_duration(global_duration_value);
        disconnect_client();
    });


    /////////// Handlers for the "ping-pong" messages.
    // Interval function that tests message latency by sending a "ping" message.
    // The server then responds with a "pong" message and the round trip time is measured.
    let ping_pong_rtt = [];
    let start_time;
    id_window_polling = window.setInterval(function() {
        start_time = (new Date).getTime();
        socket.emit('my_ping');
    }, rtt_polling_interval_ms);

    // When the pong is received, the time from the ping is stored, and the last 30 samples (1 min) for average
    socket.on('my_pong', function() {
        const latency = (new Date).getTime() - start_time;

        // keep last samples
        ping_pong_rtt.push(latency);
        ping_pong_rtt = ping_pong_rtt.slice(-number_of_samples);

        const sum = ping_pong_rtt.reduce((acc, val) => acc + val, 0);
        const avg = (Math.round(10 * sum / ping_pong_rtt.length) / 10);
        $('#ping-pong').text(latency + "ms / " + avg + "ms");
    });

});



function rt_package(package_name="", pcycle="", ) {
    $('#package_name').text(package_name);
    $('#package_cycle').text(pcycle);
}
function rt_suite(suite_name="", scycle="") {
    $('#suite_name').text(suite_name);
    $('#suite_cycle').text(scycle);
}
function rt_test(test_name="", tcycle="", usecase="", comment="", meid="0", tid="0") {
    $('#test_name').text(test_name);
    $('#test_cycle').text(tcycle);
    $('#test_usecase').text(usecase);
    $('#meid_tid').text(meid + " / " + tid);
    $('#test_comment').text(comment);
    $('#test_output').text("");
}

function show_log(tid) {
    $('#test_log').text("").append(test_log[tid]);
    return false;
}

function show_status(message) {
    $('#status_message').text(message);
}


function change_row_class_method_test_running(meid, class_name="method_running") {
    const table = document.getElementById("rm_selected_tests");
    for (let i = 0, row; row = table.rows[i]; i++)
        if (row.cells[0].innerText == meid)
            for (let j = 0, col; col = row.cells[j]; j++)
                col.className = class_name;
                return true;
}

function update_totals_counters(status) {
    let span_obj = $("#total_" + status);
    let current_value = parseInt(span_obj.text());
    span_obj.text(current_value + 1);

    span_obj = $("#total");
    current_value = parseInt(span_obj.text());
    span_obj.text(current_value + 1);
}

function update_global_duration(global_duration_value) {
    let span_obj = $("#global_duration_value");
    span_obj.text(global_duration_value);
}

function clear_all_tables() {
    // clear Parameters
    $("#rm_params > tbody").empty();

    // clear global counters
    $("#total_passed").text(0);
    $("#total_failed").text(0);
    $("#total_failed_bug").text(0);
    $("#total_skipped").text(0);
    $("#total").text(0);

    // clear Selected tests
    $("#rm_selected_tests > tbody").empty();

    // clear Ended tests
    $("#ended_tests > tbody").empty();
}

function disconnect_client() {
    try {
        window.clearInterval(id_window_polling);
        // will be closed by the s2c call
        socket.emit('disconnect_request');
        document.getElementById("btn_disconnect").disabled = true;
        $('#ping-pong').text("client disconnected");
        console.log("client disconnected " + id_window_polling);
    } catch (err) {
        console.log(err);
    }
}