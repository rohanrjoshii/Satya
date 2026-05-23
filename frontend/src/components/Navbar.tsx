import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sun as SunIcon, Moon, Github, LifeBuoy } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { clearToken, getToken } from '@/lib/auth';

const Navbar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const [isDark, setIsDark] = React.useState(false);
    const [isLoggedIn, setIsLoggedIn] = React.useState(false);

    const toggleTheme = () => {
        const root = window.document.documentElement;
        if (isDark) {
            root.classList.remove('dark');
        } else {
            root.classList.add('dark');
        }
        setIsDark(!isDark);
    };

    React.useEffect(() => {
        setIsLoggedIn(!!getToken());
    }, []);

    const handleLogout = () => {
        clearToken();
        setIsLoggedIn(false);
    };

    return (
        <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-16 max-w-7xl mx-auto items-center gap-4 px-4">
                <Link to="/" className="flex shrink-0 items-center gap-3 group">
                    {/* Ashoka Chakra-inspired Logo */}
                    <div className="relative">
                        <LifeBuoy size={32} className="text-[hsl(var(--satya-saffron))] animate-spin-slow" strokeWidth={2.5} />
                    </div>
                    <span className="text-2xl sm:text-3xl font-heading tracking-wide text-foreground">
                        Satya
                    </span>
                </Link>

                <div className="hidden md:flex flex-1 justify-center items-center gap-1 text-sm text-muted-foreground min-w-0">
                    <Link
                        to="/"
                        className={`rounded-md px-2 lg:px-3 py-2 hover:text-foreground transition-colors whitespace-nowrap ${location.pathname === '/' ? 'text-foreground font-medium' : ''}`}
                    >
                        Home
                    </Link>
                    <Link
                        to="/analysis"
                        className={`rounded-md px-2 lg:px-3 py-2 hover:text-foreground transition-colors whitespace-nowrap ${location.pathname === '/analysis' ? 'text-foreground font-medium' : ''}`}
                    >
                        Analysis
                    </Link>
                </div>

                <div className="flex shrink-0 items-center gap-2 sm:gap-4 ml-auto">
                    <Button variant="ghost" size="icon" onClick={() => window.open('https://github.com', '_blank')}>
                        <Github size={20} />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={toggleTheme}>
                        {isDark ? <SunIcon size={20} /> : <Moon size={20} />}
                    </Button>

                    {isLoggedIn ? (
                        <Button variant="outline" className="rounded-full" onClick={handleLogout}>
                            Logout
                        </Button>
                    ) : (
                        <Link to="/login">
                            <Button variant="outline" className="rounded-full">
                                Login
                            </Button>
                        </Link>
                    )}

                    <Button
                        className="bg-[hsl(var(--satya-saffron))] hover:bg-[hsl(var(--satya-saffron))]/90 text-white border-0 font-medium"
                        onClick={() => navigate('/extension')}
                    >
                        Get Extension
                    </Button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
