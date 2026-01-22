import React from 'react';
import { Sun as SunIcon, Moon, Github, LifeBuoy } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Navbar = () => {
    const [isDark, setIsDark] = React.useState(false);

    const toggleTheme = () => {
        const root = window.document.documentElement;
        if (isDark) {
            root.classList.remove('dark');
        } else {
            root.classList.add('dark');
        }
        setIsDark(!isDark);
    };

    return (
        <nav className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
            <div className="container flex h-16 max-w-7xl mx-auto items-center justify-between px-4">
                <div className="flex items-center gap-3 group cursor-pointer" onClick={() => window.location.href = '/'}>
                    {/* Ashoka Chakra-inspired Logo */}
                    <div className="relative">
                        <LifeBuoy size={32} className="text-[hsl(var(--satya-saffron))] animate-spin-slow" strokeWidth={2.5} />
                    </div>
                    <span className="text-3xl font-heading tracking-wide text-foreground">
                        Satya
                    </span>
                </div>

                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => window.open('https://github.com', '_blank')}>
                        <Github size={20} />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={toggleTheme}>
                        {isDark ? <SunIcon size={20} /> : <Moon size={20} />}
                    </Button>

                    <Button className="bg-[hsl(var(--satya-saffron))] hover:bg-[hsl(var(--satya-saffron))]/90 text-white border-0 font-medium">
                        Get Extension
                    </Button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
