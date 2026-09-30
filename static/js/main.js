const form = document.getElementById("finance-form");
const submitBtn = document.getElementById("submit-btn");
const errorBox = document.getElementById("error");
const results = document.getElementById("results");

const icons = {
  rent: "fa-house",
  food: "fa-utensils",
  transport: "fa-bus",
  dining: "fa-burger",
  entertainment: "fa-film",
  utilities: "fa-bolt",
  savings: "fa-piggy-bank",
};

function rupees(n) {
  return "₹" + Number(n).toLocaleString("en-IN", {
    maximumFractionDigits: 0,
  });
}

function showError(msg) {
  errorBox.textContent = msg;
  errorBox.hidden = false;
}

function setLoading(on) {
  submitBtn.disabled = on;
  submitBtn.querySelector(".label").hidden = on;
  submitBtn.querySelector(".spinner").hidden = !on;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  errorBox.hidden = true;

  const income = Number(document.getElementById("income").value);
  const expenses = {};

  form.querySelectorAll("[data-cat]").forEach((input) => {
    const value = Number(input.value);
    if (value > 0) {
      expenses[input.dataset.cat] = value;
    }
  });

  if (!income || income <= 0) {
    return showError("Enter your monthly income.");
  }

  if (Object.keys(expenses).length === 0) {
    return showError("Enter at least one expense.");
  }

  setLoading(true);

  try {
    const res = await fetch("/analyse", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        income,
        expenses,
        goal: document.getElementById("goal").value,
      }),
    });

    const data = await res.json();

    if (!res.ok || !data.success) {
      showError(data.error || "Something went wrong. Try again.");
      return;
    }

    renderResults(data);
  } catch (err) {
    showError("Could not reach the server. Is it running?");
  } finally {
    setLoading(false);
  }
});

function el(tag, className, text) {
  const node = document.createElement(tag);

  if (className) {
    node.className = className;
  }

  if (text !== undefined) {
    node.textContent = text;
  }

  return node;
}

function renderResults(data) {
  const income = data.summary.income;

  // Summary cards
  const summary = document.getElementById("summary");
  summary.innerHTML = "";

  [
    ["Income", rupees(income)],
    ["Spent", rupees(data.summary.total_spent)],
    [
      data.summary.left_over >= 0 ? "Left over" : "Over by",
      rupees(Math.abs(data.summary.left_over)),
    ],
    ["Savings rate", data.summary.savings_rate + "%"],
  ].forEach(([label, value]) => {
    const box = el("div");
    box.append(
      el("b", "", value),
      el("small", "", label)
    );
    summary.append(box);
  });

  // Suggested budget
  const budget = document.getElementById("budget");
  budget.innerHTML = "";

  data.budget.forEach((item) => {
    const percent = Math.round((item.amount / income) * 100);

    const card = el("div", "card");

    const name = el("div", "name");

    const icon = el(
      "i",
      "fa-solid " +
        (icons[String(item.category).toLowerCase()] || "fa-wallet")
    );

    name.append(icon, item.category);

    const bar = el("div", "bar");

    const fill = el("div");
    fill.style.width = Math.min(percent, 100) + "%";

    bar.append(fill);

    card.append(
      name,
      el("div", "amount", rupees(item.amount)),
      bar,
      el("small", "", percent + "% of income")
    );

    budget.append(card);
  });

  // Spending analysis
  const analysis = document.getElementById("analysis");
  analysis.innerHTML = "";

  data.analysis.forEach((item) => {
    const status = item.status === "over" ? "over" : "ok";

    const chip = el(
      "div",
      "chip " + status
    );

    const head = el("div", "head");

    head.append(
      el(
        "span",
        "",
        `${item.category} · ${item.percent}%`
      ),
      el(
        "span",
        "status",
        status === "over"
          ? "Overspending"
          : "On track"
      )
    );

    chip.append(head);

    if (item.note) {
      chip.append(
        el("p", "", item.note)
      );
    }

    analysis.append(chip);
  });

  // Saving suggestions
  const list = document.getElementById("suggestions");
  list.innerHTML = "";

  data.suggestions.forEach((text) => {
    list.append(
      el("li", "", text)
    );
  });

  results.hidden = false;

  // Update history and monthly summary
  loadHistory();
  loadMonthlySummary();

  results.scrollIntoView({
    behavior: "smooth",
  });
}


// -----------------------------
// Recent analyses
// -----------------------------

async function loadHistory() {
  try {
    const res = await fetch("/history");
    const data = await res.json();

    const box = document.getElementById("history");

    if (!box) {
      return;
    }

    box.innerHTML = "";

    if (
      !data.history ||
      data.history.length === 0
    ) {
      box.append(
        el(
          "p",
          "muted",
          "No analyses yet — run one above."
        )
      );
      return;
    }

    data.history.forEach((h) => {
      const date = new Date(
        h.created_at
      ).toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short",
      });

      const row = el(
        "div",
        "history-row"
      );

      row.append(
        el("span", "", date),
        el("span", "", rupees(h.income)),
        el(
          "span",
          "",
          h.goal || "—"
        ),
        el(
          "span",
          "",
          h.summary.savings_rate + "% saved"
        )
      );

      box.append(row);
    });
  } catch (err) {
    // History is optional; fail quietly.
  }
}


// -----------------------------
// Monthly summary
// -----------------------------

async function loadMonthlySummary() {
  try {
    const res = await fetch("/summary");
    const data = await res.json();

    const box = document.getElementById(
      "monthly-summary"
    );

    if (!box) {
      return;
    }

    box.innerHTML = "";

    if (
      !data.months ||
      data.months.length === 0
    ) {
      box.innerHTML =
        "<p class='muted'>No data yet — run an analysis above.</p>";
      return;
    }

    data.months.forEach((m) => {
      const card = el(
        "div",
        "month-card"
      );

      card.append(
        el("h3", "", m.month)
      );

      const grid = el(
        "div",
        "month-grid"
      );

      [
        ["Income", rupees(m.income)],
        ["Expenses", rupees(m.expense)],
        ["Net savings", rupees(m.net_savings)],
        ["Savings rate", m.savings_rate + "%"],
      ].forEach(([label, value]) => {
        const item = el("div");

        item.append(
          el("b", "", value),
          el("small", "", label)
        );

        grid.append(item);
      });

      card.append(grid);
      box.append(card);
    });
  } catch (err) {
    // Monthly summary is optional; fail quietly.
  }
}


// -----------------------------
// Initial page load
// -----------------------------

loadHistory();
loadMonthlySummary();
