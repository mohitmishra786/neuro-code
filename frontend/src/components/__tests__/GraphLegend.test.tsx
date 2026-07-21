import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { GraphLegend } from '@/components/GraphLegend';

describe('GraphLegend', () => {
    it('renders node and edge legend entries', () => {
        render(<GraphLegend />);
        expect(screen.getByLabelText('Graph legend')).toBeInTheDocument();
        expect(screen.getByText('Package')).toBeInTheDocument();
        expect(screen.getByText('Class')).toBeInTheDocument();
        expect(screen.getByText('Calls')).toBeInTheDocument();
        expect(screen.getByText(/Double-click/i)).toBeInTheDocument();
    });
});
