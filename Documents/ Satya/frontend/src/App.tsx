import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Analysis from './pages/Analysis';
import { Toaster } from "@/components/ui/toaster"

function App() {
    return (
        <div className="min-h-screen bg-background font-sans antialiased text-foreground selection:bg-primary/20">
            <Navbar />
            <main className="container max-w-7xl mx-auto pt-10 px-4 pb-24">
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/analysis" element={<Analysis />} />
                </Routes>
            </main>
            <Toaster />
        </div>
    );
}

export default App;
