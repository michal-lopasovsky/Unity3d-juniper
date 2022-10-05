####################################################################################################
## New temporary document is created as a clone of currently opened document.
## Each Layer Group is identified by the name [_METALNESS. _SMOOTHNESS, _ OCCLUSION, _EMISSION_MASK]
##    DETAIL MASK:
##      R - desaturate albedo
##      G - smoothness
##      B - none
##    MASK:
##      R - metalness
##      G - occlusion
##      B - detail
##      A - smoothness
## Based on this naming convention, each group is copied to a corresponding RGBA channel.
## Temporary document is saved, then exported and lastly removed from disk.
## Export is skipped if export path is left empty.
####################################################################################################
## File name: texture_exporter.py
## Created By: inloper@protonmail.com
## version: '1.0.1'
####################################################################################################

from json.tool import main
from PyQt5.QtWidgets import *
from PyQt5 import QtCore
from krita import *
import os

class TextureExporterDock(DockWidget):
    DEPOTROOT           = "D:\depots"
    DEPOT               = "juniper_game_dev"

    MASK_RED            = "_METALNESS"
    MASK_GREEN          = "_OCCLUSION"
    MASK_BLUE           = "_EMISSION_MASK"
    MASK_ALPHA          = "_SMOOTHNESS"

    LAYER_MASK_RED      = "_ALBEDO"
    LAYER_MASK_GREEN    = "_SMOOTHNESS"
    LAYER_MASK_BLUE     = "_NORMAL_DETAIL_MASK"

    LAYER_DIFFUSE       = "_DIFFUSE"
    LAYER_DIFFUSE_ALPHA = "_ALPHA"
    LAYER_BACKGROUND    = "_BACKGROUND"

    LAYER_DICT_GLOBAL   = {}
    KRITA_INSTANCE      = {}
    exportPathGlobal = ""
    tempFileToDeleteGlobal = ""
    actviveDocName = ""

    def __init__(self):
        super().__init__()
        mainWidget = QWidget(self)
        self.setWidget(mainWidget)

        hbox = QGridLayout()
        self.eLabel = QLabel(self)
        self.eLabel.setText("Export path:")
        self.eLabel.move(10, 20)

        self.exportPathBox = QLineEdit(self)

        self.pathButton = QPushButton('...', mainWidget)
        self.pathButton.clicked.connect(self.choose_path)

        # -------------------- EXPORT BUTTONS
        self.exportDiffuse = QPushButton("Export Diffuse")
        self.exportDiffuse.setStyleSheet("background-color : #e1a6f2;"
                                         "color: black;")
        self.exportDiffuse.clicked.connect(self.prepare_diffuse)

        self.exportMask = QPushButton("Export Mask")
        self.exportMask.setStyleSheet("background-color : #e1a6f2;"
                                         "color: black;")
        self.exportMask.clicked.connect(self.prepare_mask)

        self.exportDetailMask = QPushButton("Export Detail Mask")
        self.exportDetailMask.setStyleSheet("background-color : #e1a6f2;"
                                            "color: black;")
        self.exportDetailMask.clicked.connect(self.prepare_detail_mask)

        # -------------------- CREATE LAYERS BUTTONS
        self.createDiffuseLayers = QPushButton("Create Diffuse Layers")
        self.createDiffuseLayers.setStyleSheet("background-color : #8f867a;"
                                                "color: black;")
        self.createDiffuseLayers.clicked.connect(self.create_diffuse_layers)

        self.createMaskLayers = QPushButton("Create Mask Layers")
        self.createMaskLayers.setStyleSheet("background-color : #8f867a;"
                                            "color: black;")
        self.createMaskLayers.clicked.connect(self.create_mask_layers)

        self.createDetailMaskLayers = QPushButton("Create Detail Mask Layers")
        self.createDetailMaskLayers.setStyleSheet("background-color : #8f867a;"
                                                    "color: black;")
        self.createDetailMaskLayers.clicked.connect(self.create_detail_mask_layers)


        hbox.addWidget(self.eLabel)
        hbox.addWidget(self.exportPathBox, 0, 0)
        hbox.addWidget(self.pathButton, 0, 1)

        hbox.addWidget(self.exportDiffuse, 1, 0)
        hbox.addWidget(self.createDiffuseLayers, 1, 1)

        hbox.addWidget(self.exportMask, 2, 0)
        hbox.addWidget(self.createMaskLayers, 2, 1)

        hbox.addWidget(self.exportDetailMask, 3, 0)
        hbox.addWidget(self.createDetailMaskLayers, 3, 1)

        mainWidget.setLayout(hbox)
        self.setWindowTitle("Texture Exporter")

    def choose_path(self):
        exportPathValue = self.exportPathBox.text()
        if exportPathValue == '':
            exportPathValue = QFileDialog.getExistingDirectory(self, "Export directory", self.DEPOTROOT + "\\" + self.DEPOT + "\\Assets\\_Project\\maps\\")
            self.exportPathBox.setText(exportPathValue)
            self.exportPathGlobal = exportPathValue;

    def stepper_mask(self, i, clonedDoc):
        if i == 0:
            newNode = clonedDoc.createNode(str(self.LAYER_BACKGROUND), "paintlayer")
            newNode.setBlendingMode("normal")
            clonedDoc.rootNode().addChildNode(newNode, self.LAYER_DICT_GLOBAL["alpha"])
        if i == 1:
            self.set_foreground_color(clonedDoc, Application)
        if i == 2:
            clonedDoc.setActiveNode(self.LAYER_DICT_GLOBAL["alpha"])
            Application.action('convert_to_transparency_mask').trigger()
            clonedDoc.save()
        if i == 3:
            self.export_texture(clonedDoc, True)
        if i == 4:
            Application.activeDocument().close()
        if i == 5:
            if os.path.exists(self.tempFileToDeleteGlobal):
                os.remove(self.tempFileToDeleteGlobal)

        if i < 6: QtCore.QTimer.singleShot(100, lambda: self.stepper_mask(i+1, clonedDoc) )

    def stepper_detail_mask(self, i, clonedDoc):
        if i == 0:
            clonedDoc.save()
        if i == 1:
            self.export_texture(clonedDoc, False)
        if i == 2:
            Application.activeDocument().close()
        if i == 3:
            if os.path.exists(self.tempFileToDeleteGlobal):
                os.remove(self.tempFileToDeleteGlobal)
        if i < 4: QtCore.QTimer.singleShot(100, lambda: self.stepper_detail_mask(i+1, clonedDoc) )

    def stepper_diffuse(self, i, clonedDoc, alpha):
        temp_alpha = alpha
        if i == 0:
            if alpha == True:
                clonedDoc.setActiveNode(self.LAYER_DICT_GLOBAL["alpha"])
                Application.action('convert_to_transparency_mask').trigger()
            clonedDoc.save()
        if i == 1:
            self.export_texture(clonedDoc, alpha)
        if i == 2:
            Application.activeDocument().close()
        if i == 3:
            if os.path.exists(self.tempFileToDeleteGlobal):
                os.remove(self.tempFileToDeleteGlobal)
        if i < 4: QtCore.QTimer.singleShot(100, lambda: self.stepper_diffuse(i+1, clonedDoc, temp_alpha))

