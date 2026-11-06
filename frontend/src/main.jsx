import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

// FastAPI returns `detail` as a string (our errors) or an array (422 validation errors).
function detailToText(detail, fallback) {
    if (!detail) return fallback;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
    return JSON.stringify(detail);
}

// The LLM's JSON can omit keys or return objects instead of strings.
// Normalising here stops one bad response from crashing the whole React tree (blank page).
function toList(v) {
    if (!Array.isArray(v)) return [];
    return v.map((x) => (typeof x === "string" ? x : JSON.stringify(x)));
}
function normalizeResult(d) {
    return {
        suitable: Boolean(d && d.suitable),
        matching_skills: toList(d && d.matching_skills),
        missing_or_unverified_skills: toList(d && d.missing_or_unverified_skills),
        strengths: toList(d && d.strengths),
        recommendation: typeof (d && d.recommendation) === "string" ? d.recommendation : "",
    };
}

function App() {
    const [messages, setMessages] = useState([]), [input, setInput] = useState(""), [job, setJob] = useState(""), [result, setResult] = useState(null), [busy, setBusy] = useState(false), [analyzing, setAnalyzing] = useState(false), [uploading, setUploading] = useState(false), [candidateId, setCandidateId] = useState(null), [candidateName, setCandidateName] = useState("Demo candidate"), [error, setError] = useState("");

    async function uploadResume(event) {
        const file = event.target.files && event.target.files[0];
        event.target.value = "";
        if (!file || uploading) return;

        setError("");
        setUploading(true);
        try {
            const form = new FormData();
            form.append("file", file);
            const response = await fetch(`${API}/resumes`, { method: "POST", body: form });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(detailToText(data.detail, "Unable to process this resume."));
            if (!data.candidate_id) throw new Error("The backend did not return a candidate ID.");

            setCandidateId(data.candidate_id);
            setCandidateName(typeof data.profile?.name === "string" && data.profile.name ? data.profile.name : file.name);
            setMessages([]);
            setResult(null);
        } catch (e) {
            setError(e instanceof Error ? e.message : "Unable to upload the resume.");
        } finally {
            setUploading(false);
        }
    }
    async function send() {
        const q = input.trim();

        if (!q || busy) {
            return;
        }

        const history = messages
            .filter((m) => m.content)
            .map(({ role, content }) => ({ role, content }));

        setInput("");
        setError("");
        setBusy(true);

        setMessages((current) => [
            ...current,
            {
                role: "user",
                content: q,
            },
            {
                role: "assistant",
                content: "",
            },
        ]);

        try {
            console.log("Sending request to:", `${API}/chat`);

            const response = await fetch(`${API}/chat`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Accept": "text/plain",
                },
                body: JSON.stringify({
                    question: q,
                    history: history,
                    candidate_id: candidateId,
                }),
            });

            console.log("Backend response:", response.status);

            if (!response.ok) {
                let errorMessage = `Backend error: ${response.status}`;

                try {
                    const errorData = await response.json();

                    errorMessage = detailToText(errorData.detail, errorMessage);
                } catch {
                    // Ignore JSON parsing errors
                }

                throw new Error(errorMessage);
            }

            if (!response.body) {
                throw new Error("The backend returned an empty response.");
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            let answer = "";

            while (true) {
                const { value, done } = await reader.read();

                if (done) {
                    break;
                }

                const chunk = decoder.decode(value, {
                    stream: true,
                });

                answer += chunk;

                setMessages((current) => [
                    ...current.slice(0, -1),
                    {
                        role: "assistant",
                        content: answer,
                    },
                ]);
            }

            if (!answer) {
                throw new Error("The AI returned an empty response.");
            }

        } catch (error) {
            console.error("Chat error:", error);

            setError(
                error instanceof Error
                    ? error.message
                    : "Unable to connect to the backend."
            );

            // Remove the empty assistant message
            setMessages((current) => current.slice(0, -1));

        } finally {
            setBusy(false);
        }
    }
    async function analyze() {
        if (!job.trim() || analyzing) return;
        setError("");
        setAnalyzing(true);
        try {
            const r = await fetch(`${API}/job-match`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ job_description: job, candidate_id: candidateId }),
            });
            const data = await r.json().catch(() => ({}));
            if (!r.ok) throw new Error(detailToText(data.detail, `Backend error: ${r.status}`));
            setResult(normalizeResult(data));
        } catch (e) {
            setError(e instanceof Error ? e.message : "Unable to connect to the backend.");
        } finally {
            setAnalyzing(false);
        }
    }
    return <div className="page"><header><div><h1>AI Candidate Agent</h1><p>{candidateName}{candidateId ? " · uploaded resume" : " · bundled demo profile"}</p></div><button onClick={() => setMessages([])}>Clear chat</button></header>
        <section className="card uploader"><div><h2>Load a candidate resume</h2><p>Upload a PDF, DOCX, or TXT file. The profile is extracted and used immediately for chat and job matching.</p></div><label className="upload-button"><input type="file" accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" onChange={uploadResume} disabled={uploading || busy || analyzing} />{uploading ? "Extracting profile..." : "Upload resume"}</label>{candidateId && <button className="secondary" onClick={() => { setCandidateId(null); setCandidateName("Demo candidate"); setMessages([]); setResult(null); }}>Use demo profile</button>}</section>
        <main><section className="card chat"><div className="messages">{messages.length === 0 ? <div className="welcome"><h2>Ask about {candidateName}</h2><p>{candidateId ? "Ask about this uploaded candidate’s experience, education, or projects." : "Upload a resume, or try: “Tell me about the VectorDB project.”"}</p></div> : messages.map((m, i) => <div className={"msg " + m.role} key={i}><b>{m.role === "user" ? "You" : "AI"}</b><p>{m.content || "Thinking..."}</p></div>)}</div>
            <div className="composer"><input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} placeholder="Ask about resume, jobs, or projects..." disabled={busy} /><button onClick={send} disabled={busy}>{busy ? "..." : "Send"}</button></div></section>
            <aside className="card"><h2>Job Matcher</h2><p>Paste a job description to compare it with {candidateId ? "the uploaded resume" : "the demo profile"}.</p><textarea value={job} onChange={e => setJob(e.target.value)} placeholder="Paste job description here..." /><button onClick={analyze} disabled={analyzing || uploading}>{analyzing ? "Analyzing..." : "Analyze job"}</button>{result && <div className="result"><h3>{result.suitable ? "Potential match" : "Insufficient evidence for a match"}</h3><b>Matching skills</b><ul>{result.matching_skills.map((x, i) => <li key={i}>{x}</li>)}</ul><b>Missing / unverified</b><ul>{result.missing_or_unverified_skills.map((x, i) => <li key={i}>{x}</li>)}</ul>{result.strengths.length > 0 && <><b>Strengths</b><ul>{result.strengths.map((x, i) => <li key={i}>{x}</li>)}</ul></>}<b>Recommendation</b><p>{result.recommendation}</p></div>}</aside></main>{error && <div className="error" onClick={() => setError("")} title="Click to dismiss">{error}</div>}</div>
}
createRoot(document.getElementById("root")).render(<App />);
