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
        # Grammar: "print" "(" expr ")" ";"
        # After transformation: items = [expr] (keywords filtered out)
        expr_node = items[0]  # Can be ValueNode, LiteralExprNode, or IdentifierExprNode

        return rtc.PrintStmtNode(
            expr_node.line,
            expr_node.column,
            expr_node,  # Pass the whole expression node
        )

    def return_stmt(self, items: list[Any]) -> rtc.ReturnStmtNode:
        # items[0] is already transformed to ExprNode (either LiteralExprNode or IdentifierExprNode)
        expr_node = items[0]
        return rtc.ReturnStmtNode(expr_node.line, expr_node.column, expr_node)

    def declaration_stmt(self, items: list[Any]) -> rtc.DeclarationStmtNode:
        """Transform declaration_stmt into DeclarationStmtNode."""
        # Grammar: "let" IDENTIFIER (":" type_specifier)? ("=" expr)? ";"
        # Possible patterns:
        #   [IdentifierExprNode]                          -> let x;
        #   [IdentifierExprNode, type_str]                -> let x: int;
        #   [IdentifierExprNode, expr]                    -> let x = 10;
        #   [IdentifierExprNode, type_str, expr]          -> let x: int = 10;

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

    def type_specifier(self, items: list[Any]) -> str:
        """Transform type_specifier tree into a string."""
        return items[0].value if items else "void"

    def block(self, items: list[Any]) -> rtc.BlockNode:
        """Transform block into BlockNode."""
        statements = items
        line = statements[0].line if statements else 0
        column = statements[0].column if statements else 0
        return rtc.BlockNode(line, column, statements)

    def func_def(self, items: list[Any]) -> rtc.FuncDefNode:
        """Transform func_def into FuncDefNode."""
        type_value = items[0]  # Already a string from type_specifier
        identifier_token = items[1]  # Token('IDENTIFIER', 'main')
        body = items[2]  # BlockNode from block transformer

        return rtc.FuncDefNode(
            identifier_token.line,
            identifier_token.column,
            identifier_token.value,
            body,
            type_value,
        )

    def program(self, items: list[Any]) -> rtc.ProgramNode:
        return rtc.ProgramNode(0, 0, items)
