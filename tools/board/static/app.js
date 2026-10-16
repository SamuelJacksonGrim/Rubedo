/* Polls the run folder. Curves and captions come from schema.json, not from here. */
(function () {
  "use strict";

  var runId = null;
  var rows = [];
  var schema = null;
  var pending = {};
  var seenToggles = 0;
  var drawing = null;

  function $(id) { return document.getElementById(id); }

  function getJSON(url) {
    return fetch(url, { cache: "no-store" }).then(function (resp) {
      if (!resp.ok) throw new Error(resp.status + " " + url);
      return resp.json();
    });
  }

  function fmt(value) {
    if (value === null || value === undefined || value === "") return "—";
    if (typeof value === "number") {
      if (!isFinite(value)) return "—";
      var abs = Math.abs(value);
      if (abs !== 0 && (abs < 0.01 || abs >= 1000)) return value.toExponential(2);
      return String(Math.round(value * 1000) / 1000);
    }
    return String(value);
  }

  function latestNumber(key) {
    for (var i = rows.length - 1; i >= 0; i--) {
      var value = rows[i][key];
      if (typeof value === "number" && isFinite(value)) return value;
    }
    return null;
  }

  function pickRun() {
    return getJSON("/api/runs").then(function (runs) {
      var sel = $("run");
      var prev = sel.value;
      sel.innerHTML = "";
      if (!runs.length) {
        runId = null;
        $("empty").hidden = false;
        $("bar").hidden = true;
        $("curves").hidden = true;
        $("mixes").hidden = true;
        $("panel").hidden = true;
        $("log").hidden = true;
        return;
      }
      $("empty").hidden = true;
      $("bar").hidden = false;
      runs.forEach(function (run) {
        var opt = document.createElement("option");
        opt.value = run.run_id;
        opt.textContent = run.run_id;
        sel.appendChild(opt);
      });
      if (prev && runs.some(function (run) { return run.run_id === prev; })) sel.value = prev;
      if (sel.value !== runId) {
        runId = sel.value;
        rows = [];
        schema = null;
        pending = {};
        seenToggles = 0;
      }
    });
  }

  function loadMetrics() {
    if (!rows.length) {
      return getJSON("/api/run/" + encodeURIComponent(runId) + "/metrics").then(function (fresh) {
        rows = fresh;
      });
    }
    var after = rows[rows.length - 1].step || 0;
    return getJSON("/api/run/" + encodeURIComponent(runId) + "/metrics?after=" + after).then(function (fresh) {
      if (fresh.length) rows = rows.concat(fresh).slice(-400);
    });
  }

  function tick() {
    pickRun().then(function () {
      if (!runId) return null;
      var jobs = [loadMetrics(), getJSON("/api/run/" + encodeURIComponent(runId) + "/status"),
        getJSON("/api/run/" + encodeURIComponent(runId) + "/toggles")];
      if (!schema) jobs.push(getJSON("/api/run/" + encodeURIComponent(runId) + "/schema"));
      return Promise.all(jobs);
    }).then(function (packed) {
      if (!packed) return;
      var status = packed[1];
      var toggles = packed[2];
      if (packed[3]) schema = packed[3];
      $("error").textContent = "";
      render(status || {}, toggles || []);
    }).catch(function (err) {
      $("error").textContent = err && err.message ? err.message : String(err);
    });
  }

  function render(status, toggles) {
    var dot = $("dot");
    dot.className = "dot" + (status.state === "running" || status.state === "booting" ? " run" : " stop");
    var timing = status.timing || {};
    var bits = [
      status.state || "unknown",
      "step " + fmt(status.step),
      status.workload || "",
      status.seed != null ? "seed " + status.seed : "",
      status.threads != null ? status.threads + " thread" + (status.threads === 1 ? "" : "s") : ""
    ].filter(Boolean);
    if (typeof timing.overhead_per_step_ms === "number") {
      bits.push("overhead " + fmt(timing.overhead_per_step_ms) + " ms/step");
    } else if (typeof timing.mean_observe_ms === "number") {
      bits.push("observe " + fmt(timing.mean_observe_ms) + " ms");
    }
    $("meta").textContent = bits.join(" · ");
    $("guards").textContent = status.guards || "";
    $("stop").disabled = status.state === "stopped";

    settle(status.panel || [], toggles);
    drawCurves();
    drawMixes();
    drawLevers(status.panel || []);
    drawLog(toggles);
    seenToggles = toggles.length;
  }

  function settle(panel, toggles) {
    var waiting = false;
    var note = "";
    Object.keys(pending).forEach(function (id) {
      var want = pending[id];
      var row = panel.filter(function (item) { return item.id === id; })[0];
      if (row && row.value === want.value) {
        delete pending[id];
        return;
      }
      var newer = toggles.slice(want.at).filter(function (item) { return item.id === id; });
      if (newer.length && newer[newer.length - 1].applied === false) {
        note = (row ? row.label : id) + " refused: " + (newer[newer.length - 1].reason || "not applied");
        delete pending[id];
        return;
      }
      if (newer.length && newer[newer.length - 1].after === want.value) {
        delete pending[id];
        return;
      }
      waiting = true;
    });
    $("wait").hidden = !waiting;
    if (note) $("error").textContent = note;
  }

  function drawCurves() {
    var host = $("curves");
    host.hidden = false;
    var series = (schema && schema.series) || [];
    host.innerHTML = "";
    series.forEach(function (item) {
      var card = document.createElement("article");
      card.className = "card";
      var value = latestNumber(item.key);
      var extra = "";
      if (item.key === "timescale_ratio" && rows.length) {
        var bound = rows[rows.length - 1].timescale_bound;
        if (value === null && bound) extra = " " + bound;
      }
      card.innerHTML = "<h3>" + escape(item.label) + "<b>" + escape(fmt(value) + extra) + "</b></h3>"
        + "<p class=\"plain\">" + escape(item.plain || "") + "</p>";
      var canvas = document.createElement("canvas");
      canvas.height = 72;
      card.appendChild(canvas);
      host.appendChild(card);
      paint(canvas, item.key);
    });
  }

  function paint(canvas, key) {
    var width = canvas.clientWidth || canvas.parentNode.clientWidth || 280;
    var height = 72;
    var dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.floor(width * dpr));
    canvas.height = Math.floor(height * dpr);
    canvas.style.height = height + "px";
    var ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, width, height);
    var pts = [];
    rows.forEach(function (row, index) {
      var value = row[key];
      if (typeof value === "number" && isFinite(value)) pts.push([index, value]);
    });
    if (!pts.length) return;
    var min = pts[0][1];
    var max = pts[0][1];
    pts.forEach(function (pt) {
      if (pt[1] < min) min = pt[1];
      if (pt[1] > max) max = pt[1];
    });
    if (max === min) { max += 1; min -= 1; }
    var span = rows.length - 1 || 1;
    ctx.strokeStyle = "#8fb9a4";
    ctx.lineWidth = 1.6;
    ctx.beginPath();
    var pen = false;
    rows.forEach(function (row, index) {
      var value = row[key];
      if (typeof value !== "number" || !isFinite(value)) { pen = false; return; }
      var x = (index / span) * (width - 4) + 2;
      var y = height - 4 - ((value - min) / (max - min)) * (height - 8);
      if (!pen) { ctx.moveTo(x, y); pen = true; }
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function drawMixes() {
    var host = $("mixes");
    host.hidden = false;
    host.innerHTML = "";
    var last = rows.length ? rows[rows.length - 1] : null;
    ((schema && schema.mixes) || []).forEach(function (item) {
      var card = document.createElement("article");
      card.className = "mix";
      var obj = last ? (last[item.key] || {}) : {};
      card.innerHTML = "<h3>" + escape(item.label) + "</h3><p class=\"plain\">" + escape(item.plain || "") + "</p>";
      if (item.key === "oslash_by_pathology" && last && last.oslash_attached === false) {
        var off = document.createElement("p");
        off.className = "plain";
        off.textContent = "Not read. The consumer is off, and asking the read would bump symbol usage.";
        card.appendChild(off);
      } else {
        card.appendChild(bars(obj));
      }
      host.appendChild(card);
    });
  }

  function bars(obj) {
    var wrap = document.createElement("div");
    wrap.className = "bars";
    var entries = Object.keys(obj).map(function (key) { return [key, Number(obj[key]) || 0]; });
    var max = 0;
    entries.forEach(function (pair) { if (pair[1] > max) max = pair[1]; });
    if (!max) max = 1;
    entries.forEach(function (pair) {
      var row = document.createElement("div");
      row.className = "bar-row";
      var pct = Math.max(0, Math.min(100, (pair[1] / max) * 100));
      row.innerHTML = "<span>" + escape(pair[0]) + "</span><div class=\"track\"><i style=\"width:" + pct + "%\"></i></div><span>" + escape(fmt(pair[1])) + "</span>";
      wrap.appendChild(row);
    });
    return wrap;
  }

  function drawLevers(panel) {
    $("panel").hidden = false;
    var live = $("levers");
    var frozen = $("readonly");
    live.innerHTML = "";
    frozen.innerHTML = "";
    panel.forEach(function (item) {
      var card = document.createElement("article");
      card.className = "card lever";
      var state = item.value === true ? "ON" : item.value === false ? "OFF" : fmt(item.value);
      card.innerHTML = "<h3>" + escape(item.label) + "<b>" + escape(state) + "</b></h3>"
        + "<p class=\"plain\">" + escape(item.plain || "") + "</p>";
      if (item.note) {
        var note = document.createElement("p");
        note.className = "note";
        note.textContent = item.note;
        card.appendChild(note);
      }
      if (item.writable && typeof item.value === "boolean") {
        var button = document.createElement("button");
        button.type = "button";
        button.className = item.value ? "on" : "off";
        button.textContent = item.value ? "Turn off" : "Turn on";
        if (pending[item.id]) {
          button.disabled = true;
          button.textContent = "Waiting for the step boundary";
        }
        button.addEventListener("click", function () { send(item.id, !item.value); });
        card.appendChild(button);
      }
      (item.writable ? live : frozen).appendChild(card);
    });
  }

  function send(id, value) {
    pending[id] = { value: value, at: seenToggles };
    $("wait").hidden = false;
    fetch("/api/run/" + encodeURIComponent(runId) + "/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id: id, value: value })
    }).then(function (resp) {
      if (!resp.ok) throw new Error("control " + resp.status);
      return tick();
    }).catch(function (err) {
      delete pending[id];
      $("error").textContent = err && err.message ? err.message : String(err);
    });
  }

  function drawLog(toggles) {
    $("log").hidden = false;
    var list = $("toggles");
    list.innerHTML = "";
    toggles.slice(-40).reverse().forEach(function (item) {
      var li = document.createElement("li");
      var verb = item.applied ? "applied" : "refused";
      li.textContent = "step " + item.step + "  " + item.id + "  "
        + fmt(item.before) + " → " + fmt(item.after) + "  " + verb
        + (item.reason ? "  " + item.reason : "");
      if (!item.applied) li.className = "refused";
      list.appendChild(li);
    });
    if (!toggles.length) {
      var empty = document.createElement("li");
      empty.textContent = "None yet.";
      list.appendChild(empty);
    }
  }

  function escape(text) {
    return String(text).replace(/[&<>"]/g, function (ch) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[ch];
    });
  }

  $("run").addEventListener("change", function () {
    runId = $("run").value;
    rows = [];
    schema = null;
    pending = {};
    seenToggles = 0;
    tick();
  });

  $("stop").addEventListener("click", function () {
    if (!runId) return;
    $("stop").disabled = true;
    fetch("/api/run/" + encodeURIComponent(runId) + "/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ stop: true })
    }).then(function () { return tick(); });
  });

  window.addEventListener("resize", function () {
    if (drawing) cancelAnimationFrame(drawing);
    drawing = requestAnimationFrame(function () { if (schema) drawCurves(); });
  });

  tick();
  setInterval(tick, 1000);
})();
