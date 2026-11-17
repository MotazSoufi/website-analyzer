import { useState } from 'react';
import './App.css';

const API = "http://127.0.0.1:8000";
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function isKnown(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") {
    const v = value.trim().toLowerCase();
    return v !== "" && v !== "unknown";
  }
  if (Array.isArray(value)) return value.some(isKnown);
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}

//removes unknown items from the list
function cleanList(items) {
  return (items || []).filter(isKnown);
}

function formatDate(iso) {
  return iso ? new Date(iso).toLocaleString() : "";
}

function Card({ title, wide, children }) {
  return (
    <section className={wide ? "card wide" : "card"}>
      <h3>{title}</h3>
      {children}
    </section>
  );
}

function Field({ label, value, note }) {
  const shown = Array.isArray(value) ? cleanList(value).join(", ") : value;
  return (
    <div className="field">
      <span className="label">{label}</span>
      {isKnown(value) ? (
        <span>
          {shown}
          {note && <em className="note"> {note}</em>}
        </span>
      ) : (
        <span className="missing">Not found</span>
      )}
    </div>
  );
}

function Sources({ sources }) {
  if (!sources?.length) return null;
  return (
    <details>
      <summary>Sources ({sources.length})</summary>
      <ul>
        {sources.map((s) => (
          <li key={s.url}>
            <a href={s.url} target="_blank" rel="noreferrer">{s.title}</a>
          </li>
        ))}
      </ul>
    </details>
  );
}

