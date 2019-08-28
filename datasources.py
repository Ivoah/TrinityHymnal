import json

import ui
import dialogs

def save_tags(tags):
    with open('tags.json', 'w') as f:
        json.dump(tags, f, indent=4)

def save_history(history):
    with open('history.json', 'w') as f:
        json.dump({d[0].isoformat(): d[1] for d in history}, f, indent=4)

def get_hymn_cell(hymn, tags):
    cell = ui.TableViewCell('subtitle')
    cell.text_label.text = hymn['title']
    cell.detail_text_label.text = hymn['#']
    cell.accessory_type = 'disclosure_indicator'
    for tag in tags:
        if hymn['#'] in tag['hymns']:
            cell.background_color = tag['color']
            break
    return cell


class HymnsDataSource:
    def __init__(self, hymns, tags, history):
        self.set_hymns(hymns)
        self.tags = tags
        self.history = history
    
    def set_hymns(self, hymns):
        self.sections = []

        for hymn in hymns:
            if len(self.sections) == 0 or '{section}: {subsection}'.format(**hymn) != self.sections[-1][0]:
                self.sections.append(('{section}: {subsection}'.format(**hymn), []))
            self.sections[-1][1].append(hymn)

    def tableview_number_of_sections(self, tableview):
        # Return the number of sections (defaults to 1)
        return len(self.sections)

    def tableview_number_of_rows(self, tableview, section):
        # Return the number of rows in the section
        return len(self.sections[section][1])

    def tableview_cell_for_row(self, tableview, section, row):
        # Create and return a cell for the given section/row
        hymn = self.sections[section][1][row]
        cell = get_hymn_cell(hymn, self.tags)
        return cell

    def tableview_title_for_header(self, tableview, section):
        # Return a title for the given section.
        # If this is not implemented, no section headers will be shown.
        return self.sections[section][0]

    def tableview_did_select(self, tableview, section, row):
        # Called when a row was selected.
        hymn = self.sections[section][1][row]
        tableview.selected_row = -1
        detail_view = ui.TableView('grouped')
        detail_view.name = hymn['title']
        detail_view.data_source = DetailDataSource(hymn, self.tags, self.history, tableview.reload_data)
        detail_view.delegate = detail_view.data_source
        tableview.navigation_view.push_view(detail_view)

class DetailDataSource:
    def __init__(self, hymn, tags, history, reload_parent):
        self.hymn = hymn
        self.tags = tags
        self.history = history
        self.reload_parent = reload_parent
    
    def tableview_number_of_sections(self, tableview):
        # Return the number of sections (defaults to 1)
        return 2

    def tableview_number_of_rows(self, tableview, section):
        # Return the number of rows in the section
        return [
            len(self.tags) + 1,
            len(list(filter(lambda d: self.hymn['#'] in d[1], self.history))) + 1
        ][section]

    def tableview_cell_for_row(self, tableview, section, row):
        # Create and return a cell for the given section/row
        hist = [date[0] for date in self.history if self.hymn['#'] in date[1]]
        cell = ui.TableViewCell()
        if section == 0:
            if row == len(self.tags):
                cell.text_label.text = 'Edit tags...'
                cell.accessory_type = 'disclosure_indicator'
            else:
                tag = self.tags[row]
                cell.text_label.text = tag['name']
                cell.background_color = tag['color']
                if self.hymn['#'] in tag['hymns']:
                    cell.accessory_type = 'checkmark'
        else:
            if row == 0:
                cell.text_label.text = 'Add to history...'
            else:
                cell.text_label.text = hist[row - 1].strftime('%A %B %d, %Y')
                cell.selectable = False
        return cell

    def tableview_title_for_header(self, tableview, section):
        # Return a title for the given section.
        # If this is not implemented, no section headers will be shown.
        return ['Tags', 'History'][section]
    
    @ui.in_background
    def tableview_did_select(self, tableview, section, row):
        # Called when a row was selected.
        tableview.selected_row = -1
        if section == 0:
            if row == len(self.tags):
                detail_view = ui.TableView('grouped')

                def reload_parent():
                    tableview.reload_data()
                    self.reload_parent()
                
                def toggle_editing(s):
                    detail_view.set_editing(not detail_view.editing, True)

                @ui.in_background
                def new_tag(s):
                    name = dialogs.input_alert('Tag name')
                    color = dialogs.input_alert('Tag color')
                    self.tags.append({'name': name, 'color': color, 'hymns': []})
                    save_tags(self.tags)
                    detail_view.reload_data()
                    reload_parent()

                detail_view.name = 'Edit Tags'
                detail_view.data_source = EditTagsDataSource(self.tags, reload_parent)
                detail_view.delegate = detail_view.data_source
                detail_view.left_button_items = [ui.ButtonItem('Edit', action=toggle_editing)]
                detail_view.right_button_items = [ui.ButtonItem('New tag', action=new_tag)]
                tableview.navigation_view.push_view(detail_view)
            else:
                tag = self.tags[row]
                if self.hymn['#'] in tag['hymns']:
                    tag['hymns'].remove(self.hymn['#'])
                else:
                    tag['hymns'].append(self.hymn['#'])
                save_tags(self.tags)
        elif section == 1 and row == 0:
            date = dialogs.date_dialog()
            if date is not None:
                i = 0
                while i < len(self.history) and self.history[i][0] > date:
                    i += 1
                
                if i < len(self.history) and self.history[i][0] == date:
                    self.history[i][1].append(self.hymn['#'])
                else:
                    self.history.insert(i, (date, [self.hymn['#']]))
                
                save_history(self.history)
                    
        tableview.reload_data()
        self.reload_parent()

