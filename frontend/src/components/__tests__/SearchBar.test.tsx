/**
 * SearchBar Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchBar } from '../SearchBar';

describe('SearchBar', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('rendering', () => {
        it('should render search input', () => {
            render(<SearchBar />);
            expect(screen.getByPlaceholderText('Search nodes... (Cmd+K)')).toBeInTheDocument();
        });

        it('should show search icon', () => {
            render(<SearchBar />);
            expect(screen.getByTestId('search-icon')).toBeInTheDocument();
        });

        it('should not show results when not focused', () => {
            render(<SearchBar />);
            expect(screen.queryByText('Class1')).not.toBeInTheDocument();
        });
    });

    describe('keyboard shortcuts', () => {
        it('should focus input on Cmd+K', () => {
            render(<SearchBar />);
            const input = screen.getByPlaceholderText('Search nodes... (Cmd+K)');
            fireEvent.keyDown(window, { key: 'k', metaKey: true });
            expect(document.activeElement).toBe(input);
        });

        it('should blur input on Escape', async () => {
            render(<SearchBar />);
            const input = screen.getByPlaceholderText('Search nodes... (Cmd+K)');
            input.focus();
            expect(document.activeElement).toBe(input);
            fireEvent.keyDown(window, { key: 'Escape' });
            await waitFor(() => {
                expect(document.activeElement).not.toBe(input);
            });
        });
    });
});
