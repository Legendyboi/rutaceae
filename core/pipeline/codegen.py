import llvmlite.ir as ir
import llvmlite.binding as llvm

class CodeGenVisitor:
    def __init__(self):
        self.module = ir.Module(name="module")
        self.builder = None
        self.func = None
        self.variables = {}

    def visit(self, node):
        method_name = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f'No visit_{node.__class__.__name__} method')

    def visit_ProgramNode(self, node):
        for func_def in node.func_defs:
            self.visit(func_def)
        return self.module

    def visit_FuncDefNode(self, node):
        func_type = ir.FunctionType(ir.IntType(32), [])
        func = ir.Function(self.module, func_type, name=node.identifier)
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        self.func = func
        self.visit(node.body)
        return func

    def visit_BlockNode(self, node):
        for stmt in node.stmts:
            self.visit(stmt)

    def visit_ReturnStmtNode(self, node):
        ret_val = self.visit(node.expr)
        self.builder.ret(ret_val)

    def visit_LiteralExprNode(self, node):
        return ir.Constant(ir.IntType(32), node.value)

    def visit_IdentifierExprNode(self, node):
        var_ptr = self.variables.get(node.value)
        if var_ptr is None:
            raise Exception(f"Undefined variable: {node.value}")
        return self.builder.load(var_ptr, node.value)

    def visit_DeclarationStmtNode(self, node):
        var_type = ir.IntType(32) if node.type == "int" else ir.PointerType(ir.IntType(8))
        var_name = node.identifier

        if var_type == ir.IntType(32):
            var_ptr = self.builder.alloca(var_type, name=var_name)
            self.variables[var_name] = var_ptr
            if node.val is not None:
                var_val = self.visit(node.val)
                self.builder.store(var_val, var_ptr)
        elif var_type == ir.PointerType(ir.IntType(8)):
            var_ptr = self.builder.alloca(var_type, name=var_name)
            self.variables[var_name] = var_ptr
            if node.val is not None:
                var_val = self.builder.global_string_ptr(node.val.value, name=var_name)
                self.builder.store(var_val, var_ptr)

    def visit_ValueNode(self, node):
        if isinstance(node.value, int):
            return ir.Constant(ir.IntType(32), node.value)
        elif isinstance(node.value, str):
            return self.builder.global_string_ptr(node.value)

