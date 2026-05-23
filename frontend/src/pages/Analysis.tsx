import { useEffect, useRef, useState } from 'react';
import FileUpload from '@/components/FileUpload';
import ResultsDashboard from '@/components/ResultsDashboard';
import axios, { AxiosError } from 'axios';
import { Clock, Loader2, RefreshCw, Server, ShieldCheck, Square, UploadCloud } from 'lucide-react';
import { useToast } from "@/components/ui/use-toast"
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

const api = axios.create({
    timeout: 120_000,
});

const MAX_FILE_SIZE_MB = 100;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const SUPPORTED_FILE_TYPES = ['image/', 'video/', 'text/plain'];

function isFailedAnalysisPayload(data: unknown): boolean {
    if (!data || typeof data !== 'object') return true;
    const d = data as Record<string, unknown>;
    if (typeof d.error === 'string' && d.error.length > 0) return true;
    if (d.label === 'Error' || d.label === 'Model Error') return true;
    return false;
}

function messageFromPayload(data: Record<string, unknown>): string {
    if (typeof data.details === 'string' && data.details.trim()) return data.details.trim();
    if (typeof data.error === 'string' && data.error.trim()) return data.error.trim();
    return 'Analysis could not be completed.';
}

function formatFastApiDetail(detail: unknown): string | null {
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
        const parts = detail.map((item: { msg?: string; loc?: unknown }) => {
            if (item && typeof item === 'object' && 'msg' in item && typeof item.msg === 'string') {
                return item.msg;
            }
            return String(item);
        });
        return parts.filter(Boolean).join(' ');
    }
    return null;
}

function messageFromAxiosError(error: unknown): string {
    if (axios.isAxiosError(error)) {
        const ax = error as AxiosError<unknown>;
        const status = ax.response?.status;
        const data = ax.response?.data as unknown;

        if (typeof data === 'string') {
            const t = data.trim();
            if (t.startsWith('<') || t.length > 400) {
                return `The server returned an error page (HTTP ${status ?? '?'}). Is the API running on port 8000? Check the backend terminal.`;
            }
            return t.slice(0, 800);
        }

        if (data && typeof data === 'object') {
            const fromDetail = formatFastApiDetail((data as { detail?: unknown }).detail);
            if (fromDetail) return fromDetail;
            if (typeof (data as { error?: string }).error === 'string') {
                return (data as { error: string }).error;
            }
        }

        if (ax.code === 'ECONNREFUSED' || ax.message === 'Network Error') {
            return 'Cannot reach the analysis server. Start the backend (e.g. `uvicorn main:app` in the backend folder on port 8000) and keep this dev server running.';
        }
        if (status === 413) return 'This file is too large for the server.';
        if (status === 504 || ax.code === 'ECONNABORTED') {
            return 'The request timed out. Try a smaller image, a direct image URL (ending in .jpg, .png, etc.), or a shorter video.';
        }
        if (status === 503) {
            return 'The AI model is not available on the server. Check backend logs for load or CUDA errors.';
        }
        if (status === 400 || status === 422) {
            return (
                formatFastApiDetail((data as { detail?: unknown } | undefined)?.detail) ??
                'The server rejected this request (invalid file, URL, or parameters).'
            );
        }
        if (status != null && status >= 500) {
            return `Server error (HTTP ${status}). Check the backend logs for the traceback.`;
        }
    }
    return 'Could not complete analysis. If you just updated the app, hard-refresh the page (Cmd+Shift+R or Ctrl+Shift+R), then try again.';
}

function extractErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) return messageFromAxiosError(error);
    if (error instanceof Error && error.message) return error.message;
    if (typeof error === 'string') return error;
    return messageFromAxiosError(error);
}

