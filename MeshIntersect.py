# (C) Copyright 2015 by Autodesk, Inc.
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
        
        # Get the "Project/Include" drop-down.  Because the drop-downs created by Fusion don't
        # currently have ID's this looks for the drop-down that contains the Intersect command.
        controlAdded = False
        for cntrl in sketchPanel.controls:
            if not controlAdded:
                # Look for drop-down controls.
                if cntrl.objectType == adsk.core.DropDownControl.classType():
                    # Check to see if this drop-downn contains the Intersect command.
                    for subCntrl in cntrl.controls:
                        if subCntrl.id == 'IntersectCmd':
                            # Add the mesh body section command below the Intersect command.
                            cntrl.controls.addCommand(meshIntersectButton, 'IntersectCmd', True)
                            controlAdded = True
                            break
            else:
                break
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
        
        # Get the "Project/Include" drop-down.  Because the drop-downs created by Fusion don't
        # currently have ID's this looks for the drop-down that contains the Intersect command.
        controlDeleted = False
        for cntrl in sketchPanel.controls:
            if not controlDeleted:                
                # Look for drop-down controls.
                if cntrl.objectType == adsk.core.DropDownControl.classType():
                    # Check to see if this drop-downn contains the Intersect command.
                    for subControl in cntrl.controls:
                        if subControl.id == 'meshIntersect':
                            # Delete the control.
                            subControl.deleteMe()
                            controlDeleted = True
                            break
            else:
                break
        
        meshInterectCommandDef = ui.commandDefinitions.itemById('meshIntersect')
        if meshInterectCommandDef:
            meshInterectCommandDef.deleteMe()
    except:
        if ui:
            ui.messageBox('Unexpected failure removing command.', 'Intersect Mesh Body')
            #ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



class MeshIntersectCommandExecutedEventHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        app = adsk.core.Application.get()
        ui  = app.userInterface
        try:
            command = args.firingEvent.sender
            meshBodies = []
            
            # Get the data and settings from the command inputs.
            for input in command.commandInputs:
                if input.id == 'meshSelect':
                    for i in range(0, input.selectionCount):
                        meshSelection = input.selection(i)
                        meshBodies.append(meshSelection.entity)
                elif input.id == 'optimizeLines':
                    optimizeLines = input.value

            # Get the active sketch.
            sketch = app.activeEditObject

            # Process each selected mesh body.
            for meshBody in meshBodies:
                loops = calculateIntersection(meshBody, sketch, True, optimizeLines)
        
                sketch.isComputeDeferred = True
                lines = sketch.sketchCurves.sketchLines
                for loop in loops:
                    if loop.isConnected:
                        isFirstPoint = True
                        isFirstLine = True
                        for point in loop.points:
                            if isFirstPoint == True:
                                lastPoint = point.copy()
                                isFirstPoint = False
                            else:
                                if isFirstLine:
                                    lastLine = lines.addByTwoPoints(adsk.core.Point3D.create(lastPoint.x, lastPoint.y, lastPoint.z),
                                                                    adsk.core.Point3D.create(point.x, point.y, point.z))
                                    firstLine = lastLine
                                    isFirstLine = False
                                else:
                                    lastLine = lines.addByTwoPoints(lastLine.endSketchPoint, adsk.core.Point3D.create(point.x, point.y, point.z))
                                    
                        if loop.isClosed:
                            lastLine = lines.addByTwoPoints(lastLine.endSketchPoint, firstLine.startSketchPoint)
                    else:
                        for i in range(0, int(len(loop.points)/2)-1):
                            pnt1 = loop.points[i*2]
                            pnt2 = loop.points[i*2+1]
                            lines.addByTwoPoints(adsk.core.Point3D.create(pnt1.x, pnt1.y, pnt1.z),
                                                 adsk.core.Point3D.create(pnt2.x, pnt2.y, pnt2.z))               
                                                
                sketch.isComputeDeferred = False
        except:
            if ui:
                ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
                #ui.messageBox('command executed failed:\n{}'.format(traceback.format_exc()))



class MeshIntersectCommandCreatedEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__() 
    def notify(self, args):
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            
            # Make sure a sketch is active.
            if app.activeEditObject.objectType != adsk.fusion.Sketch.classType():
                # Exit and do nothing.
                ui.messageBox('A sketch must be active.')
                return

            cmd = args.command
            inputs = cmd.commandInputs

            # Connect to the command executed event.
            commandExecuted = MeshIntersectCommandExecutedEventHandler()
            cmd.execute.add(commandExecuted)
            handlers.append(commandExecuted)
        
            # Create the input for selecting the mesh bodies.
            selInput = inputs.addSelectionInput('meshSelect', 'Mesh bodies', 'Select meshes to section.')
            selInput.addSelectionFilter('MeshBodies')
            result = selInput.setSelectionLimits(1,0)
            
            # Create the check box input to determine if multiple colinear lines should be replaced with a single line.
            boolInput = inputs.addBoolValueInput('optimizeLines', 'Combine colinear lines', True, '', True)            

            msg = '<div align="center">By default, mesh bodies are not selectable in the graphics window. However, they are selectable in the browser.</div>'
            txtBox = inputs.addTextBoxCommandInput('message', '', msg, 5, True)
            txtBox.isFullWidth = True            
        except:
            if ui:
                ui.messageBox('Unexpected failure.', 'Intersect Mesh Body')
                #ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))   



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
def calculateIntersection(mesh, sketch, connectLoops, clean):
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
            
#==============================================================================
#             app = adsk.core.Application.get()
#             design = app.activeProduct
#             sketch = design.rootComponent.sketches.itemByName('Model')
#             sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(sideOnePoint1.x, sideOnePoint1.y, sideOnePoint1.z), adsk.core.Point3D.create(sideTwoPoint.x, sideTwoPoint.y, sideTwoPoint.z))
#             sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(sideOnePoint2.x, sideOnePoint2.y, sideOnePoint2.z), adsk.core.Point3D.create(sideTwoPoint.x, sideTwoPoint.y, sideTwoPoint.z))
#==============================================================================
            
            # Intersect the lines with the X-Y plane.
            intResult1 = lineXYPlaneIntersection(lineSeg1)
            intResult2 = lineXYPlaneIntersection(lineSeg2)
            
            # Skip any zero length segments.
            if intResult1.distanceTo(intResult2) > .000001:
                intersectionLines.append(MyLine(intResult1, intResult2))

    if connectLoops:
        # Process the lines so they're in a nice connected order and grouped
        # by loops.
        intersectionLoops = createSectionLoops(intersectionLines, clean)
    else:
        loop = SectionLoop()
        loop.isConnected = False
        
        for line in intersectionLines:
            loop.addPoint(line.start, True)
            loop.addPoint(line.end, True)
        
        intersectionLoops = []
        intersectionLoops.append(loop)
        
    return intersectionLoops



# Given a list of lines that represent the intersection this cleans them up so they're
# in head-to-tail connected loops.  It returns a list of sectionLoop objects.
def createSectionLoops(intersectionLines, clean):
    print('Line count: ' + str(len(intersectionLines)))
    for i in range(0,len(intersectionLines)):
        line = intersectionLines[i]

    # Initialize the list that will contain the section loops.
    sectionLoops = []
    
    currentLoop = SectionLoop()

    # Initialize the loop with the points from the first line.
    currentLoop.addPoint(intersectionLines[0].start, True)
    currentLoop.addPoint(intersectionLines[0].end, True)
    
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
                if pointsWithinTol(currentLine.start, currentLoop.startPoint):
                    newPoint = currentLine.end
                    isAtEnd = False
                    intersectionLines[j] = None
                elif pointsWithinTol(currentLine.start, currentLoop.endPoint):
                    newPoint = currentLine.end
                    isAtEnd = True
                    intersectionLines[j] = None
                elif pointsWithinTol(currentLine.end, currentLoop.startPoint):
                    newPoint = currentLine.start
                    isAtEnd = False
                    intersectionLines[j] = None
                elif pointsWithinTol(currentLine.end, currentLoop.endPoint):
                    newPoint = currentLine.start
                    isAtEnd = True
                    intersectionLines[j] = None

                # If a point was found, check to see if this point closes the loop.
                if newPoint != None:
                    foundPoint = True

                    if (isAtEnd and pointsWithinTol(newPoint, currentLoop.startPoint)) or (not isAtEnd and pointsWithinTol(newPoint, currentLoop.endPoint)):
                        currentLoop.isClosed = True

                        # Clean this loop of colinear lines.
                        if clean:
                            currentLoop.clean()

                        # Save this loop and start a new loop.
                        sectionLoops.append(currentLoop)
                        currentLoop = SectionLoop()

                        # Find the next unused line and use it to start the next loop.
                        for k in range(0, len(intersectionLines)):
                            if intersectionLines[k] != None:
                                # Add the two points to the end of the loop.
                                currentLoop.addPoint(intersectionLines[k].start, True)
                                currentLoop.addPoint(intersectionLines[k].end, True)
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
            if currentLoop.pointCount > 0:
                # Clean this loop of colinear lines.
                if clean:
                    currentLoop.clean()

                # Save this loop and start a new loop.
                sectionLoops.append(currentLoop)

            noMoreLines = True
            currentLoop = SectionLoop()
            for k in range(0, len(intersectionLines)):
                if intersectionLines[k] != None:
                    noMoreLines = False

                    # Add the two points to the end of the loop.
                    currentLoop.addPoint(intersectionLines[k].start, True)
                    currentLoop.addPoint(intersectionLines[k].end, True)
                    intersectionLines[k] = None
                    break

        if noMoreLines:
            break

    # Save the current loop.
    if currentLoop.pointCount > 0:
        # Clean this loop of colinear lines.
        if clean:
            currentLoop.clean()

        # Add this loop to the collection.
        sectionLoops.append(currentLoop)
            
    return sectionLoops



