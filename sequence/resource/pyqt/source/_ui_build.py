import os


# Changer le repertoire courant
os.chdir(os.path.dirname(__file__))

INPUT_DIR = "."
TARGET_DIR = os.path.join(os.pardir, "build")

NEW_FILE = 0
UPDATED_FILE = 0
UTD_FILE = 0

for input_file in os.listdir(INPUT_DIR):
    if os.path.splitext(input_file)[1] == ".ui":
        output_file = os.path.basename(input_file)
        output_file = os.path.splitext(output_file)[0] + '_ui.py'
        output_file = os.path.join(TARGET_DIR, output_file)
        input_file = os.path.join(INPUT_DIR, input_file)
        try:
            last_modif = os.path.getmtime(input_file)
            last_make = os.path.getmtime(output_file)
            if last_modif > last_make:
                print ("updating " + os.path.basename(output_file))
                os.system("pyuic4 -x " + input_file + " -o " + output_file)
                UPDATED_FILE = UPDATED_FILE + 1
            else:
                print(os.path.basename(output_file) +" up to date.")
                UTD_FILE = UTD_FILE + 1
        except WindowsError:
            print ("creating " + os.path.basename(output_file))
            os.system("pyuic4 -x " + input_file + " -o " + output_file)
            NEW_FILE = NEW_FILE + 1
    elif os.path.splitext(input_file)[1] == ".qrc":
        output_file = os.path.basename(input_file)
        output_file = os.path.splitext(output_file)[0] + '_rc.py'
        output_file = os.path.join(TARGET_DIR, output_file)
        input_file = os.path.join(INPUT_DIR, input_file)
        try:
            last_modif = os.path.getmtime(input_file)
            last_make = os.path.getmtime(output_file)
            if last_modif > last_make:
                print ("updating " + os.path.basename(output_file))
                os.system("pyrcc4 " + input_file + " -o " + output_file)
                UPDATED_FILE = UPDATED_FILE + 1
            else:
                print(os.path.basename(output_file) +" up to date.")
                UTD_FILE = UTD_FILE + 1
        except SystemError:
            print ("creating " + os.path.basename(output_file))
            os.system("pyrcc4 " + input_file + " -o " + output_file)
            NEW_FILE = NEW_FILE + 1
        

print('\n-------------------------------------')
print(str(NEW_FILE) + ' file(s) created\n' + str(UPDATED_FILE) 
    + ' file(s) updated\n' + str(UTD_FILE) + ' already up-to-date')
print('-------------------------------------\n')

# raw_input("Press return to exit...")
