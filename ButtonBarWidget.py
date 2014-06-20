'''
Created on May 28, 2014

@author: tpmaxwel
'''

import vtk, os, sys, collections
import numpy as np
from ConfigurationFunctions import *

PackagePath = os.path.dirname( __file__ )  
DataDir = os.path.join( PackagePath, 'data' )
ButtonDir = os.path.join( DataDir, 'buttons' )

class OriginPosition:
    Upper_Left = [ 0, 1 ] 
    Upper_Right = [ 1, 1 ]  
    Lower_Left = [ 0, 0 ]  
    Lower_Right = [ 1, 0 ] 
    
class Orientation:
    Horizontal = 0 
    Vertical = 1 

class ProcessMode:
    Default = 0
    Slicing = 1
    Thresholding = 2
    LowRes = 0
    HighRes = 1
    AnyRes = 2
        
class Button:
    
    FuncToggleStateOn = 1
    FuncToggleStateOff = 2
        
    def __init__( self, iren, **args ):
        self.StateChangedSignal = SIGNAL('StateChanged')
        self.invokingEvent = False
        self.active = True
        self.renderWindowInteractor = iren
        self.names = args.get( 'names', [] )
        self.state = args.get( 'state', 0 )
        self.children = args.get( 'children', [] )
        self.toggle = args.get( 'toggle', False )
        self.parents = args.get( 'parents', [] )
        self.numberOfStates = args.get( 'nstates', ( 2 if self.toggle else len( self.names ) ) )
        self.id = args.get( 'id', self.names[0] if self.numberOfStates else None )
        self.key = args.get( 'key', None )
        self.image_size = None
        self.button_files = [ ]
        self.functionKeys = { }
        self.createButtonRepresentation()
        self.buttonWidget = vtk.vtkButtonWidget()
        self.buttonWidget.SetInteractor(self.renderWindowInteractor)
        self.buttonWidget.SetRepresentation( self.buttonRepresentation )
        self.buttonWidget.AddObserver( 'StateChangedEvent', self.processStateChangeEvent )
        self.buttonRepresentation.Highlight( self.state )
        
    def getFunctionMapKey (self, key, ctrl ):
        return "c-%c" % key if ctrl else "%c" % key

    def addFunctionKey(self, key, ctrl, function ):
        fkey =  self.getFunctionMapKey( key, ctrl )       
        self.functionKeys[ fkey ]  = function
        
    def processFunctionKey( self, key, ctrl ):
        fkey =  self.getFunctionMapKey( key, ctrl )       
        function = self.functionKeys.get( fkey, None )
        if function <> None: 
            self.executeFunction( function )
            return 1
        return 0
    
    def executeFunction( self, function ):
        if   function == Button.FuncToggleStateOn:  self.setToggleState( 1 )
        elif function == Button.FuncToggleStateOff: self.setToggleState( 0 )
    
    def createButtonRepresentation(self, **args):
        JPEGReader = vtk.vtkJPEGReader()
        self.buttonRepresentation = vtk.vtkTexturedButtonRepresentation2D()
        self.buttonRepresentation.SetPlaceFactor( args.get( 'scale', 1 ) )
        num_images = len( self.names )
        if num_images:           
            self.buttonRepresentation.SetNumberOfStates(num_images)
            for button_index in range( num_images ):                
                buttonFilePath = os.path.join( ButtonDir,  '.'.join( [ self.names[ button_index ], 'jpeg' ] ) )
                JPEGReader.SetFileName ( buttonFilePath )
                JPEGReader.Update()
                image_data = JPEGReader.GetOutput()
                if self.image_size == None: self.image_size = image_data.GetDimensions()
                self.buttonRepresentation.SetButtonTexture( button_index, image_data )
                self.button_files.append( buttonFilePath )
            self.setToggleProps()
        
    def addObserver(self, observer, **args ):
        event = args.get( 'event', 'StateChangedEvent' )
        self.buttonWidget.AddObserver( event, observer )
        
    def setToggleProps(self, state = None ):
        if self.toggle:
            prop = self.buttonRepresentation.GetProperty()
            prop.SetOpacity( 0.4 if ( self.state == 0 ) else 1.0 )
            self.buttonRepresentation.SetProperty(prop)
            prop = self.buttonRepresentation.GetHoveringProperty()
            prop.SetOpacity( 0.7 if ( self.state == 0 ) else 1.0 )
            self.buttonRepresentation.SetHoveringProperty(prop)
            self.buttonRepresentation.Modified()
            self.buttonRepresentation.NeedToRenderOn()
            
    def processKeyEvent( self, key, ctrl = 0 ):
        if self.processFunctionKey( key, ctrl ): 
            return True        
        if key == self.key and not self.invokingEvent:
            self.buttonRepresentation.Highlight( self.buttonRepresentation.HighlightSelecting )
            self.processStateChangeEvent( self, "KeyEvent", True )
            self.buttonRepresentation.Highlight( self.buttonRepresentation.HighlightNormal )
            return True
        return False
    
    def setToggleState( self, state ):
        self.state = state
        self.setToggleProps()       

    def processStateChangeEvent( self, obj, event, indirect = False ):
        self.invokingEvent = True 
        self.setButtonState( ( self.state + 1 ) % self.numberOfStates, indirect )      
        self.invokingEvent = False
        
    def setButtonState( self, state, indirect = False ):
        self.state = state
        if (self.key <> None) and not indirect:
            self.renderWindowInteractor.SetKeyEventInformation( 0, 0, self.key, 1, self.key )
            self.renderWindowInteractor.InvokeEvent( 'CharEvent' )
        self.setToggleProps()
        self.broadcastState()
        
    def broadcastState(self):
        self.StateChangedSignal( self.id, self.key, self.state )
        
    def place( self, bounds ):
        self.buttonRepresentation.PlaceWidget( bounds )
        
    def size(self):
        return self.image_size
    
    def On(self):
        if self.active: 
            self.buttonWidget.On()

    def Off(self):
        self.buttonWidget.Off()
        
    def activate(self):
        self.active = True
        self.buttonWidget.On()

    def deactivate(self):
        self.active = False
        self.buttonWidget.Off()

