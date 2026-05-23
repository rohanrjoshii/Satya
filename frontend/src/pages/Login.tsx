import React from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const navigate = useNavigate();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [signupMode, setSignupMode] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  const login = async () => {
    setLoading(true);
    setError(null);
    try {
      const body = new URLSearchParams();
      body.append("grant_type", "password");
      body.append("username", username);
      body.append("password", password);

      const res = await axios.post("/api/auth/token", body, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      setToken(res.data.access_token);
      navigate("/map");
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? "Login failed";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  const signup = async () => {
    setLoading(true);
    setError(null);
    try {
      await axios.post("/api/auth/signup", { username, password }, { headers: { "Content-Type": "application/json" } });
      setSignupMode(false);
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? "Signup failed";
      setError(String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-5">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold">{signupMode ? "Create account" : "Login"}</h1>
        <p className="text-sm text-muted-foreground">
          Earn watch-time points by watching approved street videos.
        </p>
      </div>

      <div className="space-y-3">
        <label className="text-sm font-medium">Username</label>
        <Input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="yourname" />

        <label className="text-sm font-medium">Password</label>
        <Input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />

        {error && <div className="text-sm text-destructive">{error}</div>}

        <Button className="w-full" disabled={loading || !username || !password} onClick={signupMode ? signup : login}>
          {loading ? "Working..." : signupMode ? "Sign up" : "Login"}
        </Button>

        <div className="pt-2 text-sm text-muted-foreground text-center">
          {signupMode ? (
            <button className="underline" onClick={() => setSignupMode(false)}>
              I already have an account
            </button>
          ) : (
            <button className="underline" onClick={() => setSignupMode(true)}>
              Create an account
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

