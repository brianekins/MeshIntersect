#Author-Brian Ekins
#Description-Creates sketch geometry that is the intersection of selected mesh bodies and the x-y plane of the active sketch.
# (C) Copyright 2016 by Autodesk, Inc.
# Permission to use, copy, modify, and distribute this software in object code form 
# for any purpose and without fee is hereby granted, provided that the above copyright 
# notice appears in all copies and that both that copyright notice and the limited  
# warrantyand restricted rights notice below appear in all supporting documentation.

# AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS. AUTODESK SPECIFICALLY 
# DISCLAIMS ANY IMPLIED WARRANTY OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE. 
# AUTODESK, INC. DOES NOT WARRANT THAT THE OPERATION OF THE PROGRAM WILL BE 
# UNINTERRUPTED OR ERROR FREE.


import adsk.core, adsk.fusion, traceback
import math

handlers = []

# Globals variables.
_des = adsk.fusion.Design.cast(None)
_activeSketch = adsk.fusion.Sketch.cast(None)
_meshSelectInput = adsk.core.SelectionCommandInput.cast(None)
_planeSelectInput = adsk.core.SelectionCommandInput.cast(None)
_distanceTypeInput = adsk.core.DropDownCommandInput.cast(None)
_planeCountInput = adsk.core.IntegerSpinnerCommandInput.cast(None)
_distanceInput = adsk.core.DistanceValueCommandInput.cast(None)
_resultInput = adsk.core.DropDownCommandInput.cast(None)
_boolLineInput = adsk.core.BoolValueCommandInput.cast(None)
_boolArcInput = adsk.core.BoolValueCommandInput.cast(None)
_meshState = []
_pointTol = 0.000001




def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        # Get the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions
        
        # Create a button command definition.
        meshIntersectButton = cmdDefs.addButtonDefinition('meshIntersect', 'Intersect Mesh Body', 
                                                          'Intersect mesh body through sketch x-y plane.',
                                                          './/Resources//MeshIntersect')
        
        # Connect to the command created event.
        meshIntersectCommandCreated = MeshIntersectCommandCreatedEventHandler()
        meshIntersectButton.commandCreated.add(meshIntersectCommandCreated)
        handlers.append(meshIntersectCommandCreated)

        # Get the SKETCH toolbar panel. 
        sketchPanel = ui.allToolbarPanels.itemById('SketchPanel')
        
        # Get the "Project/Include" drop-down.  
        projDropDown = sketchPanel.controls.itemById('ProjectIncludeDropDown')
        
        # Add the mesh body section command below the Intersect command.
        projDropDown.controls.addCommand(meshIntersectButton, 'IntersectCmd', True)
    except:
        if ui:
            ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
            #ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        # Remove the UI.
        # Get the SKETCH toolbar panel. 
        sketchPanel = ui.allToolbarPanels.itemById('SketchPanel')
        
        # Get the "Project/Include" drop-down.  
        projDropDown = sketchPanel.controls.itemById('ProjectIncludeDropDown')
        
        # Get the meshIntersect control.
        meshCntrl = projDropDown.controls.itemById('meshIntersect')
        if meshCntrl:
            meshCntrl.deleteMe()
        
        meshInterectCommandDef = ui.commandDefinitions.itemById('meshIntersect')
        if meshInterectCommandDef:
            meshInterectCommandDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Unexpected failure removing command.', 'Intersect Mesh Body')
            #ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler for inputChanged event.
class InputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            # Get the inputs.
            inputChangedEventArgs = adsk.core.InputChangedEventArgs.cast(args)
            allInputs = adsk.core.CommandInputs.cast(inputChangedEventArgs.firingEvent.sender.commandInputs)
            changedInput = inputChangedEventArgs.input
    
            # If sketch is active:
            #   1. The sketch X-Y plane is used as the intersection plane.
            #   2. Only a single intersection is supported.
            #   3. The result will be in the active sketch.
            # If no sketch is active.
            #   1. One or more construction planes and/or planar faces can be selected.
            #       A. If one plane is selected then additional offset planes can optionally be defined as offsets of the original plane.
            #       B. If more than one plane is selected then an intersection is created using each plane.
            #   2. The resulting geometry can be created:
            #      a. specified sketch
            #      b. All in one new sketch
            #      c. Each in a new sketch.
    
            # Set the state of the dialog correctly depending on the dialog settings.
            if not _activeSketch:
                if _meshSelectInput.selectionCount > 0 and _planeSelectInput.selectionCount == 1:
                    # There is a single intersection plane selected so support offset planes.
                    _distanceTypeInput.isVisible = True
                    _distanceInput.isVisible = True
                    #_resultInput.isVisible = True
                    _boolLineInput.isVisible = True
                    _planeCountInput.isVisible = True
                    #_boolArcInput.isVisible = True
                   
                    planeEnt = _planeSelectInput.selection(0).entity
                    planeGeom = adsk.core.Plane.cast(planeEnt.geometry)
                    _distanceInput.setManipulator(planeGeom.origin, planeGeom.normal)

                    # If the distance value has been defined switch which plane count input
                    # is displayed.  This is a workaround because of the inability to set the
                    # value to 0                    
                    if math.fabs(_distanceInput.value) < 0.0000001:
                        _planeCountInput.value = 1
                    else:
                        if _planeCountInput.value == 1:
                            _planeCountInput.value = 2
                    
                    if changedInput.id == 'planeCount':
                        if _planeCountInput.value == 1:
                            _distanceInput.value = 0
                elif _meshSelectInput.selectionCount > 0 and _planeSelectInput.selectionCount > 1:
                    # There are multiple intersection planes selected so don't support offset planes.
                    _distanceTypeInput.isVisible = False
                    _planeCountInput.isVisible = False
                    _distanceInput.isVisible = False
                    #_resultInput.isVisible = True
                    _boolLineInput.isVisible = True
                    #_boolArcInput.isVisible = True
                else:
                    # There are no planes selected so don't show the offset plane options.
                    _distanceTypeInput.isVisible = False
                    _planeCountInput.isVisible = False
                    _distanceInput.isVisible = False
                    #_resultInput.isVisible = False
                    _boolLineInput.isVisible = False
                    #_boolArcInput.isVisible = False
            else:
                if _meshSelectInput.selectionCount > 0:
                    _boolLineInput.isVisible = True
                    #_boolArcInput.isVisible = True
                else:
                    _boolLineInput.isVisible = False
                    _boolArcInput.isVisible = False
                    
            if changedInput.id == 'optimizeArcs' and changedInput.value == True:
                allInputs.itemById('optimizeLines').value = True
            elif changedInput.id == 'optimizeLines' and changedInput.value == False:
                allInputs.itemById('optimizeArcs').value = False
                
        except:
            if ui:
                #ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
                ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))
                
        
