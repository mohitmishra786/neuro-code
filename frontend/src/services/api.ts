/**
 * NeuroCode API Client
 *
 * HTTP client for the backend API.
 */

import {
    ApiNode,
    SearchResponse,
    ReferencesResponse,
    GraphNode,
    ProjectTreeNode,
    isValidApiNode,
    isValidSearchResponse,
    isValidRootNodesResponse,
    isValidChildrenResponse,
    isValidAncestorsResponse,
} from '@/types/graph.types';
import { ApiError } from '@/types/errors';

/** API base URL from environment or default. */
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Request deduplication with cancellation support
const pendingRequests = new Map<string, { promise: Promise<unknown>; controller: AbortController }>();

function createAbortController(): AbortController {
    return new AbortController();
}

/**
 * Generic fetcher function type with AbortSignal support.
 * @typeParam T - The expected return type of the fetcher
 */
type Fetcher<T> = (signal: AbortSignal) => Promise<T>;

async function dedupedFetch<T>(
    key: string,
    fetcher: Fetcher<T>,
    options?: { timeout?: number },
): Promise<T> {
    const existing = pendingRequests.get(key);
    if (existing) {
        return existing.promise as Promise<T>;
    }

    const controller = createAbortController();
    const timeoutId = options?.timeout
        ? window.setTimeout(() => controller.abort(), options.timeout)
        : null;

    const promise = (async () => {
        try {
            const result = await fetcher(controller.signal);
            return result;
        } finally {
            pendingRequests.delete(key);
            if (timeoutId) {
                clearTimeout(timeoutId);
            }
        }
    })();

    pendingRequests.set(key, { promise, controller });
    return promise;
}

// Cancel a pending request
export function cancelRequest(key: string): void {
    const existing = pendingRequests.get(key);
    if (existing) {
        existing.controller.abort();
        pendingRequests.delete(key);
    }
}

// Cancel all pending requests
export function cancelAllRequests(): void {
    for (const [, { controller }] of pendingRequests) {
        controller.abort();
    }
    pendingRequests.clear();
}

/**
 * Fetch JSON response with type safety.
 * @typeParam T - The expected JSON response type
 */
async function fetchJson<T>(
    url: string,
    options?: RequestInit & { signal?: AbortSignal },
): Promise<T> {
    const response = await fetch(url, {
        ...options,
        signal: options?.signal,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = 'Unknown error';
        try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson?.message || errorJson?.detail || errorText;
        } catch {
            errorMessage = errorText || 'Unknown error';
        }
        throw new ApiError(response.status, errorMessage);
    }

    const text = await response.text();
    if (!text) {
        return {} as T;
    }

    const json = JSON.parse(text);
    return json as T;
}

function apiNodeToGraphNode(node: ApiNode, isExpanded = false): GraphNode {
    return {
        id: node.id,
        name: node.name,
        type: node.type,
        qualifiedName: node.qualified_name,
        lineNumber: node.line_number,
        docstring: node.docstring,
        childCount: node.child_count,
        isExpanded,
        isAsync: node.is_async,
        isMethod: node.is_method,
        isAbstract: node.is_abstract,
        complexity: node.complexity,
        returnType: node.return_type,
        typeHint: node.type_hint,
    };
}

// Entry point response type
interface EntryPointResponse {
    readonly entry_point: ApiNode | null;
    readonly imports: readonly ApiNode[];
    readonly all_modules: readonly ApiNode[];
}

