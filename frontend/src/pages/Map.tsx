import React from "react";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { MapContainer, TileLayer, Marker, Popup, useMapEvents } from "react-leaflet";
import { api } from "@/lib/api";
import VideoModal from "@/components/VideoModal";
import { useNavigate } from "react-router-dom";
import { getToken } from "@/lib/auth";

type VideoItem = {
  id: number;
  lat: number;
  lng: number;
  heading?: number | null;
  thumbnail_url: string | null;
  video_url: string;
  uploader_username: string | null;
};

function BoundsWatcher({ onBounds }: { onBounds: (b: L.LatLngBounds) => void }) {
  const map = useMapEvents({
    moveend: () => {
      onBounds(map.getBounds());
    },
  });
  return null;
}

function createLeafletMarkerIcons() {
  // Ensure default marker icons work with Vite bundling.
  const iconUrl = new URL("leaflet/dist/images/marker-icon.png", import.meta.url).toString();
  const iconRetinaUrl = new URL("leaflet/dist/images/marker-icon-2x.png", import.meta.url).toString();
  const shadowUrl = new URL("leaflet/dist/images/marker-shadow.png", import.meta.url).toString();

  const marker = L.icon({
    iconUrl,
    iconRetinaUrl,
    shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41],
  });

  return marker;
}

export default function MapPage() {
  const navigate = useNavigate();
  const token = getToken();
  const [items, setItems] = React.useState<VideoItem[]>([]);
  const [selected, setSelected] = React.useState<VideoItem | null>(null);
  const [open, setOpen] = React.useState(false);

  const [bounds, setBounds] = React.useState<L.LatLngBounds | null>(null);
  const markerIcon = React.useMemo(() => createLeafletMarkerIcons(), []);

  React.useEffect(() => {
    if (!bounds) return;

    const minLat = bounds.getSouth();
    const maxLat = bounds.getNorth();
    const minLng = bounds.getWest();
    const maxLng = bounds.getEast();

    void api
      .get("/api/map/videos", {
        params: { minLat, minLng, maxLat, maxLng, limit: 80 },
      })
      .then((res) => {
        setItems(res.data.items ?? []);
      })
      .catch(() => {
        // MVP: ignore map fetch errors.
        setItems([]);
      });
  }, [bounds]);

  const handleOpenVideo = (video: VideoItem) => {
    setSelected(video);
    setOpen(true);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Street Video Map</h1>
          <p className="text-sm text-muted-foreground">
            Pan/zoom to load approved street videos. Click a marker to watch.
          </p>
        </div>
        {!token && (
          <button
            onClick={() => navigate("/login")}
            className="rounded-full border border-border px-4 py-2 text-sm hover:bg-muted/50 transition-colors"
          >
            Login to earn watch-time points
          </button>
        )}
      </div>

      <div className="h-[calc(100vh-7rem)] w-full rounded-lg overflow-hidden border border-border/60">
        <MapContainer center={[20, 0]} zoom={2} scrollWheelZoom={true} style={{ width: "100%", height: "100%" }}>
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <BoundsWatcher onBounds={(b) => setBounds(b)} />

          {items.map((v) => (
            <Marker key={v.id} position={[v.lat, v.lng]} icon={markerIcon}>
              <Popup>
                <div className="max-w-[260px]">
                  <div className="font-medium">{v.uploader_username ? `@${v.uploader_username}` : "Unknown uploader"}</div>
                  <div className="text-xs text-muted-foreground">Click to watch</div>
                  <div className="mt-2">
                    <button
                      className="rounded-md bg-[hsl(var(--satya-saffron))] text-white px-3 py-1.5 text-sm hover:bg-[hsl(var(--satya-saffron))]/90 transition-colors"
                      onClick={() => handleOpenVideo(v)}
                    >
                      Watch
                    </button>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      <VideoModal video={selected} open={open} onOpenChange={(o) => setOpen(o)} />
    </div>
  );
}

