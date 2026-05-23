import React from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { useNavigate } from "react-router-dom";

type VideoItem = {
  id: number;
  video_url: string;
  thumbnail_url: string | null;
  uploader_username: string | null;
  lat: number;
  lng: number;
  heading?: number | null;
};

export default function VideoModal({
  video,
  open,
  onOpenChange,
}: {
  video: VideoItem | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();
  const token = getToken();
  const [watchSessionId, setWatchSessionId] = React.useState<number | null>(null);
  const [reportToken, setReportToken] = React.useState<string | null>(null);
  const [lastPoints, setLastPoints] = React.useState<number>(0);
  const intervalRef = React.useRef<number | null>(null);

  const videoRef = React.useRef<HTMLVideoElement | null>(null);

  const stopInterval = React.useCallback(() => {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  const endSession = React.useCallback(async () => {
    if (!video || !watchSessionId || !reportToken) return;
    try {
      const form = new FormData();
      form.append("watch_session_id", String(watchSessionId));
      form.append("report_token", reportToken);
      await api.post(`/api/watch/videos/${video.id}/session/end`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    } catch {
      // Best-effort: if it fails, don’t block the UI.
    }
  }, [reportToken, video, watchSessionId]);

  const startSession = React.useCallback(async () => {
    if (!video) return;
    if (!token) return;

    const res = await api.post(`/api/watch/videos/${video.id}/session/start`);
    setWatchSessionId(res.data.watch_session_id);
    setReportToken(res.data.report_token);
  }, [token, video]);

  const report = React.useCallback(async () => {
    if (!video || !watchSessionId || !reportToken) return;
    const el = videoRef.current;
    if (!el) return;

    const payload = {
      watch_session_id: watchSessionId,
      report_token: reportToken,
      clientVideoTimeSec: el.currentTime,
      isPlaying: !el.paused && !el.ended,
    };

    const res = await api.post(`/api/watch/videos/${video.id}/session/report`, payload);
    const pts = Number(res.data.points_awarded ?? 0);
    setLastPoints(pts);
  }, [reportToken, video, watchSessionId]);

  React.useEffect(() => {
    if (!open) {
      stopInterval();
      setLastPoints(0);
      setWatchSessionId(null);
      setReportToken(null);
      // End session asynchronously.
      void endSession();
      return;
    }

    // If opening without auth, just show the video (no watch points).
    if (!token || !video) return;

    void (async () => {
      try {
        await startSession();
      } catch {
        // Ignore start errors; user can retry by closing/reopening.
      }
    })();
  }, [endSession, open, startSession, stopInterval, token, video]);

  React.useEffect(() => {
    // Start periodic reporting once session exists.
    if (!open || !watchSessionId || !reportToken) return;
    stopInterval();
    intervalRef.current = window.setInterval(() => {
      void report();
    }, 5000);
    return () => stopInterval();
  }, [open, report, reportToken, stopInterval, watchSessionId]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>Street Video</DialogTitle>
        </DialogHeader>

        {!video ? null : (
          <div className="space-y-4">
            {!token && (
              <div className="rounded-md border border-border/60 bg-muted/30 p-3">
                Login required to earn watch-time points.
                <div className="mt-3">
                  <Button onClick={() => navigate("/login")}>Go to Login</Button>
                </div>
              </div>
            )}

            <video
              ref={videoRef}
              src={video.video_url}
              controls
              className="w-full rounded-md bg-black"
              playsInline
            />

            {token && (
              <div className="text-sm text-muted-foreground">
                Last report: <span className="text-foreground font-medium">{lastPoints.toFixed(2)}</span> points
              </div>
            )}

            {video.uploader_username && (
              <div className="text-sm text-muted-foreground">
                Uploaded by <span className="text-foreground font-medium">{video.uploader_username}</span>
              </div>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

