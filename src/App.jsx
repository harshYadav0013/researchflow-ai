import React, { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  getResearchDetail,
  getResearchHistory,
  resumeResearch,
  startResearch,
} from "./api";

const steps = [
  { id: "search", label: "Search" },
  { id: "reader", label: "Read sources" },
  { id: "writer", label: "Write draft" },
  { id: "critic", label: "Review" },
  { id: "human_review", label: "Your review" },
  { id: "final", label: "Final report" },
];

function App() {
  const [question, setQuestion] = useState("");
  const [threadId, setThreadId] = useState(null);
  const [status, setStatus] = useState("idle");
  const [history, setHistory] = useState([]);

  const [draft, setDraft] = useState("");
  const [critic, setCritic] = useState("");
  const [finalVersion, setFinalVersion] = useState("");

  const [sources, setSources] = useState([]);

  const [error, setError] = useState("");

  useEffect(() => {
  async function loadHistory() {
    try {
      const data = await getResearchHistory();
      setHistory(data.research || []);
    } catch (err) {
      console.error("Failed to load research history:", err);
    }
  }

  loadHistory();
}, []);

  const currentStep = useMemo(() => {
    if (status === "idle") return -1;
    if (status === "running") return 2;
    if (status === "review") return 4;
    if (status === "final") return 5;
    return 0;
  }, [status]);

  async function handleStart(event) {
    event.preventDefault();

    if (!question.trim()) return;

    setError("");
    setDraft("");
    setCritic("");
    setFinalVersion("");
    setSources([]);
    setStatus("running");

    try {
      const data = await startResearch(question.trim());

      setThreadId(data.thread_id);
      setDraft(data.draft || "");
      setCritic(data.critic || "");
      setSources(data.sources || []);

      setStatus(data.interrupted ? "review" : "final");

      if (data.final_version) {
        setFinalVersion(data.final_version);
      }
    } catch (err) {
      setError(err.message);
      setStatus("idle");
    }
  }

  async function handleDecision(approved) {
    if (!threadId) return;

    setError("");
    setStatus("running");

    try {
      const data = await resumeResearch(threadId, approved);

      setDraft(data.draft || draft);
      setCritic(data.critic || critic);
      setSources(data.sources || sources);

      if (data.interrupted) {
        setStatus("review");
      } else {
        setFinalVersion(data.final_version || "");
        setStatus("final");
      }
    } catch (err) {
      setError(err.message);
      setStatus("review");
    }
  }

async function handleHistoryClick(selectedThreadId) {
  setError("");

  try {
    const data = await getResearchDetail(selectedThreadId);

    setThreadId(data.thread_id);
    setQuestion(data.question || "");
    setDraft(data.draft || "");
    setCritic(data.critic || "");
    setFinalVersion(data.final_version || "");
    setSources(data.sources || []);

    if (data.status === "completed") {
      setStatus("final");
    } else {
      setStatus("review");
    }
  } catch (err) {
    setError(err.message);
  }
}

  return (
    <div className="app-shell">

      {/* ================= HEADER ================= */}

      <header className="topbar">

        <div className="brand">

          <div className="brand-mark">
            R
          </div>

          <div>
            <div className="brand-name">
              Research AI
            </div>

            <div className="brand-subtitle">
              Research workspace
            </div>
          </div>

        </div>

        <div className="status-pill">

          <span className="status-dot" />

          AI research engine

        </div>

      </header>


      {/* ================= MAIN ================= */}

      <main className="workspace">

        {/* ================= HERO ================= */}

        <section className="hero">

          <div className="eyebrow">
            AUTONOMOUS RESEARCH WORKSPACE
          </div>

          <h1>
            Turn a question into a
            <br />
            <span>reviewed research report.</span>
          </h1>

          <p>
            Search the web, read sources, draft the report,
            critique it, and keep the final decision in your hands.
          </p>


          {/* Research input */}

          <form
            className="research-form"
            onSubmit={handleStart}
          >

            <div className="input-wrap">

              <span className="search-icon">
                ⌕
              </span>

              <input
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What do you want to research?"
                disabled={status === "running"}
              />

            </div>


            <button
              className="primary-button"
              disabled={
                !question.trim() ||
                status === "running"
              }
            >

              {status === "running"
                ? "Researching..."
                : "Start research"}

              <span>
                →
              </span>

            </button>

          </form>


          {/* Error */}

          {error && (
            <div className="error-box">
              {error}
            </div>
          )}

        </section>


        {/* ================= WORKFLOW ================= */}

        <section className="pipeline-card">

          <div className="section-heading">

            <div>

              <div className="section-kicker">
                WORKFLOW
              </div>

              <h2>
                Research pipeline
              </h2>

            </div>


            <span
              className={`run-state ${status}`}
            >
              {statusLabel(status)}
            </span>

          </div>


          <div className="pipeline">

            {steps.map((step, index) => (

              <div
                className="pipeline-step"
                key={step.id}
              >

                <div
                  className={`step-node ${
                    index < currentStep
                      ? "complete"
                      : index === currentStep
                      ? "active"
                      : ""
                  }`}
                >

                  {index < currentStep
                    ? "✓"
                    : index + 1}

                </div>


                <span>
                  {step.label}
                </span>


                {index < steps.length - 1 && (

                  <div
                    className={`step-line ${
                      index < currentStep
                        ? "complete"
                        : ""
                    }`}
                  />

                )}

              </div>

            ))}

          </div>

        </section>


        {/* ================= REPORT + CRITIC ================= */}

        {(draft || critic || finalVersion) && (

          <section className="content-grid">


            {/* ================= REPORT ================= */}

            <div className="document-card">

              <div className="card-header">

                <div>

                  <div className="section-kicker">
                    RESEARCH OUTPUT
                  </div>

                  <h2>
                    {finalVersion
                      ? "Final report"
                      : "Current draft"}
                  </h2>

                </div>


                {status === "review" && (

                  <span className="review-badge">
                    Needs your review
                  </span>

                )}

              </div>


              <article className="document-body">

                <ReactMarkdown>
                  {finalVersion || draft}
                </ReactMarkdown>

              </article>

            </div>


            {/* ================= CRITIC ================= */}

            <aside className="review-card">

              <div className="section-kicker">
                EDITOR REVIEW
              </div>

              <h2>
                Critic feedback
              </h2>


              <div className="critic-body">

                {critic ||
                  "Waiting for the research engine..."}

              </div>


              {/* Human decision */}

              {status === "review" && (

                <div className="decision-area">

                  <div className="decision-title">
                    What should happen next?
                  </div>


                  <div className="decision-actions">

                    <button
                      className="approve-button"
                      onClick={() =>
                        handleDecision(true)
                      }
                    >
                      ✓ Approve
                    </button>


                    <button
                      className="revise-button"
                      onClick={() =>
                        handleDecision(false)
                      }
                    >
                      ↻ Request revision
                    </button>

                  </div>


                  <p>
                    Approval produces the final report.
                    Revision sends the draft back through
                    the writer and critic.
                  </p>

                </div>

              )}

            </aside>

          </section>

        )}


        {/* ================= SOURCES ================= */}

        {sources.length > 0 && (

          <section className="sources-card">

            <div className="section-kicker">
              RESEARCH SOURCES
            </div>


            <div className="sources-header">

              <div>

                <h2>
                  Sources used
                </h2>

                <p>
                  Sources retrieved during the
                  research process.
                </p>

              </div>


              <span className="source-count">
                {sources.length} sources
              </span>

            </div>


            <div className="sources-list">

              {sources.map((source, index) => (

                <div
                  className="source-item"
                  key={`${source.url}-${index}`}
                >

                  <div className="source-number">

                    {String(index + 1).padStart(2, "0")}

                  </div>


                  <div className="source-info">

                    <h3>
                      {source.title ||
                        "Untitled source"}
                    </h3>


                    <p>
                      {source.content ||
                        "No source summary available."}
                    </p>


                    {source.url && (

                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Open source ↗
                      </a>

                    )}

                  </div>

                </div>

              ))}

            </div>

          </section>

        )}
        {history.length > 0 && (
  <section className="history-card">
    <div className="section-kicker">RESEARCH HISTORY</div>

    <div className="history-header">
      <div>
        <h2>Previous research</h2>
        <p>Your recent research sessions.</p>
      </div>

      <span className="source-count">
        {history.length} research{history.length !== 1 ? "es" : ""}
      </span>
    </div>

    <div className="history-list">
      {history.map((item) => (
        <div
           className="history-item"
              key={item.thread_id}
                 onClick={() => handleHistoryClick(item.thread_id)}
>
          <div className="history-info">
            <h3>{item.question}</h3>

            <p>
              {item.status === "completed"
                ? "Completed"
                : "Awaiting review"}
            </p>
          </div>

          <div className="history-date">
            {new Date(item.created_at).toLocaleDateString()}
          </div>
        </div>
      ))}
    </div>
  </section>
)}


        {/* ================= EMPTY STATE ================= */}

        {status === "idle" && (

          <section className="empty-state">

            <div className="empty-icon">
              ✦
            </div>

            <h2>
              Your research workspace is ready.
            </h2>

            <p>
              Enter a research question above to
              start the workflow.
            </p>

          </section>

        )}

      </main>


      {/* ================= FOOTER ================= */}

      <footer>

        <span>
          Research AI
        </span>

        <span>
          Human-in-the-loop · Powered by LangGraph
        </span>

      </footer>

    </div>
  );
}


/* ================= STATUS LABEL ================= */

function statusLabel(status) {

  if (status === "running")
    return "RUNNING";

  if (status === "review")
    return "AWAITING REVIEW";

  if (status === "final")
    return "COMPLETED";

  return "READY";
}


export default App;