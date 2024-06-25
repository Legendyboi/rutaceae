from typing import Any
from lark import Token, Transformer
import core.pipeline.nodes as rtc

class AstBuilder(Transformer):
    def LITERAL(self, item: Token) -> rtc.LiteralExprNode:
        return rtc.LiteralExprNode(item.line, item.column, int(item.value))

    def expr(self, items: list[Any]) -> rtc.ExprNode:
        return items[0]

    def print_stmt(self, items: list[Any]) -> rtc.PrintStmtNode:
        identifier_token = items[2]
        return rtc.PrintStmtNode(identifier_token.line, identifier_token.column, identifier_token.value)

    def value(self, item: Token) -> rtc.ValueNode:
        print("ValAST called")
        if item.type == 'ESCAPED_STRING':
            value = item.value.strip('"')
            return rtc.ValueNode(item.line, item.column, value)
        elif item.type == 'INT':
            value = int(item.value)
            return rtc.ValueNode(item.line, item.column, value)
        elif item.type == 'IDENTIFIER':
            return rtc.IdentifierExprNode(item.line, item.column, item.value)
        else:
            raise TypeError(f"Unexpected token type: {item.type}")


    def return_stmt(self, items: list[Any]) -> rtc.ReturnStmtNode:
        print(items)
        expr = items[1]
        if isinstance(expr, Token):
            if expr.type == 'LITERAL':
                expr_node = self.LITERAL(expr)
            elif expr.type == 'IDENTIFIER':
                expr_node = rtc.IdentifierExprNode(expr.line, expr.column, expr.value)
            else:
                raise TypeError(f"Unexpected token type: {expr.type}")
        else:
            expr_node = expr

        return rtc.ReturnStmtNode(expr_node.line, expr_node.column, expr_node)


    def declaration_stmt(self, items: list[Any]) -> rtc.DeclarationStmtNode:
        print("declarationAST called")
        
        # Check if the first item is a type specifier
        if isinstance(items[0], Token) and items[0].type in {"type_specifier"}:
            type_token = items[1]
            name_token = items[2]
            value_token = items[4] if len(items) > 3 else None
        else:
            type_token = None
            name_token = items[1]
            value_token = items[3] if len(items) > 2 else None

        # Infer the type from the value if type_token is not provided
        if type_token is None and value_token is not None:
            if value_token.type == "ESCAPED_STRING":
                inferred_type = "string"
            elif value_token.type == "INT":
                inferred_type = "int"
            else:
                raise TypeError(f"Unexpected token type: {value_token.type}")
        else:
            inferred_type = type_token.value if type_token else "int"  # Default to int if no type and no value

        # Transform the value token to ValueNode
        val = self.value(value_token) if value_token else None

        return rtc.DeclarationStmtNode(
            name_token.line, name_token.column, inferred_type, name_token.value, val
        )

    def block(self, items: list[Any]) -> rtc.BlockNode:
        statements = items[1:-1]
        return rtc.BlockNode(items[0].line, items[0].column, statements)

    def func_def(self, items: list[Any]) -> rtc.FuncDefNode:
        type_token = items[0]
        identifier_token = items[1]
        body = items[2]

        funcDefNode = rtc.FuncDefNode(
            identifier_token.line, identifier_token.column, identifier_token.value, body, type_token.value
        )
        
        return funcDefNode

    def program(self, items: list[Any]) -> rtc.ProgramNode:
        return rtc.ProgramNode(0, 0, items)
