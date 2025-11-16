import Header from "./components/Header";
import Dashboard from "./components/Dashboard";
import './App.css'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto p-6">
        <Dashboard />
      </main>
    </div>
  );
}
