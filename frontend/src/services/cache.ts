/**
 * NeuroCode Cache Service
 *
 * IndexedDB-based caching for graph data.
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { GraphNode } from '@/types/graph.types';

interface NeuroCacheDB extends DBSchema {
    nodes: {
        key: string;
        value: {
            node: GraphNode;
            timestamp: number;
            version: number;
        };
        indexes: { 'by-type': string; 'by-timestamp': number };
    };
    children: {
        key: string; // parent node ID
        value: {
            children: GraphNode[];
            timestamp: number;
            version: number;
        };
    };
    metadata: {
        key: string;
        value: {
            data: unknown;
            timestamp: number;
            version: number;
        };
    };
}

export const DB_NAME = 'neurocode-cache';
export const DB_VERSION = 2; // Incremented for schema changes
export const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes
export const MAX_CACHE_SIZE = 10000; // Maximum number of nodes to cache
export const MAX_CHILDREN_CACHE_SIZE = 1000; // Maximum number of children entries
export const MAX_ACCESS_TRACKING = MAX_CACHE_SIZE + 1000;

class CacheService {
    private db: IDBPDatabase<NeuroCacheDB> | null = null;
    private initPromise: Promise<void> | null = null;

    // LRU tracking for eviction (public for tests)
    accessOrder: string[] = [];
    readonly MAX_ACCESS_TRACKING = MAX_ACCESS_TRACKING;

    async init(): Promise<void> {
        if (this.db) return;
        if (this.initPromise) return this.initPromise;

        this.initPromise = this.openDatabase();
        return this.initPromise;
    }

    private async openDatabase(): Promise<void> {
        this.db = await openDB<NeuroCacheDB>(DB_NAME, DB_VERSION, {
            upgrade(db, oldVersion, _newVersion, _transaction) {
                if (oldVersion < 2) {
                    // Recreate stores on schema bump
                    if (db.objectStoreNames.contains('nodes')) db.deleteObjectStore('nodes');
                    if (db.objectStoreNames.contains('children')) db.deleteObjectStore('children');
                    if (db.objectStoreNames.contains('metadata')) db.deleteObjectStore('metadata');
                }

                const nodesStore = db.createObjectStore('nodes', { keyPath: 'node.id' });
                nodesStore.createIndex('by-type', 'node.type');
                nodesStore.createIndex('by-timestamp', 'timestamp');

                db.createObjectStore('children');

                db.createObjectStore('metadata');
            },
        });
    }

    private isExpired(timestamp: number): boolean {
        return Date.now() - timestamp > CACHE_TTL_MS;
    }

    private CURRENT_VERSION = 1;

    private updateAccessOrder(nodeId: string): void {
        this.accessOrder = this.accessOrder.filter(id => id !== nodeId);
        this.accessOrder.unshift(nodeId);

        // Trim if too large
        if (this.accessOrder.length > this.MAX_ACCESS_TRACKING) {
            this.accessOrder = this.accessOrder.slice(0, this.MAX_ACCESS_TRACKING);
        }
    }

    async evictIfNeeded(): Promise<void> {
        if (!this.db) return;

        const stats = await this.getStatsInternal();
        if (stats.nodeCount <= MAX_CACHE_SIZE && stats.childrenCount <= MAX_CHILDREN_CACHE_SIZE) {
            return;
        }

        // Evict oldest expired entries first
        const now = Date.now();

        const nodesTx = this.db.transaction('nodes', 'readwrite');
        let nodesCursor = await nodesTx.store.openCursor();
        let evicted = 0;
        const targetNodeCount = Math.floor(MAX_CACHE_SIZE * 0.8);

        while (nodesCursor && stats.nodeCount - evicted > targetNodeCount) {
            const entry = nodesCursor.value;
            const isStale = this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION;
            const isOld = entry.timestamp < now - CACHE_TTL_MS;

            if (isStale || isOld) {
                await nodesCursor.delete();
                evicted++;
            }
            nodesCursor = await nodesCursor.continue();
        }
        await nodesTx.done;

        // Evict oldest children entries
        if (stats.childrenCount > MAX_CHILDREN_CACHE_SIZE) {
            const childrenTx = this.db.transaction('children', 'readwrite');
            let childrenCursor = await childrenTx.store.openCursor();
            evicted = 0;
            const targetChildrenCount = Math.floor(MAX_CHILDREN_CACHE_SIZE * 0.8);

            while (childrenCursor && stats.childrenCount - evicted > targetChildrenCount) {
                const entry = childrenCursor.value;
                const isStale = this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION;
                const isOld = entry.timestamp < now - CACHE_TTL_MS;

                if (isStale || isOld) {
                    await childrenCursor.delete();
                    evicted++;
                }
                childrenCursor = await childrenCursor.continue();
            }
            await childrenTx.done;
        }
    }

    private async getStatsInternal(): Promise<{ nodeCount: number; childrenCount: number }> {
        if (!this.db) return { nodeCount: 0, childrenCount: 0 };
        const [nodeCount, childrenCount] = await Promise.all([
            this.db.count('nodes'),
            this.db.count('children'),
        ]);
        return { nodeCount, childrenCount };
    }

    // Node operations
    async getNode(nodeId: string): Promise<GraphNode | null> {
        await this.init();
        if (!this.db) return null;

        const entry = await this.db.get('nodes', nodeId);
        if (!entry || this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION) {
            return null;
        }
        return entry.node;
    }

    async setNode(node: GraphNode): Promise<void> {
        await this.init();
        if (!this.db) return;

        // Check size before adding
        const stats = await this.getStatsInternal();
        if (stats.nodeCount >= MAX_CACHE_SIZE) {
            await this.evictIfNeeded();
        }

        // Check again after eviction attempt
        const updatedStats = await this.getStatsInternal();
        if (updatedStats.nodeCount >= MAX_CACHE_SIZE) {
            console.warn('[Cache] Cache full, evicting oldest accessed nodes');
            // Remove oldest entries
            const nodesTx = this.db.transaction('nodes', 'readwrite');
            let cursor = await nodesTx.store.openCursor();
            let removed = 0;
            const toRemove = 100; // Remove 100 oldest entries

            while (cursor && removed < toRemove) {
                await cursor.delete();
                removed++;
                cursor = await cursor.continue();
            }
            await nodesTx.done;
        }

        await this.db.put('nodes', {
            node,
            timestamp: Date.now(),
            version: this.CURRENT_VERSION,
        });

        this.updateAccessOrder(node.id);
    }

    async setNodes(nodes: GraphNode[]): Promise<void> {
        await this.init();
        if (!this.db) return;

        const tx = this.db.transaction('nodes', 'readwrite');
        await Promise.all([
            ...nodes.map((node) =>
                tx.store.put({
                    node,
                    timestamp: Date.now(),
                    version: this.CURRENT_VERSION,
                }),
            ),
            tx.done,
        ]);
    }

    // Children operations
    async getChildren(parentId: string): Promise<GraphNode[] | null> {
        await this.init();
        if (!this.db) return null;

        const entry = await this.db.get('children', parentId);
        if (!entry || this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION) {
            return null;
        }
        return entry.children;
    }

    async setChildren(parentId: string, children: GraphNode[]): Promise<void> {
        await this.init();
        if (!this.db) return;

        await this.db.put(
            'children',
            {
                children,
                timestamp: Date.now(),
                version: this.CURRENT_VERSION,
            },
            parentId,
        );
    }

    // Bulk operations
    async getNodesByType(type: string): Promise<GraphNode[]> {
        await this.init();
        if (!this.db) return [];

        const entries = await this.db.getAllFromIndex('nodes', 'by-type', type);
        return entries
            .filter((e) => !this.isExpired(e.timestamp) && e.version === this.CURRENT_VERSION)
            .map((e) => e.node);
    }

    // Cache management
    async clear(): Promise<void> {
        await this.init();
        if (!this.db) return;

        const tx = this.db.transaction(['nodes', 'children', 'metadata'], 'readwrite');
        await Promise.all([
            tx.objectStore('nodes').clear(),
            tx.objectStore('children').clear(),
            tx.objectStore('metadata').clear(),
            tx.done,
        ]);
    }

    async clearExpired(): Promise<number> {
        await this.init();
        if (!this.db) return 0;

        let clearedCount = 0;

        const nodesTx = this.db.transaction('nodes', 'readwrite');
        let nodesCursor = await nodesTx.store.openCursor();
        while (nodesCursor) {
            const entry = nodesCursor.value;
            if (this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION) {
                await nodesCursor.delete();
                clearedCount++;
            }
            nodesCursor = await nodesCursor.continue();
        }
        await nodesTx.done;

        const childrenTx = this.db.transaction('children', 'readwrite');
        let childrenCursor = await childrenTx.store.openCursor();
        while (childrenCursor) {
            const entry = childrenCursor.value;
            if (this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION) {
                await childrenCursor.delete();
                clearedCount++;
            }
            childrenCursor = await childrenCursor.continue();
        }
        await childrenTx.done;

        return clearedCount;
    }

    async getStats(): Promise<{ nodeCount: number; childrenCount: number; staleCount: number }> {
        await this.init();
        if (!this.db) return { nodeCount: 0, childrenCount: 0, staleCount: 0 };

        const [nodeCount, childrenCount] = await Promise.all([
            this.db.count('nodes'),
            this.db.count('children'),
        ]);

        let staleCount = 0;
        const nodesTx = this.db.transaction('nodes', 'readonly');
        let nodesCursor = await nodesTx.store.openCursor();
        while (nodesCursor) {
            const entry = nodesCursor.value;
            if (this.isExpired(entry.timestamp) || entry.version !== this.CURRENT_VERSION) {
                staleCount++;
            }
            nodesCursor = await nodesCursor.continue();
        }
        await nodesTx.done;

        return { nodeCount, childrenCount, staleCount };
    }
}

export const cache = new CacheService();
export default cache;
