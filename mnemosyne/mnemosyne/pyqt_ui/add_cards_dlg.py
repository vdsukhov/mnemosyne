##############################################################################
#
# Widget to add new items <Peter.Bienstman@UGent.be>
# Duplicate check by Jarno Elonen <elonen@iki.fi>
#
##############################################################################

from PyQt4.QtCore import *
from PyQt4.QtGui import *


from mnemosyne.libmnemosyne import *
from add_cards_frm import *
from card_twosided_dlg import *
#from edit_item_dlg import *


##############################################################################
#
# AddCardsDlg
#
##############################################################################

class AddCardsDlg(QDialog, Ui_AddCardsFrm):

    ##########################################################################
    #
    # __init__
    #
    ##########################################################################
    
    def __init__(self, filename, parent = None):
        
        QDialog.__init__(self, parent)

        # TODO: modal, Qt.WStyle_MinMax | Qt.WStyle_SysMenu))?
        
        self.setupUi(self)
        
        self.replace_me = CardTwoSidedDlg()

        self.vboxlayout.insertWidget(1, self.replace_me)
        
           
        #self.addViceVersa.setChecked(get_config("last_add_vice_versa"))
        #self.update_combobox(get_config("last_add_category"))

        self.connect(self.grades, SIGNAL("clicked(int)"),
                     self.new_item)

        self.connect(self.preview_button, SIGNAL("clicked()"),
                     self.preview)


        
        #if get_config("QA_font") != None:
        #    font = QFont()
        #    font.fromString(get_config("QA_font"))
        #    self.question.setFont(font)
        #    self.pronunciation.setFont(font)
        #    self.answer.setFont(font)
            #self.categories.setFont(font)
            
        


    ##########################################################################
    #
    # update_combobox
    #
    ##########################################################################

    def update_combobox(self, current_cat_name):

        no_of_categories = self.categories.count()
        for i in range(no_of_categories-1,-1,-1):
            self.categories.removeItem(i)

        self.categories.insertItem(self.trUtf8("<default>"))
        names = [cat.name for cat in get_categories()]
        names.sort()
        for name in names:
            if name != self.trUtf8("<default>"):
                self.categories.insertItem(name)

        for i in range(self.categories.count()):
            if self.categories.text(i) == current_cat_name:
                self.categories.setCurrentItem(i)
                break






            
    ##########################################################################
    #
    # reject
    #
    ##########################################################################
    
    def reject(self):

        if not self.question.text() and not self.answer.text():
            QDialog.reject(self)
            return

        status = QMessageBox.warning(None,
                        self.trUtf8("Mnemosyne"),
                        self.trUtf8("Abandon current card?"),
                        self.trUtf8("&Yes"),
                        self.trUtf8("&No"),
                        "", 1, -1)
        if status == 0:
            QDialog.reject(self)
            return
        else:
            return




    ##########################################################################
    #
    # preview
    #
    ##########################################################################

    def preview(self):

        if get_config("3_sided_input") == False:
        
            dlg = PreviewItemDlg(unicode(self.question.text()),
                                 unicode(self.answer.text()),
                                 unicode(self.categories.currentText()),
                                 self)
        else:
            dlg = PreviewItemDlg(unicode(self.question.text()),
                                 unicode(QString(self.pronunciation.text()).\
                                         append(QString("\n")).\
                                         append(QString(self.answer.text()))),
                                 unicode(self.categories.currentText()),
                                 self)            
        dlg.exec_loop()

        

    ##########################################################################
    #
    # check_duplicates_and_add
    #
    ##########################################################################

    def check_duplicates_and_add(self, grade, q, a, cat_name, id=None):

        if get_config("check_duplicates_when_adding") == True:

            # Find duplicate questions and refuse to add if duplicate
            # answers are found as well.
            
            allow_dif_cat = get_config("allow_duplicates_in_diff_cat")
            
            same_questions = []
            
            for item in get_items():
                if item.q == q:
                    if item.a == a:
                        
                        if item.cat.name == cat_name or not allow_dif_cat:
                            QMessageBox.information(None,
                                self.trUtf8("Mnemosyne"),
                                self.trUtf8("Card is already in database.\n")\
                                .append(self.trUtf8("Duplicate not added.")),
                                self.trUtf8("&OK"))
                
                            return None
                        
                    elif item.cat.name == cat_name or not allow_dif_cat:
                        same_questions.append(item)

            # Make a list of already existing answers for this question
            # and merge if the user wishes so.
            
            if len(same_questions) != 0:

                answers = a
                for i in same_questions:
                    answers += ' / ' + i.a
                        
                status = QMessageBox.question(None,
                   self.trUtf8("Mnemosyne"),
                   self.trUtf8("There are different answers for")\
                     .append(self.trUtf8(" this question:\n\n"))\
                     .append(answers),
                   self.trUtf8("&Merge and edit"),
                   self.trUtf8("&Add as is"),
                   self.trUtf8("&Do not add"), 0, -1)
                
                if status == 0: # Merge and edit.
                    
                    new_item = add_new_item(grade, q, a, cat_name, id)
                    self.update_combobox(cat_name)
                    
                    for i in same_questions:
                        new_item.grade = min(new_item.grade, i.grade)
                        new_item.a += ' / ' + i.a
                        delete_item(i)
                        
                    dlg = EditItemDlg(new_item, self)
                    
                    dlg.exec_loop()
                    
                    return new_item

                if status == 2: # Don't add.
                    return None

        new_item = add_new_item(grade, q, a, cat_name, id)
        self.update_combobox(cat_name)
                
        return new_item



    ##########################################################################
    #
    # new_item
    #
    #   Don't rebuild revision queue afterwards, as this can cause corruption
    #   for the current item. The new items will show up after the old queue
    #   is empty.
    #
    ##########################################################################

    def new_item(self, grade):

        q        = unicode(self.question.text())
        p        = unicode(self.pronunciation.text())
        a        = unicode(self.answer.text())
        cat_name = unicode(self.categories.currentText())

        if self.addViceVersa.isOn():
            if q == "" or a == "":
                return
        else:
            if q == "":
                return

        if get_config("3_sided_input") == False:

            orig_added = self.check_duplicates_and_add(grade,q,a,cat_name)
            rev_added = None
            if orig_added and self.addViceVersa.isOn():
                rev_added = self.check_duplicates_and_add(grade,a,q,\
                                               cat_name,orig_added.id+'.inv')

            if self.addViceVersa.isOn() and orig_added and not rev_added:
            
                # Swap question and answer.
            
                self.question.setText(a)
                self.answer.setText(q)
                self.addViceVersa.setChecked(False)
            
            elif orig_added:
            
                # Clear the form to make room for new question.
            
                self.question.setText("")
                self.answer.setText("")

        else: # 3-sided input.
            
            i = self.check_duplicates_and_add(grade,q,p+'\n'+a,cat_name)

            if i:
                self.check_duplicates_and_add(grade,a,q+'\n'+p,cat_name,
                                              i.id+'.tr.1')
            
            self.question.setText("")
            self.pronunciation.setText("")  
            self.answer.setText("")
                
        self.question.setFocus()

        set_config("last_add_vice_versa", self.addViceVersa.isOn())
        set_config("last_add_category",   cat_name)

        save_database(get_config("path"))