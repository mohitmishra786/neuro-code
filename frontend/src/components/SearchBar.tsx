/**
 * NeuroCode Search Bar Component
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { useGraphStore } from '@/stores/graphStore';
import { NODE_COLORS } from '@/utils/colorScheme';

export function SearchBar() {
    const [query, setQuery] = useState('');
    const [isFocused, setIsFocused] = useState(false);
    const searchResults = useGraphStore((state) => state.searchResults);
    const searchNodes = useGraphStore((state) => state.searchNodes);
    const focusNode = useGraphStore((state) => state.focusNode);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleSearch = useCallback(
        (value: string) => {
            setQuery(value);
            searchNodes(value);
        },
        [searchNodes],
    );

    const handleResultClick = useCallback(
        (nodeId: string) => {
            focusNode(nodeId);
            setQuery('');
            setIsFocused(false);
            searchNodes('');
        },
        [focusNode, searchNodes],
    );

    // Keyboard shortcut
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                inputRef.current?.focus();
            }
            if (e.key === 'Escape') {
                inputRef.current?.blur();
                setIsFocused(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    return (
        <div className="search-bar">
            <div className="search-input-wrapper">
                <svg className="search-icon" viewBox="0 0 20 20" fill="currentColor">
                    <path
                        fillRule="evenodd"
                        d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                        clipRule="evenodd"
                    />
                </svg>
                <input
                    ref={inputRef}
                    type="text"
                    value={query}
                    onChange={(e) => handleSearch(e.target.value)}
                    onFocus={() => setIsFocused(true)}
                    onBlur={() => setTimeout(() => setIsFocused(false), 200)}
                    placeholder="Search nodes... (Cmd+K)"
                    className="search-input"
                />
                {query && (
                    <button className="search-clear" onClick={() => handleSearch('')}>
                        <svg viewBox="0 0 20 20" fill="currentColor">
                            <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                                clipRule="evenodd"
                            />
                        </svg>
                    </button>
                )}
            </div>

            {isFocused && searchResults.length > 0 && (
                <div className="search-results">
                    {searchResults.slice(0, 10).map((result) => (
                        <button
                            key={result.id}
                            className="search-result-item"
                            onClick={() => handleResultClick(result.id)}
                        >
                            <span
                                className="search-result-type"
                                style={{ backgroundColor: NODE_COLORS[result.type]?.base || '#6b7280' }}
                            >
                                {result.type.charAt(0).toUpperCase()}
                            </span>
                            <div className="search-result-info">
                                <span className="search-result-name">{result.name}</span>
                                {result.qualifiedName && (
                                    <span className="search-result-qualified">{result.qualifiedName}</span>
                                )}
                            </div>
                            {result.lineNumber && (
                                <span className="search-result-line">L{result.lineNumber}</span>
                            )}
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

export default SearchBar;