class ButtonBarWidget:
    
    current_configuration_mode = None
    button_bars = {}
    
    def __init__( self, name, interactor, **args ):
        self.vtk_coord = vtk.vtkCoordinate()
        self.vtk_coord.SetCoordinateSystemToNormalizedDisplay()
        self.StateChangedSignal = SIGNAL('StateChanged')
        self.process_mode = ProcessMode.Default
        self.currentSliders = {}
        self.slider_postions = [ [ [ 0.25, 0.75 ] ], [ [0.01,0.48], [0.52, 0.99 ] ], [ [0.01,0.3], [0.35,0.7], [0.75, 0.99 ] ], [ [0.01,0.24], [0.26,0.49], [0.51,0.74], [0.76, 0.99 ] ]    ]
        self.slidersVisible = [ True, False, False, False ]
        self.interactor = interactor
        self.InteractionState = None
        self.LastInteractionState = None
        self.activeSliceIndex = 0  
        self.name = name 
        self.groups = {}
        self.origin = args.get( 'origin', OriginPosition.Upper_Left )
        self.orientation = args.get( 'orientation', Orientation.Vertical )
        self.position = args.get( 'position', ( 0.0, 1.0 ) )
        self.buffer = args.get( 'buffer', ( 3, 3 ) )
        self.fullButtonWindowSize = 1300
        self.buttons = []
        self.visible = False
        self.configurableFunctions = collections.OrderedDict()
        ButtonBarWidget.button_bars[ name ] = self
        self.updateWindowSize()
        
    def clear( self, **args ):
        current_button_id = args.get( 'current', None )
        for b in self.buttons:
            if ( current_button_id == None ) or ( b.id <> current_button_id ):
                if b.state <> 0:
                    b.setButtonState( 0 )
     
    @classmethod   
    def getButtonBar( cls, name ):
        return cls.button_bars.get( name, None )

    @classmethod   
    def broadcastButtonState( cls, type, name,  **args ):
        bbar = cls.getButtonBar( type )
        button = bbar.getButton( name )    
        button.broadcastState( **args )    

    @classmethod   
    def getButtonBars( cls ):
        return cls.button_bars.values()

    @classmethod   
    def findButton( cls, name  ):
        for bbar in cls.button_bars.values():
            b = bbar.getButton( name )
            if b <> None: return b
        return None

    @classmethod   
    def repositionButtons( cls ):
        for button_bar in cls.button_bars.values():
            button_bar.reposition()                                          

    @classmethod   
    def initializeConfigurations( cls, **args ) :
        for bbar in cls.button_bars.values():
            bbar.initializeConfiguration( **args )
        for bbar in cls.button_bars.values():
            bbar.initializeChildren( **args )
                    
    def sliceRoundRobin(self, args, config_function = None ):
        if args[0] == "InitConfig":
            self.activeSliceIndex = ( self.activeSliceIndex+ 1 ) % 3
            toggle_list = self.groups.get( config_function.name, [] )
            for iSlice in range( len(toggle_list) ):
                button = toggle_list[ iSlice ]
                state = 1 if (iSlice == self.activeSliceIndex) else 0
                button.setButtonState( state )
        
    def updateWindowSize(self):
        self.windowSize = self.interactor.GetRenderWindow().GetSize()
        
    def render( self ):
        self.interactor.GetRenderWindow().Render()
       
    def build( self, **args ):
        self.current_location = self.getScreenPosition( self.position, **args )
        for button in self.buttons:
            self.current_location = self.placeButton( button, self.current_location )
            
    def reposition( self, **args ):
