import { Info } from 'lucide-react';

const EducationalTooltips = ({ text }: { text: string }) => {
    return (
        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-md flex items-start gap-3">
            <Info className="flex-shrink-0 text-blue-500 w-5 h-5 mt-0.5" />
            <p className="text-sm text-blue-800 leading-relaxed font-medium">
                <span className="font-bold underline">Tip:</span> {text}
            </p>
        </div>
    );
};

export default EducationalTooltips;
