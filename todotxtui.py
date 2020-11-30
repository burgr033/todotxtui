import py_cui
import os
import logging
import datetime
import json
from re import escape
from pathlib import Path

config_filename = "config.json"

config_home = Path.home() / '.todotxtui' / config_filename

if(config_home.is_file()):
    config_file = config_home
elif(Path(config_filename).is_file()):
    config_file = config_filename
else:
    print("missing config file. exit")
    os._exit(1)

# loading all the config
with open(config_file, 'r', encoding='utf-8-sig') as f:
    config = json.load(f)

todo_file = Path(config['todo_file_path'])

if(todo_file.is_file()):
    pass
else:
    print("missing todo file")
    os._exit(2)

# setting variables
today = datetime.datetime.today()
tomorrow = today + datetime.timedelta(days=1)
today = today.strftime('%Y-%m-%d')
tomorrow = tomorrow.strftime('%Y-%m-%d')


class SimpleTodoList:

    # reading todo.txt file and splitting the contents for the widgets based on the identifier or the x
    # this also checks if a line is longer than 1 char. If not it get's ignored
    def read_todo_file(self):
        todo = []
        in_progress = []
        done = []
        if os.path.exists(config['todo_file_path']):
            todo_fp = open(config['todo_file_path'], 'r', encoding='utf-8-sig')
            line = todo_fp.readline()
            while line:
                line = line.strip()
                if line.startswith("x "):
                    if len(line) > 1:
                        done.append(line)
                elif config['WIP_identifier'] in line:
                    if len(line) > 1:
                        in_progress.append(line)
                elif len(line) > 1:
                    todo.append(line)
                line = todo_fp.readline()
            todo_fp.close()
        self.todo_scroll_cell.clear()
        todo = self.sort_by_priority(todo)
        self.todo_scroll_cell.add_item_list(todo)
        self.in_progress_scroll_cell.clear()
        in_progress = self.sort_by_priority(in_progress)
        self.in_progress_scroll_cell.add_item_list(in_progress)
        self.done_scroll_cell.clear()
        self.done_scroll_cell.add_item_list(done)

    # this handy function replaces something like due:today with the current date.
    # you can set 1 keyword today and for tomorrow in your own language
    # this works when you add an item or when you search for an item.
    def replace_keywords(self, item_to_work):
        item_to_work = item_to_work.replace(
            "due:today", "due:{0}".format(today))
        item_to_work = item_to_work.replace(
            "due:tomorrow", "due:{0}".format(tomorrow))
        item_to_work = item_to_work.replace(
            "due:{0}".format(config['alternate_tomorrow']), "due:{0}".format(tomorrow))
        item_to_work = item_to_work.replace(
            "due:{0}".format(config['alternate_today']), "due:{0}".format(today))
        return item_to_work

    # this is called whenever the file is loaded (either refresh or during init) and sorts the first and second widget by Priority
    # I have no fucking idea how to sort in python so this is just plain rubbish probably.
    def sort_by_priority(self, list):
        todoa = []
        todob = []
        todoc = []
        todoz = []
        for todo in list:
            if todo.startswith("(A)"):
                todoa.append(todo)
                continue
            if todo.startswith("(B)"):
                todob.append(todo)
                continue
            if todo.startswith("(C)"):
                todoc.append(todo)
                continue
            else:
                todoz.append(todo)
                continue

        return (sorted(todoa) + sorted(todob) + sorted(todoc) + sorted(todoz))

    # this is so you can remove an item from the done list. Why only from done? because i accidentally hit DEL multiple times in other widgets and removed stuff...
    def remove_done_item(self):
        self.done_scroll_cell.remove_selected_item()
        self.save_todo_file()

    # function for adding items from the text box
    def add_item(self):
        self.color_context()
        item_to_add = '{}'.format(self.new_todo_textbox.get())
        if len(item_to_add) > 1:
            finished_item_to_add = self.replace_keywords(item_to_add)
            if finished_item_to_add.startswith("x "):
                self.done_scroll_cell.add_item(finished_item_to_add)
            elif config['WIP_identifier'] in finished_item_to_add:
                self.in_progress_scroll_cell.add_item(finished_item_to_add)
            else:
                self.todo_scroll_cell.add_item(finished_item_to_add)

            self.new_todo_textbox.clear()
            self.save_todo_file()

    # function for coloring due dates (tomorrow and today)
    def color_context(self):
        self.todo_scroll_cell.add_text_color_rule(
            "due:{0}" .format(today), py_cui.RED_ON_BLACK, 'contains', match_type='regex')
        self.todo_scroll_cell.add_text_color_rule(
            "due:{0}" .format(tomorrow), py_cui.YELLOW_ON_BLACK, 'contains', match_type='regex')
        self.in_progress_scroll_cell.add_text_color_rule(
            "due:{0}" .format(today), py_cui.RED_ON_BLACK, 'contains', match_type='regex')
        self.in_progress_scroll_cell.add_text_color_rule(
            "due:{0}" .format(tomorrow), py_cui.YELLOW_ON_BLACK, 'contains', match_type='regex')

    # function for clearing all colors
    def clear_all_colors(self):
        self.todo_scroll_cell._text_color_rules = []
        self.in_progress_scroll_cell._text_color_rules = []
        self.done_scroll_cell._text_color_rules = []

    # function for marking lines that are found during search
    def mark_line(self, search):
        search_term = search['Find']
        search_term = escape(search_term)
        search_term = self.replace_keywords(search_term)
        self.done_scroll_cell.add_text_color_rule(
            search_term, py_cui.WHITE_ON_BLUE, 'contains')
        self.in_progress_scroll_cell.add_text_color_rule(
            search_term, py_cui.WHITE_ON_BLUE, 'contains')
        self.todo_scroll_cell.add_text_color_rule(
            search_term, py_cui.WHITE_ON_BLUE, 'contains')
        self.color_context()

    # opening file wrapper function that is called when you press o in overview mode
    def open_todotxt_file(self):
        command = "{} {}".format(
            config['editor_path'], config['todo_file_path'])
        os.system(command)
        self.read_todo_file()

    # i forgot why we needed this. *shrug* It works...
    def find_form_trigger(self, form_output):
        self.mark_line(form_output)

    # function for opening search form
    def open_find_form(self):
        self.clear_all_colors()
        self.master.show_form_popup('Find and Mark', ['Find'], required=[
                                    'Find'], callback=self.find_form_trigger)

    # function that is called when you press enter in first widget.
    # it adds the work in progress tag context
    # " @WIP" ius used as seperator that decides it is shown in "in progress"
    # THIS IS NOT A KEYWORD IN TODOTXT standard, but it is save to use in todotxt syntax
    def mark_as_in_progress(self):
        in_prog = self.todo_scroll_cell.get()
        if in_prog is None:
            self.master.show_error_popup(
                'No Item', 'There is no item in the list to mark as in progress')
            return
        in_prog = in_prog + ' %s' % config['WIP_identifier']
        self.todo_scroll_cell.remove_selected_item()
        self.in_progress_scroll_cell.add_item(in_prog)
        self.save_todo_file()

    # this is called when you press enter in second widget.
    # mark as done adds an x in front of the line.
    # It is done now by todotxt syntax.
    # "x " is used as seperator that decides an item goes to "done"
    def mark_as_done(self):
        done = self.in_progress_scroll_cell.get()
        if done is None:
            self.master.show_error_popup(
                'No Item', 'There is no item in the list to mark as done')
            return
        done = 'x ' + today + ' ' + \
            done.replace(" {0}".format(config['WIP_identifier']), "")
        self.in_progress_scroll_cell.remove_selected_item()
        self.done_scroll_cell.add_item(done)
        self.save_todo_file()

    # this function saves the file
    def save_todo_file(self):
        if os.path.exists(config['todo_file_path']):
            os.remove(config['todo_file_path'])
        todo_fp = open(config['todo_file_path'], 'w', encoding='utf-8-sig')
        todo_items = self.todo_scroll_cell.get_item_list()
        in_progress_items = self.in_progress_scroll_cell.get_item_list()
        done_items = self.done_scroll_cell.get_item_list()
        for item in todo_items:
            todo_fp.write(item + '\n')
        for item in in_progress_items:
            todo_fp.write(item + '\n')
        for item in done_items:
            todo_fp.write(item + '\n')
        todo_fp.close()

    # init
    def __init__(self, master):

        self.master = master

        self.new_todo_textbox = self.master.add_text_box(
            'TODO Item',       0, 0, row_span=1, column_span=6)

        self.todo_scroll_cell = self.master.add_scroll_menu(
            'FUNNEL',       1, 0, row_span=7, column_span=3)

        self.in_progress_scroll_cell = self.master.add_scroll_menu(
            'DOING',        1, 3, row_span=5, column_span=3)

        self.done_scroll_cell = self.master.add_scroll_menu(
            'DONE',         6, 3, row_span=2, column_span=3)

        self.todo_scroll_cell.set_selected_color(
            py_cui.GREEN_ON_BLACK)

        self.in_progress_scroll_cell.set_selected_color(
            py_cui.GREEN_ON_BLACK)

        self.done_scroll_cell.set_selected_color(
            py_cui.GREEN_ON_BLACK)

        # press s in overview mode to safety save the file.
        self.master.add_key_command(
            py_cui.keys.KEY_S_LOWER, self.save_todo_file)
        # press r to refresh the file and apply SORT
        self.master.add_key_command(
            py_cui.keys.KEY_R_LOWER, self.read_todo_file)
        # press f to open the search form and reset any marked lines from prior search
        self.master.add_key_command(
            py_cui.keys.KEY_F_LOWER, self.open_find_form)
        # pressing o opens the text file in default system editor for quick multi editing or pasting. The TUI waits on close and reloads.
        self.master.add_key_command(
            py_cui.keys.KEY_O_LOWER, self.open_todotxt_file)
        # for quick cycling widgets press TAB
        self.master.set_widget_cycle_key(
            forward_cycle_key=py_cui.keys.KEY_TAB)

        # in DONE context DEL removes items from todo.txt
        self.done_scroll_cell.add_key_command(
            py_cui.keys.KEY_DELETE, self.remove_done_item)

        # in TEXTBOX context ENTER adds an item to "TODO"
        self.new_todo_textbox.add_key_command(
            py_cui.keys.KEY_ENTER, self.add_item)

        # in TODO context ENTER adds an item to "IN PROGRESS"
        self.todo_scroll_cell.add_key_command(
            py_cui.keys.KEY_ENTER, self.mark_as_in_progress)

        # in IN PROGRESS context ENTER adds an item to "DONE"
        self.in_progress_scroll_cell.add_key_command(
            py_cui.keys.KEY_ENTER, self.mark_as_done)

        # read file during init
        self.read_todo_file()
        # color the due dates now
        self.color_context()

        # this is some hacky shit so that no item is selected and you don't see the first lines marked in every widget. This does not work after refresh.
        self.todo_scroll_cell.set_selected_item_index(-1)
        self.in_progress_scroll_cell.set_selected_item_index(-1)
        self.done_scroll_cell.set_selected_item_index(-1)

        # these are the texts for each widget that are shown at the bottom border of the TUI
        self.todo_scroll_cell.set_focus_text(
            'FUNNEL | ESC - OverView | ENTER - move to DOING')
        self.in_progress_scroll_cell.set_focus_text(
            'DOING | ESC - OverView | ENTER - move to DONE')
        self.done_scroll_cell.set_focus_text(
            'DONE | ESC - OverView | DEL - remove selected item')


root = py_cui.PyCUI(8, 6)

if(config['debug']):
    root.enable_logging(logging_level=logging.ERROR)

if(config['unicode_borders']):
    root.toggle_unicode_borders()

# this text is shown in overview mode at the bottom border of the TUI
root.set_status_bar_text(
    'q - quit | TAB - cycle through widgets | f - find and mark | r - refresh | o - open TODO.txt')
# set some titles...
root.set_title('TodoTxTui')
s = SimpleTodoList(root)
root.start()
