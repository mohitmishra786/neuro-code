/**
 * Dismissible first-run tip for graph discoverability.
 */

import { useCallback, useState } from 'react';

const STORAGE_KEY = 'neurocode-first-run-dismissed';

function readInitialVisible(): boolean {
    try {
        return localStorage.getItem(STORAGE_KEY) !== '1';
    } catch {
        return true;
    }
}

export function FirstRunTour() {
    const [visible, setVisible] = useState(readInitialVisible);

    const dismiss = useCallback(() => {
        setVisible(false);
        try {
            localStorage.setItem(STORAGE_KEY, '1');
        } catch {
            /* ignore */
        }
    }, []);

    if (!visible) return null;

    return (
        <div className="first-run-tour" role="dialog" aria-label="Getting started">
            <div className="first-run-tour-content">
                <strong>Getting started</strong>
                <ol>
                    <li>
                        <strong>Click</strong> a node to see details in the sidebar
                    </li>
                    <li>
                        <strong>Double-click</strong> a node with a badge to expand children
                    </li>
                    <li>Use search to jump to a symbol by name</li>
                </ol>
                <p className="first-run-tour-hint">Desktop mouse recommended. Dark theme is the default.</p>
                <button type="button" className="first-run-tour-btn" onClick={dismiss}>
                    Got it
                </button>
            </div>
        </div>
    );
}
