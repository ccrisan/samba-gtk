#!/usr/bin/python

import traceback
import gtk, gobject
import sambagtk

from samba.dcerpc import mgmt, epmapper
from objects import User, Group
from dialogs import UserEditDialog


class SAMManager:
    
    def __init__(self):
        self.connection = sambagtk.gtk_connect_rpc_interface("samr")
        self.user_list = []
        self.group_list = []
        
    def close(self):
        if (self.connection != None):
            self.connection.close()
        
    def get_from_pipe(self):
        group1 = Group("group1", "Group Description 1", 0xAAAA)
        group2 = Group("group2", "Group Description 2", 0xBBBB)
        
        del self.group_list[:]
        self.group_list.append(group1)
        self.group_list.append(group2)
        
        user1 = User("username1", "Full Name 1", "User Description 1", 0xDEAD)
        user1.password = "password1"
        user1.must_change_password = True
        user1.cannot_change_password = False
        user1.password_never_expires = False
        user1.account_disabled = False
        user1.account_locked_out = False
        user1.group_list = [self.group_list[0]]
        user1.profile_path = "/profiles/user1"
        user1.logon_script = "script1"
        user1.homedir_path = "/home/user1"
        user1.map_homedir_drive = None
                
        user2 = User("username2", "Full Name 2", "User Description 2", 0xBEEF)
        user2.password = "password2"
        user2.must_change_password = False
        user2.cannot_change_password = True
        user2.password_never_expires = True
        user2.account_disabled = True
        user2.account_locked_out = True
        user2.group_list = [self.group_list[1]]
        user2.profile_path = "/profiles/user2"
        user2.logon_script = "script2"
        user2.homedir_path = "/home/user2"
        user2.map_homedir_drive = 4
        
        del self.user_list[:]
        self.user_list.append(user1)
        self.user_list.append(user2)
        
    def set_user_to_pipe(self, user):
        None

    def set_group_to_pipe(self, group):
        None

    
