/**
 * ErrorBoundary Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorBoundary } from '../ErrorBoundary';
import { Component, ErrorInfo, ReactNode } from 'react';

describe('ErrorBoundary', () => {
    const originalError = console.error;
    beforeEach(() => {
        console.error = vi.fn();
    });
    afterEach(() => {
        console.error = originalError;
    });

    it('should render children when no error', () => {
        render(
            <ErrorBoundary>
                <div data-testid="child">Child Content</div>
            </ErrorBoundary>,
        );
        expect(screen.getByTestId('child')).toHaveTextContent('Child Content');
    });

    it('should render fallback when error occurs', () => {
        const ThrowError = (): null => {
            throw new Error('Test error');
        };

        render(
            <ErrorBoundary
                fallback={<div data-testid="custom-fallback">Custom Fallback</div>}
            >
                <ThrowError />
            </ErrorBoundary>,
        );

        expect(screen.queryByTestId('child')).not.toBeInTheDocument();
        expect(screen.getByTestId('custom-fallback')).toHaveTextContent('Custom Fallback');
    });

    it('should render default fallback when error occurs and no custom fallback', () => {
        const ThrowError = (): null => {
            throw new Error('Test error');
        };

        render(
            <ErrorBoundary>
                <ThrowError />
            </ErrorBoundary>,
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();
        expect(screen.getByText('Test error')).toBeInTheDocument();
    });

    it('should reset error state when retry button is clicked', () => {
        let shouldThrow = true;
        const ToggleError = (): ReactNode => {
            if (shouldThrow) {
                throw new Error('Test error');
            }
            return <div data-testid="recovered">Recovered</div>;
        };

        const { rerender } = render(
            <ErrorBoundary>
                <ToggleError />
            </ErrorBoundary>,
        );

        expect(screen.getByText('Something went wrong')).toBeInTheDocument();

        shouldThrow = false;
        const retryButton = screen.getByText('Try Again');
        fireEvent.click(retryButton);

        rerender(
            <ErrorBoundary>
                <ToggleError />
            </ErrorBoundary>,
        );

        expect(screen.queryByText('Something went wrong')).not.toBeInTheDocument();
        expect(screen.getByTestId('recovered')).toHaveTextContent('Recovered');
    });
});
