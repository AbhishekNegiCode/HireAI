import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Sparkles, Check } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Button, Field, ErrorState } from "../components/UI";
import { errorMessage } from "../services/api";
export default function Auth({ register = false }) {
  const { authenticate } = useAuth(),
    navigate = useNavigate(),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await authenticate(register ? "register" : "login", values);
      navigate("/");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="auth-page">
      <div className="auth-story">
        <Link to="/" className="brand">
          <span className="brand-mark">
            h<span>✦</span>
          </span>
          hire<span className="brand-ai">AI</span>
        </Link>
        <div>
          <span className="eyebrow">
            <Sparkles size={16} /> A MORE HUMAN WAY TO GET HIRED
          </span>
          <h1>
            Your experience.
            <br />
            Your ambitions.
            <br />
            <em>Your next chapter.</em>
          </h1>
          <p>
            Find work that fits who you are—and where you want to go. Thoughtful
            AI matches, built around you.
          </p>
          <div className="auth-benefits">
            {[
              "Opportunities that match your skills",
              "Clear insights from your resume",
              "Every application, all in one place",
            ].map((t) => (
              <span key={t}>
                <Check size={17} />
                {t}
              </span>
            ))}
          </div>
        </div>
        <small>Good careers begin with the right connection.</small>
      </div>
      <div className="auth-form-wrap">
        <form onSubmit={submit} className="auth-form">
          <span className="eyebrow">WELCOME TO HIREAI</span>
          <h2>
            {register ? "Make your next move." : "Good to see you again."}
          </h2>
          <p>
            {register
              ? "Create your account and start a new chapter."
              : "Sign in to pick up where you left off."}
          </p>
          {error && <ErrorState message={error} />}
          <div className="form-stack">
            {register && (
              <Field
                label="Full name"
                name="full_name"
                required
                autoComplete="name"
              />
            )}
            <Field
              label="Email address"
              name="email"
              type="email"
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
            <Field
              label="Password"
              name="password"
              type="password"
              minLength={register ? 10 : undefined}
              required
              autoComplete={register ? "new-password" : "current-password"}
            />
            {register && (
              <>
                <Field
                  label="Confirm password"
                  name="confirm_password"
                  type="password"
                  required
                  autoComplete="new-password"
                />
                <Field label="I’m here to">
                  <select name="role">
                    <option value="candidate">Find my next role</option>
                    <option value="recruiter">Hire great people</option>
                  </select>
                </Field>
              </>
            )}
            <Button loading={busy} type="submit">
              {register ? "Create account" : "Sign in"}
              <ArrowRight size={17} />
            </Button>
          </div>
          <p className="auth-switch">
            {register ? "Already have an account?" : "New to HireAI?"}{" "}
            <Link to={register ? "/login" : "/register"}>
              {register ? "Sign in" : "Create an account"}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
