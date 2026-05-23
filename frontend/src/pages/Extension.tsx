import { Link } from 'react-router-dom';
import { ArrowRight, Download, ShieldCheck, Tablet, Image } from 'lucide-react';
import { Button } from '@/components/ui/button';

const Extension = () => {
    return (
        <div className="space-y-8">
            <div className="text-center space-y-4">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl bg-primary/10 text-primary">
                    <Download size={32} />
                </div>
                <h1 className="text-4xl font-extrabold tracking-tight">Install the Browser Extension</h1>
                <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                    The extension adds image analysis directly from web pages so you can check any image with one right click. Use the web app for URL or text analysis when you want the most accurate, repeatable results.
                </p>
            </div>

            <div className="grid gap-6 lg:grid-cols-2">
                <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex items-center gap-3 text-foreground"> 
                        <Image size={24} />
                        <h2 className="text-2xl font-semibold">1. Install locally</h2>
                    </div>
                    <ol className="mt-4 space-y-3 text-sm leading-7 text-muted-foreground">
                        <li>
                            Open your browser extension page: <span className="font-semibold text-foreground">chrome://extensions</span> or <span className="font-semibold text-foreground">edge://extensions</span>.
                        </li>
                        <li>
                            Enable Developer Mode.
                        </li>
                        <li>
                            Choose "Load unpacked" and select the <span className="font-semibold text-foreground">extension</span> folder in this project.
                        </li>
                        <li>
                            The extension will now show a popup and a right-click menu on images.
                        </li>
                    </ol>
                </div>

                <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
                    <div className="flex items-center gap-3 text-foreground">
                        <ShieldCheck size={24} />
                        <h2 className="text-2xl font-semibold">2. Use it with confidence</h2>
                    </div>
                    <div className="mt-4 space-y-3 text-sm leading-7 text-muted-foreground">
                        <p>
                            Right-click any image on a webpage and choose <strong>Check if AI-Generated</strong> to see a quick signal.
                        </p>
                        <p>
                            If you need the most accurate result, use the web app's direct analysis with a URL or pasted text.
                        </p>
                        <p>
                            For URL analysis, use a direct image URL ending in <span className="font-semibold">.jpg</span>, <span className="font-semibold">.png</span>, or <span className="font-semibold">.webp</span>.
                        </p>
                        <p>
                            For text analysis, paste at least 20 characters so the detection model has enough data to score authenticity.
                        </p>
                    </div>
                </div>
            </div>

            <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
                <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                    <div>
                        <h3 className="text-2xl font-semibold">Need an immediate analysis?</h3>
                        <p className="mt-2 text-sm text-muted-foreground">
                            Use the app to paste a URL or text sample and get a reliable AI authenticity check right away.
                        </p>
                    </div>
                    <div className="flex flex-wrap gap-3">
                        <Link to="/analysis">
                        <Button className="rounded-full font-semibold" size="lg">
                            Analyze now <ArrowRight size={18} />
                        </Button>
                    </Link>
                    <Button
                        variant="outline"
                        className="rounded-full font-semibold"
                        onClick={() => window.open('chrome://extensions', '_blank')}
                    >
                        Open Extensions
                    </Button>
                    </div>
                </div>
            </div>

            <div className="rounded-3xl border border-border bg-card p-6 shadow-sm">
                <div className="flex items-center gap-3 text-foreground">
                    <Tablet size={24} />
                    <h2 className="text-2xl font-semibold">Why this works</h2>
                </div>
                <p className="mt-4 text-sm leading-7 text-muted-foreground">
                    The extension is a convenience layer, but the app is the ground truth: it sends image bytes or text directly to the local backend detector. For 100% usable results, keep the backend running, use direct URLs or file uploads, and check text samples with at least 20 characters.
                </p>
            </div>
        </div>
    );
};

export default Extension;
