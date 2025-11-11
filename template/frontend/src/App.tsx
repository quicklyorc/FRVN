import { useEffect, useState } from "react";

export default function App() {
  const [health, setHealth] = useState<string>("...");
  useEffect(() => {
    fetch("/api/healthz")
      .then((r) => r.json())
      .then((d) => setHealth(d.status ?? "ok"))
      .catch(() => setHealth("unavailable"));
  }, []);
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="p-6 rounded-xl border">
        <h1 className="text-2xl font-bold mb-2">FRVN Template</h1>
        <p className="text-gray-600">Backend health: {health}</p>
      </div>
    </div>
  );
}


