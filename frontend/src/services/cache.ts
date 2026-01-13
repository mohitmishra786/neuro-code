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
        };
        indexes: { 'by-type': string };
    };
    children: {
        key: string; // parent node ID
        value: {
            children: GraphNode[];
            timestamp: number;
        };
    };
    metadata: {
        key: string;
        value: unknown;
    };
}

const DB_NAME = 'neurocode-cache';
const DB_VERSION = 1;
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

class CacheService {
    private db: IDBPDatabase<NeuroCacheDB> | null = null;
    private initPromise: Promise<void> | null = null;

    async init(): Promise<void> {
        if (this.db) return;
        if (this.initPromise) return this.initPromise;

        this.initPromise = this.openDatabase();
        return this.initPromise;
    }

    private async openDatabase(): Promise<void> {
        this.db = await openDB<NeuroCacheDB>(DB_NAME, DB_VERSION, {
            upgrade(db) {
                // Nodes store
                const nodesStore = db.createObjectStore('nodes', { keyPath: 'node.id' });
                nodesStore.createIndex('by-type', 'node.type');

                // Children store
                db.createObjectStore('children');

                // Metadata store
                db.createObjectStore('metadata');
            },
        });
    }

    private isExpired(timestamp: number): boolean {
        return Date.now() - timestamp > CACHE_TTL_MS;
    }

    // Node operations
    async getNode(nodeId: string): Promise<GraphNode | null> {
        await this.init();
        if (!this.db) return null;

        const entry = await this.db.get('nodes', nodeId);
        if (!entry || this.isExpired(entry.timestamp)) {
            return null;
        }
        return entry.node;
    }

    async setNode(node: GraphNode): Promise<void> {
        await this.init();
        if (!this.db) return;

        await this.db.put('nodes', {
            node,
            timestamp: Date.now(),
        });
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
        if (!entry || this.isExpired(entry.timestamp)) {
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
            .filter((e) => !this.isExpired(e.timestamp))
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
        const now = Date.now();

        // Clear expired nodes
        const nodesTx = this.db.transaction('nodes', 'readwrite');
        let nodesCursor = await nodesTx.store.openCursor();
        while (nodesCursor) {
            if (now - nodesCursor.value.timestamp > CACHE_TTL_MS) {
                await nodesCursor.delete();
                clearedCount++;
            }
            nodesCursor = await nodesCursor.continue();
        }
        await nodesTx.done;

        // Clear expired children
        const childrenTx = this.db.transaction('children', 'readwrite');
        let childrenCursor = await childrenTx.store.openCursor();
        while (childrenCursor) {
            if (now - childrenCursor.value.timestamp > CACHE_TTL_MS) {
                await childrenCursor.delete();
                clearedCount++;
            }
            childrenCursor = await childrenCursor.continue();
        }
        await childrenTx.done;

        return clearedCount;
    }

    async getStats(): Promise<{ nodeCount: number; childrenCount: number }> {
        await this.init();
        if (!this.db) return { nodeCount: 0, childrenCount: 0 };

        const [nodeCount, childrenCount] = await Promise.all([
            this.db.count('nodes'),
            this.db.count('children'),
        ]);

        return { nodeCount, childrenCount };
    }
}

export const cache = new CacheService();
export default cache;
