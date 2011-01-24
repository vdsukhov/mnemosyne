#
# tag_tree_wdgt.py <Peter.Bienstman@UGent.be>
#

from PyQt4 import QtCore, QtGui

from mnemosyne.libmnemosyne.translator import _
from mnemosyne.libmnemosyne.tag_tree import TagTree
from mnemosyne.libmnemosyne.component import Component
from mnemosyne.libmnemosyne.criteria.default_criterion import DefaultCriterion

# We hijack QTreeWidgetItem a bit and store extra data in a hidden column, so
# that we don't need to implement a custom tree model.

DISPLAY_STRING = 0
NODE = 1

class TagDelegate(QtGui.QStyledItemDelegate):

    rename_node = QtCore.pyqtSignal(unicode, unicode)   

    def __init__(self, component_manager, parent=None):
        QtGui.QStyledItemDelegate.__init__(self, parent)
        self.old_node_label = None

    def createEditor(self, parent, option, index):
        editor = QtGui.QStyledItemDelegate.createEditor\
            (self, parent, option, index)        
        editor.editingFinished.connect(self.commit_and_close_editor)
        return editor

    def setEditorData(self, editor, index):
        # We display the full node (i.e. all levels including ::), so that
        # the hierarchy can be changed upon editing.
        node_index = index.model().index(index.row(), NODE, index.parent())
        self.old_node_label = index.model().data(node_index).toString()
        editor.setText(self.old_node_label)
        
    def commit_and_close_editor(self):
        editor = self.sender()
        self.rename_node.emit(self.old_node_label, editor.text())
        self.closeEditor.emit(editor, QtGui.QAbstractItemDelegate.NoHint)