# -------------------- CREATE NEW LAYERS BASED ON THE TYPE - METHODS
    def create_mask_layers(self):
        self.set_default_paint_layer_color()
        groupArray = ["_METALNESS", "_OCCLUSION", "_EMISSION_MASK", "_SMOOTHNESS"]
        self.create_layers_based_on_type(groupArray)

    def create_detail_mask_layers(self):
        self.set_default_paint_layer_color()
        groupArray = ["_ALBEDO", "_SMOOTHNESS", "_NORMAL_DETAIL_MASK"]
        self.create_layers_based_on_type(groupArray)

    def create_diffuse_layers(self):
        self.set_default_paint_layer_color()
        groupArray = ["_DIFFUSE", "_ALPHA"]
        self.create_layers_based_on_type(groupArray)

# -------------------- PREPARE LAYER BEFORE EXPORT - METHODS
    def prepare_diffuse(self):
        self.tempFileToDeleteGlobal = ""

        Application.setBatchmode(True)
        doc = Application.activeDocument()
        doc.save()

        clonedDoc = doc.clone()
        Application.activeWindow().addView(clonedDoc)
        self.actviveDocName = str(doc.fileName())[:-4].strip()
        docTempName = self.actviveDocName + "_temp.kra"
        clonedDoc.setFileName(docTempName)

        self.tempFileToDeleteGlobal = clonedDoc.fileName()

        layerDict = self.create_diffuse_layer_dict(clonedDoc)
        self.LAYER_DICT_GLOBAL = layerDict

        if "alpha" in layerDict and layerDict["alpha"] is not None:
            self.stepper_diffuse(0, clonedDoc, True)
        else:
            self.stepper_diffuse(0, clonedDoc, False)

        Application.setBatchmode(False)

    def prepare_detail_mask(self):
        self.tempFileToDeleteGlobal = ""

        Application.setBatchmode(True)
        doc = Application.activeDocument()
        doc.save()

        clonedDoc = doc.clone()
        Application.activeWindow().addView(clonedDoc)
        self.actviveDocName = str(doc.fileName())[:-4].strip()
        docTempName = self.actviveDocName + "_temp.kra"
        clonedDoc.setFileName(docTempName)

        self.tempFileToDeleteGlobal = clonedDoc.fileName()

        layerDict = self.create_detail_mask_layer_dict(clonedDoc)
        self.LAYER_DICT_GLOBAL = layerDict

        if "red" in layerDict and layerDict["red"] is not None:
            layerDict["red"].setBlendingMode("copy_red")

        if "green" in layerDict and layerDict["green"] is not None:
            layerDict["green"].setBlendingMode("copy_green")

        if "blue" in layerDict and layerDict["blue"] is not None:
            layerDict["blue"].setBlendingMode("copy_blue")

        self.stepper_detail_mask(0, clonedDoc)

        Application.setBatchmode(False)

    def prepare_mask(self):
        self.tempFileToDeleteGlobal = ""

        Application.setBatchmode(True)
        doc = Application.activeDocument()
        doc.save()

        clonedDoc = doc.clone()
        Application.activeWindow().addView(clonedDoc)
        self.actviveDocName = str(doc.fileName())[:-4].strip()
        docTempName = self.actviveDocName + "_temp.kra"
        clonedDoc.setFileName(docTempName)

        self.tempFileToDeleteGlobal = clonedDoc.fileName()

        layerDict = self.create_mask_layer_dict(clonedDoc)
        self.LAYER_DICT_GLOBAL = layerDict

        if "red" in layerDict and layerDict["red"] is not None:
            layerDict["red"].setBlendingMode("copy_red")

        if "green" in layerDict and layerDict["green"] is not None:
            layerDict["green"].setBlendingMode("copy_green")

        if "blue" in layerDict and layerDict["blue"] is not None:
            layerDict["blue"].setBlendingMode("copy_blue")

        if "alpha" in layerDict and layerDict["alpha"] is not None:
            self.stepper_mask(0, clonedDoc)

        Application.setBatchmode(False)

