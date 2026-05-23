import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Analysis from './pages/Analysis';
import Extension from './pages/Extension';
import Map from './pages/Map';
import Upload from './pages/Upload';
import Login from './pages/Login';
import Profile from './pages/Profile';
import { Toaster } from "@/components/ui/toaster"
import ErrorBoundary from './components/ErrorBoundary';

function App() {
    return (
        <div className="min-h-screen bg-background font-sans antialiased text-foreground selection:bg-primary/20">
            <Navbar />
            <ErrorBoundary>
                <main className="container max-w-7xl mx-auto pt-10 px-4 pb-24">
                    <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/analysis" element={<Analysis />} />
                        <Route path="/extension" element={<Extension />} />
                        <Route path="/map" element={<Map />} />
                        <Route path="/upload" element={<Upload />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/profile" element={<Profile />} />
                    </Routes>
                </main>
            </ErrorBoundary>
            <Toaster />
        </div>
    );
}

export default App;
