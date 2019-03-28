# -*- coding: utf-8 -*-
"""
/***************************************************************************
 NeighborMerger
                                 A QGIS plugin
 This plugin merges selected neighboring polygons
                             -------------------
        begin                : 2019-03-11
        copyright            : (C) 2019 by Matthieu
        email                : matthieu.viry@univ-grenoble-alpes.fr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load NeighborMerger class from file NeighborMerger.

    :param iface: A QGIS interface instance.
    :type iface: QgisInterface
    """
    #
    from .neighbor_merger import NeighborMerger
    return NeighborMerger(iface)
