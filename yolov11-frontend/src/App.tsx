import React, { useState } from "react";
import Header from "./components/Header";
import Dashboard from "./components/Dashboard";
import './App.css'

export default function App() {
  // global demo state
  const [projectLink, setProjectLink] = useState("");
  const [pptLink, setPptLink] = useState("");
  const [youtubeLink, setYoutubeLink] = useState("");
  return (
    <div className="min-h-screen">
      <Header />
      <main className="container mx-auto p-6">
        <Dashboard
          projectLink={projectLink}
          setProjectLink={setProjectLink}
          pptLink={pptLink}
          setPptLink={setPptLink}
          youtubeLink={youtubeLink}
          setYoutubeLink={setYoutubeLink}
        />
      </main>
    </div>
  );
}
