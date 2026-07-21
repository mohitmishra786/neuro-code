/**
 * NeuroCode Error Types
 *
 * Centralized error type definitions for the application.
 */

export class NeuroCodeError extends Error {
    constructor(
        message: string,
        public readonly code: string,
        public readonly context?: Record<string, unknown>,
    ) {
        super(message);
        this.name = 'NeuroCodeError';
    }
}

/** HTTP API failure with status code (used by services/api.ts). */
export class ApiError extends NeuroCodeError {
    constructor(
        public readonly status: number,
        message: string,
        context?: Record<string, unknown>,
    ) {
        super(message, 'API_ERROR', { status, ...context });
        this.name = 'ApiError';
    }
}

export class ApiValidationError extends NeuroCodeError {
    constructor(
        message: string,
        public readonly field?: string,
        public readonly receivedValue?: unknown,
    ) {
        super(message, 'API_VALIDATION_ERROR', { field, receivedValue });
        this.name = 'ApiValidationError';
    }
}

export class ParseError extends NeuroCodeError {
    constructor(
        message: string,
        public readonly filePath?: string,
        public readonly lineNumber?: number,
    ) {
        super(message, 'PARSE_ERROR', { filePath, lineNumber });
        this.name = 'ParseError';
    }
}

export class GraphError extends NeuroCodeError {
    constructor(
        message: string,
        public readonly nodeId?: string,
        public readonly operation?: string,
    ) {
        super(message, 'GRAPH_ERROR', { nodeId, operation });
        this.name = 'GraphError';
    }
}

export class CacheError extends NeuroCodeError {
    constructor(
        message: string,
        public readonly cacheKey?: string,
    ) {
        super(message, 'CACHE_ERROR', { cacheKey });
        this.name = 'CacheError';
    }
}

export class WebSocketError extends NeuroCodeError {
    constructor(
        message: string,
        public readonly url?: string,
        public readonly readyState?: number,
    ) {
        super(message, 'WEBSOCKET_ERROR', { url, readyState });
        this.name = 'WebSocketError';
    }
}

// Error code constants
export const ErrorCodes = {
    UNKNOWN: 'UNKNOWN',
    API_ERROR: 'API_ERROR',
    API_VALIDATION_ERROR: 'API_VALIDATION_ERROR',
    PARSE_ERROR: 'PARSE_ERROR',
    GRAPH_ERROR: 'GRAPH_ERROR',
    CACHE_ERROR: 'CACHE_ERROR',
    WEBSOCKET_ERROR: 'WEBSOCKET_ERROR',
    NETWORK_ERROR: 'NETWORK_ERROR',
    TIMEOUT_ERROR: 'TIMEOUT_ERROR',
    PERMISSION_DENIED: 'PERMISSION_DENIED',
    NOT_FOUND: 'NOT_FOUND',
    CONFLICT: 'CONFLICT',
} as const;

export type ErrorCode = typeof ErrorCodes[keyof typeof ErrorCodes];

// Error handler utility
export function handleError(error: unknown): NeuroCodeError {
    if (error instanceof NeuroCodeError) {
        return error;
    }

    if (error instanceof Error) {
        return new NeuroCodeError(
            error.message,
            ErrorCodes.UNKNOWN,
            { originalError: error.name },
        );
    }

    return new NeuroCodeError(
        'An unknown error occurred',
        ErrorCodes.UNKNOWN,
        { originalError: String(error) },
    );
}

// Type guard for NeuroCodeError
export function isNeuroCodeError(value: unknown): value is NeuroCodeError {
    return (
        value instanceof NeuroCodeError ||
        (typeof value === 'object' &&
            value !== null &&
            'name' in value &&
            'code' in value &&
            (value as { name: string }).name === 'NeuroCodeError')
    );
}

export default NeuroCodeError;