class SAMWindow(gtk.Window):

    def __init__(self):
        super(SAMWindow, self).__init__()

        self.create()
        self.sam_manager = None
        self.users_groups_notebook_page_num = 0
        self.update_sensitivity()
        
    def create(self):
        
        
        # main window        

        accel_group = gtk.AccelGroup()
        
        self.set_title("User/Group Management")
        self.set_default_size(800, 600)
        self.connect("delete_event", self.on_self_delete)
        
    	vbox = gtk.VBox(False, 0)
    	self.add(vbox)


        # menu
        
        menubar = gtk.MenuBar()
        vbox.pack_start(menubar, False, False, 0)
        

        self.file_item = gtk.MenuItem("_File")
        menubar.add(self.file_item)
        
        file_menu = gtk.Menu()
        self.file_item.set_submenu(file_menu)
        
        self.connect_item = gtk.ImageMenuItem(gtk.STOCK_CONNECT, accel_group)
        file_menu.add(self.connect_item)
        
        self.disconnect_item = gtk.ImageMenuItem(gtk.STOCK_DISCONNECT, accel_group)
        self.disconnect_item.set_sensitive(False)
        file_menu.add(self.disconnect_item)
        
        self.sel_domain_item = gtk.MenuItem("_Select Domain", accel_group)
        self.sel_domain_item.set_sensitive(False)
        file_menu.add(self.sel_domain_item)
        
        menu_separator_item = gtk.SeparatorMenuItem()
        menu_separator_item.set_sensitive(False)
        file_menu.add(menu_separator_item)
        
        self.quit_item = gtk.ImageMenuItem(gtk.STOCK_QUIT, accel_group)
        file_menu.add(self.quit_item)
        
        
        self.view_item = gtk.MenuItem("_View")
        menubar.add(self.view_item)
        
        view_menu = gtk.Menu()
        self.view_item.set_submenu(view_menu)
        
        self.refresh_item = gtk.ImageMenuItem(gtk.STOCK_REFRESH, accel_group)
        self.refresh_item.set_sensitive(False)
        view_menu.add(self.refresh_item)
        
        
        self.user_group_item = gtk.MenuItem("_User")
        menubar.add(self.user_group_item)
        
        user_group_menu = gtk.Menu()
        self.user_group_item.set_submenu(user_group_menu)

        self.new_item = gtk.ImageMenuItem(gtk.STOCK_NEW, accel_group)
        self.new_item.set_sensitive(False)
        user_group_menu.add(self.new_item)

        self.delete_item = gtk.ImageMenuItem(gtk.STOCK_DELETE, accel_group)
        self.delete_item.set_sensitive(False)
        user_group_menu.add(self.delete_item)

        self.edit_item = gtk.ImageMenuItem(gtk.STOCK_EDIT, accel_group)
        self.edit_item.set_sensitive(False)
        user_group_menu.add(self.edit_item)

        
        self.policies_item = gtk.MenuItem("_Policies")
        menubar.add(self.policies_item)

        policies_menu = gtk.Menu()
        self.policies_item.set_submenu(policies_menu)
        
        self.user_rights_item = gtk.MenuItem("_User Rights...", accel_group)
        self.user_rights_item.set_sensitive(False)
        policies_menu.add(self.user_rights_item)

        self.audit_item = gtk.MenuItem("A_udit...", accel_group)
        self.audit_item.set_sensitive(False)
        policies_menu.add(self.audit_item)

        menu_separator_item = gtk.SeparatorMenuItem()
        menu_separator_item.set_sensitive(False)
        policies_menu.add(menu_separator_item)
        
        self.trust_relations_item = gtk.MenuItem("_Trust relations", accel_group)
        self.trust_relations_item.set_sensitive(False)
        policies_menu.add(self.trust_relations_item)
        
        
        self.help_item = gtk.MenuItem("_Help")
        menubar.add(self.help_item)

        help_menu = gtk.Menu()
        self.help_item.set_submenu(help_menu)

        self.about_item = gtk.ImageMenuItem(gtk.STOCK_ABOUT, accel_group)
        help_menu.add(self.about_item)
        
        
        # user list
        
        self.users_groups_notebook = gtk.Notebook()
        vbox.pack_start(self.users_groups_notebook, True, True, 0)
        
        scrolledwindow = gtk.ScrolledWindow(None, None)
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.users_groups_notebook.append_page(scrolledwindow, gtk.Label("Users"))
        
        self.users_tree_view = gtk.TreeView()
        scrolledwindow.add(self.users_tree_view)
        
        column = gtk.TreeViewColumn()
        column.set_title("Name")
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.users_tree_view.append_column(column)
        column.add_attribute(renderer, "text", 0)
                
        column = gtk.TreeViewColumn()
        column.set_title("Full Name")
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.users_tree_view.append_column(column)
        column.add_attribute(renderer, "text", 1)
        
        column = gtk.TreeViewColumn()
        column.set_title("Description")
        column.set_expand(True)
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.users_tree_view.append_column(column)
        column.add_attribute(renderer, "text", 2)
        
        column = gtk.TreeViewColumn()
        column.set_title("RID")
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.users_tree_view.append_column(column)
        column.set_cell_data_func(renderer, self.cell_data_func_hex, 3)
        
        self.users_store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_INT)
        self.users_store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.users_tree_view.set_model(self.users_store)


        # group list

        scrolledwindow = gtk.ScrolledWindow(None, None)
        scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.users_groups_notebook.append_page(scrolledwindow, gtk.Label("Groups"))
        
        self.groups_tree_view = gtk.TreeView()
        scrolledwindow.add(self.groups_tree_view)
        
        column = gtk.TreeViewColumn()
        column.set_title("Name")
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.groups_tree_view.append_column(column)
        column.add_attribute(renderer, "text", 0)
                
        column = gtk.TreeViewColumn()
        column.set_title("Description")
        column.set_expand(True)
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.groups_tree_view.append_column(column)
        column.add_attribute(renderer, "text", 1)
        
        column = gtk.TreeViewColumn()
        column.set_title("RID")
        renderer = gtk.CellRendererText()
        column.pack_start(renderer, True)
        self.groups_tree_view.append_column(column)
        column.set_cell_data_func(renderer, self.cell_data_func_hex, 2)

        self.groups_store = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_INT)
        self.groups_store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.groups_tree_view.set_model(self.groups_store)


        # status bar

        self.statusbar = gtk.Statusbar()
        self.statusbar.set_has_resize_grip(True)
        vbox.pack_start(self.statusbar, False, False, 0)
        
        
        # signals/events
        
        self.connect_item.connect("activate", self.on_connect_item_activate)
        self.disconnect_item.connect("activate", self.on_disconnect_item_activate)
        self.sel_domain_item.connect("activate", self.on_sel_domain_item_activate)
        self.quit_item.connect("activate", self.on_quit_item_activate)
        self.refresh_item.connect("activate", self.on_refresh_item_activate)
        self.new_item.connect("activate", self.on_new_item_activate)
        self.delete_item.connect("activate", self.on_delete_item_activate)
        self.edit_item.connect("activate", self.on_edit_item_activate)
        self.user_rights_item.connect("activate", self.on_user_rights_item_activate)
        self.audit_item.connect("activate", self.on_audit_item_activate)
        self.trust_relations_item.connect("activate", self.on_trust_relations_item_activate)        
        self.about_item.connect("activate", self.on_about_item_activate)
        
        self.users_groups_notebook.connect("switch-page", self.on_users_groups_notebook_switch_page)
        self.users_tree_view.get_selection().connect("changed", self.on_users_tree_view_selection_changed)
        self.groups_tree_view.get_selection().connect("changed", self.on_groups_tree_view_selection_changed)
        
        self.add_accel_group(accel_group)

    def refresh_user_list_view(self):
        self.users_store.clear()
        for user in self.sam_manager.user_list:
            self.users_store.append(user.list_view_representation())

    def refresh_group_list_view(self):
        self.groups_store.clear()
        for group in self.sam_manager.group_list:
            self.groups_store.append(group.list_view_representation())

    def set_status(self, message):
        self.statusbar.pop(0)
        self.statusbar.push(0, message)
        
    def show_message_box(self, type, buttons, message):
        message_box = gtk.MessageDialog(self, gtk.DIALOG_MODAL, type, buttons, message)
        response = message_box.run()
        message_box.hide()
        
        return response

    def update_sensitivity(self):
        connected = (self.sam_manager != None)
        user_selected = (self.users_tree_view.get_selection().count_selected_rows() > 0)
        group_selected = (self.groups_tree_view.get_selection().count_selected_rows() > 0)
        obj_selected = [user_selected, group_selected][self.users_groups_notebook_page_num]
        
        self.connect_item.set_sensitive(not connected)
        self.disconnect_item.set_sensitive(connected)
        self.sel_domain_item.set_sensitive(connected)
        self.refresh_item.set_sensitive(connected)
        self.new_item.set_sensitive(connected)
        self.delete_item.set_sensitive(connected and obj_selected)
        self.edit_item.set_sensitive(connected and obj_selected)
        self.user_rights_item.set_sensitive(connected)
        self.audit_item.set_sensitive(connected)
        self.trust_relations_item.set_sensitive(connected)

    def run_user_edit_dialog(self, user):
        # todo implement an apply callback
        if (user == None):
            user = User("", "", "", 0x0000)
        
        dialog = UserEditDialog(self.sam_manager, user)
        dialog.show_all()
        
        while True:
            response_id = dialog.run()
            
            if (response_id == gtk.RESPONSE_OK):
                problem_msg = dialog.check_for_problems()
                
                if (problem_msg != None):
                    self.show_message_box(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, problem_msg)
                else:
                    dialog.set_to_user(user)
                    dialog.hide()
                    break
            
            elif (response_id == gtk.RESPONSE_CANCEL):
                dialog.hide()
                break
            
            elif (response_id == gtk.RESPONSE_APPLY):
                problem_msg = dialog.check_for_problems()
                
                if (problem_msg != None):
                    self.show_message_box(gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, problem_msg)
                else:
                    dialog.set_to_user(user)
            
            else:
                dialog.hide()
                break
        
        return response_id

    def cell_data_func_hex(self, column, cell, model, iter, column_no):
        cell.set_property("text", "0x%X" % model.get_value(iter, column_no))

    def on_self_delete(self, widget, event):
        if (self.sam_manager != None):
            self.on_disconnect_item_activate(self.disconnect_item)
        
        gtk.main_quit()
        return False

    def on_connect_item_activate(self, widget):
        try:
            self.sam_manager = SAMManager()
            self.sam_manager.get_from_pipe()
            
        except Exception:
            print "failed to connect"
            traceback.print_exc()
            self.sam_manager = None
            return
        
        self.refresh_user_list_view()
        self.refresh_group_list_view()
        self.update_sensitivity()

    def on_disconnect_item_activate(self, widget):
        if (self.sam_manager != None):
            self.sam_manager.close()
            self.sam_manager = None
            self.users_store.clear()
            self.groups_store.clear()
            
        self.update_sensitivity()
    
    def on_sel_domain_item_activate(self, widget):
        None

    def on_quit_item_activate(self, widget):
        self.on_self_delete(None, None)
    
    def on_refresh_item_activate(self, widget):
        self.sam_manager.get_from_pipe()
        self.refresh_user_list_view()
        self.refresh_group_list_view()
        
    def on_new_item_activate(self, widget):
        if (self.users_groups_notebook_page_num == 0):
            pass
        else:
            pass

    def on_delete_item_activate(self, widget):
        None

    def on_edit_item_activate(self, widget):
        (model, iter) = self.users_tree_view.get_selection().get_selected()
        if (iter == None): # no selection
            return 
        
        rid = model.get_value(iter, 3)
        
        edit_user = None
        for user in self.sam_manager.user_list:
            if (user.rid == rid):
                edit_user = user
                break
            
        if (edit_user != None):            
            # TODO: handle response_i
            response_id = self.run_user_edit_dialog(edit_user)


    def on_user_rights_item_activate(self, widget):
        None
    
    def on_audit_item_activate(self, widget):
        None
    
    def on_trust_relations_item_activate(self, widget):
        None
    
    def on_about_item_activate(self, widget):
        aboutwin = sambagtk.AboutDialog("PyGWSAM")
        aboutwin.run()
        aboutwin.destroy()

    def on_users_tree_view_selection_changed(self, widget):
        self.update_sensitivity()

    def on_groups_tree_view_selection_changed(self, widget):
        self.update_sensitivity()

    def on_users_groups_notebook_switch_page(self, widget, page, page_num):
        self.users_groups_notebook_page_num = page_num # workaround for the fact that the signal is emitted before the change
        self.user_group_item.get_child().set_text(["Users", "Groups"][page_num > 0])
        self.update_sensitivity()


main_window = SAMWindow()
main_window.show_all()
gtk.main()