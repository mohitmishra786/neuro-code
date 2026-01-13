/**
 * NeuroCode Breadcrumbs Component
 */

import { useGraphStore } from '@/stores/graphStore';
import { NODE_COLORS } from '@/utils/colorScheme';

export function Breadcrumbs() {
    const breadcrumbs = useGraphStore((state) => state.breadcrumbs);
    const focusNode = useGraphStore((state) => state.focusNode);
    const selectedNodeId = useGraphStore((state) => state.selectedNodeId);
    const nodes = useGraphStore((state) => state.nodes);

    const selectedNode = selectedNodeId ? nodes.get(selectedNodeId) : null;

    if (breadcrumbs.length === 0 && !selectedNode) {
        return null;
    }

    return (
        <nav className="breadcrumbs">
            <button className="breadcrumb-item breadcrumb-root" onClick={() => focusNode('')}>
                <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
                </svg>
            </button>

            {breadcrumbs.map((item, index) => (
                <div key={item.id} className="breadcrumb-segment">
                    <span className="breadcrumb-separator">/</span>
                    <button
                        className={`breadcrumb-item ${index === breadcrumbs.length - 1 ? 'breadcrumb-current' : ''}`}
                        onClick={() => focusNode(item.id)}
                    >
                        <span
                            className="breadcrumb-type"
                            style={{ backgroundColor: NODE_COLORS[item.type] }}
                        />
                        {item.name}
                    </button>
                </div>
            ))}

            {selectedNode && !breadcrumbs.find((b) => b.id === selectedNode.id) && (
                <div className="breadcrumb-segment">
                    <span className="breadcrumb-separator">/</span>
                    <span className="breadcrumb-item breadcrumb-current">
                        <span
                            className="breadcrumb-type"
                            style={{ backgroundColor: NODE_COLORS[selectedNode.type] }}
                        />
                        {selectedNode.name}
                    </span>
                </div>
            )}
        </nav>
    );
}

export default Breadcrumbs;
