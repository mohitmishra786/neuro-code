import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { FirstRunTour } from '@/components/FirstRunTour';

describe('FirstRunTour', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    it('shows tip until dismissed', () => {
        render(<FirstRunTour />);
        expect(screen.getByLabelText('Getting started')).toBeInTheDocument();
        fireEvent.click(screen.getByText('Got it'));
        expect(screen.queryByLabelText('Getting started')).not.toBeInTheDocument();
        expect(localStorage.getItem('neurocode-first-run-dismissed')).toBe('1');
    });
});
