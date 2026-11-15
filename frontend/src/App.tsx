
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Brain,
  CheckCircle2,
  ChevronDown,
  ClipboardCheck,
  FileCheck2,
  FileText,
  LayoutDashboard,
  LockKeyhole,
  Plus,
  Scale,
  Settings,
  ShieldCheck,
  Sparkles,
  Users,
  Zap,
  Bell,
  CircleHelp,
  Info,
} from "lucide-react";
import type { ReactNode } from "react";
import "./App.css";

const activities = [
  {
    title: "Personality profile created",
    detail: "New digital personality profile",
    time: "Recently",
    icon: Users,
  },
  {
    title: "Assessment validation",
    detail: "Assessment data validation",
    time: "Recently",
    icon: ClipboardCheck,
  },
  {
    title: "AI generation",
    detail: "Personality-grounded response",
    time: "Recently",
    icon: Brain,
  },
];

const scoringRanges = [
  { range: "1.0–2.4", label: "Lower", className: "range-lower" },
  { range: "2.5–3.5", label: "Middle", className: "range-middle" },
  { range: "3.6–5.0", label: "Higher", className: "range-higher" },
];

function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Brain size={25} />
          </div>
          <div>
            <h2>PersonaTwin</h2>
            <span>AI PERSONALITY PLATFORM</span>
          </div>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <nav className="navigation">
          <a className="nav-item active" href="#">
            <LayoutDashboard size={19} />
            Dashboard
          </a>
          <a className="nav-item" href="#profiles">
            <Users size={19} />
            Personality Profiles
          </a>
          <a className="nav-item" href="#assessments">
            <ClipboardCheck size={19} />
            Assessments
          </a>
          <a className="nav-item" href="#generation">
            <Sparkles size={19} />
            AI Generation
          </a>
          <a className="nav-item" href="#evaluation">
            <Activity size={19} />
            Evaluation Center
          </a>
          <a className="nav-item" href="#history">
            <FileText size={19} />
            History
          </a>
          <a className="nav-item" href="#methodology">
            <Scale size={19} />
            Methodology & Trust
          </a>
        </nav>

        <div className="sidebar-bottom">
          <div className="workspace-label">PREFERENCES</div>
          <a className="nav-item" href="#settings">
            <Settings size={19} />
            Settings
          </a>
          <a className="nav-item" href="#help">
            <CircleHelp size={19} />
            Help & Support
          </a>

          <div className="sidebar-user">
            <div className="avatar">PT</div>
            <div className="user-info">
              <strong>My Workspace</strong>
              <span>Personal account</span>
            </div>
            <ChevronDown size={16} />
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>Workspace</span>
            <span className="breadcrumb-separator">/</span>
            <strong>Dashboard</strong>
          </div>
          <div className="topbar-actions">
            <div className="api-status">
              <span className="status-dot" />
              API integration pending
            </div>
            <button className="icon-button" aria-label="Notifications">
              <Bell size={19} />
            </button>
            <div className="avatar top-avatar">PT</div>
          </div>
        </header>

        <div className="page-content">
          <section className="welcome-section">
            <div>
              <div className="eyebrow">
                <Sparkles size={15} />
                PERSONALITY INTELLIGENCE PLATFORM
              </div>
              <h1>Welcome to PersonaTwin AI</h1>
              <p>
                Build, understand, and interact with evidence-grounded
                digital personality profiles.
              </p>
            </div>
            <button className="primary-button">
              <Plus size={18} />
              Create new profile
            </button>
          </section>

          <section className="stats-grid">
            <StatCard
              icon={<Users size={21} />}
              label="Personality Profiles"
              value="0"
              description="Profiles created"
              color="blue"
            />
            <StatCard
              icon={<ClipboardCheck size={21} />}
              label="Assessments"
              value="0"
              description="Assessments completed"
              color="purple"
            />
            <StatCard
              icon={<Sparkles size={21} />}
              label="AI Generations"
              value="0"
              description="Responses generated"
              color="orange"
            />
            <StatCard
              icon={<ShieldCheck size={21} />}
              label="Evaluations"
              value="0"
              description="Evaluations completed"
              color="green"
            />
          </section>

          <section className="content-grid">
            <div className="panel getting-started">
              <div className="panel-heading">
                <div>
                  <h2>Get started</h2>
                  <p>Build your first digital personality profile.</p>
                </div>
                <span className="step-count">0 / 4</span>
              </div>

              <div className="progress-track">
                <div className="progress-fill" />
              </div>

              <div className="steps">
                <Step
                  number="01"
                  title="Record your consent"
                  description="Complete all three explicit consent agreements."
                  icon={<ShieldCheck size={19} />}
                />
                <Step
                  number="02"
                  title="Complete an assessment"
                  description="Provide evidence and correct answers when needed."
                  icon={<ClipboardCheck size={19} />}
                />
                <Step
                  number="03"
                  title="Create your profile"
                  description="Generate claims linked to their supporting answers."
                  icon={<Users size={19} />}
                />
                <Step
                  number="04"
                  title="Review, generate and evaluate"
                  description="Approve your profile and assess personality fidelity."
                  icon={<Brain size={19} />}
                />
              </div>

              <button className="secondary-button">
                Start building your profile
                <ArrowUpRight size={17} />
              </button>
            </div>

            <div className="panel quick-actions">
              <div className="panel-heading">
                <div>
                  <h2>Quick actions</h2>
                  <p>Access core platform capabilities.</p>
                </div>
                <Zap size={20} className="heading-icon" />
              </div>

              <QuickAction
                icon={<Users size={20} />}
                title="Create a profile"
                description="Build an evidence-grounded profile"
              />
              <QuickAction
                icon={<ClipboardCheck size={20} />}
                title="Start assessment"
                description="Submit and validate assessment evidence"
              />
              <QuickAction
                icon={<Sparkles size={20} />}
                title="Generate response"
                description="Interact with a digital twin"
              />
              <QuickAction
                icon={<Activity size={20} />}
                title="Run evaluation"
                description="Measure personality fidelity"
              />
            </div>
          </section>

          <section className="panel trust-overview" id="methodology">
            <div className="panel-heading">
              <div>
                <div className="section-eyebrow">
                  <ShieldCheck size={15} />
                  TRANSPARENCY & ACCOUNTABILITY
                </div>
                <h2>Methodology & Trust Framework</h2>
                <p>
                  Understand how PersonaTwin scores, validates, and protects
                  personality evidence.
                </p>
              </div>
              <span className="framework-label">Framework requirements</span>
            </div>

            <div className="trust-grid">
              <TrustCard
                icon={<Scale size={21} />}
                title="Transparent scoring"
                description="Inventory scores use reverse-keying, answered-item means, and explicit missing-answer rules."
                detail="Three or more skipped items make a domain unscored."
                color="blue"
              />
              <TrustCard
                icon={<FileCheck2 size={21} />}
                title="Evidence-linked claims"
                description="Every claim in me.md must cite the answer IDs supporting that claim."
                detail="Unanswered and test-question citations are rejected."
                color="purple"
              />
              <TrustCard
                icon={<LockKeyhole size={21} />}
                title="Consent and approval"
                description="Three explicit agreements are required before assessment answers load."
                detail="Profile download requires a passing claim check and user approval."
                color="green"
              />
              <TrustCard
                icon={<Activity size={21} />}
                title="Independent evaluation"
                description="Personality resemblance and profile consistency are evaluated separately."
                detail="Generic or overly polished writing is flagged."
                color="orange"
              />
            </div>
          </section>

          <section className="content-grid methodology-grid">
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Inventory scoring rules</h2>
                  <p>How assessment answers become domain scores.</p>
                </div>
                <Scale size={20} className="heading-icon" />
              </div>

              <div className="formula-card">
                <span className="formula-label">REVERSE-KEYED ITEM</span>
                <strong>Adjusted answer = 6 − answer</strong>
              </div>

              <div className="rule-list">
                <Rule
                  title="Domain score"
                  description="Mean of the answered items in that domain."
                />
                <Rule
                  title="One or two skipped items"
                  description="Score the remaining answers and display the answered-item count."
                />
                <Rule
                  title="Three or more skipped items"
                  description="Do not calculate a domain score."
                />
              </div>

              <div className="range-table">
                <h3>Score classifications</h3>
                {scoringRanges.map((item) => (
                  <div className="range-row" key={item.label}>
                    <strong>{item.range}</strong>
                    <span className={item.className}>{item.label}</span>
                  </div>
                ))}
              </div>
              <p className="method-note">
                Inventory scoring follows the Common Kit section 6 key.
              </p>
            </div>

            <div className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Personality fidelity judge</h2>
                  <p>Evaluation of generated responses.</p>
                </div>
                <Brain size={20} className="heading-icon" />
              </div>

              <div className="judge-scale">
                {[0, 1, 2, 3, 4].map((score) => (
                  <div className="judge-score" key={score}>
                    <strong>{score}</strong>
                    <span>{score === 0 ? "None" : score === 4 ? "Strong" : " "}</span>
                  </div>
                ))}
              </div>

              <div className="rule-list">
                <Rule
                  title="Judge output"
                  description="A score from 0 to 4, or INSUFFICIENT when evidence is inadequate."
                />
                <Rule
                  title="Different answer letter"
                  description="Cannot receive a score above 2."
                />
                <Rule
                  title="Same answer letter"
                  description="Cannot receive a score below 2."
                />
                <Rule
                  title="Separate consistency measure"
                  description="Profile consistency is scored independently of response resemblance."
                />
              </div>

              <div className="notice notice-warning">
                <AlertTriangle size={17} />
                <span>
                  Generic or excessively polished writing should be flagged
                  during evaluation.
                </span>
              </div>
            </div>
          </section>

          <section className="content-grid safeguards-grid">
            <div className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Consent and evidence safeguards</h2>
                  <p>Required controls throughout the profile lifecycle.</p>
                </div>
                <LockKeyhole size={20} className="heading-icon" />
              </div>

              <div className="safeguard-list">
                <Safeguard
                  title="Three explicit consent agreements"
                  description="No assessment answers load before all three agreements are given."
                />
                <Safeguard
                  title="Answer correction history"
                  description="People can correct answers, and corrections are recorded."
                />
                <Safeguard
                  title="Automatic claim validation"
                  description="Claims without answer IDs, or citing unanswered or test questions, fail validation."
                />
                <Safeguard
                  title="Human approval before download"
                  description="A passing claim check is not sufficient by itself. The person must also approve the profile."
                />
                <Safeguard
                  title="Test-question isolation"
                  description="Test questions are excluded from converter input."
                />
              </div>
            </div>

            <div className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Known limitations</h2>
                  <p>Important boundaries of the current methodology.</p>
                </div>
                <Info size={20} className="heading-icon" />
              </div>

              <div className="limitation-list">
                <Limitation
                  title="Writing-style analysis"
                  description="Simple counts measure length, greetings, and punctuation. They do not reliably capture humor, warmth, or word choice."
                />
                <Limitation
                  title="Choice detection"
                  description="The selected letter must appear at the beginning, such as B. or B). A sentence like “A call is best” is not interpreted as option A."
                />
                <Limitation
                  title="Limited situational evidence"
                  description="Only three scenarios and two messages contribute to the profile. Situational claims therefore rest on limited evidence."
                />
                <Limitation
                  title="Citation is not proof of fairness"
                  description="A claim check confirms that a source is cited, not that the wording is fair. The person must still read and review the profile."
                />
              </div>
            </div>
          </section>

          <section className="notice notice-info transparency-notice">
            <Info size={19} />
            <div>
              <strong>Evidence transparency matters</strong>
              <p>
                A cited claim is not automatically a fair or accurate claim.
                PersonaTwin profiles should remain reviewable, correctable,
                and subject to the person's approval.
              </p>
            </div>
          </section>

          <section className="panel activity-panel">
            <div className="panel-heading">
              <div>
                <h2>Recent activity</h2>
                <p>Your latest platform operations.</p>
              </div>
              <button className="text-button">View all</button>
            </div>

            <div className="activity-list">
              {activities.map((activity) => {
                const Icon = activity.icon;
                return (
                  <div className="activity-row" key={activity.title}>
                    <div className="activity-icon">
                      <Icon size={19} />
                    </div>
                    <div className="activity-description">
                      <strong>{activity.title}</strong>
                      <span>{activity.detail}</span>
                    </div>
                    <span className="activity-time">{activity.time}</span>
                  </div>
                );
              })}
            </div>
          </section>

          <footer className="footer">
            <span>PersonaTwin AI · Version 1.0.0</span>
            <span>
              Evidence-grounded portable digital personality profiles
            </span>
          </footer>
        </div>
      </main>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  description,
  color,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  description: string;
  color: string;
}) {
  return (
    <div className="stat-card">
      <div className={`stat-icon ${color}`}>{icon}</div>
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      <span className="stat-description">{description}</span>
    </div>
  );
}