# Calculate the intersection point of a line and the x-y plane
# This assumes the line does intersect, which in this case
# has already been validated.
def lineXYPlaneIntersection(line):
    # Get the length of the line the Z direction.
    zLength = abs(line.start.z) + abs(line.end.z)     

    # Compute the length factor of the start point to the z plane.
    factor = abs(line.start.z) / zLength

    # Create a vector along the line and scale it by the factor.    
    lineVec = line.start.vectorTo(line.end)
    lineVec.scaleBy(factor)
    
    # Move the line start point along the vector the scaled distance
    # and that will be the intersection point.
    intPoint = line.start.copy()
    intPoint.translateBy(lineVec)
    
    return intPoint
        


class MyLine:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def asString(self):
            return '(' + str(self.start.x) + ', ' + str(self.start.y) + ', ' + str(self.start.z) + ')-(' + str(self.end.x) + ', ' + str(self.end.y) + ', ' + str(self.end.z) + ')'
            
    # Multiply the point by the matrix.
    def transformBy(self, matrix):
        try:
            self.start.transformBy(matrix)
            self.end.transformBy(matrix)
        except:
            raise ArithmeticError('Point transform failed.')
            


class MyPoint:
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
        self.pointCount = 0
        self.startPoint = None
        self.endPoint = None
        self.isConnected = True

    def _setStartAndEndPoints(self):
        self.startPoint = self.points[0]
        self.endPoint = self.points[len(self.points)-1]

    def replacePoint(self, index, newPoint):
        self.points[index-1] = newPoint
        self._setStartAndEndPoints()

    def addPoint(self, newPoint, addToEnd):
        if addToEnd:
            self.points.append(newPoint)
        else:
            self.points.insert(0, newPoint)
        self._setStartAndEndPoints()
        self.pointCount += 1
            
    def getPoint(self, index):
        return self.points[index-1]

    def removePoint(self, index):
        self.points.pop(index-1)
        self._setStartAndEndPoints()        
        self.pointCount -= 1
        
    def clean(self):
        # Declare a list to store the point indices that will be removed.
        extraPoints = []

        # Initialize the start and mid points.
        startCheckPoint = self.points[0]
        midCheckPoint = self.points[1]
        endCheckPoint = None

        # Iterate over the points in the loop
        for i in range(3, self.pointCount + 3):
            # Set the current end point, special casing for the last point to be
            # able to check the closing point to see if their colinear.
            if i == self.pointCount + 1:
                endCheckPoint = self.getPoint(1)
            elif i == self.pointCount + 2:
                endCheckPoint = self.getPoint(2)
            else:
                endCheckPoint = self.getPoint(i)

            # Calculate the angle defined by the three points.  If it's within a tolerance
            # of pi then they're colinear.
            vector1 = MyVector(startCheckPoint.x - midCheckPoint.x, startCheckPoint.y - midCheckPoint.y, startCheckPoint.z - midCheckPoint.z)
            vector1.normalize()
            vector2 = MyVector(endCheckPoint.x - midCheckPoint.x, endCheckPoint.y - midCheckPoint.y, endCheckPoint.z - midCheckPoint.z)
            vector2.normalize()
            angle = math.acos(vector1.x * vector2.x + vector1.y * vector2.y + vector1.z * vector2.z)

            # Check to see if the angle is within tolerance to 180 degrees.
            if math.fabs(math.pi - angle) < 0.0001:
                # Special case for last point.
                if i == self.pointCount + 2:
                    extraPoints.append(1)
                else:
                    extraPoints.append(i - 1)

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

    
    
def pointsWithinTol(point1, point2):
        if point1.distanceTo(point2) <= 0.000001:
            return True
        else:
            return False  