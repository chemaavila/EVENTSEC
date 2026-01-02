import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createUser,
  listUsers,
  type UserCreatePayload,
  type UserProfile,
} from "../../services/api";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "../../components/common/ToastProvider";
import { EmptyState } from "../../components/common/EmptyState";
import { ErrorState } from "../../components/common/ErrorState";
import { LoadingState } from "../../components/common/LoadingState";

const emptyForm: UserCreatePayload = {
  full_name: "",
  email: "",
  password: "",
  role: "analyst",
  team: "",
  manager: "",
  computer: "",
  mobile_phone: "",
  timezone: "UTC",
};

const roles = [
  { value: "admin", label: "Admin" },
  { value: "team_lead", label: "Team lead" },
  { value: "senior_analyst", label: "Senior analyst" },
  { value: "analyst", label: "Analyst" },
];

const UserManagementPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<UserCreatePayload>(emptyForm);
  const [creating, setCreating] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const { pushToast } = useToast();

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await listUsers();
      setUsers(data);
      if (!selectedUserId && data.length > 0) {
        setSelectedUserId(data[0].id);
      }
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unexpected error while loading users"
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const stats = useMemo(() => {
    const total = users.length;
    const admins = users.filter((u) => u.role === "admin").length;
    const analysts = users.filter((u) => u.role === "analyst").length;
    const teamLeads = users.filter((u) => u.role === "team_lead").length;
    return { total, admins, analysts, teamLeads };
  }, [users]);

  const selectedUser =
    users.find((u) => u.id === selectedUserId) ?? (users.length > 0 ? users[0] : null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleCreate = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      setCreating(true);
      await createUser({
        ...form,
        team: form.team && form.team.trim() ? form.team.trim() : null,
        manager: form.manager && form.manager.trim() ? form.manager.trim() : null,
        computer: form.computer && form.computer.trim() ? form.computer.trim() : null,
        mobile_phone:
          form.mobile_phone && form.mobile_phone.trim()
            ? form.mobile_phone.trim()
            : null,
      });
      setForm(emptyForm);
      await loadUsers();
    } catch (err) {
      const details = err instanceof Error ? err.message : "Unexpected error";
      pushToast({
        title: "Failed to create user",
        message: "Please review the details and try again.",
        details,
        variant: "error",
      });
    } finally {
      setCreating(false);
    }
  };

  if (user && user.role !== "admin") {
    return (
      <div className="page-root">
        <div className="card">
          <div className="card-title">Insufficient permissions</div>
          <div className="card-subtitle">
            You need to be an administrator to access user management.
          </div>
          <div className="stack-horizontal" style={{ marginTop: "1rem" }}>
            <button type="button" className="btn" onClick={() => navigate("/")}>
              Return to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page-root">
      <div className="page-header">
        <div className="page-title-group">
          <div className="page-title">User management</div>
          <div className="page-subtitle">
            Monitor and manage SOC accounts, roles and access.
          </div>
        </div>
        <div className="stack-horizontal">
          <button type="button" className="btn btn-ghost" onClick={loadUsers}>
            Refresh
          </button>
        </div>
      </div>

      <div className="grid-3">
        <div className="card">
          <div className="card-subtitle">Total users</div>
          <div className="card-value">{stats.total}</div>
        </div>
        <div className="card">
          <div className="card-subtitle">Admins</div>
          <div className="card-value">{stats.admins}</div>
        </div>
        <div className="card">
          <div className="card-subtitle">Team leads</div>
          <div className="card-value">{stats.teamLeads}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Directory</div>
              <div className="card-subtitle">
                Active SOC users and their assigned roles.
              </div>
            </div>
          </div>
          {loading && <LoadingState message="Loading users…" />}
          {error && (
            <ErrorState
              message="Failed to load users."
              details={error}
              onRetry={() => loadUsers()}
            />
          )}
          {!loading && !error && users.length === 0 && (
            <EmptyState
              title="No users yet"
              message="Create the first SOC account to get started."
            />
          )}
          {!loading && !error && users.length > 0 && (
            <div className="stack-vertical">
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Role</th>
                      <th>Team</th>
                      <th>Email</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map((u) => (
                      <tr
                        key={u.id}
                        className={selectedUserId === u.id ? "table-row-active" : ""}
                        onClick={() => setSelectedUserId(u.id)}
                      >
                        <td>{u.full_name}</td>
                        <td>{u.role.replace("_", " ")}</td>
                        <td>{u.team || "—"}</td>
                        <td>{u.email}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Create new user</div>
              <div className="card-subtitle">
                Provision analyst accounts with proper role and context.
              </div>
            </div>
          </div>

          <form className="stack-vertical" onSubmit={handleCreate}>
            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="full_name" className="field-label">
                  Full name
                </label>
                <input
                  id="full_name"
                  name="full_name"
                  className="field-control"
                  value={form.full_name}
                  onChange={handleChange}
                  required
                />
              </div>
              <div className="field-group">
                <label htmlFor="email" className="field-label">
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  className="field-control"
                  value={form.email}
                  onChange={handleChange}
                  required
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="role" className="field-label">
                  Role
                </label>
                <select
                  id="role"
                  name="role"
                  className="field-control"
                  value={form.role}
                  onChange={handleChange}
                >
                  {roles.map((r) => (
                    <option value={r.value} key={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field-group">
                <label htmlFor="password" className="field-label">
                  Temporary password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  className="field-control"
                  value={form.password}
                  onChange={handleChange}
                  required
                  placeholder="Minimum 8 characters"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="team" className="field-label">
                  Team
                </label>
                <input
                  id="team"
                  name="team"
                  className="field-control"
                  value={form.team ?? ""}
                  onChange={handleChange}
                  placeholder="SOC team name"
                />
              </div>
              <div className="field-group">
                <label htmlFor="manager" className="field-label">
                  Manager
                </label>
                <input
                  id="manager"
                  name="manager"
                  className="field-control"
                  value={form.manager ?? ""}
                  onChange={handleChange}
                  placeholder="Direct manager"
                />
              </div>
            </div>

            <div className="grid-2">
              <div className="field-group">
                <label htmlFor="computer" className="field-label">
                  Computer
                </label>
                <input
                  id="computer"
                  name="computer"
                  className="field-control"
                  value={form.computer ?? ""}
                  onChange={handleChange}
                  placeholder="Hostname"
                />
              </div>
              <div className="field-group">
                <label htmlFor="mobile_phone" className="field-label">
                  Mobile phone
                </label>
                <input
                  id="mobile_phone"
                  name="mobile_phone"
                  className="field-control"
                  value={form.mobile_phone ?? ""}
                  onChange={handleChange}
                  placeholder="+00 000 000 000"
                />
              </div>
            </div>

            <div className="field-group">
              <label htmlFor="timezone" className="field-label">
                Timezone
              </label>
              <input
                id="timezone"
                name="timezone"
                className="field-control"
                value={form.timezone ?? ""}
                onChange={handleChange}
                placeholder="UTC, Europe/Madrid…"
              />
            </div>

            <div className="stack-horizontal" style={{ justifyContent: "flex-end" }}>
              <button type="submit" className="btn btn-sm" disabled={creating}>
                {creating ? "Creating…" : "Create user"}
              </button>
            </div>
          </form>
        </div>
      </div>

      {selectedUser && (
        <div className="card">
          <div className="card-header">
            <div>
              <div className="card-title">Profile overview</div>
              <div className="card-subtitle">
                Connection details and assigned assets.
              </div>
            </div>
          </div>
          <div className="grid-2">
            <div className="stack-vertical">
              <div className="field-group">
                <div className="field-label">Full name</div>
                <div>{selectedUser.full_name}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Role</div>
                <div className="stack-horizontal">
                  <span className="tag">{selectedUser.role.replace("_", " ")}</span>
                  {selectedUser.team && <span className="tag">{selectedUser.team}</span>}
                </div>
              </div>
              <div className="field-group">
                <div className="field-label">Email</div>
                <div>{selectedUser.email}</div>
              </div>
            </div>

            <div className="stack-vertical">
              <div className="field-group">
                <div className="field-label">Manager</div>
                <div>{selectedUser.manager || "—"}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Computer</div>
                <div>{selectedUser.computer || "—"}</div>
              </div>
              <div className="field-group">
                <div className="field-label">Mobile phone</div>
                <div>{selectedUser.mobile_phone || "—"}</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementPage;
