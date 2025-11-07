import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import FloatingOrbs from "../components/FloatingOrbs";
import { useAuth } from "../components/AuthProvider";
import NavBar from "../components/NavBar";
import { ensurePublicTheme } from "../utils/publicTheme";
import type { FormEvent } from "react";

function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    ensurePublicTheme();
  }, []);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    let succeeded = false;
    let redirectUrl: string | undefined;

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      const data: any = await response.json().catch(() => ({}));
      if (!response.ok || (data && typeof data.error === "string")) {
        const message =
          data && typeof data.error === "string"
            ? data.error
            : "Login failed. Please check your credentials and try again.";
        setError(message);
        return;
      }

      if (data && typeof data.redirect_url === "string") {
        redirectUrl = data.redirect_url as string;
      }

      succeeded = true;
    } catch (fetchError) {
      setError("Unable to reach the server. Please try again.");
    } finally {
      setIsSubmitting(false);
    }

    if (succeeded) {
      login(redirectUrl);
    }
  };

  return (
    <div className="bg-light-background font-sans text-dark-text antialiased">
      <div className="relative min-h-screen w-full overflow-x-hidden">
        <FloatingOrbs />
        <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <NavBar />
          <main className="flex justify-center py-24">
            <div className="w-full max-w-xl rounded-xl border border-border-grey bg-white/80 p-8 shadow-xl backdrop-blur-md sm:p-12">
              <div className="text-center">
                <h1 className="font-serif text-4xl font-bold text-dark-text">Welcome Back</h1>
                <p className="mt-3 text-base text-light-text">Sign in to continue your Quell AI journey.</p>
              </div>

              <form className="mt-10 space-y-6" onSubmit={handleSubmit}>
                <div className="text-left">
                  <label htmlFor="email" className="block text-sm font-semibold text-dark-text">
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                    placeholder="you@example.com"
                  />
                </div>

                <div className="text-left">
                  <label htmlFor="password" className="block text-sm font-semibold text-dark-text">
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                    placeholder="********"
                  />
                </div>

                {error && (
                  <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={cn(
                    "mt-4 flex h-12 w-full cursor-pointer items-center justify-center rounded-md border border-primary-blue/30 bg-primary-blue text-base font-bold text-white shadow-lg shadow-primary-blue/20 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                    isSubmitting ? "opacity-70" : "hover:scale-105 hover:bg-hover-blue"
                  )}
                >
                  {isSubmitting ? "Signing In..." : "Sign In"}
                </button>
              </form>

              <div className="mt-8 text-center text-sm text-light-text">
                <span>Don't have an account?</span>{" "}
                <button
                  type="button"
                  className="font-semibold text-primary-blue transition-colors hover:text-hover-blue"
                  onClick={() => navigate("/signup")}
                >
                  Create one
                </button>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