function Step({
  number,
  title,
  description,
  icon,
}: {
  number: string;
  title: string;
  description: string;
  icon: ReactNode;
}) {
  return (
    <div className="step-row">
      <span className="step-number">{number}</span>
      <div className="step-icon">{icon}</div>
      <div className="step-text">
        <strong>{title}</strong>
        <span>{description}</span>
      </div>
      <div className="step-indicator">
        <span />
      </div>
    </div>
  );
}

function QuickAction({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {
  return (
    <button className="quick-action">
      <div className="quick-action-icon">{icon}</div>
      <div className="quick-action-text">
        <strong>{title}</strong>
        <span>{description}</span>
      </div>
      <ArrowUpRight size={17} className="action-arrow" />
    </button>
  );
}

function TrustCard({
  icon,
  title,
  description,
  detail,
  color,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  detail: string;
  color: string;
}) {
  return (
    <div className="trust-card">
      <div className={`trust-icon ${color}`}>{icon}</div>
      <div>
        <h3>{title}</h3>
        <p>{description}</p>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function Rule({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rule-item">
      <CheckCircle2 size={16} />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}

function Safeguard({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="safeguard-item">
      <ShieldCheck size={18} />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}

function Limitation({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="limitation-item">
      <AlertTriangle size={17} />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default App;
