// Live conversion and the dark-mode toggle.
// The page already works without this file (the server does the converting).
// This script makes it faster: it asks /api/convert while the user types,
// and handles the tabs, swap, popular and "show all" links without reloading.
(function () {
  "use strict";

  // ---------- Dark mode ----------

  const root = document.documentElement;
  const themeButton = document.getElementById("theme-toggle");
  const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
  const pageColour = { light: "#f3f5fb", dark: "#0e1016" }; // same as --bg in style.css

  function currentTheme() {
    return root.dataset.theme || (systemDark.matches ? "dark" : "light");
  }

  function updateTheme() {
    const next = currentTheme() === "dark" ? "light" : "dark";
    themeButton.setAttribute("aria-label", "Switch to " + next + " mode");
    themeButton.title = "Switch to " + next + " mode";
    // Phones colour their browser bar with this.
    if (root.dataset.theme) {
      document.querySelectorAll('meta[name="theme-color"]').forEach(function (meta) {
        meta.content = pageColour[root.dataset.theme];
      });
    }
  }

  if (themeButton) {
    themeButton.hidden = false;
    updateTheme();
    systemDark.addEventListener("change", updateTheme);
    themeButton.addEventListener("click", function () {
      const next = currentTheme() === "dark" ? "light" : "dark";
      root.dataset.theme = next;
      try {
        localStorage.setItem("theme", next);
      } catch (e) {
        // Storage can be blocked (private mode). The theme still changes for this visit.
      }
      updateTheme();
    });
  }

  // ---------- Converter ----------

  const form = document.getElementById("converter-form");
  if (!form) return; // e.g. the 404 page

  const units = JSON.parse(document.getElementById("units-data").textContent);
  const apiUrl = form.dataset.api;
  const el = {
    category: document.getElementById("category"),
    all: document.getElementById("all"),
    value: document.getElementById("value"),
    sign: document.getElementById("sign"),
    clear: document.getElementById("clear"),
    from: document.getElementById("from"),
    to: document.getElementById("to"),
    swap: document.getElementById("swap"),
    tabsNav: document.getElementById("tabs"),
    tabs: document.querySelectorAll(".tab"),
    chips: document.getElementById("chips"),
    number: document.getElementById("result-number"),
    symbol: document.getElementById("result-symbol"),
    summary: document.getElementById("result-summary"),
    formula: document.getElementById("result-formula"),
    copy: document.getElementById("copy"),
    copyStatus: document.getElementById("copy-status"),
    toggleAll: document.getElementById("toggle-all"),
    allSection: document.getElementById("all-units"),
    allTitle: document.getElementById("all-units-title"),
    allBody: document.getElementById("all-units-body"),
    categoryError: document.getElementById("category-error"),
  };

  let timer = null;
  let requestCount = 0; // so a slow old answer can't replace a newer one

  function showingAll() {
    return !el.all.disabled;
  }

  function currentQuery(changes) {
    const query = new URLSearchParams({
      category: el.category.value,
      value: el.value.value,
      from: el.from.value,
      to: el.to.value,
    });
    if (showingAll()) query.set("all", "1");
    Object.entries(changes || {}).forEach(function (pair) { query.set(pair[0], pair[1]); });
    return query.toString();
  }

  function fillUnits(category, fromKey, toKey) {
    [[el.from, fromKey], [el.to, toKey]].forEach(function (pair) {
      const select = pair[0];
      select.replaceChildren();
      units[category].units.forEach(function (unit) {
        // unit is [key, label, symbol]
        select.add(new Option(unit[1] + " (" + unit[2] + ")", unit[0], false, unit[0] === pair[1]));
      });
    });
  }

  // ---------- Popular chips ----------

  function fillChips(category) {
    el.chips.replaceChildren();
    units[category].popular.forEach(function (pair) {
      const link = document.createElement("a");
      link.className = "chip";
      link.href = "?" + currentQuery({ category: category, from: pair.from, to: pair.to });
      link.dataset.from = pair.from;
      link.dataset.to = pair.to;
      link.textContent = pair.label;
      const item = document.createElement("li");
      item.append(link);
      el.chips.append(item);
    });
    markActiveChip();
  }

  function markActiveChip() {
    el.chips.querySelectorAll(".chip").forEach(function (chip) {
      if (chip.dataset.from === el.from.value && chip.dataset.to === el.to.value) {
        chip.setAttribute("aria-current", "true");
      } else {
        chip.removeAttribute("aria-current");
      }
    });
  }

  // ---------- Value box buttons (± and ×) ----------

  function updateValueButtons() {
    el.sign.hidden = !units[el.category.value].allowNegative;
    el.clear.hidden = el.value.value === "";
  }

  // ---------- Showing the answer ----------

  function setError(field, message) {
    const box = document.getElementById(field + "-error");
    if (box) box.textContent = message || "";
    if (field === "value") {
      if (message) el.value.setAttribute("aria-invalid", "true");
      else el.value.removeAttribute("aria-invalid");
    }
  }

  function clearAnswer(message) {
    el.number.textContent = "—";
    el.symbol.textContent = "";
    el.summary.textContent = message;
    el.formula.textContent = "";
    el.copy.disabled = true;
    el.allTitle.textContent = "Your value in every unit";
    showTable([]);
  }

  function showResult(data) {
    ["value", "from", "to"].forEach(function (field) { setError(field, ""); });
    if (el.categoryError) el.categoryError.remove();
    el.number.textContent = data.formatted;
    el.symbol.textContent = data.symbol;
    el.summary.textContent = data.summary;
    el.formula.textContent = data.formula;
    el.copy.disabled = false;
    el.allTitle.textContent = data.input + " in every unit";
    showTable(data.all || []);
  }

  function showErrors(errors) {
    ["value", "from", "to"].forEach(function (field) { setError(field, errors[field]); });
    // The summary is the live region, so screen readers hear the problem.
    clearAnswer(errors.value || errors.from || errors.to || errors.category || "Please check the input.");
  }

  // Nothing typed yet (or only "-" or "."): a calm hint, not a red error.
  function showWaiting() {
    ["value", "from", "to"].forEach(function (field) { setError(field, ""); });
    clearAnswer("Type a number to convert.");
  }

  function showTable(rows) {
    el.allBody.replaceChildren();
    rows.forEach(function (row) {
      const tr = document.createElement("tr");
      if (row.unit === el.from.value) tr.className = "is-from";
      else if (row.unit === el.to.value) tr.className = "is-to";

      const name = document.createElement("td");
      name.textContent = row.label;
      const amount = document.createElement("td");
      amount.className = "num";
      const symbol = document.createElement("span");
      symbol.className = "sym";
      symbol.textContent = row.symbol;
      amount.append(row.formatted + " ", symbol);

      tr.append(name, amount);
      el.allBody.append(tr);
    });
  }

  function convertNow() {
    clearTimeout(timer);
    updateValueButtons();
    markActiveChip();
    const query = currentQuery();
    // Keep the address bar in step, so the page can be bookmarked or shared.
    history.replaceState(null, "", "?" + query);

    const thisRequest = ++requestCount;
    if (/^[+-]?\.?$/.test(el.value.value.trim())) {
      showWaiting();
      return;
    }
    fetch(apiUrl + "?" + query, { headers: { Accept: "application/json" } })
      .then(function (response) {
        return response.json().then(function (body) {
          return { ok: response.ok, body: body };
        });
      })
      .then(function (answer) {
        if (thisRequest !== requestCount) return;
        if (answer.ok) showResult(answer.body);
        else showErrors(answer.body.errors || {});
      })
      .catch(function () {
        if (thisRequest !== requestCount) return;
        el.summary.textContent = "Can't reach the server. Is the app still running?";
      });
  }

  function convertSoon() {
    clearTimeout(timer);
    updateValueButtons();
    timer = setTimeout(convertNow, 250); // wait until the user stops typing
  }

  // ---------- Events ----------

  // Typing updates the answer. Enter converts right away.
  el.value.addEventListener("input", convertSoon);
  el.from.addEventListener("change", convertNow);
  el.to.addEventListener("change", convertNow);
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    convertNow();
  });

  el.tabs.forEach(function (tab) {
    tab.addEventListener("click", function (event) {
      event.preventDefault();
      const category = tab.dataset.category;
      el.tabs.forEach(function (other) { other.removeAttribute("aria-current"); });
      tab.setAttribute("aria-current", "page");
      el.category.value = category;
      fillUnits(category, units[category].defaultFrom, units[category].defaultTo);
      fillChips(category);
      convertNow();
    });
  });

  el.chips.addEventListener("click", function (event) {
    const chip = event.target.closest(".chip");
    if (!chip) return;
    event.preventDefault();
    el.from.value = chip.dataset.from;
    el.to.value = chip.dataset.to;
    convertNow();
  });

  el.swap.addEventListener("click", function (event) {
    event.preventDefault();
    const from = el.from.value;
    el.from.value = el.to.value;
    el.to.value = from;
    convertNow();
  });

  // ± puts a minus in front of the number, or takes it away.
  // Phone number keypads often have no minus key.
  el.sign.addEventListener("click", function () {
    const text = el.value.value.trim();
    if (text.startsWith("-")) el.value.value = text.slice(1);
    else if (text.startsWith("+")) el.value.value = "-" + text.slice(1);
    else el.value.value = "-" + text;
    convertNow();
  });

  function clearValue() {
    el.value.value = "";
    convertNow();
    el.value.focus();
  }
  el.clear.addEventListener("click", clearValue);

  // Keyboard: "/" jumps to the number box, Esc clears it.
  document.addEventListener("keydown", function (event) {
    const typing = /^(INPUT|SELECT|TEXTAREA)$/.test(event.target.tagName);
    if (event.key === "/" && !typing && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      el.value.focus();
      el.value.select();
    }
  });
  el.value.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && el.value.value !== "") {
      event.preventDefault();
      clearValue();
    }
  });

  el.toggleAll.addEventListener("click", function (event) {
    event.preventDefault();
    const show = !showingAll();
    el.all.disabled = !show;
    el.allSection.hidden = !show;
    el.toggleAll.setAttribute("aria-expanded", String(show));
    el.toggleAll.textContent = show ? "Hide all units" : "Show all units";
    convertNow();
  });

  el.copy.hidden = false;
  el.copy.addEventListener("click", function () {
    const text = (el.number.textContent + " " + el.symbol.textContent).trim();
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(function () {
      el.copy.textContent = "Copied!";
      el.copyStatus.textContent = "Copied " + text; // read out by screen readers
      setTimeout(function () {
        el.copy.textContent = "Copy";
        el.copyStatus.textContent = "";
      }, 1500);
    });
  });

  // ---------- Start ----------

  updateValueButtons();
  // On phones the tabs scroll sideways: show the chosen one.
  const activeTab = el.tabsNav.querySelector('[aria-current="page"]');
  if (activeTab && el.tabsNav.scrollWidth > el.tabsNav.clientWidth) {
    el.tabsNav.scrollLeft = activeTab.offsetLeft - (el.tabsNav.clientWidth - activeTab.offsetWidth) / 2;
  }
})();
