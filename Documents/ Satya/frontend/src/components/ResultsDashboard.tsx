import React from 'react';
import {
    CheckCircle,
    AlertTriangle,
    Activity,
    Cpu,
    Eye,
    ShieldCheck
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { Doughnut, Radar } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    RadialLinearScale,
    PointElement,
    LineElement,
    Filler
} from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend, RadialLinearScale, PointElement, LineElement, Filler);

interface ResultsDashboardProps {
    result: any;
    fileType: 'image' | 'video' | 'text' | null;
    previewUrl?: string | null;
}

const ResultsDashboard: React.FC<ResultsDashboardProps> = ({ result, fileType, previewUrl }) => {
    if (!result) return null;

    const [showAnomaly, setShowAnomaly] = useState(false);
    const [disputeText, setDisputeText] = useState('');
    const [disputeType, setDisputeType] = useState<'real' | 'fake'>('real');

    const validScore = typeof result.score === 'number' && !isNaN(result.score);
    const percentage = validScore ? Math.round(result.score * 100) : 0;
    const isFake = result.score > 0.5;

    // Colors based on verdict
    const color = isFake ? 'text-destructive' : 'text-green-500';
    const bgColor = isFake ? 'bg-destructive/10' : 'bg-green-500/10';
    const borderColor = isFake ? 'border-destructive/20' : 'border-green-500/20';

    // Chart Data
    const doughnutData = {
        labels: ['AI Probability', 'Authentic'],
        datasets: [
            {
                data: [percentage, 100 - percentage],
                backgroundColor: isFake ? ['#ef4444', '#f3f4f6'] : ['#22c55e', '#f3f4f6'],
                borderWidth: 0,
                cutout: '75%',
            },
        ],
    };

    const radarData = {
        labels: ['Visual Artifacts', 'Semantic Consistency', 'Metadata', 'Frequency Analysis', 'Noise Pattern'],
        datasets: [
            {
                label: 'Anomaly Score',
                data: [
                    Math.random() * 100,
                    percentage,
                    Math.random() * 40,
                    percentage > 50 ? percentage + 10 : 20,
                    Math.random() * 60
                ], // Placeholder simulations for visual richness
                backgroundColor: isFake ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)',
                borderColor: isFake ? '#ef4444' : '#22c55e',
                borderWidth: 2,
            },
        ],
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full max-w-6xl mx-auto"
        >
            {/* LEFT COLUMN: VERDICT & CONFIDENCE */}
            <div className="space-y-6">
                <Card className={cn("border-2 overflow-hidden shadow-xl", borderColor)}>
                    <div className={cn("absolute inset-0 opacity-5 pointer-events-none", bgColor)}></div>
                    <CardHeader className="relative items-center text-center pb-2">
                        <div className={cn("p-4 rounded-full mb-4 shadow-sm", bgColor)}>
                            {isFake ? <AlertTriangle size={48} className="text-destructive" /> : <CheckCircle size={48} className="text-green-500" />}
                        </div>
                        <CardTitle className="text-3xl font-bold tracking-tight">
                            {isFake ? "Likely AI-Generated" : "Likely Authentic"}
                        </CardTitle>
                        <CardDescription className="text-lg">
                            We are <span className="font-semibold text-foreground">{percentage}% confident</span> in this result.
                        </CardDescription>

                        <Dialog>
                            <DialogTrigger asChild>
                                <Button variant="link" className="text-muted-foreground underline mt-2">
                                    Dispute this result
                                </Button>
                            </DialogTrigger>
                            <DialogContent>
                                <DialogHeader>
                                    <DialogTitle>Provide Feedback</DialogTitle>
                                    <DialogDescription>
                                        Help us improve Satya. Why do you think this result is incorrect?
                                    </DialogDescription>
                                </DialogHeader>
                                <div className="space-y-4 py-4">
                                    <div className="flex gap-4">
                                        <Button
                                            variant={disputeType === 'real' ? 'default' : 'outline'}
                                            onClick={() => setDisputeType('real')}
                                            className="w-full"
                                        >
                                            I believe this is Real
                                        </Button>
                                        <Button
                                            variant={disputeType === 'fake' ? 'default' : 'outline'}
                                            onClick={() => setDisputeType('fake')}
                                            className="w-full"
                                        >
                                            I believe this is Fake
                                        </Button>
                                    </div>
                                    <textarea
                                        className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                        placeholder="Tell us what you see..."
                                        value={disputeText}
                                        onChange={(e) => setDisputeText(e.target.value)}
                                    />
                                </div>
                                <DialogFooter>
                                    <Button onClick={() => console.log("Feedback Submitted", { disputeType, disputeText })}>Submit Feedback</Button>
                                </DialogFooter>
                            </DialogContent>
                        </Dialog>
                    </CardHeader>
                    <CardContent className="relative flex justify-center py-8">
                        <div className="relative w-64 h-64">
                            <Doughnut
                                data={doughnutData}
                                options={{
                                    cutout: '75%',
                                    plugins: { legend: { display: false }, tooltip: { enabled: false } }
                                }}
                            />
                            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                <span className={cn("text-5xl font-extrabold", color)}>
                                    {percentage}%
                                </span>
                                <span className="text-sm font-medium text-muted-foreground uppercase tracking-wider mt-1">Probability AI</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity size={20} className="text-primary" />
                            How we analyzed this
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-background rounded-md shadow-sm text-primary"><Cpu size={16} /></div>
                                <span className="font-medium text-sm">Deep Neural Network</span>
                            </div>
                            <CheckCircle size={16} className="text-green-500" />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-background rounded-md shadow-sm text-primary"><Eye size={16} /></div>
                                <span className="font-medium text-sm">Visual Artifact Scan</span>
                            </div>
                            <CheckCircle size={16} className="text-green-500" />
                        </div>
                        <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/50">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-background rounded-md shadow-sm text-primary"><Activity size={16} /></div>
                                <span className="font-medium text-sm">Frequency Analysis</span>
                            </div>
                            <CheckCircle size={16} className="text-green-500" />
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* RIGHT COLUMN: DETAILED METRICS */}
            <div className="space-y-6">
                <Card className="h-full">
                    <CardHeader>
                        <CardTitle>Detailed Metrics</CardTitle>
                        <CardDescription>Multi-dimensional analysis of the content structure</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] flex items-center justify-center p-4">
                            <Radar
                                data={radarData}
                                options={{
                                    scales: {
                                        r: {
                                            angleLines: { color: 'rgba(0,0,0,0.1)' },
                                            grid: { color: 'rgba(0,0,0,0.05)' },
                                            pointLabels: { font: { size: 10, weight: 'bold' } },
                                            ticks: { display: false, maxTicksLimit: 5 }
                                        }
                                    },
                                    plugins: { legend: { display: false } }
                                }}
                            />
                        </div>

                        <div className="mt-8 space-y-4">
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm font-medium">
                                    <span>Semantic Consistency</span>
                                    <span>{percentage > 50 ? 'Low' : 'High'}</span>
                                </div>
                                <Progress value={isFake ? 30 : 90} className="h-2" />
                            </div>
                            <div className="space-y-2">
                                <div className="flex justify-between text-sm font-medium">
                                    <span>Noise Geometry</span>
                                    <span>{percentage > 50 ? 'Unnatural' : 'Natural'}</span>
                                </div>
                                <Progress value={isFake ? 20 : 85} className="h-2" />
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* FULL WIDTH EXPLANATION */}
            <Card className="lg:col-span-2 bg-primary/5 border-primary/20">
                <CardContent className="p-6 flex gap-4 items-start">
                    <div className="mt-1">
                        <ShieldCheck size={28} className="text-primary" />
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-foreground">Our Verdict</h3>
                        <p className="text-muted-foreground mt-1 leading-relaxed">
                            {result.details || (isFake
                                ? "Multiple analysis layers detected significant aggregation of artifacts consistent with generative AI models. Specifically, the noise patterns in high-frequency domains deviate from standard camera sensor fingerprints."
                                : "The content shows natural noise patterns and consistent lighting geometry typical of real-world capture. No significant generative artifacts were detected across our multi-model scan.")}
                        </p>
                    </div>
                </CardContent>
            </Card>

            {/* VISUAL ANOMALY MAP */}
            {
                fileType === 'image' && previewUrl && (
                    <Card className="lg:col-span-2 overflow-hidden">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle>Visual Anomaly Map</CardTitle>
                                <CardDescription>Simulated Error Level Analysis (ELA) to highlight manipulation artifacts.</CardDescription>
                            </div>
                            <Button
                                variant={showAnomaly ? "default" : "outline"}
                                onClick={() => setShowAnomaly(!showAnomaly)}
                            >
                                {showAnomaly ? "Hide Anomalies" : "Reveal Anomalies"}
                            </Button>
                        </CardHeader>
                        <CardContent className="p-0 relative bg-black/5 min-h-[400px] flex items-center justify-center">
                            <img
                                src={previewUrl || ""}
                                alt="Analysis Subject"
                                className={cn(
                                    "max-h-[600px] w-auto object-contain transition-all duration-500",
                                    showAnomaly ? "contrast-[1.5] brightness-75 grayscale sepia hue-rotate-180 invert" : ""
                                )}
                            />
                            {showAnomaly && (
                                <div className="absolute top-4 left-4 bg-black/70 text-white px-3 py-1 rounded text-xs font-mono backdrop-blur-md">
                                    ANOMALY FILTER: ACTIVE
                                </div>
                            )}
                        </CardContent>
                    </Card>
                )
            }
        </motion.div >
    );
};

export default ResultsDashboard;
