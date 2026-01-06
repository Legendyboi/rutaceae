from typing import Any
from lark import Token, Transformer
import core.pipeline.nodes as rtc
import ast


class AstBuilder(Transformer):
    def LITERAL(self, item: Token) -> rtc.LiteralExprNode:
        return rtc.LiteralExprNode(item.line, item.column, int(item.value))

    def IDENTIFIER(self, item: Token) -> rtc.IdentifierExprNode:
        """Transform IDENTIFIER tokens into IdentifierExprNode."""
        return rtc.IdentifierExprNode(item.line, item.column, item.value)

    def expr(self, items: list[Any]) -> rtc.ExprNode:
        return items[0]

    def FLOAT_LITERAL(self, item: Token) -> rtc.ValueNode:
        """Transform FLOAT_LITERAL token into ValueNode with float value."""
        return rtc.ValueNode(item.line, item.column, float(item.value))

    # Binary operators - arithmetic
    def add(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform addition: term + factor"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "+", left, right)

    def sub(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform subtraction: term - factor"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "-", left, right)

    def mul(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform multiplication: factor * unary"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "*", left, right)

    def div(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform division: factor / unary"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "/", left, right)

    def mod(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform modulo: factor % unary"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "%", left, right)

    # Binary operators - comparison
    def eq(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform equality: expr == term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "==", left, right)

    def neq(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform not equal: expr != term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "!=", left, right)

    def lt(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform less than: expr < term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "<", left, right)

    def le(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform less than or equal: expr <= term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "<=", left, right)

    def gt(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform greater than: expr > term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, ">", left, right)

    def ge(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform greater than or equal: expr >= term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, ">=", left, right)

    # Binary operators - logical
    def and_(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform logical and: expr && term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "&&", left, right)

    def or_(self, items: list[Any]) -> rtc.BinaryOpNode:
        """Transform logical or: expr || term"""
        left, right = items
        return rtc.BinaryOpNode(left.line, left.column, "||", left, right)

    # Unary operators
    def neg(self, items: list[Any]) -> rtc.UnaryOpNode:
        """Transform negation: -unary"""
        operand = items[0]
        return rtc.UnaryOpNode(operand.line, operand.column, "-", operand)

    def not_(self, items: list[Any]) -> rtc.UnaryOpNode:
        """Transform logical not: !unary"""
        operand = items[0]
        return rtc.UnaryOpNode(operand.line, operand.column, "!", operand)

    def ESCAPED_STRING(self, item: Token) -> rtc.ValueNode:
        """Transform ESCAPED_STRING tokens into ValueNode with proper escape sequences."""

        # Use ast.literal_eval to properly decode escape sequences like \n, \t, \", etc.
        string_value = ast.literal_eval(item.value)
        return rtc.ValueNode(item.line, item.column, string_value)

    def TRUE(self, item: Token) -> rtc.ValueNode:
        """Transform TRUE token into ValueNode with boolean value."""
        return rtc.ValueNode(item.line, item.column, True)

    def FALSE(self, item: Token) -> rtc.ValueNode:
        """Transform FALSE token into ValueNode with boolean value."""
        return rtc.ValueNode(item.line, item.column, False)

    def print_stmt(self, items: list[Any]) -> rtc.PrintStmtNode:
        """Transform print_stmt into PrintStmtNode."""
        # Grammar: "print" "(" expr ("," expr)* ")" ";"
        # items = [expr1, expr2, expr3, ...] (list of expressions)

        if len(items) == 1:
            # Single expression - use existing node structure
            return rtc.PrintStmtNode(items[0].line, items[0].column, items[0])
        else:
            # Multiple expressions
            return rtc.PrintStmtNode(items[0].line, items[0].column, items)

    def return_stmt(self, items: list[Any]) -> rtc.ReturnStmtNode:
        # items[0] is already transformed to ExprNode (either LiteralExprNode or IdentifierExprNode)
        expr_node = items[0]
        return rtc.ReturnStmtNode(expr_node.line, expr_node.column, expr_node)

    def let_stmt(self, items: list[Any]) -> rtc.DeclarationStmtNode:
        """Transform let_stmt into DeclarationStmtNode."""
        # Grammar: "let" IDENTIFIER (":" type_specifier)? ("=" expr)? ";"
        # This is your existing logic, just copied over

        name_node = items[0]  # IdentifierExprNode
        name_token_value = name_node.value

        type_spec = None
        value_expr = None

        # Parse based on number of items
        if len(items) == 1:
            # let x;
            type_spec = "int"  # Default type
        elif len(items) == 2:
            # Either "let x: int;" or "let x = 10;"
            if isinstance(items[1], str):
                # Type annotation: let x: int;
                type_spec = items[1]
            else:
                # Expression: let x = 10;
                value_expr = items[1]
                # Infer type from expression
                if isinstance(value_expr, rtc.ValueNode):
                    if isinstance(value_expr.value, bool):
                        type_spec = "bool"
                    elif isinstance(value_expr.value, float):
                        type_spec = "float"
                    elif isinstance(value_expr.value, str):
                        type_spec = "string"
                    else:
                        type_spec = "int"
                else:
                    type_spec = "int"  # Default
        elif len(items) == 3:
            # let x: int = 10;
            type_spec = items[1]  # Type string
            value_expr = items[2]  # Expression

        return rtc.DeclarationStmtNode(
            name_node.line,
            name_node.column,
            type_spec,
            name_token_value,
            value_expr,
            is_const=False,  # let variables are mutable
        )

    def const_stmt(self, items: list[Any]) -> rtc.DeclarationStmtNode:
        """Transform const_stmt into DeclarationStmtNode."""
        # Grammar: "const" IDENTIFIER (":" type_specifier)? "=" expr ";"
        # Const must always have an initializer

        name_node = items[0]  # IdentifierExprNode
        name_token_value = name_node.value

        if len(items) == 2:
            # const x = 10;
            value_expr = items[1]
            # Infer type from expression
            if isinstance(value_expr, rtc.ValueNode):
                if isinstance(value_expr.value, bool):
                    type_spec = "bool"
                elif isinstance(value_expr.value, float):
                    type_spec = "float"
                elif isinstance(value_expr.value, str):
                    type_spec = "string"
                else:
                    type_spec = "int"
            else:
                type_spec = "int"  # Default
        elif len(items) == 3:
            # const x: int = 10;
            type_spec = items[1]  # Type string
            value_expr = items[2]  # Expression
        else:
            raise ValueError("Const declaration must have an initializer")

        return rtc.DeclarationStmtNode(
            name_node.line,
            name_node.column,
            type_spec,
            name_token_value,
            value_expr,
            is_const=True,  # const variables are immutable
        )

    def assignment_stmt(self, items: list[Any]) -> rtc.AssignmentStmtNode:
        """Transform assignment_stmt into AssignmentStmtNode."""
        # Grammar: IDENTIFIER "=" expr ";"
        # After transformation: items = [identifier_token, expr_node]
        identifier_token = items[0]
        expr_node = items[1]

        return rtc.AssignmentStmtNode(
            identifier_token.line,
            identifier_token.column,
            identifier_token.value,
            expr_node,
        )

    def if_stmt(self, items: list[Any]) -> rtc.IfStmtNode:
        """Transform if statement into IfStmtNode."""
        # Grammar: "if" "(" expr ")" block ("else" block)?
        # items = [condition_expr, then_block] or [condition_expr, then_block, else_block]

        condition = items[0]  # ExprNode
        then_block = items[1]  # BlockNode
        else_block = items[2] if len(items) > 2 else None  # Optional BlockNode

        return rtc.IfStmtNode(
            condition.line,
            condition.column,
            condition,
            then_block,
            else_block,
        )

    def while_stmt(self, items: list[Any]) -> rtc.WhileStmtNode:
        """Transform while statement into WhileStmtNode."""
        # Grammar: "while" "(" expr ")" block
        # items = [condition_expr, body_block]

        condition = items[0]  # ExprNode
        body = items[1]  # BlockNode

        return rtc.WhileStmtNode(
            condition.line,
            condition.column,
            condition,
            body,
        )

    def for_update(self, items: list[Any]) -> rtc.AssignmentStmtNode:
        """Transform for_update into AssignmentStmtNode (without semicolon)."""
        identifier_token = items[0]
        expr_node = items[1]

        return rtc.AssignmentStmtNode(
            identifier_token.line,
            identifier_token.column,
            identifier_token.value,
            expr_node,
        )

    def for_init(self, items: list[Any]) -> rtc.StmtNode | None:
        """Transform for_init into a statement or None for empty init."""
        if len(items) == 0:
            # Empty initialization - just semicolon
            return None
        else:
            # Return the statement (declaration or assignment)
            return items[0]

    def for_stmt(self, items: list[Any]) -> rtc.ForStmtNode:
        """Transform for statement into ForStmtNode."""
        # Grammar: "for" "(" for_init expr ";" assignment_stmt ")" block
        # items = [init_stmt_or_none, condition_expr, update_stmt, body_block]

        init_stmt = items[0]  # Can be None from for_init
        condition = items[1]  # ExprNode
        update = items[2]  # StmtNode (assignment)
        body = items[3]  # BlockNode

        return rtc.ForStmtNode(
            condition.line,
            condition.column,
            init_stmt,
            condition,
            update,
            body,
        )

    def increment_stmt(self, items: list[Any]) -> rtc.IncrementStmtNode:
        """Transform increment statement into IncrementStmtNode."""
        # Grammar: IDENTIFIER "++" ";"
        identifier_token = items[0]
        return rtc.IncrementStmtNode(
            identifier_token.line, identifier_token.column, identifier_token.value
        )

    def decrement_stmt(self, items: list[Any]) -> rtc.DecrementStmtNode:
        """Transform decrement statement into DecrementStmtNode."""
        # Grammar: IDENTIFIER "--" ";"
        identifier_token = items[0]
        return rtc.DecrementStmtNode(
            identifier_token.line, identifier_token.column, identifier_token.value
        )

    def compound_assign_stmt(self, items: list[Any]) -> rtc.CompoundAssignStmtNode:
        """Transform compound assignment statement."""
        # Grammar: IDENTIFIER (PLUS_ASSIGN | MINUS_ASSIGN | MULT_ASSIGN | DIV_ASSIGN | MOD_ASSIGN) expr ";"
        # items = [identifier_token, operator_token, expr_node]

        identifier_token = items[0]  # IDENTIFIER token
        operator_token = items[1]  # One of the ASSIGN tokens
        expr_node = items[2]  # Expression

        return rtc.CompoundAssignStmtNode(
            identifier_token.line,
            identifier_token.column,
            identifier_token.value,
            operator_token.value,  # This will be "+=", "-=", etc.
            expr_node,
        )

    def break_stmt(self, items: list[Any]) -> rtc.BreakStmtNode:
        """Transform break statement into BreakStmtNode."""
        # Grammar: "break" ";"

        return rtc.BreakStmtNode(0, 0)

    def continue_stmt(self, items: list[Any]) -> rtc.ContinueStmtNode:
        """Transform continue statement into ContinueStmtNode."""
        # Grammar: "continue" ";"

        return rtc.ContinueStmtNode(0, 0)

    def type_specifier(self, items: list[Any]) -> str:
        """Transform type_specifier tree into a string."""
        if not items:
            return "void"
        # The item is an anonymous Token with the type name as its value
        token = items[0]
        if hasattr(token, 'value'):
            return str(token.value)
        return str(token)

    def param(self, items: list[Any]) -> rtc.ParamNode:
        """Transform param into ParamNode."""
        # Grammar: type_specifier IDENTIFIER
        type_spec = items[0]  # Already a string from type_specifier
        name_node = items[1]  # IdentifierExprNode
        return rtc.ParamNode(name_node.line, name_node.column, type_spec, name_node.value)

    def func_call(self, items: list[Any]) -> rtc.CallExprNode:
        """Transform func_call into CallExprNode."""
        # Grammar: IDENTIFIER "(" (expr ("," expr)*)? ")"
        name_node = items[0]  # IdentifierExprNode
        args = items[1:] if len(items) > 1 else []
        return rtc.CallExprNode(name_node.line, name_node.column, name_node.value, args)

    def block(self, items: list[Any]) -> rtc.BlockNode:
        """Transform block into BlockNode."""
        statements = items
        line = statements[0].line if statements else 0
        column = statements[0].column if statements else 0
        return rtc.BlockNode(line, column, statements)

    def func_def(self, items: list[Any]) -> rtc.FuncDefNode:
        """Transform func_def into FuncDefNode."""
        # Grammar: "fn" type_specifier IDENTIFIER "(" (param ("," param)*)? ")" block
        type_value = items[0]  # Already a string from type_specifier
        identifier_token = items[1]  # IdentifierExprNode

        # Items between identifier and body are parameters
        # Body (BlockNode) is always last
        body = items[-1]
        params = [item for item in items[2:-1] if isinstance(item, rtc.ParamNode)]

        return rtc.FuncDefNode(
            identifier_token.line,
            identifier_token.column,
            identifier_token.value,
            body,
            type_value,
            params=params,
        )

    def program(self, items: list[Any]) -> rtc.ProgramNode:
        return rtc.ProgramNode(0, 0, items)
