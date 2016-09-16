"""Contain a function to build pyqt files from ui and qrc files."""

# Directories
import os
REF = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(REF, "source")
TARGET_DIR = os.path.join(REF, "build")

# Cross platform errors
ERRORS = SystemError, OSError

# Build function
def build(verbose=False):
    """Build pyqt files from ui and qrc files."""
    nb_new_file = 0
    nb_updated_file = 0
    nb_utd_file = 0
    # Create build folder
    try: os.mkdir(TARGET_DIR)
    except ERRORS: pass
    # Loop over input files
    for input_file in os.listdir(INPUT_DIR):
        # Process ui files
        if os.path.splitext(input_file)[1] == ".ui":
            output_file = os.path.basename(input_file)
            output_file = os.path.splitext(output_file)[0] + '_ui.py'
            output_file = os.path.join(TARGET_DIR, output_file)
            input_file = os.path.join(INPUT_DIR, input_file)
            try:
                last_modif = os.path.getmtime(input_file)
                last_make = os.path.getmtime(output_file)
                if last_modif > last_make:
                    if verbose: print("updating " + os.path.basename(output_file))
                    os.system("pyuic4 -x " + input_file + " -o " + output_file)
                    nb_updated_file = nb_updated_file + 1
                else:
                    if verbose: print(os.path.basename(output_file) +" up to date.")
                    nb_utd_file = nb_utd_file + 1
            except ERRORS:
                if verbose: print ("creating " + os.path.basename(output_file))
                os.system("pyuic4 -x " + input_file + " -o " + output_file)
                nb_new_file = nb_new_file + 1
        # Process qrc files
        elif os.path.splitext(input_file)[1] == ".qrc":
            output_file = os.path.basename(input_file)
            output_file = os.path.splitext(output_file)[0] + '_rc.py'
            output_file = os.path.join(TARGET_DIR, output_file)
            input_file = os.path.join(INPUT_DIR, input_file)
            try:
                last_modif = os.path.getmtime(input_file)
                last_make = os.path.getmtime(output_file)
                if last_modif > last_make:
                    if verbose: print ("updating " + os.path.basename(output_file))
                    os.system("pyrcc4 " + input_file + " -o " + output_file)
                    nb_updated_file = nb_updated_file + 1
                else:
                    if verbose: print(os.path.basename(output_file) +" up to date.")
                    nb_utd_file = nb_utd_file + 1
            except ERRORS:
                if verbose: print ("creating " + os.path.basename(output_file))
                os.system("pyrcc4 " + input_file + " -o " + output_file)
                nb_new_file = nb_new_file + 1
    # Display report
    if verbose:
        print('\n-------------------------------------')
        print(str(nb_new_file) + ' file(s) created\n' + str(nb_updated_file) 
              + ' file(s) updated\n' + str(nb_utd_file) + ' already up-to-date')
        print('-------------------------------------\n')
    # Create __init__ file
    path = os.path.join(TARGET_DIR, "__init__.py")
    try: open(path, "a").close()
    except IOError: pass

# Main execution
if __name__ == "__main__":
    build(True)
