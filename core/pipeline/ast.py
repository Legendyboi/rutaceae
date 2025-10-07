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
        # Grammar: "let" IDENTIFIER ("=" expr)? ";"
        # After transformation: items = [IdentifierExprNode, expr?]

        name_node = items[0]  # Already transformed to IdentifierExprNode
        name_token_value = name_node.value  # Extract the string value

        # Check if there's an initializer expression
        if len(items) > 1:
            value_expr = items[1]  # Already transformed ExprNode

            # Infer type from the value
            if isinstance(value_expr, rtc.LiteralExprNode):
                inferred_type = "int"
            else:
                inferred_type = "int"  # Default fallback
        else:
            value_expr = None
            inferred_type = "int"  # Default for uninitialized

        return rtc.DeclarationStmtNode(
            name_node.line,
            name_node.column,
            inferred_type,
            name_token_value,  # Use the string value, not the node
            value_expr,
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