#        print "Reposition: %d " % self.windowSize[0]
        self.updateWindowSize()
        self.build( **args )
             
    def placeButton( self, button, position, **args ):
        max_size = button.size()
        window_size = min( self.windowSize[0], self.windowSize[1] ) 
        scale = float(window_size)/ self.fullButtonWindowSize
        if scale > 1.0:   scale = 1.0
        if scale < 0.2:   scale = 0.2
#        print "Resize: %d %s " % ( window_size, scale )
        size = [ max_size[0]*scale, max_size[1]*scale ]
        bounds = self.computeBounds( position, size )
#        print " placeButton[%s]: bounds = %s" % ( button.id, str(bounds) )
        button.place( bounds )
        return self.getOffsetScreenPosition( size, position )
           
    def getScreenPosition(self, normalized_display_position, buffered = True, **args ):
        self.vtk_coord.SetValue(  normalized_display_position[0], normalized_display_position[1] )
        screen_pos = self.vtk_coord.GetComputedDisplayValue( self.getRenderer() )
        position_offset = args.get( 'offset', [ 0, 0 ] )
        if   self.orientation == Orientation.Vertical: position_offset[ 0 ] = 0
        elif self.orientation == Orientation.Horizontal: position_offset[ 1 ] = 0
        if buffered: screen_pos = self.getBufferedPos( screen_pos, position_offset  )
        return screen_pos
  
    def getBufferedPos( self, screen_pos, position_offset = [ 0, 0 ] ): 
        buff_screen_pos = list( screen_pos )         
        for ic in range(2):
            if self.origin[ic]:  buff_screen_pos[ic] = screen_pos[ic] - self.buffer[ic] - position_offset[ic]
            else:                buff_screen_pos[ic] = screen_pos[ic] + self.buffer[ic] + position_offset[ic]
        return buff_screen_pos
            
    def getOffsetScreenPosition( self, bsize, current_location ):
        offset_location = list( current_location )
        offset = [ bsize[0] + self.buffer[0], bsize[1] + self.buffer[1] ]
        if self.orientation == Orientation.Vertical:
            offset_location[1] = offset_location[1] - offset[1] if self.origin[1] else offset_location[1] + offset[1]
        if self.orientation == Orientation.Horizontal:
            offset_location[0] = offset_location[0] - offset[0] if self.origin[0] else offset_location[0] + offset[0]
        return offset_location
            
    def processStateChangeEvent( self, button_id, key, state ):
        print " processStateChangeEvent: ", str( [ button_id, key, state ] )
        self.StateChangedSignal( button_id, key, state )
        if state > 0: 
            self.updateInteractionState( button_id, state  ) 
        else:
            b = self.getButton( button_id )
            if not b.toggle: 
                self.updateInteractionState( button_id, state  )                
            else:
                configFunct = self.configurableFunctions.get( button_id, None )
                position_index = configFunct.getPosition() if configFunct else None
                self.releaseSlider( position_index ) 
                configFunct.processInteractionEvent( [ "InitConfig", 0, False, self ] )
