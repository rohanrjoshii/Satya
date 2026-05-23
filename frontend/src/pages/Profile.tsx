import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { clearToken } from "@/lib/auth";

export default function ProfilePage() {
  const navigate = useNavigate();
  const token = getToken();

  const [loading, setLoading] = React.useState(true);
  const [me, setMe] = React.useState<{ id: number; username: string; is_admin: boolean } | null>(null);
  const [points, setPoints] = React.useState<number>(0);
  const [level, setLevel] = React.useState<string>("");
  const [watchedTodaySeconds, setWatchedTodaySeconds] = React.useState<number>(0);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    void (async () => {
      setLoading(true);
      setError(null);
      try {
        const [meRes, ptsRes] = await Promise.all([api.get("/api/me"), api.get("/api/me/points")]);
        setMe(meRes.data);
        setPoints(ptsRes.data.points);
        setLevel(ptsRes.data.level);
        setWatchedTodaySeconds(ptsRes.data.watched_today_seconds);
      } catch (e: any) {
        setError(e?.response?.data?.detail ?? "Failed to load profile");
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

  const logout = () => {
    clearToken();
    navigate("/map");
  };

  if (!token) {
    return (
      <div className="max-w-md mx-auto space-y-3">
        <h1 className="text-2xl font-bold">Profile</h1>
        <div className="text-sm text-muted-foreground">
          Login required.
        </div>
        <Button onClick={() => navigate("/login")}>Go to Login</Button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Profile</h1>
        <Button variant="outline" onClick={logout}>Logout</Button>
      </div>

      {loading ? (
        <div className="text-sm text-muted-foreground">Loading...</div>
      ) : error ? (
        <div className="text-sm text-destructive">{error}</div>
      ) : (
        <>
          <div className="rounded-lg border border-border/60 p-4 space-y-2">
            <div className="text-sm text-muted-foreground">User</div>
            <div className="text-lg font-medium">{me?.username ? `@${me.username}` : "-"}</div>

            <div className="pt-3 text-sm text-muted-foreground">Your level</div>
            <div className="text-xl font-bold">{level}</div>

            <div className="pt-3 text-sm text-muted-foreground">Total points</div>
            <div className="text-3xl font-extrabold">{points.toFixed(2)}</div>

            <div className="pt-3 text-sm text-muted-foreground">Watched today</div>
            <div className="text-lg font-medium">{(watchedTodaySeconds / 60).toFixed(1)} min</div>
          </div>
        </>
      )}
    </div>
  );
}

