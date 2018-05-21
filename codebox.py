import sublime
import sublime_plugin
import os
import time
import fnmatch


def settings():
    return sublime.load_settings('codebox.sublime-settings')


def get_root():
    project_settings = sublime.active_window().active_view().settings().get('CodeBox')
    if project_settings:
        return os.path.normpath(os.path.expanduser(project_settings.get('root', settings().get("root"))))
    else:
        return os.path.normpath(os.path.expanduser(settings().get("root")))


def return_sublist(main_list, indices):
    sublist = [[item[i] for i in indices] for item in main_list]
    return sublist


def setup_snippets_list(file_list):
    # list display options
    indices = [0]
    return return_sublist(file_list, indices)


def find_snippets(self, root, mode="all", exclude=[]):
    exclude_files = settings().get("exclude_files")
    snippet_files = []
    for path, subdirs, files in os.walk(root, topdown=True):
        if exclude:
            subdirs[:] = [d for d in subdirs if d not in exclude]
        relpath = os.path.relpath(path, root)
        if mode == "all":
            for name in files:
                title = os.path.join(relpath, name).replace(".\\", "").replace("\\", "/")
                if title in exclude_files:
                    continue
                modified_str = time.strftime(
                    "Last modified: %d/%m/%Y %H:%M", time.gmtime(os.path.getmtime(os.path.join(path, name))))
                snippet_files.append([title, os.path.join(path, name), modified_str])
        elif mode == "notes":
            for name in files:
                for ext in settings().get("note_file_extensions"):
                    if fnmatch.fnmatch(name, "*." + ext):
                        title = os.path.join(relpath, name).replace(".\\", "").replace("\\", "/")
                        if title in exclude_files:
                            continue
                        modified_str = time.strftime("Last modified: %d/%m/%Y %H:%M", time.gmtime(os.path.getmtime(os.path.join(path, name))))
                        snippet_files.append([title, os.path.join(path, name), modified_str])

    snippet_files.sort(key=lambda item: os.path.getmtime(item[1]), reverse=True)
    return snippet_files


class CodeboxListCommand(sublime_plugin.ApplicationCommand):

    def run(self, mode="all"):
        root = get_root()
        self.snippets_dir = root
        self.file_list = find_snippets(self, root, mode=mode)
        rlist = setup_snippets_list(self.file_list)
        window = sublime.active_window()
        window.show_quick_panel(rlist, self.open_snippet)

    def open_snippet(self, index):
        if index == -1:
            return
        file_path = self.file_list[index][1]
        sublime.run_command("codebox_open", {"file_path": file_path})


class CodeboxOpenCommand(sublime_plugin.ApplicationCommand):

    def run(self, file_path):
        sublime.set_timeout(lambda: self.async_open(file_path), 0)

    def async_open(self, file_path):
        view = sublime.active_window().open_file(file_path, sublime.ENCODED_POSITION)


class CodeboxNewCommand(sublime_plugin.ApplicationCommand):

    def run(self, title=None):
        self.notes_dir = get_root()
        self.window = sublime.active_window()
        if title is None:
            self.window.show_input_panel(
                "Title", "", self.create_note, None, None)
        else:
            self.create_note(title)

    def create_note(self, title):
        filename = title.split("/")
        if len(filename) > 1:
            title = filename[len(filename) - 1]
            directory = os.path.join(self.notes_dir, filename[0])
        else:
            title = filename[0]
            directory = self.notes_dir
        if not os.path.exists(directory):
            os.makedirs(directory)

        file = os.path.join(directory, title)
        if not os.path.exists(file):
            open(file, 'w+').close()
        view = sublime.active_window().open_file(file)
