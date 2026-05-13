# VIBE-CADING

> Point. Label. Vibe with AI.

OpenSCAD is powerful but describing geometry to an AI is hard.
"The top face", "that edge near the hole" — language fails where 
space is precise.

VIBE-CADING bridges that gap. Load your STL, click a face, 
give it a name. The tool outputs a structured JSON that gives 
your AI collaborator exact geometric context — normals, coordinates, 
semantics — so you can stop describing and start building.

**No server. No API. No build tools. Just open the HTML and go.**# Vibe-Cading
A  geometry annotation tool for OpenSCAD projects —  select faces, define them, let AI understand your 3D model precisely.




The author has an architectural background, and the project code was largely completed with the assistance of an LLM (including the introduction above). The author was primarily responsible for project planning and interaction logic design.

AGENT is already capable of creating SCAD files quite well. However, there is a lack of a communication bridge between humans and AI in the SCAD workflow, which makes the model creation process very cumbersome. This is the motivation behind launching this project.

In the long term, the goal is to eventually build a full web-based software solution (similar to ADAM), equipped with a more intuitive human–AI communication mechanism.
