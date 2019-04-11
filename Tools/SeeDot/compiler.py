# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license.

from antlr4 import *
import argparse
import os

from antlr.seedotLexer import seedotLexer as SeeDotLexer
from antlr.seedotParser import seedotParser as SeeDotParser

import ast.ast as AST
import ast.astBuilder as ASTBuilder
from ast.printAST import PrintAST

from codegen.arduino import Arduino as ArduinoCodegen
from codegen.x86 import X86 as X86Codegen

from ir.irBuilder import IRBuilder
import ir.irUtil as IRUtil

from type import InferType
from util import *
from writer import Writer


class Compiler:

    def __init__(self, algo, target, inputFile, outputFile, profileLogFile, maxExpnt):
        if os.path.isfile(inputFile) == False:
            raise Exception("Input file doesn't exist")

        setAlgo(algo)
        setTarget(target)
        self.input = FileStream(inputFile)
        self.outputFile = outputFile
        setProfileLogFile(profileLogFile)
        setMaxExpnt(maxExpnt)

    def run(self):
        # Parse and generate CST for the input
        lexer = SeeDotLexer(self.input)
        tokens = CommonTokenStream(lexer)
        parser = SeeDotParser(tokens)
        tree = parser.expr()

        # Generate AST
        ast = ASTBuilder.ASTBuilder().visit(tree)

        # Pretty printing AST
        # PrintAST().visit(ast)

        # Perform type inference
        InferType().visit(ast)

        IRUtil.init()

        res, state = self.compile(ast)

        writer = Writer(self.outputFile)

        if forArduino():
            codegen = ArduinoCodegen(writer, *state)
        elif forX86():
            codegen = X86Codegen(writer, *state)
        else:
            assert False

        codegen.printAll(*res)

        writer.close()

    def compile(self, ast):
        return self.genCodeWithFuncCalls(ast)

    def genCodeWithFuncCalls(self, ast):

        compiler = IRBuilder()

        res = compiler.visit(ast)

        state = compiler.decls, compiler.scales, compiler.intvs, compiler.cnsts, compiler.expTables, compiler.globalVars

        return res, state
