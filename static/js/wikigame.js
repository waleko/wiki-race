// ===== Clock =====
let seconds = 0;

function secondsToText(seconds) {
  return Math.floor(seconds / 60) + ':' + (seconds % 60).toLocaleString("en-US", {
      minimumIntegerDigits: 2,
      useGrouping: false,
  });
}

setInterval(function () {
  if (seconds > 0) {
    seconds--;
  }
  $("#text-clock").text(secondsToText(seconds));
  // TODO: colors
}, 1000);

// ===== UI =====

function updateLeaderboards(leaderboards) {
  $("#leaderboard-table").empty();
  leaderboards.forEach((record) => {
    let name = escape(record.name); // TODO: fix cyrillic
    if (record.is_admin) {
      // add star
      name +=
        ' <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-star-fill" viewBox="0 0 16 16">\n' +
        '  <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z"/>\n' +
        "</svg>";
    }
    let points = escape(record.points) + " points";
    $("#leaderboard-table").append(
      "<tr><td>" + name + "</td><td>" + points + "</td></tr>"
    );
  });
}

function setSolution(solution) {
  let text = solution.join(" -> ");
  $("#text-solution").text(text);
  $("#header-solution").show();
}

function showModal() {
  $("#modal-1").modal("show");
}

function hideModal() {
  $("#modal-1").modal("hide");
}

function initUI() {
  if (!is_admin) {
    $("#button-new-round")
      .show()
      .text("Waiting for host to start...")
      .prop("disabled", true);
  }
  $("#header-solution").hide();
  $("#button-new-round-spinner").hide();
  $("#button-finish-early").hide();
  setTimeout(showModal, 100);
}

// ===== Handlers =====

let origin, destination;

function newGame(data) {
  origin = data["start_page"];
  destination = data["end_page"];
  $("#origin").text(origin);
  $("#destination").text(destination);

  seconds = data["time_limit"];
  $("#game-iframe")[0].src = "/wiki/" + origin;

  $("#button-new-round").hide();
  if (is_admin) {
    $("#button-new-round-spinner").hide();
    $("#button-finish-early").show();
  }

  $("#modal-title").text("Game in progress...");
  $("#header-solution").hide();
  hideModal();
}

let solution, leaderboards;

function roundFinished(data) {
  solution = data["solution"];
  leaderboards = data["leaderboards"];
  seconds = 0;

  if (is_admin) {
    $("#button-finish-early").hide();
    $("#button-new-round")
      .show()
      .text("Start new round")
      .prop("disabled", false);
  } else {
    $("#button-new-round")
      .show()
      .text("Waiting for host to start...")
      .prop("disabled", true);
  }

  updateLeaderboards(leaderboards);
  setSolution(solution);

  $("#modal-title").text("Round finished...");
  showModal();
}

function forceRedirect(data) {
  $("#game-iframe")[0].src = "/wiki/" + data["page"];
}

function solved() {
  $("#button-new-round")
    .show()
    .text("Waiting for game to finish...")
    .prop("disabled", true);
  $("#modal-title").text("Solved. Well done!");
  showModal();
}

// ===== Websockets =====

let socket;

function parseMessage(actionName, data) {
  console.debug(actionName);
  console.debug(data);

  if (actionName === "new_round") {
    return newGame(data);
  }
  if (actionName === "force_redirect") {
    return forceRedirect(data);
  }
  if (actionName === "round_finished") {
    return roundFinished(data);
  }
  if (actionName === "leaderboard_update") {
    leaderboards = data["leaderboards"];
    return updateLeaderboards(leaderboards);
  }
  if (actionName === "solved") {
    return solved();
  }
  console.warn("Unprocessed: " + actionName);
}

function receiveMessage(event) {
  let msg = JSON.parse(event.data);
  if (msg["error"] !== undefined) {
    console.error(msg["error"]);
    return;
  }
  parseMessage(msg["type"], msg["data"]);
}

function connectWebsocket(url) {
  socket = new WebSocket(url);
  socket.onmessage = receiveMessage;
  socket.onclose = function (_) {
    console.info("Websocket closed!");
  };
  socket.onerror = function (ev) {
    console.error(ev);
  };
}

if (conf["WEBSOCKET_URL"] !== undefined) {
  initUI();

  console.info("Connecting to websocket: " + conf["WEBSOCKET_URL"] + "...");
  connectWebsocket(conf["WEBSOCKET_URL"]);
}

// ===== Internal =====

function sendAction(actionName, data) {
  data["type"] = actionName;
  socket.send(JSON.stringify(data));
}

function requestNewRound() {
  sendAction("new_round", {});
  $("#button-new-round").prop("disabled", true);
  $("#button-new-round-spinner").show();
}

function requestFinishEarly() {
  sendAction("finish_early", {});
}

// ===== Iframe =====

window.onmessage = function (event) {
  let type = event.data["type"];
  if (type === "click") {
    window.scrollTo(0, 0);
  }
  sendAction(type, event.data);
};