# Event handler for executePreview event.
class ExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            if not _activeSketch:
                # Check that there is a single intersection plane.
                if _planeSelectInput.selectionCount == 1:
                    # Only show the preview if bodies have been selected.
                    if _meshSelectInput.selectionCount > 0:
                        distance = _distanceInput.value    
                        count = _planeCountInput.value
                            
                        planeEnt = _planeSelectInput.selection(0).entity
                        if _distanceTypeInput.selectedItem.name == 'Spacing':
                            distance = _distanceInput.value
                        elif _distanceTypeInput.selectedItem.name == 'Total Extent':
                            if count == 1:
                                distance = 0
                            else:
                                distance = _distanceInput.value / (count-1)
                            
                        if math.fabs(distance) > 0.000001:
                            # Create construction planes for the preview.
                            app = adsk.core.Application.get()
                            des = adsk.fusion.Design.cast(app.activeProduct)
                            constPlanes = des.rootComponent.constructionPlanes
    
                            for i in range(1, count):
                                constPlaneInput = constPlanes.createInput()
                                constPlaneInput.setByOffset(planeEnt, adsk.core.ValueInput.createByReal(distance * i))
                                constPlane = constPlanes.add(constPlaneInput)                               
        except:
            if ui:
                #ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
                ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))


class MeshIntersectCommandExecutedEventHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        try:
            command = args.firingEvent.sender
            cmdInputs = adsk.core.CommandInputs.cast(command.commandInputs)
            meshBodies = []

            app = adsk.core.Application.get()
            des = adsk.fusion.Design.cast(app.activeProduct)

            # Get the inputs that are used for both sketches and planes.
            for i in range(0, _meshSelectInput.selectionCount):
                meshSelection = _meshSelectInput.selection(i)
                meshBodies.append(meshSelection.entity)

            boolInput = adsk.core.BoolValueCommandInput.cast(cmdInputs.itemById('optimizeLines'))                
            optimizeLines = boolInput.value

            boolInput = adsk.core.BoolValueCommandInput.cast(cmdInputs.itemById('optimizeArcs'))                
            optimizeArcs = boolInput.value
            
            progDialog = ui.createProgressDialog()
            progDialog.isCancelButtonShown = False
            progDialog.show('Intersection Progress', 'Calculating intersections', 0, 100)
            progDialog.progressValue = 0

            # Create the sections through the active sketch's x-y plane.
            if _activeSketch:
                # Process each selected mesh body.
                sectionCount = 1
                for meshBody in meshBodies:
                    if not progDialog.wasCancelled:
                        loops = calculateIntersection(meshBody, _activeSketch, True, optimizeLines, optimizeArcs)
                        if loops != None:
                            drawLoops(_activeSketch, loops)
                            
                        progDialog.progressValue = int((sectionCount / len(meshBodies)) * 100)
                        sectionCount += 1
            else:
                # Check that there is a single intersection plane.
                intPlanes = []
                firstItem = None
                lastItem = None
                if _planeSelectInput.selectionCount == 1:
                    # Construct all of the needed construction planes.
                    distance = _distanceInput.value    
                    count = _planeCountInput.value
                        
                    planeEnt = _planeSelectInput.selection(0).entity
                    intPlanes.append(planeEnt)
                    if _distanceTypeInput.selectedItem.name == 'Spacing':
                        distance = _distanceInput.value
                    elif _distanceTypeInput.selectedItem.name == 'Total Extent':
                        if count == 1:
                            distance = 0
                        else:
                            distance = _distanceInput.value / (count-1)
                        
                    if math.fabs(distance) > 0.000001:
                        # Create construction planes for the preview.
                        constPlanes = des.rootComponent.constructionPlanes

                        for i in range(1, count):
                            constPlaneInput = constPlanes.createInput()
                            constPlaneInput.setByOffset(planeEnt, adsk.core.ValueInput.createByReal(distance * i))
                            constPlane = constPlanes.add(constPlaneInput)
                            intPlanes.append(constPlane)
                            if not firstItem:
                                firstItem = constPlane.timelineObject
                else:
                    for i in range(0, _planeSelectInput.selectionCount):
                        intPlanes.append(_planeSelectInput.selection(i).entity)

                root = des.rootComponent
                sectionCount = 1
                totalCuts = len(intPlanes) * len(meshBodies)
                cutCount = 0
                for intPlane in intPlanes:
                    if _resultInput.selectedItem.name == 'Each section in new sketch':
                        newSketch = root.sketches.add(intPlane)
                        if not firstItem:
                            firstItem = newSketch.timelineObject
                            
                        lastItem = newSketch.timelineObject

                        bodyCount = 1
                        for meshBody in meshBodies:
                            if not progDialog.wasCancelled:
                                loops = calculateIntersection(meshBody, newSketch, True, optimizeLines, optimizeArcs)
                                if loops != None:
                                    drawLoops(newSketch, loops)
                             
                                cutCount += 1
                                progDialog.progressValue = int((cutCount / totalCuts) * 100)
                                bodyCount += 1 
                        sectionCount += 1

                if firstItem and lastItem:
                    if firstItem != lastItem:
                        tlGroup = des.timeline.timelineGroups.add(firstItem.index, lastItem.index)
                        tlGroup.name = 'Mesh Intersection Result'
                        
            progDialog.hide()
        except:
            if ui:
                if progDialog:
                    progDialog.hide()
                ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
                ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))


