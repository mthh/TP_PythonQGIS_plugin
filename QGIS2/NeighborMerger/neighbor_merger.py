# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NeighborMerger
                                 A QGIS plugin
 This plugin merges selected neighboring polygons
                              -------------------
        begin                : 2019-03-11
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Matthieu
        email                : matthieu.viry@univ-grenoble-alpes.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
from qgis.core import QgsFeature, QgsGeometry
from qgis.gui import QgsMessageBar
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from neighbor_merger_dialog import NeighborMergerDialog
import os.path


class NeighborMerger:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgisInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'NeighborMerger_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&NeighborMerger')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'NeighborMerger')
        self.toolbar.setObjectName(u'NeighborMerger')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('NeighborMerger', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = NeighborMergerDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/NeighborMerger/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Merge neighbors'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&NeighborMerger'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def display_error(self, message):
        self.iface.messageBar().pushMessage(
            "Erreur", message, level=QgsMessageBar.CRITICAL)

    def merge_selected_features(self, layer):
        # Récupération de la liste des entités (QgsFeature) sélectionnées :
        selected = layer.selectedFeatures()
        if len(selected) < 2:
            self.display_error(
                u'Le nombre d\'entités sélectionnées est insuffisant.')
            return

        # Déselectionne les entités sélectionnés :
        layer.removeSelection()

        # Récupération des géométries (QgsGeometry)
        # des entités sélectionnées :
        geoms = [ft.geometry() for ft in selected]

        valid, invalidity_msg = all_touches_one_group(geoms)
        if not valid:
            self.display_error(invalidity_msg)
            return

        # Fusion des entités dans la nouvelle géométrie 'merged_geom' :
        merged_geom = QgsGeometry(geoms[0])
        for geom in geoms[1:]:
            merged_geom = merged_geom.combine(geom)

        # Création de la nouvelle entité utilisant cette géométrie
        # (il est nécessaire de lui dire les champs à utiliser
        #  avant l'ouverture du formulaire)
        new_feature = QgsFeature()
        new_feature.setGeometry(merged_geom)
        new_feature.setFields(layer.fields())

        # Entre en mode édition :
        layer.startEditing()

        # Ouverture du formulaire relatif à la nouvelle entité :
        valid = self.iface.openFeatureForm(layer, new_feature, False)
        if not valid:
            # Sortie du mode édition sans valider d'éventuels changements
            # et affichage d'un message d'erreur
            layer.rollBack()
            self.display_error(u'Erreur dans la saisie des attributs.')
            return

        # Ajout de la nouvelle entité :
        valid = layer.dataProvider().addFeatures([new_feature])
        if not valid:
            # Sortie du mode édition sans valider d'éventuels changements
            # et affichage d'un message d'erreur
            layer.rollBack()
            self.display_error(
                u'Erreur lors de l\'ajout de la nouvelle entité.')
            return

        # Suppression des entités dont est issues la fusion :
        for ft in selected:
            layer.deleteFeature(ft.id())

        # Validation des changements :
        layer.commitChanges()

        # Affichage d'un message de validation :
        self.iface.messageBar().pushMessage(
            "OK",
            u"La nouvelle entité a été créée.",
            level=QgsMessageBar.SUCCESS,
        )

    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            #
            target_layer = self.dlg.targetLayerComboBox.currentLayer()
            if not target_layer:
                self.display_error(u"Pas de couche séléctionnée.")
                return
            self.merge_selected_features(target_layer)


def all_touches_one_group(geoms):
    """
    Étant donné une liste de `QgsGeometry` cette fonction retourne un tuple
    dont le premier élément contient une valeur booléene (True / False, en
    fonction de si les géométries se touchent en formant un seul groupe)
    et dont le deuxième élément contient la raison si la réponse est False,
    ou un message vide sinon.
    """
    d = {i: [] for i in range(len(geoms))}
    # Pour chaque géométrie on va créer une liste de
    # ses voisines directes
    for ix1, g1 in enumerate(geoms):
      for ix2, g2 in enumerate(geoms):
          if ix1 == ix2: continue
          if g1.touches(g2):
              d[ix1].append(ix2)

    # Si au moins une d'entre elles à cette liste de vide,
    # c'est qu'elle n'a aucune voisine
    if any(len(li) == 0 for li in d.values()):
      return (False, u'Au moins une géométrie est isolée')

    # Pas besoin de continuer les vérifications s'il n'y a que
    # deux géomtries, elles sont bien voisines :
    if len(geoms) == 2:
      return (True, u'')

    # On va regarder si on peut parcourir l'ensemble des géométries
    # en allant de géométrie qui se touche à géométrie qui se touche

    # Un `set` pour garder une trace des polygones parcourus
    seen = set()

    # Une fonction récursive est définie pour parcourir les polygones
    # qui n'ont pas encore été vus
    def go_through(li):
      for item in li:
          if not item in seen:
              seen.add(item)
              go_through(d[item])

    # On applique cette fonction de manière arbitraire au premier polygone
    start_list = d[0]
    for ix in start_list:
      go_through(d[ix])

    # On vérifie que le nombre de polygones parcourus est égal au
    # nombre de polygones en entrée, sinon c'est qu'il y a plusieurs
    # groupes distincts de polygones qui se touchent

    if len(seen) != len(geoms):
      return (False, u'Les géométries sont en plusieurs groupes distincts')

    return (True, u'')