# -------------------- EXPORT
    def export_texture(self, currentDocument, alpha):
        if len(str(self.exportPathGlobal)) != 0:
            exportParameters = InfoObject()
            exportParameters.setProperty("alpha", alpha)
            exportParameters.setProperty("compression", 1)
            exportParameters.setProperty("forceSRGB", False)
            exportParameters.setProperty("indexed", False)
            exportParameters.setProperty("interlaced", False)
            exportParameters.setProperty("saveSRGBProfile", False)
            currentDocument.exportImage(self.exportPathGlobal + '/' + self.actviveDocName.split('/')[-1].strip() + '.tga', exportParameters )

    def create_mask_layer_dict(self, doc):
        layerDict = {}
        for node in doc.topLevelNodes():
            if self.MASK_RED in node.name():
                layerDict["red"] = node
            if self.MASK_GREEN in node.name():
                layerDict["green"] = node
            if self.MASK_BLUE in node.name():
                layerDict["blue"] = node
            if self.MASK_ALPHA in node.name():
                layerDict["alpha"] = node
        return layerDict

    def create_detail_mask_layer_dict(self, doc):
        layerDict = {}
        for node in doc.topLevelNodes():
            if self.LAYER_MASK_RED in node.name():
                layerDict["red"] = node
            if self.LAYER_MASK_GREEN in node.name():
                layerDict["green"] = node
            if self.LAYER_MASK_BLUE in node.name():
                layerDict["blue"] = node
        return layerDict

    def create_diffuse_layer_dict(self, doc):
        layerDict = {}
        for node in doc.topLevelNodes():
            if self.LAYER_DIFFUSE_ALPHA in node.name():
                layerDict["alpha"] = node
        return layerDict


    def set_foreground_color(self, doc, app):
        activeView = app.activeWindow().activeView()
        # QMessageBox.information(QWidget(), "Debug", " |test| " + str(activeView))
        bgNode = doc.nodeByName(self.LAYER_BACKGROUND)
        doc.setActiveNode(bgNode)

        colorBlack = ManagedColor("RGBA", "U8", "")
        colorComponents = colorBlack.components()
        colorComponents[0] = 0.0
        colorComponents[1] = 0.0
        colorComponents[2] = 0.0
        colorComponents[3] = 1.0
        colorBlack.setComponents(colorComponents)

        activeView.setForeGroundColor(colorBlack)
        app.action('fill_selection_foreground_color').trigger()
        doc.refreshProjection()
        # doc.waitForDone()

    def setup_texture_info():
        exportParameters = InfoObject()
        exportParameters.setProperty("alpha", True)

    def canvasChanged(self, canvas):
        pass


# -------------------- UTILITIES
    def set_default_paint_layer_color(self):
        bgColor = ManagedColor("RGBA", "U8", "")
        colorComponents = bgColor.components()
        colorComponents[0] = 0.0  # R
        colorComponents[1] = 0.0  # G
        colorComponents[2] = 0.0  # B
        colorComponents[3] = 1.0  # A
        bgColor.setComponents(colorComponents)
        Application.activeWindow().activeView().setForeGroundColor(bgColor)

    def create_layers_based_on_type(self, groupArray):
        # TODO: add check if any document is opened
        Application.setBatchmode(True)
        doc = Application.activeDocument()
        root = doc.rootNode()

        for group in groupArray:
            group = doc.createNode(group, "groupLayer")
            root.addChildNode(group, None)
            new_layer = doc.createNode("empty", "paintLayer")
            group.addChildNode(new_layer, None)
            doc.setActiveNode(new_layer)
            Application.action('fill_selection_foreground_color').trigger()

        doc.refreshProjection()


Application.addDockWidgetFactory(DockWidgetFactory("textureExporter", DockWidgetFactoryBase.DockRight, TextureExporterDock))