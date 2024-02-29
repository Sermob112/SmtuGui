import os

def list_files_in_current_directory():
    # Получаем текущую рабочую папку
    current_directory = os.getcwd()

    # Получаем список файлов и папок в текущей рабочей папке
    files_and_folders = os.listdir(current_directory)

    # Фильтруем только файлы и выводим их на экран
    files = [file for file in files_and_folders if os.path.isfile(os.path.join(current_directory, file))]
    for file in files:
        print(file)

if __name__ == "__main__":
    list_files_in_current_directory()