#        config_function = self.configurableFunctions.get( button_id, None )
#        if config_function: config_function.processStateChangeEvent( state )
#        button = self.buttons.get( button_id, None )
    
    def computeBounds( self, pos, size ):
        bds = [0.0]*6
        bds[0] = pos[0] - size[0] if self.origin[0] else pos[0]
        bds[1] = pos[0] if self.origin[0] else pos[0] + size[0]
        bds[2] = pos[1] - size[1] if self.origin[1] else pos[1]
        bds[3] = pos[1] if self.origin[1] else pos[1] + size[1]
        return bds
    
    def show(self):
        self.visible = True
        for button in self.buttons: button.On()
        
    def processKeyEvent( self, key, ctrl = 0 ):
        processed = False
        for button in self.buttons: 
            if button.processKeyEvent( key, ctrl ): 
                processed = True
        return processed
 
    def hide(self):
        self.visible = False
        for button in self.buttons: button.Off()
            
    def toggleVisibility(self):
        if self.visible: 
            self.hide()
        else:
            self.updatePositions() 
            self.show()

    def addSliderButton( self, **args ):
        button = self.addButton( **args )
        self.addConfigurableSliderFunction( button.id, **args)
        return button
        
    def addConfigButton( self, **args ):
        button = self.addButton( **args )
        self.addConfigurableFunction( button.id, **args)
        return button

    def getButton(self, name ): 
        for b in self.buttons:
            if b.id == name: return b
        return None

    def addButton( self, **args ):
        button = Button( self.interactor, **args )
        button.StateChangedSignal.connect( self.processStateChangeEvent )
        self.buttons.append( button )
        roundRobin = args.get( 'group', None )
        if roundRobin:
            grpList = self.groups.setdefault(roundRobin,[])
            grpList.append( button )
        return button
            
    def getRenderer(self):
        rw = self.interactor.GetRenderWindow()
        return rw.GetRenderers().GetFirstRenderer ()

    def addConfigurableFunction(self, name, **args):
        self.configurableFunctions[name] = ConfigurableFunction( name, **args )

    def addConfigurableSliderFunction(self, name, **args):
        self.configurableFunctions[name] = ConfigurableSliderFunction( name, **args )

    def getConfigFunction( self, name ):
        return self.configurableFunctions.get(name,None)

    def removeConfigurableFunction(self, name ):        
        del self.configurableFunctions[name]

    def applyConfiguration(self, **args ):       
        for configFunct in self.configurableFunctions.values():
            configFunct.applyParameter( **args  )

    def updateSliderWidgets(self, value0, value1 ): 
        for index, value in enumerate( ( value0, value1 ) ):
            if value <> None: self.setSliderValue( index, value )

    def setSliderValue(self, index, value ):
        ( process_mode, interaction_state, swidget ) = self.currentSliders.get( index, ( None, None, None ) )
        if swidget:
            srep = swidget.GetRepresentation( )   
            srep.SetValue( value  )
            
    def centerSlider( self, index ):
        ( process_mode, interaction_state, swidget ) = self.currentSliders.get( index, ( None, None, None ) )
        if swidget:
            srep = swidget.GetRepresentation( )  
            value = ( srep.GetMinimumValue() + srep.GetMaximumValue() ) / 2.0 
            srep.SetValue( value  ) 
                    
    def createSliderWidget( self, index ): 
        sliderRep = vtk.vtkSliderRepresentation2D()
            
        sliderRep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedDisplay()
        sliderRep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedDisplay()
        prop = sliderRep.GetSliderProperty()
        prop.SetColor( 1.0, 0.0, 0.0 )
        prop.SetOpacity( 0.5 )
        sprop = sliderRep.GetSelectedProperty()
        sprop.SetOpacity( 0.8 )           
        tprop = sliderRep.GetTubeProperty()
        tprop.SetColor( 0.5, 0.5, 0.5 )
        tprop.SetOpacity( 0.5 )
        cprop = sliderRep.GetCapProperty()
        cprop.SetColor( 0.0, 0.0, 1.0 )
        cprop.SetOpacity( 0.5 )
