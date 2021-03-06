# -*- coding: utf-8 -*-

"""
***************************************************************************
    Dissolve.py
    ---------------------
    Date                 : August 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Victor Olaya'
__date__ = 'August 2012'
__copyright__ = '(C) 2012, Victor Olaya'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from sextante.core.GeoAlgorithm import GeoAlgorithm
import os.path
from PyQt4 import QtGui
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from sextante.parameters.ParameterVector import ParameterVector
from sextante.core.QGisLayers import QGisLayers
from sextante.outputs.OutputVector import OutputVector
from sextante.parameters.ParameterBoolean import ParameterBoolean
from sextante.parameters.ParameterTableField import ParameterTableField
from sextante.core.SextanteLog import SextanteLog

class Dissolve(GeoAlgorithm):

    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    FIELD = "FIELD"
    DISSOLVE_ALL = "DISSOLVE_ALL"

    #===========================================================================
    # def getIcon(self):
    #    return QtGui.QIcon(os.path.dirname(__file__) + "/icons/dissolve.png")
    #===========================================================================

    def processAlgorithm(self, progress):        
        useField = not self.getParameterValue(Dissolve.DISSOLVE_ALL)
        fieldname = self.getParameterValue(Dissolve.FIELD)
        vlayerA = QGisLayers.getObjectFromUri(self.getParameterValue(Dissolve.INPUT))
        field = vlayerA.dataProvider().fieldNameIndex(fieldname)
        GEOS_EXCEPT = True
        vproviderA = vlayerA.dataProvider()
        allAttrsA = vproviderA.attributeIndexes()
        fields = vproviderA.fields()
        writer = self.getOutputFromName(Dissolve.OUTPUT).getVectorWriter(fields, vproviderA.geometryType(), vproviderA.crs() )
        #inFeat = QgsFeature()
        outFeat = QgsFeature()
        vproviderA.rewind()
        nElement = 0
        nFeat = vproviderA.featureCount()
        if not useField:
            first = True
            features = QGisLayers.features(vlayerA)
            for inFeat in features:
                nElement += 1
                progress.setPercentage(int(nElement/nFeat * 100))
                if first:
                    attrs = inFeat.attributeMap()
                    tmpInGeom = QgsGeometry( inFeat.geometry() )
                    outFeat.setGeometry( tmpInGeom )
                    first = False
                else:
                    tmpInGeom = QgsGeometry( inFeat.geometry() )
                    tmpOutGeom = QgsGeometry( outFeat.geometry() )
                    try:
                        tmpOutGeom = QgsGeometry( tmpOutGeom.combine( tmpInGeom ) )
                        outFeat.setGeometry( tmpOutGeom )
                    except:
                        GEOS_EXCEPT = False
                        continue
                    outFeat.setAttributeMap( attrs )
                    writer.addFeature( outFeat )
        else:
            unique = vproviderA.uniqueValues( int( field ) )
            nFeat = nFeat * len( unique )
            for item in unique:
                first = True
                add = True
                vproviderA.select( allAttrsA )
                vproviderA.rewind()
                features = QGisLayers.features(vlayerA)
                for inFeat in features:
                    nElement += 1
                    progress.setPercentage(int(nElement/nFeat * 100))
                    atMap = inFeat.attributeMap()
                    tempItem = atMap[ field ]
                    if tempItem.toString().trimmed() == item.toString().trimmed():
                        if first:
                            QgsGeometry( inFeat.geometry() )
                            tmpInGeom = QgsGeometry( inFeat.geometry() )
                            outFeat.setGeometry( tmpInGeom )
                            first = False
                            attrs = inFeat.attributeMap()
                        else:
                            tmpInGeom = QgsGeometry( inFeat.geometry() )
                            tmpOutGeom = QgsGeometry( outFeat.geometry() )
                        try:
                            tmpOutGeom = QgsGeometry( tmpOutGeom.combine( tmpInGeom ) )
                            outFeat.setGeometry( tmpOutGeom )
                        except:
                            GEOS_EXCEPT = False
                            add = False
                if add:
                    outFeat.setAttributeMap( attrs )
                    writer.addFeature( outFeat )
        del writer
        if not GEOS_EXCEPT:
            SextanteLog.addToLog(SextanteLog.LOG_WARNING, "Geometry exception while dissolving")

    def defineCharacteristics(self):
        self.name = "Dissolve"
        self.group = "Vector geometry tools"
        self.addParameter(ParameterVector(Dissolve.INPUT, "Input layer", ParameterVector.VECTOR_TYPE_POLYGON))        
        self.addParameter(ParameterBoolean(Dissolve.DISSOLVE_ALL, "Dissolve all (do not use field)", True))
        self.addParameter(ParameterTableField(Dissolve.FIELD, "Unique ID field",Dissolve.INPUT ))
        self.addOutput(OutputVector(Dissolve.OUTPUT, "Dissolved"))

    #=========================================================
