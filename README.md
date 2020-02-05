# Massive Boolean Addon
## Overview
This Blender addon lets you combine all selected objects, using either "Union" or "Difference" Boolean operations.

(TODO: screenshot of tool in action)

Typically, as you combine more and more objects with Boolean operations, you'll eventually reach a breaking point, where an operation creates degenerate geometry, or some numerical precision issue causes the resulting geometry to have holes or break down completely. The "Massive Boolean" addon attempts to work around these problems by running various mesh cleanup operations after each Boolean operation. 
*While results are by no means guaranteed, this should allow you to combine much more objects than other Boolean addons (on the order of hundreds, if their geometry is simple).*

## Installation
Navigate to Edit -> Preferences -> Addons -> Install. Select the .zip file or the unzipped .py file.

## How To Use
The addon lives in the 3D View's sidebar (press N while the cursor is over the 3D View to access it), in the Edit tab. Select all objects you want to combine. Your selection's active object (usually the last object you selected) will be the one to which all other objects will be added ("Union") or from which they will be subtracted ("Difference")

The "Massive Boolean" panel has an "Options" sub-panel, which lets you configure which operations should be run after every boolean step. By default, every option except for "Merge By Distance" is activated, as this produced the best results in the tests I ran. Depending on what geometry you're trying to combine, activating or deactivating some of the listed operations might work better for you. 

(TODO: screenshot of parameters)

Once you click "Union" or "Difference", the addon starts its work. Blender will likely appear to freeze, if you're combining more than a couple dozen objects. *The addon can take quite a while to complete, but shouldn't freeze permanently - enable the system console before starting the operation (Window -> Toggle System Console) to get updates on its progress.*
