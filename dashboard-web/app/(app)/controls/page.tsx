import { ControlButtons } from "./ControlButtons";

export default function Controls() {
  const configured = !!process.env.GH_PAT && !!process.env.GH_REPO;
  return (
    <>
      <h1>Controls</h1>
      <p className="sub">Trigger any pipeline job on demand. The crons still run automatically.</p>
      {configured ? (
        <ControlButtons />
      ) : (
        <div className="card">
          <p className="muted">
            Manual triggers are disabled. Set <code>GH_PAT</code> (a GitHub token with the
            <code> workflow</code> scope) and <code>GH_REPO</code> in your environment variables to enable them.
          </p>
        </div>
      )}
    </>
  );
}
