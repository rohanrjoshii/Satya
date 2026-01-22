import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image as ImageIcon, Video, X, CheckCircle, File as FileIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils'; // Assuming you have this utility

interface FileUploadProps {
    onFileSelect: (file: File) => void;
    onUrlSubmit: (url: string) => void;
    isAnalyzing: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, onUrlSubmit, isAnalyzing }) => {
    const [preview, setPreview] = useState<string | null>(null);
    const [fileName, setFileName] = useState<string | null>(null);
    const [fileSize, setFileSize] = useState<string | null>(null);
    const [urlInput, setUrlInput] = useState("");

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            const file = acceptedFiles[0];
            handleFile(file);
        }
    }, [onFileSelect]);

    const handleFile = (file: File) => {
        onFileSelect(file);
        setFileName(file.name);
        setFileSize((file.size / (1024 * 1024)).toFixed(2) + " MB");

        // Create preview
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = () => setPreview(reader.result as string);
            reader.readAsDataURL(file);
        } else {
            setPreview(null);
        }
    };

    const clearFile = (e: React.MouseEvent) => {
        e.stopPropagation();
        setPreview(null);
        setFileName(null);
        setFileSize(null);
        // Reset logic in parent if needed, but for now just clear UI
    };

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        disabled: isAnalyzing,
        accept: {
            'image/*': [],
            'video/*': [],
            'text/plain': []
        },
        maxFiles: 1
    });

    const handleUrlSubmitInternal = (e: React.FormEvent) => {
        e.preventDefault();
        if (urlInput.trim()) {
            onUrlSubmit(urlInput);
        }
    };

    return (
        <div className="w-full max-w-3xl mx-auto space-y-8">

            <AnimatePresence mode="wait">
                {!fileName ? (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.2 }}
                    >
                        <div
                            {...getRootProps()}
                            className={cn(
                                "relative group cursor-pointer flex flex-col items-center justify-center w-full h-[400px] rounded-3xl border-2 border-dashed transition-all duration-300 ease-in-out",
                                isDragActive ? "border-primary bg-primary/5 scale-[1.01] shadow-xl shadow-primary/10" : "border-muted-foreground/20 hover:border-primary/50 hover:bg-muted/30",
                                isAnalyzing && "opacity-50 pointer-events-none"
                            )}
                        >
                            <input {...getInputProps()} />

                            <div className="flex flex-col items-center gap-6 p-8 text-center">
                                <div className={cn(
                                    "w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-sm",
                                    isDragActive ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground group-hover:bg-primary/10 group-hover:text-primary group-hover:scale-110"
                                )}>
                                    <Upload strokeWidth={1.5} size={48} />
                                </div>

                                <div className="space-y-2">
                                    <h3 className="text-2xl font-bold tracking-tight text-foreground">
                                        {isDragActive ? "Drop to analyze" : "Drag and drop media"}
                                    </h3>
                                    <p className="text-muted-foreground text-lg max-w-sm mx-auto">
                                        Upload images or videos to detect AI-generated artifacts vs real captures.
                                    </p>
                                </div>

                                <div className="flex gap-4 mt-4">
                                    <div className="px-4 py-2 bg-background border rounded-full text-xs font-medium text-muted-foreground flex items-center gap-2 shadow-sm">
                                        <ImageIcon size={14} /> JPG, PNG, WEBP
                                    </div>
                                    <div className="px-4 py-2 bg-background border rounded-full text-xs font-medium text-muted-foreground flex items-center gap-2 shadow-sm">
                                        <Video size={14} /> MP4, MOV, AVI
                                    </div>
                                </div>

                                <div className="absolute bottom-8 text-xs text-muted-foreground/60 uppercase tracking-widest font-semibold">
                                    Max File Size: 100MB
                                </div>
                            </div>
                        </div>
                    </motion.div>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        layout
                    >
                        <Card className="p-6 relative overflow-hidden border-primary/20 shadow-lg shadow-primary/5">
                            <div className="flex items-center gap-6">
                                <div className="relative shrink-0 w-32 h-32 rounded-xl overflow-hidden bg-muted border border-border">
                                    {preview ? (
                                        <img src={preview} alt="Preview" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                                            <FileIcon size={48} strokeWidth={1} />
                                        </div>
                                    )}
                                </div>

                                <div className="flex-grow min-w-0 space-y-2">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h3 className="text-xl font-bold truncate pr-4 text-foreground">{fileName}</h3>
                                            <p className="text-sm font-medium text-muted-foreground">{fileSize}</p>
                                        </div>
                                        <Button size="icon" variant="ghost" className="text-muted-foreground hover:text-destructive" onClick={clearFile} disabled={isAnalyzing}>
                                            <X size={20} />
                                        </Button>
                                    </div>

                                    <div className="pt-2">
                                        {isAnalyzing ? (
                                            <div className="space-y-2">
                                                <div className="flex justify-between text-xs font-semibold text-primary uppercase tracking-wider">
                                                    <span>Analyzing Content</span>
                                                    <span className="animate-pulse">Processing...</span>
                                                </div>
                                                <Progress value={45} className="h-2 w-full" />
                                            </div>
                                        ) : (
                                            <div className="flex items-center gap-2 text-green-600 font-medium bg-green-500/10 px-3 py-1.5 rounded-md w-fit text-sm">
                                                <CheckCircle size={16} />
                                                <span>Ready for analysis</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </Card>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="relative flex items-center">
                <div className="flex-grow border-t border-border"></div>
                <span className="flex-shrink-0 mx-4 text-muted-foreground text-sm font-medium uppercase tracking-wider">Or paste URL</span>
                <div className="flex-grow border-t border-border"></div>
            </div>

            <form onSubmit={handleUrlSubmitInternal} className="relative group">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <div className="p-1.5 rounded-md bg-muted text-muted-foreground">
                        <FileText size={16} />
                    </div>
                </div>
                <Input
                    disabled={isAnalyzing}
                    type="text"
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    className="pl-14 h-14 text-base rounded-xl transition-all border-muted-foreground/20 focus-visible:ring-primary/20 focus-visible:border-primary shadow-sm"
                />
                <div className="absolute inset-y-0 right-2 flex items-center">
                    <Button
                        type="submit"
                        disabled={!urlInput.trim() || isAnalyzing}
                        size="sm"
                        className="h-9 px-4 rounded-lg font-semibold"
                    >
                        Analyze
                    </Button>
                </div>
            </form>
        </div>
    );
};

export default FileUpload;
