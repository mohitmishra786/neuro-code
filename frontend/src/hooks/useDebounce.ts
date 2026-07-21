/**
 * useDebounce Hook
 *
 * Debounces a value for reducing update frequency.
 */

import { useEffect, useState } from 'react';

/**
 * Debounce a value with type safety.
 * @typeParam T - The type of value to debounce
 */
export function useDebounce<T>(value: T, delay: number = 300): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);

    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedValue(value);
        }, delay);

        return () => {
            clearTimeout(timer);
        };
    }, [value, delay]);

    return debouncedValue;
}

/**
 * Debounce a callback function.
 * @typeParam T - The callback function type
 */
export function useDebouncedCallback<T extends (...args: Parameters<T>) => ReturnType<T>>(
    callback: T,
    delay: number = 300,
): T {
    const [timeoutId, setTimeoutId] = useState<number | null>(null);

    const debouncedCallback = ((...args: Parameters<T>) => {
        if (timeoutId) {
            clearTimeout(timeoutId);
        }

        const id = window.setTimeout(() => {
            callback(...args);
        }, delay);

        setTimeoutId(id);
    }) as T;

    useEffect(() => {
        return () => {
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        };
    }, [timeoutId]);

    return debouncedCallback;
}

export default useDebounce;
