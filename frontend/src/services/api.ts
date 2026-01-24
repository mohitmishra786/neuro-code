/**
 * NeuroCode API Client
 *
 * HTTP client for the backend API.
 */

import {
    ApiNode,
    RootNodesResponse,
    ChildrenResponse,
    AncestorsResponse,
    SearchResponse,
    ReferencesResponse,
    GraphNode,
    ProjectTreeNode,
} from '@/types/graph.types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiError extends Error {
    constructor(
        public status: number,
        message: string,
    ) {
        super(message);
        this.name = 'ApiError';
    }
}

// Request deduplication
const pendingRequests = new Map<string, Promise<unknown>>();

async function dedupedFetch<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
    const pending = pendingRequests.get(key);
    if (pending) {
        return pending as Promise<T>;
    }

    const promise = fetcher().finally(() => {
        pendingRequests.delete(key);
    });

    pendingRequests.set(key, promise);
    return promise;
}

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options?.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new ApiError(response.status, error.message || error.detail || 'Request failed');
    }

    return response.json();
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
    entry_point: ApiNode | null;
    imports: ApiNode[];
    all_modules: ApiNode[];
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
        return dedupedFetch('entry-point', async () => {
            const response = await fetchJson<EntryPointResponse>(`${API_BASE}/graph/entry-point`);
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
        return dedupedFetch('root', async () => {
            const response = await fetchJson<RootNodesResponse>(`${API_BASE}/graph/root`);
            return response.nodes.map((n) => apiNodeToGraphNode(n));
        });
    },

    /**
     * Get a single node by ID
     */
    async getNode(nodeId: string): Promise<GraphNode> {
        return dedupedFetch(`node:${nodeId}`, async () => {
            const encodedId = encodeURIComponent(nodeId);
            const node = await fetchJson<ApiNode>(`${API_BASE}/graph/node/${encodedId}`);
            return apiNodeToGraphNode(node);
        });
    },

    /**
     * Get immediate children of a node
     */
    async getNodeChildren(nodeId: string, limit = 1000): Promise<GraphNode[]> {
        return dedupedFetch(`children:${nodeId}`, async () => {
            const encodedId = encodeURIComponent(nodeId);
            const response = await fetchJson<ChildrenResponse>(
                `${API_BASE}/graph/node/${encodedId}/children?limit=${limit}`,
            );
            return response.children.map((n) => apiNodeToGraphNode(n));
        });
    },

    /**
     * Get ancestors of a node (for breadcrumbs)
     */
    async getNodeAncestors(nodeId: string): Promise<GraphNode[]> {
        return dedupedFetch(`ancestors:${nodeId}`, async () => {
            const encodedId = encodeURIComponent(nodeId);
            const response = await fetchJson<AncestorsResponse>(
                `${API_BASE}/graph/node/${encodedId}/ancestors`,
            );
            return response.ancestors.map((n) => apiNodeToGraphNode(n));
        });
    },

    /**
     * Get all references to/from a node
     */
    async getNodeReferences(nodeId: string): Promise<ReferencesResponse> {
        return dedupedFetch(`references:${nodeId}`, async () => {
            return fetchJson<ReferencesResponse>(`${API_BASE}/graph/node/${nodeId}/references`);
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
        return dedupedFetch(`expand:${nodeId}`, async () => {
            const encodedId = encodeURIComponent(nodeId);
            const response = await fetchJson<{
                node: ApiNode | null;
                children: ApiNode[];
                outgoing: { id: string; name: string; type: string; edge_type: string }[];
            }>(`${API_BASE}/graph/expand/${encodedId}`);
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
        return fetchJson<SearchResponse>(`${API_BASE}/search?${params}`);
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
     *
    */
    async healthCheck(): Promise<{ status: string; version: string; neo4j: string }> {
        return fetchJson(`${API_BASE}/health`);
    },
};

export default api;
