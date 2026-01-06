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


class ParamNode(Node):
    """Represents a function parameter."""

    def __init__(self, line: int, column: int, type: str, name: str) -> None:
        super().__init__(line, column)
        self.type = type
        self.name = name


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


class CallExprNode(ExprNode):
    """Represents a function call expression."""

    def __init__(
        self, line: int, column: int, name: str, args: list[ExprNode]
    ) -> None:
        super().__init__(line, column)
        self.name = name
        self.args = args


class CastExprNode(ExprNode):
    """Represents a type casting expression."""

    def __init__(self, line: int, column: int, target_type: str, expr: ExprNode):
        super().__init__(line, column)
        self.target_type = target_type
        self.expr = expr


class StmtNode(Node):
    def __init__(self, line: int, column: int) -> None:
        super().__init__(line, column)


class PrintStmtNode(StmtNode):
    def __init__(self, line: int, column: int, expr: ExprNode | list[ExprNode]) -> None:
        super().__init__(line, column)

        if isinstance(expr, list):
            # Multiple expressions
            assert all([isinstance(e, ExprNode) for e in expr])
            self.expressions = expr
        else:
            # Single expression (backward compatibility)
            assert isinstance(expr, ExprNode)
            self.expressions = [expr]

        # Maintain backward compatibility: keep .expr for single expression
        self.expr = self.expressions[0]


class DeclarationStmtNode(StmtNode):
    def __init__(
        self,
        line: int,
        column: int,
        type: str,
        identifier: str,
        val: ExprNode | None,
        is_const: bool = False,
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

        if val is not None and not isinstance(val, ExprNode):
            raise TypeError(
                f"Expected val to be ExprNode or None, got {val.__class__.__name__}"
            )
        self.val = val

        # Add const tracking
        self.is_const = is_const

        # Const variables must have an initializer
        if is_const and val is None:
            raise ValueError(f"Const variable '{identifier}' must be initialized")


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


class IncrementStmtNode(StmtNode):
    def __init__(self, line: int, column: int, identifier: str) -> None:
        super().__init__(line, column)
        if not isinstance(identifier, str):
            raise TypeError(
                f"Expected identifier to be a str, got {identifier.__class__.__name__}"
            )
        self.identifier = identifier


class DecrementStmtNode(StmtNode):
    def __init__(self, line: int, column: int, identifier: str) -> None:
        super().__init__(line, column)
        if not isinstance(identifier, str):
            raise TypeError(
                f"Expected identifier to be a str, got {identifier.__class__.__name__}"
            )
        self.identifier = identifier


class CompoundAssignStmtNode(StmtNode):
    def __init__(
        self, line: int, column: int, identifier: str, operator: str, expr: ExprNode
    ) -> None:
        super().__init__(line, column)
        if not isinstance(identifier, str):
            raise TypeError(
                f"Expected identifier to be a str, got {identifier.__class__.__name__}"
            )

        valid_operators = {"+=", "-=", "*=", "/=", "%="}
        if operator not in valid_operators:
            raise ValueError(f"Invalid compound operator: {operator}")

        assert isinstance(expr, ExprNode)

        self.identifier = identifier
        self.operator = operator
        self.expr = expr


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
        params: list = None,
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

        # Store function parameters
        self.params = params if params is not None else []

    def __str__(self):
        return f"FuncDefNode(type={self.type}, identifier={self.identifier}, body={self.body})"


class ProgramNode(Node):
    def __init__(self, line: int, column: int, func_defs: list[FuncDefNode]) -> None:
        super().__init__(line, column)
        assert all([isinstance(n, FuncDefNode) for n in func_defs])
        self.func_defs = func_defs
