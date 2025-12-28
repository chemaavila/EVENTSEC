import { useEffect, useState } from "react";
import type { UserProfile } from "../../services/api";
import { getMyProfile } from "../../services/api";

const ProfilePage = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const run = async () => {
      try {
        const data = await getMyProfile();
        setProfile(data);
        setError(null);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Unexpected error while loading profile"
        );
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">User profile</div>
          <div className="page-subtitle">
            Basic information for the currently authenticated analyst.
          </div>
        </div>
      </div>

      <div className="card">
        {loading && <div className="muted">Loading profile…</div>}
        {error && (
          <div className="muted">
            Failed to load profile:
            {" "}
            {error}
          </div>
        )}
        {!loading && !error && profile && (
          <div className="grid-2">
            <div className="stack-vertical">
              <div className="stack-horizontal">
                <div className="topbar-user-avatar">
                  {profile.full_name
                    .split(" ")
                    .map((p) => p[0])
                    .join("")
                    .slice(0, 2)
                    .toUpperCase()}
                </div>
                <div className="topbar-user-text">
                  <div className="topbar-user-name">{profile.full_name}</div>
                  <div className="topbar-user-role">{profile.role}</div>
                </div>
              </div>

              <div className="field-group">
                <div className="field-label">Email</div>
                <div>{profile.email}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Name</div>
                <div className="muted">
                  {profile.full_name.split(" ").slice(0, -1).join(" ") || profile.full_name}
                </div>
              </div>
              <div className="field-group">
                <div className="field-label">Surname</div>
                <div className="muted">
                  {profile.full_name.split(" ").slice(-1).join(" ") || profile.full_name}
                </div>
              </div>
            </div>

            <div className="stack-vertical">
              <div className="field-group">
                <div className="field-label">Timezone</div>
                <div className="muted">{profile.timezone}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Team</div>
                <div>{profile.team ?? "—"}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Manager</div>
                <div>{profile.manager ?? "—"}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Computer</div>
                <div>{profile.computer ?? "—"}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Mobile phone</div>
                <div>{profile.mobile_phone ?? "—"}</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProfilePage;
