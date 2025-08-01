'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { EULA_CONTENT, EULA_VERSION } from './EULA';
import { X, FileText, AlertTriangle, CheckCircle } from 'lucide-react';

interface EULAModalProps {
  isOpen: boolean;
  onAccept: () => void;
  onDecline: () => void;
}

export function EULAModal({ isOpen, onAccept, onDecline }: EULAModalProps) {
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);

  useEffect(() => {
    if (isOpen) {
      const timer = setInterval(() => {
        setTimeSpent((prev) => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [isOpen]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const element = e.currentTarget;
    const isAtBottom = element.scrollHeight - element.scrollTop - element.clientHeight < 50;
    if (isAtBottom && timeSpent >= 5) {
      setHasScrolledToBottom(true);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <Card className="max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-3">
            <FileText className="h-6 w-6 text-primary" />
            <div>
              <h2 className="text-2xl font-bold">{EULA_CONTENT.title}</h2>
              <p className="text-sm text-muted-foreground">
                Version {EULA_CONTENT.version} • Last updated: {EULA_CONTENT.lastUpdated}
              </p>
            </div>
          </div>
          <button
            onClick={onDecline}
            className="p-2 hover:bg-accent rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div 
          className="flex-1 overflow-y-auto p-6 space-y-6"
          onScroll={handleScroll}
        >
          {/* Warning Banner */}
          <div className="flex items-start gap-3 p-4 bg-orange-500/10 border border-orange-500/20 rounded-lg">
            <AlertTriangle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold text-orange-500 mb-1">ALPHA SOFTWARE WARNING</p>
              <p className="text-muted-foreground">
                This is experimental software in active development. Use at your own risk. 
                Do not invest more than you can afford to lose.
              </p>
            </div>
          </div>

          {/* EULA Sections */}
          {EULA_CONTENT.sections.map((section, index) => (
            <div key={index} className="space-y-2">
              <h3 className="text-lg font-semibold">{section.title}</h3>
              <div className="text-sm text-muted-foreground whitespace-pre-line">
                {section.content}
              </div>
            </div>
          ))}

          {/* Acknowledgment */}
          <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
            <h4 className="font-semibold mb-2 flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-primary" />
              Acknowledgment
            </h4>
            <p className="text-sm text-muted-foreground whitespace-pre-line">
              {EULA_CONTENT.acknowledgment}
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t space-y-4">
          {!hasScrolledToBottom && (
            <p className="text-sm text-center text-muted-foreground">
              Please read the entire agreement before accepting
            </p>
          )}
          
          <div className="flex gap-4">
            <button
              onClick={onDecline}
              className="flex-1 px-4 py-2 border border-border rounded-lg hover:bg-accent transition-colors"
            >
              Decline
            </button>
            <button
              onClick={onAccept}
              disabled={!hasScrolledToBottom}
              className={`flex-1 px-4 py-2 rounded-lg transition-colors ${
                hasScrolledToBottom
                  ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                  : 'bg-muted text-muted-foreground cursor-not-allowed'
              }`}
            >
              {hasScrolledToBottom ? 'I Accept' : 'Please Read Agreement First'}
            </button>
          </div>
          
          <p className="text-xs text-center text-muted-foreground">
            By accepting, you confirm that you are at least 18 years old and agree to all terms
          </p>
        </div>
      </Card>
    </div>
  );
}

// Hook to check if EULA has been accepted
export function useEULAAcceptance() {
  const [hasAccepted, setHasAccepted] = useState<boolean | null>(null);

  useEffect(() => {
    const stored = localStorage.getItem('eula_acceptance');
    if (stored) {
      const acceptance = JSON.parse(stored);
      // Check if accepted version matches current version
      setHasAccepted(acceptance.version === EULA_VERSION);
    } else {
      setHasAccepted(false);
    }
  }, []);

  const acceptEULA = () => {
    const acceptance = {
      version: EULA_VERSION,
      timestamp: new Date().toISOString(),
      accepted: true
    };
    localStorage.setItem('eula_acceptance', JSON.stringify(acceptance));
    setHasAccepted(true);
  };

  const resetEULA = () => {
    localStorage.removeItem('eula_acceptance');
    setHasAccepted(false);
  };

  return { hasAccepted, acceptEULA, resetEULA };
}