#        sliderRep.PlaceWidget(  bounds   )  
        sliderRep.SetSliderLength(0.05)
        sliderRep.SetSliderWidth(0.02)
        sliderRep.SetTubeWidth(0.01)
        sliderRep.SetEndCapLength(0.02)
        sliderRep.SetEndCapWidth(0.02)
        sliderRep.SetTitleHeight( 0.02 )    
        sliderWidget = vtk.vtkSliderWidget()
        sliderWidget.SetInteractor(self.interactor)
        sliderWidget.SetRepresentation( sliderRep )
        sliderWidget.SetAnimationModeToAnimate()
        sliderWidget.EnabledOn()
        sliderWidget.AddObserver("StartInteractionEvent", self.processStartInteractionEvent )
        sliderWidget.AddObserver("EndInteractionEvent", self.processEndInteractionEvent )
        sliderWidget.AddObserver("InteractionEvent", self.processInteractionEvent )
        sliderWidget.KeyPressActivationOff()
        return sliderWidget
    
    def positionSliders( self, nsliders ): 
        for islider in range( nsliders ):
            self.positionSlider( islider, nsliders )
            
    def releaseSliders( self ):
        for index in range(4): 
            self.releaseSlider( index )            
            
    def positionSlider(self, position_index, n_sliders ):
        slider_pos = self.slider_postions[ n_sliders ]
        ( process_mode, interaction_state, swidget ) = self.currentSliders[position_index]
        sliderRep = swidget.GetRepresentation( ) 
        sliderRep.GetPoint1Coordinate().SetValue( slider_pos[position_index][0], 0.06, 0 )  
        sliderRep.GetPoint2Coordinate().SetValue( slider_pos[position_index][1], 0.06, 0 )
        sliderRep.Modified()
        swidget.Modified()    
        sliderRep.NeedToRenderOn()
                        
    def commandeerSlider(self, index, label, bounds, value ): 
        widget_item = self.currentSliders.get( index, None )
        if widget_item == None: 
            swidget = self.createSliderWidget(index) 
        else:
            ( process_mode, interaction_state, swidget ) = widget_item 
        srep = swidget.GetRepresentation( )      
        srep.SetTitleText( label )    
        srep.SetMinimumValue( bounds[ 0 ] )
        srep.SetMaximumValue( bounds[ 1 ]  )
        srep.SetValue( value )
        swidget.SetEnabled( 1 ) 
        self.currentSliders[index] = ( self.process_mode, self.InteractionState, swidget )
        
    def releaseSlider( self, index ):      
        ( process_mode, interaction_state, swidget ) = self.currentSliders.get( index, ( None, None, None ) )  
        if swidget: swidget.SetEnabled( 0 ) 

    def getSliderEnabled( self, index ):        
        ( process_mode, interaction_state, swidget ) = self.currentSliders.get( index, ( None, None, None ) )  
        if swidget: return swidget.GetEnabled() 
        return False
        
    def clearInteractions(self):
        if self.InteractionState <> None: 
            configFunct = self.configurableFunctions[ self.InteractionState ]
            configFunct.close()   
        self.process_mode = ProcessMode.Default
        self.InteractionState = None
        for ( process_mode, interaction_state, swidget ) in self.currentSliders.values():
            swidget.SetEnabled( 0 ) 
        self.render()

    def processInteractionEvent( self, obj=None, event=[] ):
#        print " processInteractionEvent: ( %s %d )" % ( self.InteractionState, self.process_mode )
        if ( self.InteractionState <> None ): 
            srep = obj.GetRepresentation( ) 
            config_function = self.getConfigFunction( self.InteractionState )
            config_function.processInteractionEvent( [ "UpdateConfig", self.getSliderIndex(obj), srep, event  ] )                         
#         else:
#             if self.process_mode == ProcessMode.Slicing:
#                 ( process_mode, interaction_state, swidget ) = self.currentSliders[1] 
#                 slice_pos = swidget.GetRepresentation( ).GetValue()
#                 self.pushSlice( slice_pos )         

    def processStartInteractionEvent( self, obj, event ): 
        slider_index = self.checkInteractionState( obj, event ) 