class EditTagsDataSource:
    def __init__(self, tags, reload_parent):
        self.tags = tags
        self.reload_parent = reload_parent
    
    def tableview_number_of_sections(self, tableview):
        # Return the number of sections (defaults to 1)
        return 1

    def tableview_number_of_rows(self, tableview, section):
        # Return the number of rows in the section
        return len(self.tags)

    def tableview_cell_for_row(self, tableview, section, row):
        # Create and return a cell for the given section/row
        cell = ui.TableViewCell()
        tag = self.tags[row]
        cell.text_label.text = tag['name']
        cell.background_color = tag['color']
        return cell

    def tableview_title_for_header(self, tableview, section):
        # Return a title for the given section.
        # If this is not implemented, no section headers will be shown.
        return 'Tags'

    def tableview_can_delete(self, tableview, section, row):
        # Return True if the user should be able to delete the given row.
        return True

    def tableview_can_move(self, tableview, section, row):
        # Return True if a reordering control should be shown for the given row (in editing mode).
        return True

    @ui.in_background
    def tableview_delete(self, tableview, section, row):
        # Called when the user confirms deletion of the given row.
        dialogs.alert('Confirm delete', 'Are you sure you want to delete the tag?', 'Delete')
        del self.tags[row]
        save_tags(self.tags)
        tableview.reload_data()
        self.reload_parent()

    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        # Called when the user moves a row with the reordering control (in editing mode).
        self.tags.insert(to_row, self.tags.pop(from_row))
        save_tags(self.tags)
        self.reload_parent()

    @ui.in_background
    def tableview_did_select(self, tableview, section, row):
        # Called when a row was selected.
        tableview.selected_row = -1
        name_or_color = dialogs.alert('Edit', '', 'Name', 'Color')
        if name_or_color == 1:
            name = dialogs.input_alert('Tag name', '', self.tags[row]['name'])
            self.tags[row]['name'] = name
        elif name_or_color == 2:
            color = dialogs.input_alert('Tag color', '', self.tags[row]['color'])
            self.tags[row]['color'] = color
        
        save_tags(self.tags)
        tableview.reload_data()
        self.reload_parent()

class HistoryDataSource:
    def __init__(self, hymns, tags, history, reload_parent):
        self.hymns = hymns
        self.tags = tags
        self.history = history
        self.reload_parent = reload_parent
    
    def tableview_number_of_sections(self, tableview):
        # Return the number of sections (defaults to 1)
        return len(self.history)

    def tableview_number_of_rows(self, tableview, section):
        # Return the number of rows in the section
        return len(self.history[section][1])

    def tableview_cell_for_row(self, tableview, section, row):
        # Create and return a cell for the given section/row
        cell = get_hymn_cell(self.hymns[int(self.history[section][1][row]) - 1], self.tags)
        return cell

    def tableview_title_for_header(self, tableview, section):
        # Return a title for the given section.
        # If this is not implemented, no section headers will be shown.
        return self.history[section][0].strftime('%A %B %d, %Y')

    def tableview_can_delete(self, tableview, section, row):
        # Return True if the user should be able to delete the given row.
        return True

    def tableview_can_move(self, tableview, section, row):
        # Return True if a reordering control should be shown for the given row (in editing mode).
        return True

    def tableview_delete(self, tableview, section, row):
        # Called when the user confirms deletion of the given row.
        del self.history[section][1][row]
        if not self.history[section][1]: del self.history[section]
        save_history(self.history)
        tableview.reload_data()

    def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
        # Called when the user moves a row with the reordering control (in editing mode).
        self.history[to_section][1].insert(to_row, self.history[from_section][1].pop(from_row))
        if not self.history[from_section][1]: del self.history[from_section]
        save_history(self.history)
        tableview.reload_data()

    def tableview_did_select(self, tableview, section, row):
        # Called when a row was selected.

        def reload_parent():
            tableview.reload_data()
            self.reload_parent()

        hymn = self.hymns[int(self.history[section][1][row]) - 1]
        tableview.selected_row = -1
        detail_view = ui.TableView('grouped')
        detail_view.name = hymn['title']
        detail_view.data_source = DetailDataSource(hymn, self.tags, self.history, reload_parent)
        detail_view.delegate = detail_view.data_source
        tableview.navigation_view.push_view(detail_view)
