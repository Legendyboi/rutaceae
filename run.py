from pathlib import Path
import subprocess
import typer
from lark.tree import pydot__tree_to_png
import rich
from core.pipeline.parser import Parser
from core.pipeline.ast import AstBuilder
from core.pipeline.codegen import CodeGenVisitor

import llvmlite.binding as llvm

app = typer.Typer()

@app.command(help="Compiles a Rutaceae program and creates an executable.")
def build(input_file: Path, output_file: Path = Path("output")):
    print("-----------------")
    print("Rutaceae Compiler")
    print("-----------------")
    print(f"Compiling {input_file} into executable {output_file}")

    parser = Parser()
    with input_file.open("rt") as f:
        tree = parser.parse_text(f.read())
    rich.print(tree)

    pydot__tree_to_png(tree, str(input_file.with_suffix(".png")), rankdir="TB")

    ast = AstBuilder().transform(tree)

    # Generate LLVM IR code
    codegen_visitor = CodeGenVisitor()
    llvm_ir = codegen_visitor.visit(ast)
    print(llvm_ir)

    # Initialize LLVM
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # Compile LLVM IR to object file
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    mod = llvm.parse_assembly(str(llvm_ir))
    mod.verify()

    with llvm.create_mcjit_compiler(mod, target_machine) as engine:
        engine.finalize_object()
        engine.run_static_constructors()

        obj_file = str(output_file.with_suffix(".o"))
        with open(obj_file, "wb") as f:
            f.write(target_machine.emit_object(mod))

    # Link the object file to create the executable
    executable = str(output_file)
    subprocess.run(["gcc", obj_file, "-o", executable], check=True)
    print(f"Executable {executable} created successfully.")

@app.command(help="Compiles and runs a Rutaceae program with a lot of debug info.")
def run(input_file: Path):
    print("-----------------")
    print("Rutaceae Compiler")
    print("-----------------")
    print(f"Compiling and running {input_file}")

    parser = Parser()
    with input_file.open("rt") as f:
        tree = parser.parse_text(f.read())
    rich.print(tree)

    pydot__tree_to_png(tree, str(input_file.with_suffix(".png")), rankdir="TB")

    ast = AstBuilder().transform(tree)

    # Generate LLVM IR code
    codegen_visitor = CodeGenVisitor()
    llvm_ir = codegen_visitor.visit(ast)
    print(llvm_ir)

    # Initialize LLVM
    llvm.initialize()
    llvm.initialize_native_target()
    llvm.initialize_native_asmprinter()

    # Compile LLVM IR to machine code
    target = llvm.Target.from_default_triple()
    target_machine = target.create_target_machine()
    mod = llvm.parse_assembly(str(llvm_ir))
    mod.verify()

    with llvm.create_mcjit_compiler(mod, target_machine) as engine:
        engine.finalize_object()
        engine.run_static_constructors()

        func_ptr = engine.get_function_address("main")

        from ctypes import CFUNCTYPE, c_int

        func_type = CFUNCTYPE(c_int)
        main_func = func_type(func_ptr)
        result = main_func()
        print(f"Program result: {result}")

def main():
    app()

if __name__ == "__main__":
    app()
