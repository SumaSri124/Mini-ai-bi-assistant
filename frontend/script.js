const questionInput = document.getElementById("question");
const askButton = document.getElementById("ask-button");
const connectionStatus = document.getElementById("connection-status");

const resultSection = document.getElementById("result-section");
const resultStatus = document.getElementById("result-status");
const answerText = document.getElementById("answer-text");
const resultsTable = document.getElementById("results-table");
const sqlText = document.getElementById("sql-text");
const sqlPanel = document.querySelector(".sql-panel");

const tableEmpty = document.getElementById("table-empty");

function formatValue(value) {
    if (value === null || value === undefined) {
        return "—";
    }

    if (typeof value === "number" && Number.isFinite(value)) {
        return value.toLocaleString("en-IN", {
            maximumFractionDigits: 2
        });
    }

    return String(value);
}

function showError(message) {
    let errorElement = document.getElementById("error-message");

    if (!errorElement) {
        errorElement = document.createElement("div");
        errorElement.id = "error-message";
        errorElement.setAttribute("role", "alert");
        errorElement.style.cssText = [
            "padding: 14px 18px",
            "margin-top: 14px",
            "border-radius: 10px",
            "background: #fff0f0",
            "color: #b42318",
            "border: 1px solid #fecdca"
        ].join(";");

        askButton.closest(".question-panel")?.appendChild(errorElement);
    }

    errorElement.textContent = message;
    errorElement.hidden = false;
}

function clearError() {
    const errorElement = document.getElementById("error-message");

    if (errorElement) {
        errorElement.textContent = "";
        errorElement.hidden = true;
    }
}

function setLoading(isLoading) {
    askButton.disabled = isLoading;
    askButton.textContent = isLoading ? "Analyzing..." : "✦ Ask AI →";
    questionInput.disabled = isLoading;
}

function renderTable(columns, rows) {
    const thead = resultsTable.querySelector("thead");
    const tbody = resultsTable.querySelector("tbody");

    thead.replaceChildren();
    tbody.replaceChildren();

    if (!columns.length || !rows.length) {
        if (tableEmpty) {
            tableEmpty.hidden = false;
        }

        return;
    }

    if (tableEmpty) {
        tableEmpty.hidden = true;
    }

    const headerRow = document.createElement("tr");

    columns.forEach((column) => {
        const th = document.createElement("th");
        th.textContent = column
            .replaceAll("_", " ")
            .replace(/\b\w/g, (letter) => letter.toUpperCase());

        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);

    rows.forEach((item) => {
        const row = document.createElement("tr");

        columns.forEach((column) => {
            const cell = document.createElement("td");
            cell.textContent = formatValue(item[column]);
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });
}

function renderResult(data) {
    resultSection.hidden = false;

    answerText.textContent = data.answer || "No answer was returned.";

    const needsClarification = data.status === "needs_clarification";

    resultStatus.textContent = needsClarification
        ? "Needs clarification"
        : "Completed";

    resultStatus.classList.toggle("warning", needsClarification);

    renderTable(data.columns || [], data.rows || []);

    sqlText.textContent = data.sql || "No SQL query was executed.";

    if (sqlPanel) {
        sqlPanel.hidden = !data.sql;
    }

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

async function askQuestion() {
    const question = questionInput.value.trim();

    clearError();

    if (question.length < 3) {
        showError("Please enter a question containing at least 3 characters.");
        questionInput.focus();
        return;
    }

    setLoading(true);

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        let data;

        try {
            data = await response.json();
        } catch {
            throw new Error("The server returned an invalid response.");
        }

        if (!response.ok) {
            const message = typeof data.detail === "string"
                ? data.detail
                : "The request failed. Please try again.";

            throw new Error(message);
        }

        renderResult(data);

    } catch (error) {
        showError(
            error.message ||
            "Could not connect to the server. Check that FastAPI is running."
        );
    } finally {
        setLoading(false);
    }
}

askButton.addEventListener("click", askQuestion);

questionInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        askQuestion();
    }
});

document.querySelectorAll(".example-card").forEach((button) => {
    button.addEventListener("click", () => {
        questionInput.value = button.dataset.question || "";
        askQuestion();
    });
});

async function checkConnection() {
    try {
        const response = await fetch("/health");
        const data = await response.json();

        if (response.ok && data.status === "ok" && data.database_exists) {
            connectionStatus.textContent = "Connected";
        } else {
            connectionStatus.textContent = "Database unavailable";
        }
    } catch {
        connectionStatus.textContent = "Connection unavailable";
    }
}

checkConnection();