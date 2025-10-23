import abc


class Node(abc.ABC):
    def __init__(self, line: int, column: int) -> None:
        self.line = line
        self.column = column

    def accept(self, visitor):
        return visitor.visit(self)


class ExprNode(Node):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)


class ValueNode(ExprNode):
    def __init__(self, line: int, column: int, value: str | int) -> None:
        super().__init__(line, column)
        self.value = value


class LiteralExprNode(ExprNode):
    def __init__(self, line: int, column: int, value: int) -> None:
        super().__init__(line, column)
        self.value = value


class IdentifierExprNode(ExprNode):
    def __init__(self, line: int, column: int, value: str) -> None:
        super().__init__(line, column)
        self.value = value


class BinaryOpNode(ExprNode):
    def __init__(
        self, line: int, column: int, op: str, left: ExprNode, right: ExprNode
    ) -> None:
        super().__init__(line, column)
        self.op = (
            op  # '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||'
        )
        assert isinstance(left, ExprNode)
        assert isinstance(right, ExprNode)
        self.left = left
        self.right = right


class UnaryOpNode(ExprNode):
    def __init__(self, line: int, column: int, op: str, operand: ExprNode) -> None:
        super().__init__(line, column)
        self.op = op  # '-', '!'
        assert isinstance(operand, ExprNode)
        self.operand = operand


class StmtNode(Node):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)


class PrintStmtNode(StmtNode):
    def __init__(self, line: int, column: int, expr: ExprNode) -> None:
        super().__init__(line, column)
        assert isinstance(expr, ExprNode)
        self.expr = expr


class DeclarationStmtNode(StmtNode):
    def __init__(
        self, line: int, column: int, type: str, identifier: str, val: ExprNode | None
    ) -> None:
        super().__init__(line, column)

        VALID_TYPES = {"int", "string", "float", "void", "bool"}
        if type not in VALID_TYPES:
            raise TypeError(f"Expected type to be one of {VALID_TYPES}, got {type}")
        self.type = type

        if not isinstance(identifier, str):
            raise TypeError(
                f"Expected identifier to be a str, got {identifier.__class__.__name__}"
            )
        self.identifier = identifier

        if val is not None and not isinstance(val, ExprNode):  # Changed from ValueNode
            raise TypeError(
                f"Expected val to be ExprNode or None, got {val.__class__.__name__}"
            )
        self.val = val


class AssignmentStmtNode(StmtNode):
    def __init__(self, line: int, column: int, identifier: str, expr: ExprNode) -> None:
        super().__init__(line, column)
        self.identifier = identifier
        assert isinstance(expr, ExprNode)
        self.expr = expr


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


class IfStmtNode(StmtNode):
    def __init__(
        self,
        line: int,
        column: int,
        condition: ExprNode,
        then_block: BlockNode,
        else_block: BlockNode | None = None,
    ) -> None:
        super().__init__(line, column)
        assert isinstance(condition, ExprNode)
        assert isinstance(then_block, BlockNode)
        if else_block is not None:
            assert isinstance(else_block, BlockNode)

        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block


class WhileStmtNode(StmtNode):
    def __init__(
        self,
        line: int,
        column: int,
        condition: ExprNode,
        body: BlockNode,
    ) -> None:
        super().__init__(line, column)
        assert isinstance(condition, ExprNode)
        assert isinstance(body, BlockNode)

        self.condition = condition
        self.body = body


class ForStmtNode(StmtNode):
    def __init__(
        self,
        line: int,
        column: int,
        init: StmtNode | None,  # Initialization (let i = 0; or i = 0;)
        condition: ExprNode,  # Loop condition (i < 10)
        update: StmtNode,  # Update statement (i = i + 1)
        body: BlockNode,  # Loop body
    ) -> None:
        super().__init__(line, column)
        if init is not None:
            assert isinstance(init, StmtNode)
        assert isinstance(condition, ExprNode)
        assert isinstance(update, StmtNode)
        assert isinstance(body, BlockNode)

        self.init = init
        self.condition = condition
        self.update = update
        self.body = body


class BreakStmtNode(StmtNode):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)


class ContinueStmtNode(StmtNode):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)


class FuncDefNode(Node):
    VALID_TYPES = {"int", "string", "float", "void", "bool"}

    def __init__(
        self,
        line: int,
        column: int,
        identifier: str,
        body: BlockNode,
        type: str = "int",
    ) -> None:
        super().__init__(line, column)
        if type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid type '{type}'. Must be one of: {', '.join(self.VALID_TYPES)}"
            )
        self.type = type

        if not isinstance(identifier, str):
            raise TypeError(
                f"Expected identifier to be a str, got {identifier.__class__.__name__}"
            )
        self.identifier = identifier

        if not isinstance(body, BlockNode):
            raise TypeError(
                f"Expected body to be BlockNode, got {body.__class__.__name__}"
            )
        self.body = body

    def __str__(self):
        return f"FuncDefNode(type={self.type}, identifier={self.identifier}, body={self.body})"


class ProgramNode(Node):
    def __init__(self, line: int, column: int, func_defs: list[FuncDefNode]) -> None:
        super().__init__(line, column)
        assert all([isinstance(n, FuncDefNode) for n in func_defs])
        self.func_defs = func_defs
