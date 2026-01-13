"""
NeuroCode Parser Package.

Tree-sitter based Python code parser for the visualization system.
Requires Python 3.11+.
"""

from parser.models import (
    NodeType,
    RelationshipType,
    AccessType,
    SourceLocation,
    VariableInfo,
    ParameterInfo,
    DecoratorInfo,
    ImportInfo,
    FunctionInfo,
    ClassInfo,
    ModuleInfo,
    Relationship,
)
from parser.tree_sitter_parser import TreeSitterParser
from parser.ast_analyzer import ASTAnalyzer
from parser.relationship_extractor import RelationshipExtractor

__all__ = [
    # Enums
    "NodeType",
    "RelationshipType",
    "AccessType",
    # Data classes
    "SourceLocation",
    "VariableInfo",
    "ParameterInfo",
    "DecoratorInfo",
    "ImportInfo",
    "FunctionInfo",
    "ClassInfo",
    "ModuleInfo",
    "Relationship",
    # Parser classes
    "TreeSitterParser",
    "ASTAnalyzer",
    "RelationshipExtractor",
]
