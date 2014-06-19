'''
Created on May 13, 2014

@author: tpmaxwel
'''
import cdms2
from PointCloudViewer import CPCPlot
#from VolumeViewer import VolumePlot
from SliceViewer import SlicePlot
from RectilinearGridPlot import RectGridPlot
from ConfigurationFunctions import PlotType

class DV3DApp:
    
    def __init__( self, **args ):
        self.plot = None
    
    
    def init(self, **args ):
        var= None
        init_args = args.get( 'init', None )
        if init_args:
            ( grid_file, data_file, interface, varnames, grd_coords, var_proc_op, ROI, subSpace ) = init_args
            df = cdms2.open( data_file )       
            var = df[ varnames[0] ]
        else:
            init_var = args.get( 'init_var', None )
            if init_var:
                ( var, var1,  roi, axes  ) = init_var
            
        if id(var) <> id(None):
            grid_metadata = var.getGrid()
            plot_type = args.get( 'plot_type', PlotType.getPointsLayout( grid_metadata ) )
            
            if plot_type == PlotType.Grid:
                self.plot = RectGridPlot(**args) 
                self.plot.init( **args ) 
            else:
                self.plot = CPCPlot(**args) 
                self.plot.init( **args  ) 

    def gminit(self, var1, var2, **args ):
        grid_metadata = var1.getGrid()
        plot_type = args.get( 'plot_type', PlotType.getPointsLayout( grid_metadata ) )
        
        if plot_type == PlotType.Grid:
            self.plot = RectGridPlot(**args) 
            self.plot.gminit( var1, var2, **args ) 
        else:
            self.plot = CPCPlot(**args) 
            self.plot.gminit( var1, var2, **args  ) 

            
    def getRenderWindow(self):
        return self.plot.renderWindow 
    
    def onKeyEvent( self, eventArgs ): 
        return self.plot.onKeyEvent( eventArgs )               

    def terminate( self ): 
        return self.plot.terminate( )               
        