#        print " processStartInteractionEvent: ( %s %d )" % ( self.InteractionState, self.process_mode )
        if ( self.InteractionState <> None ): 
            config_function = self.getConfigFunction( self.InteractionState )
            config_function.processInteractionEvent( [ "StartConfig", slider_index ] )  
                
    def checkInteractionState( self, obj, event ):
        for item in self.currentSliders.items():
            ( process_mode, interaction_state, swidget ) = item[1]
            if ( id( swidget ) == id( obj ) ): 
                if self.InteractionState <> interaction_state:            
                    self.processEndInteractionEvent( obj, event )
                    if self.InteractionState <> None: self.endInteraction()
                    self.InteractionState = interaction_state
                    self.process_mode = process_mode
#                    print "Change Interaction State: %s %d " % ( self.InteractionState, self.process_mode )
                return item[0]
        return None
            
    def getSliderIndex(self, obj ):
        for index in self.currentSliders:
            ( process_mode, interaction_state, swidget ) = self.currentSliders[index]
            if ( id( swidget ) == id( obj ) ): return index
        return None

    def processEndInteractionEvent( self, obj, event ):  
#        print " processEndInteractionEvent: ( %s %d )" % ( self.InteractionState, self.process_mode )
        if ( self.InteractionState <> None ): 
            config_function = self.getConfigFunction( self.InteractionState )
            config_function.processInteractionEvent( [ "EndConfig" ] )  

    def startConfiguration( self, x, y, config_types ): 
        if (self.InteractionState <> None) and not self.configuring:
            configFunct = self.configurableFunctions[ self.InteractionState ]
            if configFunct.type in config_types:
                self.configuring = True
                configFunct.start( self.InteractionState, x, y )
                self.haltNavigationInteraction()
#                if (configFunct.type == 'leveling'): self.getLabelActor().VisibilityOn()

    def haltNavigationInteraction(self):
        print " ----------------------BBW haltNavigationInteraction -------------------------- "
        if self.interactor: 
            istyle = self.interactor.GetInteractorStyle () 
            istyle.Off()  
    
    def resetNavigation(self):
        print " ----------------------BBW resetNavigation -------------------------- "
        if self.interactor:
            istyle = self.interactor.GetInteractorStyle () 
            istyle.On()  
            self.enableVisualizationInteraction()

    def getInteractionState( self, key ):
        for configFunct in self.configurableFunctions.values():
            if configFunct.matches( key ): return ( configFunct.name, configFunct.persisted, self )
        return ( None, None, None )    

    def updateInteractionState( self, config_state, button_state, **args ):    
        rcf = None
        if config_state == None: 
            self.finalizeLeveling()
            self.endInteraction()   
        else:            
            if self.InteractionState <> None: 
                configFunct = self.configurableFunctions[ self.InteractionState ]
                if configFunct.name <> config_state:
                    configFunct.close()                 
            configFunct = self.configurableFunctions.get( config_state, None )
            print " UpdateInteractionState, config_state = %s, cf = %s " % ( config_state, configFunct.key )
            if configFunct:
                child_activations = []
                if configFunct.type <> 'slider': 
                    self.releaseSliders() 
                configFunct.open( config_state )
                self.InteractionState = config_state                   
                self.LastInteractionState = self.InteractionState
                self.disableVisualizationInteraction()
                initialize_config_state = ( configFunct.label <> ButtonBarWidget.current_configuration_mode )               
                configFunct.processInteractionEvent( [ "InitConfig", button_state, initialize_config_state, self ] )
                if initialize_config_state:
                    bbar = ButtonBarWidget.getButtonBar( 'Interaction' )
                    child_activations = bbar.initConfigState( active_button=configFunct.name )
                
                if (configFunct.type == 'slider'):
                    force_enable = args.get( 'enable', False )

                    tvals = configFunct.value.getValues()
                    if initialize_config_state: 
                        for bbar in ButtonBarWidget.getButtonBars():
                            bbar.releaseSliders()
                    
                    if configFunct.position <> None:
                        n_active_sliders = configFunct.position[1]
                        position_index = configFunct.position[0]
                        
                        if initialize_config_state:
                            self.slidersVisible = [ ( iSlice == position_index ) for iSlice in range(4)  ] 
                        else:
                            self.slidersVisible[ position_index ] = button_state
                            
