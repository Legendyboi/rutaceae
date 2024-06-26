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

    def visit_PrintStmtNode(self, node):
        if isinstance(node.identifier, int):
            print("its int!")
            print(node.identifier)

            int_val = ir.Constant(ir.IntType(32), node.identifier)

            # Declare the printf function
            voidptr_ty = ir.IntType(8).as_pointer()
            printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
            printf = ir.Function(self.module, printf_ty, name="printf")

            # Create format string
            format_str = "%d\n\0"
            c_format_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_str)),
                                    bytearray(format_str.encode("utf8")))
            global_format_str = ir.GlobalVariable(self.module, c_format_str.type, name="fstr")
            global_format_str.linkage = 'internal'
            global_format_str.global_constant = True
            global_format_str.initializer = c_format_str

            # Cast the format string to i8*
            fmt_arg = self.builder.bitcast(global_format_str, voidptr_ty)
            self.builder.call(printf, [fmt_arg, int_val])

        elif '"' in node.identifier and isinstance(node.identifier, str):
            print("its str!")
            print(f"Heres the String Value Obtained: {node.identifier}")
            string_val = node.identifier.strip("\"")
            print(f"Heres the String Value after Strip: {string_val}")

            string_val += "\0"
            c_str_val = ir.Constant(ir.ArrayType(ir.IntType(8), len(string_val)),
                                    bytearray(string_val.encode("utf8")))
            print(f"c_str_val: {c_str_val}")

            # Declare the printf function
            voidptr_ty = ir.IntType(8).as_pointer()
            printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
            printf = ir.Function(self.module, printf_ty, name="printf")

            c_str = self.builder.alloca(c_str_val.type)
            self.builder.store(c_str_val, c_str)
            print(f"c_str: {c_str}")

            # Create format string
            format_str = "%s\n\0"
            c_format_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_str)),
                                    bytearray(format_str.encode("utf8")))
            print(f"c_format_str: {c_format_str}")
            global_format_str = ir.GlobalVariable(self.module, c_format_str.type, name="fstr")
            global_format_str.linkage = 'internal'
            global_format_str.global_constant = True
            global_format_str.initializer = c_format_str

            fmt_arg = self.builder.bitcast(global_format_str, voidptr_ty)
            print(fmt_arg)
            self.builder.call(printf, [fmt_arg, c_str])
            

        else:
            var_ptr = self.variables.get(node.identifier)
            print(f"identifier: {node.identifier}")
            print(f"heres the var_ptr: {var_ptr}")
            if var_ptr is None:
                raise Exception(f"Undefined variable: {node.identifier}")
            var_val = self.builder.load(var_ptr, node.identifier)
            print(f"heres the var_val: {var_val}")

            # Declare the printf function
            voidptr_ty = ir.IntType(8).as_pointer()
            printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
            printf = ir.Function(self.module, printf_ty, name="printf")

            # Create format string
            format_str = "%d\n\0"
            c_format_str = ir.Constant(ir.ArrayType(ir.IntType(8), len(format_str)),
                                    bytearray(format_str.encode("utf8")))
            global_format_str = ir.GlobalVariable(self.module, c_format_str.type, name="fstr")
            global_format_str.linkage = 'internal'
            global_format_str.global_constant = True
            global_format_str.initializer = c_format_str

            # Cast the format string to i8*
            fmt_arg = self.builder.bitcast(global_format_str, voidptr_ty)
            self.builder.call(printf, [fmt_arg, var_val])