const Analysis = () => {
    const { toast } = useToast()
    const [status, setStatus] = useState<'idle' | 'analyzing' | 'success' | 'error'>('idle');
    const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');
    const [result, setResult] = useState<any>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [uploadProgress, setUploadProgress] = useState<number | null>(null);
    const [analysisPhase, setAnalysisPhase] = useState('Preparing evidence');
    const [elapsedSeconds, setElapsedSeconds] = useState(0);
    const abortControllerRef = useRef<AbortController | null>(null);
    /** Remount FileUpload after a failed request so preview state does not stay ready while an error is shown. */
    const [fileUploadKey, setFileUploadKey] = useState(0);

    useEffect(() => {
        if (status !== 'analyzing') {
            setElapsedSeconds(0);
            return;
        }

        const startedAt = Date.now();
        const timer = window.setInterval(() => {
            setElapsedSeconds(Math.floor((Date.now() - startedAt) / 1000));
        }, 1000);

        return () => window.clearInterval(timer);
    }, [status]);

    const checkApiStatus = async () => {
        setApiStatus('checking');
        try {
            await api.get('/api/health', { timeout: 2500 });
            setApiStatus('online');
        } catch {
            setApiStatus('offline');
        }
    };

    useEffect(() => {
        void checkApiStatus();
    }, []);

    const visiblePhase =
        uploadProgress !== null && uploadProgress < 100 && elapsedSeconds >= 4
            ? 'Server processing or upload progress unavailable'
            : analysisPhase;

    const fail = (message: string, toastTitle: string) => {
        setErrorMessage(message);
        setStatus('error');
        setUploadProgress(null);
        setAnalysisPhase('Preparing evidence');
        abortControllerRef.current = null;
        setFileUploadKey((k) => k + 1);
        toast({
            variant: "destructive",
            title: toastTitle,
            description: message,
        });
    };

    const succeed = (data: unknown, toastTitle: string, toastDescription: string) => {
        if (isFailedAnalysisPayload(data)) {
            const msg = messageFromPayload(data as Record<string, unknown>);
            fail(msg, "Analysis failed");
            return;
        }
        setResult(data);
        setStatus('success');
        setUploadProgress(null);
        setAnalysisPhase('Preparing evidence');
        abortControllerRef.current = null;
        toast({
            title: toastTitle,
            description: toastDescription,
        });
    };

    const handleCanceledRequest = () => {
        setStatus('idle');
        setResult(null);
        setErrorMessage(null);
        setUploadProgress(null);
        setAnalysisPhase('Preparing evidence');
        abortControllerRef.current = null;
        setFileUploadKey((k) => k + 1);
        toast({
            title: "Analysis canceled",
            description: "Choose another file, URL, or text sample when ready.",
        });
    };

    const createAbortSignal = () => {
        abortControllerRef.current?.abort();
        const controller = new AbortController();
        abortControllerRef.current = controller;
        return controller.signal;
    };

    const validateFile = (file: File): string | null => {
        if (file.size > MAX_FILE_SIZE_BYTES) {
            return `This file is ${(file.size / (1024 * 1024)).toFixed(1)} MB. Use a file under ${MAX_FILE_SIZE_MB} MB.`;
        }

        const isSupported = SUPPORTED_FILE_TYPES.some((prefix) => file.type.startsWith(prefix));
        if (!isSupported) {
            return 'Unsupported file type. Use an image, video, or plain text file.';
        }

        return null;
    };

    const handleUrlSubmit = async (url: string) => {
        if (apiStatus === 'offline') {
            fail('The backend API is offline. Start the FastAPI server on port 8000, then retry.', 'Backend offline');
            return;
        }

        setStatus('analyzing');
        setErrorMessage(null);
        setResult(null);
        setUploadProgress(null);
        setAnalysisPhase('Fetching remote media');
        const signal = createAbortSignal();

        const formData = new FormData();
        formData.append('url', url);

        try {
            const response = await api.post(`/api/analyze/image`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
                signal,
            });
            succeed(response.data, "Analysis Complete", "The content has been processed successfully.");
        } catch (error) {
            if (axios.isCancel(error) || (error as AxiosError).code === 'ERR_CANCELED') {
                handleCanceledRequest();
                return;
            }
            console.error(error);
            fail(extractErrorMessage(error), "Analysis failed");
        }
    };

    const handleFileSelect = async (file: File) => {
        if (apiStatus === 'offline') {
            fail('The backend API is offline. Start the FastAPI server on port 8000 before uploading media.', 'Backend offline');
            return;
        }

        const validationError = validateFile(file);
        if (validationError) {
            fail(validationError, "File rejected");
            return;
        }

        setStatus('analyzing');
        setErrorMessage(null);
        setResult(null);
        setUploadProgress(0);
        setAnalysisPhase('Uploading evidence');
        const signal = createAbortSignal();

        let type: 'image' | 'video' | 'text' = 'text';
        if (file.type.startsWith('image/')) type = 'image';
        else if (file.type.startsWith('video/')) type = 'video';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const endpoint = `/api/analyze/${type}`;

            let response;
            if (type === 'text') {
                setAnalysisPhase('Reading text sample');
                setUploadProgress(null);
                const text = await file.text();
                setAnalysisPhase('Running language model checks');
                response = await api.post(endpoint, null, { params: { text }, signal });
            } else {
                response = await api.post(endpoint, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                    signal,
                    onUploadProgress: (event) => {
                        if (!event.total) {
                            if (event.loaded > 0) setAnalysisPhase('Transferring evidence');
                            return;
                        }
                        const percent = Math.min(100, Math.round((event.loaded * 100) / event.total));
                        setUploadProgress(percent);
                        if (percent >= 98) setAnalysisPhase('Running forensic checks');
                    }
                });
            }

            succeed(response.data, "Analysis Complete", `Successfully analyzed ${file.name}`);
        } catch (error) {
            if (axios.isCancel(error) || (error as AxiosError).code === 'ERR_CANCELED') {
                handleCanceledRequest();
                return;
            }
            console.error(error);
            fail(extractErrorMessage(error), "Analysis failed");
        }
    };

    const handleTextSubmit = async (text: string) => {
        if (apiStatus === 'offline') {
            fail('The backend API is offline. Start the FastAPI server on port 8000 before analyzing text.', 'Backend offline');
            return;
        }

        const trimmedText = text.trim();
        if (trimmedText.length < 20) {
            fail('Paste at least 20 characters so the text detector has enough signal.', 'Text too short');
            return;
        }

        setStatus('analyzing');
        setErrorMessage(null);
        setResult(null);
        setUploadProgress(null);
        setAnalysisPhase('Running language model checks');
        const signal = createAbortSignal();

        try {
            const response = await api.post('/api/analyze/text', null, {
                params: { text: trimmedText },
                signal,
            });
            succeed(response.data, "Analysis Complete", "Successfully analyzed pasted text.");
        } catch (error) {
            if (axios.isCancel(error) || (error as AxiosError).code === 'ERR_CANCELED') {
                handleCanceledRequest();
                return;
            }
            console.error(error);
            fail(extractErrorMessage(error), "Analysis failed");
        }
    };

    const handleCancel = () => {
        abortControllerRef.current?.abort();
    };

    const handleReset = () => {
        abortControllerRef.current?.abort();
        abortControllerRef.current = null;
        setStatus('idle');
        setResult(null);
        setErrorMessage(null);
        setUploadProgress(null);
        setAnalysisPhase('Preparing evidence');
        setFileUploadKey((k) => k + 1);
    };

    return (
        <div className="space-y-12">
            <div className="text-center space-y-4">
                <h2 className="text-4xl font-extrabold tracking-tight lg:text-5xl">Content Analyzer</h2>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                    Upload media or provide a URL to uncover hidden AI artifacts using our deep learning ensemble.
                </p>
                <div className="mx-auto flex w-fit items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
                    <Server className="h-3.5 w-3.5" />
                    <span>
                        API {apiStatus === 'checking' ? 'checking' : apiStatus === 'online' ? 'online' : 'offline'}
                    </span>
                    {apiStatus === 'offline' && (
                        <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="h-6 gap-1 px-2 text-xs"
                            onClick={checkApiStatus}
                        >
                            <RefreshCw className="h-3 w-3" />
                            Recheck
                        </Button>
                    )}
                </div>
            </div>

            <div className="max-w-4xl mx-auto">
                <FileUpload
                    key={fileUploadKey}
                    onFileSelect={handleFileSelect}
                    onUrlSubmit={handleUrlSubmit}
                    onTextSubmit={handleTextSubmit}
                    isAnalyzing={status === 'analyzing'}
                    uploadProgress={uploadProgress}
                    analysisPhase={visiblePhase}
                />
            </div>

            {status === 'analyzing' && (
                <div className="mx-auto flex max-w-xl flex-col items-center justify-center rounded-xl border bg-card p-8 text-center shadow-sm">
                    <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary/10 text-primary">
                        {uploadProgress !== null && uploadProgress < 100 ? (
                            <UploadCloud className="h-7 w-7" />
                        ) : (
                            <Loader2 className="h-7 w-7 animate-spin" />
                        )}
                    </div>
                    <p className="text-lg font-semibold text-foreground">{visiblePhase}</p>
                    <p className="mt-1 text-sm text-muted-foreground">
                        {uploadProgress !== null && uploadProgress < 100 && elapsedSeconds < 4
                            ? 'Transferring the file to the local API.'
                            : 'The backend is running model inference and forensic checks. Large videos can take longer.'}
                    </p>
                    {uploadProgress !== null && (
                        <div className="mt-5 w-full space-y-2">
                            <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                                <span>Upload progress</span>
                                <span>{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} className="h-2" />
                        </div>
                    )}
                    <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                        <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground">
                            <Clock className="h-3.5 w-3.5 text-primary" />
                            {elapsedSeconds}s elapsed
                        </div>
                        <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium text-muted-foreground">
                            <ShieldCheck className="h-3.5 w-3.5 text-primary" />
                            Temporary files are cleared after analysis
                        </div>
                    </div>
                    <Button variant="outline" className="mt-5 gap-2" onClick={handleCancel}>
                        <Square className="h-3.5 w-3.5" />
                        Cancel analysis
                    </Button>
                </div>
            )}

            {status === 'success' && result && (
                <div className="animate-fade-in-up">
                    <ResultsDashboard result={result} onReset={handleReset} />
                </div>
            )}

            {status === 'error' && (
                <div className="p-6 bg-destructive/10 border border-destructive/20 rounded-xl max-w-lg mx-auto space-y-4">
                    <div className="text-center space-y-1">
                        <h3 className="text-lg font-semibold text-destructive">Analysis failed</h3>
                        <p className="text-sm text-muted-foreground">
                            The request did not return a usable result.
                        </p>
                    </div>
                    <p className="rounded-lg border border-destructive/20 bg-background/70 p-3 text-sm text-destructive/90 whitespace-pre-wrap">
                        {errorMessage ??
                            'No error details were captured. Make sure the backend API is running on port 8000, then choose a file or URL again.'}
                    </p>
                    <Button variant="outline" className="w-full" onClick={handleReset}>
                        Choose another file or URL
                    </Button>
                </div>
            )}
        </div>
    );
};

export default Analysis;