# Event handler for activate event.
class CommandActivatedHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        global _meshState
        _meshState.clear
        for comp in _des.allComponents:
            for mesh in comp.meshBodies:
                _meshState.append([mesh, mesh.isSelectable])
                if mesh.isSelectable == False:
                    mesh.isSelectable = True
        

class MeshIntersectCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__() 
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface

            # Check that a design is active.
            global _des
            _des = app.activeProduct
            if not _des:
                ui.messageBox('A design must be active.')
                return
                
            # Check to see if a sketch is active and get it.
            if app.activeEditObject.objectType == adsk.fusion.Sketch.classType():
                sk = app.activeEditObject
                global _activeSketch
                _activeSketch = adsk.fusion.Sketch.cast(sk)

            cmd = adsk.core.Command.cast(args.command)
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs

            onActivate = CommandActivatedHandler()
            cmd.activate.add(onActivate)
            handlers.append(onActivate)
         
            # Connect to the command executed event.
            commandExecuted = MeshIntersectCommandExecutedEventHandler()
            cmd.execute.add(commandExecuted)
            handlers.append(commandExecuted)
            
            # Connect to the input changed event.
            inputChanged = InputChangedHandler()
            cmd.inputChanged.add(inputChanged)
            handlers.append(inputChanged)
            
            # Connect to the validate inputs event.            
