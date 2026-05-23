import React from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";

export default function UploadPage() {
  const navigate = useNavigate();
  const token = getToken();

  const [file, setFile] = React.useState<File | null>(null);
  const [lat, setLat] = React.useState<number | null>(null);
  const [lng, setLng] = React.useState<number | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [status, setStatus] = React.useState<string | null>(null);

  const requestLocation = async () => {
    setStatus(null);
    if (!navigator.geolocation) {
      setStatus("Geolocation not available in this browser.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLat(pos.coords.latitude);
        setLng(pos.coords.longitude);
      },
      (err) => {
        setStatus(err.message ?? "Failed to get location.");
      },
      { enableHighAccuracy: true, timeout: 15_000, maximumAge: 10_000 }
    );
  };

  const submit = async () => {
    if (!token) {
      navigate("/login");
      return;
    }
    if (!file || lat == null || lng == null) {
      setStatus("Select a video and get location first.");
      return;
    }

    setLoading(true);
    setStatus(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("lat", String(lat));
      form.append("lng", String(lng));

      const res = await api.post("/api/videos/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatus(`Uploaded. Status: ${res.data.status}. Video ID: ${res.data.video_id}`);
    } catch (e: any) {
      const msg = e?.response?.data?.detail ?? "Upload failed";
      setStatus(String(msg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto space-y-5">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold">Upload Street Video</h1>
        <p className="text-sm text-muted-foreground">
          Your video goes into moderation first. Points are awarded only after approval.
        </p>
      </div>

      {!token && (
        <div className="rounded-md border border-border/60 bg-muted/30 p-3">
          Please <button className="underline" onClick={() => navigate("/login")}>log in</button> to upload.
        </div>
      )}

      <div className="space-y-3">
        <label className="text-sm font-medium">Video file</label>
        <Input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />

        <div className="flex gap-3">
          <Button type="button" variant="outline" onClick={requestLocation}>
            Get location
          </Button>
          <div className="text-sm text-muted-foreground self-center">
            {lat != null && lng != null ? `Lat ${lat.toFixed(5)}, Lng ${lng.toFixed(5)}` : "No location yet"}
          </div>
        </div>

        <Button className="w-full" disabled={loading || !file || lat == null || lng == null} onClick={submit}>
          {loading ? "Uploading..." : "Submit for moderation"}
        </Button>

        {status && <div className="text-sm">{status}</div>}
      </div>
    </div>
  );
}

