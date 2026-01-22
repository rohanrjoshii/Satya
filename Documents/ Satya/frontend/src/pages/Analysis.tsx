import { useState } from 'react';
import FileUpload from '@/components/FileUpload';
import ResultsDashboard from '@/components/ResultsDashboard';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { useToast } from "@/components/ui/use-toast"

const Analysis = () => {
    const { toast } = useToast()
    const [status, setStatus] = useState<'idle' | 'analyzing' | 'success' | 'error'>('idle');
    const [result, setResult] = useState<any>(null);
    const [fileType, setFileType] = useState<'image' | 'video' | 'text' | null>(null);
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);

    const handleUrlSubmit = async (url: string) => {
        setStatus('analyzing');
        setFileType('image'); // Assume image for URL for now
        setPreviewUrl(url);

        const formData = new FormData();
        formData.append('url', url);

        try {
            const endpoint = `/api/analyze/image`;
            const response = await axios.post(endpoint, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setResult(response.data);
            setStatus('success');
            toast({
                title: "Analysis Complete",
                description: "The content has been processed successfully.",
            })
        } catch (error) {
            console.error(error);
            setStatus('error');
            toast({
                variant: "destructive",
                title: "Analysis Failed",
                description: "Something went wrong. Please check the URL and try again.",
            })
        }
    };

    const handleFileSelect = async (file: File) => {
        setStatus('analyzing');

        // Determine type
        let type: 'image' | 'video' | 'text' = 'text';
        if (file.type.startsWith('image/')) type = 'image';
        else if (file.type.startsWith('video/')) type = 'video';

        setFileType(type);
        if (type === 'image') {
            setPreviewUrl(URL.createObjectURL(file));
        } else {
            setPreviewUrl(null); // No preview for video/text yet
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const endpoint = `/api/analyze/${type}`;

            let response;
            if (type === 'text') {
                const text = await file.text();
                response = await axios.post(endpoint, null, { params: { text } });
            } else {
                response = await axios.post(endpoint, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
            }

            setResult(response.data);
            setStatus('success');
            toast({
                title: "Analysis Complete",
                description: `Successfully analyzed ${file.name}`,
            })
        } catch (error) {
            console.error(error);
            setStatus('error');
            toast({
                variant: "destructive",
                title: "Upload Failed",
                description: "There was an error processing your file.",
            })
        }
    };

    return (
        <div className="space-y-12">
            <div className="text-center space-y-4">
                <h2 className="text-4xl font-extrabold tracking-tight lg:text-5xl">Content Analyzer</h2>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Upload media or provide a URL to uncover hidden AI artifacts using our deep learning ensemble.
                </p>
            </div>

            <div className="max-w-4xl mx-auto">
                <FileUpload
                    onFileSelect={handleFileSelect}
                    onUrlSubmit={handleUrlSubmit}
                    isAnalyzing={status === 'analyzing'}
                />
            </div>

            {status === 'analyzing' && (
                <div className="flex flex-col items-center justify-center p-12 space-y-4">
                    <Loader2 className="animate-spin text-primary h-12 w-12" />
                    <p className="text-lg font-medium text-foreground">Analyzing deep patterns...</p>
                    <p className="text-sm text-muted-foreground">This usually takes 2-5 seconds.</p>
                </div>
            )}

            {status === 'success' && result && (
                <div className="animate-fade-in-up">
                    <ResultsDashboard result={result} fileType={fileType} previewUrl={previewUrl} />
                </div>
            )}

            {status === 'error' && (
                <div className="p-6 bg-destructive/10 border border-destructive/20 rounded-xl text-center max-w-md mx-auto">
                    <h3 className="text-lg font-semibold text-destructive">Analysis Error</h3>
                    <p className="text-destructive/80 mt-1">Please try again with a different file or URL.</p>
                </div>
            )}
        </div>
    );
};

export default Analysis;