#                        slicePosition = configFunct.value
#                        self.setSliderValue( position_index, slicePosition.getValue() )  
                                               
                        if self.slidersVisible[ position_index ] or force_enable:
                            self.commandeerSlider( position_index, configFunct.sliderLabels[0], configFunct.getRangeBounds(), tvals[0]  )
                            self.positionSlider( position_index, n_active_sliders )
                            self.slidersVisible[ position_index ] = True
                        else: self.releaseSlider( position_index )
                    else:
                        n_active_sliders = len( configFunct.sliderLabels )
                        self.slidersVisible = [ ( slider_index < n_active_sliders ) for slider_index in range(4) ]
                        for slider_index in range(4):
                            if self.slidersVisible[ slider_index ]:
                                self.commandeerSlider( slider_index, configFunct.sliderLabels[slider_index], configFunct.getRangeBounds(), tvals[slider_index]  )
                                self.positionSlider( slider_index, n_active_sliders )
                            else:
                                self.releaseSlider( slider_index )
                    ButtonBarWidget.current_configuration_mode = configFunct.label
                    configFunct.processInteractionEvent( [ "ProcessSliderInit" ] )
                for child_button in child_activations: 
                    child_button.setButtonState(1)
                self.render()                     
            elif config_state == 'reset':
                self.resetCamera()              
                if  len(self.persistedParameters):
                    pname = self.persistedParameters.pop()
                    configFunct = self.configurableFunctions[pname]
                    param_value = configFunct.reset() 
                    if param_value: self.persistParameterList( [ (configFunct.name, param_value), ], update=True, list=False )                                      
        return configFunct

    def enableVisualizationInteraction(self): 
        pass

    def disableVisualizationInteraction(self):
        pass
    
    def printInteractionStyle(self, msg ):
        print "%s: InteractionStyle = %s " % ( msg,  self.renderWindow.GetInteractor().GetInteractorStyle().__class__.__name__ ) 

    def finalizeConfigurationObserver( self, parameter_name, **args ):
        self.finalizeParameter( parameter_name, **args )
        self.endConfiguration()    
#        for parameter_name in self.getModuleParameters(): self.finalizeParameter( parameter_name, *args ) 
        self.endInteraction( **args ) 

    def finalizeParameter(self, parameter_name, **args ):
        pass
    
    def endInteraction( self, **args ):  
        self.resetNavigation() 
        self.configuring = False
        self.InteractionState = None
        self.enableVisualizationInteraction()

    def endConfiguration( self ):
        pass
    
    def updateChildState(self, child_button, parent_name ):
        if len( child_button.parents ):
            if ( parent_name in child_button.parents ):
                parent_button = ButtonBarWidget.findButton( parent_name )
                if parent_button <> None: 
                    if parent_button.state:     
                        child_button.activate() 
                        if child_button.id in parent_button.children:
                            return True
                    else:                       
                        child_button.deactivate()
        return False
                
    
    def initConfigState( self, **args ):
        active_button = args.get( 'active_button', '' )
        child_activations = [ ]
        for button in self.buttons:
            if self.updateChildState( button, active_button ):
                child_activations.append( button )
            else:
                if button.toggle and (button.id <> active_button):
                    button.setToggleState(0)
        return child_activations
           
    def initializeConfiguration( self, **args ):
        for configFunct in self.configurableFunctions.values():
            configFunct.init( **args )
        for button in self.buttons:
            if button.toggle:
                button.broadcastState()
                
    def initializeChildren( self, **args ):
        for button in self.buttons:
            for parent_name in button.parents:
                self.updateChildState( button, parent_name )


if __name__ == '__main__':
        
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    iren.SetInteractorStyle( vtk.vtkInteractorStyleTrackballCamera()  )
    ren.SetBackground( 1.0, 1.0, 1.0 )
    renWin.SetSize(1000,800)
    
    buttonBarWidget = ButtonBarWidget( "Test", iren, orientation=Orientation.Vertical )
    buttonBarWidget.addButton( names=['ScaleColormap'], id='Scale Colormap', key='S' )
    buttonBarWidget.addButton( names=['Configure'], id='Configure', key='C' )

    ren.ResetCamera()
    ren.ResetCameraClippingRange()   
    iren.Initialize()
    renWin.Render()
    
    buttonBarWidget.build()
    buttonBarWidget.show()
    
    iren.Start()