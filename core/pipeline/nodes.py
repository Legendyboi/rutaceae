import abc

class Node(abc.ABC):
    def __init__(self, line: int, column: int) -> None:
        self.line = line
        self.column = column

    def accept(self, visitor):
        return visitor.visit(self)

class ValueNode(Node):
    def __init__(self, line: int, column: int, value: str | int) -> None:
        super().__init__(line, column)
        self.value = value

class ExprNode(Node):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)

class LiteralExprNode(ExprNode):
    def __init__(self, line: int, column: int, value: int) -> None:
        super().__init__(line, column)
        self.value = value

class IdentifierExprNode(ExprNode):
    def __init__(self, line: int, column: int, value: str) -> None:
        super().__init__(line, column)
        self.value = value

class StmtNode(Node):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)

class PrintStmtNode(StmtNode):
    def __init__(self, line: int, column: int, identifier: str) -> None:
        super().__init__(line, column)
        self.identifier = identifier

class DeclarationStmtNode(StmtNode):
    VALID_TYPES = {"int", "string", "float", "void", "bool"}

    def __init__(self, line: int, column: int, type: str, identifier: str, val: ValueNode = None) -> None:
        super().__init__(line, column)
        if type not in self.VALID_TYPES:
            raise ValueError(f"Invalid type '{type}'. Must be one of: {', '.join(self.VALID_TYPES)}")
        self.type = type

        if not isinstance(identifier, str):
            raise TypeError(f"Expected identifier to be a str, got {identifier.__class__.__name__}")
        self.identifier = identifier

        if val is not None and not isinstance(val, ValueNode):
            raise TypeError(f"Expected value to be ValNode, got {val.__class__.__name__}")
        self.val = val

    def __str__(self):
        return f"DeclarationStmtNode(type={self.type}, identifier={self.identifier}, expr={self.expr})"

class ReturnStmtNode(StmtNode):
    def __init__(self, line: int, column: int, expr: ExprNode) -> None:
        super().__init__(line, column)
        assert isinstance(expr, ExprNode)
        self.expr = expr

class BlockNode(Node):
    def __init__(self, line: int, column: int, stmts: list[StmtNode]) -> None:
        super().__init__(line, column)
        assert all([isinstance(n, StmtNode) for n in stmts])
        self.stmts = stmts

class FuncDefNode(Node):
    VALID_TYPES = {"int", "string", "float", "void", "bool"}

    def __init__(self, line: int, column: int, identifier: str, body: BlockNode, type: str = "int") -> None:
        super().__init__(line, column)
        if type not in self.VALID_TYPES:
            raise ValueError(f"Invalid type '{type}'. Must be one of: {', '.join(self.VALID_TYPES)}")
        self.type = type

        if not isinstance(identifier, str):
            raise TypeError(f"Expected identifier to be a str, got {identifier.__class__.__name__}")
        self.identifier = identifier

        if not isinstance(body, BlockNode):
            raise TypeError(f"Expected body to be BlockNode, got {body.__class__.__name__}")
        self.body = body

    def __str__(self):
        return f"FuncDefNode(type={self.type}, identifier={self.identifier}, body={self.body})"

class ProgramNode(Node):
    def __init__(self, line: int, column: int, func_defs: list[FuncDefNode]) -> None:
        super().__init__(line, column)
        assert all([isinstance(n, FuncDefNode) for n in func_defs])
        self.func_defs = func_defs
