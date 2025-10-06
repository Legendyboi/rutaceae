from typing import Any
from lark import Token, Transformer
import core.pipeline.nodes as rtc


class AstBuilder(Transformer):
    def LITERAL(self, item: Token) -> rtc.LiteralExprNode:
        return rtc.LiteralExprNode(item.line, item.column, int(item.value))

    def IDENTIFIER(self, item: Token) -> rtc.IdentifierExprNode:
        """Transform IDENTIFIER tokens into IdentifierExprNode."""
        return rtc.IdentifierExprNode(item.line, item.column, item.value)

    def expr(self, items: list[Any]) -> rtc.ExprNode:
        return items[0]

    def ESCAPED_STRING(self, item: Token) -> rtc.ValueNode:
        """Transform ESCAPED_STRING tokens into ValueNode with the string value."""
        # Strip the surrounding quotes
        string_value = item.value.strip('"')
        return rtc.ValueNode(item.line, item.column, string_value)

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
