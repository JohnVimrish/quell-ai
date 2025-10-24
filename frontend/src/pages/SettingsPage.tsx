import { useEffect, useState } from "react";
import type { FormEvent } from "react";

type SettingsState = {
  ai_mode_enabled: boolean;
  auto_join_meetings: boolean;
  auto_reply_chats: boolean;
  voice_clone_enabled: boolean;
  disclose_voice_clone: boolean;
  data_retention_days: number;
  transcript_auto_delete_days: number;
};

const defaultState: SettingsState = {
  ai_mode_enabled: false,
  auto_join_meetings: false,
  auto_reply_chats: false,
  voice_clone_enabled: false,
  disclose_voice_clone: true,
  data_retention_days: 30,
  transcript_auto_delete_days: 90,
};

export default function SettingsPage() {
  const [settings, setSettings] = useState<SettingsState>(defaultState);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadSettings() {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("/api/settings", { credentials: "include" });
        if (!response.ok) {
          throw new Error(`request failed: ${response.status}`);
        }
        const payload = (await response.json()) as SettingsState;
        if (isMounted) {
          setSettings({ ...defaultState, ...payload });
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : "unknown error");
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    loadSettings();
    return () => {
      isMounted = false;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const response = await fetch("/api/settings", {
        method: "PUT",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
      });
      if (!response.ok) {
        throw new Error(`request failed: ${response.status}`);
      }
      const payload = (await response.json()) as SettingsState;
      setSettings({ ...defaultState, ...payload });
      setSavedAt(new Date().toLocaleTimeString());
    } catch (err) {
      setError(err instanceof Error ? err.message : "unknown error");
    } finally {
      setSaving(false);
    }
  }

  function updateSetting<K extends keyof SettingsState>(key: K, value: SettingsState[K]) {
    setSettings((prev) => ({ ...prev, [key]: value }));
  }

  return (
    <div className="section-padding">
      <div className="glass-panel" style={{ padding: "48px", marginBottom: "32px" }}>
        <h1
          style={{
            fontSize: "clamp(2.5rem, 4vw, 3rem)",
            fontWeight: 800,
            margin: "0 0 16px",
            background: "var(--gradient-orange-green)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          Settings
        </h1>
        <p style={{ color: "var(--color-grey-600)", fontSize: "1.15rem", margin: 0 }}>
          Configure what the AI can handle, when it should disclose itself, and how long data sticks around.
        </p>
      </div>

      <form className="glass-panel" style={{ padding: "40px" }} onSubmit={handleSubmit}>
        {loading ? (
          <p>Loading settings...</p>
        ) : (
          <div style={{ display: "grid", gap: "32px", maxWidth: "820px" }}>
            <section>
              <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>Assistant coverage</h3>
              <ToggleRow
                label="Enable AI across channels"
                description="When on, the delegate can pick up calls, attend meetings, and answer chat while you are away."
                checked={settings.ai_mode_enabled}
                onChange={(val) => updateSetting("ai_mode_enabled", val)}
              />
              <ToggleRow
                label="Auto-join Zoom/Teams when busy"
                description="The assistant will join scheduled meetings when your calendar says busy or out of office."
                checked={settings.auto_join_meetings}
                onChange={(val) => updateSetting("auto_join_meetings", val)}
              />
              <ToggleRow
                label="Auto-reply in Slack/Teams chat"
                description="Respond on your behalf while you are offline, respecting important contact overrides."
                checked={settings.auto_reply_chats}
                onChange={(val) => updateSetting("auto_reply_chats", val)}
              />
            </section>

            <section>
              <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>Voice and transparency</h3>
              <ToggleRow
                label="Enable voice clone"
                description="Allow the assistant to speak in your voice during calls and meetings."
                checked={settings.voice_clone_enabled}
                onChange={(val) => updateSetting("voice_clone_enabled", val)}
              />
              <ToggleRow
                label="Require disclosure before speaking"
                description="Play an announcement before the clone voice introduces itself to new participants."
                checked={settings.disclose_voice_clone}
                onChange={(val) => updateSetting("disclose_voice_clone", val)}
                disabled={!settings.voice_clone_enabled}
              />
            </section>

            <section>
              <h3 style={{ marginBottom: "20px", color: "var(--color-grey-900)" }}>Data retention</h3>
              <div className="placeholder-card">
                <label style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <span>Auto-delete documents after (days)</span>
                  <input
                    type="number"
                    min={7}
                    value={settings.data_retention_days}
                    onChange={(event) => updateSetting("data_retention_days", Number(event.target.value) || 0)}
                    className="input"
                  />
                </label>
                <label style={{ display: "flex", flexDirection: "column", gap: "8px", marginTop: "16px" }}>
                  <span>Auto-delete transcripts after (days)</span>
                  <input
                    type="number"
                    min={14}
                    value={settings.transcript_auto_delete_days}
                    onChange={(event) => updateSetting("transcript_auto_delete_days", Number(event.target.value) || 0)}
                    className="input"
                  />
                </label>
              </div>
            </section>

            {error && (
              <p role="alert" style={{ color: "var(--color-orange-500)" }}>
                {error}
              </p>
            )}
            {savedAt && !error && (
              <p style={{ color: "var(--color-grey-600)" }}>Saved at {savedAt}</p>
            )}

            <div>
              <button type="submit" className="primary-button" disabled={saving}>
                {saving ? "Saving..." : "Save settings"}
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}

type ToggleRowProps = {
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
};

function ToggleRow({ label, description, checked, onChange, disabled }: ToggleRowProps) {
  return (
    <div className="placeholder-card" style={{ opacity: disabled ? 0.6 : 1 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h4 style={{ margin: "0 0 8px", color: "var(--color-grey-900)" }}>{label}</h4>
          <p style={{ margin: 0, color: "var(--color-grey-600)", fontSize: "0.95rem" }}>{description}</p>
        </div>
        <label style={{ position: "relative", display: "inline-block", width: "60px", height: "34px" }}>
          <input
            type="checkbox"
            checked={checked}
            disabled={disabled}
            onChange={(event) => onChange(event.target.checked)}
            style={{ opacity: 0, width: 0, height: 0 }}
          />
          <span
            style={{
              position: "absolute",
              cursor: disabled ? "not-allowed" : "pointer",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: checked ? "var(--color-green-500)" : "var(--color-grey-300)",
              transition: "0.4s",
              borderRadius: "34px",
            }}
          >
            <span
              style={{
                position: "absolute",
                height: "26px",
                width: "26px",
                left: checked ? "30px" : "4px",
                bottom: "4px",
                background: "white",
                transition: "0.4s",
                borderRadius: "50%",
              }}
            />
          </span>
        </label>
      </div>
    </div>
  );
}


