/**
 * In-graph legend for node and edge types.
 */

import { NODE_COLORS, NODE_TYPE_LABELS, EDGE_STYLES } from '@/constants/nodeColors';
import type { NodeType } from '@/types/graph.types';

const NODE_ORDER: NodeType[] = ['package', 'module', 'class', 'function', 'variable'];

export function GraphLegend() {
    return (
        <aside className="graph-legend" aria-label="Graph legend">
            <h3 className="graph-legend-title">Legend</h3>
            <div className="graph-legend-section">
                <span className="graph-legend-subtitle">Nodes</span>
                <ul className="graph-legend-list">
                    {NODE_ORDER.map((type) => (
                        <li key={type} className="graph-legend-item">
                            <span
                                className="graph-legend-swatch"
                                style={{ backgroundColor: NODE_COLORS[type] }}
                                aria-hidden
                            />
                            <span>{NODE_TYPE_LABELS[type]}</span>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="graph-legend-section">
                <span className="graph-legend-subtitle">Edges</span>
                <ul className="graph-legend-list">
                    {Object.entries(EDGE_STYLES).map(([key, style]) => (
                        <li key={key} className="graph-legend-item" title={style.description}>
                            <span
                                className="graph-legend-edge"
                                style={{
                                    borderColor: style.color,
                                    borderStyle: style.strokeDasharray ? 'dashed' : 'solid',
                                }}
                                aria-hidden
                            />
                            <span>{style.label}</span>
                        </li>
                    ))}
                </ul>
            </div>
            <p className="graph-legend-hint">Double-click a node with children to expand</p>
        </aside>
    );
}