function Report({ report, darkLogo, setDarkLogo, onRefresh }) {
  const instagram = report.instagram && !report.instagram.failed ? report.instagram : null;
  const youtube = report.youtube && !report.youtube.failed ? report.youtube : null;
  const branches = report.branches || [];
  const emails = cleanList(report.emails);
  const phones = cleanList(report.phones);
  const colors = cleanList(report.brand_colors);
  const hasContact = emails.length > 0 || phones.length > 0 || branches.length > 0 || isKnown(report.headquarters);

  return (
    <div className="report">
      <header className='report-header'>
        {report.logo_url && (
          <img
            src={report.logo_url}
            alt="logo"
            className={darkLogo ? "logo dark" : "logo"}
            onClick={() => setDarkLogo(!darkLogo)}
            title="Click to switch the background"
            onError={(e) => {
              if (report.logo_fallback_url && e.target.src !== report.logo_fallback_url) {
                e.target.src = report.logo_fallback_url;
              } else {
                e.target.style.display = "none";
              }
            }}
          />
        )}
        <div>
          <h2>{isKnown(report.brand_name) ? report.brand_name : "Unknown brand"}</h2>
          <a href={report.url} target="_blank" rel="noreferrer">{report.url}</a>
        </div>
      </header>

      {report.cached_at && (
        <div className="notice">
          Saved report from <strong>{formatDate(report.cached_at)}</strong>.{" "}
          <button className="link-button" onClick={onRefresh}>Analyze again</button>
        </div>
      )}

      {report.mode === "archive" && (
        <div className='notice'>
          The website blocked direct access. This report uses an archived copy from {" "}
          <strong>{report.archive_date}</strong>.{" "}
          <a href={report.archive_url} target="_blank" rel="noreferrer">View snapshot</a>
        </div>
      )}

      {report.mode === "fallback" && (
        <div className='notice'>
          The website blocked direct access, so this report is based on public web sources. 
          The logo is provided by Brandfetch.
          <Sources sources={report.research_sources} />
        </div>
      )}

      {report.filled_by_research?.length > 0 && (
        <div className='notice'>
          Filled in from web research: <strong>{report.filled_by_research.join(", ")}</strong>
          <Sources sources={report.research_sources} />
        </div>
      )}

      {report.failed_agents?.length > 0 && (
        <div className='notice warning'>
          Some parts couldn't be loaded: {report.failed_agents.join(", ")}
        </div>
      )}

      {isKnown(report.summary) && <p className='summary'>{report.summary}</p>}

      <div className='grid'>
        <Card title="Business">
          <Field label="Market" value={report.market} />
          <Field label="Products" value={report.products} />
          <Field label="Services" value={report.services} />
          <Field 
            label="Size" 
              value={report.size}
              note={isKnown(report.size_reason) ? `(${report.size_reason})`: ""} 
          />
        </Card>

        <Card title="Location & language">
          <Field
            label="Region"
            value={report.region}
            note={isKnown(report.region_reason)? `(${report.region_reason})` : ""}
          />
          <Field label="Countries" value={report.countries} />
          <Field 
            label="Languages"
            value={report.languages}
            note={report.languages_estimated ? "(estimated)" : ""}
          />
        </Card>

        <Card title="Brand identity">
          <div className="field">
            <span className="label">Colors</span>
            {colors.length > 0 ? (
              <div className="colors">
                {colors.map((color) => (
                  <div key={color} className="color">
                    <div className="swatch" style={{ background: color }} />
                    <span>{color}</span>
                  </div>
                ))}
              </div>
            ) : (
              <span className="missing">Not found</span>
            )}
          </div>
          <Field label="Theme" value={report.theme} />
          <Field label="Logo" value={report.logo_description} />
        </Card>

        <Card title="Website & socials">
          <div className="field">
            <span className="label">Tech stack</span>
            {isKnown(report.tech_stack) ? (
              <span>
                {Object.entries(report.tech_stack).map(([category, names]) => (
                  <div key={category}>
                    <strong>{category}:</strong> {names.join(", ")}
                  </div>
                ))}
              </span>
            ) : (
              <span className="missing">Not detected</span>
            )}
          </div>
          <div className="field">
            <span className="label">Socials</span>
            {isKnown(report.social_links) ? (
              <span className="links">
                {Object.entries(report.social_links).map(([platform, link]) => (
                  <a key={platform} href={link} target="_blank" rel="noreferrer">{platform}</a>
                ))}
              </span>
            ) : (
              <span className="missing">Not found</span>
            )}
          </div>
        </Card>

        {hasContact && (
          <Card title="Contact & branches">
            <Field label="Email" value={emails} />
            <Field label="Phone" value={phones} />
            <Field label="Headquarters" value={report.headquarters} />
            {branches.length > 0 && (
              <>
                <p className="label">Branches ({branches.length})</p>
                <ul className="branches">
                  {branches.map((b, i) => {
                    const place = [b.city, b.country].filter(Boolean).join(", ");
                    return (
                      <li key={i}>
                        <strong>{b.name || b.city || "Branch"}</strong>
                        {place && ` (${place})`}
                        {b.address && <div>{b.address}</div>}
                        {b.phone && <div>{b.phone}</div>}
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
            {report.contact_page && (
              <a href={report.contact_page} target="_blank" rel="noreferrer">View contact page</a>
            )}
          </Card>
        )}

        {report.competitors?.length > 0 && (
          <Card title="Competitors" wide>
            <ul className="competitors">
              {report.competitors.map((c) => (
                <li key={c.name}>
                  {isKnown(c.website) ? (
                    <a href={c.website} target="_blank" rel="noreferrer"><strong>{c.name}</strong></a>
                  ) : (
                    <strong>{c.name}</strong>
                  )}
                  : {c.reason}
                </li>
              ))}
            </ul>
            <Sources sources={report.competitor_sources} />
          </Card>
        )}

        {instagram && (
          <Card title="Instagram" wide>
            <p>
              <a href={instagram.profile_url} target="_blank" rel="noreferrer">@{instagram.username}</a>
              {instagram.is_verified && " ✓"} ·{" "}
              {Number(instagram.followers || 0).toLocaleString()} followers ·{" "}
              {Number(instagram.post_count || 0).toLocaleString()} posts
            </p>
            {instagram.bio && <p className="bio">{instagram.bio}</p>}
            <ul className="posts">
              {instagram.latest_posts.map((post) => (
                <li key={post.url}>
                  <a href={post.url} target="_blank" rel="noreferrer">{post.date}</a>
                  {" · "}❤️ {post.likes ?? "?"} · 💬 {post.comments ?? "?"}
                  <p>{post.caption || "(no caption)"}</p>
                </li>
              ))}
            </ul>
          </Card>
        )}

        {youtube && (
          <Card title="YouTube" wide>
            <p>
              <a href={youtube.channel_url} target="_blank" rel="noreferrer">{youtube.channel_name}</a>
              {youtube.subscribers && ` · ${Number(youtube.subscribers).toLocaleString()} subscribers`}
              {` · ${youtube.video_count} videos`}
            </p>
            <div className="videos">
              {youtube.latest_videos.map((video) => (
                <a key={video.url} href={video.url} target="_blank" rel="noreferrer" className="video">
                  <img src={video.thumbnail} alt={video.title} />
                  <span>{video.title}</span>
                  <small>{video.published}</small>
                </a>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

function App() {
  const [url, setUrl] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [steps, setSteps] = useState([]);
  const [darkLogo, setDarkLogo] = useState(false);
  const [tab, setTab] = useState("analyze");
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  function handleSubmit(e) {
    e.preventDefault();
    runAnalysis(false);
  }

  async function loadHistory() {
    setHistoryLoading(true);
    try {
      const res = await fetch(`${API}/history`);
      setHistory(await res.json());
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function openHistoryItem(id) {
    const res = await fetch(`${API}/history/${id}`);
    if (!res.ok) return;
    const saved = await res.json();
    setReport(saved);
    setSteps([]);
    setError("");
    setDarkLogo(false);
    setTab("analyze");
  }

  async function runAnalysis(refresh = false, targetUrl = url) {
    if (!targetUrl.trim() || loading) return;

    setTab("analyze");
    setUrl(targetUrl);
    setLoading(true);
    setError("");
    setReport(null);
    setSteps([]);
    setDarkLogo(false);
    
    try {
      const startRes = await fetch(`${API}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: targetUrl, refresh }),
      });
      const startData = await startRes.json();
      if (!startRes.ok) throw new Error(startData.detail || "Could not start the analysis");

      while (true) {
        await sleep(1000);
        const res = await fetch(`${API}/jobs/${startData.job_id}`);
        const job = await res.json();
        if (!res.ok) throw new Error(job.detail || "Lost track of the analysis");

        setSteps(job.steps);
        if (job.done) {
          if (job.error) throw new Error(job.error);
          setReport(job.report);
          break;
        }
      }
  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}

return (
  <div className="container">
    <h1>Website Analyzer</h1>

    <nav className='tabs'>
      <button className={tab === "analyze" ? "active" : ""} onClick={() => setTab("analyze")}>
        New analysis
      </button>
      <button
        className={tab === "history" ? "active" : ""}
        onClick={() => {
          setTab("history");
          loadHistory();
        }}
      >
        History
      </button>
    </nav>

    {tab === "analyze" && (
      <>
    

    <form className="search" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder='Enter a website, e.g. example.com'
        value={url}
        onChange={(e) => setUrl(e.target.value)}
      />
      <button type="submit" disabled={loading}>
        {loading ? "Analyzing..." : "Analyze"}
      </button>
    </form>

    {steps.length > 0 && (loading || error) && (
      <ul className='steps'>
        {steps.map((step, i) => {
          const isCurrent = loading && i === steps.length - 1;
          return (
            <li key={i} className={isCurrent ? "current" : ""}>
              {isCurrent ? "⏳" : "✓"} {step}
            </li>
          );
        })}
      </ul>
    )}

    {error && <p className="error">{error}</p>}
    {report && (
      <Report 
        report={report}
        darkLogo={darkLogo}
        setDarkLogo={setDarkLogo}
        onRefresh={() => runAnalysis(true, report.url)}
      />
    )}
    </>
    )}

    {tab === "history" && (
      <div className='history'>
        {historyLoading && <p>Loading...</p>}
        {!historyLoading && history.length === 0 && (
          <p className='missing'>No saved reports yet.</p>
        )}
        <ul>
          {history.map((item) => (
            <li key={item.id} onClick={() => openHistoryItem(item.id)}>
              {item.logo_url && (
                <img src={item.logo_url} alt="" onError={(e) => (e.target.style.display = "none")} />
              )}
              <div className='history-info'>
                <strong>{isKnown(item.brand_name) ? item.brand_name : item.domain}</strong>
                <span>{item.domain}</span>
              </div>
              <span className='history-date'>{formatDate(item.created_at)}</span>
              <span className='mode'>{item.mode}</span>
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);
}

export default App;
