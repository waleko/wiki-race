let WIKI_API_ENDPOINT;

// ===== Example rounds =====
const exampleRounds = [
  ['Milk', 'Mozzarella'],
  ['Albert Einstein', 'International Space Station'],
  ['Potato', 'Pizza'],
  ['Burger King', 'Barack Obama'],
  ['Scientology', 'Berlin Wall'],
  ['Cat', 'New York City'],
  ['Poland', 'Brisbane'],
  ['Diplomacy', 'Video game industry'],
  ['French language', 'Elizabeth II']
]

let suggestedOrigin, suggestedTarget;

function setRandomExampleRound() {
  const item = exampleRounds[Math.floor(Math.random() * exampleRounds.length)];
  suggestedOrigin = item[0];
  suggestedTarget = item[1];
  $("#suggested-route").text("from " + suggestedOrigin + " to " + suggestedTarget);
}

function useSuggestedRound() {
  $("#myorigin").typeahead("val", suggestedOrigin);
  $("#mytarget").typeahead("val", suggestedTarget);
}

// ===== Clock =====
let seconds = 0;

function secondsToText(seconds) {
  return (
    Math.floor(seconds / 60) +
    ":" +
    (seconds % 60).toLocaleString("en-US", {
      minimumIntegerDigits: 2,
      useGrouping: false,
    })
  );
}

setInterval(function () {
  if (seconds > 0) {
    seconds--;
  }
  $("#text-clock").text(secondsToText(seconds));
  // TODO: colors
}, 1000);

// ===== UI =====

const star_icon = ' <i class="bi bi-star-fill"></i>';

function updateLeaderboards(leaderboards) {
  $("#leaderboard-table").empty();
  leaderboards.forEach((record) => {
    record.name;
    let name = record.name;
    let points = escape(record.points) + " points";

    let name_cell = $("<td></td>").text(name);
    if (record.is_admin) {
      name_cell.append(star_icon);
    }
    let row = $("<tr></tr>")
      .append(name_cell)
      .append($("<td></td>").text(points));
    $("#leaderboard-table").append(row);
  });
}

function setSolution(solution) {
  let text;
  if (solution === null) {
    text = "We could not find a solution :(";
  } else {
    text = solution.join(" -> ");
  }
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
  setRandomExampleRound();
  if (is_admin) {
    $("#button-waiting").hide();
  } else {
    $("#host-panel").hide();
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

  $("#modal-title").text("Game in progress...");
  hideModal();
  $("#header-solution").hide();
  if (is_admin) {
    $("#button-new-round-spinner").hide();
    $("#button-finish-early").show();
    $("#host-panel").hide();
  } else {
    $("#button-waiting").text("Waiting for game to finish...");
  }
  $("#myorigin").typeahead("val", "");
  $("#mytarget").typeahead("val", "");
}

let solution, leaderboards;

function roundFinished(data) {
  solution = data["solution"];
  leaderboards = data["leaderboards"];
  seconds = 0;

  if (is_admin) {
    setRandomExampleRound();
    $("#button-finish-early").hide();
    $("#button-new-round").prop("disabled", false);
    $("#host-panel").show();
  } else {
    $("#button-waiting").text("Waiting for host to start...");
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
  if (actionName === "set_wiki_endpoint") {
    WIKI_API_ENDPOINT = data["url"];
    console.info(`Now using this wiki endpoint: ${WIKI_API_ENDPOINT}`);
    return;
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
  sendAction("new_round", {
    origin: $("#myorigin").val(),
    target: $("#mytarget").val(),
  });
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

// ===== Typeahead =====
$(document).ready(function () {
  $(".typeahead").typeahead(
    {
      hint: true,
      highlight: true,
      minLength: 1,
    },
    {
      async: true,
      source: function (qry, _, async) {
        $.ajax(
          `${WIKI_API_ENDPOINT}?` +
          $.param({
            action: "opensearch",
            search: qry,
            namespace: 0,
            redirects: "resolve",
            origin: "*",
          }),
          {}
        ).done(function (res) {
          async(res[1]);
        });
      },
      limit: 5,
    }
  );
});

function setRandomOriginAndTitle() {
  $.ajax(
    `${WIKI_API_ENDPOINT}?` +
    $.param({
      action: "query",
      list: "random",
      rnnamespace: 0,
      rnlimit: 2,
      format: "json",
      origin: "*",
    }),
    {}
  ).done(function (res) {
    $("#myorigin").typeahead("val", res.query.random[0].title);
    $("#mytarget").typeahead("val", res.query.random[1].title);
  });
}

async function checkPageExists(page) {
  const resp = await $.ajax(
    `${WIKI_API_ENDPOINT}?` +
    $.param({
      action: "query",
      prop: "info",
      titles: page,
      format: "json",
      origin: "*",
    })
  ).done(function (res) {
  });
  return resp.query.pages["-1"] === undefined;
}

async function checkExistOriginAndTarget() {
  if (!(await checkPageExists($("#myorigin").val()))) {
    alert("Please select origin to be a correct wiki page title");
    return false;
  }
  if (!(await checkPageExists($("#mytarget").val()))) {
    alert("Please select origin to be a correct wiki page title");
    return false;
  }
  return true;
}

// ===== Form =====
jQuery.validator.addMethod(
  "origin_target_different",
  function (_, element) {
    return (
      this.optional(element) || $("#myorigin").val() !== $("#mytarget").val()
    );
  },
  "Origin and target pages must be different!"
);

$("#new-round-form")
  .submit(function (e) {
    e.preventDefault();
    checkExistOriginAndTarget().then(function (res) {
      if (res) requestNewRound();
    });
  })
  .validate({
    rules: {
      origin: {
        required: true,
        origin_target_different: true,
      },
      target: {
        required: true,
        origin_target_different: true,
      },
    },
  });

function copyInviteLink() {
  navigator.clipboard.writeText(conf["GAME_URL"]);
}