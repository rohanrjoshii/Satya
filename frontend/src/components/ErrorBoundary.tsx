import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface ErrorBoundaryProps {
    children: React.ReactNode;
}

interface ErrorBoundaryState {
    error: Error | null;
}

class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    state: ErrorBoundaryState = {
        error: null
    };

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { error };
    }

    componentDidCatch(error: Error, info: React.ErrorInfo) {
        console.error('Satya UI crashed', error, info);
    }

    handleReset = () => {
        this.setState({ error: null });
    };

    render() {
        if (!this.state.error) return this.props.children;

        return (
            <div className="mx-auto mt-16 max-w-xl rounded-xl border border-destructive/20 bg-destructive/10 p-6 text-center shadow-sm">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-background text-destructive">
                    <AlertTriangle className="h-6 w-6" />
                </div>
                <h2 className="text-xl font-semibold text-foreground">This view could not render</h2>
                <p className="mt-2 text-sm text-muted-foreground">
                    The server returned data in an unexpected shape. Your upload was not changed.
                </p>
                <pre className="mt-4 max-h-32 overflow-auto rounded-md bg-background p-3 text-left text-xs text-muted-foreground">
                    {this.state.error.message}
                </pre>
                <Button className="mt-5 gap-2" variant="outline" onClick={this.handleReset}>
                    <RotateCcw className="h-4 w-4" />
                    Retry view
                </Button>
            </div>
        );
    }
}

export default ErrorBoundary;