#            validateInputs = ValidateInputsHandler()
#            cmd.validateInputs.add(validateInputs)
#            handlers.append(validateInputs)
            
            # Connect to the execute preview event.
            onExecutePreview = ExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            handlers.append(onExecutePreview)            

            # Create the input for selecting the mesh bodies.
            global _meshSelectInput
            _meshSelectInput = inputs.addSelectionInput('meshSelect', 'Mesh Bodies', 'Select mesh bodies to section.')
            _meshSelectInput.addSelectionFilter('MeshBodies')
            _meshSelectInput.setSelectionLimits(1, 0)

            # Create the input for selecting the intersection planes.
            global _planeSelectInput
            _planeSelectInput = inputs.addSelectionInput('planeSelect', 'Intersection Planes', 'Select  planar faces and construction planes.')            
            _planeSelectInput.addSelectionFilter('PlanarFaces')
            _planeSelectInput.addSelectionFilter('ConstructionPlanes')
            _planeSelectInput.setSelectionLimits(1, 0)
            if _activeSketch:
                _planeSelectInput.isVisible = False

            # Create the input to get the distance type.  This is only used once the quantity is greater than 1.
            global _distanceTypeInput
            _distanceTypeInput = inputs.addDropDownCommandInput('distanceType', 'Distance Type', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            _distanceTypeInput.listItems.add('Total Extent', True, 'Resources/extent')
            _distanceTypeInput.listItems.add('Spacing', False, 'Resources/spacing')
            _distanceTypeInput.isVisible = False

            # Create the input to get the number of offset planes.  This number includes the original selected plane
            # so a value of 1 will create a single intersection with the selected plane.
            global _planeCountInput
            _planeCountInput = inputs.addIntegerSpinnerCommandInput('planeCount', 'Quantity', 1, 10000, 1, 1)
            _planeCountInput.isVisible = False
                                   
            # Create the input to get the distance value.  The default is 0 of the current active length unit.
            global _distanceInput
            _distanceInput = inputs.addDistanceValueCommandInput('distance', 'Distance', adsk.core.ValueInput.createByString('0'))
            _distanceInput.isVisible = False

            # Create the input to get the results location.
            global _resultInput
            _resultInput = inputs.addDropDownCommandInput('results', 'Results', adsk.core.DropDownStyles.LabeledIconDropDownStyle)
            _resultInput.listItems.add('All sections in new sketch', False, '')
            _resultInput.listItems.add('Each section in new sketch', True, '')
            _resultInput.isVisible = False
            
            # Create the check box input to determine if multiple colinear lines should be replaced with a single line.
            global _boolLineInput
            _boolLineInput = inputs.addBoolValueInput('optimizeLines', 'Combine colinear lines', True, '', True) 
            _boolLineInput.isVisible = False
            
            # Create the check box input to determine if an arc should replace multiple lines that fit through a common arc.
            global _boolArcInput
            _boolArcInput = inputs.addBoolValueInput('optimizeArcs', 'Fit Arcs', True, '', False)            
            _boolArcInput.isVisible = False

#            msg = '<div align="center">By default, mesh bodies are not selectable in the graphics window. However, they are selectable in the browser.</div>'
#            txtBox = inputs.addTextBoxCommandInput('message', '', msg, 5, True)
#            txtBox.isFullWidth = True            
        except:
            if ui:
                #ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   


def dumpLoops(loops):
    f = open('C:/Temp/LoopDump.txt','w')

    loopCnt = 0
    for loop in loops:
        loopCnt += 1
        f.write('Loop ' + str(loopCnt) + ', isClosed: ' + str(loop.isClosed) + '\n')
        
        pointCnt = 0
        for point in loop.points:
            if point.pointType == PointType.lineStart:
                pntType = 'lineStart'
            elif point.pointType == PointType.lineEnd:
                pntType = 'lineEnd'
            elif point.pointType == PointType.lineStartAndEnd:
                pntType = 'lineStartAndEnd'
            elif point.pointType == PointType.arcMid:
                pntType = 'arcMid'
            elif point.pointType == PointType.unknown:
                pntType = 'unknown'
                
            f.write('    ' + str(pointCnt) + '. ' + pntType + ', ' + str(point.x) + ', ' + str(point.y) + ', ' + str(point.z) + '\n' )
            pointCnt += 1

    f.close()

def drawLoops(sketch, loops):
    sketch.isComputeDeferred = True
    lines = sketch.sketchCurves.sketchLines
    arcs = adsk.fusion.SketchArcs.cast(sketch.sketchCurves.sketchArcs)
    for loop in loops:
        lastPoint = None
        firstPoint = None
        arcStartPoint = None
        arcMidPoint = None
        isArc = False
        if loop.isConnected:
            isFirstPoint = True
            for point in loop.points:
                if isFirstPoint == True:
                    lastPoint = adsk.core.Point3D.create(point.x, point.y, point.z)
                    isFirstPoint = False
                else:
                    # Check to see if the next item in the list is a Point3D or not.
                    # If it is then a line is defined.  If it's not, then an arc is defined.
                    if point.pointType != PointType.arcMid and not isArc:                           
                        newLine = lines.addByTwoPoints(lastPoint, adsk.core.Point3D.create(point.x, point.y, point.z))
                        lastPoint = newLine.endSketchPoint
                        
                        if not firstPoint:
                            # Save this point to be able to connect the end together.
                            firstPoint = newLine.startSketchPoint
                    elif point.pointType == PointType.arcMid or isArc:
                        if not arcStartPoint and not arcMidPoint:
                            arcStartPoint = lastPoint
                            arcMidPoint = point
                            isArc = True
                        elif arcStartPoint and arcMidPoint:
                            newArc = arcs.addByThreePoints(arcStartPoint, asFusionPoint(arcMidPoint), asFusionPoint(point))
                            
                            if asFusionPoint(point).isEqualTo(newArc.endSketchPoint.geometry):                                
                                lastPoint = newArc.endSketchPoint
                                
                                if not firstPoint:
                                    firstPoint = newArc.startSketchPoint
                            else:
                                lastPoint = newArc.startSketchPoint
                                
                                if not firstPoint:
                                    firstPoint = newArc.endSketchPoint
                                    
                            arcStartPoint = None
                            arcMidPoint = None
                            isArc = False
            if loop.isClosed:
                if arcMidPoint:
                    newArc = arcs.addByThreePoints(lastPoint, asFusionPoint(arcMidPoint), firstPoint)
                else:
                    newLine = lines.addByTwoPoints(lastPoint, firstPoint)
        else:
            for i in range(0, int(len(loop.points)/2)-1):
                pnt1 = loop.points[i*2]
                pnt2 = loop.points[i*2+1]
                lines.addByTwoPoints(adsk.core.Point3D.create(pnt1.x, pnt1.y, pnt1.z),
                                     adsk.core.Point3D.create(pnt2.x, pnt2.y, pnt2.z))               
                                    
    sketch.isComputeDeferred = False


def asFusionPoint(myPoint):
    return adsk.core.Point3D.create(myPoint.x, myPoint.y, myPoint.z)


def pntFromArray(array, index):
    return [array[index*3], array[index*3+1], array[index*3+2]]


def transformPointArray(coords, matrix):
    # Create a copy of the array.
    newCoords = list(coords)
    
    # Transform each of the points.
    for i in range(0, int(len(newCoords)/3)):
        # Load the point coordinates into an array.
        pnt = MyPoint(newCoords[i*3], newCoords[i*3+1], newCoords[i*3+2])

        # Mulitply the point by the matrix.
        pnt.transformBy(matrix)

        # Save the results back into the original array.
        newCoords[i*3] = pnt.x
        newCoords[i*3+1] = pnt.y
        newCoords[i*3+2] = pnt.z

    return newCoords


def getCoordinate(coordIndex, vertices):
    x = vertices[coordIndex * 3]
    y = vertices[coordIndex * 3 + 1]
    z = vertices[coordIndex * 3 + 2]

    coordinate = [x, y, z]

    return coordinate



# Returns loops of coordinates.
def calculateIntersection(mesh, sketch, connectLoops, optimizeLines, optimizeArcs):
    intersectionLines = []
    
    # Get the triangular mesh from the body.
    triangleMesh = mesh.displayMesh
    
    # Get the coordinate data from the mesh.
    nodeCoords = triangleMesh.nodeCoordinatesAsDouble
    nodeIndices = triangleMesh.nodeIndices
    
    # Build up the transform to transform the points so the
    # position of the sketch plane will be the x-y model plane.
    tempSketchToWorld = sketch.transform
    tempSketchToWorld.invert()
    
    # Create a MyMatrix object.
    sketchToWorld = MyMatrix()
    sketchToWorld.setWithArray(tempSketchToWorld.asArray())

    # Transform the points so the intersection plane is the x-y model plane.        
    transCoords = transformPointArray(nodeCoords, sketchToWorld)

    # Iterate through the triangles to identify which ones overlap the x-y plane.
    intCount = 0
    for i in range(0, int(len(nodeIndices)/3)):
        # Get the three coordinates of the current triangle.      
        point1 = getCoordinate(nodeIndices[i*3], transCoords)
        point2 = getCoordinate(nodeIndices[i*3+1], transCoords)
        point3 = getCoordinate(nodeIndices[i*3+2], transCoords)

        isAboveZ = False
        isBelowZ = False

        if point1[2] >= 0 or point2[2] >= 0 or point3[2] >= 0:
            isAboveZ = True

        if point1[2] < 0 or point2[2] < 0 or point3[2] < 0:
            isBelowZ = True

        # Check to see if the triangle intersects the plane.
        if isAboveZ and isBelowZ:
            # This triangle overlaps the input plane, increase the intersection count.
            intCount += 1

            # Get the two points that are on one side and the single point on the other side.
            sideOnePoint1 = []
            sideOnePoint2 = []
            sideTwoPoint = []
            if point1[2] >= 0 and point2[2] >= 0:
                sideOnePoint1 = MyPoint(point1[0], point1[1], point1[2])
                sideOnePoint2 = MyPoint(point2[0], point2[1], point2[2])
                sideTwoPoint = MyPoint(point3[0], point3[1], point3[2])
            elif point1[2] >= 0 and point3[2] >= 0:
                sideOnePoint1 = MyPoint(point1[0], point1[1], point1[2])
                sideOnePoint2 = MyPoint(point3[0], point3[1], point3[2])
                sideTwoPoint = MyPoint(point2[0], point2[1], point2[2])
            elif point2[2] >= 0 and point3[2] >= 0:
                sideOnePoint1 = MyPoint(point2[0], point2[1], point2[2])
                sideOnePoint2 = MyPoint(point3[0], point3[1], point3[2])
                sideTwoPoint = MyPoint(point1[0], point1[1], point1[2])
            elif point1[2] < 0 and point2[2] < 0:
                sideOnePoint1 = MyPoint(point1[0], point1[1], point1[2])
                sideOnePoint2 = MyPoint(point2[0], point2[1], point2[2])
                sideTwoPoint = MyPoint(point3[0], point3[1], point3[2])
            elif point1[2] < 0 and point3[2] < 0:
                sideOnePoint1 = MyPoint(point1[0], point1[1], point1[2])
                sideOnePoint2 = MyPoint(point3[0], point3[1], point3[2])
                sideTwoPoint = MyPoint(point2[0], point2[1], point2[2])
            elif point2[2] < 0 and point3[2] < 0:
                sideOnePoint1 = MyPoint(point2[0], point2[1], point2[2])
                sideOnePoint2 = MyPoint(point3[0], point3[1], point3[2])
                sideTwoPoint = MyPoint(point1[0], point1[1], point1[2])

            # Create the two lines that represent sides of the triangle that overlap the plane.
            lineSeg1 = MyLine(sideOnePoint1, sideTwoPoint)
            lineSeg2 = MyLine(sideOnePoint2, sideTwoPoint)
            
            # Intersect the lines with the X-Y plane.
            intResult1 = lineSeg1.intersectWithXYPlane()
            intResult2 = lineSeg2.intersectWithXYPlane()
            
            # Skip any zero length segments.
            if intResult1.distanceTo(intResult2) > 0.000001:
                intersectionLines.append(MyLine(intResult1, intResult2))

    if len(intersectionLines) == 0:
        return None
    elif connectLoops:
        # Process the lines so they're in a nice connected order and grouped
        # by loops.
        intersectionLoops = createSectionLoops(intersectionLines, optimizeLines, optimizeArcs)
    else:
        loop = SectionLoop()
        loop.isConnected = False
        
        for line in intersectionLines:
            loop.addPoint(line.startPoint, True)
            loop.addPoint(line.endPoint, True)
        
        intersectionLoops = []
        intersectionLoops.append(loop)
        
    return intersectionLoops



# Given a list of lines that represent the intersection this cleans them up so they're
# in head-to-tail connected loops.  It returns a list of sectionLoop objects.
def createSectionLoops(intersectionLines, optimizeLines, optimizeArcs):
    # Initialize the list that will contain the section loops.
    sectionLoops = []
    
    currentLoop = SectionLoop()

    # Initialize the loop with the points from the first line.
    currentLoop.addPoint(intersectionLines[0].startPoint, True)
    currentLoop.addPoint(intersectionLines[0].endPoint, True)
    
    # Set this line to Empty indicating it's been processed.
    intersectionLines[0] = None
    
    # Begin processing the lines.
    for i in range(0, len(intersectionLines)):
        foundPoint = False
        for j in range(1, len(intersectionLines)):
            currentLine = intersectionLines[j]
            newPoint = None
            isAtEnd = True

            if i != j and currentLine != None:
                # Check to see if the end points of the current line match the check line.
                if currentLine.startPoint.isEqualTo(currentLoop.startPoint):
                    newPoint = currentLine.endPoint
                    isAtEnd = False
                    intersectionLines[j] = None
                elif currentLine.startPoint.isEqualTo(currentLoop.endPoint):
                    newPoint = currentLine.endPoint
                    isAtEnd = True
                    intersectionLines[j] = None
                elif currentLine.endPoint.isEqualTo(currentLoop.startPoint):
                    newPoint = currentLine.startPoint
                    isAtEnd = False
                    intersectionLines[j] = None
                elif currentLine.endPoint.isEqualTo(currentLoop.endPoint):
                    newPoint = currentLine.startPoint
                    isAtEnd = True
                    intersectionLines[j] = None

                # If a point was found, check to see if this point closes the loop.
                if newPoint != None:
                    foundPoint = True

                    if (isAtEnd and newPoint.isEqualTo(currentLoop.startPoint)) or (not isAtEnd and newPoint.isEqualTo(currentLoop.endPoint)):
                        currentLoop.isClosed = True

                        # Clean this loop of colinear lines.
                        if optimizeLines:
                            currentLoop.optimizeLines()
                            
                            if optimizeArcs:
                                currentLoop.optimizeArcs()
                            
                        # Save this loop and start a new loop.
                        sectionLoops.append(currentLoop)
                        currentLoop = SectionLoop()

                        # Find the next unused line and use it to start the next loop.
                        for k in range(0, len(intersectionLines)):
                            if intersectionLines[k] != None:
                                # Add the two points to the end of the loop.
                                currentLoop.addPoint(intersectionLines[k].startPoint, True)
                                currentLoop.addPoint(intersectionLines[k].endPoint, True)
                                intersectionLines[k] = None
                                break
                    else:
                        # Check that the new point is far enough away from the previous point for a line to be valid.
                        if isAtEnd:
                            if newPoint.distanceTo(currentLoop.endPoint) > 0.000001:
                                # Add the point to the end of the loop.
                                currentLoop.addPoint(newPoint, True)
                        elif not isAtEnd:
                            if newPoint.distanceTo(currentLoop.startPoint) > 0.000001:
                                # Add the point to the start of the loop.
                                currentLoop.addPoint(newPoint, False)

                    break

        noMoreLines = False
        if not foundPoint:
            if currentLoop.pointCount() > 0:
                # Clean this loop of colinear lines.
                if optimizeLines:
                    currentLoop.optimizeLines()
                    
                    if optimizeArcs:
                        currentLoop.optimizeArcs()

                # Save this loop and start a new loop.
                sectionLoops.append(currentLoop)

            noMoreLines = True
            currentLoop = SectionLoop()
            for k in range(0, len(intersectionLines)):
                if intersectionLines[k] != None:
                    noMoreLines = False

                    # Add the two points to the end of the loop.
                    currentLoop.addPoint(intersectionLines[k].startPoint, True)
                    currentLoop.addPoint(intersectionLines[k].endPoint, True)
                    intersectionLines[k] = None
                    break

        if noMoreLines:
            break

    # Save the current loop.
    if currentLoop.pointCount() > 0:
        # Clean this loop of colinear lines.
        if optimizeLines:
            currentLoop.optimizeLines()

        if optimizeArcs:
            currentLoop.optimizeArcs()
            
        # Add this loop to the collection.
        sectionLoops.append(currentLoop)
            
    return sectionLoops


class MyLine:
    def __init__(self, start, end):
        self.startPoint = start
        self.endPoint = end

    def asString(self):
            return '(' + str(self.startPoint.x) + ', ' + str(self.startPoint.y) + ', ' + str(self.startPoint.z) + ')-(' + str(self.endPoint.x) + ', ' + str(self.endPoint.y) + ', ' + str(self.endPoint.z) + ')'
            
    # Multiply the point by the matrix.
    def transformBy(self, matrix):
        try:
            self.start.transformBy(matrix)
            self.end.transformBy(matrix)
        except:
            raise ArithmeticError('Point transform failed.')

    def intersectWithLine(self, otherLine):
        a = [self.endPoint.x - self.startPoint.x, self.endPoint.y - self.startPoint.y]
        b = [otherLine.startPoint.x - otherLine.endPoint.x, otherLine.startPoint.y - otherLine.endPoint.y]
        c = [self.startPoint.x - otherLine.startPoint.x, self.startPoint.y - otherLine.startPoint.y]
        
        # Compute alpha
        denominator = (a[1] * b[0]) - (a[0] * b[1])
        if denominator == 0:
            return None

        numerator = (b[1] * c[0]) - (b[0] * c[1])
        alpha = numerator / denominator

        dX = self.startPoint.x + (alpha * (self.endPoint.x - self.startPoint.x))
        dY = self.startPoint.y + (alpha * (self.endPoint.y - self.startPoint.y))
        return MyPoint(dX, dY, 0)
        
        
    # Calculate the intersection point of the line and the x-y plane
    # This assumes the line does intersect, which in this case
    # has already been validated.
    def intersectWithXYPlane(self):
        # Get the length of the line the Z direction.
        zLength = abs(self.startPoint.z) + abs(self.endPoint.z)     
    
        # Compute the length factor of the start point to the z plane.
        factor = abs(self.startPoint.z) / zLength
    
        # Create a vector along the line and scale it by the factor.    
        lineVec = self.startPoint.vectorTo(self.endPoint)
        lineVec.scaleBy(factor)
        
        # Move the line start point along the vector the scaled distance
        # and that will be the intersection point.
        intPoint = self.startPoint.copy()
        intPoint.translateBy(lineVec)
        
        return intPoint
                       

class MyCircle:
    # Create a circle through three points.
    def __init__(self, startPoint, midPoint, endPoint):
        try:
            # Create two perpendiculars for the intersection.
            x = (startPoint.x + midPoint.x) / 2
            y = (startPoint.y + midPoint.y) / 2
            sideMid = MyPoint(x, y, 0)
    
            angle = startPoint.bearingTo(midPoint) + (math.pi / 2)
            x = x + math.cos(angle)
            y = y + math.sin(angle)
            perpPoint = MyPoint(x, y, 0)
            perpLine1 = MyLine(sideMid, perpPoint)
    
            x = (endPoint.x + midPoint.x) / 2
            y = (endPoint.y + midPoint.y) / 2
            sideMid = MyPoint(x, y, 0)
    
            angle = midPoint.bearingTo(endPoint) + (math.pi / 2)
            x = x + math.cos(angle)
            y = y + math.sin(angle)
            perpPoint = MyPoint(x, y, 0)
            perpLine2 = MyLine(sideMid, perpPoint)
    
            # Compute the center of the circle.
            self.center = perpLine1.intersectWithLine(perpLine2)
            if not self.center:
                return None
    
            # Compute the radius of the circle.
            self.radius = startPoint.distanceTo(self.center)
        except:
            return None

    def asString(self):
            return '(' + str(self.center.x) + ', ' + str(self.center.y) + ', ' + str(self.center.z) + ')-(' + str(self.radius) + ')'
            
    # Multiply the point by the matrix.
    def transformBy(self, matrix):
        try:
            self.center.transformBy(matrix)
        except:
            raise ArithmeticError('Circle transform failed.')


# Enum of point types.
class PointType():
     unknown = 1
     lineStart = 2
     lineEnd = 3
     lineStartAndEnd = 4
     arcMid = 5


class MyPoint:
    def __init__(self, x=0, y=0, z=0, type=PointType.unknown):
        self.x = x
        self.y = y
        self.z = z
        self.pointType = type
 
    # Multiply the point by the matrix.
    def transformBy(self, matrix):
        try:
            newX = self.x * matrix.getCell(1, 1) + self.y * matrix.getCell(2, 1) + self.z * matrix.getCell(3, 1) + matrix.getCell(4, 1)
            newY = self.x * matrix.getCell(1, 2) + self.y * matrix.getCell(2, 2) + self.z * matrix.getCell(3, 2) + matrix.getCell(4, 2)
            newZ = self.x * matrix.getCell(1, 3) + self.y * matrix.getCell(2, 3) + self.z * matrix.getCell(3, 3) + matrix.getCell(4, 3)
            self.x = newX
            self.y = newY
            self.z = newZ
        except:
            raise ArithmeticError('Point transform failed.')

    def vectorTo(self, point):
        return MyVector(point.x - self.x, point.y - self.y, point.z - self.z)            
    
    def asString(self):
        return str(self.x) + ', ' + str(self.y) + ', ' + str(self.z)
            
    def translateBy(self, vector):
        self.x += vector.x
        self.y += vector.y
        self.z += vector.z
        
    def copy(self):
        return MyPoint(self.x, self.y, self.z)
        
    def distanceTo(self, point):
        return math.sqrt(((point.x - self.x) ** 2) + ((point.y - self.y) ** 2) + ((point.z - self.z) ** 2))
        
    def bearingTo(self, point):        
        pointDist = self.distanceTo(point)
        if pointDist < _pointTol:
            raise ValueError('The points are at the same location.')

        # Determine which quadrant the point is in.
        if point.x >= self.x and point.y >= self.y:
            # First quadrant
            return math.acos((point.x - self.x) / pointDist)
        elif point.x < self.x and point.y >= self.y:
            # Second quadrant
            return math.acos((point.x - self.x) / pointDist)
        elif point.x >= self.x and point.y < self.y:
            # Third quadrant
            return (math.pi * 2) - math.acos((point.x - self.x) / pointDist)
        else:
            # Fourth quadrant
            return (math.pi * 2) - math.acos((point.x - self.x) / pointDist)
            
    def isEqualTo(self, point):
            if self.distanceTo(point) <= 0.000001:
                return True
            else:
                return False  


class MyVector:
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z
 
    # Multiply the point by the matrix.
    def transformBy(self, matrix):
        try:
            newX = self.x * matrix.getCell(1, 1) + self.y * matrix.getCell(2, 1) + self.z * matrix.getCell(3, 1) + matrix.getCell(4, 1)
            newY = self.x * matrix.getCell(1, 2) + self.y * matrix.getCell(2, 2) + self.z * matrix.getCell(3, 2) + matrix.getCell(4, 2)
            newZ = self.x * matrix.getCell(1, 3) + self.y * matrix.getCell(2, 3) + self.z * matrix.getCell(3, 3) + matrix.getCell(4, 3)
            self.x = newX
            self.y = newY
            self.z = newZ
        except:
            raise ArithmeticError('Point transform failed.')
            
    def asString(self):
            return str(self.x) + ', ' + str(self.y) + ', ' + str(self.z)
    
    def scaleBy(self, scale):
        self.x = self.x * scale
        self.y = self.y * scale
        self.z = self.z * scale
        
    # Calculate the dot product of two vectors.
    def dotProduct(self, vec):
        return (self.x * vec.x + self.y * vec.y + self.z * vec.z)

    # Calculate the angle between two vectors.        
    def angleTo(self, vec):
        dotProd = self.dotProduct(vec)
        val = dotProd / (self.length() * vec.length())
        if val < -1.0:
            val = -1.0
        elif val > 1.0:
            val = 1.0
        return math.acos(val)

    # Add two vectors.
    def add(self, vec):
        return MyVector(self.x + vec.x, self.y + vec.y, self.z + vec.z)
        
    # Subtract two vectors.
    def subtract(self, vec):
        return MyVector(self.x - vec.x, self.y - vec.y, self.z - vec.z)

    # Multiply the vectory by a value.
    def multiply(self, val):
        self.x *= val
        self.y *= val
        self.z *= val
    
    def length(self):
        return math.sqrt((self.x * self.x) + (self.y * self.y) + (self.z * self.z))
        
    def normalize(self):
        lng = self.length()
        self.x = self.x / lng
        self.y = self.y / lng
        self.z = self.z / lng
    


class MyMatrix:
    def __init__(self):
        self._data = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        
    def copy(self):
        newMatrix = MyMatrix()
        for i in range(0,16):
            newMatrix._data[i] = self._data[i]
        return newMatrix
        
    def setWithArray(self, array):
        for i in range(0,16):
            self._data[i] = array[i]
                
    def setToIdenty(self):
        self._data = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
                
    def getCell(self, column, row):
        return self._data[(row - 1) * 4 + (column - 1)]
                        
    def setCell(self, column, row, value):
        self._data[(row - 1) * 4 + (column - 1)] = value
       
    def transformBy(self, trans):
        newMatrix = MyMatrix()
        
        for i in range(1,5):
            for j in range(1,5):
                newMatrix.setCell(i, j, str(self.getCell(i, 1)) * trans.getCell(1, j) + self.getCell(i, 2) * trans.getCell(2, j) + self.getCell(i, 3) * trans.getCell(3, j) + self.getCell(i, 4) * trans.getCell(4, j))

        for i in range(0,16):
            self._data[i] = newMatrix._data[i]

    def invert(self): 
        # Create a new matrix with the translation portion stripped off.
        newMatrix = self.copy() 
        newMatrix.setCell(4, 1, 0)
        newMatrix.setCell(4, 2, 0)
        newMatrix.setCell(4, 3, 0)

        # Invert the matrix by swapping the cells along the diagonal.  This only
        # works for orthogonal matrices, which is all we need here.
        newMatrix.setCell(1, 2, self.getCell(2, 1))
        newMatrix.setCell(1, 3, self.getCell(3, 1))
        newMatrix.setCell(2, 3, self.getCell(3, 2))
        newMatrix.setCell(2, 1, self.getCell(1, 2))
        newMatrix.setCell(3, 1, self.getCell(1, 3))
        newMatrix.setCell(3, 2, self.getCell(2, 3))

        # Reverse the direction of the translation component.
        trans = self.translation()
        trans.transformBy(newMatrix)
        trans.scaleBy(-1)

        # Put the translation back into the matrix.
        newMatrix.setCell(4, 1, trans.x)
        newMatrix.setCell(4, 2, trans.y)
        newMatrix.setCell(4, 3, trans.z)

        for i in range(0,16):
            self._data[i] = newMatrix._data[i]
    
    def translation(self):
        return MyVector(self.getCell(4,1), self.getCell(4,2), self.getCell(4,3))
       
    def asString(self):
        result = ''
        for row in range(1, 5):
            if row == 1:
                result = str(self.getCell(1, row)) + ', ' + str(self.getCell(2, row)) + ', ' + str(self.getCell(3, row)) + ', ' + str(self.getCell(4, row))
            else:
                result += '\n' + str(self.getCell(1, row)) + ', ' + str(self.getCell(2, row)) + ', ' + str(self.getCell(3, row)) + ', ' + str(self.getCell(4, row))
            
        return result


class SectionLoop:
    def __init__(self):
        self.points = []
        self.isClosed = False
        self.startPoint = None
        self.endPoint = None
        self.isConnected = True


    def _setStartAndEndPoints(self):
        self.startPoint = self.points[0]
        self.endPoint = self.points[len(self.points)-1]

    def pointCount(self):
        return len(self.points)

    def replacePoint(self, index, newPoint):
        self.points[index-1] = newPoint
        self._setStartAndEndPoints()

    def addPoint(self, newPoint, addToEnd):
        if addToEnd:
            self.points.append(newPoint)
        else:
            self.points.insert(0, newPoint)
        self._setStartAndEndPoints()
        cnt = len(self.points)
        print(str(cnt))
            
    def removePoint(self, index):
        if index < len(self.points):
            self.points.pop(index)
            self._setStartAndEndPoints()        
        
    def optimizeLines(self):
        # Declare a list to store the point indices that will be removed.
        extraPoints = []

        # Initialize the start and mid points.
        startCheckPoint = self.points[0]
        midCheckPoint = self.points[1]
        endCheckPoint = None

        # Iterate over the points in the loop.  This overshoots
        # the length of the list so it will overlap to the beginning
        # so that the connecting points can be checked for colinearity.
        for i in range(2, len(self.points) + 2):
            # Special case when the index is the length plus 1 or 2
            # so that the start points are also considered.
            if i == len(self.points):
                endCheckPoint = self.points[0]
            elif i == len(self.points) + 1:
                endCheckPoint = self.points[1]
            else:
                endCheckPoint = self.points[i]

            # Calculate the angle defined by the three points.  If it's within a tolerance
            # of pi then they're colinear.
            vector1 = MyVector(startCheckPoint.x - midCheckPoint.x, startCheckPoint.y - midCheckPoint.y, startCheckPoint.z - midCheckPoint.z)
            vector1.normalize()
            vector2 = MyVector(endCheckPoint.x - midCheckPoint.x, endCheckPoint.y - midCheckPoint.y, endCheckPoint.z - midCheckPoint.z)
            vector2.normalize()
            angle = vector1.angleTo(vector2)
 
            # Check to see if the angle is within tolerance to 180 degrees.
            if math.fabs(math.pi - angle) < 0.0001:
                # Special case for last point.
                if i == len(self.points) + 2:
                    extraPoints.append(0)
#                elif i == len(self.points) + 1:
#                    extraPoints.append(1)
                else:
                    extraPoints.append(i-1)

                if startCheckPoint.pointType == PointType.lineEnd:
                    startCheckPoint.pointType = PointType.lineStartAndEnd
                else:
                    startCheckPoint.pointType = PointType.lineStart

                if endCheckPoint.pointType == PointType.lineStart:
                    endCheckPoint.pointType = PointType.lineStartAndEnd
                else:                    
                    endCheckPoint.pointType = PointType.lineEnd

                midCheckPoint = endCheckPoint
            else:
                startCheckPoint = midCheckPoint
                midCheckPoint = endCheckPoint

        # Sort the points to be removed.
        extraPoints.sort()
        extraPoints.reverse()

        for i in range(0, len(extraPoints)):
            self.removePoint(extraPoints[i])
        
        self._setStartAndEndPoints()
        
        
    def optimizeArcs(self):
        dumpPoints(self.points)        
        
        tolerance = 0.001
        
        # Declare a list to store the point indices that will be removed.
        extraPoints = []

        startPoint = self.points[0]
        midPoint = self.points[1]
        endPoint = self.points[2]
        currentCircle = MyCircle(startPoint, midPoint, endPoint)
        
        lastEndIndex = -1

        # Specify the minimum number of points that define an arc.
        minArcPoints = 6
        
        # Iterate over the points in the loop.
        goodPointCount = 0
        for i in range(3, len(self.points)+1):
            # Special case for the last point.
            if i == len(self.points):
                nextPoint = self.points[0]
            else:
                nextPoint = self.points[i]

            # Check to see if this point lies on the circle.            
            if currentCircle:
                if math.fabs(currentCircle.radius - nextPoint.distanceTo(currentCircle.center)) < tolerance:
                    goodPointCount += 1
                    if goodPointCount == minArcPoints - 3:
                        extraPoints.append(i-2)
                        extraPoints.append(i-1)
                    elif goodPointCount > minArcPoints - 3:
                        extraPoints.append(i-1)

                    if i == len(self.points) and goodPointCount >= minArcPoints - 3:
                        extraPoints.append(lastEndIndex-1)
                else:
                    # The point isn't on a circle so create any current arc info 
                    # and create a new circle to check
                    # A value of 1 indicates that the circle must pass through 5 points.
                    if goodPointCount > minArcPoints - 3:  
                        midPoint.pointType = PointType.arcMid
                        goodPointCount = 0
                        startPoint = nextPoint
                        midPoint = None
                        endPoint = None
                        currentCircle = None
                    else:    
                        goodPointCount = 0
                        startPoint = midPoint
                        midPoint = endPoint
                        endPoint = nextPoint
                        currentCircle = MyCircle(startPoint, midPoint, endPoint)
                        lastEndIndex = i
            else:
                if not midPoint:
                    midPoint = nextPoint
                elif not endPoint:
                    endPoint = nextPoint
                    currentCircle = MyCircle(startPoint, midPoint, endPoint)

        if goodPointCount > minArcPoints - 3:  
            midPoint.pointType = PointType.arcMid
            goodPointCount = 0

        # Sort the points to be removed.
        extraPoints.sort()
        extraPoints.reverse()

        for i in range(0, len(extraPoints)):
            self.removePoint(extraPoints[i])
        
        self._setStartAndEndPoints()
        

def dumpPoints(points):
    f = open('C:/Temp/PointsDump.txt','w')

    pointCnt = 0
    for point in points:
        if point.pointType == PointType.lineStart:
            pntType = 'lineStart'
        elif point.pointType == PointType.lineEnd:
            pntType = 'lineEnd'
        elif point.pointType == PointType.lineStartAndEnd:
            pntType = 'lineStartAndEnd'
        elif point.pointType == PointType.arcMid:
            pntType = 'arcMid'
        elif point.pointType == PointType.unknown:
            pntType = 'unknown'
            
        f.write(str(pointCnt) + '. ' + pntType + ', ' + str(point.x) + ', ' + str(point.y) + ', ' + str(point.z) + '\n' )
        pointCnt += 1
    f.close()        