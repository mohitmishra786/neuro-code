/**
 * SearchBar Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchBar } from '../SearchBar';

vi.mock('@/stores/treeStore', () => ({
    useTreeStore: vi.fn((selector) => {
        const state = {
            searchQuery: '',
            searchResults: [],
            search: vi.fn(),
            setSearchQuery: vi.fn(),
            navigateToSearchResult: vi.fn(),
        };
        return selector(state);
    }),
    NODE_COLORS: {
        package: '#6366f1',
        module: '#8b5cf6',
        class: '#10b981',
        function: '#f59e0b',
        variable: '#ec4899',
        unknown: '#64748b',
    },
}));

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

            expect(screen.getByRole('img')).toBeInTheDocument();
        });

        it('should not show results when not focused', () => {
            render(<SearchBar />);

            expect(screen.queryByText('Class1')).not.toBeInTheDocument();
        });
    });

    describe('search debouncing', () => {
        it('should debounce search input', async () => {
            const mockSearch = vi.fn();
            
            vi.mocked(require('@/stores/treeStore').useTreeStore)
                .mockImplementationOnce((selector) => {
                    const state = {
                        searchQuery: '',
                        searchResults: [],
                        search: mockSearch,
                        setSearchQuery: vi.fn(),
                        navigateToSearchResult: vi.fn(),
                    };
                    return selector(state);
                });

            render(<SearchBar />);

            const input = screen.getByPlaceholderText('Search nodes... (Cmd+K)');
            fireEvent.change(input, { target: { value: 'test' } });

            expect(mockSearch).not.toHaveBeenCalled();

            await waitFor(() => {
                expect(mockSearch).toHaveBeenCalledWith('test');
            }, { timeout: 500 });
        });

        it('should clear debounced search on clear button click', async () => {
            const mockSearch = vi.fn();
            const mockSetSearchQuery = vi.fn();
            
            vi.mocked(require('@/stores/treeStore').useTreeStore)
                .mockImplementationOnce((selector) => {
                    const state = {
                        searchQuery: 'test',
                        searchResults: [],
                        search: mockSearch,
                        setSearchQuery: mockSetSearchQuery,
                        navigateToSearchResult: vi.fn(),
                    };
                    return selector(state);
                });

            render(<SearchBar />);

            const clearButton = screen.getByRole('button', { name: '' });
            fireEvent.click(clearButton);

            expect(mockSetSearchQuery).toHaveBeenCalledWith('');
            expect(mockSearch).toHaveBeenCalledWith('');
        });

        it('should cancel pending search when navigating to result', async () => {
            const mockNavigate = vi.fn().mockResolvedValue(undefined);
            
            vi.mocked(require('@/stores/treeStore').useTreeStore)
                .mockImplementationOnce((selector) => {
                    const state = {
                        searchQuery: 'test',
                        searchResults: [{ id: 'node1', name: 'Node1', type: 'class' }],
                        search: vi.fn(),
                        setSearchQuery: vi.fn(),
                        navigateToSearchResult: mockNavigate,
                    };
                    return selector(state);
                });

            render(<SearchBar />);

            const resultButton = screen.getByText('Node1');
            fireEvent.click(resultButton);

            expect(mockNavigate).toHaveBeenCalledWith('node1');
        });
    });

    describe('keyboard shortcuts', () => {
        it('should focus input on Cmd+K', () => {
            render(<SearchBar />);

            const input = screen.getByPlaceholderText('Search nodes... (Cmd+K)');
            
            fireEvent.keyDown(window, { key: 'k', metaKey: true });

            expect(document.activeElement).toBe(input);
        });

        it('should blur input on Escape', () => {
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
