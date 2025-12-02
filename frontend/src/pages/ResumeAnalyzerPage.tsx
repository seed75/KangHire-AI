import { useState } from "react";
import type { ChangeEvent } from "react";

export interface AiAnalysisResult {
  summary: string;
  skills_found: string[];
  skills_missing: string[];
  score: number;
  recommendations: string[];
  error?: string;
  raw_output?: string;
}

type AnalysisStatus = "idle" | "loading" | "success" | "error";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function ResumeAnalyzerPage() {
  const [resumeText, setResumeText] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [result, setResult] = useState<AiAnalysisResult | null>(null);
  const [status, setStatus] = useState<AnalysisStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // new state for target role
  const [targetRole, setTargetRole] = useState<string>("Software Developer");

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTargetRole(e.target.value);
  };

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setResumeText(e.target.value);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
  };

  const resetStateBeforeRequest = () => {
    setStatus("loading");
    setErrorMessage(null);
    setResult(null);
  };

  const handleAnalyzeRule = async () => {
    if (!resumeText.trim()) {
      setErrorMessage("Please enter your resume text first.");
      setStatus("error");
      return;
    }

    resetStateBeforeRequest();

    try {
      const response = await fetch(`${API_BASE_URL}/analyze_resume`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: resumeText, target_role: targetRole }),
      });

      if (!response.ok) {
        throw new Error(`Server error (status: ${response.status})`);
      }

      const data: AiAnalysisResult = await response.json();
      setResult(data);
      setStatus("success");
    } catch (err: any) {
      setErrorMessage(err.message ?? "An unknown error occurred.");
      setStatus("error");
    }
  };

  const handleAnalyzeAiText = async () => {
    if (!resumeText.trim()) {
      setErrorMessage("Please enter your resume text first.");
      setStatus("error");
      return;
    }

    resetStateBeforeRequest();

    try {
      const response = await fetch(`${API_BASE_URL}/analyze_resume_ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: resumeText, target_role: targetRole }),
      });

      if (!response.ok) {
        throw new Error(`Server error (status: ${response.status})`);
      }

      const data: AiAnalysisResult = await response.json();

      if (data.error) {
        setErrorMessage(data.error);
        setStatus("error");
      } else {
        setResult(data);
        setStatus("success");
      }
    } catch (err: any) {
      setErrorMessage(err.message ?? "An unknown error occurred.");
      setStatus("error");
    }
  };

  const handleAnalyzeAiFile = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select a PDF or DOCX resume file first.");
      setStatus("error");
      return;
    }

    resetStateBeforeRequest();

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("target_role", targetRole);

      const response = await fetch(`${API_BASE_URL}/upload_resume_ai`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server error (status: ${response.status})`);
      }

      const data: AiAnalysisResult = await response.json();

      if (data.error) {
        setErrorMessage(data.error);
        setStatus("error");
      } else {
        setResult(data);
        setStatus("success");
      }
    } catch (err: any) {
      setErrorMessage(err.message ?? "An unknown error occurred.");
      setStatus("error");
    }
  };

  const renderResult = () => {
    if (status === "idle") {
      return (
        <p className="kh-result-placeholder">
          The analysis results will appear here. Enter your resume and click a button to begin.
        </p>
      );
    }

    if (status === "loading") {
      return <p className="kh-result-placeholder">AI is analyzing your resume... 🔍</p>;
    }

    if (status === "error") {
      return <p className="kh-result-error">⚠ {errorMessage}</p>;
    }

    if (status === "success" && result) {
      return (
        <>
          <p className="kh-result-summary">{result.summary}</p>

          <div className="kh-score-box">
            <span className="kh-label">Score</span>
            <div className="kh-score-value">{result.score} / 100</div>
          </div>

          <div style={{ marginTop: "0.4rem" }}>
            <span className="kh-label">Detected Skills</span>
            {result.skills_found.length === 0 ? (
              <p className="kh-result-placeholder">No skills detected.</p>
            ) : (
              <div className="kh-tag-row">
                {result.skills_found.map((skill) => (
                  <span key={skill} className="kh-tag-found">
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginTop: "0.6rem" }}>
            <span className="kh-label">Missing / Weak Skills</span>
            {result.skills_missing.length === 0 ? (
              <p className="kh-result-placeholder">No missing or weak skills detected.</p>
            ) : (
              <div className="kh-tag-row">
                {result.skills_missing.map((skill) => (
                  <span key={skill} className="kh-tag-missing">
                    {skill}
                  </span>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginTop: "0.6rem" }}>
            <span className="kh-label">Recommendations</span>
            {result.recommendations.length === 0 ? (
              <p className="kh-result-placeholder">No recommendations available.</p>
            ) : (
              <ul className="kh-reco-list">
                {result.recommendations.map((item, index) => (
                  <li key={index}>{item}</li>
                ))}
              </ul>
            )}
          </div>
        </>
      );
    }

    return null;
  };

  return (
    <div className="kh-root">
      <div className="kh-shell">
        {/* Header */}
        <header>
          <div className="kh-header-pill">
            <span>Resume Coach</span>
            <span>by KangHire AI</span>
          </div>
          <h1 className="kh-title">
            Good careers come to those <span>who prepare.</span>
          </h1>
          <p className="kh-subtitle">
            Paste your resume or upload a PDF/DOCX file. KangHire AI analyzes your strengths, missing skills, and improvement suggestions.
          </p>
        </header>

        {/* Main layout: 2 columns */}
        <main className="kh-main-grid">
          {/* Left: Input Panel */}
          <section className="kh-panel">
            <div className="kh-panel-title">1. Resume Input</div>

            <div>
              <div className="kh-label">Paste your resume text</div>
              <textarea
                className="kh-textarea"
                value={resumeText}
                onChange={handleTextChange}
                placeholder="Paste your English resume here..."
              />
            </div>

            <div style={{ marginTop: "0.4rem" }}>
              <div className="kh-label">Target Role</div>
              <select
                value={targetRole}
                onChange={handleRoleChange}
                style={{
                  marginTop: "0.25rem",
                  width: "100%",
                  padding: "0.45rem 0.75rem",
                  borderRadius: "0.6rem",
                  border: "1px solid rgba(55, 65, 81, 0.9)",
                  background: "rgba(15, 23, 42, 0.9)",
                  color: "#e5e7eb",
                  fontSize: "0.85rem",
                }}
              >
                <option value="Software Developer">Software Developer</option>
                <option value="Frontend Developer">Frontend Developer</option>
                <option value="Backend Developer">Backend Developer</option>
                <option value="Data Analyst">Data Analyst</option>
                <option value="UI/UX Designer">UI/UX Designer</option>
                <option value="Marketing Specialist">Marketing Specialist</option>
                <option value="Customer Service">Customer Service</option>
                <option value="Project Manager">Project Manager</option>
                <option value="Other">Other / General</option>
              </select>
            </div>

            <div className="kh-file-row">
              <div className="kh-label">Or upload a PDF / DOCX file</div>
              <input
                type="file"
                accept=".pdf,.doc,.docx"
                onChange={handleFileChange}
              />
              {selectedFile && (
                <div className="kh-selected-file">
                  Selected file: {selectedFile.name}
                </div>
              )}
            </div>

            <div className="kh-button-row">
              <button className="kh-btn" onClick={handleAnalyzeRule}>
                Analyze Text (Rule-based)
              </button>
              <button className="kh-btn" onClick={handleAnalyzeAiText}>
                Analyze Text (AI)
              </button>
              <button className="kh-btn kh-btn-primary" onClick={handleAnalyzeAiFile}>
                Analyze File (AI)
              </button>
            </div>
          </section>

          {/* Right: Result Panel */}
          <section className="kh-panel kh-panel-right">
            <div className="kh-panel-title">2. Analysis Result</div>
            {renderResult()}
          </section>
        </main>
      </div>
    </div>
  );
}