export const api = {
    /**
     * Get entry point and its imports for initial flow display
     */
    async getEntryPoint(): Promise<{
        entryPoint: GraphNode | null;
        imports: GraphNode[];
        allModules: GraphNode[];
    }> {
        return dedupedFetch('entry-point', async (signal) => {
            const response = await fetchJson<EntryPointResponse>(
                `${API_BASE}/graph/entry-point`,
                { signal },
            );
            return {
                entryPoint: response.entry_point ? apiNodeToGraphNode(response.entry_point) : null,
                imports: response.imports.map((n) => apiNodeToGraphNode(n)),
                allModules: response.all_modules.map((n) => apiNodeToGraphNode(n)),
            };
        });
    },

    /**
     * Get root-level modules
     */
    async getRootNodes(): Promise<GraphNode[]> {
        return dedupedFetch('root', async (signal) => {
            const rawResponse = await fetchJson<unknown>(
                `${API_BASE}/graph/root`,
                { signal },
            );
            if (!isValidRootNodesResponse(rawResponse)) {
                throw new ApiError(500, 'Invalid response format from server');
            }
            return rawResponse.nodes.map((n) => apiNodeToGraphNode(n));
        });
    },

    /**
     * Get a single node by ID
     */
    async getNode(nodeId: string): Promise<GraphNode> {
        return dedupedFetch(`node:${nodeId}`, async (signal) => {
            const encodedId = encodeURIComponent(nodeId);
            const rawNode = await fetchJson<unknown>(
                `${API_BASE}/graph/node/${encodedId}`,
                { signal },
            );
            if (!isValidApiNode(rawNode)) {
                throw new ApiError(500, 'Invalid node response format');
            }
            return apiNodeToGraphNode(rawNode);
        });
    },

    /**
     * Get immediate children of a node
     */
    async getNodeChildren(nodeId: string, limit = 1000): Promise<GraphNode[]> {
        return dedupedFetch(`children:${nodeId}`, async (signal) => {
            const encodedId = encodeURIComponent(nodeId);
            const rawResponse = await fetchJson<unknown>(
                `${API_BASE}/graph/node/${encodedId}/children?limit=${limit}`,
                { signal },
            );
            if (!isValidChildrenResponse(rawResponse)) {
                throw new ApiError(500, 'Invalid children response format');
            }
            return rawResponse.children.map((n) => apiNodeToGraphNode(n));
        });
    },

    /**
     * Get ancestors of a node (for breadcrumbs)
     */
    async getNodeAncestors(nodeId: string): Promise<GraphNode[]> {
        return dedupedFetch(`ancestors:${nodeId}`, async (signal) => {
            const encodedId = encodeURIComponent(nodeId);
            const rawResponse = await fetchJson<unknown>(
                `${API_BASE}/graph/node/${encodedId}/ancestors`,
                { signal },
            );
            if (!isValidAncestorsResponse(rawResponse)) {
                throw new ApiError(500, 'Invalid ancestors response format');
            }
            return rawResponse.ancestors.map((n) => apiNodeToGraphNode(n));
        });
    },

    /**
     * Get all references to/from a node
     */
    async getNodeReferences(nodeId: string): Promise<ReferencesResponse> {
        return dedupedFetch(`references:${nodeId}`, async (signal) => {
            return fetchJson<ReferencesResponse>(
                `${API_BASE}/graph/node/${nodeId}/references`,
                { signal },
            );
        });
    },

    /**
     * Expand a node to get children + outgoing connections (for incremental loading)
     */
    async expandNode(nodeId: string): Promise<{
        node: GraphNode | null;
        children: GraphNode[];
        outgoing: { id: string; name: string; type: string; edgeType: string }[];
    }> {
        return dedupedFetch(`expand:${nodeId}`, async (signal) => {
            const encodedId = encodeURIComponent(nodeId);
            const response = await fetchJson<{
                node: ApiNode | null;
                children: ApiNode[];
                outgoing: { id: string; name: string; type: string; edge_type: string }[];
            }>(`${API_BASE}/graph/expand/${encodedId}`, { signal });
            return {
                node: response.node ? apiNodeToGraphNode(response.node) : null,
                children: response.children.map((n) => apiNodeToGraphNode(n)),
                outgoing: response.outgoing.map((o) => ({
                    id: o.id,
                    name: o.name,
                    type: o.type,
                    edgeType: o.edge_type,
                })),
            };
        });
    },

    /**
     * Search for nodes
     */
    async search(query: string, limit = 50, typeFilter?: string): Promise<SearchResponse> {
        const params = new URLSearchParams({ q: query, limit: String(limit) });
        if (typeFilter) {
            params.set('type_filter', typeFilter);
        }
        const rawResponse = await fetchJson<unknown>(
            `${API_BASE}/search?${params}`,
        );
        if (!isValidSearchResponse(rawResponse)) {
            throw new ApiError(500, 'Invalid search response format');
        }
        return rawResponse;
    },

    /**
     * Get autocomplete suggestions
     */
    async getSuggestions(query: string, limit = 10): Promise<{ name: string; type: string }[]> {
        const params = new URLSearchParams({ q: query, limit: String(limit) });
        const response = await fetchJson<{ suggestions: { name: string; type: string }[] }>(
            `${API_BASE}/search/suggest?${params}`,
        );
        return response.suggestions;
    },

    /**
     * Parse a codebase
     */
    async parseCodebase(
        path: string,
        recursive = true,
    ): Promise<{ status: string; modules_parsed: number; errors: string[] }> {
        return fetchJson(`${API_BASE}/graph/parse`, {
            method: 'POST',
            body: JSON.stringify({ path, recursive }),
        });
    },

    /**
     * Update changed files
     */
    async updateFiles(
        paths: string[],
    ): Promise<{ status: string; files_updated: number; nodes_added: number }> {
        return fetchJson(`${API_BASE}/graph/update`, {
            method: 'POST',
            body: JSON.stringify({ paths }),
        });
    },

    /**
     * Clear the graph
     */
    async clearGraph(): Promise<{ status: string }> {
        return fetchJson(`${API_BASE}/graph/clear`, { method: 'DELETE' });
    },

    async getProjectTree(path: string, recursive = true): Promise<ProjectTreeNode> {
        return fetchJson(`${API_BASE}/graph/tree?path=${encodeURIComponent(path)}&recursive=${recursive}`);
    },

    /**
     * Health check
     */
    async healthCheck(): Promise<{ status: string; version: string; neo4j: string }> {
        return fetchJson(`${API_BASE}/health`);
    },
};

export default api;
