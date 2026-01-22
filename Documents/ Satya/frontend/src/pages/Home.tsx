import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { ArrowRight, Shield, Globe, Zap, Activity } from 'lucide-react';
import { motion } from 'framer-motion';

const Home = () => {
    const navigate = useNavigate();

    return (
        <div className="space-y-32 py-12">
            {/* HERO SECTION */}
            <section className="text-center space-y-8 relative">
                {/* Saffron Glow */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[hsl(var(--satya-saffron))]/10 blur-[120px] rounded-full pointer-events-none -z-10"></div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5 }}
                >
                    <span className="inline-block py-1 px-3 rounded-full bg-[hsl(var(--satya-saffron))]/10 text-[hsl(var(--satya-saffron))] text-xs font-bold uppercase tracking-wider mb-6 border border-[hsl(var(--satya-saffron))]/20">
                        Satyameva Jayate
                    </span>
                    <h1 className="text-6xl md:text-8xl font-heading text-foreground mb-4">
                        Satya
                    </h1>
                    <p className="text-3xl md:text-5xl font-light text-muted-foreground leading-tight">
                        Satya over <span className="text-[hsl(var(--satya-saffron))] font-medium italic">everything</span>.
                    </p>

                    <p className="text-lg text-muted-foreground mt-8 max-w-2xl mx-auto leading-relaxed">
                        Detect deepfakes and manipulated media with unwavering precision.
                    </p>

                    <div className="flex items-center justify-center gap-4 mt-12">
                        <Button size="lg" className="h-14 px-8 text-lg rounded-full bg-[hsl(var(--satya-saffron))] hover:bg-[hsl(var(--satya-saffron))]/90 text-white shadow-lg shadow-orange-500/20" onClick={() => navigate('/analysis')}>
                            Begin Analysis <ArrowRight className="ml-2 h-5 w-5" />
                        </Button>
                        <Button size="lg" variant="outline" className="h-14 px-8 text-lg rounded-full border-2 hover:bg-muted/50" onClick={() => document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' })}>
                            How it Works
                        </Button>
                    </div>
                </motion.div>
            </section>

            {/* FEATURES */}
            <section className="grid md:grid-cols-3 gap-8">
                {[
                    {
                        icon: <Shield className="h-8 w-8 text-[hsl(var(--satya-saffron))]" />,
                        title: "Ironclad Privacy",
                        desc: "Your data never leaves your device's memory for longer than the analysis takes."
                    },
                    {
                        icon: <Zap className="h-8 w-8 text-yellow-500" />,
                        title: "Instant Results",
                        desc: "Real-time edge inferencing that cuts through the noise in milliseconds."
                    },
                    {
                        icon: <Globe className="h-8 w-8 text-green-500" />,
                        title: "Universal Truth",
                        desc: "Verify content across the web with our browser extension."
                    }
                ].map((feature, i) => (
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: i * 0.1 }}
                        key={i}
                        className="p-8 rounded-2xl border bg-card hover:shadow-lg transition-all hover:border-[hsl(var(--satya-saffron))]/30 group"
                    >
                        <div className="mb-6 p-4 bg-muted/50 rounded-2xl w-fit group-hover:bg-[hsl(var(--satya-saffron))]/10 transition-colors">{feature.icon}</div>
                        <h3 className="text-xl font-bold mb-3 font-heading">{feature.title}</h3>
                        <p className="text-muted-foreground leading-relaxed">{feature.desc}</p>
                    </motion.div>
                ))}
            </section>

            {/* HOW IT WORKS SECTION */}
            <section id="how-it-works" className="py-24 bg-muted/30 rounded-[3rem] p-8 md:p-16">
                <div className="max-w-4xl mx-auto text-center space-y-16">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="text-4xl md:text-5xl font-heading mb-6">Built on Truth</h2>
                        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                            Satya isn't magic. It's advanced forensics engineering wrapped in a beautiful interface.
                        </p>
                    </motion.div>

                    <div className="grid md:grid-cols-2 gap-12 text-left">
                        <motion.div
                            initial={{ opacity: 0, x: -20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.2 }}
                            className="space-y-4"
                        >
                            <div className="h-12 w-12 rounded-2xl bg-[hsl(var(--satya-saffron))]/20 flex items-center justify-center text-[hsl(var(--satya-saffron))] mb-6">
                                <Shield className="h-6 w-6" />
                            </div>
                            <h3 className="text-2xl font-bold">Ensemble Learning</h3>
                            <p className="text-muted-foreground leading-relaxed text-lg">
                                We don't rely on a single opinion. Satya aggregates predictions from multiple state-of-the-art neural networks, each trained on different generations of GANs and Diffusion models. This "council of models" ensures higher accuracy and drastically reduces false positives.
                            </p>
                        </motion.div>
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            whileInView={{ opacity: 1, x: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.3 }}
                            className="space-y-4"
                        >
                            <div className="h-12 w-12 rounded-2xl bg-blue-500/20 flex items-center justify-center text-blue-500 mb-6">
                                <Activity className="h-6 w-6" />
                            </div>
                            <h3 className="text-2xl font-bold">Frequency Analysis</h3>
                            <p className="text-muted-foreground leading-relaxed text-lg">
                                AI generation often leaves behind invisible "fingerprints" in the noise patterns of an image. We perform Fast Fourier Transform (FFT) analysis to visualize these spectral anomalies, spotting what the human eye misses.
                            </p>
                        </motion.div>
                    </div>
                </div>
            </section>
        </div>
    );
};

export default Home;