class TagsTreeWdgt(QtGui.QWidget, Component):

    """Displays all the tags in a tree together with check boxes.
    
    If 'before_libmnemosyne_db' and 'after_libmnemosyne_db' are set, these need
    to be called before and after libmnemosyne operations which can modify the
    database.
    
    """

    def __init__(self, component_manager, parent,
        before_libmnemosyne_db=None, after_libmnemosyne_db=None):
        Component.__init__(self, component_manager)
        self.tag_tree = TagTree(self.component_manager)
        QtGui.QWidget.__init__(self, parent)
        self.before_libmnemosyne_db = before_libmnemosyne_db
        self.after_libmnemosyne_db = after_libmnemosyne_db
        self.layout = QtGui.QVBoxLayout(self)
        self.tag_tree_wdgt = QtGui.QTreeWidget(self)
        self.tag_tree_wdgt.setColumnCount(2)
        self.tag_tree_wdgt.setColumnHidden(1, True)
        self.tag_tree_wdgt.setColumnHidden(NODE, True)        
        self.tag_tree_wdgt.setHeaderHidden(True)
        self.tag_tree_wdgt.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.delegate = TagDelegate(component_manager, self)
        self.tag_tree_wdgt.setItemDelegate(self.delegate)
        self.delegate.rename_node.connect(self.rename_node)
        self.layout.addWidget(self.tag_tree_wdgt)
        self.tag_tree_wdgt.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tag_tree_wdgt.customContextMenuRequested.connect(self.context_menu)

    def selected_non_read_indices(self):
        indices = []
        for index in self.tag_tree_wdgt.selectedIndexes():
            node_index = \
                index.model().index(index.row(), NODE, index.parent())
            if index.model().data(node_index).toString() not in \
                ["__ALL__", "__UNTAGGED__"]:
                indices.append(index)
        return indices

    def context_menu(self, point):
        menu = QtGui.QMenu(self)
        rename_tag_action = QtGui.QAction(_("Re&name tag"), menu)
        rename_tag_action.setShortcut(QtCore.Qt.Key_Enter)
        rename_tag_action.triggered.connect(self.menu_rename)
        menu.addAction(rename_tag_action)
        remove_tag_action = QtGui.QAction(_("Re&move tag"), menu)
        remove_tag_action.setShortcut(QtGui.QKeySequence.Delete)
        remove_tag_action.triggered.connect(self.menu_remove)
        menu.addAction(remove_tag_action)
        indices = self.selected_non_read_indices()
        if len(indices) > 1:
            rename_tag_action.setEnabled(False)
            remove_tag_action.setText(_("Re&move tags"))
        if len(indices) >= 1:
            menu.exec_(self.tag_tree_wdgt.mapToGlobal(point))

    def menu_rename(self):
        # We display the full node (i.e. all levels including ::), so that
        # the hierarchy can be changed upon editing.
        index = self.selected_non_read_indices()[0]        
        node_index = index.model().index(index.row(), NODE, index.parent())
        old_node_label = index.model().data(node_index).toString()

        from mnemosyne.pyqt_ui.ui_rename_tag_dlg import Ui_RenameTagDlg        
        class RenameDlg(QtGui.QDialog, Ui_RenameTagDlg):          
            def __init__(self, old_node_label):
                QtGui.QDialog.__init__(self)
                self.setupUi(self)
                self.tag_name.setText(old_node_label)

        dlg = RenameDlg(old_node_label)  
        if dlg.exec_() == QtGui.QDialog.Accepted:
            self.rename_node(old_node_label, unicode(dlg.tag_name.text()))
        
    def menu_remove(self):
        for index in self.selected_non_read_indices():        
            print 'delete', index

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]:
            self.menu_rename()
        elif event.key() in [QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace]:
            self.menu_remove()
        
    def create_tree(self, tree, qt_parent):
        for node in tree:
            node_name = "%s (%d)" % \
                (self.tag_tree.display_name_for_node[node],
                self.tag_tree.card_count_for_node[node])
            node_item = QtGui.QTreeWidgetItem(qt_parent, [node_name, node], 0)
            node_item.setFlags(node_item.flags() | \
                QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate)
            if node not in ["__ALL__", "__UNTAGGED__"]:
                node_item.setFlags(node_item.flags() | \
                    QtCore.Qt.ItemIsEditable)
            if node in self.tag_tree.tag_for_node:
                self.tag_for_node_item[node_item] = \
                    self.tag_tree.tag_for_node[node]
            node_item.setData(NODE, QtCore.Qt.DisplayRole,
                    QtCore.QVariant(QtCore.QString(node)))              
            self.create_tree(tree=self.tag_tree[node], qt_parent=node_item)
        
    def display(self, criterion=None):
        # Create criterion if needed.
        if criterion is None:
            criterion = DefaultCriterion(self.component_manager)
            for tag in self.database().tags():
                criterion.active_tag__ids.add(tag._id)            
        # Create tree.
        self.tag_tree_wdgt.clear()
        self.tag_for_node_item = {}
        node = "__ALL__"
        node_name = "%s (%d)" % (self.tag_tree.display_name_for_node[node],
            self.tag_tree.card_count_for_node[node])
        root = self.tag_tree[node]
        root_item = QtGui.QTreeWidgetItem(\
            self.tag_tree_wdgt, [node_name, node], 0)
        root_item.setFlags(root_item.flags() | \
           QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsTristate)
        root_item.setCheckState(0, QtCore.Qt.Checked)
        self.create_tree(self.tag_tree[node], qt_parent=root_item)
        # Set forbidden tags.
        if len(criterion.forbidden_tag__ids):
            for node_item, tag in self.tag_for_node_item.iteritems():
                if tag._id in criterion.forbidden_tag__ids:
                    node_item.setCheckState(0, QtCore.Qt.Checked)
                else:
                    node_item.setCheckState(0, QtCore.Qt.Unchecked)  
        # Set active tags.
        else:
            for node_item, tag in self.tag_for_node_item.iteritems():
                if tag._id in criterion.active_tag__ids:
                    node_item.setCheckState(0, QtCore.Qt.Checked)
                else:
                    node_item.setCheckState(0, QtCore.Qt.Unchecked)
        # Finalise.
        self.tag_tree_wdgt.expandAll()

    def selection_to_active_tags_in_criterion(self, criterion):
        for item, tag in self.tag_for_node_item.iteritems():
            if item.checkState(0) == QtCore.Qt.Checked:
                criterion.active_tag__ids.add(tag._id)
        criterion.forbidden_tags = set()
        return criterion

    def selection_to_forbidden_tags_in_criterion(self, criterion):
        for item, tag in self.tag_for_node_item.iteritems():
            if item.checkState(0) == QtCore.Qt.Checked:
                criterion.forbidden_tag__ids.add(tag._id)
        criterion.active_tags = set(self.tag_for_node_item.values())
        return criterion

    def rename_node(self, old_node_label, new_node_label):
        old_node_label = unicode(old_node_label)
        new_node_label = unicode(new_node_label)
        saved_criterion = DefaultCriterion(self.component_manager)
        self.selection_to_active_tags_in_criterion(saved_criterion)
        # Case 1: regular rename.
        if old_node_label != new_node_label:
            if self.before_libmnemosyne_db:
                self.before_libmnemosyne_db()
            self.tag_tree.rename_node(old_node_label, new_node_label)
            # Rebuild the tree widget to reflect the changes.
            new_criterion = DefaultCriterion(self.component_manager)
            for tag in self.database().tags():
                if tag._id in saved_criterion.active_tag__ids:
                    new_criterion.active_tag__ids.add(tag._id)  
            self.display(new_criterion)
            if self.after_libmnemosyne_db:
                self.after_libmnemosyne_db()
        else:
            # Case 2: aborted edit, we need to redraw the tree to show the
            # card counts again.
            if old_node_label in self.tag_tree:
                new_criterion = DefaultCriterion(self.component_manager)
                for tag in self.database().tags():
                    if tag._id in saved_criterion.active_tag__ids:
                        new_criterion.active_tag__ids.add(tag._id)  
                self.display(new_criterion)
            # Case 3: extra event after regular rename, caused by hooking up
            # 'editor.editingFinished' (to treat case 2) as opposed to
            # 'editor.returnPressed'. We need to ignore this, otherwise we get
            # crashes.
            else:
                return

