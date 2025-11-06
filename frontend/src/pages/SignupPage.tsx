import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import FloatingOrbs from "../components/FloatingOrbs";
import { useAuth } from "../components/AuthProvider";
import { ensurePublicTheme } from "../utils/publicTheme";
import type { ChangeEvent, FormEvent } from "react";

function cn(...parts: Array<string | false | null | undefined>) {
  return parts.filter(Boolean).join(" ");
}

export default function SignupPage() {
  const { login, engage } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    password: "",
    confirmPassword: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeNav, setActiveNav] = useState<"about" | "lab">("about");

  useEffect(() => {
    ensurePublicTheme();
  }, []);

  const handleNavClick = (target: "about" | "lab") => {
    setActiveNav(target);
    if (target === "about") {
      navigate("/");
    } else {
      navigate("/labs/dev-playground");
    }
  };

  const handleChange = (field: keyof typeof form) => (event: ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: event.target.value }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) return;

    if (form.password !== form.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    let succeeded = false;
    let redirectUrl: string | undefined;

    try {
      const response = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: form.name.trim(),
          email: form.email.trim(),
          phone: form.phone.trim() || undefined,
          password: form.password,
        }),
      });

      const data: any = await response.json().catch(() => ({}));
      if (!response.ok || (data && typeof data.error === "string")) {
        const message =
          data && typeof data.error === "string"
            ? data.error
            : "Signup failed. Please try again.";
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
          <header className="sticky top-6 z-50 mt-6 grid h-16 grid-cols-3 items-center rounded-lg border border-border-grey bg-light-background/90 px-4 shadow-md backdrop-blur-md sm:px-6">
            <div className="flex items-center gap-3 justify-self-start">
              <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary-blue/10 text-primary-blue">
                <svg className="h-6 w-6" fill="none" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                  <path d="M24 4C25.7818 14.2173 33.7827 22.2182 44 24C33.7827 25.7818 25.7818 33.7827 24 44C22.2182 33.7827 14.2173 25.7818 4 24C14.2173 22.2182 22.2182 14.2173 24 4Z" fill="currentColor" />
                </svg>
              </div>
              <button type="button" className="hidden text-xl font-bold text-dark-text sm:block" onClick={() => navigate("/")}>Quell AI</button>
            </div>
            <nav className="hidden items-center justify-center gap-2 justify-self-center md:flex">
              <button
                type="button"
                className={cn(
                  "nav-3d rounded-md px-4 py-2 text-sm font-semibold text-light-text transition-all hover:bg-primary-blue/10 hover:text-primary-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                  activeNav === "about" && "active-nav"
                )}
                aria-current={activeNav === "about" ? "page" : undefined}
                onClick={() => handleNavClick("about")}
              >
                About
              </button>
              <button
                type="button"
                className={cn(
                  "nav-3d rounded-md px-4 py-2 text-sm font-semibold text-light-text transition-all hover:bg-primary-blue/10 hover:text-primary-blue focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-blue/50",
                  activeNav === "lab" && "active-nav"
                )}
                aria-current={activeNav === "lab" ? "page" : undefined}
                onClick={() => handleNavClick("lab")}
              >
                Conversation Lab
              </button>
            </nav>
            <div className="flex items-center gap-3 justify-self-end">
              <button
                type="button"
                className="btn-3d hidden h-10 cursor-pointer items-center justify-center rounded-md border border-primary-blue/30 bg-white/80 px-5 text-sm font-bold text-dark-text shadow-lg hover:bg-primary-blue/10 hover:text-primary-blue sm:flex"
                onClick={() => navigate("/login")}
              >
                Log In
              </button>
              <button
                type="button"
                className="flex h-10 min-w-[108px] cursor-pointer items-center justify-center overflow-hidden rounded-md border border-primary-blue/30 bg-primary-blue px-5 text-sm font-bold text-white shadow-lg shadow-primary-blue/20 transition-all hover:scale-105 hover:bg-hover-blue"
                onClick={() => engage()}
              >
                Access Portal
              </button>
            </div>
          </header>

          <main className="flex justify-center py-24">
            <div className="w-full max-w-2xl rounded-xl border border-border-grey bg-white/80 p-8 shadow-xl backdrop-blur-md sm:p-12">
              <div className="text-center">
                <h1 className="font-serif text-4xl font-bold text-dark-text">Create your account</h1>
                <p className="mt-3 text-base text-light-text">Join Quell AI to orchestrate every conversation with precision.</p>
              </div>

              <form className="mt-10 space-y-6" onSubmit={handleSubmit}>
                <div className="text-left">
                  <label htmlFor="name" className="block text-sm font-semibold text-dark-text">
                    Full Name
                  </label>
                  <input
                    id="name"
                    type="text"
                    autoComplete="name"
                    required
                    value={form.name}
                    onChange={handleChange("name")}
                    className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                    placeholder="Ada Lovelace"
                  />
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                  <div className="text-left">
                    <label htmlFor="email" className="block text-sm font-semibold text-dark-text">
                      Email Address
                    </label>
                    <input
                      id="email"
                      type="email"
                      autoComplete="email"
                      required
                      value={form.email}
                      onChange={handleChange("email")}
                      className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                      placeholder="you@example.com"
                    />
                  </div>
                  <div className="text-left">
                    <label htmlFor="phone" className="block text-sm font-semibold text-dark-text">
                      Phone Number <span className="font-normal text-light-text">(optional)</span>
                    </label>
                    <input
                      id="phone"
                      type="tel"
                      inputMode="tel"
                      autoComplete="tel"
                      value={form.phone}
                      onChange={handleChange("phone")}
                      className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                      placeholder="(555) 123-4567"
                    />
                  </div>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                  <div className="text-left">
                    <label htmlFor="password" className="block text-sm font-semibold text-dark-text">
                      Password
                    </label>
                    <input
                      id="password"
                      type="password"
                      autoComplete="new-password"
                      required
                      minLength={8}
                      value={form.password}
                      onChange={handleChange("password")}
                      className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                      placeholder="At least 8 characters"
                    />
                  </div>
                  <div className="text-left">
                    <label htmlFor="confirmPassword" className="block text-sm font-semibold text-dark-text">
                      Confirm Password
                    </label>
                    <input
                      id="confirmPassword"
                      type="password"
                      autoComplete="new-password"
                      required
                      value={form.confirmPassword}
                      onChange={handleChange("confirmPassword")}
                      className="mt-2 w-full rounded-md border border-border-grey bg-white/80 px-4 py-3 text-dark-text placeholder:text-light-text focus:border-primary-blue focus:outline-none focus:ring-2 focus:ring-primary-blue/40"
                      placeholder="Repeat your password"
                    />
                  </div>
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
                  {isSubmitting ? "Creating Account..." : "Create Account"}
                </button>
              </form>

              <div className="mt-8 text-center text-sm text-light-text">
                <span>Already have an account?</span>{" "}
                <button
                  type="button"
                  className="font-semibold text-primary-blue transition-colors hover:text-hover-blue"
                  onClick={() => navigate("/login")}
                >
                  Log in instead
                </button>
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

