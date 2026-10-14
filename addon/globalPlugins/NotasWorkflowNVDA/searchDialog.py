# -*- coding: UTF-8 -*-
# NotasWorkflowNVDA - searchDialog.py
# "Search notes": searches while typing (300 ms), results with excerpt and relevance.
# Copyright (C) 2026 Wellington Cruz <weliveiracruz@gmail.com>
# This file is covered by the GNU General Public License, version 2.

import addonHandler
import wx
from gui import guiHelper

from . import messages, search

addonHandler.initTranslation()

#: Pause in the typing before searching.
DEBOUNCE_MS = 300


class SearchDialog(wx.Dialog):
	def __init__(self, parent, plugin, query=""):
		# Translators: title of the search window.
		super().__init__(parent, title=_("Search notes"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
		self.plugin = plugin
		self.resultIds = []
		#: Id of the last note opened from the results (the main window selects it).
		self.openedId = None
		self.lastQuery = None
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		# Translators: label of the search field.
		self.queryEdit = sHelper.addLabeledControl(_("&Search for:"), wx.TextCtrl, style=wx.TE_PROCESS_ENTER, size=(560, -1))
		self.queryEdit.SetMaxLength(search.MAX_QUERY)
		self.resultsLabel = wx.StaticText(self, label=self._label(0))
		self.results = wx.ListCtrl(self, size=(560, 300), style=wx.LC_REPORT | wx.LC_SINGLE_SEL)
		for title, width in (
			# Translators: column of the search results.
			(_("Title"), 170),
			# Translators: column of the search results: part of the text where the words were found.
			(_("Excerpt"), 250),
			# Translators: column of the search results.
			(_("Relevance"), 70),
			# Translators: column of the search results.
			(_("Updated on"), 70),
		):
			self.results.AppendColumn(title, width=width)
		sHelper.addItem(self.resultsLabel)
		sHelper.addItem(self.results, flag=wx.EXPAND, proportion=1)
		buttons = guiHelper.ButtonHelper(wx.HORIZONTAL)
		# Translators: button that opens the selected note.
		self.openButton = buttons.addButton(self, label=_("&Open"))
		# Translators: button that closes the window.
		self.closeButton = buttons.addButton(self, id=wx.ID_CLOSE, label=_("C&lose"))
		sHelper.addItem(buttons)
		main = wx.BoxSizer(wx.VERTICAL)
		main.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL | wx.EXPAND, proportion=1)
		self.SetSizer(main)
		main.Fit(self)
		self.SetEscapeId(wx.ID_CLOSE)
		self.timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, lambda evt: self.runSearch(), self.timer)
		self.queryEdit.Bind(wx.EVT_TEXT, lambda evt: self.timer.StartOnce(DEBOUNCE_MS))
		self.queryEdit.Bind(wx.EVT_TEXT_ENTER, self.onEnter)
		self.results.Bind(wx.EVT_LIST_ITEM_ACTIVATED, lambda evt: self.onOpen(None))
		self.results.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda evt: self.updateButtons())
		self.openButton.Bind(wx.EVT_BUTTON, self.onOpen)
		self.closeButton.Bind(wx.EVT_BUTTON, lambda evt: self.close())
		self.Bind(wx.EVT_CLOSE, lambda evt: self.close())
		self.updateButtons()
		self.CentreOnScreen()
		if query:
			self.queryEdit.ChangeValue(query)
			self.runSearch(announce=False)
		self.queryEdit.SetFocus()

	def _label(self, count):
		# Translators: label of the search results with their number.
		return _("&Results ({count}):").format(count=count)

	def updateButtons(self):
		self.openButton.Enable(self.results.GetFirstSelected() >= 0)

	def runSearch(self, announce=True):
		self.timer.Stop()
		query = self.queryEdit.GetValue()
		self.lastQuery = query
		notes = self.plugin.store.notes
		index = self.plugin.searchIndex
		found = search.search(notes, query, index=index)
		if len(index) > len(notes) + 1000:
			# Many notes were deleted or replaced: drop their prepared text.
			index.forget({n["id"] for n in notes})
		self.results.DeleteAllItems()
		self.resultIds = []
		for note, score, excerpt in found:
			row = self.results.InsertItem(self.results.GetItemCount(), messages.noteTitle(note))
			self.results.SetItem(row, 1, excerpt)
			self.results.SetItem(row, 2, "%d%%" % round(score * 100))
			self.results.SetItem(row, 3, messages.formatDate(note["updatedAt"]))
			self.resultIds.append(note["id"])
		if self.resultIds:
			self.results.Select(0)
			self.results.Focus(0)
		self.resultsLabel.SetLabel(self._label(len(self.resultIds)))
		self.updateButtons()
		if announce and query.strip():
			if self.resultIds:
				# Translators: spoken after a search; {count} is "1 note" or "3 notes".
				self.plugin.speak(_("{count} found").format(count=messages.notesCount(len(self.resultIds))))
			else:
				# Translators: spoken when the search found nothing.
				self.plugin.speak(_("No note found"))
		return found

	def onEnter(self, evt):
		self.runSearch()
		if self.resultIds:
			self.results.SetFocus()

	def onOpen(self, evt):
		row = self.results.GetFirstSelected()
		if not 0 <= row < len(self.resultIds):
			return
		noteId = self.resultIds[row]
		self.openedId = noteId
		self.plugin.editNote(self, noteId)
		# The note may have changed (or been deleted): search again, keeping the place.
		self.runSearch(announce=False)
		if noteId in self.resultIds:
			row = self.resultIds.index(noteId)
			self.results.Select(row)
			self.results.Focus(row)
		if self.resultIds:
			self.results.SetFocus()
		else:
			self.queryEdit.SetFocus()

	def close(self):
		self.timer.Stop()
		if self.IsModal():
			self.EndModal(wx.ID_CLOSE)
		else:
			self.Destroy()
