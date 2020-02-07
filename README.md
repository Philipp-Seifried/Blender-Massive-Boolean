# Massive Boolean Addon
## Overview
This Blender 2.8x addon lets you combine all selected objects, using either "Union" or "Difference" Boolean operations.

![Screenshot](http://www.philippseifried.com/github/massive_bool_screenshot.png)

Typically, as you combine more and more objects with Boolean operations, you'll eventually reach a breaking point, where an operation creates degenerate geometry, or some numerical precision issue causes the resulting geometry to have holes or break down completely. The "Massive Boolean" addon attempts to work around these problems by running various mesh cleanup operations after each Boolean operation. 
**While results are by no means guaranteed, this should allow you to combine much more objects than other Boolean addons (on the order of hundreds, if their geometry is simple).**

## Installation
Navigate to Edit -> Preferences -> Addons -> Install. Select the .zip file or the unzipped massive_boolean.py file.

## How To Use
The addon lives in the 3D View's sidebar (press N while the cursor is over the 3D View to access it), in the Edit tab. Select all objects you want to combine. Your selection's active object (usually the last object you selected) will be the one to which all other objects will be added ("Union") or from which they will be subtracted ("Difference")

![Parameters](http://www.philippseifried.com/github/massive_bool_params.png)

The "Massive Boolean" panel has an "Options" sub-panel, which lets you configure which operations should be run after every boolean step. The above screenshot shows the default settings, which generally produced the best results in the tests I ran. Depending on what geometry you're trying to combine, activating or deactivating some of the listed operations might work better for you. 
**TIPP:** If you're combining geometry with a lot of perfectly aligned faces, try enabling "Jitter Operand Position" to move every boolean operand by a tiny random offset.

![Parameters](http://www.philippseifried.com/github/massive_bool_console.png)

Once you click "Union" or "Difference", the addon starts its work. Blender will likely appear to freeze, if you're combining more than a couple dozen objects. **The addon can take quite a while to complete, but shouldn't freeze permanently - enable the system console before starting the operation (Window -> Toggle System Console) to get updates on its progress.**

## Authors
[Philipp Seifried](https://twitter.com/PhilippSeifried)
