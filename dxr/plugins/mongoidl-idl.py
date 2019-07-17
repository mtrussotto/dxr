#!/usr/bin/python
import sys
import os
import errno
import importlib
import re

__compile_idl = None
__parse_idl = None
__temp_folder = None
__source_folder = None

def __makedirs(path):
    try:
        os.makedirs(path)
    except IOError as e:
        if e.errno != errno.EEXIST:
            raise

def __metapath(path):
    path = os.path.realpath(path)
    print(path);
    print(__source_folder);
    if path.startswith(__source_folder):
        path = path[len(__source_folder):]
    if path[0] == os.path.sep:
        return os.path.join(__temp_folder, path[1:])
    return os.path.join(__temp_folder, path)
    
def compile_idl_intercept(args):
    global __compile_idl
    global __temp_folder
    input_meta = __metapath(args.input_file)
    source_meta = __metapath(args.output_source)
    header_meta = __metapath(args.output_header)
    __makedirs(os.path.dirname(input_meta));
    __makedirs(os.path.dirname(source_meta));
    __makedirs(os.path.dirname(header_meta));
    with open(input_meta, "a") as f:
        f.write("SOURCEGEN:" + args.output_source + "\n");
        f.write("HEADERGEN:" + args.output_header + "\n");
    with open(source_meta, "a") as f:
        f.write("IDLSOURCE:"  + args.input_file + "\n");
    with open(header_meta, "a") as f:
        f.write("IDLSOURCE:"  + args.input_file + "\n");

#    sys.stderr.write("Output source " + args.output_source +"\n")
#    sys.stderr.write("Output header " + args.output_header +"\n")
#    sys.stderr.write("Input file " + args.input_file +"\n")
    return __compile_idl(args)

def __p(obj, name):
    return str([x.__dict__ for x in obj if x.file_name == name])

def parse_idl_intercept(stream, input_file_name, resolver):
    global __parse_idl
#    sys.stderr.write("parsing file = " + input_file_name + "\n");
    parsed_doc = __parse_idl(stream, input_file_name, resolver)
    idl_doc = parsed_doc.spec
    sym_tab = idl_doc.symbols
    for t in sym_tab.types:
        # file_name, name, line, column
        # TODO -- cache the metadata file handles
        metaname = __metapath(t.file_name)
        __makedirs(os.path.dirname(metaname))
        with open(metaname, "a") as f:
            f.write(":".join(["TYPE", t.name, str(t.line), str(t.column)]) + "\n")
        
#    sys.stderr.write("parser output globals= " + str(idl_doc.globals)+ "\n");
#    sys.stderr.write("parser output imports= " + str(idl_doc.imports)+ "\n");
#    sys.stderr.write("parser output parms= " + __p(idl_doc.server_parameters, input_file_name) + "\n")
#    sys.stderr.write("parser output configs= " + str(idl_doc.configs)+ "\n");
#    sys.stderr.write("parser output commands= " + str(sym_tab.commands)+ "\n");
#    sys.stderr.write("parser output enums= " + str(sym_tab.enums)+ "\n");
#    sys.stderr.write("parser output structs= " + str(sym_tab.structs)+ "\n");
#    sys.stderr.write("parser output types= " + __p(sym_tab.types, input_file_name)+ "\n")
    return parsed_doc

def main():
    major_version = sys.version_info[0]
    global __temp_folder
    global __source_folder
    assert sys.argv[1] == "--temp_folder", sys.argv
    __temp_folder = sys.argv[2]
    assert sys.argv[3] == "--source_folder", sys.argv
    __source_folder = os.path.realpath(sys.argv[4])
#    sys.stderr.write("temp_folder = "  + __temp_folder);
    modpath = sys.argv[5];
    if major_version == 2:
        first_line = None
        with open(modpath, "r") as f:
            first_line = f.readline();
        if re.match("#!.*python3", first_line):
#            sys.stderr.write("Restarting with python3\n");
            sys.argv.insert(0, "python3")
            os.execvp("python3", sys.argv)
                
                
    module = os.path.splitext(modpath)[0]
#    sys.stderr.write(module+"\n");
    sys.path.append(os.path.dirname(module))
    idlc = importlib.import_module("idlc")
    global __compile_idl
    global __parse_idl
    __compile_idl = idlc.idl.compiler.compile_idl
    __parse_idl = idlc.idl.parser.parse
    idlc.idl.compiler.compile_idl = compile_idl_intercept
    idlc.idl.parser.parse = parse_idl_intercept
    sys.argv = sys.argv[5:]
    idlc.main()

if __name__ == '__main__':
    main()
